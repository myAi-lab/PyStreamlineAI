import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extras = {
            "request_id",
            "session_id",
            "user_id",
            "model_used",
            "latency",
            "cost_usd",
        }
        for field in extras:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            exc_type = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
            exc_message = str(record.exc_info[1]) if record.exc_info[1] else ""
            payload["exception_type"] = exc_type
            payload["exception_message"] = exc_message
            payload["traceback"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
        force=True,
    )
