from domain.balance import BACKPACK_SLOT_LIMIT, MIN_HEALTH_AFTER_EFFECT
from domain.entities import Character
from domain.items import Backpack, Item, ItemType, Stat


def apple():
    return Item(ItemType.FOOD, "Яблоко", health=20)


def test_backpack_holds_nine_items_per_type():
    bag = Backpack()
    for _ in range(BACKPACK_SLOT_LIMIT):
        assert bag.add(apple())
    assert not bag.add(apple())
    assert bag.is_full(ItemType.FOOD)
    assert bag.add(Item(ItemType.SCROLL, "Свиток силы", strength=5))  # другой тип - место есть


def test_treasure_lives_in_single_cell_and_is_never_full():
    bag = Backpack()
    for _ in range(50):
        assert bag.add(Item(ItemType.TREASURE, "Золото", cost=3))
    assert bag.treasure == 150


def test_take_returns_none_for_bad_index():
    bag = Backpack()
    bag.add(apple())
    assert bag.take(ItemType.FOOD, 5) is None
    assert bag.take(ItemType.FOOD, 0) is not None
    assert bag.items_of(ItemType.FOOD) == []


def test_stat_bonus_finds_the_nonzero_field():
    assert Item(ItemType.SCROLL, "s", agility=2).stat_bonus() == (Stat.AGILITY, 2)


def test_heal_is_capped_by_max_health():
    p = Character()
    p.health = 50
    p.heal(1000)
    assert p.health == p.max_health


def test_permanent_max_health_also_raises_health():
    p = Character()
    p.health = 60
    p.apply_permanent(Stat.MAX_HEALTH, 20)
    assert p.max_health == 120 and p.health == 80


def test_temporary_effect_expires():
    p = Character()
    base = p.strength
    p.apply_temporary(Stat.STRENGTH, 10, turns=3)
    assert p.strength == base + 10
    assert p.tick_effects() == [] and p.tick_effects() == []
    assert len(p.tick_effects()) == 1
    assert p.strength == base and p.effects == []


def test_health_stays_positive_after_max_health_elixir_expires():
    p = Character()
    p.apply_temporary(Stat.MAX_HEALTH, 30, turns=1)
    p.health = 5                       # игрок сильно ранен, пока эликсир действует
    p.tick_effects()
    assert p.max_health == 100
    assert p.health == MIN_HEALTH_AFTER_EFFECT
