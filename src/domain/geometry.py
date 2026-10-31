"""Чистая геометрия сетки: поиск пути и линия Брезенхэма.

Здесь нет ни curses, ни знания об игре - только клетки и функция «проходима ли клетка».
Ray Casting для тумана войны находится в domain/visibility.py.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterator

from domain.level import Pos

Passable = Callable[[Pos], bool]


def bfs_distances(start: Pos, passable: Passable, max_dist: int | None = None) -> dict[Pos, int]:
    """Расстояния (в шагах по соседним клеткам) от start до всех достижимых клеток."""
    dist = {start: 0}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if max_dist is not None and dist[cur] >= max_dist:
            continue
        for nxt in cur.neighbors():
            if nxt not in dist and passable(nxt):
                dist[nxt] = dist[cur] + 1
                queue.append(nxt)
    return dist


def bfs_path(
    start: Pos, goal: Pos, passable: Passable, max_dist: int | None = None
) -> list[Pos] | None:
    """Кратчайший путь от start к goal без start, с goal в конце. None - пути нет.

    goal должна быть проходимой (иначе путь не найдётся).
    """
    if start == goal:
        return []
    # Наличие клетки в prev означает, что она уже посещена.
    prev: dict[Pos, Pos] = {start: start}
    queue = deque([(start, 0)])
    while queue:
        cur, d = queue.popleft()
        if max_dist is not None and d >= max_dist:
            continue
        for nxt in cur.neighbors():
            if nxt in prev or not passable(nxt):
                continue
            prev[nxt] = cur
            if nxt == goal:
                path = []
                cell = goal
                while cell != start:
                    path.append(cell)
                    cell = prev[cell]
                path.reverse()
                return path
            queue.append((nxt, d + 1))
    return None


def bresenham(a: Pos, b: Pos) -> Iterator[Pos]:
    """Клетки отрезка a-b (включая обе границы), алгоритм Брезенхэма."""
    x, y = a.x, a.y
    dx, dy = abs(b.x - a.x), abs(b.y - a.y)
    sx = 1 if b.x > a.x else -1
    sy = 1 if b.y > a.y else -1
    err = dx - dy
    while True:
        yield Pos(x, y)
        if (x, y) == (b.x, b.y):
            return
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
