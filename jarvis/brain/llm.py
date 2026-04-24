from __future__ import annotations

from openai import OpenAI

from jarvis.brain.memory import ConversationMemory
from jarvis.utils.config import has_valid_openai_key, settings

SYSTEM_PROMPT = (
    "You are Jarvis, a highly intelligent AI assistant. You are concise, "
    "efficient, and slightly witty. You help execute tasks, answer questions, "
    "and assist with development workflows. Always prioritize clarity and action."
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
