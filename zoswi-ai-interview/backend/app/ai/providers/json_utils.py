import json
import re
from typing import Any


def parse_json_payload(raw_text: str) -> dict[str, Any]:
    stripped = raw_text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    brace_match = re.search(r"(\{.*\})", stripped, flags=re.DOTALL)
    if brace_match:
        return json.loads(brace_match.group(1))

    raise ValueError("No JSON object detected in model response")

