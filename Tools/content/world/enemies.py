"""Monster roster for the 35-floor campaign.

Stats come from one level model (a normal monster of level L) times a per-monster identity ratio, so a monster
keeps its character (a beetle is tanky, a wisp is a glass cannon) at any level:
- the 51 original monsters: ratio = authored stat / model(original level), re-levelled into chapters 1-4;
- palette variants (spec VARIANTS): ratios of their base monster, a new element theme, model = base id + tint;
- new models (spec NEW_MODELS): hand-written ratios per archetype.
EXP follows the hero curve so a party fighting the chapter roster levels through the chapter's range.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ level model
MODEL = {'max_hp': (60, 20.0), 'attack': (15, 2.4), 'magic': (12, 2.3), 'defense': (8, 1.6),
         'resistance': (4, 1.9), 'speed': (12, 0.75)}
STATS = ('max_hp', 'attack', 'magic', 'defense', 'resistance', 'speed')
# Past the original level range (36) heroes gain gear tiers 5-8 on top of linear growth; monsters keep pace.
LATE = {'max_hp': 0.022, 'attack': 0.010, 'magic': 0.010, 'defense': 0.012, 'resistance': 0.012, 'speed': 0.0}
LATE_FROM = 36


def model(stat, level):
    a, b = MODEL[stat]
    v = a + b * level
    return v * (1 + LATE[stat] * max(0, level - LATE_FROM))


def xp_to_next(level):
    """Mirror of PartyStats.XpToNext."""
    return int(math.floor(30.0 * max(1, level) ** 1.75 + 0.5)) + 25


# Kills of matching level per hero level (lower = faster levelling). Interpolated by level; tuned with the
# campaign simulation (Tools/content/build_world.py --levels) so the party tracks each chapter's level range.
KILLS_PER_LEVEL = [(1, 9), (6, 14), (12, 21), (24, 31), (34, 38), (44, 44), (54, 50), (64, 58), (72, 64)]


def kills_per_level(level):
    pts = KILLS_PER_LEVEL
    if level <= pts[0][0]:
        return pts[0][1]
    for (l0, d0), (l1, d1) in zip(pts, pts[1:]):
        if level <= l1:
            return d0 + (d1 - d0) * (level - l0) / (l1 - l0)
    return pts[-1][1]


def exp_for(level, mult=1.0):
    return max(1, int(round(xp_to_next(level) / kills_per_level(level) * mult)))


def gold_for(level, mult=1.0):
    return max(1, int(round((6 + 3.6 * level) * mult)))


# ------------------------------------------------------------------ chapter roster (existing monsters)
# id -> new level. Normal monsters spread over the chapter; elites are FOE / mid-boss levels; bosses sit one
# level above the chapter's exit level.
RELEVEL = {
    # chapter 1 (Lv 1-12)
    'slime': 1, 'sprout': 2, 'horned_rabbit': 3, 'mushroom': 5, 'killer_bee': 5, 'bat': 7, 'mandragora': 7,
    'rhino_beetle': 9, 'pixie': 10, 'elite_mushroom': 6, 'elite_rhino_beetle': 8, 'elite_bat': 11, 'forest_guardian': 13,
    # chapter 2 (Lv 12-24)
    'jellyfish': 13, 'frost_spider': 14, 'coral_crab': 15, 'snow_fairy': 16, 'penguin_mage': 18, 'ice_wolf': 19,
    'yeti': 20, 'ice_golem': 22, 'elite_ice_wolf': 18, 'elite_yeti': 20, 'elite_coral_crab': 22, 'frost_kraken': 25,
    # chapter 3 (Lv 24-34)
    'magma_slime': 25, 'hellhound': 26, 'flame_elemental': 26, 'sand_scorpion': 28, 'sand_golem': 28, 'lizardman': 30,
    'phoenix': 30, 'harpy': 32, 'fire_drake': 32, 'elite_hellhound': 28, 'elite_sand_golem': 30, 'elite_fire_drake': 33,
    'flame_sphinx': 35,
    # chapter 4 (Lv 34-44)
    'skeleton': 35, 'ghost': 35, 'grave_bat': 37, 'mimic': 38, 'scarecrow': 39, 'dark_knight': 41, 'lich': 42, 'wisp': 42,
    'elite_skeleton': 38, 'elite_dark_knight': 40, 'elite_scarecrow': 42, 'elite_mimic': 43, 'boss': 45,
}

# Boss trinkets, progression items and chapter materials added to the original drop tables.
EXTRA_DROPS = {
    'forest_guardian': [('job_medal', 1.0), ('acc_crystal_crown', 1.0), ('enhance_stone', 1.0)],
    'frost_kraken': [('job_medal', 1.0), ('acc_kraken_eye', 1.0), ('enhance_stone', 1.0)],
    'flame_sphinx': [('acc_sphinx_riddle', 1.0), ('enhance_stone_hi', 1.0), ('seed_magic', 1.0)],
    'boss': [('master_seal', 1.0), ('acc_lich_phylactery', 1.0), ('enhance_stone_hi', 1.0), ('seed_life', 1.0)],
}
# Legendary (tier 8) pieces leave the chapter 4 boss: they belong to the trial corridor now.
REPLACE_DROPS = {
    'boss': {'sword_dawn': 'sword_runic', 'staff_starlight': 'staff_bone', 'bow_star': 'bow_wraith', 'mace_dawn': 'mace_requiem'},
}
RENAME = {'boss': '심연의 전령 모르데인'}


def chapter_of_level(level):
    for c, (lo, hi) in enumerate(((1, 12), (12, 24), (24, 34), (34, 44), (44, 54), (54, 64), (64, 72)), 1):
        if level <= hi:
            return c
    return 7


STONES = {1: 'enhance_stone', 2: 'enhance_stone', 3: 'enhance_stone', 4: 'enhance_stone_hi', 5: 'enhance_stone_hi',
          6: 'enhance_stone_abyss', 7: 'enhance_stone_abyss'}


def _ratios(row, level):
    return {s: row[s] / model(s, level) for s in STATS}


def _apply(row, level, ratios, rank, exp_mult=None, gold_mult=None):
    for s in STATS:
        row[s] = max(1, int(round(model(s, level) * ratios[s])))
    row['level'] = level
    if exp_mult is None:
        tough = math.sqrt(max(0.3, ratios['max_hp']) * max(0.3, (ratios['attack'] + ratios['magic']) / 2))
        exp_mult = min(1.6, max(0.7, tough))
        if rank == 1:
            exp_mult *= 4.5
        if rank == 2:
            exp_mult = 1
    row['experience_reward'] = exp_for(level, exp_mult)
    row['gold_reward'] = gold_for(level, gold_mult if gold_mult is not None else exp_mult)


def relevel_existing(base):
    out = []
    for src in base:
        row = json.loads(json.dumps(src))
        old = src['level']
        new = RELEVEL[row['id']]
        r = _ratios(src, old)
        rank = row['rank']
        if rank == 2:
            _apply(row, new, r, rank, exp_mult=BOSS_EXP[row['id']], gold_mult=BOSS_GOLD)
        else:
            _apply(row, new, r, rank)
        c = chapter_of_level(new)
        drops = row['drops']
        for old_id, new_id in REPLACE_DROPS.get(row['id'], {}).items():
            for d in drops:
                if d['id'] == old_id:
                    d['id'] = new_id
        have = {d['id'] for d in drops}
        for item, chance in EXTRA_DROPS.get(row['id'], []):
            if item not in have:
                drops.append({'id': item, 'chance': chance})
                have.add(item)
        stone = STONES[c]
        if rank < 2 and stone not in have:
            drops.append({'id': stone, 'chance': 0.06 if rank == 0 else 0.5})
        if row['id'] in RENAME:
            row['display_name'] = RENAME[row['id']]
        out.append(row)
    return out


# Boss EXP multiples of a normal monster of the same level, and gold multiple.
BOSS_EXP = {'forest_guardian': 30, 'frost_kraken': 32, 'flame_sphinx': 34, 'boss': 36, 'leviathan': 38, 'abyss_lord': 40,
            'forest_guardian_ex': 30, 'frost_kraken_ex': 30, 'flame_sphinx_ex': 30, 'boss_ex': 30, 'leviathan_ex': 32,
            'abyss_lord_ex': 40}
BOSS_GOLD = 25


# ------------------------------------------------------------------ palette variants
# id -> (level, element theme overrides, skills/weights, ai, extra fields, drops)
def variant_rows(base_rows, spec):
    by_id = {r['id']: r for r in base_rows}
    base_src = {r['id']: r for r in json.load(open(os.path.join(HERE, 'base_enemies.json'), encoding='utf-8'))}
    out = []
    for vid, name, base, tint, chapter, role in spec.VARIANTS:
        if vid.endswith('_ex'):
            continue  # superbosses are built separately
        cfg = VARIANT_CFG[vid]
        src = base_src[base]
        row = json.loads(json.dumps(by_id[base]))
        row['id'] = vid
        row['display_name'] = name
        row['_file'] = vid
        row['model'] = base
        row['tint'] = [tint[0], tint[1], tint[2], 1.0]
        ratios = _ratios(src, src['level'])
        for k, v in cfg.get('ratio', {}).items():
            ratios[k] *= v
        level = cfg['level']
        rank = cfg.get('rank', 0)
        row['rank'] = rank
        row['is_boss'] = False
        _apply(row, level, ratios, rank, exp_mult=cfg.get('exp'), gold_mult=cfg.get('gold'))
        for k in ('weaknesses', 'resistances', 'skills', 'skill_weights', 'ai_profile', 'evade', 'break_shield',
                  'summons', 'summon_limit', 'gimmicks', 'max_mp', 'actions_per_turn', 'scale_mult', 'hit'):
            if k in cfg:
                row[k] = cfg[k]
        for k in cfg.get('set', {}):
            row[k] = cfg['set'][k]
        if not row.get('summons'):
            row['summons'] = []
            row['summon_limit'] = 0
        row['drops'] = [{'id': i, 'chance': c} for i, c in cfg['drops']]
        row.pop('phases', None)
        out.append(row)
    return out


def D(*pairs):
    return list(pairs)


VARIANT_CFG = {
    'metal_slime': dict(level=20, ratio={'max_hp': 0.0}, exp=None, gold=0.2, ai_profile='runner', evade=0.35,
                        set={'max_hp': 8, 'defense': 999, 'resistance': 999, 'speed': 160, 'experience_reward': 6000,
                             'gold_reward': 30, 'max_mp': 0},
                        weaknesses=[], resistances=[], break_shield=8, gimmicks=['cc_immune', 'dot_resist'],
                        skills=['basic_attack', 'sk_acid_spit'], skill_weights=[3, 1],
                        drops=D(('metal_gel', 1.0), ('seed_swift', 0.15), ('enhance_stone_hi', 0.3), ('acc_exp_charm', 0.02))),
    'gold_slime': dict(level=15, ratio={'max_hp': 0.7, 'defense': 3.0}, gold=1, ai_profile='runner', evade=0.25,
                       set={'gold_reward': 2500, 'speed': 90, 'experience_reward': 120},
                       weaknesses=[4], resistances=[2, 3], break_shield=4, gimmicks=['cc_resist'],
                       skills=['basic_attack', 'sk_acid_spit'], skill_weights=[3, 1],
                       drops=D(('slime_gel', 1.0), ('enhance_stone', 0.3), ('acc_gold_charm', 0.03), ('sword_iron', 0.05))),
    'poison_mushroom': dict(level=9, ratio={'magic': 1.1}, weaknesses=[4], resistances=[7],
                            skills=['basic_attack', 'poison_spore', 'sk_toxic_cloud'], skill_weights=[2, 3, 1], max_mp=30,
                            drops=D(('forest_fiber', 1.0), ('remedy', 0.12), ('healing_potion', 0.22), ('enhance_stone', 0.06),
                                    ('staff_crystal', 0.05), ('acc_antidote_ring', 0.03))),
    'snow_rabbit': dict(level=13, ratio={'speed': 1.2}, weaknesses=[4], resistances=[5], evade=0.15,
                        skills=['basic_attack', 'strong_attack', 'sk_ice_shard'], skill_weights=[3, 1, 1], max_mp=12,
                        drops=D(('frost_fur', 1.0), ('hi_potion', 0.2), ('ether', 0.1), ('enhance_stone', 0.06),
                                ('garb_ranger', 0.05), ('acc_swift_anklet', 0.02))),
    'ice_slime': dict(level=16, ratio={'magic': 1.2}, weaknesses=[4, 6], resistances=[5, 2], max_mp=20,
                      skills=['basic_attack', 'sk_ice_shard'], skill_weights=[2, 2], ai_profile='caster',
                      drops=D(('slime_gel', 1.0), ('frost_crystal', 0.05), ('hi_potion', 0.2), ('enhance_stone', 0.06),
                              ('robe_silk', 0.05), ('acc_freeze_ward', 0.025))),
    'frost_bee': dict(level=21, ratio={'attack': 1.05}, weaknesses=[4, 3], resistances=[5],
                      skills=['basic_attack', 'sk_poison_arrow', 'sk_ice_shard'], skill_weights=[3, 1, 2], max_mp=16,
                      drops=D(('frost_fur', 1.0), ('hi_potion', 0.22), ('ether', 0.1), ('enhance_stone', 0.06),
                              ('bow_hunter', 0.05), ('acc_freeze_ward', 0.025))),
    'ember_bee': dict(level=25, weaknesses=[5, 3], resistances=[4],
                      skills=['basic_attack', 'sk_poison_arrow', 'fireball'], skill_weights=[3, 1, 2], max_mp=20,
                      drops=D(('drake_scale', 1.0), ('mega_potion', 0.15), ('hi_ether', 0.08), ('enhance_stone', 0.06),
                              ('mace_blessed', 0.05), ('acc_burn_ward', 0.025))),
    'lava_beetle': dict(level=29, ratio={'max_hp': 1.15}, weaknesses=[5], resistances=[4, 3, 1],
                        skills=['basic_attack', 'sk_harden', 'sk_fire_breath'], skill_weights=[3, 1, 1], max_mp=20,
                        drops=D(('magma_core', 1.0), ('mega_potion', 0.18), ('hi_ether', 0.08), ('enhance_stone', 0.07),
                                ('armor_plate', 0.05), ('acc_burn_ward', 0.025))),
    'flame_wisp': dict(level=31, weaknesses=[5], resistances=[4, 7], skills=['basic_attack', 'fireball', 'sk_flame_wave'],
                       skill_weights=[1, 3, 1], max_mp=60,
                       drops=D(('magma_core', 1.0), ('ether', 0.1), ('mega_potion', 0.18), ('enhance_stone', 0.06),
                               ('staff_sage', 0.05), ('acc_spirit_pendant', 0.025))),
    'crimson_scorpion': dict(level=33, ratio={'attack': 1.1}, weaknesses=[5, 2], resistances=[4, 3],
                             skills=['basic_attack', 'sk_poison_arrow', 'sk_bleed_edge'], skill_weights=[2, 2, 1], max_mp=20,
                             drops=D(('golem_sandstone', 1.0), ('remedy', 0.12), ('mega_potion', 0.18), ('enhance_stone', 0.07),
                                     ('bow_gale', 0.05), ('acc_thunder_amulet', 0.025))),
    'skeleton_mage': dict(level=38, ratio={'magic': 1.5, 'attack': 0.7, 'resistance': 1.3}, weaknesses=[8, 2],
                          resistances=[7, 5], ai_profile='caster', max_mp=60,
                          skills=['basic_attack', 'sk_spirit_fire', 'sk_hex', 'sk_ice_lance'], skill_weights=[1, 3, 1, 2],
                          drops=D(('old_bone', 1.0), ('hi_ether', 0.12), ('mega_potion', 0.18), ('enhance_stone_hi', 0.05),
                                  ('robe_spirit', 0.04), ('acc_dark_amulet', 0.025))),
    'dark_pixie': dict(level=36, ratio={'magic': 1.1}, weaknesses=[8], resistances=[7], ai_profile='support', max_mp=60,
                       skills=['basic_attack', 'heal', 'sk_hex', 'sk_curse_screech'], skill_weights=[1, 2, 2, 1],
                       drops=D(('ghost_essence', 1.0), ('hi_ether', 0.12), ('mega_potion', 0.18), ('enhance_stone_hi', 0.05),
                               ('garb_wraith', 0.04), ('acc_curse_ward', 0.025))),
    'ghost_mushroom': dict(level=39, ratio={'max_hp': 1.1}, weaknesses=[4, 8], resistances=[7],
                           skills=['basic_attack', 'poison_spore', 'sk_lullaby'], skill_weights=[2, 2, 2], max_mp=30,
                           ai_profile='caster',
                           drops=D(('forest_fiber', 1.0), ('ghost_essence', 0.3), ('mega_potion', 0.18), ('enhance_stone_hi', 0.05),
                                   ('mace_requiem', 0.04), ('acc_sleep_ward', 0.025))),
    'crypt_hound': dict(level=41, weaknesses=[8, 4], resistances=[7], skills=['basic_attack', 'sk_twin_bite', 'sk_e_shadow_bite'],
                        skill_weights=[3, 2, 1], ai_profile='aggressive', max_mp=12,
                        drops=D(('old_bone', 1.0), ('mega_potion', 0.2), ('hi_ether', 0.1), ('enhance_stone_hi', 0.05),
                                ('sword_runic', 0.04), ('acc_paralyze_ward', 0.025))),
    'deep_jelly': dict(level=46, ratio={'magic': 1.15}, weaknesses=[2, 4], resistances=[6, 5], max_mp=40,
                       skills=['basic_attack', 'sk_e_thunder', 'sk_lullaby'], skill_weights=[1, 3, 1], ai_profile='caster',
                       drops=D(('pearl', 1.0), ('max_ether', 0.06), ('x_potion', 0.12), ('enhance_stone_hi', 0.06),
                               ('staff_coral', 0.03), ('acc_thunder_amulet', 0.025))),
    'swamp_lizardman': dict(level=48, ratio={'attack': 1.05}, weaknesses=[5, 6], resistances=[3],
                            skills=['basic_attack', 'sk_e_venom_fang', 'sk_bleed_edge'], skill_weights=[3, 2, 1], max_mp=20,
                            drops=D(('scale_blue', 1.0), ('panacea', 0.08), ('x_potion', 0.12), ('enhance_stone_hi', 0.06),
                                    ('garb_tide', 0.03), ('acc_earth_amulet', 0.025))),
    'storm_harpy': dict(level=50, weaknesses=[3, 5], resistances=[6], max_mp=40,
                        skills=['basic_attack', 'sk_e_thunder', 'sk_e_feather_storm'], skill_weights=[2, 2, 1],
                        drops=D(('siren_feather', 1.0), ('x_potion', 0.12), ('max_ether', 0.05), ('enhance_stone_hi', 0.06),
                                ('bow_tide', 0.03), ('acc_swift_anklet', 0.025))),
    'coral_golem': dict(level=52, ratio={'max_hp': 1.1}, weaknesses=[6, 2], resistances=[5, 3, 1],
                        skills=['basic_attack', 'sk_harden', 'sk_titan_crash'], skill_weights=[3, 1, 1], max_mp=24,
                        drops=D(('temple_stone', 1.0), ('pearl', 0.3), ('x_potion', 0.12), ('enhance_stone_hi', 0.07),
                                ('armor_tidal', 0.03), ('acc_iron_bangle', 0.025))),
    'tide_drake': dict(level=53, weaknesses=[6], resistances=[5, 4], max_mp=40,
                       skills=['basic_attack', 'sk_e_water_jet', 'sk_e_tidal_wave'], skill_weights=[2, 2, 1], ai_profile='caster',
                       drops=D(('scale_blue', 1.0), ('x_potion', 0.14), ('max_ether', 0.06), ('enhance_stone_hi', 0.07),
                               ('sword_tidal', 0.03), ('acc_freeze_ward', 0.025))),
    'golden_mimic': dict(level=50, ratio={'defense': 2.5, 'resistance': 2.0, 'max_hp': 0.8}, ai_profile='aggressive', evade=0.05,
                         set={'gold_reward': 4000}, exp=4, weaknesses=[6], resistances=[1, 2, 3], break_shield=6,
                         gimmicks=['cc_resist'], skills=['basic_attack', 'strong_attack', 'sk_dread_stare'], skill_weights=[2, 2, 1],
                         drops=D(('pearl', 1.0), ('seed_power', 0.25), ('seed_magic', 0.25), ('seed_guard', 0.2),
                                 ('sword_void', 0.12), ('staff_void', 0.12), ('bow_void', 0.12), ('mace_judgment', 0.12),
                                 ('acc_ribbon', 0.03))),
    'void_wisp': dict(level=56, weaknesses=[8], resistances=[7, 4], skills=['basic_attack', 'sk_spirit_fire', 'sk_e_void_gaze'],
                      skill_weights=[1, 3, 2], ai_profile='caster', max_mp=60,
                      drops=D(('void_shard', 1.0), ('max_ether', 0.07), ('x_potion', 0.14), ('enhance_stone_abyss', 0.05),
                              ('staff_void', 0.025), ('acc_dark_amulet', 0.025))),
    'void_knight': dict(level=62, ratio={'max_hp': 1.05}, weaknesses=[8], resistances=[7, 1], ai_profile='berserker',
                        skills=['basic_attack', 'sk_cleave', 'sk_e_shadow_bite', 'sk_harden'], skill_weights=[2, 2, 2, 1], max_mp=30,
                        drops=D(('void_shard', 1.0), ('x_potion', 0.16), ('max_ether', 0.07), ('enhance_stone_abyss', 0.06),
                                ('armor_void', 0.025), ('acc_counter_charm', 0.025))),
    'shadow_hound': dict(level=57, weaknesses=[8, 4], resistances=[7], ai_profile='aggressive',
                         skills=['basic_attack', 'sk_twin_bite', 'sk_e_shadow_bite'], skill_weights=[3, 2, 2], max_mp=12,
                         drops=D(('shadow_pelt', 1.0), ('x_potion', 0.14), ('max_ether', 0.06), ('enhance_stone_abyss', 0.05),
                                 ('garb_void', 0.025), ('acc_regen_ring', 0.02))),
    'phantom': dict(level=60, ratio={'magic': 1.1}, weaknesses=[8], resistances=[7, 3, 1], evade=0.22, ai_profile='caster',
                    skills=['basic_attack', 'sk_m_drain', 'sk_dread_stare', 'sk_e_void_gaze'], skill_weights=[1, 3, 1, 2], max_mp=60,
                    drops=D(('void_shard', 1.0), ('ghost_essence', 0.3), ('max_ether', 0.08), ('enhance_stone_abyss', 0.05),
                            ('robe_void', 0.025), ('acc_mana_spring', 0.02))),
    'abyss_crab': dict(level=59, ratio={'defense': 1.15}, weaknesses=[6, 8], resistances=[7, 3],
                       skills=['basic_attack', 'sk_harden', 'sk_e_clamp'], skill_weights=[3, 1, 2], max_mp=20,
                       drops=D(('void_shard', 1.0), ('pearl', 0.2), ('x_potion', 0.14), ('enhance_stone_abyss', 0.06),
                               ('mace_judgment', 0.025), ('acc_iron_bangle', 0.025))),
    'elder_lich': dict(level=66, ratio={'magic': 1.1, 'max_hp': 1.15}, weaknesses=[8, 4], resistances=[7, 5], ai_profile='summoner',
                       summons=['skeleton_mage'], summon_limit=1, max_mp=120,
                       skills=['basic_attack', 'sk_spirit_fire', 'sk_e_void_scythe', 'sk_hex'], skill_weights=[1, 3, 2, 1],
                       drops=D(('trial_emblem', 1.0), ('megalixir', 0.03), ('max_ether', 0.12), ('enhance_stone_abyss', 0.08),
                               ('staff_void', 0.04), ('acc_lich_phylactery', 0.01), ('seed_mind', 0.03))),
    'chaos_yeti': dict(level=67, ratio={'max_hp': 1.15, 'attack': 1.1}, weaknesses=[8, 4], resistances=[5, 7],
                       ai_profile='berserker', max_mp=30,
                       skills=['basic_attack', 'stunning_slam', 'sk_e_dark_trample', 'sk_war_cry'], skill_weights=[3, 2, 2, 1],
                       drops=D(('trial_emblem', 1.0), ('x_potion', 0.2), ('enhance_stone_abyss', 0.08), ('seed_power', 0.03),
                               ('armor_void', 0.04), ('acc_berserk_ring', 0.02))),
    'inferno_phoenix': dict(level=68, ratio={'magic': 1.15}, weaknesses=[5, 3], resistances=[4, 7], ai_profile='support', max_mp=80,
                            skills=['basic_attack', 'sk_rebirth_flame', 'sk_inferno', 'sk_flame_wave'], skill_weights=[1, 2, 2, 2],
                            drops=D(('trial_emblem', 1.0), ('phoenix_plume', 0.12), ('max_ether', 0.1), ('enhance_stone_abyss', 0.08),
                                    ('bow_void', 0.04), ('acc_burn_ward', 0.03), ('seed_life', 0.03))),
}


# ------------------------------------------------------------------ new models (chapter 5 and 6)
def N(id, level, rank, ratios, weak, resist, skills, weights, ai='basic', evade=0.05, shield=3, row=1, mp=30,
      actions=1, scale=1.0, summons=None, limit=0, gimmicks=None, drops=(), exp=None, hit=0.95):
    r = dict(zip(STATS, ratios))
    return dict(id=id, level=level, rank=rank, ratios=r, weak=weak, resist=resist, skills=skills, weights=weights, ai=ai,
                evade=evade, shield=shield, row=row, mp=mp, actions=actions, scale=scale, summons=summons or [],
                limit=limit, gimmicks=gimmicks or [], drops=list(drops), exp=exp, hit=hit)


#                       hp    atk   mag   def   res   spd
NEW_CFG = [
    N('puffer', 45, 0, (0.85, 0.9, 0.8, 1.0, 0.8, 0.9), [3, 6], [5], ['basic_attack', 'sk_e_spike_burst', 'sk_e_puff_up'], [2, 2, 1],
      drops=D(('pearl', 1.0), ('x_potion', 0.12), ('max_ether', 0.05), ('enhance_stone_hi', 0.06), ('sword_tidal', 0.03), ('acc_life_pendant', 0.025))),
    N('sea_urchin', 45, 0, (0.75, 1.0, 0.6, 1.4, 0.8, 0.7), [2, 4], [3, 1], ['basic_attack', 'sk_e_spike_burst', 'sk_harden'], [2, 2, 1],
      row=0, shield=4, drops=D(('pearl', 1.0), ('panacea', 0.06), ('x_potion', 0.12), ('enhance_stone_hi', 0.06), ('mace_pearl', 0.03), ('acc_counter_charm', 0.02))),
    N('merfolk_guard', 47, 0, (1.05, 1.1, 0.7, 1.15, 0.9, 1.0), [6], [5, 3], ['basic_attack', 'sk_e_coral_spear', 'sk_e_shell_bash'], [2, 2, 1],
      row=0, shield=4, drops=D(('scale_blue', 1.0), ('x_potion', 0.12), ('max_ether', 0.05), ('enhance_stone_hi', 0.06), ('armor_tidal', 0.03), ('acc_paralyze_ward', 0.025))),
    N('angler', 47, 0, (0.9, 0.9, 1.15, 0.8, 1.0, 1.0), [6, 3], [5], ['basic_attack', 'sk_e_lure', 'sk_e_deep_bite'], [1, 2, 2],
      ai='aggressive', drops=D(('scale_blue', 1.0), ('max_ether', 0.06), ('x_potion', 0.12), ('enhance_stone_hi', 0.06), ('bow_tide', 0.03), ('acc_sleep_ward', 0.025))),
    N('giant_clam', 49, 0, (1.3, 1.0, 1.0, 1.6, 1.2, 0.6), [6, 2], [5, 1, 3], ['basic_attack', 'sk_e_clamp', 'sk_e_pearl_beam', 'sk_harden'], [2, 2, 1, 1],
      row=0, shield=5, exp=1.4, drops=D(('pearl', 1.0), ('pearl', 0.5), ('x_potion', 0.12), ('enhance_stone_hi', 0.08), ('robe_pearl', 0.03), ('acc_mana_spring', 0.02))),
    N('siren', 50, 0, (0.85, 0.8, 1.25, 0.8, 1.2, 1.15), [3, 2], [5, 6], ['basic_attack', 'sk_e_siren_song', 'sk_e_water_jet', 'heal'], [1, 1, 3, 1],
      ai='support', evade=0.12, mp=70, drops=D(('siren_feather', 1.0), ('max_ether', 0.08), ('x_potion', 0.12), ('enhance_stone_hi', 0.06), ('staff_coral', 0.03), ('acc_sleep_ward', 0.025))),
    N('sea_serpent', 51, 0, (1.15, 1.15, 0.9, 1.0, 0.9, 1.1), [6, 1], [5], ['basic_attack', 'sk_e_constrict', 'sk_e_venom_fang'], [2, 2, 2],
      ai='aggressive', drops=D(('scale_blue', 1.0), ('panacea', 0.06), ('x_potion', 0.12), ('enhance_stone_hi', 0.06), ('garb_tide', 0.03), ('acc_earth_amulet', 0.025))),
    N('temple_guardian', 52, 0, (1.3, 1.15, 0.7, 1.35, 1.0, 0.8), [6, 2], [3, 1, 7], ['basic_attack', 'sk_e_halberd', 'sk_e_stone_skin'], [2, 2, 1],
      ai='berserker', row=0, shield=6, exp=1.4, drops=D(('temple_stone', 1.0), ('x_potion', 0.14), ('max_ether', 0.05), ('enhance_stone_hi', 0.08), ('sword_tidal', 0.03), ('acc_iron_bangle', 0.025))),
    N('drowned_knight', 48, 1, (1.0, 1.25, 0.8, 1.25, 1.0, 0.95), [6, 8], [5, 7, 1], ['basic_attack', 'sk_e_anchor_smash', 'sk_e_drowning_sweep', 'sk_harden'],
      [2, 2, 2, 1], ai='berserker', actions=2, shield=6, scale=1.3, gimmicks=['cc_resist'],
      drops=D(('scale_blue', 1.0), ('temple_stone', 1.0), ('x_potion', 0.4), ('max_ether', 0.2), ('armor_tidal', 0.2), ('acc_paralyze_ward', 0.15), ('enhance_stone_hi', 0.5))),
    N('naga_priestess', 53, 1, (0.95, 0.9, 1.3, 1.0, 1.3, 1.05), [3, 6], [5, 7], ['basic_attack', 'sk_e_trident', 'sk_e_tidal_wave', 'sk_e_naga_hymn'],
      [1, 3, 2, 1], ai='summoner', actions=2, shield=5, scale=1.25, summons=['sea_serpent'], limit=2, gimmicks=['cc_resist'], mp=120,
      drops=D(('pearl', 1.0), ('siren_feather', 1.0), ('max_ether', 0.4), ('x_potion', 0.4), ('staff_coral', 0.2), ('acc_mana_spring', 0.15), ('enhance_stone_hi', 0.5))),
    N('turtle_titan', 50, 1, (1.4, 1.1, 0.9, 1.6, 1.2, 0.7), [6, 2], [5, 1, 3], ['basic_attack', 'sk_e_shell_quake', 'sk_e_stone_skin', 'sk_e_water_jet'],
      [2, 2, 1, 1], ai='basic', actions=2, shield=8, scale=1.4, gimmicks=['cc_resist'], row=0,
      drops=D(('temple_stone', 1.0), ('pearl', 1.0), ('x_potion', 0.4), ('seed_guard', 0.1), ('armor_tidal', 0.2), ('acc_iron_bangle', 0.15), ('enhance_stone_hi', 0.5))),
    # chapter 6
    N('void_eye', 55, 0, (0.8, 0.7, 1.25, 0.8, 1.2, 1.0), [8, 3], [7], ['basic_attack', 'sk_e_void_gaze', 'sk_dread_stare'], [1, 3, 1],
      ai='caster', evade=0.12, mp=60, drops=D(('void_shard', 1.0), ('max_ether', 0.07), ('x_potion', 0.12), ('enhance_stone_abyss', 0.05), ('staff_void', 0.025), ('acc_silence_ward', 0.025))),
    N('chaos_spawn', 56, 0, (1.2, 1.05, 0.9, 0.9, 0.9, 0.8), [8, 4], [7, 2], ['basic_attack', 'sk_e_tentacle_flail', 'sk_e_devour'], [2, 2, 1],
      ai='aggressive', row=0, drops=D(('void_shard', 1.0), ('x_potion', 0.14), ('panacea', 0.06), ('enhance_stone_abyss', 0.05), ('mace_judgment', 0.025), ('acc_regen_ring', 0.02))),
    N('shadow_beast', 58, 0, (1.15, 1.2, 0.9, 1.0, 0.9, 1.15), [8, 4], [7], ['basic_attack', 'sk_e_shadow_bite', 'sk_twin_bite'], [2, 2, 2],
      ai='aggressive', drops=D(('shadow_pelt', 1.0), ('x_potion', 0.14), ('max_ether', 0.05), ('enhance_stone_abyss', 0.05), ('garb_void', 0.025), ('acc_tp_crest', 0.02))),
    N('gargoyle', 58, 0, (1.0, 1.1, 0.8, 1.4, 0.9, 1.0), [2, 8], [3, 1, 7], ['basic_attack', 'sk_e_stone_dive', 'sk_harden'], [2, 2, 1],
      shield=5, drops=D(('gargoyle_horn', 1.0), ('x_potion', 0.14), ('max_ether', 0.05), ('enhance_stone_abyss', 0.06), ('armor_void', 0.025), ('acc_iron_bangle', 0.025))),
    N('nightmare', 60, 0, (1.05, 1.0, 1.15, 1.0, 1.1, 1.25), [8], [7, 4], ['basic_attack', 'sk_e_dark_trample', 'sk_e_nightmare'], [2, 2, 1],
      ai='aggressive', drops=D(('shadow_pelt', 1.0), ('max_ether', 0.08), ('x_potion', 0.14), ('enhance_stone_abyss', 0.05), ('bow_void', 0.025), ('acc_sleep_ward', 0.025))),
    N('doppelganger', 61, 0, (1.0, 1.1, 1.1, 1.0, 1.0, 1.1), [8, 2], [7], ['basic_attack', 'sk_e_mirror_strike', 'sk_e_mirror_guard', 'strong_attack'], [2, 2, 1, 1],
      ai='caster', mp=60, drops=D(('void_shard', 1.0), ('max_ether', 0.08), ('x_potion', 0.14), ('enhance_stone_abyss', 0.05), ('sword_void', 0.025), ('acc_counter_charm', 0.025))),
    N('abyss_worm', 63, 0, (1.35, 1.2, 0.8, 1.1, 0.9, 0.75), [4, 8], [2, 7], ['basic_attack', 'sk_e_burrow_strike', 'sk_e_devour'], [2, 2, 1],
      row=0, shield=5, exp=1.4, drops=D(('shadow_pelt', 1.0), ('x_potion', 0.16), ('megalixir', 0.01), ('enhance_stone_abyss', 0.07), ('armor_void', 0.025), ('acc_life_pendant', 0.025))),
    N('fallen_angel', 59, 1, (1.0, 1.3, 1.1, 1.1, 1.1, 1.15), [7, 3], [8, 1], ['basic_attack', 'sk_e_fallen_blade', 'sk_e_black_wings', 'holy_light'],
      [1, 3, 2, 1], ai='aggressive', actions=2, shield=6, scale=1.3, gimmicks=['cc_resist'], evade=0.1,
      drops=D(('fallen_feather', 1.0), ('void_shard', 1.0), ('x_potion', 0.4), ('phoenix_plume', 0.15), ('sword_void', 0.2), ('acc_holy_amulet', 0.15), ('enhance_stone_abyss', 0.5))),
    N('void_reaper', 63, 1, (0.95, 1.1, 1.3, 1.0, 1.2, 1.2), [8], [7, 3], ['basic_attack', 'sk_e_void_scythe', 'sk_e_death_mark', 'sk_soul_reap'],
      [1, 3, 1, 2], ai='caster', actions=2, shield=6, scale=1.3, gimmicks=['cc_resist'], mp=150, evade=0.12,
      drops=D(('void_shard', 1.0), ('fallen_feather', 1.0), ('max_ether', 0.4), ('megalixir', 0.05), ('staff_void', 0.2), ('acc_curse_ward', 0.15), ('enhance_stone_abyss', 0.5))),
    N('crystal_horror', 61, 1, (1.45, 1.15, 1.0, 1.45, 1.1, 0.85), [2, 8], [3, 1, 7], ['basic_attack', 'sk_e_crystal_spike', 'sk_e_crystal_shell', 'sk_titan_crash'],
      [2, 2, 1, 2], ai='berserker', actions=2, shield=8, scale=1.35, gimmicks=['cc_resist'], row=0,
      drops=D(('void_shard', 1.0), ('gargoyle_horn', 1.0), ('x_potion', 0.4), ('seed_guard', 0.1), ('armor_void', 0.2), ('acc_crystal_crown', 0.05), ('enhance_stone_abyss', 0.5))),
]

# Boss rows (phases written out). Ratios are relative to the normal model at the boss level.
BOSSES = {
    'leviathan': dict(level=55, ratios=(16.0, 2.05, 2.05, 1.15, 1.15, 1.1), weak=[6, 3], resist=[5, 4], shield=7,
                      skills=['sk_lev_tail_crush', 'sk_lev_maelstrom', 'sk_lev_thunder_fin', 'sk_lev_deep_roar', 'sk_lev_abyss_breath'],
                      phases=[
                          dict(hp_below=1.0, actions_per_turn=2, skills=['sk_lev_tail_crush', 'sk_lev_maelstrom', 'sk_lev_deep_roar'], weights=[3, 2, 1], summon=[],
                               line='신전의 종이 울리지 않은 지 천 년. 뭍의 것들이 다시 이 바다를 더럽히는가.'),
                          dict(hp_below=0.6, actions_per_turn=2, skills=['sk_lev_tail_crush', 'sk_lev_thunder_fin', 'sk_lev_maelstrom'], weights=[2, 2, 2],
                               summon=['siren', 'siren'], line='노래하라, 딸들아! 침입자를 깊은 잠에 가둬라!'),
                          dict(hp_below=0.3, actions_per_turn=3, skills=['sk_lev_abyss_breath', 'sk_lev_tail_crush', 'sk_lev_thunder_fin'], weights=[2, 2, 1],
                               summon=[], line='이 아래에 무엇이 있는지 아느냐… 나는 문이 아니다. 뚜껑이다!'),
                      ],
                      drops=D(('leviathan_fin', 1.0), ('master_seal', 1.0), ('acc_dragon_fang', 1.0), ('enhance_stone_abyss', 1.0),
                              ('seed_life', 1.0), ('megalixir', 1.0), ('sword_void', 0.25), ('robe_void', 0.25))),
    'abyss_lord': dict(level=65, ratios=(19.0, 2.2, 2.2, 1.25, 1.25, 1.2), weak=[8], resist=[7, 1, 3], shield=8,
                       skills=['sk_lord_void_blade', 'sk_lord_dominion', 'sk_lord_eclipse', 'sk_lord_crown', 'sk_lord_annihilation', 'sk_lord_soul_drain'],
                       phases=[
                           dict(hp_below=1.0, actions_per_turn=2, skills=['sk_lord_void_blade', 'sk_lord_dominion', 'sk_lord_eclipse'], weights=[3, 2, 1], summon=[],
                                line='종지기들이여. 루멘의 등불이 여기까지 너희를 이끌었구나. 그 불도 곧 꺼진다.'),
                           dict(hp_below=0.65, actions_per_turn=2, skills=['sk_lord_void_blade', 'sk_lord_soul_drain', 'sk_lord_dominion', 'sk_lord_crown'],
                                weights=[3, 2, 2, 1], summon=['void_knight', 'void_wisp'], line='무릎 꿇어라. 너희가 잃은 모든 것을 돌려주마. 그것이 심연의 자비다.'),
                           dict(hp_below=0.3, actions_per_turn=3, skills=['sk_lord_annihilation', 'sk_lord_void_blade', 'sk_lord_soul_drain', 'sk_lord_eclipse'],
                                weights=[2, 3, 2, 1], summon=['phantom'], line='빛이… 어째서 꺼지지 않는가! 좋다, 모든 것을 무(無)로 되돌리겠다!'),
                       ],
                       drops=D(('lord_crown', 1.0), ('acc_abyss_heart', 1.0), ('enhance_stone_abyss', 1.0), ('megalixir', 1.0),
                               ('seed_power', 1.0), ('seed_magic', 1.0))),
}

# Superbosses: the gold-tinted rematches of the trial corridor (postgame). Base boss skills plus a signature.
SUPERBOSS = {
    'forest_guardian_ex': dict(level=66, mult=(1.25, 1.15), sig='sk_ex_ancient_wrath', summon=['inferno_phoenix'],
                               drops=D(('trial_emblem', 1.0), ('bow_star', 1.0), ('acc_crystal_crown', 1.0), ('seed_life', 1.0), ('megalixir', 1.0))),
    'frost_kraken_ex': dict(level=67, mult=(1.25, 1.15), sig='sk_ex_abyss_tide', summon=['deep_jelly', 'deep_jelly'],
                            drops=D(('trial_emblem', 1.0), ('staff_starlight', 1.0), ('acc_kraken_eye', 1.0), ('seed_mind', 1.0), ('megalixir', 1.0))),
    'flame_sphinx_ex': dict(level=68, mult=(1.25, 1.15), sig='sk_ex_solar_apocalypse', summon=['flame_wisp', 'flame_wisp'],
                            drops=D(('trial_emblem', 1.0), ('mace_dawn', 1.0), ('acc_sphinx_riddle', 1.0), ('seed_magic', 1.0), ('megalixir', 1.0))),
    'boss_ex': dict(level=69, mult=(1.25, 1.15), sig='sk_ex_requiem', summon=['elder_lich'],
                    drops=D(('trial_emblem', 1.0), ('robe_dawn', 1.0), ('garb_dawn', 1.0), ('acc_lich_phylactery', 1.0), ('seed_guard', 1.0))),
    'leviathan_ex': dict(level=70, mult=(1.25, 1.15), sig='sk_ex_abyss_tide', summon=['naga_priestess'],
                         drops=D(('trial_emblem', 1.0), ('armor_dawn', 1.0), ('acc_dragon_fang', 1.0), ('seed_swift', 1.0), ('megalixir', 1.0))),
    'abyss_lord_ex': dict(level=72, mult=(1.3, 1.2), sig='sk_ex_true_void', summon=['void_reaper', 'fallen_angel'],
                          drops=D(('trial_emblem', 1.0), ('sword_dawn', 1.0), ('acc_ribbon', 1.0), ('acc_abyss_heart', 1.0), ('seed_power', 1.0), ('megalixir', 1.0))),
}

EX_LINES = {
    'forest_guardian_ex': ['시련의 회랑에 오신 것을 환영한다, 종지기여. 나는 숲의 기억. 그대들의 뿌리가 얼마나 깊은지 보겠다.',
                           '뿌리는 천 년을 버틴다. 그대들은 몇 걸음이나 버티겠느냐!', '좋다… 숲 전체가 그대들을 시험하리라!'],
    'frost_kraken_ex': ['다시 왔구나, 아이들아. 이번엔 자장가가 아니야. 진짜 바다의 노래를 들려줄게.',
                        '심해의 아이들아, 손님을 맞으렴.', '파도가… 너희를 원해!'],
    'flame_sphinx_ex': ['수수께끼는 끝났다. 남은 것은 답뿐이다. 태양 앞에서 너희의 답을 증명하라.',
                        '태양은 지지 않는다. 다만 잠시 숨을 고를 뿐.', '보아라, 마지막 일출을!'],
    'boss_ex': ['스승님의 회랑에서 다시 만나는군. 이번엔 심연이 아닌, 나 자신의 힘으로 겨루겠다.',
                '망자들이여, 내 곁에! 한 번만 더 함께 싸워다오!', '이것이… 내가 지키지 못한 모든 것의 무게다!'],
    'leviathan_ex': ['뚜껑은 닫혔고, 바다는 다시 자유롭다. 그러니 이제 마음껏 싸워 보자, 뭍의 용사들이여.',
                     '나가여, 노래하라! 신전이 깨어난다!', '천 년의 바다가 한 번에 덮친다!'],
    'abyss_lord_ex': ['…회랑의 끝에서 다시 만났군. 나는 심연이 남긴 그림자. 너희가 이긴 것이 정말 끝이었는지 시험하겠다.',
                      '보아라, 너희가 쓰러뜨린 자들의 그림자다!', '여명이 오는 한, 밤도 다시 온다. 그 밤을 이길 수 있겠느냐!'],
}


def build_new(spec, drops_check=None):
    out = []
    archetypes = {i: a for i, _, _, a, _, _ in spec.NEW_MODELS}
    names = {i: n for i, n, *_ in spec.NEW_MODELS}
    for cfg in NEW_CFG:
        level, rank = cfg['level'], cfg['rank']
        row = {
            'id': cfg['id'], 'display_name': names[cfg['id']], 'rank': rank, 'is_boss': False, 'hit': cfg['hit'],
            'level': level, 'max_mp': cfg['mp'], 'evade': cfg['evade'], 'break_shield': cfg['shield'],
            'weaknesses': cfg['weak'], 'resistances': cfg['resist'], 'drops': [], 'scale_mult': cfg['scale'],
            'actions_per_turn': cfg['actions'], 'ai_profile': cfg['ai'], 'summons': cfg['summons'],
            'summon_limit': cfg['limit'], 'skill_weights': cfg['weights'], 'skills': cfg['skills'],
            'archetype': archetypes[cfg['id']], 'battle_row': cfg['row'], 'tint': [1.0, 1.0, 1.0, 1.0], 'model': '',
        }
        if cfg['gimmicks']:
            row['gimmicks'] = cfg['gimmicks']
        _apply(row, level, cfg['ratios'], rank, exp_mult=None if cfg['exp'] is None else cfg['exp'] * (4.5 if rank == 1 else 1))
        seen = set()
        for i, c in cfg['drops']:
            if i in seen:
                continue
            seen.add(i)
            row['drops'].append({'id': i, 'chance': c})
        row['_file'] = cfg['id']
        out.append(row)
    for bid, cfg in BOSSES.items():
        out.append(_boss_row(bid, names[bid], archetypes[bid], cfg))
    return out


def _boss_row(bid, name, archetype, cfg):
    level = cfg['level']
    ratios = dict(zip(STATS, cfg['ratios']))
    row = {
        'id': bid, 'display_name': name, 'rank': 2, 'is_boss': True, 'hit': 0.95, 'gimmicks': ['cc_immune', 'dot_resist'],
        'level': level, 'max_mp': 0, 'evade': 0.05, 'break_shield': cfg['shield'], 'weaknesses': cfg['weak'],
        'resistances': cfg['resist'], 'drops': [{'id': i, 'chance': c} for i, c in cfg['drops']], 'scale_mult': 1.0,
        'actions_per_turn': 2, 'ai_profile': 'boss', 'summons': [], 'summon_limit': 0,
        'skill_weights': [1] * len(cfg['skills']), 'skills': cfg['skills'], 'archetype': archetype, 'battle_row': 1,
        'tint': [1.0, 1.0, 1.0, 1.0], 'model': '', 'phases': cfg['phases'], '_file': bid,
    }
    _apply(row, level, ratios, 2, exp_mult=BOSS_EXP[bid], gold_mult=BOSS_GOLD)
    return row


def build_superbosses(rows, spec):
    by_id = {r['id']: r for r in rows}
    tints = {v[0]: v[3] for v in spec.VARIANTS}
    names = {v[0]: v[1] for v in spec.VARIANTS}
    out = []
    for xid, cfg in SUPERBOSS.items():
        base = by_id[xid[:-3]]
        row = json.loads(json.dumps(base))
        row['id'] = xid
        row['_file'] = xid
        row['display_name'] = names[xid]
        row['model'] = base['id']
        t = tints[xid]
        row['tint'] = [t[0], t[1], t[2], 1.0]
        level = cfg['level']
        ratios = _ratios(base, base['level'])
        hpm, offm = cfg['mult']
        ratios['max_hp'] *= hpm
        ratios['attack'] *= offm
        ratios['magic'] *= offm
        _apply(row, level, ratios, 2, exp_mult=BOSS_EXP[xid], gold_mult=BOSS_GOLD)
        row['break_shield'] = base['break_shield'] + 2
        sig = cfg['sig']
        if sig not in row['skills']:
            row['skills'] = row['skills'] + [sig]
            row['skill_weights'] = row['skill_weights'] + [1]
        lines = EX_LINES[xid]
        phases = json.loads(json.dumps(base.get('phases') or []))
        if not phases:
            phases = [dict(hp_below=1.0, actions_per_turn=2, skills=list(base['skills']), weights=[1] * len(base['skills']), summon=[], line='')]
        # Three phases: opening, summons at 60 %, signature frenzy at 30 % — one more action than the original.
        first = phases[0]
        mid = phases[1] if len(phases) > 1 else phases[0]
        last = phases[-1]
        new = [
            dict(hp_below=1.0, actions_per_turn=min(3, first['actions_per_turn'] + 1), skills=first['skills'], weights=first['weights'],
                 summon=[], line=lines[0]),
            dict(hp_below=0.6, actions_per_turn=min(3, mid['actions_per_turn'] + 1), skills=mid['skills'] + [sig],
                 weights=mid['weights'] + [1], summon=cfg['summon'], line=lines[1]),
            dict(hp_below=0.3, actions_per_turn=min(4, last['actions_per_turn'] + 1), skills=[sig] + last['skills'],
                 weights=[3] + last['weights'], summon=[], line=lines[2]),
        ]
        row['phases'] = new
        row['drops'] = [{'id': i, 'chance': c} for i, c in cfg['drops']]
        out.append(row)
    return out


def build(spec):
    base = json.load(open(os.path.join(HERE, 'base_enemies.json'), encoding='utf-8'))
    rows = relevel_existing(base)
    rows += variant_rows(rows, spec)
    rows += build_new(spec)
    rows += build_superbosses(rows, spec)
    order = {r['id']: i for i, r in enumerate(rows)}
    return rows
