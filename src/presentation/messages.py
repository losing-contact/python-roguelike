"""События домена -> строки для игрока. Домен текстов не знает."""
from __future__ import annotations

from domain import events as ev
from domain.enemies.types import SPECS
from domain.models.items import Item, ItemType, Stat
from domain.models.keys import KeyColor

KEY_NAMES = {KeyColor.RED: "красный", KeyColor.YELLOW: "жёлтый", KeyColor.BLUE: "синий"}

STAT_NAMES = {
    Stat.MAX_HEALTH: "макс. здоровью",
    Stat.AGILITY: "ловкости",
    Stat.STRENGTH: "силе",
}

ITEM_TYPE_TITLES = {
    ItemType.WEAPON: "Оружие",
    ItemType.FOOD: "Еда",
    ItemType.ELIXIR: "Эликсиры",
    ItemType.SCROLL: "Свитки",
}


def item_label(item: Item) -> str:
    """«Меч (урон +12)», «Эликсир силы (+10 к силе на 30 ходов)»."""
    match item.item_type:
        case ItemType.FOOD:
            return f"{item.subtype} (+{item.health} здоровья)"
        case ItemType.WEAPON:
            return f"{item.subtype} (урон +{item.strength})"
        case ItemType.ELIXIR:
            stat, amount = item.stat_bonus()
            return f"{item.subtype} (+{amount} к {STAT_NAMES[stat]} на {item.duration} ходов)"
        case ItemType.SCROLL:
            stat, amount = item.stat_bonus()
            return f"{item.subtype} (+{amount} к {STAT_NAMES[stat]} навсегда)"
    return item.subtype


def format_event(event: ev.Event) -> str | None:
    match event:
        case ev.KeyPickedUp(color=color):
            return f"Вы нашли {KEY_NAMES[color]} ключ"
        case ev.DoorOpened(color=color):
            return f"Дверь открыта: {KEY_NAMES[color]} ключ подошёл"
        case ev.DoorLocked(color=color):
            return f"Дверь заперта: нужен {KEY_NAMES[color]} ключ"
        case ev.PlayerAttacked(target=kind, hit=True, damage=damage):
            return f"Вы ударили: {SPECS[kind].name} (-{damage})"
        case ev.PlayerAttacked(target=kind):
            return f"Вы промахнулись по: {SPECS[kind].name}"
        case ev.EnemyAttacked(attacker=kind, hit=True, damage=damage, drained_max_health=drained, slept=slept):
            drain = f", макс. здоровье -{drained}" if drained else ""
            sleep = ", вы уснули" if slept else ""
            return f"{SPECS[kind].name} бьёт вас (-{damage}{drain}{sleep})"
        case ev.EnemyAttacked(attacker=kind):
            return f"{SPECS[kind].name} промахнулся"
        case ev.EnemyKilled(kind=kind, treasure=treasure):
            return f"{SPECS[kind].name} повержен: +{treasure} сокровищ"
        case ev.ItemPickedUp(item=item):
            return f"Подобрано: {item.subtype}"
        case ev.BackpackFull(item=item):
            return f"Рюкзак полон, {item.subtype} остался на полу"
        case ev.ItemUsed(item=item):
            return f"Использовано: {item.subtype}"
        case ev.WeaponEquipped(item=item):
            return f"Вы взяли в руки: {item.subtype}"
        case ev.WeaponUnequipped(item=item):
            return f"{item.subtype} убран в рюкзак"
        case ev.WeaponDropped(item=item):
            return f"{item.subtype} упало на пол рядом"
        case ev.EffectExpired():
            return "Действие эликсира закончилось"
        case ev.LevelChanged(level=level):
            return f"Вы спустились на уровень {level}"
        case ev.PlayerSlept():
            return "Вы спите и пропускаете ход"
        case ev.PlayerDied():
            return "Вы погибли"
        case ev.GameWon():
            return "Вы прошли все уровни!"
        case ev.MimicRevealed():
            return "Это был мимик!"
    return None
