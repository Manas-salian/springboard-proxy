"""
Logger Addon

Logs all HTTP/HTTPS requests and responses to:
  - Console: color-coded summary (method, URL, status, size)
  - File:    detailed log with headers and body previews (daily rotation, 30-day retention)
"""

import os
import sys
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from mitmproxy import http

# Enable ANSI escape codes on Windows 10+
if sys.platform == "win32":
    os.system("")


class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"


METHOD_COLORS = {
    "GET": Colors.GREEN,
    "POST": Colors.YELLOW,
    "PUT": Colors.BLUE,
    "DELETE": Colors.RED,
    "PATCH": Colors.MAGENTA,
    "HEAD": Colors.CYAN,
    "OPTIONS": Colors.GRAY,
}


def _status_color(code: int) -> str:
    if 200 <= code < 300:
        return Colors.GREEN
    elif 300 <= code < 400:
        return Colors.CYAN
    elif 400 <= code < 500:
        return Colors.YELLOW
    elif code >= 500:
        return Colors.RED
    return Colors.WHITE


def _human_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    return f"{size_bytes / (1024 * 1024):.1f}MB"


def _setup_file_logger() -> logging.Logger:
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("proxy_file_logger")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = TimedRotatingFileHandler(
            os.path.join(log_dir, "proxy.log"),
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        handler.suffix = "%Y-%m-%d"
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(handler)

    return logger


class RequestResponseLogger:
    """Mitmproxy addon that logs all traffic to console and file."""

    def __init__(self):
        self.file_logger = _setup_file_logger()

    def request(self, flow: http.HTTPFlow) -> None:
        req = flow.request
        method = req.method
        url = req.pretty_url
        method_color = METHOD_COLORS.get(method, Colors.WHITE)
        ts = datetime.now().strftime("%H:%M:%S")

        print(
            f"{Colors.DIM}{ts}{Colors.RESET} "
            f"{Colors.BOLD}{method_color}> {method:7s}{Colors.RESET} "
            f"{Colors.WHITE}{url}{Colors.RESET}"
        )

        self.file_logger.info(f"REQUEST  | {method:7s} | {url}")

        for key, value in req.headers.items():
            self.file_logger.debug(f"  REQ HDR | {key}: {value}")

        if req.content and len(req.content) > 0:
            content_type = req.headers.get("content-type", "unknown")
            body_preview = req.content[:500].decode("utf-8", errors="replace")
            self.file_logger.debug(
                f"  REQ BODY | type={content_type} size={len(req.content)} | {body_preview}"
            )

    def response(self, flow: http.HTTPFlow) -> None:
        req = flow.request
        resp = flow.response
        if resp is None:
            return

        method = req.method
        url = req.pretty_url
        status = resp.status_code
        content_type = resp.headers.get("content-type", "unknown")
        size = len(resp.content) if resp.content else 0
        method_color = METHOD_COLORS.get(method, Colors.WHITE)
        ts = datetime.now().strftime("%H:%M:%S")

        print(
            f"{Colors.DIM}{ts}{Colors.RESET} "
            f"{Colors.BOLD}{method_color}< {method:7s}{Colors.RESET} "
            f"{_status_color(status)}{status}{Colors.RESET} "
            f"{Colors.DIM}{_human_size(size):>8s}{Colors.RESET} "
            f"{Colors.GRAY}{content_type.split(';')[0]:30s}{Colors.RESET} "
            f"{Colors.WHITE}{url}{Colors.RESET}"
        )

        self.file_logger.info(
            f"RESPONSE | {method:7s} | {status} | {_human_size(size):>8s} | "
            f"{content_type} | {url}"
        )

        for key, value in resp.headers.items():
            self.file_logger.debug(f"  RES HDR | {key}: {value}")

        # Log body preview for text-based content types only
        if resp.content and len(resp.content) > 0:
            ct_lower = content_type.lower()
            if any(t in ct_lower for t in ["text/", "json", "xml", "javascript", "html"]):
                body_preview = resp.content[:1000].decode("utf-8", errors="replace")
                self.file_logger.debug(
                    f"  RES BODY | preview ({min(1000, len(resp.content))}/{size} bytes) | "
                    f"{body_preview}"
                )

    def error(self, flow: http.HTTPFlow) -> None:
        if flow.error:
            ts = datetime.now().strftime("%H:%M:%S")
            url = flow.request.pretty_url if flow.request else "unknown"
            print(
                f"{Colors.DIM}{ts}{Colors.RESET} "
                f"{Colors.BOLD}{Colors.RED}x ERROR{Colors.RESET}  "
                f"{Colors.RED}{flow.error.msg}{Colors.RESET} "
                f"{Colors.WHITE}{url}{Colors.RESET}"
            )
            self.file_logger.error(f"ERROR    | {flow.error.msg} | {url}")


addons = [RequestResponseLogger()]
