import json

from core.config import Settings, default_settings
from core.jarvis import _format_message, get_ai_agents
from core.logging import logging
from core.tool import Tool


class _Request:
    VALID_TYPES = ["CONVERSATION", "FUNCTION"]
    def __init__(self, type_="CONVERSATION", data_="") -> None:
        if type_ not in _Request.VALID_TYPES:
            type_ = "CONVERSATION"
        self.type_ = type_
        self.data_ = data_

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
