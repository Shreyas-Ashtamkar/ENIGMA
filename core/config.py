import os
from openai import OpenAI
from types import SimpleNamespace
from core.settings import Settings, default_settings
from core.Tool import Tool
from core.ai import Enigma
from core.system_prompts import SYSTEM_PROMPT

# Base directory for tools
TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')

# Load all JSON tools
if os.path.exists(TOOLS_DIR):
    for filename in os.listdir(TOOLS_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(TOOLS_DIR, filename)
            Tool.create(file_path)

def get_ai_agents(settings: Settings) -> SimpleNamespace:
    client = OpenAI(base_url=settings.API_BASE, api_key=settings.API_KEY)
    model = settings.MODEL_ID
    
    return SimpleNamespace(
        conversation = Enigma(
            model  = model,
            prompt = SYSTEM_PROMPT["CONVERSATION"],
            default_response = "Hey sorry can you elaborate a bit more?",
            client = client
        ),
        summary = Enigma(
            model  = model,
            prompt = SYSTEM_PROMPT["SUMMARY"],
            default_response = "NO_SPECIFIC_TASK",
            response_tester = lambda resp: ("Do this -" in resp),
            options = {
                'temperature' : 0
            },
            client = client
        ),
        tool = Enigma(
            model  = model,
            prompt = SYSTEM_PROMPT["FUNCTION"],
            default_response = """{"tool":"conversation"}""",
            default_error    = """{"tool":"error", "tool_kwargs":{"error_message": "I don't have the ability to do that yet."}}""",
            response_tester  = lambda resp: resp[0] == "{" and resp[-1] == "}",
            options = {
                'temperature' : 0,
                'tools': Tool.openai_tools(),
                'tool_choice': 'required'
            },
            client = client
        ),
        responder = Enigma(
            model  = model,
            prompt = SYSTEM_PROMPT["RESPONDER"],
            default_response = "I'm sorry there's some internal errors, can we please chat later?",
            client = client
        ),
    )

AI = get_ai_agents(default_settings)
