# E.N.I.G.M.A Recommended Project Structure

## Current State Issues
- **Critical**: Circular imports (configs → system_prompts → Tool → config)
- **Critical**: Wildcard imports polluting namespace (`from module import *`)
- **High**: Wrong module organization (Tool in utils, ai in utils, etc.)
- **High**: Mixed configuration with business logic

---

## Recommended Restructure

### Directory Layout

```
E.N.I.G.M.A/
├── enigma/                           # Main package (replaces scattered files)
│   ├── __init__.py                   # Package initialization
│   │
│   ├── core/                         # Core orchestration logic
│   │   ├── __init__.py
│   │   ├── tool.py                   # Rename from utils/Tool.py
│   │   │   - class Tool: Registry and executor for tools
│   │   │   - Handles parameter validation, execution
│   │   │   - Static methods become @classmethod (shared state)
│   │   │
│   │   └── orchestrator.py           # Rename from enigma.py
│   │       - process() main function
│   │       - _get_summary(), _get_request(), _get_tool(), _run_tool()
│   │       - Imports only what it needs (no wildcard)
│   │
│   ├── ai/                           # LLM interaction layer
│   │   ├── __init__.py
│   │   ├── models.py                 # From utils/ai.py
│   │   │   - class _AI: LLM wrapper around Ollama
│   │   │   - chat(), simple_chat() methods
│   │   │   - response_tester validation
│   │   │
│   │   ├── types.py                  # New: Data structures
│   │   │   - class Request (was _Request)
│   │   │   - Message type aliases
│   │   │   - Response structures
│   │   │
│   │   └── prompts.py                # From utils/system_prompts.py
│   │       - SYSTEM_PROMPT dict
│   │       - All LLM prompts centralized
│   │
│   ├── tools/                        # Tool implementations
│   │   ├── __init__.py
│   │   ├── builtin.py                # From configs/tools.py
│   │   │   - hint_conversation()
│   │   │   - hint_error()
│   │   │   - get_weather_data()
│   │   │   - get_time_data()
│   │   │   - generate_image()
│   │   │
│   │   └── registry.py               # New: Tool registration
│   │       - Tool registration isolated from config
│   │       - Keeps config.py clean
│   │
│   ├── ui/                           # User interface layer
│   │   ├── __init__.py
│   │   └── streamlit_app.py          # From gui.py + main.py
│   │       - Streamlit UI code
│   │       - Session state management
│   │       - Page configuration
│   │
│   ├── config/                       # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py               # New: All settings
│   │   │   - DEBUG, VERBOSE, MAX_RETRY
│   │   │   - Model names and temperatures
│   │   │   - Environment variables
│   │   │   - Use pydantic.BaseSettings for validation
│   │   │
│   │   ├── logging.py                # New: Logging setup
│   │   │   - Replace print1-4 with logging
│   │   │   - Logger configuration
│   │   │
│   │   └── exceptions.py             # New: Custom exceptions
│   │       - OllamaConnectionError
│   │       - InvalidToolError
│   │       - ToolExecutionError
│   │
│   └── app.py                        # Single entry point
│       - Initializes Ollama, loads config
│       - Starts Streamlit app
│       - Error handling for startup
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration
│   ├── fixtures/
│   │   ├── __init__.py
│   │   └── conversations.py          # From sample_conversations.py
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_orchestrator.py
│   │   ├── test_tools.py
│   │   └── test_models.py
│   │
│   └── integration/
│       ├── __init__.py
│       └── test_pipeline.py
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md               # System design
│   ├── API.md                        # Tool API reference
│   ├── SETUP.md                      # Development setup
│   └── CONTRIBUTING.md               # Contributing guidelines
│
├── .env.example                      # Environment template
├── .env                              # Local environment (gitignored)
├── .gitignore                        # Already exists
├── pyproject.toml                    # Modern Python packaging (PEP 517/518)
├── setup.py                          # Legacy support (if needed)
├── setup.cfg                         # Setuptools configuration
├── requirements.txt                  # Production dependencies (from pyproject.toml)
├── requirements-dev.txt              # Development dependencies
├── ARCHITECTURE.md                   # System design overview
├── README.md                         # Project overview
└── LICENSE                           # Already exists

```

---

## Import Structure (Fixing Circular Dependencies)

### Before (❌ Broken)
```python
# enigma.py
from configs.config import *  # Wildcard - hides all imports

# configs/config.py
from configs.tools import *   # Wildcard
from utils.system_prompts import SYSTEM_PROMPT  # Creates dependency chain
from utils.Tool import Tool

# utils/system_prompts.py
from utils.Tool import Tool
```

