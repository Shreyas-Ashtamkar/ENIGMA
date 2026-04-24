import json
from utils.ai import _AI, _Request, _format_message
from utils.Tool import Tool
from configs.config import (
    DEBUG,
    VERBOSE,
    MAX_RETRY,
    print1,
    print2,
    print3,
    print4,
    AI
)

def _stringify_conversation(conversation:list):
    conversation = conversation[::-1][:3][::-1]
    string_conversation = ""
    for message in conversation:
        role, content = message['role'], message['content']
        if role == "system": continue
        string_conversation += f"\n{role}:{content}\n"
    
    print3("\n_stringify_conversation :", string_conversation)
    return string_conversation.strip()


def _get_summary(conversation:list[dict[str,str]]=None) -> str:
    conversation = _stringify_conversation(conversation)
    if len(conversation) < 1: return "NO_SPECIFIC_TASK"
    summary:str = AI.summary.simple_chat(conversation).split("\n")[0].strip()
    print2("\n----------_get_summary called----------")
    print3(summary)
    return summary


def _get_request(summary:str) -> _Request:
    request = _Request(type_="CONVERSATION", data_="")
    
    if "NO_SPECIFIC_TASK" in summary:
        request.type_ = "CONVERSATION"
    elif "Do this - " in summary:
        request.type_ = "FUNCTION"
        request.data_ = summary.split("\n")[0][10:]
    
    print2("\n------------_get_request called-------------")
    print3(f"Type:{request.type_} \nData:'{request.data_}'")
    return request
        

def _get_tool(task:str):
    tool_details = AI.tool.default_response
    try:
        tool_details:dict = json.loads(AI.tool.simple_chat(task))
    except Exception as e:
        print(e)
    print2("\n------------_get_tool called-------------")
    print3(tool_details)
    return tool_details


def _run_tool(tool_details:dict):
    tool_name:Tool   = tool_details.get('tool')
    tool_kwargs:dict = tool_details.get('tool_kwargs') or {}
    tool = Tool.get(tool_name)
    print2("\n------------_run_tool called-------------")
    tool_response = tool.exec(**tool_kwargs)
    print3(tool_response)
    return tool_response

def _response_conversation(conversation:list[dict[str:str]]) -> str:
    print2("\n------------_response_conversation called-------------")
    print3(conversation)
    chat_response = AI.responder.chat(conversation)
    print3(chat_response)
    return chat_response

    
def _continue_conversation(conversation:list[dict[str:str]]) -> str:
    print2("\n------------_continue_conversation called-------------")
    chat_response = AI.conversation.chat(conversation)
    print3(chat_response)
    return chat_response


def process(conversation:list[dict[str:str]], retry=0, stream=False):
    try:
        summary = _get_summary(conversation)
        request = _get_request(summary)
        chat_response = ""
        if request.type_ == "FUNCTION":
            # Run the tool
            tool_details  = _get_tool(request.data_)
            tool_response = _run_tool(tool_details)
            if "IMAGE : " in tool_response:
                chat_response = tool_response[8:]
            else:
                tool_conversation = [_format_message(f"{summary}", role='user'), _format_message(f"{tool_response}", role='user')]
                chat_response = _response_conversation(tool_conversation)
        else:
            if len(conversation) > 0:
                chat_response = _continue_conversation(conversation)
            else:
                chat_response = _continue_conversation([_format_message("Introduce yourself in a fun way in a single sentence.", "user")])
    except Exception as e: 
        if retry < MAX_RETRY:
            print("------------- Retry -------------")
            chat_response = process(conversation, retry+1)
        else:
            chat_response = _response_conversation(e.__str__())
    return chat_response


if __name__ == "__main__":
    chat_response = process([
        {
            'role' : 'user',
            'content':"Generate an image of a playful baby elephant."
        },
    ])
    
    print(chat_response)
