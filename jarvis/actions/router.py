from __future__ import annotations

import re

from jarvis.actions import developer, system, web


class CommandRouter:
    def route_many(self, command: str) -> str | None:
        chunks = [c.strip() for c in re.split(r"\band\b", command) if c.strip()]
        if len(chunks) <= 1:
            return self.route(command)
        results = []
        for chunk in chunks:
            result = self.route(chunk)
            if result:
                results.append(result)
        return " | ".join(results) if results else None

    def route(self, command: str) -> str | None:
        text = command.lower().strip()

        if text.startswith("open "):
            target = text.removeprefix("open ").strip()
            if "." in target or "www" in target:
                return web.open_website(target)
            return system.open_app(target)

        if text.startswith("close "):
            return system.close_app(text.removeprefix("close ").strip())

        if "lock screen" in text:
            return system.lock_screen()
        if "shutdown" in text:
            return system.shutdown()
        if "restart" in text:
            return system.restart()
        if "volume up" in text:
            return system.volume_up()
        if "volume down" in text:
            return system.volume_down()
        if "mute" in text and "unmute" not in text:
            return system.mute()
        if "unmute" in text:
            return system.unmute()

        weather_match = re.search(r"weather(?: in)? (.+)", text)
        if weather_match:
            return web.get_weather(weather_match.group(1).strip())

        if text.startswith("google "):
            return web.google_search(text.removeprefix("google ").strip())
        if text.startswith("youtube "):
            return web.youtube_search(text.removeprefix("youtube ").strip())
        if "news" in text:
            return web.get_news()

        if text.startswith("run "):
            return developer.run_terminal_command(text.removeprefix("run ").strip())
        if "git status" in text:
            return developer.git_status()
        if "git pull" in text:
            return developer.git_pull()
        if "git push" in text:
            return developer.git_push()

        if text.startswith("find file "):
            return system.search_file(text.removeprefix("find file ").strip())

        return None
