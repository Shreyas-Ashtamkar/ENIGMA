from types import SimpleNamespace
from utils.ai import _AI, _Request, _format_message
from utils.system_prompts import SYSTEM_PROMPT
from utils.Tool import Tool

from configs.settings import DEBUG, VERBOSE, MAX_RETRY
from configs.logging import print1, print2, print3, print4, cls
from configs.registry import register_tools, show_toolbox
from configs.tools import (
    hint_conversation,
    hint_error,
    get_weather_data,
    get_time_data,
    generate_image
)
from configs.constants import (
    CONVERSATION_CONTEXT_WINDOW,
    TASK_PREFIX,
    NO_TASK_MARKER,
    MAX_RETRY_ATTEMPTS
)

AI = SimpleNamespace(
    conversation=_AI(
        model="llama3",
        prompt=SYSTEM_PROMPT["CONVERSATION"],
        default_response="Hey sorry can you elaborate a bit more?"
    ),
    summary=_AI(
        model="phi3",
        prompt=SYSTEM_PROMPT["SUMMARY"],
        default_response="NO_SPECIFIC_TASK",
        response_tester=lambda resp: ("Do this -" in resp),
        options={
            'temperature': 0
        }
    ),
    tool=_AI(
        model="mistral",
        prompt=SYSTEM_PROMPT["FUNCTION"].format(tool_call_format=Tool.CALL_FORMAT, tool_box=Tool.box()),
        default_response="""{"tool":"conversation"}""",
        default_error="""{"tool":"error", "tool_kwargs":"I don't have the ability to do that yet."}""",
        response_tester=lambda resp: resp[0] == "{" and resp[-1] == "}",
        options={
            'temperature': 0
        }
    ),
    responder=_AI(
        model="llama3",
        prompt=SYSTEM_PROMPT["RESPONDER"],
        default_response="I'm sorry there's some internal errors, can we please chat later?"
    ),
)

register_tools()