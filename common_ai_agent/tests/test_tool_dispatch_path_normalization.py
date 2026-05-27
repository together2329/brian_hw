"""Windows path-separator normalization at the tool-dispatch chokepoint.

Backslash paths (Windows clients, or the LLM echoing a Windows-style path) must
resolve on POSIX backends. dispatch_tool normalizes path-only kwargs to forward
slashes for every tool, while leaving content / pattern / regex args untouched.
"""

from core.tool_dispatcher import dispatch_tool


def _dispatch(kwargs):
    captured = {}

    def fake(path=None, directory=None, pattern=None, content=None,
             old_text=None, root=None, **rest):
        captured.update(
            path=path, directory=directory, pattern=pattern,
            content=content, old_text=old_text, root=root,
        )
        return "ok"

    dispatch_tool(
        "faketool",
        pre_parsed_kwargs=dict(kwargs),
        available_tools={"faketool": fake},
    )
    return captured


def test_path_and_directory_backslashes_are_normalized():
    got = _dispatch({"path": "src\\rtl\\top.sv", "directory": "ip\\uart\\hdl"})
    assert got["path"] == "src/rtl/top.sv"
    assert got["directory"] == "ip/uart/hdl"


def test_mixed_separators_normalized():
    got = _dispatch({"path": "ROOT_IP\\demo/yaml\\demo.ssot.yaml"})
    assert got["path"] == "ROOT_IP/demo/yaml/demo.ssot.yaml"


def test_windows_absolute_path_separators_normalized():
    got = _dispatch({"path": "C:\\Users\\brian\\ip\\top.sv"})
    assert got["path"] == "C:/Users/brian/ip/top.sv"


def test_content_and_pattern_backslashes_preserved():
    # regex / file content legitimately contain backslashes — must NOT be touched
    got = _dispatch({
        "path": "a\\b.txt",
        "pattern": r"foo\d+\s",
        "content": "reg [7:0] x;\\n\\talways @(posedge clk)",
        "old_text": "C:\\not\\a\\path\\but\\text",
    })
    assert got["path"] == "a/b.txt"
    assert got["pattern"] == r"foo\d+\s"
    assert got["content"] == "reg [7:0] x;\\n\\talways @(posedge clk)"
    assert got["old_text"] == "C:\\not\\a\\path\\but\\text"


def test_forward_slash_paths_unchanged():
    got = _dispatch({"path": "already/posix/path.sv"})
    assert got["path"] == "already/posix/path.sv"
