"""
Tests for tool_schema + LLM client API compatibility.

Validates that tool schemas produced by tool_schema.py are valid for:
1. OpenAI Chat Completions API (non-strict mode)
2. OpenAI Responses API (/v1/responses) format
3. GLM / DeepSeek / other providers via _strip_strict_from_tools()
4. The todo_write nested schema bug that caused "invalid tool schema" errors

Also tests:
- _build_responses_request tool format conversion
- _strip_strict_from_tools removes strict/additionalProperties
- Dynamic schema registration
- All schemas are valid JSON Schema (basic structural checks)
"""

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "lib"))


# ─── Helper: basic JSON Schema structural validation ─────────────────────────

def _validate_schema_structure(schema, path="root"):
    """Recursively validate basic JSON Schema structure."""
    errors = []

    if not isinstance(schema, dict):
        return [f"{path}: expected dict, got {type(schema).__name__}"]

    # 'type' at parameter level should be a known JSON Schema type
    if "type" in schema:
        valid_types = {"object", "string", "integer", "number", "boolean", "array", "null"}
        t = schema["type"]
        if isinstance(t, str) and t not in valid_types:
            errors.append(f"{path}.type: invalid type '{t}'")

    # 'properties' must be a dict of schemas
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            errors.append(f"{path}.properties: expected dict")
        else:
            for pname, pschema in schema["properties"].items():
                errors.extend(_validate_schema_structure(pschema, f"{path}.properties.{pname}"))

    # 'items' must be a schema (for arrays)
    if "items" in schema:
        if isinstance(schema["items"], dict):
            errors.extend(_validate_schema_structure(schema["items"], f"{path}.items"))
        elif isinstance(schema["items"], list):
            for i, ischema in enumerate(schema["items"]):
                errors.extend(_validate_schema_structure(ischema, f"{path}.items[{i}]"))

    # 'required' must be a list of strings
    if "required" in schema:
        if not isinstance(schema["required"], list):
            errors.append(f"{path}.required: expected list, got {type(schema['required']).__name__}")
        elif not all(isinstance(r, str) for r in schema["required"]):
            errors.append(f"{path}.required: all items must be strings")

    # 'enum' must be a list
    if "enum" in schema:
        if not isinstance(schema["enum"], list):
            errors.append(f"{path}.enum: expected list")

    return errors


# ═══════════════════════════════════════════════════════════════════════════════
#  1. Tool Schema Core Structure Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolSchemaCoreStructure(unittest.TestCase):
    """Validate every tool schema has correct OpenAI function-calling structure."""

    @classmethod
    def setUpClass(cls):
        from core.tool_schema import TOOL_SCHEMAS
        cls.schemas = TOOL_SCHEMAS
        cls.all_tool_names = list(TOOL_SCHEMAS.keys())

    def test_all_schemas_have_type_function(self):
        """Every schema must have type='function'."""
        for name, schema in self.schemas.items():
            self.assertEqual(schema.get("type"), "function",
                           f"{name}: type must be 'function', got {schema.get('type')}")

    def test_all_schemas_have_function_key(self):
        """Every schema must have a 'function' dict."""
        for name, schema in self.schemas.items():
            self.assertIn("function", schema, f"{name}: missing 'function' key")
            self.assertIsInstance(schema["function"], dict, f"{name}: 'function' must be a dict")

    def test_all_schemas_have_name(self):
        """Every function must have a 'name' matching the key."""
        for name, schema in self.schemas.items():
            func = schema.get("function", {})
            self.assertEqual(func.get("name"), name,
                           f"Schema key '{name}' has function.name='{func.get('name')}'")

    def test_all_schemas_have_description(self):
        """Every function must have a non-empty description."""
        for name, schema in self.schemas.items():
            func = schema.get("function", {})
            desc = func.get("description", "")
            self.assertTrue(len(desc) > 0, f"{name}: missing or empty description")

    def test_all_schemas_have_parameters_object(self):
        """Every function must have parameters with type='object'."""
        for name, schema in self.schemas.items():
            func = schema.get("function", {})
            params = func.get("parameters", {})
            self.assertEqual(params.get("type"), "object",
                           f"{name}: parameters.type must be 'object'")

    def test_all_schemas_have_properties_dict(self):
        """Every function parameters must have 'properties' dict."""
        for name, schema in self.schemas.items():
            func = schema.get("function", {})
            params = func.get("parameters", {})
            self.assertIn("properties", params, f"{name}: missing 'properties' in parameters")
            self.assertIsInstance(params["properties"], dict,
                               f"{name}: 'properties' must be a dict")

    def test_all_schemas_have_required_list(self):
        """Every function parameters must have 'required' list."""
        for name, schema in self.schemas.items():
            func = schema.get("function", {})
            params = func.get("parameters", {})
            self.assertIn("required", params, f"{name}: missing 'required' in parameters")
            self.assertIsInstance(params["required"], list,
                               f"{name}: 'required' must be a list")

    def test_required_fields_exist_in_properties(self):
        """Every field in 'required' must exist in 'properties'."""
        for name, schema in self.schemas.items():
            func = schema.get("function", {})
            params = func.get("parameters", {})
            props = set(params.get("properties", {}).keys())
            for req in params.get("required", []):
                self.assertIn(req, props,
                            f"{name}: required field '{req}' not in properties")

    def test_no_strict_key(self):
        """After fix: no schema should have 'strict' key."""
        for name, schema in self.schemas.items():
            self.assertNotIn("strict", schema,
                           f"{name}: should NOT have 'strict' key (removed in fix)")

    def test_no_additional_properties(self):
        """After fix: no schema parameters should have 'additionalProperties'."""
        for name, schema in self.schemas.items():
            func = schema.get("function", {})
            params = func.get("parameters", {})
            self.assertNotIn("additionalProperties", params,
                           f"{name}: should NOT have 'additionalProperties' (removed in fix)")

    def test_property_descriptions(self):
        """Every property should have a 'description' string."""
        for name, schema in self.schemas.items():
            func = schema.get("function", {})
            params = func.get("parameters", {})
            for pname, pdef in params.get("properties", {}).items():
                if pdef.get("type") == "object":
                    continue  # nested objects may not have description
                self.assertIn("description", pdef,
                            f"{name}.{pname}: missing 'description'")
                self.assertIsInstance(pdef["description"], str,
                                    f"{name}.{pname}: description must be string")

    def test_property_types_are_valid(self):
        """Every property type must be a valid JSON Schema type."""
        valid_types = {"string", "integer", "number", "boolean", "array", "object"}
        for name, schema in self.schemas.items():
            func = schema.get("function", {})
            params = func.get("parameters", {})
            for pname, pdef in params.get("properties", {}).items():
                if "type" in pdef:
                    self.assertIn(pdef["type"], valid_types,
                                f"{name}.{pname}: invalid type '{pdef['type']}'")


