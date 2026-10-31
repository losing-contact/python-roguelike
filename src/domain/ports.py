"""Порты: что домену нужно от внешнего мира. Реализуют их другие слои (инверсия зависимостей).

datalayer знает про эти интерфейсы, а domain про datalayer - нет.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from domain.session import GameSession
    from domain.stats import RunStats


class SaveRepository(Protocol):
    """Хранилище прогресса и таблицы рекордов (Задание 5)."""

    def save_session(self, session: GameSession) -> None: ...

    def load_session(self) -> GameSession | None: ...

    def add_record(self, stats: RunStats) -> None: ...

    def delete_session(self) -> None: ...

    def top_records(self, limit: int = 10) -> list[RunStats]: ...
