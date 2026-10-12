from __future__ import annotations

from dataclasses import dataclass

CARDINALS = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True)
class Pos:
    """Клетка карты: x - столбец, y - строка."""

    x: int
    y: int

    def shifted(self, dx: int, dy: int) -> Pos:
        return Pos(self.x + dx, self.y + dy)

    def manhattan(self, other: Pos) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def neighbors(self) -> list[Pos]:
        return [self.shifted(dx, dy) for dx, dy in CARDINALS]
