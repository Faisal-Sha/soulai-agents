import re

CYRILLIC_PATTERN = re.compile(r"[\u0400-\u04FF]")
LATIN_PATTERN = re.compile(r"[A-Za-z]")


def detect_user_language(text: str) -> str:
    """
    Detect whether the user message is primarily Russian or English.
    Defaults to English when the message is empty or ambiguous.
    """
    if not text or not text.strip():
        return "en"

    cyrillic_count = len(CYRILLIC_PATTERN.findall(text))
    latin_count = len(LATIN_PATTERN.findall(text))

    if cyrillic_count > latin_count:
        return "ru"

    return "en"
