"""Бот проходит игру на настоящих сгенерированных уровнях: проверяем инварианты мира."""
import random

import pytest

from domain.balance import BACKPACK_SLOT_LIMIT
from domain.commands import Move, UseItem
from domain.generation.locks import can_pass
from domain.geometry import bfs_distances, bfs_path
from domain.models.items import ItemType
from domain.models.tile import Tile
from domain.session import GameSession, GameState


def check_invariants(session: GameSession) -> None:
    level, player = session.level, session.player
    assert level.is_walkable(player.pos)
    assert 0 <= player.health <= player.max_health
    assert level.enemy_at(player.pos) is None
    cells = [e.pos for e in level.enemies]
    assert len(cells) == len(set(cells))
    for enemy in level.enemies:
        assert enemy.alive
        assert level.tile_at(enemy.pos) in (Tile.FLOOR, Tile.DOORWAY, Tile.CORRIDOR)
        assert 0 <= enemy.health <= enemy.max_health
    for item_type in ItemType:
        if item_type is not ItemType.TREASURE:
            assert len(player.backpack.items_of(item_type)) <= BACKPACK_SLOT_LIMIT


def bot_step(session: GameSession) -> None:
    """Один ход бота: лечится, берёт оружие, собирает достижимые ключи, потом идёт к выходу."""
    player, level = session.player, session.level
    if player.health * 2 < player.max_health and player.backpack.items_of(ItemType.FOOD):
        session.handle(UseItem(ItemType.FOOD, 0))
        return
    if player.weapon is None and player.backpack.items_of(ItemType.WEAPON):
        session.handle(UseItem(ItemType.WEAPON, 0))
        return

    passable = can_pass(level, player.keys)
    target = level.exit
    if level.keys:   # на уровне ещё лежат ключи: идём к ближайшему из тех, до которых можно дойти
        reach = bfs_distances(player.pos, passable)
        keys_in_reach = [pos for pos in level.keys if pos in reach]
        if keys_in_reach:
            target = min(keys_in_reach, key=lambda pos: reach[pos])
    path = bfs_path(player.pos, target, passable)
    assert path, f"бот не нашёл пути к {target}: уровень {level.number} непроходим"
    nxt = path[0]
    session.handle(Move(nxt.x - player.pos.x, nxt.y - player.pos.y))


@pytest.mark.parametrize("seed", range(12))
def test_bot_plays_without_breaking_invariants(seed):
    session = GameSession(random.Random(seed))
    for _ in range(4000):
        if session.state is not GameState.PLAYING:
            break
        bot_step(session)
        check_invariants(session)
    assert session.stats.steps > 0


def test_a_strong_bot_can_reach_the_end():
    """Игра проходима: с запасом здоровья и силы бот доходит до победы."""
    session = GameSession(random.Random(5), total_levels=3)
    session.player.max_health = session.player.health = 100_000
    session.player.strength = 1_000
    for _ in range(5000):
        if session.state is not GameState.PLAYING:
            break
        bot_step(session)
    assert session.state is GameState.WON
    assert session.stats.level_reached == 3


def test_full_21_level_game_is_generated_lazily_and_finishes():
    session = GameSession(random.Random(9))
    session.player.max_health = session.player.health = 10**9
    session.player.strength = 10**6
    session.player.agility = 100
    for _ in range(40_000):
        if session.state is not GameState.PLAYING:
            break
        bot_step(session)
    assert session.state is GameState.WON
    assert session.stats.level_reached == 21