class TestSchemaJSONSerialization(unittest.TestCase):
    """Verify all schemas serialize cleanly to JSON (required for API calls)."""

    @classmethod
    def setUpClass(cls):
        from core.tool_schema import TOOL_SCHEMAS
        cls.schemas = TOOL_SCHEMAS

    def test_all_schemas_json_serializable(self):
        """Every schema must be JSON-serializable."""
        for name, schema in self.schemas.items():
            try:
                json_str = json.dumps(schema)
                self.assertTrue(len(json_str) > 0, f"{name}: empty JSON output")
            except (TypeError, ValueError) as e:
                self.fail(f"{name}: schema is not JSON-serializable: {e}")

    def test_round_trip_json(self):
        """JSON encode → decode should produce identical structure."""
        for name, schema in self.schemas.items():
            encoded = json.dumps(schema, sort_keys=True)
            decoded = json.loads(encoded)
            re_encoded = json.dumps(decoded, sort_keys=True)
            self.assertEqual(encoded, re_encoded,
                           f"{name}: JSON round-trip mismatch")

    def test_all_schemas_valid_structure(self):
        """Validate nested schema structure recursively."""
        from core.tool_schema import TOOL_SCHEMAS
        for name, schema in TOOL_SCHEMAS.items():
            func = schema.get("function", {})
            params = func.get("parameters", {})
            errors = _validate_schema_structure(params, f"{name}.parameters")
            for err in errors:
                self.fail(err)


# ═══════════════════════════════════════════════════════════════════════════════
#  2. todo_write Schema Specific Tests (the original bug)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTodoWriteSchema(unittest.TestCase):
    """Specific tests for the todo_write schema that caused the Codex 5.3 error.

    The original bug: strict=True + additionalProperties=False was set on the
    top-level schema, but the nested 'items' object (for the todos array) was
    missing additionalProperties=False. OpenAI strict mode requires EVERY nested
    object to have additionalProperties=False, and ALL properties must be required.

    The fix removed strict mode entirely since many tools have optional params.
    """

    @classmethod
    def setUpClass(cls):
        from core.tool_schema import TOOL_SCHEMAS
        cls.schema = TOOL_SCHEMAS["todo_write"]

    def test_todo_write_has_todos_param(self):
        """todo_write must have a 'todos' parameter."""
        func = self.schema["function"]
        params = func["parameters"]
        self.assertIn("todos", params["properties"])

    def test_todos_is_array_type(self):
        """The 'todos' parameter must be type 'array'."""
        todos_def = self.schema["function"]["parameters"]["properties"]["todos"]
        self.assertEqual(todos_def["type"], "array")

    def test_todos_has_items(self):
        """The 'todos' array must have 'items' schema."""
        todos_def = self.schema["function"]["parameters"]["properties"]["todos"]
        self.assertIn("items", todos_def)
        self.assertIsInstance(todos_def["items"], dict)

    def test_items_has_required_fields(self):
        """Items schema must have required fields: content, activeForm, status."""
        items = self.schema["function"]["parameters"]["properties"]["todos"]["items"]
        self.assertIn("required", items)
        required = items["required"]
        self.assertIn("content", required)
        self.assertIn("activeForm", required)
        self.assertIn("status", required)

    def test_items_status_has_enum(self):
        """Items status must have enum with pending/in_progress/completed."""
        items = self.schema["function"]["parameters"]["properties"]["todos"]["items"]
        status_def = items["properties"]["status"]
        self.assertIn("enum", status_def)
        self.assertIn("pending", status_def["enum"])
        self.assertIn("in_progress", status_def["enum"])
        self.assertIn("completed", status_def["enum"])

    def test_no_strict_mode(self):
        """todo_write schema must NOT have strict mode (was the bug cause)."""
        self.assertNotIn("strict", self.schema)

    def test_no_additional_properties_on_parameters(self):
        """Parameters must NOT have additionalProperties (removed in fix)."""
        params = self.schema["function"]["parameters"]
        self.assertNotIn("additionalProperties", params)

    def test_todos_is_required(self):
        """'todos' must be in the required list."""
        params = self.schema["function"]["parameters"]
        self.assertIn("todos", params["required"])

    def test_items_object_type(self):
        """Items schema should be type 'object'."""
        items = self.schema["function"]["parameters"]["properties"]["todos"]["items"]
        self.assertEqual(items.get("type"), "object")

    def test_items_has_properties(self):
        """Items schema must have properties dict."""
        items = self.schema["function"]["parameters"]["properties"]["todos"]["items"]
        self.assertIn("properties", items)
        self.assertIsInstance(items["properties"], dict)


# ═══════════════════════════════════════════════════════════════════════════════
#  3. OpenAI Chat Completions API Compatibility
# ═══════════════════════════════════════════════════════════════════════════════

