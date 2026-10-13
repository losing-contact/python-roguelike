import random

import pytest
from level_builder import level_from_ascii

from domain.session import GameSession


class HitRng(random.Random):
    """Генератор, при котором любая проверка попадания успешна."""

    def random(self) -> float:
        return 0.0


class MissRng(random.Random):
    """Генератор, при котором любая проверка попадания - промах."""

    def random(self) -> float:
        return 0.999


@pytest.fixture
def hit_rng() -> HitRng:
    return HitRng(1)


@pytest.fixture
def miss_rng() -> MissRng:
    return MissRng(1)


@pytest.fixture
def make_session():
    """Сессия на заранее нарисованных уровнях: make_session([rows1, rows2], rng)."""

    def factory(levels: list[list[str]], rng: random.Random | None = None):
        def generator(number: int, _rng, _total):
            return level_from_ascii(levels[number - 1], number)

        return GameSession(rng or random.Random(1), total_levels=len(levels), generator=generator)

    return factory
