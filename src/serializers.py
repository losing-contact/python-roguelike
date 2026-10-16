"""Перевод объектов игры в обычные словари и списки (их умеет записывать json) и обратно.

У каждого объекта две функции: ..._to_dict и ..._from_dict.
"""
from dataclasses import asdict

from domain.enemies.types import SPECS, EnemyKind
from domain.models.entities import ActiveEffect, Character, Enemy
from domain.models.exploration import Exploration
from domain.models.items import Backpack, Item, ItemType, Stat
from domain.models.level import Corridor, Level, Room
from domain.models.position import Pos
from domain.models.stats import RunStats
from domain.models.tile import Tile
from domain.session import GameSession

# Каждый тип клетки записываем одним символом, чтобы карту в файле можно было прочитать глазами
TILE_CHARS = {
    Tile.VOID: " ",
    Tile.WALL: "#",
    Tile.FLOOR: ".",
    Tile.DOORWAY: "+",
    Tile.CORRIDOR: ":",
    Tile.EXIT: ">",
}
CHAR_TILES = {char: tile for tile, char in TILE_CHARS.items()}


def pos_to_list(pos):
    return [pos.x, pos.y]


def pos_from_list(data):
    return Pos(data[0], data[1])


def item_to_dict(item):
    data = asdict(item)
    data["item_type"] = item.item_type.value   # Enum в файл не запишешь, берём его значение
    return data


def item_from_dict(data):
    data = dict(data)
    data["item_type"] = ItemType(data["item_type"])
    return Item(**data)


def backpack_to_dict(backpack):
    items = []
    for item_type in ItemType:
        if item_type is not ItemType.TREASURE:   # сокровища лежат не в списке, а числом
            items += [item_to_dict(item) for item in backpack.items_of(item_type)]
    return {"treasure": backpack.treasure, "items": items}


def backpack_from_dict(data):
    backpack = Backpack()
    backpack.treasure = data["treasure"]
    for item_data in data["items"]:
        backpack.add(item_from_dict(item_data))
    return backpack


def player_to_dict(player):
    return {
        "pos": pos_to_list(player.pos),
        "health": player.health,
        "max_health": player.max_health,
        "agility": player.agility,
        "strength": player.strength,
        "weapon": item_to_dict(player.weapon) if player.weapon else None,
        "backpack": backpack_to_dict(player.backpack),
        "effects": [
            {"stat": e.stat.value, "amount": e.amount, "turns_left": e.turns_left}
            for e in player.effects
        ],
    }


def player_from_dict(data):
    player = Character(pos_from_list(data["pos"]))
    player.health = data["health"]
    player.max_health = data["max_health"]
    player.agility = data["agility"]
    player.strength = data["strength"]
    if data["weapon"] is not None:
        player.weapon = item_from_dict(data["weapon"])
    player.backpack = backpack_from_dict(data["backpack"])
    player.effects = [
        ActiveEffect(Stat(e["stat"]), e["amount"], e["turns_left"]) for e in data["effects"]
    ]
    return player


def enemy_to_dict(enemy):
    return {
        "kind": enemy.kind.value,
        "pos": pos_to_list(enemy.pos),
        "health": enemy.health,
        "max_health": enemy.max_health,
        "agility": enemy.agility,
        "strength": enemy.strength,
        "timer": enemy.timer,
        "first_hit_spent": enemy.first_hit_spent,
    }


def enemy_from_dict(data):
    return Enemy(
        spec=SPECS[EnemyKind(data["kind"])],   # характеристики-шаблон берём по типу врага
        pos=pos_from_list(data["pos"]),
        health=data["health"],
        max_health=data["max_health"],
        agility=data["agility"],
        strength=data["strength"],
        timer=data["timer"],
        first_hit_spent=data["first_hit_spent"],
    )


def corridor_to_dict(corridor):
    return {
        "room_a": corridor.room_a,
        "room_b": corridor.room_b,
        "door_a": pos_to_list(corridor.door_a),
        "door_b": pos_to_list(corridor.door_b),
        "cells": [pos_to_list(cell) for cell in corridor.cells],
    }


def corridor_from_dict(data):
    return Corridor(
        data["room_a"],
        data["room_b"],
        pos_from_list(data["door_a"]),
        pos_from_list(data["door_b"]),
        [pos_from_list(cell) for cell in data["cells"]],
    )


def level_to_dict(level):
    return {
        "number": level.number,
        "width": level.width,
        "height": level.height,
        "tiles": ["".join(TILE_CHARS[tile] for tile in row) for row in level.tiles],
        "rooms": [asdict(room) for room in level.rooms],
        "corridors": [corridor_to_dict(c) for c in level.corridors],
        "start": pos_to_list(level.start),
        "exit": pos_to_list(level.exit),
        "start_room": level.start_room,
        "exit_room": level.exit_room,
        "enemies": [enemy_to_dict(e) for e in level.enemies],
        # ключом в json может быть только строка, поэтому предметы на полу - список пар
        "items": [{"pos": pos_to_list(pos), "item": item_to_dict(item)}
                  for pos, item in level.items.items()],
    }


def level_from_dict(data):
    return Level(
        number=data["number"],
        width=data["width"],
        height=data["height"],
        tiles=[[CHAR_TILES[char] for char in row] for row in data["tiles"]],
        rooms=[Room(**room) for room in data["rooms"]],
        corridors=[corridor_from_dict(c) for c in data["corridors"]],
        start=pos_from_list(data["start"]),
        exit=pos_from_list(data["exit"]),
        start_room=data["start_room"],
        exit_room=data["exit_room"],
        enemies=[enemy_from_dict(e) for e in data["enemies"]],
        items={pos_from_list(e["pos"]): item_from_dict(e["item"]) for e in data["items"]},
    )


def exploration_to_list(exploration):
    return sorted([pos.x, pos.y] for pos in exploration.seen)


def exploration_from_list(data):
    return Exploration({Pos(x, y) for x, y in data})


def session_to_dict(session):
    return {
        "total_levels": session.total_levels,
        "stats": asdict(session.stats),
        "player": player_to_dict(session.player),
        "level": level_to_dict(session.level),
        "exploration": exploration_to_list(session.exploration),
    }


def session_from_dict(data):
    return GameSession(
        total_levels=data["total_levels"],
        player=player_from_dict(data["player"]),
        level=level_from_dict(data["level"]),
        stats=RunStats(**data["stats"]),
        exploration=exploration_from_list(data["exploration"]),
    )
