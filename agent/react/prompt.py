"""State machine rules for the DeepSeek search scenario.

Each state maps to one PlanStep. The ReAct loop runs one state and returns 'done'.
The executor then starts a new loop for the next plan step with the next state.
"""

DEEPSEEK_STATE_MACHINE = {
    "navigate": {
        "action": "navigate",
        "params": {"url": "https://chat.deepseek.com"},
        "next": "page_loading",
    },
    "page_loading": {
        "action": "navigate",
        "params": {"action": "wait_loaded"},
        "next": "done",
        "retry_on": "loading_timeout",
    },
    "login": {
        "action": "input",
        "params": {"action": "wait_for_login"},
        "next": "done",
    },
    "input": {
        "action": "input",
        "params": {"action": "type_and_submit", "text": "{query}"},
        "next": "done",
    },
    "wait": {
        "action": "input",
        "params": {"action": "wait_for_response"},
        "next": "done",
    },
    "sidebar": {
        "action": "sidebar",
        "params": {"action": "collapse"},
        "next": "done",
    },
    "screenshot": {
        "action": "screenshot",
        "params": {"action": "fullpage"},
        "next": "done",
    },
}
