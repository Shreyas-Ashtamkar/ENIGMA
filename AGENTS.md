# AGENTS.md: E.N.I.G.M.A Development Guide

## Quick Start

**Run the app:**
```bash
streamlit run main.py
```

**External dependency (critical):**
- Ollama must be running locally with three models pre-downloaded:
  - `phi3` — request summarization
  - `mistral` — function/tool calling
  - `llama3` — conversation responses

If Ollama is not running, the app will hang or crash silently.

## Architecture

**Entry points:**
- `main.py` — Streamlit UI (chat interface, session state management)
- `enigma.py` — Core orchestration; defines `process(conversation, retry=0, stream=False)` function

**Request processing pipeline (in `enigma.py`):**
1. `_get_summary()` → phi3 analyzes last 3 messages, returns "Do this - {task}" or "NO_SPECIFIC_TASK"
2. `_get_request()` → Classifies as FUNCTION or CONVERSATION
3. If FUNCTION: `_get_tool()` → mistral selects tool + parameters (JSON)
4. If FUNCTION: `_run_tool()` → Executes from Tool registry
5. `_response_conversation()` or `_continue_conversation()` → llama3 formats output to user-friendly text

**Message format (throughout pipeline):**
```python
{'role': 'user' | 'assistant' | 'system', 'content': str}
```

## Configuration & Tools

**Debug/runtime config** (`configs/config.py`):
- `DEBUG = True/False` — Toggle all debug output
- `VERBOSE = 0-4` — Verbosity levels; controls `print1`–`print4` output
- `MAX_RETRY = 2` — Retry attempts on pipeline failure

**Available tools** (registered in `configs/config.py`; implementations in `configs/tools.py` except `show_toolbox` currently in `configs/config.py` — will be moved to tools.py per repo plan):
- `show_toolbox` — Lists chatbot capabilities
- `conversation` — Routes to llama3 for conversational response
- `error` — Error message fallback
- `get_weather_data` — Mock weather API (hardcoded)
- `get_time_data` — Mock time API (hardcoded)
- `generate_image` — Uses Pollinations API

**Adding new tools:**
```python
# In configs/config.py:
Tool.create(
    exec=my_function,
    fname="tool_name",
    description="What it does",
    param1=Tool.parameter(type_="string", description="...", required=True)
)
```

## Common Patterns & Gotchas

**Tool invocation flow:**
- mistral returns JSON: `{"tool": "tool_name", "tool_kwargs": {...}}`
- Tool executed via `Tool.get(fname).exec(**kwargs)`
- Tool output passed to llama3 for human-friendly formatting
- If tool selection fails, falls back to `error` tool

**LLM interaction:**
- All models accessed via `ollama.chat()` in `utils/ai.py` → `_AI` class
- Each `_AI` instance has `response_tester` (validates format before returning)
- Failed validation → returns `default_response`
- Ensure Ollama models are downloaded before first run

**Conversation history:**
- Last 3 messages used for summarization (prevents context window overflow)
- Full history stored in Streamlit `session_state`
- Message format strictly enforced via `_format_message()`

**System prompts:**
- All stored in `utils/system_prompts.py` → `SYSTEM_PROMPT` dict
- Prompts are injected as "system" role message in chat history
- Tool registry injected into mistral prompt via `.format(tool_box=Tool.box())`

## Testing & Debugging

**Sample conversations:**
- `sample_conversations.py` contains test message arrays for manual testing

**Enable verbose output:**
```python
# In configs/config.py:
DEBUG = True
VERBOSE = 4  # Maximum detail
```

**Check Ollama:**
```bash
ollama list          # Verify models are downloaded
ollama serve         # Start Ollama (usually runs as daemon)
```

## Key Code References

- Core pipeline: `enigma.py:process()`
- AI wrapper: `utils/ai.py:_AI` class
- Tool registry: `utils/Tool.py:Tool` class
- UI state: `utils/gui.py:init_chat()`, `get_messages()`, `new_message()`
- System prompts: `utils/system_prompts.py:SYSTEM_PROMPT`
- Model config: `configs/config.py:AI` namespace
