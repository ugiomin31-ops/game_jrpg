"""Floor data for the 35-floor campaign: layout plans per chapter/floor, roster-driven encounter groups, FOE
patrols, treasure tables, lore stones and the pacing model (encounter rate tuned for ~20-25 real minutes).

Everything is deterministic: a floor's seed is derived from its index; the generator retries seeds until the
solver accepts the layout and every requested feature (vault, mid-boss route, FOE routes, lore cells) exists.
"""
import random

from . import maps, solver, texts

# ------------------------------------------------------------------ chapter look
# Chapters 1-4 keep their biome's look (copied from the original floors); 5-7 get a region mood via overlay
# (Atmosphere.ForFloor: tidewater / voidglow / trialfire) plus their own fog colour and particle tint.
LOOK = {
    5: dict(fog_color=[0.05, 0.2, 0.24, 1.0], ambient_particle_tint=[0.55, 1.0, 0.92, 1.0], overlay='tidewater'),
    6: dict(fog_color=[0.12, 0.05, 0.2, 1.0], ambient_particle_tint=[0.78, 0.5, 1.0, 1.0], overlay='voidglow'),
    7: dict(fog_color=[0.2, 0.13, 0.05, 1.0], ambient_particle_tint=[1.0, 0.85, 0.45, 1.0], overlay='trialfire'),
}
SIZES = {1: 21, 2: 23, 3: 23, 4: 25, 5: 27, 6: 27, 7: 27}
SUPERBOSS_FLOOR = {31: 'forest_guardian_ex', 32: 'frost_kraken_ex', 33: 'flame_sphinx_ex', 34: 'boss_ex', 35: 'leviathan_ex'}

# Random battles a main-path party fights per floor (pacing): with ~0.5 s per step and ~65 s per battle plus
# fixed fights, a fully explored floor lands at 20-25 minutes. Encounter rate is derived from these.
TARGET_BATTLES = {1: 11, 2: 12, 3: 12, 4: 13, 5: 13, 6: 14, 7: 12}
MIN_STEPS = 6

# Mid-boss (floor 3) and FOE groups per chapter: (group, power).
MIDBOSS = {
    1: (['elite_rhino_beetle', 'rhino_beetle'], 1.5),
    2: (['elite_yeti', 'yeti'], 1.45),
    3: (['elite_sand_golem', 'sand_golem'], 1.45),
    4: (['elite_dark_knight', 'dark_knight'], 1.4),
    5: (['turtle_titan', 'giant_clam'], 1.3),
    6: (['crystal_horror', 'gargoyle'], 1.3),
    7: (['void_reaper', 'elder_lich'], 1.35),
}
FOES = {
    1: [(['elite_mushroom', 'mushroom'], 1.25), (['elite_bat', 'bat', 'bat'], 1.3), (['elite_mushroom', 'poison_mushroom'], 1.3)],
    2: [(['elite_ice_wolf', 'ice_wolf'], 1.3), (['elite_coral_crab', 'jellyfish', 'jellyfish'], 1.3), (['elite_ice_wolf', 'snow_rabbit', 'ice_wolf'], 1.35)],
    3: [(['elite_hellhound', 'hellhound'], 1.3), (['elite_fire_drake'], 1.45), (['elite_hellhound', 'ember_bee', 'hellhound'], 1.35)],
    4: [(['elite_skeleton', 'skeleton', 'skeleton_mage'], 1.3), (['elite_scarecrow', 'wisp'], 1.3), (['elite_mimic'], 1.35)],
    5: [(['drowned_knight', 'merfolk_guard'], 1.2), (['naga_priestess', 'siren'], 1.2), (['drowned_knight', 'sea_serpent'], 1.25)],
    6: [(['fallen_angel', 'shadow_beast'], 1.2), (['void_reaper', 'void_eye'], 1.2), (['fallen_angel', 'nightmare'], 1.25)],
    7: [(['fallen_angel', 'chaos_yeti'], 1.3), (['crystal_horror', 'inferno_phoenix'], 1.3), (['void_reaper', 'elder_lich'], 1.3)],
}
# Rare monsters mixed into encounter tables (one rare group among ~14 rows): floor numbers (1-based).
RARE = {
    'gold_slime': [3, 4, 5, 7, 9, 12],
    'metal_slime': [9, 10, 13, 14, 15, 17, 19, 20],
    'golden_mimic': [23, 24, 25, 27, 29, 33],
}


