import re

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"bypass\s+security",
    r"system\s+prompt",
    r"reveal\s+instructions"
]

def check_input_guardrail(text: str) -> str | None:
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "Safety Alert: This request was flagged by guardrails."
    return None

def check_output_guardrail(text: str) -> str | None:
    if not text or not text.strip():
        return "I apologize, but I am unable to generate a response at this time."
    if "You are a helpful AI Assistant" in text or "rag_tool" in text:
        return "I encountered an internal validation error. How else can I assist you?"
    return None
