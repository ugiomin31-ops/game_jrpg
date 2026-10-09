"""Floor data for the campaign: 13 zones x 3 floors (spec.CHAPTERS, FLOORS_PER_ZONE).

Each zone has a layout style (world/maps.py), a party level range (spec 'levels') and a roster from spec.ZONE_POOLS.
Floor 2 of a zone holds the zone's mid-boss FOE (spec midboss + a partner), floor 3 its boss (spec boss). Postgame
zone 13 (R-1..R-3) holds the rematch superbosses as fixed event battles on floors 1-2 and leviathan_ex / abyss_lord_ex
on floor 3. Everything is deterministic: a floor's seed is derived from its index; the generator retries seeds
until the solver accepts the layout and every requested feature exists.
"""
import random

from . import maps, solver, texts

# ------------------------------------------------------------------ look
# Zones with an overlay (10 tidewater, 12 voidglow, 13 trialfire) take that overlay's fog and particle mood. The other
# zones keep the look (battle backdrop, fog, particles, overlay) of the base_dungeon.json floor named here.
MOOD = {
    'tidewater': dict(fog_color=[0.05, 0.2, 0.24, 1.0], ambient_particle_tint=[0.55, 1.0, 0.92, 1.0]),
    'voidglow': dict(fog_color=[0.12, 0.05, 0.2, 1.0], ambient_particle_tint=[0.78, 0.5, 1.0, 1.0]),
    'trialfire': dict(fog_color=[0.2, 0.13, 0.05, 1.0], ambient_particle_tint=[1.0, 0.85, 0.45, 1.0]),
}
# The hunter-world places have their own kits and Atmosphere presets: their fog and dust colours, and no template overlay.
TILESET_LOOK = {
    'subway': dict(fog_color=[0.11, 0.13, 0.15, 1.0], ambient_particle_tint=[0.84, 0.9, 1.0, 1.0]),
    'factory': dict(fog_color=[0.16, 0.11, 0.09, 1.0], ambient_particle_tint=[1.0, 0.81, 0.54, 1.0]),
    'cave': dict(fog_color=[0.08, 0.1, 0.2, 1.0], ambient_particle_tint=[0.62, 0.9, 1.0, 1.0]),
    'school': dict(fog_color=[0.1, 0.11, 0.2, 1.0], ambient_particle_tint=[1.0, 0.85, 0.6, 1.0]),
    'hospital': dict(fog_color=[0.58, 0.76, 0.74, 1.0], ambient_particle_tint=[0.85, 1.0, 0.95, 1.0]),
    'guild_street': dict(fog_color=[0.14, 0.16, 0.26, 1.0], ambient_particle_tint=[1.0, 0.7, 0.45, 1.0]),
}
TEMPLATE_OF_ZONE = {1: 'B1F', 2: 'B1F', 3: 'B7F', 4: 'B4F', 5: 'B4F', 6: 'B7F', 7: 'B10F', 8: 'B10F', 9: 'B4F',
                    10: 'B4F', 11: 'B10F', 12: 'B10F', 13: 'B7F'}
PLACEHOLDER_KEY = '카드키'

# ------------------------------------------------------------------ pacing
# Random battles a main-path party fights per floor. Zone 1 is short and gentle (the first boss within ~30-40 min).
# ~0.5 s per walked step and ~65 s per battle plus ~1.5 min per event/FOE fight put a well-explored floor at 20-25
# minutes; build_world.py --pace prints the estimate.
TARGET_BATTLES = {z: (6 if z == 1 else 10 if z <= 8 else 9) for z in range(1, 14)}
WALK_FACTOR = 1.25   # steps actually walked per exploration step (turning back, detours, revisits)
MIN_STEPS = 6

# Zone grid (lattice split) per style. The maze gates use the size-based grid.
ZONE_GRID = {'tunnels': (2, 2), 'aisles': (3, 2), 'cave': (3, 2), 'halls': (3, 1), 'streets': (3, 3)}

# Rare monsters mixed into encounter tables: one rare group among ~14 rows.
RARE_DILUTE = 4


def zone_grid(ch):
    if ch['style'] == 'maze':
        return (2, 2) if ch['size'] <= 21 else (3, 2) if ch['size'] <= 25 else (3, 3)
    return ZONE_GRID[ch['style']]


