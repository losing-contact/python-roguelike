import random

from level_builder import level_from_ascii
from test_playthrough import bot_step

from domain import events as ev
from domain.commands import Move
from domain.entities import Character, EnemyKind, create_enemy
from domain.generation import generate_level
from domain.level import KeyColor, Pos
from domain.session import GameSession, GameState
from domain.visibility import compute_visible
from presentation.messages import format_event

RIGHT = Move(1, 0)


def session_on(*rows, total=1):
    """Игра на заранее нарисованных уровнях (по одной строке-коридору на уровень)."""
    def generator(number, rng, total_levels):
        return level_from_ascii([rows[number - 1]], number)

    return GameSession(random.Random(1), total_levels=total, generator=generator)


# --- ключи и двери в игре ---------------------------------------------------
def test_stepping_on_a_key_picks_it_up():
    session = session_on("@R:>")
    events = session.handle(RIGHT)
    assert session.player.keys == {KeyColor.RED}
    assert ev.KeyPickedUp(KeyColor.RED) in events
    assert session.level.keys == {}


def test_door_opens_with_the_right_key_and_we_step_into_it():
    session = session_on("@Rr:>")
    session.handle(RIGHT)
    events = session.handle(RIGHT)
    assert ev.DoorOpened(KeyColor.RED) in events
    assert session.player.pos == Pos(2, 0)
    assert session.level.doors == {}


def test_locked_door_does_not_let_the_player_in():
    session = session_on("@r:>")
    events = session.handle(RIGHT)
    assert events == [ev.DoorLocked(KeyColor.RED)]
    assert session.player.pos == Pos(0, 0)
    assert Pos(1, 0) in session.level.doors


def test_bumping_into_a_locked_door_does_not_spend_a_turn():
    session = session_on("@r:>")
    session.handle(RIGHT)
    assert session.stats.steps == 0


def test_wrong_key_does_not_open_the_door():
    session = session_on("@Br:>")
    session.handle(RIGHT)                            # подняли синий
    events = session.handle(RIGHT)
    assert events == [ev.DoorLocked(KeyColor.RED)]
    assert session.player.pos == Pos(1, 0)


def test_key_is_not_used_up_by_the_door():
    session = session_on("@Rr:r:>")
    for _ in range(3):
        session.handle(RIGHT)                        # ключ, первая дверь, коридор
    events = session.handle(RIGHT)                   # вторая красная дверь
    assert ev.DoorOpened(KeyColor.RED) in events


def test_keys_do_not_leave_the_level():
    session = session_on("@R>", "@:>", total=2)
    session.handle(RIGHT)
    assert session.player.keys
    session.handle(RIGHT)                            # выход
    assert session.level.number == 2
    assert session.player.keys == set()


def test_enemy_cannot_walk_through_a_locked_door():
    session = session_on("@:::r::>")
    enemy = create_enemy(EnemyKind.ZOMBIE, Pos(5, 0), 1)
    session.level.enemies.append(enemy)
    for _ in range(10):
        session._enemy_turn(enemy, [])
    assert enemy.pos.x > 4                           # враг остался за дверью


# --- видимость --------------------------------------------------------------
def test_a_locked_door_blocks_the_view():
    lv = level_from_ascii(["@::r:::"])
    seen = compute_visible(lv, Pos(0, 0), radius=8)
    assert Pos(3, 0) in seen                         # саму дверь видно
    assert Pos(4, 0) not in seen                     # а за ней нет


def test_an_opened_door_no_longer_blocks_the_view():
    lv = level_from_ascii(["@::r:::"])
    del lv.doors[Pos(3, 0)]
    assert Pos(5, 0) in compute_visible(lv, Pos(0, 0), radius=8)


# --- сообщения --------------------------------------------------------------
def test_messages_name_the_color():
    assert format_event(ev.KeyPickedUp(KeyColor.RED)) == "Вы нашли красный ключ"
    assert "жёлтый" in format_event(ev.DoorLocked(KeyColor.YELLOW))
    assert "синий" in format_event(ev.DoorOpened(KeyColor.BLUE))


# --- настоящие уровни -------------------------------------------------------
def test_levels_with_doors_can_be_finished_by_playing():
    """Бот проходит сгенерированные уровни с дверями: ключи подбирает, двери открывает."""
    played = 0
    for seed in range(25):
        level = generate_level(9, random.Random(seed))
        if not level.doors:
            continue
        player = Character(level.start)
        player.max_health = player.health = 10**6
        player.strength = 10**4
        session = GameSession(random.Random(seed), total_levels=1, player=player, level=level)
        for _ in range(3000):
            if session.state is not GameState.PLAYING:
                break
            bot_step(session)
        assert session.state is GameState.WON, f"seed {seed}: уровень с дверями не пройден"
        assert session.player.keys, f"seed {seed}: бот прошёл, не взяв ни одного ключа"
        played += 1
    assert played >= 15
