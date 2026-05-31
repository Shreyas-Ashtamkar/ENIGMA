import json
import os
from types import SimpleNamespace
from typing import Callable

from openai import OpenAI

from core.config import Settings
from core.tool import Tool


def _format_message(message, role='user'):
    return {
        'role': role,
        'content' : message
    }

class Jarvis:
    def __init__(self, model, prompt, json_response=False, client=None, **kwargs) -> None:
        self.model:str                  = model
        self.prompt:str                 = prompt
        self.default_response:str       = ""
        self.json_response:bool         = json_response
        self.response_tester:Callable   = lambda x: True
        self.options:dict               = {}
        self.client                     = client

        for arg, value in kwargs.items():
            if arg == "default_response":
                self.default_response = value
            elif arg == "response_tester":
                self.response_tester = value
            elif arg == 'options':
                self.options = value

    def chat(self, message_history:list):
        '''Send a message history to llm and recieve response'''

        message_history = list(filter(lambda x: x['role']!='system', message_history))

        messages = [_format_message(self.prompt, 'system')] + message_history

        kwargs = {}
        if self.json_response:
            kwargs['response_format'] = {"type": "json_object"}
        kwargs.update(self.options)

        if self.client:
            response = self.client.chat.completions.create(
                model    = self.model,
                messages = messages,
                **kwargs
            )
        else:
            client = OpenAI()
            response = client.chat.completions.create(
                model    = self.model,
                messages = messages,
                **kwargs
            )

        message = response.choices[0].message
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            try:
                args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            except Exception:
                args = {}
            assistant_response = json.dumps({
                "tool": tool_call.function.name,
                "tool_kwargs": args
            })
        else:
            assistant_response = message.content.strip() if message.content else ""

        try:
            if not self.response_tester(assistant_response):
                assistant_response = self.default_response
        except Exception as e:
            print("CANNOT TEST :", e)
            assistant_response = self.default_response

        return assistant_response

    def simple_chat(self, message:str):
        '''Send a single message to llm, and recieve response.'''

        return self.chat([_format_message(message)])

# Dynamic Prompt loading
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prompts')
SYSTEM_PROMPT = {}
if os.path.exists(PROMPTS_DIR):
    for filename in os.listdir(PROMPTS_DIR):
        if filename.endswith('.md'):
            key = filename[:-3].upper()
            file_path = os.path.join(PROMPTS_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                SYSTEM_PROMPT[key] = f.read().strip()

def get_ai_agents(settings: Settings) -> SimpleNamespace:
    client = OpenAI(base_url=settings.API_BASE, api_key=settings.API_KEY)
    model = settings.MODEL_ID

    return SimpleNamespace(
        conversation = Jarvis(
            model  = model,
            prompt = SYSTEM_PROMPT.get("CONVERSATION", ""),
            default_response = "Hey sorry can you elaborate a bit more?",
            client = client
        ),
        summary = Jarvis(
            model  = model,
            prompt = SYSTEM_PROMPT.get("SUMMARY", ""),
            default_response = "NO_SPECIFIC_TASK",
            response_tester = lambda resp: ("Do this -" in resp),
            options = {
                'temperature' : 0
            },
            client = client
        ),
        tool = Jarvis(
            model  = model,
            prompt = SYSTEM_PROMPT.get("FUNCTION", ""),
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
        responder = Jarvis(
            model  = model,
            prompt = SYSTEM_PROMPT.get("RESPONDER", ""),
            default_response = "I'm sorry there's some internal errors, can we please chat later?",
            client = client
        ),
    )
