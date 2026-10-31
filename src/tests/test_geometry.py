from domain.geometry import bfs_distances, bfs_path, bresenham
from domain.level import Pos

OPEN = {Pos(x, y) for x in range(5) for y in range(5)}


def passable(p):
    return p in OPEN


def test_path_goes_straight_and_excludes_start():
    path = bfs_path(Pos(0, 0), Pos(3, 0), passable)
    assert path == [Pos(1, 0), Pos(2, 0), Pos(3, 0)]


def test_path_to_self_is_empty():
    assert bfs_path(Pos(1, 1), Pos(1, 1), passable) == []


def test_path_goes_around_wall():
    wall = {Pos(2, 0), Pos(2, 1), Pos(2, 2)}
    path = bfs_path(Pos(0, 0), Pos(4, 0), lambda p: p in OPEN and p not in wall)
    assert path is not None
    assert path[-1] == Pos(4, 0)
    assert not wall & set(path)
    assert len(path) == 4 + 2 * 3  # 4 вправо + обход стены высотой 3 вниз и обратно


def test_no_path_returns_none():
    wall = {Pos(2, y) for y in range(5)}
    assert bfs_path(Pos(0, 0), Pos(4, 0), lambda p: p in OPEN and p not in wall) is None


def test_max_dist_limits_search():
    assert bfs_path(Pos(0, 0), Pos(4, 0), passable, max_dist=3) is None
    assert bfs_path(Pos(0, 0), Pos(4, 0), passable, max_dist=4) is not None


def test_path_steps_are_adjacent():
    path = bfs_path(Pos(0, 0), Pos(4, 4), passable)
    cells = [Pos(0, 0), *path]
    assert all(a.manhattan(b) == 1 for a, b in zip(cells, cells[1:]))


def test_bfs_distances():
    dist = bfs_distances(Pos(0, 0), passable)
    assert dist[Pos(0, 0)] == 0
    assert dist[Pos(4, 4)] == 8
    assert max(bfs_distances(Pos(0, 0), passable, max_dist=2).values()) == 2


def test_bresenham_includes_both_ends():
    line = list(bresenham(Pos(0, 0), Pos(5, 2)))
    assert line[0] == Pos(0, 0) and line[-1] == Pos(5, 2)
    assert len(line) == 6


def test_bresenham_horizontal_and_reverse():
    assert list(bresenham(Pos(0, 0), Pos(3, 0))) == [Pos(i, 0) for i in range(4)]
    assert list(bresenham(Pos(3, 0), Pos(0, 0))) == [Pos(i, 0) for i in (3, 2, 1, 0)]
