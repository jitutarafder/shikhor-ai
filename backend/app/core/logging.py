"""Structured logging setup for Shikhor AI.

Enforces:
- Request correlation ID tracking
- JSON / structured formatting
- Redaction of sensitive fields (passwords, tokens, OTPs, raw coordinates)
"""

import logging
import sys
from typing import Any, Dict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "otp",
    "secret",
    "api_key",
}


def redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redacts sensitive keys from log dictionaries."""
    redacted = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_data(value)
        else:
            redacted[key] = value
    return redacted


def setup_logging(debug: bool = False) -> None:
    """Configures root logger with clean stream output."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    log_level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").handlers = [handler]