def floor_plan(n):
    """Layout targets for floor n (1-based)."""
    c = (n - 1) // 5 + 1
    k = (n - 1) % 5 + 1
    size = SIZES[c]
    zones = (2, 2) if size <= 21 else (3, 2) if size <= 23 else (3, 3) if k in (2, 4, 5) else (3, 2)
    if size == 25:
        zones = (3, 2) if k in (1, 3) else (3, 3)
    plan = dict(
        size=size, zones=zones,
        locked_gates=0 if n == 1 else (2 if k in (4, 5) and c >= 3 else 1),
        vaults=1 if n == 1 else (2 if c >= 4 and k in (2, 4) else 1),
        treasures=5 + min(c, 4) + (1 if k == 4 else 0),
        lore=len(texts.FLOORS[n - 1][3]),
        traps=min(8, 1 + c + (k // 2)),
        events=1 if k in (1, 3) or c == 1 else 2,
        foes=0 if n <= 1 else (1 if c == 1 or k == 1 else 2),
        boss=k == 5 or c == 7, spring=k in (3, 5) or c == 7, warp=(k in (1, 3, 5) and n > 1),
        midboss=k == 3, rooms=3 + (size - 21) // 3, loop_chance=0.16 + 0.02 * min(c, 4),
        down_stairs=n < 35,
    )
    if n == 1:
        plan.update(traps=1, events=1, foes=0)
    return c, k, plan


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
        # FOEs never stand on the start cell's neighbours at spawn (no instant fights on arrival).
        start = L.start
        if any(abs(r[0][0] - start[0]) + abs(r[0][1] - start[1]) <= 3 for _, r in L.patrols):
            continue
        return L, seed, res
    raise RuntimeError('floor %d: no valid layout' % n)


# ------------------------------------------------------------------ loot tables
POTION = {1: 'healing_potion', 2: 'hi_potion', 3: 'mega_potion', 4: 'mega_potion', 5: 'x_potion', 6: 'x_potion', 7: 'x_potion'}
ETHER = {1: 'ether', 2: 'ether', 3: 'hi_ether', 4: 'hi_ether', 5: 'max_ether', 6: 'max_ether', 7: 'max_ether'}
REVIVE = {1: 'phoenix_feather', 2: 'phoenix_feather', 3: 'phoenix_feather', 4: 'phoenix_feather', 5: 'phoenix_plume', 6: 'phoenix_plume', 7: 'phoenix_plume'}
CURE = {1: 'remedy', 2: 'remedy', 3: 'remedy', 4: 'remedy', 5: 'panacea', 6: 'panacea', 7: 'panacea'}
BOMBS = {1: ['bomb'], 2: ['bomb', 'fire_bomb'], 3: ['big_bomb', 'ice_bomb'], 4: ['big_bomb', 'holy_water'],
         5: ['thunder_bomb', 'fire_bomb'], 6: ['holy_water', 'thunder_bomb'], 7: ['holy_water', 'ice_bomb']}
MATERIALS = {1: ['forest_fiber', 'slime_gel', 'bat_wing'], 2: ['frost_crystal', 'coral_shard', 'frost_fur', 'jelly_core'],
             3: ['drake_scale', 'magma_core', 'golem_sandstone'], 4: ['old_bone', 'ghost_essence', 'cursed_straw'],
             5: ['pearl', 'scale_blue', 'temple_stone', 'siren_feather'], 6: ['void_shard', 'shadow_pelt', 'gargoyle_horn', 'fallen_feather'],
             7: ['trial_emblem', 'void_shard']}
RARE_MATERIAL = {1: 'verdant_crystal', 2: 'frost_crystal', 3: 'ember_crystal', 4: 'abyss_crystal', 5: 'leviathan_fin', 6: 'abyss_crystal', 7: 'lord_crown'}
STONE = {1: 'enhance_stone', 2: 'enhance_stone', 3: 'enhance_stone', 4: 'enhance_stone_hi', 5: 'enhance_stone_hi', 6: 'enhance_stone_abyss', 7: 'enhance_stone_abyss'}
SEEDS = ['seed_power', 'seed_magic', 'seed_guard', 'seed_mind', 'seed_swift', 'seed_life']
ACCESSORIES = {
    1: ['acc_iron_bangle', 'acc_mind_ring', 'acc_lucky_charm'],
    2: ['acc_swift_anklet', 'acc_freeze_ward', 'acc_sleep_ward', 'acc_life_pendant'],
    3: ['acc_burn_ward', 'acc_spirit_pendant', 'acc_thunder_amulet', 'acc_earth_amulet'],
    4: ['acc_holy_amulet', 'acc_dark_amulet', 'acc_silence_ward', 'acc_curse_ward', 'acc_paralyze_ward'],
    5: ['acc_mana_spring', 'acc_regen_ring', 'acc_counter_charm', 'acc_tp_crest'],
    6: ['acc_berserk_ring', 'acc_sniper_scope', 'acc_gold_charm', 'acc_exp_charm'],
    7: ['acc_regen_ring', 'acc_mana_spring', 'acc_tp_crest', 'acc_exp_charm'],
}
LINES = ['sword', 'staff', 'bow', 'mace', 'armor', 'robe', 'garb']


def chest_gold(c, k):
    level = (c - 1) * 10 + 2 * k
    return int(round((60 + 22 * level + 0.9 * level * level) / 10.0)) * 10


def _loot(spec, n, c, k, rng, cells, vault_cells, guarded_cells):
    """Contents per treasure cell. Vaults hold the next gear tier or a seed, guarded chests an accessory or gear,
    the rest consumables, gold, chapter materials and enhancement stones."""
    out = {}
    lines = list(LINES)
    rng.shuffle(lines)
    accs = list(ACCESSORIES[c])
    rng.shuffle(accs)
    regular = []
    for p in cells:
        if p in vault_cells:
            if c >= 2 and (n % 3 == 0 or len([v for v in vault_cells if v in out]) % 2 == 1):
                out[p] = dict(gold=0, items={SEEDS[(n * 7 + len(out)) % 6]: 1, STONE[c]: 1}, equipment={})
            else:
                line = lines.pop() if lines else 'sword'
                tier = min(7, c + (1 if k >= 3 else 0))  # GEAR_LINES index: chapter c's own tier is index c-1
                out[p] = dict(gold=0, items={}, equipment={spec.GEAR_LINES[line][min(6, tier)]: 1})
        elif p in guarded_cells:
            if accs:
                out[p] = dict(gold=0, items={}, equipment={accs.pop(): 1})
            else:
                line = lines.pop() if lines else 'robe'
                out[p] = dict(gold=0, items={}, equipment={spec.GEAR_LINES[line][min(6, c - 1 + (k >= 4))]: 1})
        else:
            regular.append(p)
    table = [
        lambda: dict(gold=chest_gold(c, k), items={}, equipment={}),
        lambda: dict(gold=0, items={POTION[c]: 2 + (k >= 3)}, equipment={}),
        lambda: dict(gold=0, items={ETHER[c]: 1 + (k >= 4)}, equipment={}),
        lambda: dict(gold=0, items={MATERIALS[c][n % len(MATERIALS[c])]: 2}, equipment={}),
        lambda: dict(gold=0, items={STONE[c]: 1 + (k == 5)}, equipment={}),
        lambda: dict(gold=0, items={REVIVE[c]: 1}, equipment={}),
        lambda: dict(gold=0, items={BOMBS[c][n % len(BOMBS[c])]: 2}, equipment={}),
        lambda: dict(gold=chest_gold(c, k) * 2, items={}, equipment={}),
        lambda: dict(gold=0, items={CURE[c]: 2}, equipment={}),
        lambda: dict(gold=0, items={}, equipment={spec.GEAR_LINES[lines[0] if lines else 'garb'][c - 1]: 1}),
        lambda: dict(gold=0, items={RARE_MATERIAL[c]: 1}, equipment={}) if k >= 4 else dict(gold=0, items={POTION[c]: 3}, equipment={}),
    ]
    start = n % len(table)
    for i, p in enumerate(regular):
        out[p] = table[(start + i) % len(table)]()
    if n == 1:  # first floor: the original welcome chests
        firsts = [dict(gold=50, items={}, equipment={}), dict(gold=0, items={'healing_potion': 2}, equipment={}),
                  dict(gold=0, items={}, equipment={'acc_lucky_charm': 1}), dict(gold=0, items={'remedy': 1}, equipment={})]
        for p, contents in zip(regular, firsts):
            out[p] = contents
    return out


# ------------------------------------------------------------------ rosters / encounter groups
def floor_level(c, k, levels):
    lo, hi = levels
    return lo + (hi - lo) * (k - 0.5) / 5.0


def roster(enemies, c, k, levels):
    """Normal (rank 0) monsters for a floor: the chapter's own monsters around the floor's level."""
    lvl = floor_level(c, k, levels)
    pool = []
    for e in enemies:
        if e['rank'] != 0 or e['id'] in RARE or e.get('_chapter') is None:
            continue
        ch = e['_chapter']
        if c == 7:
            ok = ch == 7 or (ch == 6 and e['level'] >= 58)
        else:
            ok = ch == c
        if not ok:
            continue
        if c < 7 and not (lvl - 7 <= e['level'] <= lvl + 2.5):
            continue
        pool.append(e)
    if len(pool) < 3:  # chapter edges: widen the window
        pool = [e for e in enemies if e['rank'] == 0 and e.get('_chapter') == c and e['id'] not in RARE]
        pool.sort(key=lambda e: abs(e['level'] - lvl))
        pool = pool[:5]
    return pool


def encounter_groups(pool, c, k, n, rng):
    size_lo, size_hi = (2, 3) if c == 1 and k <= 2 else (2, 4) if c <= 2 else (3, 4) if c <= 4 else (3, 5)
    groups = []
    seen = set()
    weights = [1.0 + 0.15 * e['level'] for e in pool]
    tries = 0
    count = 8 if c <= 2 else 9
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
        # At most two copies of one monster, and big groups only of the chapter's lighter monsters.
        if max(g.count(x) for x in g) > 3:
            continue
        key = tuple(sorted(g))
        if key in seen:
            continue
        seen.add(key)
        groups.append(sorted(g, key=lambda x: [p['id'] for p in pool].index(x)))
    return groups


def build_floors(spec, enemies, originals):
    """Returns (floor rows in campaign order, layout metadata per floor)."""
    by_label = {f['floor_label']: f for f in originals}
    chapter_template = {1: by_label['B1F'], 2: by_label['B4F'], 3: by_label['B7F'], 4: by_label['B10F']}
    by_id = {e['id']: e for e in enemies}
    floors, meta = [], []
    for n in range(1, 36):
        c, k, plan = floor_plan(n)
        ch = spec.CHAPTERS[c - 1]
        L, seed, res = _make(n, plan, n)
        rows = L.rows()
        rng = random.Random(9000 + n)
        tmpl = chapter_template[min(c, 4) if c <= 4 else {5: 2, 6: 4, 7: 3}[c]]
        area, desc, key_name, lore = texts.FLOORS[n - 1]
        cells = lambda ch_: [(x, y) for y, r in enumerate(rows) for x, cc in enumerate(r) if cc == ch_]
        # ---- treasures
        tcells = cells('T')
        loot = _loot(spec, n, c, k, rng, tcells, set(L.vault_cells), set(L.guarded_cells))
        treasures = [dict(cell=[x, y], contents=loot[(x, y)]) for x, y in tcells]
        # ---- encounters
        pool = roster(enemies, c, k, ch['levels'])
        groups = encounter_groups(pool, c, k, n, rng)
        for rid, fls in RARE.items():
            if n in fls:
                partner = min(pool, key=lambda e: e['level'])['id']
                groups += [list(g) for g in groups[:4]]  # dilute: the rare row is ~1 in 13
                groups.append([rid, partner] if rid != 'golden_mimic' else [rid])
        # ---- events (guards in front of chests; trial floors: the superbosses)
        events = []
        ecells = cells('E')
        for i, p in enumerate(ecells):
            size = 4 if c <= 3 else 5
            g = sorted(rng.sample(pool, min(len(pool), 2)), key=lambda e: e['level'])
            grp = [g[-1]['id']] * 2 + [x['id'] for x in rng.choices(pool, k=size - 2)]
            events.append(dict(cell=list(p), group=grp))
        boss_group = [ch['boss']] if k == 5 and c < 7 else (['abyss_lord_ex'] if n == 35 else [])
        # ---- FOEs
        foes = []
        fl = [r for kind, r in L.patrols if kind == 'foe']
        for j, route in enumerate(fl[:plan['foes']]):
            group, power = FOES[c][(n + j) % len(FOES[c])]
            chase = 0 if c == 1 and k <= 2 else min(4, 1 + c // 2 + j)
            foes.append(dict(id='foe_b%d_%d' % (n, j + 1), group=list(group), spawn=list(route[0]),
                             patrol=[list(p) for p in route], chase_range=chase, power=power))
        mid = [r for kind, r in L.patrols if kind == 'midboss']
        if plan['midboss'] and mid:
            group, power = MIDBOSS[c]
            foes.append(dict(id='midboss_b%d' % n, group=list(group), spawn=list(mid[0][0]),
                             patrol=[list(p) for p in mid[0]], chase_range=0, power=power))
        # ---- lore stones (texts in reading order: nearest the start first)
        dist = L.bfs(L.start)
        ncells = sorted(cells('N'), key=lambda p: dist.get(p, 999))
        lore_stones = [dict(cell=list(p), text=t) for p, t in zip(ncells, lore)]
        # ---- pacing
        steps = solver.exploration_steps(rows, coverage=0.85)
        battles = TARGET_BATTLES[c]
        per = max(MIN_STEPS + 6, steps / battles)
        rate = round(1.0 / max(4.0, per - MIN_STEPS), 3)
        row = {
            'id': '%s_%d' % (ch['id'], k),
            'floor_label': 'B%dF' % n,
            'area_name': area,
            'area_description': desc,
            'rows': rows,
            'tileset': ch['tileset'],
            'battle_backdrop': tmpl.get('battle_backdrop', ''),
            'encounter_groups': groups,
            'showcase_group': list(groups[0]),
            'boss_group': boss_group,
            'fog_color': list(tmpl['fog_color']),
            'ambient_particle_tint': list(tmpl['ambient_particle_tint']),
            'overlay': tmpl['overlay'],
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
        if c >= 5:
            row.update({kk: (list(v) if isinstance(v, list) else v) for kk, v in LOOK[c].items()})
        if k == 5 and c < 7:
            pre, post = texts.BOSS_TEXT[ch['boss']]
            row['boss_pre_text'], row['boss_post_text'] = pre, post
        if n == 30:
            row['ending'] = True
        if c == 7:
            sb = SUPERBOSS_FLOOR[n]
            if n < 35:
                # Boss cell -> fixed event battle with the superboss; it guards the stairs.
                rows2 = [list(r) for r in rows]
                bx, by = cells('B')[0]
                rows2[by][bx] = 'E'
                row['rows'] = [''.join(r) for r in rows2]
                row['events'].append(dict(cell=[bx, by], group=[sb]))
            else:
                # B35F: leviathan's echo waits on the corridor before the last chamber.
                path = L.path(L.start, cells('B')[0])
                guard = None
                for p in reversed(path[:-1]):
                    if rows[p[1]][p[0]] == '.' and L.degree(p) == 2:
                        guard = p
                        break
                rows2 = [list(r) for r in rows]
                rows2[guard[1]][guard[0]] = 'E'
                row['rows'] = [''.join(r) for r in rows2]
                row['events'].append(dict(cell=list(guard), group=[sb]))
                pre, post = texts.BOSS_TEXT['abyss_lord_ex']
                row['boss_pre_text'], row['boss_post_text'] = pre, post
            row['events'].sort(key=lambda e: (e['cell'][1], e['cell'][0]))
        row['_file'] = 'b%02d_%s_%d' % (n, ch['id'], k)
        # sanity: every FOE/event/encounter id exists
        for g in groups + [e['group'] for e in row['events']] + [f['group'] for f in foes] + [boss_group]:
            for eid in g:
                assert eid in by_id, (n, eid)
        floors.append(row)
        meta.append(dict(n=n, c=c, k=k, seed=seed, states=res['states'], walkable=res['walkable'], steps=steps,
                         rate=rate, battles=battles, layout=L))
    return floors, meta
