#!/usr/bin/env python3
import json
import os
import sys
import time
import traceback

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.enigma import enigma
except ImportError as e:
    print(f"Error importing E.N.I.G.M.A. modules: {e}")
    print("Please make sure you are running the tests from the project root directory or have configured your PYTHONPATH.")
    sys.exit(1)

# ANSI escape codes for coloring
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"

# Tracked execution state
actual_request = None
actual_tool_details = None

# Save original methods for patching/restoring
orig_request_type_identifier = enigma.request_type_identifier
orig_function_executer = enigma.function_executer

def patch_enigma():
    """Monkey-patch EnigmaSystem to capture its internal decisions and stub tool side effects."""
    global actual_request, actual_tool_details
    actual_request = None
    actual_tool_details = None

    def mock_request_type_identifier(summary):
        global actual_request
        req = orig_request_type_identifier(summary)
        actual_request = req
        return req

    def mock_function_executer(tool_details):
        global actual_tool_details
        actual_tool_details = tool_details
        tool_name = tool_details.get("tool", "unknown")
        # Stub the tool response to avoid side-effects (e.g. sending real emails, writing files)
        return f"Mocked execution response for tool '{tool_name}'"

    enigma.request_type_identifier = mock_request_type_identifier
    enigma.function_executer = mock_function_executer

def restore_enigma():
    """Restore EnigmaSystem to its original behavior."""
    enigma.request_type_identifier = orig_request_type_identifier
    enigma.function_executer = orig_function_executer


def run_test_case(file_path, verbose=False):
    """Loads and runs a single test case from a JSON file."""
    with open(file_path, "r") as f:
        try:
            test_data = json.load(f)
        except Exception as e:
            return False, [f"Failed to parse JSON test file: {e}"]

    test_name = test_data.get("name", os.path.basename(file_path))
    conversation = test_data.get("conversation", [])
    expected = test_data.get("expected", {})

    if not conversation:
        return False, ["No conversation history provided in the test case."]

    if verbose:
        print(f"\n{COLOR_CYAN}--- Running Test: {test_name} ---{COLOR_RESET}")
        print("Conversation history:")
        for msg in conversation:
            print(f"  {msg['role']}: {msg['content']}")

    patch_enigma()
    start_time = time.time()
    errors = []

    try:
        chat_response = enigma.process(conversation)
        duration = time.time() - start_time
    except Exception as e:
        restore_enigma()
        tb = traceback.format_exc()
        return False, [f"Enigma threw an exception during processing: {e}\n{tb}"]

    restore_enigma()

    # Assertions
    # 1. Assert Request Type
    expected_request_type = expected.get("request_type")
    if expected_request_type:
        actual_type = actual_request.type_ if actual_request else None
        if actual_type != expected_request_type:
            errors.append(f"Expected request type '{expected_request_type}', but got '{actual_type}'")

    # 2. Assert Tool Called
    expected_tool = expected.get("tool")
    if expected_tool:
        actual_tool = actual_tool_details.get("tool") if actual_tool_details else None
        if actual_tool != expected_tool:
            errors.append(f"Expected tool '{expected_tool}' to be called, but got '{actual_tool or 'None'}'")

    # 3. Assert Tool Arguments
    expected_kwargs = expected.get("tool_kwargs")
    if expected_kwargs and actual_tool_details:
        actual_kwargs = actual_tool_details.get("tool_kwargs", {})
        for k, expected_v in expected_kwargs.items():
            if k not in actual_kwargs:
                errors.append(f"Expected tool argument '{k}' was missing from the tool call")
            elif actual_kwargs[k] != expected_v:
                errors.append(f"Expected tool argument '{k}' to be '{expected_v}', but got '{actual_kwargs[k]}'")

    # 4. Assert Response Substrings
    expected_substring = expected.get("response_contains")
    if expected_substring:
        if isinstance(expected_substring, str):
            expected_substrings = [expected_substring]
        else:
            expected_substrings = expected_substring

        for substr in expected_substrings:
            if substr.lower() not in chat_response.lower():
                errors.append(f"Expected response to contain '{substr}', but got: '{chat_response}'")

    if verbose:
        print(f"Captured Request Type: {actual_request.type_ if actual_request else 'None'}")
        if actual_tool_details:
            print(f"Captured Tool Call: {actual_tool_details.get('tool')} with kwargs: {actual_tool_details.get('tool_kwargs')}")
        print(f"Final AI Response: {chat_response}")
        print(f"Duration: {duration:.2f}s")
        print(f"{COLOR_CYAN}--------------------------------------{COLOR_RESET}")

    if errors:
        return False, errors
    return True, duration


