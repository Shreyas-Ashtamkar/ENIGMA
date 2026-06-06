import os

from openai import OpenAI

from core.config import Settings, default_settings
from core.logging import logging
from core.slm import SLM
from core.tool import Tool


def _load_prompt(filename: str) -> str:
    """Load a prompt file from the prompts/ directory."""
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prompts')
    filepath = os.path.join(prompts_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return ""


class Enigma:
    """Orchestrator — enables small language models to perform tool calling
    through a cooperative multi-stage pipeline.
    
    Stage 1: Intent Classification  (TASK or CONVERSATION)
    Stage 2: Tool Selection         (pick from registered tools)
    Stage 3: Parameter Extraction   (extract key=value pairs)
    Stage 4: Tool Execution         (run the tool — no LLM)
    Stage 5: Response Generation    (natural language reply)
    """

    def __init__(self, settings: Settings = None):
        self.settings = settings or default_settings
        client = OpenAI(base_url=self.settings.API_BASE, api_key=self.settings.API_KEY)

        # Stage 1 — Intent Classifier (fast, low-token)
        self.intent_classifier = SLM(
            model=self.settings.INTENT_MODEL,
            system_prompt=_load_prompt('intent.md'),
            client=client,
            temperature=0,
            max_tokens=20,
        )

        # Stage 2 — Tool Selector (fast, low-token)
        self.tool_selector = SLM(
            model=self.settings.TOOL_SELECT_MODEL,
            system_prompt=_load_prompt('tool_select.md'),
            client=client,
            temperature=0,
            max_tokens=50,
        )

        # Stage 3 — Parameter Extractor
        self.param_extractor = SLM(
            model=self.settings.PARAM_EXTRACT_MODEL,
            system_prompt=_load_prompt('param_extract.md'),
            client=client,
            temperature=0,
            max_tokens=256,
        )

        # Stage 5 — Response Generator (conversational quality)
        self.responder = SLM(
            model=self.settings.RESPONSE_MODEL,
            system_prompt=_load_prompt('response.md'),
            client=client,
            temperature=0.7,
            max_tokens=512,
        )

    # ── Helpers ──

    def _get_last_user_message(self, conversation: list[dict]) -> str:
        """Extract the most recent user message from conversation."""
        for msg in reversed(conversation):
            if msg['role'] == 'user':
                return msg['content']
        return ""

    def _stringify_recent(self, conversation: list[dict], n: int = 3) -> str:
        """Stringify the last n user/assistant messages for context."""
        recent = conversation[-n:]
        lines = []
        for msg in recent:
            if msg['role'] in ('user', 'assistant'):
                lines.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(lines)

    # ── Stage 1: Intent Classification ──

    def classify_intent(self, conversation: list[dict]) -> str:
        """Classify the user's intent as TASK or CONVERSATION."""
        context = self._stringify_recent(conversation)
        response = self.intent_classifier.ask(context)

        logging.info(f"[INTENT] {response}")

        if "TASK" in response.strip().upper():
            return "TASK"
        return "CONVERSATION"

    # ── Stage 2: Tool Selection ──

    def select_tool(self, user_message: str) -> str | None:
        """Select the appropriate tool for the user's request."""
        prompt = Tool.build_selection_prompt(user_message)
        if prompt is None:
            return None

        response = self.tool_selector.ask(prompt)

        logging.info(f"[TOOL_SELECT] {response}")

        # Parse: take the first word, strip punctuation
        tool_name = response.strip().lower().strip('"\'.!,').split('\n')[0].split(' ')[0]

        if tool_name == 'none' or Tool.get(tool_name) is None:
            return None
        return tool_name

    # ── Stage 3: Parameter Extraction ──

    def extract_parameters(self, user_message: str, tool: Tool) -> dict:
        """Extract parameter values from the user's message for the given tool."""
        if not tool.params:
            return {}

        prompt = Tool.build_extraction_prompt(user_message, tool)
        response = self.param_extractor.ask(prompt)

        logging.info(f"[PARAM_EXTRACT] {response}")

        # Parse key=value lines
        params = {}
        for line in response.strip().split('\n'):
            line = line.strip().lstrip('- ')
            if '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()
            if value and value != '__MISSING__':
                params[key] = value

        return params

    # ── Stage 5: Response Generation ──

    def generate_response(self, conversation: list[dict], tool_context: str = None) -> str:
        """Generate a natural language response, optionally incorporating tool results."""
        # Build clean message list (only user/assistant roles)
        messages = []
        for msg in conversation:
            if msg['role'] in ('user', 'assistant'):
                messages.append({'role': msg['role'], 'content': msg['content']})

        # Inject tool context as a system-like user message
        if tool_context:
            messages.append({'role': 'user', 'content': tool_context})

        response = self.responder.complete(messages)
        logging.debug(f"[RESPONSE] {response}")
        return response

    # ── Main Pipeline ──

    def process(self, conversation: list[dict]) -> str:
        """Process a conversation through the full ENIGMA pipeline."""
        try:
            # Stage 1: Intent Classification
            intent = self.classify_intent(conversation)

            if intent == "CONVERSATION":
                return self.generate_response(conversation)

            # Stage 2: Tool Selection
            user_message = self._get_last_user_message(conversation)
            tool_name = self.select_tool(user_message)

            if tool_name is None:
                # No matching tool — fall back to conversation
                return self.generate_response(conversation)

            tool = Tool.get(tool_name)

            # Stage 3: Parameter Extraction
            params = self.extract_parameters(user_message, tool)

            # Validate required parameters
            missing = tool.get_missing_required(params)
            if missing:
                missing_desc = ", ".join(missing)
                tool_context = (
                    f"The user asked to use the '{tool_name}' tool, but the following "
                    f"required information is missing: {missing_desc}. "
                    f"Please ask the user to provide the missing details politely."
                )
                return self.generate_response(conversation, tool_context=tool_context)

            # Stage 4: Tool Execution (no LLM)
            logging.info(f"[EXEC] Tool: {tool_name}, Params: {params}")
            result = tool.execute(params)
            logging.info(f"[EXEC] Result: {result}")

            # Handle image results — return markdown directly
            if isinstance(result, str) and result.startswith("IMAGE : "):
                return result[8:]

            # Handle tool errors
            if isinstance(result, str) and result.startswith("TOOL_ERROR:"):
                tool_context = (
                    f"The user asked: \"{user_message}\"\n"
                    f"I tried to use the '{tool_name}' tool but it failed with: {result}\n"
                    f"Please let the user know something went wrong."
                )
                return self.generate_response(conversation, tool_context=tool_context)

            # Stage 5: Response Generation with tool result
            tool_context = (
                f"The user asked: \"{user_message}\"\n"
                f"I used the '{tool_name}' tool and got this result:\n{result}\n"
                f"Please respond to the user with this information in a friendly, concise way."
            )
            return self.generate_response(conversation, tool_context=tool_context)

        except Exception as e:
            logging.error(f"[PIPELINE_ERROR] {e}")
            return "I'm sorry, I ran into an issue processing your request. Could you try again?"


# Default instance
enigma = Enigma()