class TestOpenAIChatCompat(unittest.TestCase):
    """Test that schemas work with OpenAI Chat Completions API.

    Validates the format sent to POST /v1/chat/completions with tools parameter.
    """

    @classmethod
    def setUpClass(cls):
        from core.tool_schema import get_tool_schemas
        cls.all_schemas = get_tool_schemas([
            "todo_write", "todo_update", "todo_add", "todo_remove", "todo_status",
            "read_file", "write_file", "replace_in_file", "run_command",
            "grep_file", "find_files", "git_status",
        ])

    def test_schemas_are_list(self):
        """get_tool_schemas returns a list."""
        self.assertIsInstance(self.all_schemas, list)

    def test_expected_count(self):
        """Should return exactly the number of requested tools that exist."""
        self.assertEqual(len(self.all_schemas), 12)

    def test_each_schema_is_valid_openai_tool(self):
        """Each schema must be a valid OpenAI tool definition."""
        for schema in self.all_schemas:
            self.assertEqual(schema["type"], "function")
            self.assertIn("function", schema)
            func = schema["function"]
            self.assertIn("name", func)
            self.assertIn("description", func)
            self.assertIn("parameters", func)
            params = func["parameters"]
            self.assertEqual(params["type"], "object")
            self.assertIn("properties", params)
            self.assertIn("required", params)

    def test_can_serialize_for_api_request(self):
        """Schemas must be serializable into a tools JSON payload."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "test"}],
            "tools": self.all_schemas,
            "tool_choice": "auto",
        }
        json_str = json.dumps(payload)
        self.assertTrue(len(json_str) > 100)  # Non-trivial payload

    def test_no_extra_top_level_keys(self):
        """No unexpected top-level keys (e.g. 'strict') in schemas."""
        valid_top_keys = {"type", "function"}
        for schema in self.all_schemas:
            for key in schema.keys():
                self.assertIn(key, valid_top_keys,
                            f"Unexpected top-level key '{key}' in {schema['function']['name']}")

    def test_empty_properties_tools(self):
        """Tools with no parameters (like git_status, todo_status) have empty properties."""
        from core.tool_schema import get_tool_schemas
        schemas = get_tool_schemas(["git_status", "todo_status"])
        for schema in schemas:
            params = schema["function"]["parameters"]
            self.assertEqual(params["properties"], {})
            self.assertEqual(params["required"], [])

    def test_optional_params_not_in_required(self):
        """Optional params should NOT be in required list."""
        from core.tool_schema import TOOL_SCHEMAS
        # todo_update: reason, content, detail are optional
        todo_update = TOOL_SCHEMAS["todo_update"]
        required = todo_update["function"]["parameters"]["required"]
        self.assertIn("index", required)
        self.assertIn("status", required)
        self.assertNotIn("reason", required)
        self.assertNotIn("content", required)
        self.assertNotIn("detail", required)

    def test_todo_add_optional_params(self):
        """todo_add: priority and index are optional."""
        from core.tool_schema import TOOL_SCHEMAS
        todo_add = TOOL_SCHEMAS["todo_add"]
        required = todo_add["function"]["parameters"]["required"]
        self.assertIn("content", required)
        self.assertNotIn("priority", required)
        self.assertNotIn("index", required)


class TestGetToolSchemasFiltering(unittest.TestCase):
    """Test get_tool_schemas filtering logic."""

    def test_filter_to_known_tools(self):
        """Only requested tools that exist are returned."""
        from core.tool_schema import get_tool_schemas
        result = get_tool_schemas(["read_file", "write_file", "nonexistent_tool_xyz"])
        names = [s["function"]["name"] for s in result]
        self.assertIn("read_file", names)
        self.assertIn("write_file", names)
        self.assertNotIn("nonexistent_tool_xyz", names)

    def test_empty_list(self):
        """Empty allowed list returns empty result."""
        from core.tool_schema import get_tool_schemas
        result = get_tool_schemas([])
        self.assertEqual(result, [])

    def test_all_unknown(self):
        """All unknown tools returns empty list."""
        from core.tool_schema import get_tool_schemas
        result = get_tool_schemas(["fake1", "fake2"])
        self.assertEqual(result, [])

    def test_order_preserved(self):
        """Results maintain the order of allowed_tools."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write", "todo_update", "todo_add"])
        names = [s["function"]["name"] for s in tools]
        self.assertEqual(names, ["todo_write", "todo_update", "todo_add"])


