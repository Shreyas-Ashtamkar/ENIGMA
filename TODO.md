# E.N.I.G.M.A Codebase Issues & Fixes TODO

## CRITICAL ISSUES

- [x] **1. Circular Import Dependency Chain**
  - Location: `configs/config.py` → `utils/system_prompts.py` → `utils/Tool.py` → `configs/config.py`
  - Fixed by replacing wildcard imports with explicit imports
  - References: `enigma.py:1-12`, `configs/config.py:1-11`

- [x] **2. Wildcard Imports Breaking Namespace**
  - Location: `enigma.py` line 5, `configs/config.py` line 5
  - Fixed by replacing `from module import *` with explicit import lists
  - References: `enigma.py:1-12`, `configs/config.py:1-11`

- [x] **3. Type Hint Syntax Error (Unreported)**
  - Location: `enigma.py` lines 62, 70, 77
  - Issue: `dict[str:str]` should be `dict[str, str]`
  - Will crash at runtime if type checking is enabled
  - Fix: Change all occurrences to use comma instead of colon
  - Files affected: `enigma.py` (3 occurrences)

---

## HIGH SEVERITY ISSUES

- [x] **4. Missing `__init__.py` Files**
  - Location: `configs/` and `utils/` directories
  - Issue: No `__init__.py` in package directories
  - Fix: Create empty `__init__.py` in `configs/__init__.py` and `utils/__init__.py`
  - Violates: PEP 420 namespace packages convention

- [x] **5. Configuration Mixed with Business Logic**
  - Location: `configs/config.py` (95 lines)
  - Issue: Tool implementations, Tool registration, AI setup all mixed
  - Fix: Split into separate modules:
    - `configs/settings.py` - DEBUG, VERBOSE, MAX_RETRY only
    - `configs/logging.py` - print1-4 setup
    - `configs/registry.py` - Tool registration
  - References: `configs/config.py:19-26` (tools), lines 22-62 (registration), lines 65-95 (AI setup)

- [ ] **6. Overly Broad "utils" Directory**
  - Location: `utils/` directory contains 4 unrelated modules
  - Issue: `Tool.py` (framework), `ai.py` (domain logic), `gui.py` (UI), `system_prompts.py` (config)
  - Fix: Restructure per `recommended_structure.md`:
    - `enigma/core/tool.py` ← `utils/Tool.py`
    - `enigma/ai/models.py` ← `utils/ai.py`
    - `enigma/ui/streamlit_app.py` ← `utils/gui.py` + `main.py`
    - `enigma/ai/prompts.py` ← `utils/system_prompts.py`

- [ ] **7. Multiple Entry Points with Unclear Ownership**
  - Location: `main.py`, `enigma.py`, `sample_conversations.py`
  - Issue: Three entry points with unclear purpose
  - Fix: 
    - Keep `main.py` as primary entry
    - Remove `if __name__ == "__main__"` from `enigma.py` (make it pure module)
    - Move `sample_conversations.py` to `tests/fixtures/conversations.py`

---

## MEDIUM SEVERITY ISSUES

- [ ] **8. Inconsistent Naming Conventions (PEP 8 Violations)**
  - Issues:
    - [ ] CapCase filename: `utils/Tool.py` → `utils/tool.py`
    - [ ] Inconsistent underscore prefix: `_AI`, `_Request` should be `AI`, `Request` if public
    - [ ] Mixed function naming: `_stringify_conversation`, `_get_summary`, `_get_request` inconsistent underscore usage
  - References: `utils/Tool.py`, `utils/ai.py`, `enigma.py`

- [ ] **9. Missing Type Hints on Public APIs**
  - Location: Multiple functions missing type hints
  - Examples:
    - `utils/ai.py`: `def _format_message(message, role='user'):` missing return type
    - `utils/Tool.py`: `def parameter(type_:str, ...)` missing types on all params
    - `utils/gui.py`: `def init_chatbox(height=550, container=st):` all types missing
    - `enigma.py`: `def _get_tool(task:str):` missing return type
  - Fix: Add type hints to all function signatures (PEP 484)

- [ ] **10. Incomplete/Missing Docstrings**
  - Location: All Python files have ZERO docstring coverage
  - Issue: No module, class, or function docstrings
  - Fix: Add docstrings following PEP 257 to:
    - [ ] All module files (module-level docstring)
    - [ ] All classes (class docstring)
    - [ ] All public functions (function docstring with args/returns)
  - Also fix: Line 27 in `utils/ai.py` has typo: "recieve" → "receive"

- [ ] **11. Magic Numbers and Hardcoded Values Scattered**
  - Issues:
    - [ ] `3` in `enigma.py:8` → Create `CONVERSATION_CONTEXT_WINDOW = 3`
    - [ ] Model names hardcoded 3 times in `configs/config.py` → Centralize as `MODEL_NAMES`
    - [ ] `"Do this - "` in `enigma.py:33,35` → Create `TASK_PREFIX = "Do this - "`
    - [ ] `"NO_SPECIFIC_TASK"` in multiple locations → Create `NO_TASK_MARKER = "NO_SPECIFIC_TASK"`
    - [ ] Temperature values (0) hardcoded → Centralize as `TEMPERATURES`
    - [ ] Retry max (2) in multiple locations → Use single source
  - Fix: Create `configs/constants.py` for all magic values

- [ ] **12. Environment and Configuration Not Managed**
  - Location: `configs/config.py` and throughout
  - Issues:
    - [ ] No `.env` file handling (missing `python-dotenv`)
    - [ ] Ollama connection hardcoded (assumed `localhost:11434`)
    - [ ] No environment-specific configs (dev, staging, prod)
  - Fix: 
    - [ ] Create `.env.example` template
    - [ ] Add `.env` to `.gitignore` (if not already)
    - [ ] Use `python-dotenv` to load environment variables
    - [ ] Create `configs/settings.py` with `pydantic.BaseSettings` or similar