def main():
    # Setup paths
    tests_dir = os.path.join(project_root, "tests")
    conv_dir = os.path.join(tests_dir, "conversations")

    if not os.path.exists(conv_dir):
        print(f"{COLOR_RED}Error: Test conversations directory does not exist at {conv_dir}{COLOR_RESET}")
        sys.exit(1)

    # CLI argument parsing
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    # Lint check execution
    if "--lint" in sys.argv or "-l" in sys.argv:
        print("=" * 60)
        print(f"  {COLOR_BOLD}E.N.I.G.M.A. Style and Code Quality Check (Ruff){COLOR_RESET}")
        print("=" * 60)
        print("Running linting checks on E.N.I.G.M.A. modules...")

        import subprocess
        ruff_path = os.path.join(project_root, ".venv", "bin", "ruff")
        if not os.path.exists(ruff_path):
            ruff_path = "ruff"

        try:
            res = subprocess.run([ruff_path, "check", "."], cwd=project_root)
            if res.returncode != 0:
                print(f"\n{COLOR_RED}✗ Linting checks failed! Please resolve style/syntax issues.{COLOR_RESET}")
                sys.exit(res.returncode)
            else:
                print(f"\n{COLOR_GREEN}✓ Style and code quality checks passed successfully!{COLOR_RESET}")
                # If only lint check was requested, exit 0
                if len(sys.argv) == 2:
                    sys.exit(0)
        except FileNotFoundError:
            print(f"{COLOR_YELLOW}Warning: Ruff linter not found. Install developer requirements to enable lint checks.{COLOR_RESET}")
            if len(sys.argv) == 2:
                sys.exit(0)

    test_files_filter = [arg for arg in sys.argv[1:] if not arg.startswith("-") and arg not in ["--lint", "-l"]]

    # Discover JSON test files
    all_files = sorted(os.listdir(conv_dir))
    test_files = [f for f in all_files if f.endswith(".json")]

    if test_files_filter:
        # Filter files based on argument
        filtered_files = []
        for filter_name in test_files_filter:
            # Match exact file name or partial
            matched = [f for f in test_files if filter_name in f]
            filtered_files.extend(matched)
        test_files = sorted(list(set(filtered_files)))

    if not test_files:
        print(f"{COLOR_YELLOW}No conversation test cases found matching your filters.{COLOR_RESET}")
        sys.exit(0)

    print("=" * 60)
    print(f"  {COLOR_BOLD}E.N.I.G.M.A. Automated Conversation Test Suite{COLOR_RESET}")
    print("=" * 60)
    print(f"Discovered {len(test_files)} test case(s). Running suite...\n")

    passed_count = 0
    failed_count = 0
    failed_details = []

    total_start_time = time.time()

    for filename in test_files:
        file_path = os.path.join(conv_dir, filename)

        # Extract display name
        try:
            with open(file_path, "r") as f:
                test_name = json.load(f).get("name", filename)
        except Exception:
            test_name = filename

        print(f"[ RUN  ] {test_name} ({filename})")

        success, result = run_test_case(file_path, verbose=verbose)

        if success:
            passed_count += 1
            duration = result
            print(f"[{COLOR_GREEN} PASS {COLOR_RESET}] {test_name} ({duration:.2f}s)\n")
        else:
            failed_count += 1
            errors = result
            print(f"[{COLOR_RED} FAIL {COLOR_RESET}] {test_name}")
            for err in errors:
                print(f"        - {err}")
            print()
            failed_details.append((test_name, filename, errors))

    total_duration = time.time() - total_start_time

    print("-" * 60)
    print(f"{COLOR_BOLD}Test Execution Summary:{COLOR_RESET}")
    print(f"  Total Run Time: {total_duration:.2f}s")
    print(f"  Passed Tests:   {COLOR_GREEN}{passed_count}{COLOR_RESET}")
    print(f"  Failed Tests:   {COLOR_RED if failed_count > 0 else COLOR_GREEN}{failed_count}{COLOR_RESET}")

    if failed_count > 0:
        print("\n" + "=" * 60)
        print(f"  {COLOR_RED}{COLOR_BOLD}Detailed Failures Summary:{COLOR_RESET}")
        print("=" * 60)
        for name, filename, errors in failed_details:
            print(f"\n{COLOR_BOLD}{name}{COLOR_RESET} ({filename})")
            for err in errors:
                print(f"  {COLOR_RED}✗{COLOR_RESET} {err}")
        print("=" * 60)
        sys.exit(1)
    else:
        print(f"\n{COLOR_GREEN}{COLOR_BOLD}✓ All conversation tests completed successfully!{COLOR_RESET}")
        print("=" * 60)
        sys.exit(0)

if __name__ == "__main__":
    main()
