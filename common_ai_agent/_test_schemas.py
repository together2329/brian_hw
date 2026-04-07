from core.tool_schema import TOOL_SCHEMAS, get_tool_schemas

web_schemas = [k for k in TOOL_SCHEMAS if k.startswith("web_")]
print("Web tool schemas:", web_schemas)

schemas = get_tool_schemas(["web_search", "web_fetch", "web_extract"])
for s in schemas:
    fn = s["function"]
    name = fn["name"]
    req = fn["parameters"]["required"]
    params = list(fn["parameters"]["properties"].keys())
    print(f"  {name}: required={req}, params={params}")

print("OK")
