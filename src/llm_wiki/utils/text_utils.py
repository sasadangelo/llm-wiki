"""Text processing utilities."""

import json
import re


def extract_json_from_text(text: str) -> dict | None:
    """
    Extract JSON object from text.

    Args:
        text: Text containing JSON

    Returns:
        Parsed JSON dict or None if not found
    """
    try:
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        pass
    return None


def extract_json_array_from_text(text: str) -> list | None:
    """
    Extract JSON array from text.

    Args:
        text: Text containing JSON array

    Returns:
        Parsed JSON list or None if not found
    """
    try:
        json_match = re.search(r"\[.*?\]", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        pass
    return None


# Made with Bob
