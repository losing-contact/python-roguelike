import random

from domain import combat
from domain.balance import HIT_MAX, HIT_MIN, MIN_MAX_HEALTH, SCALE, VAMPIRE_DRAIN
from domain.enemies.factory import create_enemy
from domain.enemies.types import EnemyKind
from domain.models.entities import Character
from domain.models.items import Item, ItemType
from domain.models.position import Pos


def zombie(level=1):
    return create_enemy(EnemyKind.ZOMBIE, Pos(1, 1), level)


def vampire(level=1):
    return create_enemy(EnemyKind.VAMPIRE, Pos(1, 1), level)


def test_hit_chance_is_clamped():
    player, z = Character(), zombie()
    player.agility = 100
    assert combat.hit_chance(player, z) == HIT_MAX
    player.agility = -100
    assert combat.hit_chance(player, z) == HIT_MIN


def test_higher_agility_hits_more_often():
    player, z = Character(), zombie()
    low = combat.hit_chance(z, player)       # у зомби ловкость ниже
    high = combat.hit_chance(player, z)
    assert high > low


def test_miss_deals_no_damage(miss_rng):
    player, z = Character(), zombie()
    result = combat.resolve_attack(player, z, miss_rng)
    assert not result.hit and result.damage == 0
    assert z.health == z.max_health


def test_hit_deals_strength_damage(hit_rng):
    player, z = Character(), zombie()
    result = combat.resolve_attack(player, z, hit_rng)
    assert result.hit and result.damage == player.strength
    assert z.health == z.max_health - player.strength


def test_weapon_adds_to_damage(hit_rng):
    player, z = Character(), zombie()
    player.weapon = Item(ItemType.WEAPON, "Меч", strength=12)
    result = combat.resolve_attack(player, z, hit_rng)
    assert result.damage == player.strength + 12


def test_health_never_goes_below_zero(hit_rng):
    player, z = Character(), zombie()
    z.health = 1
    combat.resolve_attack(player, z, hit_rng)
    assert z.health == 0 and not z.alive


def test_first_hit_on_vampire_always_misses(hit_rng):
    player, v = Character(), vampire()
    first = combat.resolve_attack(player, v, hit_rng)
    second = combat.resolve_attack(player, v, hit_rng)
    assert not first.hit
    assert second.hit


def test_vampire_drains_max_health(hit_rng):
    player, v = Character(), vampire()
    result = combat.resolve_attack(v, player, hit_rng)
    assert result.hit
    assert result.drained_max_health == VAMPIRE_DRAIN
    assert player.max_health == 10 * SCALE - VAMPIRE_DRAIN
    assert player.health <= player.max_health


def test_vampire_cannot_drain_below_minimum(hit_rng):
    player, v = Character(), vampire()
    player.max_health = MIN_MAX_HEALTH
    player.health = player.max_health
    v.strength = 1
    combat.resolve_attack(v, player, hit_rng)
    assert player.max_health == MIN_MAX_HEALTH


def test_enemies_grow_with_level():
    assert zombie(10).max_health > zombie(1).max_health
    assert zombie(10).strength > zombie(1).strength
    assert zombie(10).agility > zombie(1).agility


def test_treasure_value_is_positive_and_scales():
    rng = random.Random(0)
    weak, strong = zombie(1), vampire(15)
    weak_values = [combat.treasure_value(weak, weak.hostility, rng) for _ in range(50)]
    strong_values = [combat.treasure_value(strong, strong.hostility, rng) for _ in range(50)]
    assert min(weak_values) >= 1
    assert max(strong_values) > max(weak_values)