def zone_of_floor(n, spec):
    """Campaign floor number n (1-based) -> (zone number, k) with k = 1..FLOORS_PER_ZONE."""
    per = spec.FLOORS_PER_ZONE
    return (n - 1) // per + 1, (n - 1) % per + 1


def floor_label(zone, k):
    return 'R-%d' % k if zone == 13 else '%d-%d' % (zone, k)


def floor_text(n, ch, k, spec):
    """(area name, description, key name, lore texts) for floor n. Placeholders until texts.FLOORS has every floor."""
    total = spec.FLOORS_PER_ZONE * len(spec.CHAPTERS)
    if len(texts.FLOORS) == total:
        return texts.FLOORS[n - 1]
    return ('%s %d' % (ch['name'], k), '', PLACEHOLDER_KEY, ['[placeholder] lore 1', '[placeholder] lore 2'])


def floor_level(zone, k, spec):
    lo, hi = spec.CHAPTERS[zone - 1]['levels']
    return lo + (hi - lo) * (k - 0.5) / spec.FLOORS_PER_ZONE


def plan_for(n, spec):
    """Layout targets for floor n. Returns (zone, k, plan dict for maps.FloorSpec)."""
    zone, k = zone_of_floor(n, spec)
    ch = spec.CHAPTERS[zone - 1]
    size = ch['size']
    last = n == spec.FLOORS_PER_ZONE * len(spec.CHAPTERS)
    plan = dict(
        size=size, zones=zone_grid(ch), style=ch['style'],
        locked_gates=0 if (n == 1 or zone == 1) else (2 if k == 3 and zone >= 3 else 1),
        vaults=0 if n == 1 else 1,
        treasures=5 if zone == 1 else 5 + min(zone // 3, 3) + (1 if k == 2 else 0),
        lore=len(floor_text(n, ch, k, spec)[3]),
        traps=1 if zone == 1 else min(8, 1 + min(zone, 6) // 2 + k // 2),
        events=1 if zone == 1 or k in (1, 3) else 2,
        foes=0 if n == 1 or zone == 1 else (1 if k == 1 else 2),
        boss=k == 3 or zone == 13, spring=k in (2, 3), warp=(k in (1, 3) and n > 1),
        midboss=k == 2, rooms=3 + (size - 21) // 3, loop_chance=0.16 + 0.02 * min(zone, 4),
        down_stairs=not last,
    )
    if n == 1:
        plan.update(vaults=0, traps=0, foes=0)
    return zone, k, plan


def _make(n, plan, base_seed):
    for attempt in range(400):
        seed = base_seed * 1000 + attempt
        spec = maps.FloorSpec(seed=seed, **plan)
        try:
            L = maps.build(spec)
        except (ValueError, IndexError):
            continue
        rows = L.rows()
        res = solver.analyse(rows)
        if not res['ok']:
            continue
        flat = ''.join(rows)
        if flat.count('T') < plan['treasures'] + plan['vaults'] or flat.count('N') != plan['lore']:
            continue
        if flat.count('L') != plan['locked_gates'] + plan['vaults'] or flat.count('K') != flat.count('L'):
            continue
        if plan['warp'] and 'W' not in flat:
            continue
        if plan['spring'] and 'H' not in flat:
            continue
        if flat.count('E') < plan['events']:
            continue
        foes = [r for kind, r in L.patrols if kind == 'foe']
        mids = [r for kind, r in L.patrols if kind == 'midboss']
        if len(foes) < plan['foes'] or (plan['midboss'] and not mids):
            continue
        if not all(solver.check_patrol(rows, r) for _, r in L.patrols):
            continue
        # FOEs never stand within 3 steps of the start cell (no instant fights on arrival).
        start = L.start
        if any(abs(r[0][0] - start[0]) + abs(r[0][1] - start[1]) <= 3 for _, r in L.patrols):
            continue
        return L, seed, res
    raise RuntimeError('floor %d: no valid layout' % n)


# ------------------------------------------------------------------ loot tables (keyed by zone 1..13)
# The seven original chapter tables are spread over the zones by level: chapter c covers zones CH_OF_ZONE == c.
CH_OF_ZONE = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 5, 10: 5, 11: 6, 12: 6, 13: 7}
_CH_POTION = {1: 'healing_potion', 2: 'hi_potion', 3: 'mega_potion', 4: 'mega_potion', 5: 'x_potion', 6: 'x_potion', 7: 'x_potion'}
_CH_ETHER = {1: 'ether', 2: 'ether', 3: 'hi_ether', 4: 'hi_ether', 5: 'max_ether', 6: 'max_ether', 7: 'max_ether'}
_CH_REVIVE = {1: 'phoenix_feather', 2: 'phoenix_feather', 3: 'phoenix_feather', 4: 'phoenix_feather', 5: 'phoenix_plume',
              6: 'phoenix_plume', 7: 'phoenix_plume'}
_CH_CURE = {1: 'remedy', 2: 'remedy', 3: 'remedy', 4: 'remedy', 5: 'panacea', 6: 'panacea', 7: 'panacea'}
_CH_BOMBS = {1: ['bomb'], 2: ['bomb', 'fire_bomb'], 3: ['big_bomb', 'ice_bomb'], 4: ['big_bomb', 'holy_water'],
             5: ['thunder_bomb', 'fire_bomb'], 6: ['holy_water', 'thunder_bomb'], 7: ['holy_water', 'ice_bomb']}
_CH_MATERIALS = {1: ['forest_fiber', 'slime_gel', 'bat_wing'], 2: ['frost_crystal', 'coral_shard', 'frost_fur', 'jelly_core'],
                 3: ['drake_scale', 'magma_core', 'golem_sandstone'], 4: ['old_bone', 'ghost_essence', 'cursed_straw'],
                 5: ['pearl', 'scale_blue', 'temple_stone', 'siren_feather'],
                 6: ['void_shard', 'shadow_pelt', 'gargoyle_horn', 'fallen_feather'], 7: ['trial_emblem', 'void_shard']}
_CH_RARE_MATERIAL = {1: 'verdant_crystal', 2: 'frost_crystal', 3: 'ember_crystal', 4: 'abyss_crystal', 5: 'leviathan_fin',
                     6: 'abyss_crystal', 7: 'lord_crown'}
_CH_STONE = {1: 'enhance_stone', 2: 'enhance_stone', 3: 'enhance_stone', 4: 'enhance_stone_hi', 5: 'enhance_stone_hi',
             6: 'enhance_stone_abyss', 7: 'enhance_stone_abyss'}
_CH_ACCESSORIES = {
    1: ['acc_iron_bangle', 'acc_mind_ring', 'acc_lucky_charm'],
    2: ['acc_swift_anklet', 'acc_freeze_ward', 'acc_sleep_ward', 'acc_life_pendant'],
    3: ['acc_burn_ward', 'acc_spirit_pendant', 'acc_thunder_amulet', 'acc_earth_amulet'],
    4: ['acc_holy_amulet', 'acc_dark_amulet', 'acc_silence_ward', 'acc_curse_ward', 'acc_paralyze_ward'],
    5: ['acc_mana_spring', 'acc_regen_ring', 'acc_counter_charm', 'acc_tp_crest'],
    6: ['acc_berserk_ring', 'acc_sniper_scope', 'acc_gold_charm', 'acc_exp_charm'],
    7: ['acc_regen_ring', 'acc_mana_spring', 'acc_tp_crest', 'acc_exp_charm'],
}


def _by_zone(table):
    return {z: table[CH_OF_ZONE[z]] for z in range(1, 14)}


POTION, ETHER, REVIVE, CURE = _by_zone(_CH_POTION), _by_zone(_CH_ETHER), _by_zone(_CH_REVIVE), _by_zone(_CH_CURE)
BOMBS, MATERIALS = _by_zone(_CH_BOMBS), _by_zone(_CH_MATERIALS)
RARE_MATERIAL, STONE, ACCESSORIES = _by_zone(_CH_RARE_MATERIAL), _by_zone(_CH_STONE), _by_zone(_CH_ACCESSORIES)
SEEDS = ['seed_power', 'seed_magic', 'seed_guard', 'seed_mind', 'seed_swift', 'seed_life']
LINES = ['sword', 'staff', 'bow', 'mace', 'armor', 'robe', 'garb']


def chest_gold(level):
    return int(round((60 + 22 * level + 0.9 * level * level) / 10.0)) * 10


def _loot(spec, n, zone, k, rng, cells, vault_cells, guarded_cells, level):
    """Contents per treasure cell. Vaults hold the next gear tier or a seed, guarded chests an accessory or gear,
    the rest consumables, gold, zone materials and enhancement stones. Gear tier = spec.TIER_OF_ZONE[zone]."""
    out = {}
    lines = list(LINES)
    rng.shuffle(lines)
    accs = list(ACCESSORIES[zone])
    rng.shuffle(accs)
    tier = spec.TIER_OF_ZONE[zone]
    regular = []
    for p in cells:
        if p in vault_cells:
            if zone >= 2 and (n % 3 == 0 or len([v for v in vault_cells if v in out]) % 2 == 1):
                out[p] = dict(gold=0, items={SEEDS[(n * 7 + len(out)) % 6]: 1, STONE[zone]: 1}, equipment={})
            else:
                line = lines.pop() if lines else 'sword'
                out[p] = dict(gold=0, items={}, equipment={spec.GEAR_LINES[line][min(7, tier)]: 1})  # next tier
        elif p in guarded_cells:
            if accs:
                out[p] = dict(gold=0, items={}, equipment={accs.pop(): 1})
            else:
                line = lines.pop() if lines else 'robe'
                out[p] = dict(gold=0, items={}, equipment={spec.GEAR_LINES[line][tier - 1]: 1})
        else:
            regular.append(p)
    table = [
        lambda: dict(gold=chest_gold(level), items={}, equipment={}),
        lambda: dict(gold=0, items={POTION[zone]: 2 + (k >= 3)}, equipment={}),
        lambda: dict(gold=0, items={ETHER[zone]: 1 + (k == 3)}, equipment={}),
        lambda: dict(gold=0, items={MATERIALS[zone][n % len(MATERIALS[zone])]: 2}, equipment={}),
        lambda: dict(gold=0, items={STONE[zone]: 1 + (k == 3)}, equipment={}),
        lambda: dict(gold=0, items={REVIVE[zone]: 1}, equipment={}),
        lambda: dict(gold=0, items={BOMBS[zone][n % len(BOMBS[zone])]: 2}, equipment={}),
        lambda: dict(gold=chest_gold(level) * 2, items={}, equipment={}),
        lambda: dict(gold=0, items={CURE[zone]: 2}, equipment={}),
        lambda: dict(gold=0, items={}, equipment={spec.GEAR_LINES[lines[0] if lines else 'garb'][tier - 1]: 1}),
        lambda: dict(gold=0, items={RARE_MATERIAL[zone]: 1}, equipment={}) if k == 3
        else dict(gold=0, items={POTION[zone]: 3}, equipment={}),
    ]
    start = n % len(table)
    for i, p in enumerate(regular):
        out[p] = table[(start + i) % len(table)]()
    if n == 1:  # first floor: the four original welcome chests
        firsts = [dict(gold=50, items={}, equipment={}), dict(gold=0, items={'healing_potion': 2}, equipment={}),
                  dict(gold=0, items={}, equipment={'acc_lucky_charm': 1}), dict(gold=0, items={'remedy': 1}, equipment={})]
        for p, contents in zip(regular, firsts):
            out[p] = contents
    return out


# ------------------------------------------------------------------ rosters / encounter groups
def roster(by_id, spec, zone):
    """Normal (rank 0) monsters of the zone's pool, rows from the enemy table."""
    pool = [by_id[x] for x in spec.ZONE_POOLS[zone]['normal']]
    for e in pool:
        assert e['rank'] == 0, (zone, e['id'])
    return pool


def encounter_groups(pool, zone, rng):
    size_lo, size_hi = (2, 3) if zone == 1 else (2, 4) if zone <= 2 else (3, 4) if zone <= 4 else (3, 5)
    count = 7 if zone == 1 else 8 if zone <= 2 else 9
    groups, seen = [], set()
    weights = [1.0 + 0.15 * e['level'] for e in pool]
    tries = 0
    while len(groups) < count and tries < 500:
        tries += 1
        size = rng.randint(size_lo, size_hi)
        g = []
        for _ in range(size):
            e = rng.choices(pool, weights)[0]
            if e.get('archetype') == 'body_only' and e.get('scale_mult', 1) > 1.2 and any(x == e['id'] for x in g):
                continue
            g.append(e['id'])
        if len(g) < size_lo:
            continue
        if max(g.count(x) for x in g) > 3:
            continue
        key = tuple(sorted(g))
        if key in seen:
            continue
        seen.add(key)
        groups.append(sorted(g, key=lambda x: [p['id'] for p in pool].index(x)))
    return groups


def midboss_group(by_id, spec, zone):
    """Zone mid-boss FOE: the zone's elite midboss plus the normal monster closest to its level."""
    elite = spec.CHAPTERS[zone - 1]['midboss']
    partner = min(spec.ZONE_POOLS[zone]['normal'], key=lambda x: abs(by_id[x]['level'] - by_id[elite]['level']))
    return [elite, partner]


def foe_groups(by_id, spec, zone):
    """Patrolling FOE groups of a zone: one zone elite with two normals (index j cycles the pools)."""
    elites = spec.ZONE_POOLS[zone]['elite']
    normals = sorted(spec.ZONE_POOLS[zone]['normal'], key=lambda x: by_id[x]['level'])
    out = []
    for j in range(3):
        out.append([elites[j % len(elites)], normals[(2 * j) % len(normals)], normals[(2 * j + 3) % len(normals)]])
    return out


def build_floors(spec, enemies, originals):
    """Returns (floor rows in campaign order, layout metadata per floor)."""
    by_label = {f['floor_label']: f for f in originals}
    by_id = {e['id']: e for e in enemies}
    total = spec.FLOORS_PER_ZONE * len(spec.CHAPTERS)
    floors, meta = [], []
    for n in range(1, total + 1):
        zone, k, plan = plan_for(n, spec)
        ch = spec.CHAPTERS[zone - 1]
        L, seed, res = _make(n, plan, n)
        rows = L.rows()
        rng = random.Random(9000 + n)
        tmpl = by_label[TEMPLATE_OF_ZONE[zone]]
        area, desc, key_name, lore = floor_text(n, ch, k, spec)
        level = floor_level(zone, k, spec)
        cells = lambda ch_: [(x, y) for y, r in enumerate(rows) for x, cc in enumerate(r) if cc == ch_]
        # ---- treasures
        tcells = cells('T')
        loot = _loot(spec, n, zone, k, rng, tcells, set(L.vault_cells), set(L.guarded_cells), level)
        treasures = [dict(cell=[x, y], contents=loot[(x, y)]) for x, y in tcells]
        # ---- encounters
        pool = roster(by_id, spec, zone)
        groups = encounter_groups(pool, zone, rng)
        for rid, zones in spec.RARE_BY_ZONE.items():
            if zone in zones:
                partner = min(pool, key=lambda e: e['level'])['id']
                groups += [list(g) for g in groups[:RARE_DILUTE]]  # dilute: the rare row is ~1 in 13
                groups.append([rid, partner] if rid != 'golden_mimic' else [rid])
        # ---- events (guards in front of chests)
        events = []
        for p in cells('E'):
            size = 4 if zone <= 3 else 5
            g = sorted(rng.sample(pool, min(len(pool), 2)), key=lambda e: e['level'])
            grp = [g[-1]['id']] * 2 + [x['id'] for x in rng.choices(pool, k=size - 2)]
            events.append(dict(cell=list(p), group=grp))
        last_zone = zone == len(spec.CHAPTERS)
        boss_group = [ch['boss']] if k == 3 else []
        # ---- FOEs
        foes = []
        patrols = [r for kind, r in L.patrols if kind == 'foe']
        fgroups = foe_groups(by_id, spec, zone)
        for j, route in enumerate(patrols[:plan['foes']]):
            foes.append(dict(id='foe_b%d_%d' % (n, j + 1), group=list(fgroups[(j + k - 1) % len(fgroups)]), spawn=list(route[0]),
                             patrol=[list(p) for p in route], chase_range=0 if zone == 1 and k <= 2 else min(4, 1 + zone // 3 + j),
                             power=1.3))
        mid = [r for kind, r in L.patrols if kind == 'midboss']
        if plan['midboss'] and mid:
            foes.append(dict(id='midboss_b%d' % n, group=midboss_group(by_id, spec, zone), spawn=list(mid[0][0]),
                             patrol=[list(p) for p in mid[0]], chase_range=0, power=1.45))
        # ---- lore stones (texts in reading order: nearest the start first)
        dist = L.bfs(L.start)
        ncells = sorted(cells('N'), key=lambda p: dist.get(p, 999))
        lore_stones = [dict(cell=list(p), text=t) for p, t in zip(ncells, lore)]
        # ---- pacing
        steps = int(solver.exploration_steps(rows, coverage=0.85) * WALK_FACTOR)
        battles = TARGET_BATTLES[zone]
        per = max(MIN_STEPS + 6, steps / battles)
        rate = round(1.0 / max(4.0, per - MIN_STEPS), 3)
        look = MOOD.get(ch['overlay']) or TILESET_LOOK.get(ch['tileset'], {})
        row = {
            'id': '%s_%d' % (ch['id'], k),
            'floor_label': floor_label(zone, k),
            'area_name': area,
            'area_description': desc,
            'rows': rows,
            'tileset': ch['tileset'],
            'battle_backdrop': tmpl.get('battle_backdrop', ''),
            'encounter_groups': groups,
            'showcase_group': list(groups[0]),
            'boss_group': boss_group,
            'fog_color': list(look.get('fog_color', tmpl['fog_color'])),
            'ambient_particle_tint': list(look.get('ambient_particle_tint', tmpl['ambient_particle_tint'])),
            'overlay': ch['overlay'] or ('' if ch['tileset'] in TILESET_LOOK else tmpl['overlay']),
            'encounter_rate': rate,
            'min_encounter_steps': MIN_STEPS,
            'max_encounter_steps': int(round(per * 2.2)),
            'treasures': treasures,
            'events': events,
            'foes': foes,
            'key_name': key_name,
            'lore_text': lore[0] if lore else '',
            'lore_stones': lore_stones,
            'boss_pre_text': '',
            'boss_post_text': '',
        }
        if k == 3:
            row['boss_pre_text'], row['boss_post_text'] = texts.BOSS_TEXT.get(ch['boss'], ('', ''))
        if n == spec.MAIN_ZONES * spec.FLOORS_PER_ZONE:  # 12-3: the last main floor (index 35 of 39)
            row['ending'] = True
        if last_zone and k < 3:
            # Postgame: the boss cell is a fixed superboss battle (event); a second superboss guards the corridor.
            boss_id, guard_id = {1: ('forest_guardian_ex', 'frost_kraken_ex'), 2: ('flame_sphinx_ex', 'boss_ex')}[k]
            _superboss_floor(L, row, rows, cells, boss_id, guard_id, boss_row=False)
        elif last_zone:
            # R-3: the abyss lord is the boss (kept as the B cell); leviathan_ex guards the corridor before it.
            _superboss_floor(L, row, rows, cells, ch['boss'], 'leviathan_ex', boss_row=True)
        row['_file'] = 'b%02d_%s_%d' % (n, ch['id'], k)
        for g in groups + [e['group'] for e in row['events']] + [f['group'] for f in foes] + [boss_group]:
            for eid in g:
                assert eid in by_id, (n, eid)
        floors.append(row)
        meta.append(dict(n=n, zone=zone, k=k, seed=seed, states=res['states'], walkable=res['walkable'], steps=steps,
                         rate=rate, battles=battles, layout=L))
    return floors, meta


def _superboss_floor(L, row, rows, cells, boss_id, guard_id, boss_row):
    """Postgame floors: the boss cell fights boss_id (a fixed event when boss_row is False, the zone boss otherwise);
    guard_id waits on the corridor leading to the boss cell. Events stay sorted by cell."""
    bx, by = cells('B')[0]
    rows2 = [list(r) for r in rows]
    path = L.path(L.start, (bx, by))
    guard = None
    for p in reversed(path[:-1]):
        if rows[p[1]][p[0]] == '.' and L.degree(p) == 2:
            guard = p
            break
    if not boss_row:
        rows2[by][bx] = 'E'
        row['events'].append(dict(cell=[bx, by], group=[boss_id]))
    rows2[guard[1]][guard[0]] = 'E'
    row['events'].append(dict(cell=list(guard), group=[guard_id]))
    row['rows'] = [''.join(r) for r in rows2]
    row['events'].sort(key=lambda e: (e['cell'][1], e['cell'][0]))
