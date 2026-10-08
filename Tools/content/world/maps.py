"""Deterministic dungeon floor layouts for the campaign (13 zones x 3 floors).

A floor is carved on a node lattice (odd coordinates). The lattice is split into zones that are chained
start -> stairs through single gate corridors; some gates are locked doors whose key lies in an earlier zone.
Dead ends receive the floor's points of interest: up/down stairs, warp, treasure, keys, lore stones, a spring;
vaults are dead ends behind a locked door; events guard treasure.

Layout styles (zone 'style' in spec.CHAPTERS) differ in structure, not colour:
- maze: randomised spanning tree plus a few loops, small rooms (the original generator, used by the gates).
- tunnels: long straight parallel E-W tunnels joined by a few short cross passages, one platform room.
- aisles: a regular grid of long vertical aisles and bays, many loops, two big halls.
- cave: a winding random walk per zone with wide chambers and uneven, branching passages.
- halls: one or two long central corridors with small pockets (classrooms, wards) off both sides, one door each.
- streets: a Manhattan grid of streets around solid blocks, with two plazas and cul-de-sacs.

Grid symbols (DungeonGrid.Markers): # wall . floor S start < up > down W warp T treasure E event battle
B boss L locked door K key X trap H spring N lore stone.
"""
import random
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
STYLES = ('maze', 'tunnels', 'aisles', 'cave', 'halls', 'streets')


class FloorSpec:
    """What one floor needs. Counts are targets; generation retries seeds until the validator passes."""

    def __init__(self, size, zones, seed, locked_gates=1, vaults=1, treasures=6, lore=2, traps=2, events=1,
                 foes=1, boss=False, spring=False, warp=False, midboss=False, rooms=2, loop_chance=0.14,
                 down_stairs=True, style='maze'):
        self.size = size
        self.zones = zones
        self.seed = seed
        self.locked_gates = locked_gates
        self.vaults = vaults
        self.treasures = treasures
        self.lore = lore
        self.traps = traps
        self.events = events
        self.foes = foes
        self.boss = boss
        self.spring = spring
        self.warp = warp
        self.midboss = midboss
        self.rooms = rooms
        self.loop_chance = loop_chance
        self.down_stairs = down_stairs
        self.style = style