### After (✅ Fixed)
```
enigma/
├── core/
│   ├── orchestrator.py
│   │   from enigma.ai.models import _AI
│   │   from enigma.ai.types import Request
│   │   from enigma.core.tool import Tool
│   │   # Explicit imports only
│   │
│   └── tool.py
│       (No imports from config)
│
├── ai/
│   ├── models.py
│   │   (No config imports)
│   ├── types.py
│   │   (No config imports)
│   └── prompts.py
│       (No other enigma imports)
│
├── tools/
│   ├── builtin.py
│   │   (No config imports)
│   └── registry.py
│       from enigma.core.tool import Tool
│       from enigma.tools.builtin import *  # Only here, isolated
│
└── config/
    ├── settings.py
    │   (Pure data, no imports from enigma)
    ├── logging.py
    │   (Pure setup, minimal imports)
    └── exceptions.py
        (Pure exceptions)
```

---

## Configuration Management (Before vs After)

### Before (❌ Mixed)
```python
# configs/config.py (95 lines)
DEBUG = True                                    # Config
print1 = print if DEBUG else dummy_print       # Debug setup
Tool.create(exec=show_toolbox, ...)            # Tool registration
AI = SimpleNamespace(...)                      # LLM initialization
```

### After (✅ Separated)
```python
# enigma/config/settings.py
DEBUG = True
VERBOSE = 3
MAX_RETRY = 2
MODEL_NAMES = {"summary": "phi3", "tool": "mistral", ...}
TEMPERATURES = {"summary": 0, "tool": 0}
# Pure configuration, no code execution

# enigma/config/logging.py
import logging
logger = logging.getLogger(__name__)
def setup_logging(level=logging.INFO):
    # Logging configuration only

# enigma/tools/registry.py
from enigma.core.tool import Tool
from enigma.tools.builtin import *
# Tool registration isolated

# enigma/core/orchestrator.py (main script initialization)
from enigma.config.settings import DEBUG, AI_CONFIG
from enigma.ai.models import _AI
# Creates AI instances from settings
```

---

## Explicit Imports (Replacing Wildcards)

### enigma/core/orchestrator.py
```python
# BEFORE: from configs.config import *
# AFTER: Explicit imports only

from enigma.core.tool import Tool
from enigma.ai.models import _AI, _Request, _format_message
from enigma.config.settings import DEBUG, VERBOSE, MAX_RETRY, print1, print2, print3, print4
from enigma.config.logging import logger

# Now all symbols are traceable and IDE autocomplete works
```

### enigma/config/registry.py
```python
# BEFORE: from configs.tools import *

# AFTER: Explicit imports
from enigma.tools.builtin import (
    hint_conversation,
    hint_error,
    get_weather_data,
    get_time_data,
    generate_image
)
from enigma.core.tool import Tool

# Tool registration here
Tool.create(exec=hint_conversation, ...)
Tool.create(exec=hint_error, ...)
# etc.
```

---

## Migration Steps

1. **Phase 1: Create new directory structure**
   - Create `enigma/` package with subdirectories
   - Move files: `Tool.py` → `enigma/core/tool.py`, etc.
   - Create new `__init__.py` files

2. **Phase 2: Fix imports (no logic changes)**
   - Replace wildcard imports with explicit imports
   - Update import paths throughout
   - Run tests after each file

3. **Phase 3: Split configuration**
   - Extract settings from `config.py` → `enigma/config/settings.py`
   - Extract logging setup → `enigma/config/logging.py`
   - Move tool registration → `enigma/tools/registry.py`

4. **Phase 4: Modernize packaging**
   - Create `pyproject.toml` (PEP 517/518)
   - Separate dev/prod dependencies
   - Add entry points

5. **Phase 5: Add infrastructure**
   - Add type hints throughout
   - Add docstrings (PEP 257)
   - Add custom exceptions
   - Add pytest tests

---

## Benefits of New Structure

| Issue | Before | After |
|-------|--------|-------|
| **Circular imports** | Tangled dependency chain | Linear imports, clear hierarchy |
| **Namespace pollution** | Wildcard imports hide symbols | Explicit imports, IDE works |
| **Configuration location** | Mixed in config.py | Centralized in `enigma/config/` |
| **Tool registration** | In config.py | Isolated in `enigma/tools/registry.py` |
| **Testing** | Hard to mock imports | Easy dependency injection |
| **IDE support** | Broken (symbols unknown) | Works (explicit imports) |
| **Documentation** | Implicit dependencies | Explicit import statements |
| **Maintenance** | Hard to trace dependencies | Clear import graph |

---

## Priority Fixes

1. ✅ **Move files to new structure** (fixes circular imports)
2. ✅ **Replace wildcard imports** (fixes namespace pollution)
3. ⏳ Add `__init__.py` files throughout
4. ⏳ Split `config.py` into multiple modules
5. ⏳ Add type hints and docstrings
6. ⏳ Add logging infrastructure
7. ⏳ Create `pyproject.toml`
8. ⏳ Add comprehensive tests

