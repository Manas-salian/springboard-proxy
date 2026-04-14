"""
Interceptor Addon

Intercepts assessment responses from Infosys Springboard endpoints:
  1. lex-iap.infosysapps.com  - POST /backend/TakeContest/Proceed
  2. one.techademy.com        - PATCH /v1/tenant/user_attempts/*/auto_save

Extracts question data, saves to file, and sends to Discord.
"""

import os
import json
from mitmproxy import http, ctx
from addons.discord_helper import send_file_to_discord

OUTPUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "assessment_sectionData.json")


class TargetInterceptor:
    """Intercepts assessment responses from multiple Springboard endpoints."""

    def response(self, flow: http.HTTPFlow) -> None:
        req = flow.request
        resp = flow.response

        if resp is None:
            return

        host = req.pretty_host
        path = req.path.split("?")[0]  # strip query params
        method = req.method

        # Route to the appropriate extractor
        if host == "lex-iap.infosysapps.com" and method == "POST" and path == "/backend/TakeContest/Proceed":
            self._handle_lex_iap(flow)

        elif host == "one.techademy.com" and method == "PATCH" and "/user_attempts/" in path and path.endswith("/auto_save"):
            self._handle_techademy(flow)

    def _handle_lex_iap(self, flow: http.HTTPFlow) -> None:
        """Extract objectiveQuestionsData from lex-iap TakeContest/Proceed response."""
        try:
            data = json.loads(flow.response.content.decode("utf-8", errors="replace"))

            section_data = data.get("sectionData")
            if section_data is None:
                keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
                ctx.log.warn(f"[interceptor:lex-iap] sectionData not found. Keys: {keys}")
                return

            # Flatten objectiveQuestionsData across all sections
            all_questions = []
            for section in section_data:
                all_questions.extend(section.get("objectiveQuestionsData", []))

            if not all_questions:
                ctx.log.warn("[interceptor:lex-iap] No objectiveQuestionsData in any section")
                return

            self._save_and_send(all_questions, "lex-iap", len(section_data))

        except json.JSONDecodeError:
            ctx.log.warn("[interceptor:lex-iap] Response is not valid JSON")
        except Exception as e:
            ctx.log.error(f"[interceptor:lex-iap] Error: {e}")

    def _handle_techademy(self, flow: http.HTTPFlow) -> None:
        """Extract questions from techademy auto_save response."""
        try:
            data = json.loads(flow.response.content.decode("utf-8", errors="replace"))

            # Navigate: data -> responses -> sections -> questions
            responses = data.get("data", {}).get("responses", {})
            sections = responses.get("sections", [])

            if not sections:
                keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
                ctx.log.warn(f"[interceptor:techademy] No sections found. Top-level keys: {keys}")
                return

            all_questions = []
            for section in sections:
                all_questions.extend(section.get("questions", []))

            if not all_questions:
                ctx.log.warn("[interceptor:techademy] No questions found in any section")
                return

            self._save_and_send(all_questions, "techademy", len(sections))

        except json.JSONDecodeError:
            ctx.log.warn("[interceptor:techademy] Response is not valid JSON")
        except Exception as e:
            ctx.log.error(f"[interceptor:techademy] Error: {e}")

    def _save_and_send(self, questions: list, source: str, section_count: int) -> None:
        """Save questions to file and send to Discord."""
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        ctx.log.info(
            f"[interceptor:{source}] Saved {len(questions)} questions "
            f"from {section_count} section(s) -> {OUTPUT_FILE}"
        )

        send_file_to_discord(OUTPUT_FILE, title=f"Assessment questions ({source})")


addons = [TargetInterceptor()]