- [ ] **13. No Error Handling or Custom Exceptions**
  - Location: Throughout codebase
  - Issues:
    - [ ] Generic `Exception` catches (line 46, 96 in `enigma.py`)
    - [ ] No custom exception hierarchy
    - [ ] Ollama connection failures silently fail
    - [ ] No logging infrastructure
  - Fix:
    - [ ] Create `enigma/config/exceptions.py` with custom exceptions:
      - `OllamaConnectionError`
      - `InvalidToolError`
      - `ToolExecutionError`
      - `InvalidRequestError`
    - [ ] Replace generic exceptions with specific ones
    - [ ] Add try-except blocks for Ollama initialization

- [ ] **14. Debug/Verbose Print Statements as Configuration**
  - Location: `configs/config.py` lines 12-17
  - Issue: Uses `print()` instead of `logging` module
  - Fix:
    - [ ] Replace with Python's `logging` module
    - [ ] Create `enigma/config/logging.py`
    - [ ] Use log levels: DEBUG, INFO, WARNING, ERROR
    - [ ] Remove `print1`, `print2`, `print3`, `print4` approach

---

## MEDIUM-LOW SEVERITY ISSUES

- [ ] **15. No Dependency Management (Missing pyproject.toml)**
  - Location: Project root
  - Current: Only `requirements.txt` exists
  - Missing:
    - [ ] `pyproject.toml` (PEP 517/518 standard)
    - [ ] Project metadata (name, version, description)
    - [ ] Development vs. production dependencies separated
    - [ ] Entry points defined
  - Fix: Create modern `pyproject.toml` following PEP 517/518

- [ ] **16. Unused Imports and Dead Code**
  - Issues:
    - [ ] `configs/config.py:6` imports `system` only used in lambda
    - [ ] `enigma.py:101` passes string to method expecting message object
    - [ ] `utils/gui.py:16-20` has unused `async def _ai_stream()`
  - Fix: Remove unused imports and clean up dead code

- [ ] **17. Incomplete Tool Implementation**
  - Issues:
    - [ ] `hint_conversation()` doesn't match Tool schema
    - [ ] `hint_error()` returns wrong format
    - [ ] `generate_image()` returns markdown, not structured response
    - [ ] `get_time_data()` ignores `format` parameter
  - Fix: Standardize tool return formats (JSON structured responses)

- [ ] **18. Incorrect `@staticmethod` Decorators**
  - Location: `utils/Tool.py` lines 34-60
  - Issue: All static methods use class state (`Tool._box`), should be `@classmethod`
  - Fix: Change all `@staticmethod` to `@classmethod` and add `cls` parameter
  - References:
    - [ ] `Tool.parameter()`
    - [ ] `Tool.create()`
    - [ ] `Tool.get()`
    - [ ] `Tool.box()`

- [ ] **19. GUI and Business Logic Tightly Coupled**
  - Location: `main.py` and `utils/gui.py`
  - Issue: No separation between view and model
  - Fix:
    - [ ] Create clear separation with dependency injection
    - [ ] Move business logic out of `main.py`
    - [ ] Make `gui.py` pure UI layer

- [ ] **20. Test File at Project Root**
  - Location: `sample_conversations.py`
  - Issue: Test/sample data at root level without organization
  - Fix:
    - [ ] Move to `tests/fixtures/conversations.py`
    - [ ] Create `tests/test_enigma.py`
    - [ ] Add `pytest` configuration

---

## LOW SEVERITY ISSUES

- [ ] **21. Inconsistent Spacing and Formatting**
  - Location: Throughout codebase
  - Issue: Inconsistent blank lines, spacing, formatting
  - Fix: Run code formatter (Black) and linter (flake8)

- [ ] **22. Missing `__all__` Exports**
  - Location: All package/module files
  - Issue: No explicit public API surface defined
  - Fix: Add `__all__` to each module defining public exports

- [ ] **23. Unused Lambda Functions**
  - Location: `configs/config.py` lines 12, 17
  - Issue: Lambda functions used for simple operations
  - Fix: Replace with regular functions for clarity

- [ ] **24. Missing/Incomplete README Documentation**
  - Location: `README.md` exists but lacks details
  - Missing:
    - [ ] Installation instructions
    - [ ] Development setup guide
    - [ ] Project structure explanation
    - [ ] API documentation
    - [ ] Contributing guidelines
  - Fix: Expand README with comprehensive documentation

- [ ] **25. Hardcoded Streamlit Configuration**
  - Location: `main.py` line 5
  - Issue: `st.set_page_config()` hardcoded
  - Fix: Move to config file and make configurable

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| CRITICAL | 3 | 2 | 1 |
| HIGH | 4 | 0 | 4 |
| MEDIUM | 7 | 0 | 7 |
| MEDIUM-LOW | 6 | 0 | 6 |
| LOW | 5 | 0 | 5 |
| **TOTAL** | **25** | **2** | **23** |

---

## Next Priority Actions

1. Fix type hint syntax error (Issue #3) - 5 min
2. Add `__init__.py` files (Issue #4) - 5 min
3. Fix `@staticmethod` to `@classmethod` (Issue #18) - 10 min
4. Create `configs/constants.py` (Issue #11) - 15 min
5. Set up logging infrastructure (Issue #14) - 30 min
6. Create custom exceptions (Issue #13) - 20 min

