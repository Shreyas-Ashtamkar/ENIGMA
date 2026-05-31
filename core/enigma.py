import json
import os
from types import FunctionType, SimpleNamespace
from typing import Callable

from openai import OpenAI

from core.config import Settings, default_settings
from core.logging import logging


# ==========================================
# Tool
# ==========================================
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

# ==========================================
# AI Base Wrapper
# ==========================================
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

class _Request:
    VALID_TYPES = ["CONVERSATION", "FUNCTION"]
    def __init__(self, type_="CONVERSATION", data_="") -> None:
        if type_ not in _Request.VALID_TYPES:
            type_ = "CONVERSATION"
        self.type_ = type_
        self.data_ = data_

# ==========================================
# Dynamic Loaders
# ==========================================
# Base directory for tools and dynamic tool compilation
TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools')

if os.path.exists(TOOLS_DIR):
    for filename in os.listdir(TOOLS_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(TOOLS_DIR, filename)
            Tool.create(file_path)

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

# ==========================================
# Orchestrator
# ==========================================
class Enigma:
    def __init__(self, settings: Settings = None, ai_agents = None):
        self.settings = settings or default_settings
        self.ai = ai_agents or get_ai_agents(self.settings)

    def recent_request_summarizer(self, conversation: list[dict[str, str]]) -> str:
        conversation_str = self._stringify_conversation(conversation)
        if len(conversation_str) < 1:
            return "NO_SPECIFIC_TASK"
        summary = self.ai.summary.simple_chat(conversation_str).split("\n")[0].strip()
        logging.info("\n----------get_conversation_summary called----------")
        logging.debug(summary)
        return summary

    def _stringify_conversation(self, conversation: list[dict[str, str]]) -> str:
        conversation = conversation[::-1][:3][::-1]
        string_conversation = ""
        for message in conversation:
            role, content = message['role'], message['content']
            if role == "system": continue
            string_conversation += f"\n{role}:{content}\n"

        logging.debug(f"\n_stringify_conversation :\n{string_conversation}")
        return string_conversation.strip()

    def request_type_identifier(self, summary: str) -> _Request:
        request = _Request(type_="CONVERSATION", data_="")

        if "NO_SPECIFIC_TASK" in summary:
            request.type_ = "CONVERSATION"
        elif "Do this - " in summary:
            request.type_ = "FUNCTION"
            request.data_ = summary.split("\n")[0][10:]

        logging.info("\n------------request_type_identifier called-------------")
        logging.debug(f"Type:{request.type_} \nData:'{request.data_}'")
        return request

    def function_parser(self, task: str):
        tool_details = self.ai.tool.default_response
        try:
            tool_details:dict = json.loads(self.ai.tool.simple_chat(task))
        except Exception as e:
            print(e)
        logging.info("\n------------function_parser called-------------")
        logging.debug(tool_details)
        return tool_details

    def function_executer(self, tool_details: dict):
        tool_name:str    = tool_details.get('tool')
        tool_kwargs:dict = tool_details.get('tool_kwargs') or {}
        tool = Tool.get(tool_name)
        logging.info("\n------------function_executer called-------------")
        if not tool:
            return f"Error: Tool '{tool_name}' not found."
        tool_response = tool.exec(**tool_kwargs)
        logging.debug(tool_response)
        return tool_response

    def chatter_box(self, conversation: list[dict[str, str]], summary: str = "", tool_response: str = "") -> str:
        logging.info("\n------------chatter_box called-------------")
        if tool_response:
            tool_conversation = [
                _format_message(f"{summary}", role='user'),
                _format_message(f"{tool_response}", role='user')
            ]
            chat_response = self.ai.responder.chat(tool_conversation)
        else:
            if len(conversation) > 0:
                chat_response = self.ai.conversation.chat(conversation)
            else:
                chat_response = self.ai.conversation.chat([_format_message("Introduce yourself in a fun way in a single sentence.", "user")])
        logging.debug(chat_response)
        return chat_response

    def process(self, conversation: list[dict[str, str]], retry=0, stream=False):
        try:
            summary = self.recent_request_summarizer(conversation)
            request = self.request_type_identifier(summary)
            chat_response = ""

            if request.type_ == "FUNCTION":
                tool_details = self.function_parser(request.data_)
                tool_response = self.function_executer(tool_details)
                if isinstance(tool_response, str) and "IMAGE : " in tool_response:
                    chat_response = tool_response[8:]
                else:
                    chat_response = self.chatter_box(conversation, summary=summary, tool_response=tool_response)
            else:
                chat_response = self.chatter_box(conversation)

        except Exception as e:
            if retry < self.settings.MAX_RETRY:
                print("------------- Retry -------------")
                chat_response = self.process(conversation, retry+1)
            else:
                chat_response = self.ai.responder.chat([_format_message(str(e))])
        return chat_response

# Instantiate default enigma instance for backward compatibility
enigma = Enigma()

if __name__ == "__main__":
    chat_response = enigma.process([
        {
            'role' : 'user',
            'content':"Generate an image of a playful baby elephant."
        },
    ])
    print(chat_response)
