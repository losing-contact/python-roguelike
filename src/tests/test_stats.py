from domain import events as ev
from domain.entities import EnemyKind
from domain.items import Item, ItemType
from domain.stats import RunStats


def test_player_hits_misses_and_received_hits_are_separate():
    stats = RunStats()
    for event in [
        ev.PlayerAttacked(EnemyKind.ZOMBIE, True, 20),
        ev.PlayerAttacked(EnemyKind.ZOMBIE, False, 0),
        ev.EnemyAttacked(EnemyKind.ZOMBIE, True, 10),
        ev.EnemyAttacked(EnemyKind.ZOMBIE, True, 10),
        ev.EnemyAttacked(EnemyKind.ZOMBIE, False, 0),
    ]:
        stats.record(event)
    assert stats.hits_dealt == 1
    assert stats.hits_missed == 1
    assert stats.hits_received == 2


def test_consumables_treasure_steps_and_level_are_counted():
    stats = RunStats()
    for kind in (ItemType.FOOD, ItemType.ELIXIR, ItemType.SCROLL):
        stats.record(ev.ItemUsed(Item(kind, 'test')))
    stats.record(ev.EnemyKilled(EnemyKind.ZOMBIE, 37))
    stats.record(ev.Moved())
    stats.record(ev.LevelChanged(2))
    assert stats == RunStats(
        treasure=37, level_reached=2, enemies_killed=1,
        food_eaten=1, elixirs_drunk=1, scrolls_read=1, steps=1,
    )
