import json
import os
from types import FunctionType


class Tool:
    _box: dict[str, 'Tool'] = {}

    def __init__(self, fname: str, description: str, exec: FunctionType, **params: dict[str, any]) -> None:
        self.fname           = fname
        self.description     = description
        self.exec            = exec
        self.params          = params

    @staticmethod
    def create(file_path: str) -> 'Tool':
        with open(file_path, 'r') as f:
            data = json.load(f)

        fname = data.get('name')
        data.get('extention') or data.get('extension', 'py')
        data.get('language', 'python')
        code = data.get('code', '')
        data.get('expected output') or data.get('expected_output')
        description = data.get('description', '')

        # Execute the python code to extract the function callable
        local_vars = {}
        exec(code, globals(), local_vars)

        exec_func = local_vars.get(fname)
        if not exec_func:
            # Fallback to any callable in local_vars if not found by name
            callables = [v for k, v in local_vars.items() if callable(v)]
            if callables:
                exec_func = callables[0]
            else:
                raise ValueError(f"No function defined in code for tool {fname}")

        # Parse params
        params = data.get('parameters', {})

        new_tool = Tool(
            fname = fname,
            description = description,
            exec = exec_func,
            **params
        )
        Tool._box[fname] = new_tool
        return new_tool

    @staticmethod
    def get(fname:str) -> 'Tool':
        return Tool._box.get(fname)

    @staticmethod
    def openai_tools() -> list[dict]:
        tools_list = []
        for name, tool in Tool._box.items():
            properties = {}
            required = []
            for param_name, param_details in tool.params.items():
                properties[param_name] = {
                    "type": param_details.get("type", "string"),
                    "description": param_details.get("description", "")
                }
                if param_details.get("required", True):
                    required.append(param_name)

            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool.fname,
                    "description": tool.description,
                }
            }
            if properties:
                tool_schema["function"]["parameters"] = {
                    "type": "object",
                    "properties": properties,
                }
                if required:
                    tool_schema["function"]["parameters"]["required"] = required
            else:
                tool_schema["function"]["parameters"] = {
                    "type": "object",
                    "properties": {}
                }
            tools_list.append(tool_schema)
        return tools_list

# Base directory for tools and dynamic tool compilation
TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')

if os.path.exists(TOOLS_DIR):
    for filename in os.listdir(TOOLS_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(TOOLS_DIR, filename)
            Tool.create(file_path)
