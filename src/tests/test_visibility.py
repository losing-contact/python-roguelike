from level_builder import level_from_ascii

from domain.level import Pos
from domain.visibility import compute_visible


def test_ray_sees_a_wall_but_not_the_cell_behind_it():
    level = level_from_ascii(['@:#..'])
    visible = compute_visible(level, level.start)
    assert Pos(2, 0) in visible
    assert Pos(3, 0) not in visible


def test_ray_cannot_cross_the_corner_between_two_walls():
    level = level_from_ascii(['@#', '#.'])
    visible = compute_visible(level, level.start)
    assert Pos(1, 0) in visible and Pos(0, 1) in visible
    assert Pos(1, 1) not in visible


def test_room_is_fully_visible_but_not_the_corridor_outside():
    level = level_from_ascii(['#######', '#000+::', '#000###', '#######'], start=Pos(1, 1))
    visible = compute_visible(level, level.start)
    assert set(level.rooms[0].footprint()) <= visible
    assert Pos(5, 1) not in visible


def test_view_from_corridor_reveals_only_part_of_room():
    level = level_from_ascii(
        ['#######', '#000+::', '#000###', '#000###', '#000###', '#######'],
        start=Pos(6, 1),
    )
    visible = compute_visible(level, level.start)
    assert Pos(3, 1) in visible
    assert Pos(3, 4) not in visible


def test_visible_cells_stay_inside_level_and_radius():
    level = level_from_ascii(['@:::::', '::::::', '::::::'])
    visible = compute_visible(level, level.start, radius=2)
    assert all(level.in_bounds(p) and p.x * p.x + p.y * p.y <= 4 for p in visible)
