from utils.Tool import Tool

def register_tools():
    from configs.config import (
        show_toolbox,
        hint_conversation,
        hint_error,
        get_weather_data,
        get_time_data,
        generate_image
    )

    Tool.create(
        exec=show_toolbox,
        fname='show_toolbox',
        description="Listing down the capabilities (the toolset) of this chatbot, in a user friendly way"
    )

    Tool.create(
        exec=hint_conversation,
        fname='conversation',
        description="Responding with only the topic of the conversation.",
        message=Tool.parameter(type_="string", description="A user-friendly message.")
    )

    Tool.create(
        exec=hint_error,
        fname='error',
        description="Responding with an error, with an error message",
        error_message=Tool.parameter(type_="string", description="A user-friendly message notifying the user of the error")
    )

    Tool.create(
        exec=get_weather_data,
        fname="get_weather_data",
        description="Getting the weather-temperature data for a location in the chosen unit",
        location=Tool.parameter(type_='string', description="Location of the data"),
        unit=Tool.parameter(type_='string', description="Unit of temperature (celsius, fahrenheit). ", required=False)
    )

    Tool.create(
        exec=get_time_data,
        fname="get_time_data",
        description="Getting the time data for a location",
        location=Tool.parameter(type_='string', description="Location of the data")
    )

    Tool.create(
        exec=generate_image,
        fname="generate_image",
        description="Create images based on the user-provided prompt.",
        prompt=Tool.parameter(type_='string', description="The prompt provided by the user on basis of which the image will be created.")
    )

def show_toolbox(**kwargs):
    from configs.logging import print1
    print1("CALLED: show_toolbox", "\nPASSED :", kwargs)