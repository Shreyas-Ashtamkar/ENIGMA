# Constants for E.N.I.G.M.A application

# Conversation context window size
CONVERSATION_CONTEXT_WINDOW = 3

# Task processing markers
TASK_PREFIX = "Do this - "
NO_TASK_MARKER = "NO_SPECIFIC_TASK"

# Model names
MODEL_NAMES = {
    'summary': 'phi3',
    'tool': 'mistral', 
    'conversation': 'llama3'
}

# Temperature settings
TEMPERATURES = {
    'summary': 0,
    'tool': 0,
    'conversation': 0
}

# Retry configuration
MAX_RETRY_ATTEMPTS = 2

# Streamlit configuration
STREAMLIT_PAGE_TITLE = "E.N.I.G.M.A"
STREAMLIT_LAYOUT = "centered"