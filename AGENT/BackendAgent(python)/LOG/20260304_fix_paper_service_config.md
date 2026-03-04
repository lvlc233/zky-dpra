# 2026-03-04 Backend Fix: Paper Service Configuration Handling

## Issue
Users reported errors during `summary` and `mind_map` generation tasks:
1. `summary`: `IndexError: list index out of range` - caused by assuming a specific agent configuration exists in the list.
2. `mind_map`: `AttributeError: 'NoneType' object has no attribute 'get'` - caused by `llm_config` being None/Empty when no configuration was found, leading to runtime context failure.

## Changes
Modified `main/backend/src/service/papers/paper_service.py`:

### Summary Task
- Replaced direct list access `[0]` with safe `next(..., None)` retrieval.
- Added fallback logic: `summary` -> `chat` -> first available agent.
- Added default `llm_config` values if no configuration is found to prevent downstream crashes.

### Mind Map Task
- Implemented similar robust configuration retrieval with fallbacks: `mind_map` -> `summary` -> `chat` -> first available.
- Ensured `llm_config` is always a valid dictionary with default values (`gpt-3.5-turbo`, `openai`) even if user settings are missing.

## Verification
- Code analysis confirms that `summary_config` and `mindmap_config` are now retrieved safely.
- `llm_config` is guaranteed to be a dictionary, preventing `None` context issues in LangGraph nodes.