class Layout:
    """A carved floor plus the metadata the data builder needs (patrol routes, cells by role)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [['#'] * w for _ in range(h)]
        self.zone_of = {}            # node cell -> zone index in chain order
        self.patrols = []            # list of (kind, [cells]) kind: 'foe' | 'midboss'
        self.vault_cells = []        # treasure cells behind locked doors
        self.guarded_cells = []      # treasure cells behind an event battle
        self.event_cells = []
        self.main_path = []
        self.start = None

    def rows(self):
        return [''.join(r) for r in self.g]

    def get(self, p):
        x, y = p
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.g[y][x]
        return '#'

    def set(self, p, c):
        self.g[p[1]][p[0]] = c

    def open(self, p):
        return self.get(p) != '#'

    def neighbors(self, p):
        for dx, dy in DIRS:
            q = (p[0] + dx, p[1] + dy)
            if self.open(q):
                yield q

    def degree(self, p):
        return sum(1 for _ in self.neighbors(p))

    def cells(self, marker=None):
        for y in range(self.h):
            for x in range(self.w):
                c = self.g[y][x]
                if (marker is None and c != '#') or c == marker:
                    yield (x, y)

    def bfs(self, src, passable=None):
        passable = passable or (lambda p: self.get(p) != '#')
        dist = {src: 0}
        q = deque([src])
        while q:
            p = q.popleft()
            for dx, dy in DIRS:
                n = (p[0] + dx, p[1] + dy)
                if n not in dist and passable(n):
                    dist[n] = dist[p] + 1
                    q.append(n)
        return dist

    def path(self, src, dst, passable=None):
        passable = passable or (lambda p: self.get(p) != '#')
        prev = {src: None}
        q = deque([src])
        while q:
            p = q.popleft()
            if p == dst:
                break
            for dx, dy in DIRS:
                n = (p[0] + dx, p[1] + dy)
                if n not in prev and passable(n):
                    prev[n] = p
                    q.append(n)
        if dst not in prev:
            return []
        out = [dst]
        while prev[out[-1]] is not None:
            out.append(prev[out[-1]])
        return out[::-1]


def _bands(n, parts):
    """Split range(n) into `parts` contiguous bands of near-equal size."""
    out, start = [], 0
    for i in range(parts):
        size = n // parts + (1 if i < n % parts else 0)
        out.append(range(start, start + size))
        start += size
    return out


def _zone_chain(zx, zy, rng):
    """Hamiltonian snake through the zx * zy zone grid, randomly mirrored/transposed."""
    order = []
    transpose = rng.random() < 0.5 and zx == zy
    a, b = (zy, zx) if transpose else (zx, zy)
    for j in range(b):
        row = list(range(a)) if j % 2 == 0 else list(range(a - 1, -1, -1))
        for i in row:
            order.append((j, i) if transpose else (i, j))
    if rng.random() < 0.5:
        order = [(zx - 1 - x, y) for x, y in order]
    if rng.random() < 0.5:
        order = [(x, zy - 1 - y) for x, y in order]
    return order


class _DSU:
    def __init__(self):
        self.p = {}

    def find(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self.p[ra] = rb
        return True


def carve(spec):
    """Carve corridors/rooms. Returns (layout, gates, rng); gates[k] is the cell between chain zone k and k+1."""
    if spec.style in (None, 'maze'):
        return _carve_maze(spec)
    return _carve_styled(spec)


def _carve_maze(spec):
    rng = random.Random(spec.seed)
    W = H = spec.size
    L = Layout(W, H)
    nw, nh = (W - 1) // 2, (H - 1) // 2
    zx, zy = spec.zones
    xb, yb = _bands(nw, zx), _bands(nh, zy)
    chain = _zone_chain(zx, zy, rng)
    zindex = {z: k for k, z in enumerate(chain)}

    def zone(i, j):
        bx = next(k for k, r in enumerate(xb) if i in r)
        by = next(k for k, r in enumerate(yb) if j in r)
        return zindex[(bx, by)]

    def cell(i, j):
        return (2 * i + 1, 2 * j + 1)

    nodes = [(i, j) for j in range(nh) for i in range(nw)]
    for i, j in nodes:
        L.zone_of[cell(i, j)] = zone(i, j)
        L.set(cell(i, j), '.')
    dsu = _DSU()

    # Rooms: 2x2 / 3x2 node blocks fully opened (no pillar), never spanning two zones.
    rooms = []
    for _ in range(spec.rooms * 6):
        if len(rooms) >= spec.rooms:
            break
        rw, rh = rng.choice(((2, 2), (3, 2), (2, 3), (2, 2)))
        i0, j0 = rng.randrange(0, nw - rw + 1), rng.randrange(0, nh - rh + 1)
        block = [(i, j) for i in range(i0, i0 + rw) for j in range(j0, j0 + rh)]
        if len({zone(i, j) for i, j in block}) != 1:
            continue
        if any(abs(i - a) <= rw and abs(j - b) <= rh for a, b, _, _ in rooms for i, j in [(i0, j0)]):
            continue
        rooms.append((i0, j0, rw, rh))
        for x in range(2 * i0 + 1, 2 * (i0 + rw)):
            for y in range(2 * j0 + 1, 2 * (j0 + rh)):
                L.set((x, y), '.')
        for i, j in block:
            dsu.union((i0, j0), (i, j))
    L.rooms = [(2 * i + 1, 2 * j + 1, 2 * w - 1, 2 * h - 1) for i, j, w, h in rooms]

    def link(a, b):
        (i, j), (k, l) = a, b
        L.set((i + k + 1, j + l + 1), '.')

    # Spanning tree inside each zone, then a few loop edges.
    edges = []
    for i, j in nodes:
        for di, dj in ((1, 0), (0, 1)):
            k, l = i + di, j + dj
            if k < nw and l < nh and zone(i, j) == zone(k, l):
                edges.append(((i, j), (k, l)))
    rng.shuffle(edges)
    spare = []
    for a, b in edges:
        if dsu.union(a, b):
            link(a, b)
        else:
            spare.append((a, b))
    for a, b in spare:
        mid = (a[0] + b[0] + 1, a[1] + b[1] + 1)
        if L.get(mid) == '#' and rng.random() < spec.loop_chance:
            link(a, b)

    # Chain gates: one corridor between consecutive zones.
    gates = []
    for k in range(len(chain) - 1):
        cands = []
        for i, j in nodes:
            for di, dj in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                a, b = i + di, j + dj
                if 0 <= a < nw and 0 <= b < nh and zone(i, j) == k and zone(a, b) == k + 1:
                    cands.append(((i, j), (a, b)))
        a, b = rng.choice(cands)
        link(a, b)
        gates.append((a[0] + b[0] + 1, a[1] + b[1] + 1))
    L.chain = chain
    L.zone_fn = zone
    L.node_cell = cell
    L.nodes = nodes
    L.nw, L.nh = nw, nh
    return L, gates, rng


# ------------------------------------------------------------------ styled layouts
# A style returns the open node set plus how the generic carver should join them: base priority per edge (lower
# is linked first, so 0 makes straight lines), loop chance per spare edge, banned edges (single doors) and room
# blocks (fully open, all inner edges forced). Zones, gates, locks and features are shared with the maze.

def _block(i0, j0, w, h, nw, nh):
    return [(i, j) for i in range(i0, i0 + w) for j in range(j0, j0 + h) if 0 <= i < nw and 0 <= j < nh]


def _one_zone(zone, nodes):
    return len({zone(i, j) for i, j in nodes}) == 1


def _style_tunnels(nw, nh, rng, zone, xb, yb):
    open_ = {(i, j) for j in range(0, nh, 2) for i in range(nw)}   # parallel E-W tunnels on even node rows
    for j in range(1, nh - 1, 2):                                   # cross passages on the gap rows
        for band in xb:
            for _ in range(1 + (1 if rng.random() < 0.35 else 0)):
                open_.add((rng.choice(list(band)), j))
    rooms = []
    for _ in range(12):                                             # one platform spanning two tunnels
        if rooms or nh < 5 or rng.random() > 0.7:
            break
        i0, j0 = rng.randrange(0, nw - 1), 2 * rng.randrange(0, (nh - 1) // 2)
        block = _block(i0, j0, 2, 3, nw, nh)
        if len(block) == 6 and _one_zone(zone, block):
            rooms.append(block)
            open_ |= set(block)
    return dict(open=open_, base=lambda a, b: 0.0 if a[1] == b[1] else 1.5,
                loop=lambda a, b: 0.0 if a[1] == b[1] else 0.3, banned=set(), rooms=rooms)


def _style_aisles(nw, nh, rng, zone, xb, yb):
    open_ = {(i, j) for i in range(nw) for j in range(nh) if i % 2 == 0 or j % 4 == 0}
    rooms = []
    for _ in range(2):                                              # two big halls cut into the grid
        for _try in range(30):
            i0, j0 = rng.randrange(0, nw - 2), rng.randrange(0, nh - 2)
            block = _block(i0, j0, 3, 3, nw, nh)
            if len(block) == 9 and _one_zone(zone, block) and not any(set(block) & set(r) for r in rooms):
                rooms.append(block)
                open_ |= set(block)
                break
    return dict(open=open_, base=lambda a, b: 0.0 if a[0] == b[0] else 0.8,
                loop=lambda a, b: 0.25 if a[0] == b[0] else 0.35, banned=set(), rooms=rooms)


def _path_into(open_, node, members):
    """Nodes (inside `members`) that join `node` to the open set by the shortest walk; empty if already open."""
    if node in open_:
        return set()
    prev = {node: None}
    q = deque([node])
    while q:
        p = q.popleft()
        for dx, dy in DIRS:
            n = (p[0] + dx, p[1] + dy)
            if n not in members or n in prev:
                continue
            if n in open_:
                out = set()
                cur = p
                while cur is not None:
                    out.add(cur)
                    cur = prev[cur]
                return out
            prev[n] = p
            q.append(n)
    return {node}


def _style_cave(nw, nh, rng, zone, xb, yb):
    open_ = set()
    by_zone = {}
    for i in range(nw):
        for j in range(nh):
            by_zone.setdefault(zone(i, j), []).append((i, j))
    for z in sorted(by_zone):                                       # one winding walk per zone keeps it connected
        members = set(by_zone[z])
        target = int(len(members) * 0.6)
        cur = sorted(members)[rng.randrange(len(members))]
        mine = {cur}
        d = DIRS[rng.randrange(4)]
        steps = 0
        while len(mine) < target and steps < 4000:
            steps += 1
            if rng.random() < 0.3:
                d = DIRS[rng.randrange(4)]
            nxt = (cur[0] + d[0], cur[1] + d[1])
            if nxt not in members:
                d = DIRS[rng.randrange(4)]
                continue
            cur = nxt
            mine.add(cur)
            if rng.random() < 0.18:                                 # wide chamber around this step
                for dx, dy in DIRS:
                    q = (cur[0] + dx, cur[1] + dy)
                    if q in members:
                        mine.add(q)
        open_ |= mine
    # Chain neighbours must touch: open a boundary pair per zone pair, joined to each zone's walk by a short path.
    for z in sorted(by_zone)[:-1]:
        pairs = [(p, q) for p in sorted(by_zone[z]) for q in ((p[0] + 1, p[1]), (p[0], p[1] + 1), (p[0] - 1, p[1]),
                 (p[0], p[1] - 1)) if 0 <= q[0] < nw and 0 <= q[1] < nh and zone(*q) == z + 1]
        if not pairs:
            continue
        p, q = pairs[rng.randrange(len(pairs))]
        for node, zz in ((p, z), (q, z + 1)):
            open_ |= _path_into(open_, node, {r for r in by_zone[zz]})
        open_ |= {p, q}

    def deg(p):
        return sum(1 for dx, dy in DIRS if (p[0] + dx, p[1] + dy) in open_)

    def chamber(a, b):
        return deg(a) >= 3 and deg(b) >= 3

    return dict(open=open_, base=lambda a, b: 0.0 if chamber(a, b) else 1.0,
                loop=lambda a, b: 0.8 if chamber(a, b) else 0.12, banned=set(), rooms=[])


def _style_halls(nw, nh, rng, zone, xb, yb):
    """One or two spines (long corridors) across the zone strip; pockets off both sides, one door each."""
    spines = [nh // 2] if nh <= 9 else [nh // 3, (2 * nh) // 3]
    open_ = {(i, r) for r in spines for i in range(nw)}
    if len(spines) == 2:
        for band in xb:                                             # a crossover in every zone
            cols = [i for i in band if 1 <= i <= nw - 2]
            if cols:
                i = rng.choice(cols)
                open_ |= {(i, j) for j in range(spines[0], spines[1] + 1)}
    wide = rng.random() < 0.5
    w, step = (2, 3) if wide else (1, 2)
    banned = set()
    for k, r in enumerate(spines):
        up = spines[k - 1] + 2 if k > 0 else 0
        down = spines[k + 1] - 2 if k + 1 < len(spines) else nh - 1
        for i in range(1, nw - 1, step):
            if i + w - 1 > nw - 2:
                break
            for side in (-1, 1):
                if rng.random() < 0.2:
                    continue
                cells_ = []
                for dd in (1, 2):
                    j = r + side * dd
                    if (side < 0 and j < up) or (side > 0 and j > down) or not (0 <= j < nh):
                        break
                    cells_ += [(x, j) for x in range(i, i + w)]
                if not cells_ or any(p in open_ for p in cells_) or not _one_zone(zone, cells_ + [(i, r)]):
                    continue
                open_ |= set(cells_)
                for x in range(i + 1, i + w):                       # one door per pocket
                    banned.add(frozenset({(x, r), (x, r + side)}))
    spine_rows = set(spines)
    return dict(open=open_, base=lambda a, b: 0.0 if (a[1] == b[1] and a[1] in spine_rows) else 0.6,
                loop=lambda a, b: 0.04, banned=banned, rooms=[])


def _style_streets(nw, nh, rng, zone, xb, yb):
    open_ = {(i, j) for i in range(nw) for j in range(nh) if i % 3 == 0 or j % 3 == 0}
    blocks = [(i0, j0) for i0 in range(1, nw - 1, 3) for j0 in range(1, nh - 1, 3)]
    rng.shuffle(blocks)
    rooms = []
    for i0, j0 in blocks:                                           # two plazas: open solid blocks
        if len(rooms) == 2:
            break
        block = _block(i0, j0, 2, 2, nw, nh)
        if len(block) == 4 and _one_zone(zone, block):
            rooms.append(block)
            open_ |= set(block)
    return dict(open=open_, base=lambda a, b: 0.0, loop=lambda a, b: 0.3, banned=set(), rooms=rooms)


STYLE_FN = {'tunnels': _style_tunnels, 'aisles': _style_aisles, 'cave': _style_cave,
            'halls': _style_halls, 'streets': _style_streets}


def _carve_styled(spec):
    rng = random.Random(spec.seed)
    W = H = spec.size
    L = Layout(W, H)
    nw, nh = (W - 1) // 2, (H - 1) // 2
    zx, zy = spec.zones
    xb, yb = _bands(nw, zx), _bands(nh, zy)
    chain = _zone_chain(zx, zy, rng)
    zindex = {z: k for k, z in enumerate(chain)}

    def zone(i, j):
        bx = next(k for k, r in enumerate(xb) if i in r)
        by = next(k for k, r in enumerate(yb) if j in r)
        return zindex[(bx, by)]

    def cell(i, j):
        return (2 * i + 1, 2 * j + 1)

    nodes = [(i, j) for j in range(nh) for i in range(nw)]
    for i, j in nodes:
        L.zone_of[cell(i, j)] = zone(i, j)
    plan = STYLE_FN[spec.style](nw, nh, rng, zone, xb, yb)
    open_, banned, rooms = plan['open'], plan['banned'], plan['rooms']
    forced = set()
    for block in rooms:
        bs = set(block)
        for a in block:
            for dx, dy in ((1, 0), (0, 1)):
                b = (a[0] + dx, a[1] + dy)
                if b in bs:
                    forced.add(frozenset({a, b}))
    for p in open_:
        L.set(cell(*p), '.')
    for block in rooms:
        for a in block:
            for dx, dy in ((1, 0), (0, 1)):
                b = (a[0] + dx, a[1] + dy)
                if b in set(block):
                    L.set((cell(*a)[0] + dx, cell(*a)[1] + dy), '.')

    def mid(a, b):
        return (a[0] + b[0] + 1, a[1] + b[1] + 1)

    def link(a, b):
        L.set(mid(a, b), '.')

    edges = []
    for p in sorted(open_):
        for q in ((p[0] + 1, p[1]), (p[0], p[1] + 1)):
            if q in open_ and zone(*p) == zone(*q) and frozenset({p, q}) not in banned:
                edges.append((p, q))
    noise = {e: rng.random() * 0.6 for e in edges}
    base, loop_p = plan['base'], plan['loop']
    edges.sort(key=lambda e: (-1.0 if frozenset(e) in forced else base(*e)) + noise[e])
    dsu = _DSU()
    spare = []
    for a, b in edges:
        if dsu.union(a, b):
            link(a, b)
        else:
            spare.append((a, b))
    for a, b in spare:
        p = 1.0 if frozenset({a, b}) in forced else loop_p(a, b)
        if L.get(mid(a, b)) == '#' and rng.random() < p:
            link(a, b)
    for z in range(len(chain)):
        roots = {dsu.find(p) for p in open_ if zone(*p) == z}
        if len(roots) != 1:
            raise ValueError('zone %d is not one piece' % z)
    gates = []
    for k in range(len(chain) - 1):
        cands = []
        for p in sorted(open_):
            if zone(*p) != k:
                continue
            for dx, dy in DIRS:
                q = (p[0] + dx, p[1] + dy)
                if q in open_ and zone(*q) == k + 1:
                    cands.append((p, q))
        if not cands:
            raise ValueError('no gate between zones %d and %d' % (k, k + 1))
        a, b = cands[rng.randrange(len(cands))]
        link(a, b)
        gates.append(mid(a, b))
    L.rooms = [(2 * min(p[0] for p in r) + 1, 2 * min(p[1] for p in r) + 1,
                2 * (max(p[0] for p in r) - min(p[0] for p in r)) + 1,
                2 * (max(p[1] for p in r) - min(p[1] for p in r)) + 1) for r in rooms]
    L.chain = chain
    L.zone_fn = zone
    L.node_cell = cell
    L.nodes = nodes
    L.nw, L.nh = nw, nh
    return L, gates, rng


def dead_ends(L, exclude=()):
    out = []
    for p in L.cells('.'):
        if p in exclude:
            continue
        if L.degree(p) == 1 and p[0] % 2 == 1 and p[1] % 2 == 1:
            out.append(p)
    return out


def node_zone(L, p):
    """Zone of a cell (nearest node)."""
    x, y = p
    i, j = min(max((x - 1) // 2, 0), L.nw - 1), min(max((y - 1) // 2, 0), L.nh - 1)
    return L.zone_fn(i, j)


def _corridor_neighbor(L, p):
    ns = list(L.neighbors(p))
    return ns[0] if len(ns) == 1 else None


def _ensure_dead_ends(L, rng, zone, need, avoid):
    """Cut extra dead ends in a zone by removing one link of a junction node (keeps zone connected)."""
    tries = 0
    while len([d for d in dead_ends(L, avoid) if node_zone(L, d) == zone]) < need and tries < 200:
        tries += 1
        cands = [p for p in L.cells('.') if p[0] % 2 == 1 and p[1] % 2 == 1 and node_zone(L, p) == zone
                 and L.degree(p) >= 3 and not _in_room(L, p)]
        if not cands:
            return
        p = rng.choice(cands)
        links = [q for q in L.neighbors(p) if (q[0] % 2 == 0) != (q[1] % 2 == 0) and L.get(q) == '.'
                 and q not in avoid and not _in_room(L, q)]
        rng.shuffle(links)
        for q in links:
            L.set(q, '#')
            if _connected(L):
                break
            L.set(q, '.')


def _in_room(L, p):
    return any(x <= p[0] < x + w and y <= p[1] < y + h for x, y, w, h in L.rooms)


def _connected(L):
    cells = list(L.cells())
    if not cells:
        return True
    return len(L.bfs(cells[0])) == len(cells)


def build(spec):
    """Generate a full floor layout for `spec` (raises ValueError when a seed cannot satisfy the spec)."""
    L, gates, rng = carve(spec)
    zones = len(L.chain)
    last = zones - 1
    reserved = set()

    # Locked gates: the later chain gates are locked first (they protect the stairs side).
    lock_idx = sorted(rng.sample(range(len(gates)), min(spec.locked_gates, len(gates))))
    for k in lock_idx:
        L.set(gates[k], 'L')
        reserved.add(gates[k])

    want_per_zone = {z: 1 for z in range(zones)}
    want_per_zone[0] = 3
    want_per_zone[last] = 3
    for z in range(zones):
        _ensure_dead_ends(L, rng, z, want_per_zone[z] + spec.treasures // zones, reserved)

    def free_dead_ends(zone=None):
        return [d for d in dead_ends(L, reserved) if (zone is None or node_zone(L, d) == zone) and L.get(d) == '.']

    # Up stairs + start in zone 0, at the dead end closest to the zone's corner.
    ups = free_dead_ends(0)
    if not ups:
        raise ValueError('no dead end for up stairs')
    corner = L.node_cell(*[(0 if L.chain[0][0] == 0 else L.nw - 1), (0 if L.chain[0][1] == 0 else L.nh - 1)])
    up = min(ups, key=lambda d: abs(d[0] - corner[0]) + abs(d[1] - corner[1]))
    start = _corridor_neighbor(L, up)
    L.set(up, '<')
    L.set(start, 'S')
    reserved |= {up, start}
    L.start = start
    dist = L.bfs(start, lambda p: L.get(p) != '#')

    # Down stairs (or the final boss chamber) at the farthest dead end of the last zone.
    downs = free_dead_ends(last)
    if not downs:
        raise ValueError('no dead end for stairs')
    down = max(downs, key=lambda d: dist.get(d, -1))
    if dist.get(down, -1) < 0:
        raise ValueError('stairs unreachable')
    before = _corridor_neighbor(L, down)
    if spec.down_stairs:
        L.set(down, '>')
    reserved |= {down, before}
    if spec.boss:
        L.set(before, 'B')
        if not spec.down_stairs:
            L.set(down, '.')
    boss_cell = before if spec.boss else None
    L.main_path = L.path(start, down, lambda p: L.get(p) != '#')

    # Warp crystal: the free dead end nearest to the start.
    if spec.warp:
        cands = free_dead_ends()
        if not cands:
            raise ValueError('no dead end for warp')
        wcell = min(cands, key=lambda d: dist.get(d, 999))
        L.set(wcell, 'W')
        reserved.add(wcell)

    # Spring: a dead end near the boss (or mid-floor on other floors).
    if spec.spring:
        cands = free_dead_ends()
        if not cands:
            raise ValueError('no dead end for spring')
        target = boss_cell or L.main_path[len(L.main_path) // 2]
        dd = L.bfs(target)
        hcell = min(cands, key=lambda d: dd.get(d, 999))
        L.set(hcell, 'H')
        reserved.add(hcell)

    # Vaults: a free dead end whose access corridor becomes a locked door.
    vaults = []
    for _ in range(spec.vaults):
        cands = [d for d in free_dead_ends() if node_zone(L, d) not in (0,) or zones == 1]
        cands = [d for d in cands if L.get(_corridor_neighbor(L, d)) == '.' and _corridor_neighbor(L, d) not in reserved
                 and L.degree(_corridor_neighbor(L, d)) == 2]
        if not cands:
            break
        d = rng.choice(cands)
        door = _corridor_neighbor(L, d)
        L.set(door, 'L')
        L.set(d, 'T')
        reserved |= {door, d}
        vaults.append((door, d))
        L.vault_cells.append(d)

    # Keys: one per locked door. Gate keys go to a dead end in an earlier zone (prefer the zone right before the
    # gate); vault keys anywhere reachable without that vault.
    def reachable_zones_before(k):
        return set(range(k + 1))

    keys_needed = [('gate', k) for k in lock_idx] + [('vault', v) for v in vaults]
    for kind, ref in keys_needed:
        if kind == 'gate':
            allowed = reachable_zones_before(ref)
            prefer = ref
        else:
            z = node_zone(L, ref[1])
            allowed = set(range(zones))
            prefer = z
        cands = [d for d in free_dead_ends() if node_zone(L, d) in allowed]
        if not cands:
            raise ValueError('no dead end for key')
        best = [d for d in cands if node_zone(L, d) == prefer] or cands
        kcell = max(best, key=lambda d: dist.get(d, 0) + rng.random() * 6)
        L.set(kcell, 'K')
        reserved.add(kcell)

    # Treasure: remaining dead ends, preferring far ones; some are guarded by an event battle.
    pool = free_dead_ends()
    rng.shuffle(pool)
    pool.sort(key=lambda d: -dist.get(d, 0))
    chests = []
    for d in pool[:spec.treasures]:
        L.set(d, 'T')
        reserved.add(d)
        chests.append(d)
    for d in chests[:spec.events]:
        e = _corridor_neighbor(L, d)
        if e and L.get(e) == '.' and L.degree(e) == 2 and e not in reserved:
            L.set(e, 'E')
            reserved.add(e)
            L.event_cells.append(e)
            L.guarded_cells.append(d)

    # Lore stones: remaining dead ends, else room cells.
    lore = []
    for d in free_dead_ends()[:spec.lore]:
        L.set(d, 'N')
        reserved.add(d)
        lore.append(d)
    if len(lore) < spec.lore:
        roomcells = [p for p in L.cells('.') if _in_room(L, p) and p not in reserved and L.degree(p) <= 3]
        rng.shuffle(roomcells)
        for p in roomcells[:spec.lore - len(lore)]:
            L.set(p, 'N')
            reserved.add(p)
            lore.append(p)

    # Traps: corridor cells (degree 2) off the start zone, a few on the main path from chapter 3 on.
    corr = [p for p in L.cells('.') if L.degree(p) == 2 and p not in reserved and node_zone(L, p) != 0]
    rng.shuffle(corr)
    for p in corr[:spec.traps]:
        L.set(p, 'X')
        reserved.add(p)

    # FOE patrols: loops when a zone has one, else long corridors.
    L.patrols = []
    foe_zones = list(range(1, zones)) or [0]
    rng.shuffle(foe_zones)
    for n in range(spec.foes):
        z = foe_zones[n % len(foe_zones)]
        route = _patrol_route(L, rng, z, reserved)
        if route:
            L.patrols.append(('foe', route))
    if spec.midboss:
        target = vaults[0][0] if vaults else None
        route = _guard_route(L, target) if target else None
        if not route:
            route = _patrol_route(L, rng, last, reserved)
        if route:
            L.patrols.append(('midboss', route))
    return L


def _foe_ok(L, p):
    return L.get(p) not in '#SLW<>BE'


def _patrol_route(L, rng, zone, reserved):
    """Waypoints of a loop (or out-and-back corridor) inside a zone, on FOE-passable cells."""
    cells = [p for p in L.cells() if node_zone(L, p) == zone and _foe_ok(L, p)]
    if len(cells) < 6:
        return None
    for _ in range(40):
        a = rng.choice(cells)
        b = max(cells, key=lambda c: abs(c[0] - a[0]) + abs(c[1] - a[1]) + rng.random() * 4)
        p = L.path(a, b, lambda q: _foe_ok(L, q))
        if len(p) >= 6:
            mid = p[len(p) // 2]
            return [p[0], mid, p[-1], mid]
    return None


def _guard_route(L, door):
    """Mid-boss walks back and forth in front of a vault door."""
    front = [q for q in L.neighbors(door) if _foe_ok(L, q) and L.get(q) != 'T']
    if not front:
        return None
    a = front[0]
    dist = L.bfs(a, lambda q: _foe_ok(L, q))
    far = [q for q, d in dist.items() if 3 <= d <= 5]
    if not far:
        return None
    b = sorted(far)[len(far) // 2]
    return [a, b]
