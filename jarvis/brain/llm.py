from __future__ import annotations

import re

from openai import OpenAI

from jarvis.brain.memory import ConversationMemory
from jarvis.utils.config import has_valid_openai_key, settings

SYSTEM_PROMPT = (
    "You are Jarvis, a highly intelligent AI assistant for a desktop agent. "
    "Be concise, efficient, and action-oriented.\n"
    "When the user intent is an executable desktop/web/system action, respond with exactly one line:\n"
    "CMD: <single executable command>\n"
    "Use commands this app can route, such as: open <app_or_url>, close <app>, google <query>, "
    "youtube <query>, weather [in <city>], news, run <terminal command>, find file <name>, "
    "git status, git pull, git push, git commit <message>, git commit and push <message>.\n"
    "If required details are missing (for example city for weather), ask one short clarifying question "
    "instead of guessing defaults.\n"
    "If the intent is NOT actionable, respond in normal natural language with no CMD line.\n"
    "Do not include markdown fences, bullets, or extra prefixes."
)


class JarvisBrain:
    def __init__(self, memory: ConversationMemory) -> None:
        self.client = None
        self.api_key = settings.openai_api_key or ""
        self.set_api_key(self.api_key)
        self.memory = memory
        self.model = settings.openai_model

    def set_api_key(self, api_key: str) -> None:
        self.api_key = (api_key or "").strip()
        self.client = OpenAI(api_key=self.api_key) if has_valid_openai_key(self.api_key) else None

    def set_model(self, model: str) -> None:
        if model.strip():
            self.model = model.strip()

    @staticmethod
    def extract_command(reply: str) -> str | None:
        text = (reply or "").strip()
        if not text:
            return None
        m = re.match(r"^\s*CMD:\s*(.+?)\s*$", text, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        cmd = m.group(1).strip()
        if not cmd:
            return None
        # Defensive cleanup in case model emits accidental wrapping quotes.
        if (cmd.startswith('"') and cmd.endswith('"')) or (cmd.startswith("'") and cmd.endswith("'")):
            cmd = cmd[1:-1].strip()
        return cmd or None

    def reply(self, user_text: str) -> str:
        if self.client is None:
            return (
                "I can hear you, but my AI brain is offline. "
                "Set a valid OpenAI API key in Settings > AI Settings."
            )

        self.memory.add("user", user_text)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.memory.as_chat_messages())

        response = self.client.responses.create(
            model=self.model,
            input=messages,
            temperature=0.4,
        )
        answer = response.output_text.strip()
        if not answer:
            answer = "I had a brief thinko. Could you repeat that?"
        self.memory.add("assistant", answer)
        return answer
