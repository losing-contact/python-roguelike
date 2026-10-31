# Игровая сессия: единственная точка входа в игру для остальных слоёв.

from __future__ import annotations

import random
from collections.abc import Callable
from enum import Enum

from domain import combat
from domain import events as ev
from domain.balance import LEVELS
from domain.commands import Command, Move, UseItem
from domain.enemies import PATTERNS, update_ghost_visibility
from domain.entities import Character, Enemy, EnemyKind
from domain.generation import generate_level
from domain.geometry import bfs_path
from domain.items import ItemType
from domain.level import Exploration, Level, Pos, Tile
from domain.stats import RunStats
from domain.visibility import compute_visible

LevelGenerator = Callable[[int, random.Random, int], Level]


class GameState(Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


class GameSession:
    def __init__(
            self,
            rng: random.Random | None = None,
            total_levels: int = LEVELS,
            generator: LevelGenerator = generate_level,
            player: Character | None = None,
            level: Level | None = None,
            stats: RunStats | None = None,
            exploration: Exploration | None = None,
    ) -> None:
        # player, level, stats и exploration нужны, чтобы собрать сессию из сохранения
        self.rng = rng or random.Random()
        self.total_levels = total_levels
        self._generate = generator
        self.state = GameState.PLAYING
        self.stats = stats or RunStats()
        self.player = player or Character()
        if level is None:
            level = self._generate(1, self.rng, total_levels)
            self.player.pos = level.start
        self.level = level
        self.exploration = exploration or Exploration()
        self.visible: set[Pos] = set()
        self._refresh_vision()

    # ------------------------------------------------------------------
    # Публичный интерфейс

    def handle(self, command: Command) -> list[ev.Event]:
        """Выполняет команду игрока и ход мира. Возвращает произошедшие события."""
        if self.state is not GameState.PLAYING:
            return []
        events: list[ev.Event] = []
        match command:
            case _ if self.player.asleep > 0:  # во сне команда тратит ход
                self.player.asleep -= 1
                events.append(ev.PlayerSlept())
                spent = True
            case Move(dx=dx, dy=dy):
                spent = self._move_player(dx, dy, events)
            case UseItem(item_type=item_type, slot=slot):
                spent = self._use_item(item_type, slot, events)
            case _:
                spent = False
        if spent and self.state is GameState.PLAYING:
            self._end_of_turn(events)
        for event in events:
            self.stats.record(event)
        self._refresh_vision()
        return events

    def _refresh_vision(self) -> None:
        """Пересчитывает видимое и дописывает его в память об уровне."""
        self.visible = compute_visible(self.level, self.player.pos)
        self.exploration.seen |= self.visible

    # ------------------------------------------------------------------
    # Действия игрока (возвращают True, если потратили ход)
    # ------------------------------------------------------------------
    def _move_player(self, dx: int, dy: int, events: list[ev.Event]) -> bool:
        target = self.player.pos.shifted(dx, dy)
        enemy = self.level.enemy_at(target)
        if enemy is not None:
            self._player_attack(enemy, events)
            return True
        door = self.level.doors.get(target)
        if door is not None:
            if door not in self.player.keys:
                events.append(ev.DoorLocked(door))
                return False
            del self.level.doors[target]
            events.append(ev.DoorOpened(door))
        if not self.level.is_walkable(target):
            return False  # упёрся в стену: ход не тратится

        self.player.pos = target
        events.append(ev.Moved())
        self._pick_up(target, events)
        if self.level.tile_at(target) is Tile.EXIT:
            self._leave_level(events)
            return False  # после перехода враги нового уровня не ходят
        return True

    def _player_attack(self, enemy: Enemy, events: list[ev.Event]) -> None:

        if enemy.disguised:                         # игрок наступил на «предмет»
            enemy.disguised = False
            events.append(ev.MimicRevealed())

        result = combat.resolve_attack(self.player, enemy, self.rng)
        events.append(ev.PlayerAttacked(enemy.kind, result.hit, result.damage))
        if not enemy.alive:
            self.level.enemies.remove(enemy)
            value = combat.treasure_value(enemy, enemy.hostility, self.rng)
            self.player.backpack.treasure += value
            events.append(ev.EnemyKilled(enemy.kind, value))

    def _pick_up(self, pos: Pos, events: list[ev.Event]) -> None:
        key = self.level.keys.pop(pos, None)
        if key is not None:
            self.player.keys.add(key)
            events.append(ev.KeyPickedUp(key))
        item = self.level.items.get(pos)
        if item is None:
            return
        if self.player.backpack.add(item):
            del self.level.items[pos]
            events.append(ev.ItemPickedUp(item))
        else:
            events.append(ev.BackpackFull(item))

    def _leave_level(self, events: list[ev.Event]) -> None:
        if self.level.number >= self.total_levels:
            self.state = GameState.WON
            events.append(ev.GameWon())
            return
        number = self.level.number + 1
        self.level = self._generate(number, self.rng, self.total_levels)
        self.player.pos = self.level.start
        self.exploration = Exploration()
        self.player.keys.clear()
        events.append(ev.LevelChanged(number))

    def _use_item(self, item_type: ItemType, slot: int | None, events: list[ev.Event]) -> bool:
        player = self.player
        if item_type is ItemType.WEAPON:
            return self._change_weapon(slot, events)
        if slot is None:
            return False
        item = player.backpack.take(item_type, slot)
        if item is None:
            return False
        match item_type:
            case ItemType.FOOD:
                player.heal(item.health)
            case ItemType.ELIXIR:
                stat, amount = item.stat_bonus()
                player.apply_temporary(stat, amount, item.duration)
            case ItemType.SCROLL:
                stat, amount = item.stat_bonus()
                player.apply_permanent(stat, amount)
        events.append(ev.ItemUsed(item))
        return True

    def _change_weapon(self, slot: int | None, events: list[ev.Event]) -> bool:
        player = self.player
        if slot is None:  # убрать оружие из рук, но оставить в рюкзаке
            if player.weapon is None:
                return False
            if not player.backpack.add(player.weapon):
                return False
            events.append(ev.WeaponUnequipped(player.weapon))
            player.weapon = None
            return True
        # Сначала проверяем место: при неудаче рюкзак и оружие остаются как были.
        drop_pos = None
        if player.weapon is not None:
            for cell in player.pos.neighbors():
                if (self.level.is_walkable(cell) and self.level.tile_at(cell) is not Tile.EXIT
                        and cell not in self.level.items and cell not in self.level.keys
                        and self.level.enemy_at(cell) is None):
                    drop_pos = cell
                    break
            if drop_pos is None:
                return False

        new_weapon = player.backpack.take(ItemType.WEAPON, slot)
        if new_weapon is None:
            return False
        old_weapon, player.weapon = player.weapon, new_weapon
        events.append(ev.WeaponEquipped(new_weapon))
        if old_weapon is not None:
            self.level.items[drop_pos] = old_weapon
            events.append(ev.WeaponDropped(old_weapon))
        return True

    # ------------------------------------------------------------------
    # Ход мира
    # ------------------------------------------------------------------
    def _end_of_turn(self, events: list[ev.Event]) -> None:
        for _ in self.player.tick_effects():
            events.append(ev.EffectExpired())
        for enemy in list(self.level.enemies):
            update_ghost_visibility(enemy, self.rng)
            if enemy.alive:
                self._enemy_turn(enemy, events)
            if not self.player.alive:
                self.state = GameState.LOST
                events.append(ev.PlayerDied())
                return


    def _enemy_turn(self, enemy: Enemy, events: list[ev.Event]) -> None:

        if enemy.disguised:
            if enemy.pos.manhattan(self.player.pos) > 1:
                return                              # лежит как предмет, не двигается
            enemy.disguised = False                 # игрок вплотную: маска спадает, мимик бьёт
            events.append(ev.MimicRevealed())

        if enemy.resting:                 # огр отдыхает: ход пропущен
            enemy.resting = False
            enemy.counter_ready = True
            return

        # Контратака огра готова сразу после одного хода отдыха.
        if not enemy.counter_ready:
            enemy.timer += 1
            if enemy.timer < enemy.spec.move_every:
                return
        enemy.timer = 0

        player_pos = self.player.pos

        if enemy.pos.manhattan(player_pos) == 1:
            self._enemy_attack(enemy, events)
            return

        if enemy.pos.manhattan(player_pos) <= enemy.hostility:
            occupied = {e.pos for e in self.level.enemies if e is not enemy}
            level = self.level

            def passable(p: Pos) -> bool:
                return p == player_pos or (
                    level.is_walkable(p) and level.tile_at(p) is not Tile.EXIT
                    and p not in occupied
                )

            path = bfs_path(enemy.pos, player_pos, passable, max_dist=enemy.hostility)
            if path:
                enemy.pos = path[0]
                return

        step = PATTERNS[enemy.kind](enemy, self.level, self.rng)
        if step is not None and step != player_pos:
            if enemy.kind is EnemyKind.WIZZARD:
                dx, dy = step.x - enemy.pos.x, step.y - enemy.pos.y
                if abs(dx) == abs(dy) == 1:
                    enemy.last_diagonal = (dx, dy)
            enemy.pos = step


    def _enemy_attack(self, enemy: Enemy, events: list[ev.Event]) -> None:
        result = combat.resolve_attack(enemy, self.player, self.rng)
        events.append(ev.EnemyAttacked(enemy.kind, result.hit, result.damage,
                                       result.drained_max_health, result.slept))
