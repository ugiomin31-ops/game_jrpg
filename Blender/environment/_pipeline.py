"""Shared environment production entry point and metre/grid finalisation."""
import _kit_common_b as K

LAYOUT = [
    "W W boss_gate W W".split(),
    "W lore_stone . torch W".split(),
    "W . chest warp W".split(),
    "W trap spring stairs_down W".split(),
    "W W door_locked W W".split(),
]
EXTRAS = [(f"decor_{i}", (1.1 + (i % 3) * 0.8, 1.25 + (i // 3) * 1.0), i * 30) for i in range(1, 7)]
EXTRAS += [("overlay_1", (1, 4), 0), ("overlay_2", (3, 4), 0), ("foe_marker", (2, 3), 0)]
PIECE_NAMES = (
    "floor_a", "floor_b", "floor_c", "wall_a", "wall_b", "wall_c", "door", "door_locked",
    "stairs_down", "stairs_up", "chest", "lore_stone", "trap", "spring", "warp", "torch",
    "decor_1", "decor_2", "decor_3", "decor_4", "decor_5", "decor_6", "overlay_1", "overlay_2",
    "boss_gate", "foe_marker",
)


def grid_piece(name, builder):
    """Bake paving inlays flush at zero and fit sculpted wall relief to one cell.

    Floors intentionally contain their moss, roots, bone and runes as flush
    surface relief; raised foliage belongs to the separate decoration pieces.
    Wall blocks keep all detail, scaled together rather than clipped at seams.
    """
    def build():
        objs = builder()
        if name.startswith("floor_"):
            for o in objs:
                if o.type != "MESH":
                    continue
                for v in o.data.vertices:
                    v.co.x = max(-2.0, min(2.0, v.co.x))
                    v.co.y = max(-2.0, min(2.0, v.co.y))
                    v.co.z = min(0.0, v.co.z)
                o.data.update()
        elif name.startswith("wall_"):
            meshes = [o for o in objs if o.type == "MESH"]
            verts = [v for o in meshes for v in o.data.vertices]
            lo = [min(v.co[a] for v in verts) for a in range(3)]
            hi = [max(v.co[a] for v in verts) for a in range(3)]
            for v in verts:
                for a in range(3):
                    target_lo, size = (-2.0, 4.0) if a < 2 else (0.0, 4.5)
                    v.co[a] = target_lo + (v.co[a] - lo[a]) * size / (hi[a] - lo[a])
            for o in meshes:
                o.data.update()
        return objs
    return build


def run(ts, pieces, layout=None, extras=None, world="#26343f"):
    # Failing at generation time prevents publishing a partial kit under a full-kit name.
    names = [n for n, _ in pieces]
    if len(names) != len(set(names)) or set(names) != set(PIECE_NAMES):
        raise RuntimeError(f"Incomplete or duplicate environment pieces for {ts}: {names}")
    return K.run_kit(ts, [(name, grid_piece(name, fn)) for name, fn in pieces],
                     layout or LAYOUT, EXTRAS if extras is None else extras,
                     walls=("wall_a", "wall_b", "wall_c"), floors=("floor_a", "floor_b", "floor_c"), world=world)
