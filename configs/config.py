from utils.Tool import Tool
from utils.ai import _AI
from types import SimpleNamespace
from utils.system_prompts import SYSTEM_PROMPT
from configs.tools import (
    hint_conversation,
    hint_error,
    get_weather_data,
    get_time_data,
    generate_image
)
from os import system

DEBUG   = True
VERBOSE = 3
MAX_RETRY = 2

dummy_print = lambda *y, **z: ""
print1 = print if DEBUG else dummy_print
print2 = print1 if VERBOSE > 1 else dummy_print
print3 = print1 if VERBOSE > 2 else dummy_print
print4 = print1 if VERBOSE > 3 else dummy_print
cls = lambda : system("cls") if DEBUG else dummy_print

def show_toolbox(**kwargs):
    print("CALLED: show_toolbox","\nPASSED :", kwargs)

Tool.create(
    exec  = show_toolbox,
    fname = 'show_toolbox',
    description = "Listing down the capabilities (the toolset) of this chatbot, in a user friendly way"
)

Tool.create(
    exec  = hint_conversation,
    fname = 'conversation',
    description = "Responding with only the topic of the conversation.",
    message = Tool.parameter(type_="string", description="A user-friendly message.")
)

Tool.create(
    exec  = hint_error,
    fname = 'error',
    description = "Responding with an error, with an error message",
    error_message = Tool.parameter(type_="string", description="A user-friendly message notifying the user of the error")
)

Tool.create(
    exec        = get_weather_data,
    fname       = "get_weather_data",
    description = "Getting the weather-temperature data for a location in the chosen unit",
    location    = Tool.parameter(type_='string', description="Location of the data"),
    unit        = Tool.parameter(type_='string', description="Unit of temperature (celsius, fahrenheit). ", required=False)
)

Tool.create(
    exec        = get_time_data,
    fname       = "get_time_data",
    description = "Getting the time data for a location",
    location    = Tool.parameter(type_='string', description="Location of the data")
)

Tool.create(
    exec        = generate_image,
    fname       = "generate_image",
    description = "Create images based on the user-provided prompt.",
    prompt      = Tool.parameter(type_='string', description="The prompt provided by the user on basis of which the image will be created.")
)


AI = SimpleNamespace(
    conversation = _AI(
        model  = "llama3",
        prompt = SYSTEM_PROMPT["CONVERSATION"],
        default_response = "Hey sorry can you elaborate a bit more?"
    ),
    summary = _AI(
        model  = "phi3",
        prompt = SYSTEM_PROMPT["SUMMARY"],
        default_response = "NO_SPECIFIC_TASK",
        response_tester = lambda resp: ("Do this -" in resp),
        options = {
            'temperature' : 0
        }
    ),
    tool = _AI(
        model  = "mistral",
        prompt = SYSTEM_PROMPT["FUNCTION"].format(tool_call_format=Tool.CALL_FORMAT, tool_box=Tool.box()),
        default_response = """{"tool":"conversation"}""",
        default_error    = """{"tool":"error", "tool_kwargs":"I don't have the ability to do that yet."}""",
        response_tester  = lambda resp: resp[0] == "{" and resp[-1] == "}",
        options = {
            'temperature' : 0
        }
    ),
    responder = _AI(
        model  = "llama3",
        prompt = SYSTEM_PROMPT["RESPONDER"],
        default_response = "I'm sorry there's some internal errors, can we please chat later?"
    ),
)