# ═══════════════════════════════════════════════════════════════════════════════
#  4. OpenAI Responses API Format Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestResponsesAPIFormat(unittest.TestCase):
    """Test _build_responses_request converts tool schemas correctly.

    The Responses API (/v1/responses) has a different tool format than
    Chat Completions. Tools must be:
      {"type": "function", "name": "...", "description": "...", "parameters": {...}}

    NOT wrapped in a "function" key like Chat Completions.
    """

    def _build_responses_data(self, tools):
        """Helper: build a chat completions data dict and convert to Responses API."""
        from src.llm_client import _build_responses_request
        chat_data = {
            "model": "gpt-5.3-codex",
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Test"},
            ],
            "tools": tools,
            "max_completion_tokens": 4096,
            "stream": True,
        }
        return _build_responses_request(chat_data, "gpt-5.3-codex")

    def test_responses_format_no_function_key(self):
        """Responses API tools should NOT have 'function' wrapper key."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write", "read_file"])
        resp_data = self._build_responses_data(tools)

        for tool in resp_data.get("tools", []):
            self.assertNotIn("function", tool,
                           f"Responses API tool '{tool.get('name')}' should NOT have 'function' key")

    def test_responses_format_has_required_keys(self):
        """Each Responses API tool must have type, name, description, parameters."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write", "todo_update", "read_file"])
        resp_data = self._build_responses_data(tools)

        for tool in resp_data.get("tools", []):
            self.assertEqual(tool["type"], "function")
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("parameters", tool)

    def test_responses_format_preserves_name(self):
        """Tool names must be preserved in conversion."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write"])
        resp_data = self._build_responses_data(tools)

        self.assertEqual(len(resp_data["tools"]), 1)
        self.assertEqual(resp_data["tools"][0]["name"], "todo_write")

    def test_responses_format_preserves_parameters(self):
        """Parameters must be preserved exactly in conversion."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write"])
        original_params = tools[0]["function"]["parameters"]
        resp_data = self._build_responses_data(tools)

        resp_params = resp_data["tools"][0]["parameters"]
        self.assertEqual(original_params, resp_params)

    def test_responses_max_output_tokens(self):
        """max_completion_tokens is converted to max_output_tokens."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["read_file"])
        resp_data = self._build_responses_data(tools)
        self.assertEqual(resp_data.get("max_output_tokens"), 4096)

    def test_responses_stream_flag(self):
        """Stream flag is preserved."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["read_file"])
        resp_data = self._build_responses_data(tools)
        self.assertTrue(resp_data.get("stream"))

    def test_responses_model_set(self):
        """Model name is set correctly."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["read_file"])
        resp_data = self._build_responses_data(tools)
        self.assertEqual(resp_data["model"], "gpt-5.3-codex")

    def test_responses_no_strict_in_tools(self):
        """After fix: no 'strict' key in Responses API tools."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write", "todo_update"])
        resp_data = self._build_responses_data(tools)

        for tool in resp_data.get("tools", []):
            self.assertNotIn("strict", tool,
                           f"Tool '{tool.get('name')}' should NOT have 'strict' key")

    def test_responses_todo_write_nested_items(self):
        """todo_write items schema must survive Responses API conversion."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write"])
        resp_data = self._build_responses_data(tools)

        params = resp_data["tools"][0]["parameters"]
        todos_props = params["properties"]["todos"]
        items = todos_props["items"]

        # Must have the nested structure intact
        self.assertEqual(items["type"], "object")
        self.assertIn("content", items["properties"])
        self.assertIn("activeForm", items["properties"])
        self.assertIn("status", items["properties"])
        self.assertIn("required", items)

    def test_responses_no_tools_if_none_provided(self):
        """No tools key in response if input has no tools."""
        from src.llm_client import _build_responses_request
        chat_data = {
            "model": "gpt-5.3-codex",
            "messages": [{"role": "user", "content": "hi"}],
        }
        resp_data = _build_responses_request(chat_data, "gpt-5.3-codex")
        self.assertNotIn("tools", resp_data)

    def test_responses_only_function_tools(self):
        """Only type='function' tools are converted (non-function are skipped)."""
        from src.llm_client import _build_responses_request
        chat_data = {
            "model": "gpt-5.3-codex",
            "messages": [],
            "tools": [
                {"type": "function", "function": {"name": "my_func", "description": "test", "parameters": {"type": "object", "properties": {}}}},
                {"type": "web_search"},  # Non-function, should be skipped
            ],
        }
        resp_data = _build_responses_request(chat_data, "gpt-5.3-codex")
        self.assertEqual(len(resp_data["tools"]), 1)
        self.assertEqual(resp_data["tools"][0]["name"], "my_func")


# ═══════════════════════════════════════════════════════════════════════════════
#  5. GLM / Non-OpenAI Provider Compatibility
# ═══════════════════════════════════════════════════════════════════════════════

class TestStripStrictFromTools(unittest.TestCase):
    """Test _strip_strict_from_tools for GLM/DeepSeek compatibility.

    Even though we removed strict mode from schemas, _strip_strict_from_tools
    should still work correctly as a safety net (it's now a no-op but must not
    break anything).
    """

    def _strip(self, tools):
        from src.llm_client import _strip_strict_from_tools
        return _strip_strict_from_tools(tools)

    def test_does_not_mutate_input(self):
        """Returns new list — does not mutate input."""
        from core.tool_schema import get_tool_schemas
        original = get_tool_schemas(["todo_write", "read_file"])
        original_copy = copy.deepcopy(original)

        result = self._strip(original)

        # Original unchanged
        self.assertEqual(original, original_copy)
        # Result is a different object
        self.assertIsNot(result, original)

    def test_preserves_function_name(self):
        """Function names are preserved."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write", "todo_update"])
        result = self._strip(tools)
        names = [t["function"]["name"] for t in result]
        self.assertEqual(names, ["todo_write", "todo_update"])

    def test_preserves_parameters(self):
        """Parameter schemas are preserved."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write"])
        result = self._strip(tools)
        params = result[0]["function"]["parameters"]
        self.assertIn("todos", params["properties"])

    def test_preserves_description(self):
        """Descriptions are preserved."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["read_file"])
        result = self._strip(tools)
        self.assertTrue(len(result[0]["function"]["description"]) > 0)

    def test_handles_tools_with_strict_key(self):
        """If a tool somehow still has 'strict', it's removed."""
        tools = [{
            "type": "function",
            "strict": True,
            "function": {
                "name": "test_tool",
                "description": "test",
                "parameters": {
                    "type": "object",
                    "properties": {"x": {"type": "string"}},
                    "required": ["x"],
                    "additionalProperties": False,
                },
            },
        }]
        result = self._strip(tools)
        self.assertNotIn("strict", result[0])
        self.assertNotIn("additionalProperties", result[0]["function"]["parameters"])

    def test_handles_empty_list(self):
        """Empty list returns empty list."""
        result = self._strip([])
        self.assertEqual(result, [])

    def test_handles_deep_copy(self):
        """Deep nested objects are independent copies."""
        from core.tool_schema import get_tool_schemas
        tools = get_tool_schemas(["todo_write"])
        result = self._strip(tools)

        # Modify result — original should be unchanged
        result[0]["function"]["parameters"]["properties"]["todos"]["items"]["properties"]["content"]["type"] = "number"
        original_type = tools[0]["function"]["parameters"]["properties"]["todos"]["items"]["properties"]["content"]["type"]
        self.assertEqual(original_type, "string")


class TestGLMAPISchemaPayload(unittest.TestCase):
    """Simulate what a GLM API request payload looks like with our tool schemas."""

    def test_glm_request_payload_structure(self):
        """Build a GLM-style request and verify it's valid JSON."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _strip_strict_from_tools

        tools = get_tool_schemas(["todo_write", "todo_update", "read_file"])
        # GLM doesn't support strict mode
        tools = _strip_strict_from_tools(tools)

        payload = {
            "model": "glm-5.1",
            "messages": [
                {"role": "system", "content": "You are a coding assistant."},
                {"role": "user", "content": "Create a todo list"},
            ],
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.7,
        }

        # Must be serializable
        json_str = json.dumps(payload)
        self.assertTrue(len(json_str) > 0)

        # Parse back and verify structure
        parsed = json.loads(json_str)
        self.assertEqual(parsed["model"], "glm-5.1")
        self.assertEqual(len(parsed["tools"]), 3)
        for tool in parsed["tools"]:
            self.assertEqual(tool["type"], "function")
            self.assertNotIn("strict", tool)

    def test_glm_no_strict_in_any_nested_object(self):
        """Ensure no 'strict' or 'additionalProperties' in any level."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _strip_strict_from_tools

        tools = get_tool_schemas(["todo_write"])
        tools = _strip_strict_from_tools(tools)

        json_str = json.dumps(tools[0])
        self.assertNotIn('"strict"', json_str)
        self.assertNotIn('"additionalProperties"', json_str)

    def test_deepseek_payload_structure(self):
        """DeepSeek API payload structure."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _strip_strict_from_tools

        tools = get_tool_schemas(["todo_write", "todo_add", "run_command"])
        tools = _strip_strict_from_tools(tools)

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "help"}],
            "tools": tools,
        }

        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed["tools"]), 3)

    def test_zai_payload_structure(self):
        """Z.AI payload structure."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _strip_strict_from_tools

        tools = get_tool_schemas(["todo_write"])
        tools = _strip_strict_from_tools(tools)

        payload = {
            "model": "z1-chat",
            "messages": [{"role": "user", "content": "test"}],
            "tools": tools,
        }
        json_str = json.dumps(payload)
        self.assertTrue(len(json_str) > 0)


