from __future__ import annotations

from dataclasses import dataclass, field

from domain.models.position import Pos


@dataclass
class Exploration:
    """Что игрок уже видел на текущем уровне. Это состояние нужно сохранять.

    Хранятся только клетки (позиции). Что именно показывать на месте увиденной клетки,
    решает слой отображения: см. presentation/theme.py::REMEMBERED_TILES.
    """

    seen: set[Pos] = field(default_factory=set)
