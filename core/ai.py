import json
from openai import OpenAI
from typing import Callable

def _format_message(message, role='user'):
    return {
        'role': role,
        'content' : message
    }

class Enigma:
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
