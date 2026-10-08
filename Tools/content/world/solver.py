"""Exhaustive floor validator: keys/doors state search, softlock detection and reachability.

Keys are floor-local and interchangeable (DungeonGrid.OpenDoor spends any key on any door), so the state is
(opened doors, taken keys). From every reachable state the stairs and every treasure must stay reachable,
otherwise some door order can strand the player (softlock).
"""
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
TERMINAL = '<>'          # stepping here changes floor: reachable but not walked through


def _cells(rows, ch):
    return [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == ch]


def _region(rows, start, opened):
    h = len(rows)
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        if rows[y][x] in TERMINAL and (x, y) != start:
            continue
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if not (0 <= ny < h and 0 <= nx < len(rows[ny])):
                continue
            c = rows[ny][nx]
            if c == '#' or (nx, ny) in seen:
                continue
            if c == 'L' and (nx, ny) not in opened:
                continue
            seen.add((nx, ny))
            q.append((nx, ny))
    return seen


def analyse(rows):
    """Returns dict(ok, problems, states, steps_full) for one floor layout."""
    problems = []
    starts = _cells(rows, 'S')
    if len(starts) != 1:
        return dict(ok=False, problems=['need exactly one S, got %d' % len(starts)], states=0)
    start = starts[0]
    doors = _cells(rows, 'L')
    keys = _cells(rows, 'K')
    goals = _cells(rows, '>') or _cells(rows, 'B')
    chests = _cells(rows, 'T')
    if len(_cells(rows, '<')) != 1:
        problems.append('need exactly one <')
    if len(keys) < len(doors):
        problems.append('fewer keys (%d) than doors (%d)' % (len(keys), len(doors)))

    def successors(state):
        opened, taken = state
        reg = _region(rows, start, opened)
        held = len(taken) - len(opened)
        out = []
        for k in keys:
            if k in reg and k not in taken:
                out.append((opened, taken | {k}))
        if held > 0:
            for d in doors:
                if d in opened:
                    continue
                if any((d[0] + dx, d[1] + dy) in reg and rows[d[1] + dy][d[0] + dx] not in TERMINAL for dx, dy in DIRS):
                    out.append((opened | {d}, taken))
        return reg, out

    init = (frozenset(), frozenset())
    graph, regions = {}, {}
    q = deque([init])
    seen = {init}
    while q:
        s = q.popleft()
        reg, nxt = successors(s)
        regions[s] = reg
        graph[s] = nxt
        for n in nxt:
            if n not in seen:
                seen.add(n)
                q.append(n)
    # A target is "eventually reachable" from s when some state reachable from s has it in its region.
    targets = set(goals) | set(chests) | set(keys)
    memo = {}

    def closure(s):
        if s in memo:
            return memo[s]
        acc = set(regions[s])
        stack, vis = [s], {s}
        while stack:
            cur = stack.pop()
            acc |= regions[cur]
            for n in graph[cur]:
                if n not in vis:
                    vis.add(n)
                    stack.append(n)
        memo[s] = acc
        return acc

    for s in graph:
        reach = closure(s)
        missing = [t for t in targets if t not in reach]
        if missing:
            problems.append('softlock from state doors=%s keys=%s: unreachable %s' % (
                sorted(s[0]), sorted(s[1]), sorted(missing)[:4]))
            break
    full = _region(rows, start, frozenset(doors))
    walk = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c != '#']
    isolated = [p for p in walk if p not in full]
    if isolated:
        problems.append('isolated cells %s' % isolated[:5])
    if not goals or goals[0] not in closure(init):
        problems.append('stairs/boss unreachable')
    return dict(ok=not problems, problems=problems, states=len(graph), walkable=len(walk))


def foe_passable(rows, p):
    x, y = p
    return 0 <= y < len(rows) and 0 <= x < len(rows[y]) and rows[y][x] not in '#SLW<>BE'


def check_patrol(rows, points):
    """Every waypoint FOE-passable and mutually reachable for FOEs."""
    if not points or not all(foe_passable(rows, p) for p in points):
        return False
    start = points[0]
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if n not in seen and foe_passable(rows, n):
                seen.add(n)
                q.append(n)
    return all(p in seen for p in points)


def exploration_steps(rows, coverage=0.65):
    """Rough step count to explore `coverage` of a floor: a depth-first walk from S over the open cells
    (every corridor walked out and back), scaled by coverage, plus the direct S->stairs path."""
    start = _cells(rows, 'S')[0]
    full = _region(rows, start, frozenset(_cells(rows, 'L')))
    order, seen = 0, {start}
    stack = [start]
    # DFS edge count ~ 2 * (tree edges); loops add little. Each new cell costs ~2 steps (in and back out).
    tree_edges = len(full) - 1
    return int(tree_edges * 2 * coverage)
