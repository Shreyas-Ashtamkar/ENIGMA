import json
import os


class Tool:
    """Dynamic tool registry — loads tool definitions from JSON files."""

    _registry: dict[str, 'Tool'] = {}

    def __init__(self, name: str, description: str, fn, params: dict, internal: bool = False) -> None:
        self.name = name
        self.description = description
        self.fn = fn
        self.params = params
        self.internal = internal

    @staticmethod
    def create(file_path: str) -> 'Tool':
        """Create a Tool from a JSON definition file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        name = data.get('name')
        code = data.get('code', '')
        description = data.get('description', '')
        internal = data.get('internal', False)

        # Execute the embedded Python code to extract the callable
        local_vars = {}
        exec(code, {}, local_vars)

        fn = local_vars.get(name)
        if not fn:
            callables = [v for v in local_vars.values() if callable(v)]
            if callables:
                fn = callables[0]
            else:
                raise ValueError(f"No function found in tool: {name}")

        params = data.get('parameters', {})

        tool = Tool(name=name, description=description, fn=fn, params=params, internal=internal)
        Tool._registry[name] = tool
        return tool

    @staticmethod
    def get(name: str) -> 'Tool':
        """Get a tool by name."""
        return Tool._registry.get(name)

    @staticmethod
    def list_all() -> list[str]:
        """List all registered tool names."""
        return list(Tool._registry.keys())

    @staticmethod
    def get_selectable_tools() -> list['Tool']:
        """Get all tools available for user-facing selection (excludes internal tools)."""
        return [t for t in Tool._registry.values() if not t.internal]

    def describe_for_selection(self) -> str:
        """One-line description for the tool selector prompt."""
        return f"{self.name} — {self.description}"

    def describe_params_for_extraction(self) -> str:
        """Describe parameters for the parameter extraction prompt."""
        if not self.params:
            return "This tool requires no parameters."

        lines = []
        for param_name, details in self.params.items():
            required = details.get('required', False)
            desc = details.get('description', '')
            req_tag = "(required)" if required else "(optional)"
            lines.append(f"- {param_name} {req_tag}: {desc}")
        return "\n".join(lines)

    def get_missing_required(self, params: dict) -> list[str]:
        """Check which required parameters are missing from the provided params."""
        missing = []
        for param_name, details in self.params.items():
            if details.get('required', False) and param_name not in params:
                missing.append(param_name)
        return missing

    def execute(self, params: dict) -> str:
        """Execute the tool function with the given parameters."""
        try:
            result = self.fn(**params)
            return str(result) if result is not None else ""
        except TypeError as e:
            return f"TOOL_ERROR: Invalid parameters — {e}"
        except Exception as e:
            return f"TOOL_ERROR: {e}"

    @staticmethod
    def build_selection_prompt(user_message: str) -> str:
        """Build the dynamic prompt for Stage 2 (Tool Selection)."""
        tools = Tool.get_selectable_tools()
        if not tools:
            return None

        tool_list = "\n".join(
            f"{i+1}. {t.describe_for_selection()}"
            for i, t in enumerate(tools)
        )

        return (
            f"Available tools:\n{tool_list}\n\n"
            f"If NO tool matches the user's request, respond with: none\n\n"
            f"User's request: \"{user_message}\"\n\n"
            f"Respond with ONLY the tool name or \"none\"."
        )

    @staticmethod
    def build_extraction_prompt(user_message: str, tool: 'Tool') -> str:
        """Build the dynamic prompt for Stage 3 (Parameter Extraction)."""
        param_desc = tool.describe_params_for_extraction()

        return (
            f"Extract the following parameters from the user's message.\n"
            f"For each parameter, write the value on a new line in the format: parameter_name=value\n"
            f"If a parameter's value is not mentioned by the user, write: parameter_name=__MISSING__\n\n"
            f"Parameters to extract:\n{param_desc}\n\n"
            f"User's message: \"{user_message}\"\n\n"
            f"Output:"
        )


# ── Load tools from the tools/ directory at import time ──
TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')

if os.path.exists(TOOLS_DIR):
    for filename in sorted(os.listdir(TOOLS_DIR)):
        if filename.endswith('.json'):
            try:
                Tool.create(os.path.join(TOOLS_DIR, filename))
            except Exception as e:
                print(f"Warning: Failed to load tool {filename}: {e}")