# ═══════════════════════════════════════════════════════════════════════════════
#  6. Responses API Model Detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestResponsesAPIModelDetection(unittest.TestCase):
    """Test is_responses_api_model for correct routing."""

    def test_codex_models_are_responses_api(self):
        """gpt-*codex* models use Responses API."""
        from src.llm_client import is_responses_api_model
        self.assertTrue(is_responses_api_model("gpt-5.1-codex"))
        self.assertTrue(is_responses_api_model("gpt-5.3-codex"))
        self.assertTrue(is_responses_api_model("gpt-4-codex"))
        self.assertTrue(is_responses_api_model("GPT-5.3-CODEX"))  # case insensitive

    def test_regular_gpt_models_are_not_responses_api(self):
        """Regular GPT models use Chat Completions API."""
        from src.llm_client import is_responses_api_model
        self.assertFalse(is_responses_api_model("gpt-4o"))
        self.assertFalse(is_responses_api_model("gpt-4o-mini"))
        self.assertFalse(is_responses_api_model("gpt-3.5-turbo"))

    def test_glm_is_not_responses_api(self):
        """GLM models use Chat Completions API."""
        from src.llm_client import is_responses_api_model
        self.assertFalse(is_responses_api_model("glm-5.1"))
        self.assertFalse(is_responses_api_model("glm-4"))

    def test_deepseek_is_not_responses_api(self):
        """DeepSeek models use Chat Completions API."""
        from src.llm_client import is_responses_api_model
        self.assertFalse(is_responses_api_model("deepseek-chat"))
        self.assertFalse(is_responses_api_model("deepseek-coder"))

    def test_path_prefix_stripped(self):
        """Model name with path prefix is handled."""
        from src.llm_client import is_responses_api_model
        self.assertTrue(is_responses_api_model("openai/gpt-5.3-codex"))
        self.assertFalse(is_responses_api_model("openai/gpt-4o"))


# ═══════════════════════════════════════════════════════════════════════════════
#  7. Dynamic Schema Registration
# ═══════════════════════════════════════════════════════════════════════════════

