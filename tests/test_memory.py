from pathlib import Path

from jarvis.brain.memory import ConversationMemory


def test_memory_add_and_save(tmp_path: Path) -> None:
    memory = ConversationMemory(tmp_path / "memory.json", max_short_term=3)
    memory.add("user", "hello")
    memory.add("assistant", "hi")

    assert len(memory.short_term) == 2
    assert memory.long_term["frequent_commands"]["hello"] == 1
    assert (tmp_path / "memory.json").exists()