class TestDynamicSchemaRegistration(unittest.TestCase):
    """Test register_dynamic_schema for MCP tool support."""

    def setUp(self):
        from core.tool_schema import _dynamic_schemas
        self._orig = dict(_dynamic_schemas)
        _dynamic_schemas.clear()

    def tearDown(self):
        from core.tool_schema import _dynamic_schemas
        _dynamic_schemas.clear()
        _dynamic_schemas.update(self._orig)

    def test_register_and_retrieve(self):
        """Registered schema appears in get_tool_schemas."""
        from core.tool_schema import register_dynamic_schema, get_tool_schemas

        register_dynamic_schema("my_mcp_tool", {
            "type": "function",
            "function": {
                "name": "my_mcp_tool",
                "description": "An MCP tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "Input data"},
                    },
                    "required": ["input"],
                },
            },
        })

        result = get_tool_schemas(["my_mcp_tool"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["function"]["name"], "my_mcp_tool")

    def test_dynamic_overrides_builtin(self):
        """Dynamic schema takes precedence over builtin (merged last)."""
        from core.tool_schema import register_dynamic_schema, get_tool_schemas

        register_dynamic_schema("read_file", {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "OVERRIDDEN",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        })

        result = get_tool_schemas(["read_file"])
        self.assertEqual(result[0]["function"]["description"], "OVERRIDDEN")

    def test_mixed_builtin_and_dynamic(self):
        """Both builtin and dynamic tools appear together."""
        from core.tool_schema import register_dynamic_schema, get_tool_schemas

        register_dynamic_schema("mcp_tool_a", {
            "type": "function",
            "function": {
                "name": "mcp_tool_a",
                "description": "MCP Tool A",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        })

        result = get_tool_schemas(["read_file", "mcp_tool_a", "todo_write"])
        names = [s["function"]["name"] for s in result]
        self.assertIn("read_file", names)
        self.assertIn("mcp_tool_a", names)
        self.assertIn("todo_write", names)


# ═══════════════════════════════════════════════════════════════════════════════
#  8. Regression Tests: Specific Schema Patterns
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemaRegressionTests(unittest.TestCase):
    """Regression tests for specific patterns that previously caused API errors."""

    def test_nested_array_items_have_required(self):
        """Array-typed properties with 'items' must have required in items."""
        from core.tool_schema import TOOL_SCHEMAS

        todo_write = TOOL_SCHEMAS["todo_write"]
        items = todo_write["function"]["parameters"]["properties"]["todos"]["items"]
        self.assertIn("required", items,
                     "todo_write items must have 'required' for OpenAI compatibility")

    def test_nested_array_items_have_type(self):
        """Array items must have 'type'."""
        from core.tool_schema import TOOL_SCHEMAS

        # Check all array-typed properties
        for name, schema in TOOL_SCHEMAS.items():
            func = schema.get("function", {})
            params = func.get("parameters", {})
            for pname, pdef in params.get("properties", {}).items():
                if pdef.get("type") == "array":
                    self.assertIn("items", pdef,
                                f"{name}.{pname}: array must have 'items'")
                    self.assertIn("type", pdef["items"],
                                f"{name}.{pname}: items must have 'type'")

    def test_enum_values_are_strings(self):
        """All enum values in schemas should be strings."""
        from core.tool_schema import TOOL_SCHEMAS

        def _check_enums(obj, path=""):
            if isinstance(obj, dict):
                if "enum" in obj:
                    for val in obj["enum"]:
                        if not isinstance(val, str):
                            return [f"{path}.enum: non-string value {val!r}"]
                for k, v in obj.items():
                    errors = _check_enums(v, f"{path}.{k}" if path else k)
                    if errors:
                        return errors
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    errors = _check_enums(v, f"{path}[{i}]")
                    if errors:
                        return errors
            return []

        for name, schema in TOOL_SCHEMAS.items():
            errors = _check_enums(schema, name)
            for err in errors:
                self.fail(err)

    def test_sv_compile_files_is_string_array(self):
        """sv_compile files parameter must be array of strings."""
        from core.tool_schema import TOOL_SCHEMAS
        sv_compile = TOOL_SCHEMAS["sv_compile"]
        files_prop = sv_compile["function"]["parameters"]["properties"]["files"]
        self.assertEqual(files_prop["type"], "array")
        self.assertEqual(files_prop["items"]["type"], "string")

    def test_no_null_or_undefined_values(self):
        """No None/undefined values in serialized schemas."""
        from core.tool_schema import TOOL_SCHEMAS

        def _check_none(obj, path=""):
            if obj is None:
                return [f"{path}: null value"]
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if v is None:
                        return [f"{path}.{k}: null value"]
                    errors = _check_none(v, f"{path}.{k}" if path else k)
                    if errors:
                        return errors
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    if v is None:
                        return [f"{path}[{i}]: null value"]
                    errors = _check_none(v, f"{path}[{i}]")
                    if errors:
                        return errors
            return []

        for name, schema in TOOL_SCHEMAS.items():
            errors = _check_none(schema, name)
            for err in errors:
                self.fail(err)

    def test_build_responses_url(self):
        """build_responses_url produces correct path for standard and Azure providers."""
        from src.llm_client import build_responses_url

        # Standard OpenAI URL
        with patch('src.llm_client.is_azure_provider', return_value=False):
            self.assertEqual(build_responses_url("https://api.openai.com/v1"),
                            "https://api.openai.com/v1/responses")
            self.assertEqual(build_responses_url("https://api.openai.com/v1/"),
                            "https://api.openai.com/v1/responses")

        # Azure OpenAI URL — uses v1 API format, NOT deployment-based
        with patch('src.llm_client.is_azure_provider', return_value=True):
            url = build_responses_url("https://my-endpoint.openai.azure.com", model="gpt5.1")
            self.assertEqual(url, "https://my-endpoint.openai.azure.com/openai/v1/responses")

    def test_strip_strict_idempotent(self):
        """Running _strip_strict_from_tools twice produces same result."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _strip_strict_from_tools

        tools = get_tool_schemas(["todo_write", "todo_update"])
        result1 = _strip_strict_from_tools(tools)
        result2 = _strip_strict_from_tools(result1)
        self.assertEqual(result1, result2)


# ═══════════════════════════════════════════════════════════════════════════════
#  9. Full Pipeline Integration: Schema → API Request
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullPipelineIntegration(unittest.TestCase):
    """End-to-end tests: schema generation → API request construction."""

    def test_openai_chat_pipeline(self):
        """Full pipeline for OpenAI Chat Completions API."""
        from core.tool_schema import get_tool_schemas

        tools = get_tool_schemas(["todo_write", "read_file", "run_command"])

        # Simulate what llm_client._build_chat_request does
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Create todos and run them"},
            ],
            "tools": tools,
            "tool_choice": "auto",
            "max_tokens": 4096,
        }

        # Verify it's valid JSON
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["model"], "gpt-4o")
        self.assertEqual(len(parsed["tools"]), 3)

        # Verify no strict/additionalProperties
        for tool in parsed["tools"]:
            self.assertNotIn("strict", tool)
            params = tool["function"]["parameters"]
            self.assertNotIn("additionalProperties", params)

    def test_openai_responses_pipeline(self):
        """Full pipeline for OpenAI Responses API."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _build_responses_request

        tools = get_tool_schemas(["todo_write", "todo_update"])

        chat_data = {
            "model": "gpt-5.3-codex",
            "messages": [
                {"role": "system", "content": "Help"},
                {"role": "user", "content": "Create a todo list"},
            ],
            "tools": tools,
            "max_completion_tokens": 4096,
            "stream": True,
        }

        resp_data = _build_responses_request(chat_data, "gpt-5.3-codex")

        # Verify Responses API format
        self.assertEqual(resp_data["model"], "gpt-5.3-codex")
        self.assertEqual(resp_data["max_output_tokens"], 4096)
        self.assertTrue(resp_data["stream"])
        self.assertEqual(len(resp_data["tools"]), 2)

        # Verify tool format (flat, no 'function' wrapper)
        for tool in resp_data["tools"]:
            self.assertEqual(tool["type"], "function")
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("parameters", tool)
            self.assertNotIn("function", tool)
            self.assertNotIn("strict", tool)

        # Serialize to verify API-ready
        json.dumps(resp_data)

    def test_glm_pipeline(self):
        """Full pipeline for GLM API with strict stripping."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _strip_strict_from_tools

        tools = get_tool_schemas(["todo_write", "todo_update", "read_file"])
        # GLM doesn't support strict
        tools = _strip_strict_from_tools(tools)

        payload = {
            "model": "glm-5.1",
            "messages": [
                {"role": "user", "content": "Track my tasks"},
            ],
            "tools": tools,
            "tool_choice": "auto",
        }

        json_str = json.dumps(payload)
        parsed = json.loads(json_str)

        # Verify clean structure
        self.assertEqual(len(parsed["tools"]), 3)
        for tool in parsed["tools"]:
            self.assertEqual(tool["type"], "function")
            self.assertNotIn("strict", tool)
            self.assertNotIn("additionalProperties",
                           json.dumps(tool["function"]["parameters"]))

    def test_deepseek_pipeline(self):
        """Full pipeline for DeepSeek API."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _strip_strict_from_tools

        tools = get_tool_schemas(["todo_write"])
        tools = _strip_strict_from_tools(tools)

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "test"}],
            "tools": tools,
        }

        # Must serialize cleanly
        json.dumps(payload)

    def test_codex_53_full_pipeline(self):
        """Simulate exact Codex 5.3 (Responses API) flow that was failing."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _build_responses_request, is_responses_api_model

        # Step 1: Is this a Responses API model?
        model = "gpt-5.3-codex"
        self.assertTrue(is_responses_api_model(model),
                       "Codex 5.3 should be detected as Responses API model")

        # Step 2: Get tool schemas
        tools = get_tool_schemas([
            "todo_write", "todo_update", "todo_add", "todo_remove",
            "todo_status", "read_file", "write_file",
        ])
        self.assertTrue(len(tools) > 0)

        # Step 3: Build Responses API request
        chat_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a coding agent."},
                {"role": "user", "content": "Create a todo list and implement"},
            ],
            "tools": tools,
            "max_completion_tokens": 16384,
            "stream": True,
        }
        resp_data = _build_responses_request(chat_data, model)

        # Step 4: Verify the exact payload structure
        self.assertIn("tools", resp_data)
        self.assertNotIn("messages", resp_data)  # converted to "input"

        # Step 5: Verify todo_write is correctly formatted
        todo_write_tool = None
        for tool in resp_data["tools"]:
            if tool["name"] == "todo_write":
                todo_write_tool = tool
                break
        self.assertIsNotNone(todo_write_tool, "todo_write must be in tools")

        # Step 6: Verify nested items schema (this was the bug)
        params = todo_write_tool["parameters"]
        self.assertIn("todos", params["properties"])
        todos_schema = params["properties"]["todos"]
        self.assertEqual(todos_schema["type"], "array")
        self.assertIn("items", todos_schema)

        items_schema = todos_schema["items"]
        self.assertEqual(items_schema["type"], "object")
        self.assertIn("properties", items_schema)
        self.assertIn("required", items_schema)

        # Verify no strict / additionalProperties anywhere
        full_json = json.dumps(resp_data)
        self.assertNotIn('"strict"', full_json)
        self.assertNotIn('"additionalProperties"', full_json)


# ═══════════════════════════════════════════════════════════════════════════════
#  10. API Response Parsing Simulation
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPIResponseParsing(unittest.TestCase):
    """Simulate API responses with tool calls and verify our schemas match."""

    def test_simulated_openai_tool_call(self):
        """Verify a simulated OpenAI tool_call response matches our schema."""
        from core.tool_schema import TOOL_SCHEMAS

        # Simulate what OpenAI returns for a todo_write call
        tool_call_response = {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "todo_write",
                "arguments": json.dumps({
                    "todos": [
                        {"content": "Write tests", "activeForm": "Writing tests", "status": "pending"},
                        {"content": "Run tests", "activeForm": "Running tests", "status": "pending"},
                    ]
                }),
            },
        }

        # Verify the function name exists in our schemas
        self.assertIn(tool_call_response["function"]["name"], TOOL_SCHEMAS)

        # Verify the arguments match the schema
        args = json.loads(tool_call_response["function"]["arguments"])
        self.assertIn("todos", args)
        self.assertIsInstance(args["todos"], list)
        for todo in args["todos"]:
            self.assertIn("content", todo)
            self.assertIn("activeForm", todo)
            self.assertIn("status", todo)

    def test_simulated_openai_tool_call_with_optional_args(self):
        """Verify tool call with optional args (not all fields required)."""
        from core.tool_schema import TOOL_SCHEMAS

        # todo_update: only index and status are required
        tool_call = {
            "id": "call_xyz",
            "type": "function",
            "function": {
                "name": "todo_update",
                "arguments": json.dumps({
                    "index": 1,
                    "status": "in_progress",
                    # reason, content, detail are optional — omitted
                }),
            },
        }

        schema = TOOL_SCHEMAS["todo_update"]
        required = schema["function"]["parameters"]["required"]
        self.assertEqual(required, ["index", "status"])

        args = json.loads(tool_call["function"]["arguments"])
        for field in required:
            self.assertIn(field, args)

    def test_simulated_glm_tool_call(self):
        """GLM returns the same format for tool calls."""
        from core.tool_schema import TOOL_SCHEMAS

        tool_call = {
            "id": "call_glm_123",
            "type": "function",
            "function": {
                "name": "todo_add",
                "arguments": json.dumps({
                    "content": "New task",
                    "priority": "high",
                }),
            },
        }

        schema = TOOL_SCHEMAS["todo_add"]
        self.assertIn(tool_call["function"]["name"], TOOL_SCHEMAS)

        # content is required, priority is optional
        required = schema["function"]["parameters"]["required"]
        self.assertIn("content", required)
        self.assertNotIn("priority", required)


# ═══════════════════════════════════════════════════════════════════════════════
#  11. Todo Tools Schema Completeness
# ═══════════════════════════════════════════════════════════════════════════════

class TestTodoToolsSchemasComplete(unittest.TestCase):
    """Verify all 5 todo tools have correct and complete schemas."""

    @classmethod
    def setUpClass(cls):
        from core.tool_schema import TOOL_SCHEMAS
        cls.todo_schemas = {
            name: TOOL_SCHEMAS[name]
            for name in ["todo_write", "todo_update", "todo_add", "todo_remove", "todo_status"]
        }

    def test_all_five_todo_tools_exist(self):
        """All 5 todo tools must have schemas."""
        self.assertEqual(len(self.todo_schemas), 5)
        for name in ["todo_write", "todo_update", "todo_add", "todo_remove", "todo_status"]:
            self.assertIn(name, self.todo_schemas)

    def test_todo_update_status_enum_values(self):
        """todo_update status must include all valid states."""
        schema = self.todo_schemas["todo_update"]
        status_prop = schema["function"]["parameters"]["properties"]["status"]
        enum_values = status_prop["enum"]
        self.assertIn("pending", enum_values)
        self.assertIn("in_progress", enum_values)
        self.assertIn("completed", enum_values)
        self.assertIn("approved", enum_values)
        self.assertIn("rejected", enum_values)

    def test_todo_remove_has_only_index(self):
        """todo_remove should only require index."""
        schema = self.todo_schemas["todo_remove"]
        props = schema["function"]["parameters"]["properties"]
        self.assertIn("index", props)
        self.assertEqual(len(props), 1)
        self.assertEqual(schema["function"]["parameters"]["required"], ["index"])

    def test_todo_status_has_no_params(self):
        """todo_status should have empty parameters."""
        schema = self.todo_schemas["todo_status"]
        params = schema["function"]["parameters"]
        self.assertEqual(params["properties"], {})
        self.assertEqual(params["required"], [])

    def test_all_todo_tools_json_serializable(self):
        """All todo tools must serialize to JSON."""
        for name, schema in self.todo_schemas.items():
            json.dumps(schema)

    def test_all_todo_tools_in_responses_api_format(self):
        """All todo tools must convert cleanly to Responses API format."""
        from core.tool_schema import get_tool_schemas
        from src.llm_client import _build_responses_request

        tools = get_tool_schemas(["todo_write", "todo_update", "todo_add", "todo_remove", "todo_status"])
        chat_data = {
            "model": "gpt-5.3-codex",
            "messages": [],
            "tools": tools,
        }
        resp_data = _build_responses_request(chat_data, "gpt-5.3-codex")
        self.assertEqual(len(resp_data["tools"]), 5)


class TestReasoningParameter(unittest.TestCase):
    """Test that reasoning parameter is correctly added to Responses API requests."""

    def test_gpt51_has_reasoning_param(self):
        """GPT-5.1 request should include reasoning parameter."""
        from src.llm_client import _build_responses_request

        data = {
            "model": "gpt-5.1",
            "messages": [{"role": "user", "content": "test"}],
            "stream": True,
        }
        resp_data = _build_responses_request(data, "gpt-5.1")
        self.assertIn("reasoning", resp_data)
        self.assertIn("effort", resp_data["reasoning"])
        self.assertIn("summary", resp_data["reasoning"])
        self.assertEqual(resp_data["reasoning"]["summary"], "auto")

    def test_gpt51_codex_has_reasoning(self):
        """GPT-5.1-codex has reasoning (all GPT-5.x models support it)."""
        from src.llm_client import _build_responses_request

        data = {
            "model": "gpt-5.1-codex",
            "messages": [{"role": "user", "content": "test"}],
            "stream": True,
        }
        resp_data = _build_responses_request(data, "gpt-5.1-codex")
        self.assertIn("reasoning", resp_data)

    def test_gpt53_codex_has_reasoning(self):
        """GPT-5.3-codex has reasoning."""
        from src.llm_client import _build_responses_request

        data = {
            "model": "gpt-5.3-codex",
            "messages": [{"role": "user", "content": "test"}],
            "stream": True,
        }
        resp_data = _build_responses_request(data, "gpt-5.3-codex")
        self.assertIn("reasoning", resp_data)

    def test_o3_has_reasoning(self):
        """o3 model should have reasoning parameter."""
        from src.llm_client import _build_responses_request

        data = {
            "model": "o3",
            "messages": [{"role": "user", "content": "test"}],
            "stream": True,
        }
        resp_data = _build_responses_request(data, "o3")
        self.assertIn("reasoning", resp_data)

    def test_o1_has_reasoning(self):
        """o1 model should have reasoning parameter."""
        from src.llm_client import _build_responses_request

        data = {
            "model": "o1",
            "messages": [{"role": "user", "content": "test"}],
            "stream": True,
        }
        resp_data = _build_responses_request(data, "o1")
        self.assertIn("reasoning", resp_data)

    def test_gpt4o_no_reasoning(self):
        """GPT-4o should NOT have reasoning parameter."""
        from src.llm_client import _build_responses_request

        data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "test"}],
            "stream": True,
        }
        resp_data = _build_responses_request(data, "gpt-4o")
        self.assertNotIn("reasoning", resp_data)

    def test_reasoning_mode_config_controls_effort_level(self):
        """REASONING_MODE config controls effort level."""
        from src.llm_client import _build_responses_request

        for effort in ("low", "medium", "high"):
            with patch('src.llm_client.config') as mock_config:
                mock_config.REASONING_MODE = effort
                mock_config.REASONING_EFFORT = effort
                mock_config.RESPONSES_REASONING_SUMMARY = True
                data = {
                    "model": "gpt-5.1",
                    "messages": [{"role": "user", "content": "test"}],
                    "stream": True,
                }
                resp_data = _build_responses_request(data, "gpt-5.1")
                self.assertEqual(resp_data["reasoning"]["effort"], effort)
                self.assertEqual(resp_data["reasoning"]["summary"], "auto")

    def test_reasoning_mode_off_omits_reasoning_param(self):
        """REASONING_MODE=off should omit the reasoning field entirely."""
        from src.llm_client import _build_responses_request

        with patch('src.llm_client.config') as mock_config:
            mock_config.REASONING_MODE = "off"
            mock_config.REASONING_EFFORT = "off"
            mock_config.RESPONSES_REASONING_SUMMARY = True
            data = {
                "model": "gpt-5.1",
                "messages": [{"role": "user", "content": "test"}],
                "stream": True,
            }
            resp_data = _build_responses_request(data, "gpt-5.1")
            self.assertNotIn("reasoning", resp_data)

    def test_reasoning_summary_can_be_disabled(self):
        """RESPONSES_REASONING_SUMMARY=false should omit summary:auto."""
        from src.llm_client import _build_responses_request

        with patch('src.llm_client.config') as mock_config:
            mock_config.REASONING_MODE = "medium"
            mock_config.REASONING_EFFORT = "medium"
            mock_config.RESPONSES_REASONING_SUMMARY = False
            data = {
                "model": "gpt-5.1",
                "messages": [{"role": "user", "content": "test"}],
                "stream": True,
                "base_url": "https://openrouter.ai/api/v1/responses",
            }
            resp_data = _build_responses_request(data, "gpt-5.1")
            self.assertEqual(resp_data["reasoning"]["effort"], "medium")
            self.assertNotIn("summary", resp_data["reasoning"])

    def test_openrouter_also_gets_summary_when_enabled(self):
        """Summary:auto should be sent to compatible providers when enabled."""
        from src.llm_client import _build_responses_request

        with patch('src.llm_client.config') as mock_config:
            mock_config.REASONING_MODE = "medium"
            mock_config.REASONING_EFFORT = "medium"
            mock_config.RESPONSES_REASONING_SUMMARY = True
            data = {
                "model": "gpt-5.1",
                "messages": [{"role": "user", "content": "test"}],
                "stream": True,
                "base_url": "https://openrouter.ai/api/v1/responses",
            }
            resp_data = _build_responses_request(data, "gpt-5.1")
            self.assertEqual(resp_data["reasoning"]["summary"], "auto")

    def test_reasoning_param_serializable(self):
        """Reasoning parameter must be JSON serializable."""
        from src.llm_client import _build_responses_request

        data = {
            "model": "gpt-5.1",
            "messages": [{"role": "user", "content": "test"}],
            "stream": True,
        }
        resp_data = _build_responses_request(data, "gpt-5.1")
        json_str = json.dumps(resp_data)
        self.assertIn('"reasoning"', json_str)
        self.assertIn('"effort"', json_str)

    def test_is_reasoning_model_for_name(self):
         """_is_reasoning_model_for_name correctly identifies reasoning models."""
         from src.llm_client import _is_reasoning_model_for_name

         # Should be reasoning models (all GPT-5.x including codex)
         for name in ["gpt-5.1", "GPT-5.1", "gpt-5.1-codex", "gpt-5.3-codex",
                       "o1", "o3-mini", "o4-mini",
                       "glm-5.1", "deepseek-v3", "qwq-32b", "deepseek-r1"]:
             self.assertTrue(_is_reasoning_model_for_name(name),
                           f"{name} should be a reasoning model")

         # Should NOT be reasoning models
         for name in ["gpt-4o", "gpt-4o-mini", ""]:
             self.assertFalse(_is_reasoning_model_for_name(name),
                            f"{name} should NOT be a reasoning model")


if __name__ == "__main__":
    unittest.main(verbosity=2)
