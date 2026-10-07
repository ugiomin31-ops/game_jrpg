"""Author resource recipes for the pooled Unity particle, mesh and trail renderer (VfxLibrary.cs).

Every recipe is a stack of layers, timed with `delay` so effects read like anime cuts:
  anticipation (converging ring / speed lines / seal)  ->  impact (hit flash, star glint, shock ring)
  ->  linger (embers, smoke, drifting motes).
Layer kinds: quad (billboard or `horizontal`), orbit, burst, emitter, ring (ground ribbon), arc (slash
ribbon), sphere, trail (only while travelling). Sizes are metres at scale 1; `y` is relative to the
effect origin, which BattleView puts at the unit's CenterPoint (about 0.9 m up), so y = -0.82 is the floor.
BattleView multiplies every layer colour by the skill's light colour, so shared keys (impact, slash, ring,
smoke, spark, magic_circle, ...) use near-white colours and let the element tint them, while element/job
keys carry their own palette. `upright` particles keep the texture unrotated (falling arrows, rain).

Preview offline: python Tools/vfx/preview_effects.py --keys fire,job_paladin
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EFFECTS = {}
FLOOR = -0.82


def layer(kind, texture, color, **values):
    return dict(kind=kind, texture=texture, color=color, **values)


def effect(key, description, *layers, duration=1.2, loop=False):
    EFFECTS[key] = dict(key=key, description=description, duration=duration, loop=loop, layers=list(layers))


# --- building blocks -------------------------------------------------------------------------------

def quad(texture, color, life, size, end=0, **values):
    if end:
        values['endSize'] = end
    return layer('quad', texture, color, life=life, size=size, **values)


def burst(texture, color, count=22, life=.65, size=.22, speed=2.2, radius=.12, **values):
    return layer('burst', texture, color, count=count, life=life, size=size, speed=speed, radius=radius, **values)


def emitter(texture, color, rate, life=.8, size=.12, speed=1.5, radius=.5, **values):
    return layer('emitter', texture, color, rate=rate, life=life, size=size, speed=speed, radius=radius, **values)


def seal(texture, color, size, life=1.4, spin=40, y=FLOOR, end=0, **values):
    """Horizontal magic circle lying on the floor (or in the sky with a large y)."""
    return quad(texture, color, life, size, end, horizontal=True, spin=spin, y=y, **values)


def ground_ring(color, size, end, life=.5, y=FLOOR + .04, **values):
    return layer('ring', 'trail', color, life=life, size=size, endSize=end, y=y, **values)


def flash(color='FFFFFF', size=.5, end=1.6, life=.16, delay=0, rotation=12, **values):
    """Anime hit spark: jagged white star that pops and erodes in a few frames."""
    return quad('hit_flash', color, life, size, end, delay=delay, rotation=rotation, **values)


def glint(color='FFFFFF', size=.3, end=1.3, life=.22, delay=0, texture='star4', **values):
    return quad(texture, color, life, size, end, delay=delay, **values)


def shock(color, size=.4, end=2.2, life=.32, delay=0, **values):
    return quad('shockwave', color, life, size, end, delay=delay, **values)


def sparks(color, count=16, speed=4.0, life=.34, size=.26, delay=0, **values):
    return burst('spark', color, count, life=life, size=size, speed=speed, delay=delay, **values)


def embers(color, count=14, speed=1.4, life=.9, size=.11, delay=0, gravity=-.15, **values):
    return burst('ember', color, count, life=life, size=size, speed=speed, delay=delay, gravity=gravity, **values)


def smoke(color, count=8, speed=1.0, life=1.0, size=.8, delay=0, radius=.3, **values):
    return burst('smoke_sheet', color, count, life=life, size=size, speed=speed, delay=delay, radius=radius,
                 tiles=4, alpha=True, **values)


# --- shared battle keys ----------------------------------------------------------------------------

def battle_effects():
    effect('impact', 'Blunt hit: jagged hit spark, star glint, shock ring, spray of sparks and settling embers',
           flash('FFFFFF', .5, 1.5), glint('FFF6E0', .4, 1.4, delay=.02),
           shock('FFE6B8', .3, 1.9, .3), ground_ring('FFE8C0', .4, 2.2, .35, y=-.25),
           sparks('FFE2A8', 16, 4.2), embers('FFD08A', 10, 1.6, .6, gravity=.4, delay=.05), duration=.8)
    effect('slash', 'Blade cut: white-edged crescent sweep, second echo crescent, contact spark and steel sparks',
           layer('arc', 'slash_strip', 'FFFFFF', life=.22, size=1.15, endSize=1.9, rotation=200),
           quad('slash_arc', 'E8F6FF', .28, 2.0, 2.5, height=1.0, rotation=-28, delay=.04),
           flash('FFFFFF', .3, 1.0, .14, delay=.03), sparks('E8F7FF', 14, 3.6),
           embers('D8F0FF', 8, .9, .6, delay=.06, gravity=0), duration=.8)
    effect('critical', 'Critical: converging speed lines, X-slash, hit spark, radiant burst, double shock ring, star rain',
           quad('speed_lines', 'FFFFFF', .35, 3.4, 2.5),
           quad('slash_cross', 'FFFFFF', .3, 1.3, 2.5, delay=.02),
           flash('FFF2C0', .6, 2.1, .2, delay=.04),
           quad('sunburst', 'FFC860', .45, .4, 2.7, delay=.06, spin=30),
           shock('FFE0A0', .5, 3.0, .4, delay=.08), ground_ring('FF7080', .3, 3.2, .5, delay=.06, y=-.3),
           burst('star4', 'FFF4C8', 16, life=.55, size=.3, speed=3.5, delay=.04),
           sparks('FFB060', 24, 6, .4, .34, delay=.04), embers('FFD080', 16, 1.2, 1.0, delay=.1, gravity=-.2),
           duration=1.1)
    effect('spark', 'Electric orb/impact: hot core, flickering bolts, star burst, crackling sparks, ribbon trail',
           quad('lightning_sheet', 'F0F8FF', .5, 1.0, height=2.0, tiles=4),
           quad('glow_hard', 'FFFFFF', .26, .5, .9), glint('FFFFFF', .3, 1.4, .2, delay=.02, texture='star8'),
           layer('trail', 'trail', 'BFE6FF', life=.2, size=.35),
           sparks('F0FAFF', 16, 4.5, .3, .25), embers('C8E8FF', 8, 1.0, .6, gravity=0), duration=.8)
    effect('fire', 'Fireball: hit spark, cel explosion flipbook, flame lick, ember spray and dark smoke, hot trail',
           quad('explosion_sheet', 'FFD9A0', .7, 1.2, 2.1, tiles=4),
           flash('FFF0D0', .5, 1.5, .14), quad('flame_sheet', 'FFC890', .6, 1.1, 1.4, y=.25, tiles=4, delay=.06),
           layer('trail', 'trail', 'FFB070', life=.22, size=.5),
           embers('FFD090', 24, 3.0, .8, .14, gravity=-.15),
           smoke('3A2A30', 6, .8, 1.0, .75, delay=.15, gravity=-.05), duration=1.1)
    effect('flame', 'Fire column: glowing floor scorch, two staggered flame flipbooks, heat pillar, cinders and smoke',
           seal('glow_hard', 'FFB060', 1.5, life=1.1, spin=0, end=2.1),
           quad('flame_sheet', 'FFD8A8', 1.0, 1.5, height=2.6, y=.45, tiles=4),
           quad('flame_sheet', 'FFC080', .9, 1.1, height=2.0, y=.3, tiles=4, delay=.15, rotation=4),
           quad('beam', 'FFB070', .8, .9, height=3.0, y=.7, delay=.05),
           emitter('ember', 'FFE0A0', 40, .8, .13, 2.2, .45, y=FLOOR),
           emitter('smoke_sheet', '403038', 6, 1.2, .6, 1.0, .3, tiles=4, alpha=True, delay=.3, y=.4), duration=1.5)
    effect('ice', 'Frost burst: crystal cluster erupts, snowflake seal spins out, ice shards, frost mist and glints',
           quad('crystal', 'C8F2FF', .8, .6, 1.7, y=-.2), quad('snowflake', 'E8FCFF', .5, .3, 1.8, spin=90),
           flash('DFF8FF', .4, 1.3, .14), ground_ring('A8E8FF', .3, 2.4, .5),
           burst('ice_shard', '9EE4FF', 18, life=.7, size=.3, speed=3.5, gravity=.6),
           smoke('D8F0FF', 5, .5, .9, .7, delay=.1), embers('E0FAFF', 12, .8, 1.0, delay=.1, gravity=-.05), duration=1.1)
    effect('ring', 'Holy/frost seal at the target: rune ring on the floor, light pillar, star glint, orbiting motes',
           ground_ring('FFFFFF', .3, 2.6, .6), seal('magic_circle_c', 'FFF6DA', 1.4, life=.8, end=2.0, spin=90),
           quad('beam', 'FFF8E0', .6, .8, height=3.0, y=.6, delay=.05),
           glint('FFFFFF', .3, 1.6, .3, delay=.05, texture='star8'),
           layer('orbit', 'star4', 'FFF0B8', life=.9, size=.25, radius=.8, spin=220, count=6),
           emitter('ember', 'FFF4D0', 25, .8, .1, 1.6, .6, y=FLOOR), duration=1.1)
    effect('magic_circle', 'Casting seal under the caster: converging ring, counter-rotating rune circles, rising motes',
           ground_ring('FFFFFF', 2.6, 1.2, .45),
           seal('magic_circle_a', 'E8F0FF', 1.5, life=1.4, end=1.8, spin=50),
           seal('magic_circle_c', 'FFFFFF', 1.9, life=1.4, end=2.1, spin=-70, y=FLOOR + .02),
           quad('beam', 'DDE8FF', 1.2, .9, height=1.8, delay=.1),
           layer('orbit', 'star4', 'F0F6FF', life=1.2, size=.16, radius=.9, spin=120, count=4, y=-.4),
           emitter('dot', 'E0F0FF', 26, .8, .08, 1.2, .7, y=FLOOR), duration=1.4)
    effect('heal', 'Healing: leaf-green seal, soft pillar, rising crosses and leaves, body bloom, sparkles',
           seal('magic_circle_b', 'E0FFE8', 1.6, life=1.2, end=1.9, spin=40), ground_ring('E8FFF0', .4, 2.2, .5),
           quad('beam', 'C8FFE0', 1.0, .8, height=2.6, y=.4, delay=.05),
           emitter('plus', 'E8FFF0', 14, .9, .22, 1.3, .5, y=-.6),
           emitter('leaf', 'D0FFD8', 10, 1.0, .18, 1.0, .6, y=-.6),
           quad('glow', 'E0FFE8', .5, .6, 1.4, y=.2, delay=.15),
           embers('F0FFF4', 16, 1.0, 1.0, delay=.1, gravity=-.2), duration=1.5)
    effect('revive', 'Resurrection: sun seal, heaven pillar, unfolding wings, halo, feather fall and rising light',
           seal('magic_circle_f', 'FFF2C8', 2.2, life=1.5, spin=30),
           quad('beam', 'FFF6D8', 1.3, 1.1, height=4.0, y=1.0),
           quad('wings', 'FFF4D2', 1.3, 2.2, 2.8, y=.5, delay=.2),
           quad('halo', 'FFFFFF', 1.2, .7, horizontal=True, y=1.05, delay=.3, spin=60),
           burst('feather', 'FFF8E8', 20, life=1.4, size=.25, speed=1.6, gravity=.1, delay=.25),
           emitter('ember', 'FFF0C0', 25, 1.0, .12, 1.8, .6, y=FLOOR), duration=1.8)
    effect('smoke', 'Toxic/dark cloud: small pop, two waves of cel smoke puffs, bubbles and specks',
           smoke('E8E8E8', 12, .9, 1.1, .9, radius=.4), smoke('B8B8C0', 8, 1.6, .8, .6, delay=.05, radius=.2),
           flash('FFFFFF', .3, 1.0, .14),
           emitter('bubble', 'F0FFF0', 14, .7, .16, .7, .6),
           embers('FFFFFF', 10, 1.2, .8, delay=.1, gravity=0), duration=1.4)
    effect('buff', 'Enhancement: golden seal, rising chevrons orbit, upward motes, light column, finishing glint',
           seal('magic_circle_b', 'FFF2D0', 1.2, life=1.1, end=1.6, spin=60), ground_ring('FFFFFF', .4, 2.0, .5),
           layer('orbit', 'arrow_up', 'FFF0C0', life=1.0, size=.32, radius=.7, spin=120, count=4, y=-.1),
           emitter('ember', 'FFF4D0', 22, .8, .12, 2.0, .5, y=FLOOR),
           quad('beam', 'FFE8B0', .8, .9, height=2.2, y=.2, delay=.05),
           glint('FFFFFF', .3, 1.0, .25, delay=.45, y=.6, texture='star8'), duration=1.2)
    effect('debuff', 'Weakening: abyss sigil, sinking chevrons, spectral skull, dark smoke and falling motes',
           seal('magic_circle_d', 'E8D0FF', 1.5, life=1.1, spin=-50),
           layer('orbit', 'arrow_down', 'E0C8FF', life=.9, size=.32, radius=.7, spin=-90, count=4, y=.3),
           quad('skull_wisp', 'D8B8FF', .8, .8, 1.1, y=.6, delay=.1),
           smoke('403050', 8, .6, 1.1, .8, radius=.4, gravity=-.05),
           emitter('ember', 'D0B0FF', 18, .8, .1, -1.2, .6, y=.8), duration=1.2)
    effect('guard', 'Guard: hex barrier shell flashes, ring pulse, star glint and chips of light',
           layer('sphere', 'hex', 'B8E0FF', life=.9, size=1.6, endSize=1.75),
           quad('ring', 'E0F4FF', .35, .6, 1.8), glint('FFFFFF', .3, 1.0, .2, delay=.02),
           burst('square', 'D0EEFF', 8, life=.4, size=.14, speed=2.0), duration=1.1)
    effect('shield', 'Sustained hexagonal shield shell with a floor ring and slow drifting motes',
           layer('sphere', 'hex', '91D8FF', life=1.5, size=1.6, spin=15),
           seal('ring', 'C8ECFF', 1.6, life=1.5, spin=20),
           emitter('dot', 'D8F2FF', 6, 1.2, .06, .5, .7, y=FLOOR), loop=True)
    effect('break', 'Barrier break: hit spark, shell pops, shard spray, shock ring and an anger mark',
           flash('FFFFFF', .5, 1.6, .15), layer('sphere', 'hex', 'C8ECFF', life=.25, size=1.6, endSize=2.0),
           burst('square', 'B8E4FF', 30, life=.8, size=.2, speed=4.0, gravity=.9),
           shock('D8F0FF', .4, 2.2, .35),
           quad('anger', 'FF6784', .75, 1.0, 1.4, y=.7, delay=.1, alpha=True), duration=1.2)
    effect('summon', 'Summoning: abyss sigil and rune band, opening void rift with glowing seam, circling skulls',
           seal('magic_circle_d', 'D8A8FF', 2.4, life=1.5, spin=40),
           seal('magic_circle_c', 'F0D8FF', 2.8, life=1.5, spin=-60, y=FLOOR + .02),
           quad('rift', 'C890FF', 1.3, 1.0, height=2.0, y=.4, delay=.1, alpha=True),
           quad('rift_glow', 'B070FF', 1.3, 1.15, height=2.2, y=.4, delay=.1),
           layer('orbit', 'skull_wisp', 'E0C0FF', life=1.2, size=.45, radius=.9, spin=140, count=5, y=.2),
           emitter('ember', 'C8A0FF', 25, 1.0, .1, 1.5, .9, y=FLOOR), duration=1.6)
    effect('dark', 'Dark burst: imploding ring, abyss vortex, hit spark, shadow smoke, flung spirits and violet embers',
           ground_ring('A060FF', 2.4, .3, .5, y=-.5),
           quad('swirl', 'B080FF', .8, .4, 2.2, spin=-200), flash('E0C8FF', .4, 1.2, .15),
           smoke('2A1838', 10, 1.2, 1.0, .8, radius=.3),
           burst('skull_wisp', 'C8A8F0', 8, life=.8, size=.35, speed=2.0, delay=.05),
           embers('D8B8FF', 14, 2.5, .8, .12, gravity=-.2), duration=1.2)
    effect('holy', 'Holy strike: pillar from above, radiant wedge burst, sun seal, cross flash and feather fan',
           quad('beam', 'FFF6D0', .7, 1.0, height=4.0, y=1.2),
           quad('sunburst', 'FFF3C2', .6, .3, 2.6, delay=.05, spin=20),
           seal('magic_circle_f', 'FFF0C0', 1.8, life=1.0, end=2.1, spin=30),
           quad('cross', 'FFFFFF', .5, .6, height=1.2, y=.3, delay=.08),
           burst('feather', 'FFF2D0', 18, life=1.2, size=.22, speed=1.8, gravity=.15, delay=.1),
           emitter('ember', 'FFF8E0', 30, .8, .1, 2.0, .6, y=FLOOR), duration=1.3)
    effect('pierce', 'Arrow hit: light-arrow streak, small hit spark, tight shock ring, focused sparks',
           quad('arrow_streak', 'E0F4FF', .25, 2.2, height=.55),
           flash('FFFFFF', .3, 1.0, .14, delay=.03), shock('D8F0FF', .2, 1.2, .25, delay=.03),
           sparks('E8F8FF', 14, 4.0, .3, .25), duration=.8)
    effect('blunt', 'Heavy blow: hit spark, shock ring, floor ring, dust cloud, flying rock chips and sparks',
           flash('FFF0D8', .6, 1.8, .16), shock('FFE8C0', .4, 2.4, .35), ground_ring('E8D0A0', .3, 3.0, .5),
           smoke('C8B898', 14, 1.8, .9, .7, radius=.3, y=-.6, gravity=.1),
           burst('rock', 'A89878', 12, life=.8, size=.18, speed=3.5, gravity=1.2, y=-.4, alpha=True),
           sparks('FFE0B0', 12, 4.0, .3, .25), duration=1.1)
    effect('thunder', 'Lightning strike: two staggered bolts from above, white flash, floor ring, sparks and static',
           quad('lightning_sheet', 'F0F8FF', .55, 1.5, height=3.6, y=1.2, tiles=4),
           quad('lightning_sheet', 'C0DCFF', .5, 1.2, height=3.0, y=1.0, tiles=4, delay=.12, rotation=8),
           flash('F0F8FF', .6, 1.8, .16, delay=.02), quad('glow_hard', 'D0E8FF', .3, .5, 1.1),
           ground_ring('B0D8FF', .3, 2.6, .4),
           sparks('E8F4FF', 24, 5.0, .3, .3), embers('A8D0FF', 14, 1.5, .8, .12, delay=.1, gravity=0), duration=1.1)


def ultimates():
    """Hero ultimates, authored at their final (full-screen) size; GROW leaves them alone."""
    effect('ultimate_warrior', 'Heaven rend: focus lines, the sky tears open in a seam of light, a giant holy sword drops, a '
           'vertical heaven-splitting cut and X-slash, heaven pillar, triple shock and star storm',
           quad('speed_lines', 'FFFFFF', .6, 6.0, 4.0),
           seal('magic_circle_a', 'FFE6A0', 4.6, life=2.0, spin=40),
           quad('rift_glow', 'FFF0C0', 1.2, 1.4, 1.8, height=6.0, y=2.4, delay=.05),
           quad('sword', 'FFF0C0', 1.0, 2.4, height=5.0, y=1.8, delay=.12),
           quad('slash_arc', 'FFFFFF', .35, 5.0, 6.6, height=2.6, rotation=-72, delay=.42),
           quad('slash_cross', 'FFFFFF', .4, 2.2, 4.8, delay=.5), pillar('FFF4D0', 1.8, 8.0, .7, delay=.45),
           flash('FFF8E0', 1.6, 5.0, .22, delay=.5), shock('FFE0A0', .6, 5.0, .45, delay=.5),
           seal('shockwave', 'FFC060', .6, life=.7, end=8.0, spin=0, delay=.5), ground_ring('FFC060', .5, 6.0, .6, delay=.55),
           burst('star8', 'FFF2C0', 36, life=.9, size=.42, speed=6.0, delay=.5),
           embers('FFD080', 50, 3.0, 1.4, .15, delay=.55, gravity=-.3, radius=1.0), duration=2.2)
    effect('ultimate_mage', 'Meteor: grand arcane seals, a portal opens in the sky, a colossal burning meteor and a shower of '
           'smaller ones crash into the group - crater blast, flame columns, shockwaves, flying rock, ember storm and smoke',
           seal('magic_circle_e', 'FFD8F0', 6.4, life=2.4, spin=30),
           seal('magic_circle_c', 'FFFFFF', 7.4, life=2.4, spin=-50, y=FLOOR + .02),
           seal('magic_circle_a', 'FFE0C0', 4.0, life=1.4, spin=60, y=3.6),
           quad('meteor', 'FFE0C0', .5, 2.4, height=5.2, y=3.0, delay=.05),
           emitter('glow_hard', 'FFE0B0', .9, .45, 2.4, -9.0, .02, y=3.6, upright=True, delay=.05),
           emitter('meteor', 'FFD8B0', 10, .45, 1.4, -9.0, 3.2, y=3.6, upright=True, delay=.1),
           quad('explosion_sheet', 'FFD0A0', .9, 3.0, 6.4, tiles=4, delay=.45),
           flash('FFF0D0', 1.8, 6.0, .24, delay=.45),
           seal('shockwave', 'FFB070', .8, life=.8, end=10.0, spin=0, delay=.45),
           ground_ring('FF9050', .6, 9.0, .8, delay=.5),
           quad('flame_sheet', 'FFC080', 1.0, 3.0, height=5.0, y=1.4, tiles=4, delay=.55),
           emitter('explosion_sheet', 'FFE0B8', 8, .6, 2.4, .2, 3.2, y=-.2, tiles=4, upright=True, delay=.55),
           burst('rock', '806050', 30, life=1.1, size=.32, speed=6.0, gravity=1.4, y=-.5, radius=1.5, delay=.45, alpha=True),
           embers('FFC080', 80, 4.0, 1.4, .16, delay=.5, gravity=-.25, radius=1.5),
           smoke('302028', 16, 1.6, 1.6, 1.5, delay=.6, radius=2.4), duration=2.4)
    effect('ultimate_archer', 'Starfall volley: twin seals in the sky loose a storm of shooting stars and light arrows over the '
           'group, star glints burst on the ground, shock ring and motes',
           seal('magic_circle_b', 'D8F0FF', 4.6, life=2.0, spin=60, y=3.4),
           seal('magic_circle_c', 'FFFFFF', 5.2, life=2.0, spin=-80, y=3.42),
           emitter('meteor', 'E0F4FF', 16, .45, 1.4, -10.0, 3.4, y=3.4, upright=True, delay=.15),
           emitter('arrow_rain', 'E8F8FF', 100, .45, 1.5, -11.0, 3.4, y=3.2, upright=True, delay=.2),
           emitter('star8', 'F0FAFF', 40, .3, .7, .3, 3.4, y=FLOOR, delay=.5),
           flash('F0F8FF', 1.4, 4.6, .22, delay=.5),
           ground_ring('C8ECFF', .6, 8.0, .7, delay=.5), seal('shockwave', 'D8F0FF', .6, life=.6, end=8.0, spin=0, delay=.55),
           emitter('ember', 'D8F0FF', 50, .9, .12, 1.4, 3.4, y=FLOOR, delay=.5), duration=2.2)
    effect('ultimate_cleric', 'Seraph hymn: sun seal, heaven pillar, great seraph wings and halo, hymn glyphs and notes circle the '
           'party, radiant burst, feather fall and rising light',
           seal('magic_circle_f', 'FFF4D0', 6.4, life=2.4, spin=25),
           pillar('FFF8E0', 2.6, 8.0, 1.8, delay=.1),
           quad('wings', 'FFFFF0', 1.8, 4.6, 5.8, y=1.2, delay=.25),
           quad('halo', 'FFFFFF', 1.6, 1.6, horizontal=True, y=2.2, delay=.35, spin=50),
           layer('orbit', 'hymn', 'FFF8E0', life=1.8, size=.6, radius=2.8, spin=70, count=8, y=1.0, delay=.2),
           layer('orbit', 'note', 'FFF4D0', life=1.6, size=.5, radius=1.8, spin=-90, count=6, y=.3, delay=.3, alpha=True),
           quad('sunburst', 'FFF2C0', .8, 1.0, 5.6, y=.6, delay=.4, spin=15), flash('FFFFFF', 1.4, 4.4, .22, delay=.4),
           emitter('feather', 'FFF6E0', 26, 1.6, .3, -1.0, 3.2, y=3.2, gravity=.02),
           emitter('ember', 'FFF6D0', 60, 1.0, .13, 2.6, 3.2, y=FLOOR), duration=2.4)


def jobs():
    """Signature effects for the advanced / top jobs of the job tree. Data only: nothing plays them yet
    (a job-skill presentation entry or BattleView hook has to reference `job_<id>`)."""
    # warrior -> knight -> paladin
    effect('job_knight', 'Knight: azure guard seal and hex bulwark, then a sweeping shield-cleave and blue shock',
           seal('magic_circle_b', '9CC8FF', 2.4, life=1.4, spin=40),
           layer('sphere', 'hex', 'A8D4FF', life=1.0, size=1.8, endSize=2.0, delay=.05),
           layer('arc', 'slash_strip', 'E0F0FF', life=.25, size=1.4, endSize=2.2, rotation=200, delay=.3),
           quad('slash_arc', 'C8E4FF', .3, 2.2, 2.6, height=1.1, rotation=-25, delay=.35),
           flash('FFFFFF', .5, 1.6, .16, delay=.38), shock('B8DCFF', .4, 2.6, .4, delay=.4),
           sparks('D8ECFF', 18, 4.5, .35, .28, delay=.38), embers('A8D0FF', 12, 1.0, 1.0, delay=.45, gravity=-.2),
           duration=1.6)
    effect('job_paladin', 'Paladin: sun seal, heaven pillar with a descending holy sword, unfolding wings, radiant burst',
           seal('magic_circle_f', 'FFE8A8', 3.0, life=1.9, spin=30),
           quad('beam', 'FFF4C8', 1.4, 1.3, height=5.0, y=1.6, delay=.1),
           quad('sword', 'FFF8E0', 1.2, 1.4, height=2.8, y=.9, delay=.2),
           quad('wings', 'FFF0C8', 1.4, 3.2, 3.6, y=.7, delay=.35),
           quad('sunburst', 'FFE8A0', .6, .5, 3.0, y=.3, delay=.55, spin=20),
           flash('FFFFFF', .6, 2.0, .18, delay=.55),
           burst('feather', 'FFF6E0', 22, life=1.4, size=.24, speed=2.2, gravity=.1, delay=.55),
           emitter('ember', 'FFF0C0', 35, 1.0, .12, 2.4, .8, y=FLOOR), duration=2)
    # warrior -> berserker -> warlord
    effect('job_berserker', 'Berserker: red focus lines, two frenzied claw rakes, X-slash, blood spray and rage embers',
           quad('speed_lines', 'FF6060', .4, 3.6, 2.6),
           quad('claw', 'FFD0D0', .32, 1.8, 2.4, rotation=15, delay=.15),
           quad('claw', 'FFB0B0', .32, 1.8, 2.4, rotation=-160, delay=.28),
           quad('slash_cross', 'FF8080', .3, 1.2, 2.4, delay=.4), flash('FFE0E0', .6, 1.8, .18, delay=.42),
           burst('droplet', 'FF4050', 16, life=.7, size=.16, speed=3.5, gravity=1.0, delay=.42, alpha=True),
           sparks('FFA0A0', 20, 5.0, .35, .3, delay=.42),
           emitter('ember', 'FF6050', 25, .8, .12, 1.5, .6, y=-.6), duration=1.6)
    effect('job_warlord', 'Warlord: crimson war sigil, ground-shattering explosion, double crimson shockwave, rocks and embers',
           seal('magic_circle_d', 'FF6040', 3.2, life=1.8, spin=-30),
           quad('speed_lines', 'FFB080', .45, 4.0, 3.0),
           quad('explosion_sheet', 'FF9060', .8, 1.8, 3.0, tiles=4, delay=.35),
           flash('FFE0C0', .8, 2.6, .2, delay=.35),
           seal('shockwave', 'FF7050', .5, life=.6, end=4.4, spin=0, delay=.35),
           shock('FFB090', .5, 3.4, .45, delay=.4), ground_ring('FF4030', .5, 4.8, .7, delay=.4),
           burst('rock', '806050', 16, life=.9, size=.22, speed=4.0, gravity=1.3, y=-.5, delay=.35, alpha=True),
           smoke('503030', 10, 1.6, 1.2, 1.0, delay=.4, radius=.5, y=-.5),
           embers('FF8040', 40, 3.0, 1.4, .14, delay=.4, gravity=-.25), duration=2.2)
    # mage -> elementalist -> archmage
    effect('job_elementalist', 'Elementalist: fire and ice spirits orbit a rune circle with sparks, then converge in a prismatic blast',
           seal('magic_circle_a', 'C8E0FF', 2.6, life=1.6, spin=50),
           layer('orbit', 'flame_sheet', 'FF9050', life=1.0, size=.55, radius=1.0, spin=160, count=2, y=.2, tiles=4),
           layer('orbit', 'crystal', 'A0E0FF', life=1.0, size=.5, radius=1.0, spin=-160, count=2, y=.2),
           layer('orbit', 'star8', 'FFF0A0', life=1.0, size=.35, radius=.7, spin=100, count=3, y=.6),
           flash('FFFFFF', .6, 2.2, .2, delay=.9),
           quad('explosion_sheet', 'D0C0FF', .7, 1.0, 2.4, tiles=4, delay=.9),
           sparks('C0E0FF', 18, 5.0, .4, .3, delay=.9), embers('FFB080', 16, 2.4, 1.0, delay=.9),
           burst('ice_shard', 'A0E0FF', 10, life=.7, size=.28, speed=3.0, gravity=.5, delay=.9), duration=2)
    effect('job_archmage', 'Archmage: three stacked arcane seals (floor, air, sky), a meteor streaks down, grand explosion',
           seal('magic_circle_e', 'D8C0FF', 3.4, life=2.2, spin=25),
           seal('magic_circle_c', 'FFFFFF', 3.9, life=2.2, spin=-40, y=FLOOR + .02),
           seal('magic_circle_a', 'E8D8FF', 2.0, life=1.8, spin=-60, y=1.4, delay=.1),
           seal('magic_circle_b', 'F0E0FF', 1.4, life=1.6, spin=80, y=3.0, delay=.2),
           quad('meteor', 'FFD0A0', .4, 1.4, height=3.0, y=1.9, delay=.6),
           emitter('glow_hard', 'FFE0B0', .9, .35, 1.0, -8.0, .02, y=3.0, upright=True, delay=.6),
           quad('explosion_sheet', 'FFB070', .8, 2.0, 3.4, tiles=4, delay=.95),
           flash('FFF0D0', .8, 2.8, .2, delay=.95),
           seal('shockwave', 'FFC090', .5, life=.6, end=4.2, spin=0, delay=.95),
           ground_ring('FFB070', .5, 4.4, .7, delay=1.0),
           embers('FFC080', 40, 3.0, 1.2, .14, delay=1.0, gravity=-.25),
           smoke('2A1C30', 10, 1.4, 1.3, 1.0, delay=1.05, radius=.5), duration=2.4)
    # mage -> warlock -> abyssal
    effect('job_warlock', 'Warlock: violet curse sigil, tightening vortex, circling skull wisps, shadow smoke, curse pop',
           seal('magic_circle_d', 'B070FF', 2.6, life=1.6, spin=-40),
           quad('swirl', 'C080FF', 1.2, .6, 2.4, spin=-160, y=.2, delay=.1),
           layer('orbit', 'skull_wisp', 'D0A8FF', life=1.3, size=.45, radius=.9, spin=-140, count=4, y=.3),
           smoke('2A1640', 12, .9, 1.3, 1.0, delay=.2, radius=.5),
           flash('E8D0FF', .5, 1.8, .2, delay=.7), embers('C890FF', 24, 2.6, 1.0, .12, delay=.7, gravity=-.2),
           duration=1.8)
    effect('job_abyssal', 'Abyssal: cyan-violet twin sigils, a void rift tears open with a glowing seam, vortex, abyss smoke',
           seal('magic_circle_d', '60E0FF', 3.2, life=2.0, spin=30),
           seal('magic_circle_c', 'B080FF', 3.7, life=2.0, spin=-50, y=FLOOR + .02),
           quad('swirl', '9060FF', 1.4, 1.0, 3.0, spin=-120, y=.5, delay=.3),
           quad('rift', 'B8F4FF', 1.6, 1.3, 1.5, height=2.8, y=.6, delay=.15, alpha=True),
           quad('rift_glow', '60E8FF', 1.6, 1.5, 1.7, height=3.0, y=.6, delay=.15),
           emitter('smoke_sheet', '180C28', 8, 1.2, .8, 1.0, .8, tiles=4, alpha=True, y=FLOOR, delay=.2),
           ground_ring('8040FF', 4.0, .5, .6, delay=.5),
           flash('D0F8FF', .6, 2.0, .2, delay=.6), embers('70F0FF', 30, 3.0, 1.2, .12, delay=.6, gravity=-.3),
           duration=2.2)
    # archer -> sniper -> divine_archer
    effect('job_sniper', 'Sniper: lock-on reticle and ring converge, then a piercing light arrow, focus lines and sharp burst',
           quad('magic_circle_c', 'D0F0FF', .6, 1.8, 1.0, spin=120),
           quad('ring', 'FFFFFF', .5, 2.4, .6),
           quad('arrow_streak', 'E8F8FF', .25, 3.6, height=.6, delay=.5),
           quad('speed_lines', 'C0E8FF', .3, 3.0, 2.4, delay=.5),
           flash('FFFFFF', .4, 1.6, .16, delay=.55), shock('C8ECFF', .3, 2.4, .35, delay=.55),
           sparks('E0F6FF', 20, 6.0, .35, .3, delay=.55), duration=1.4)
    effect('job_divine_archer', 'Divine Archer: golden sun seal opens in the sky and rains golden arrows; sparkling impacts',
           seal('magic_circle_f', 'FFE8A0', 3.2, life=2.0, spin=40, y=2.9),
           seal('sunburst', 'FFE8A0', 2.0, life=1.6, spin=60, y=2.92),
           seal('magic_circle_b', 'FFE0A0', 3.0, life=1.8, spin=-30),
           emitter('arrow_rain', 'FFE8B0', 65, .55, 1.4, -8.5, 1.4, y=2.7, upright=True, delay=.2),
           emitter('star4', 'FFF4D0', 35, .25, .5, .2, 1.4, y=FLOOR, delay=.5),
           ground_ring('FFD070', .5, 3.6, .7, delay=.55),
           emitter('ember', 'FFE8B0', 30, 1.0, .12, 1.5, 1.2, y=FLOOR, delay=.5), duration=2.2)
    # archer -> ranger -> shadow_stalker
    effect('job_ranger', 'Ranger: leaf storm whirls around a green seal, two wind cuts and a burst of leaves',
           seal('magic_circle_b', 'A8F0B0', 2.4, life=1.4, spin=60),
           layer('orbit', 'leaf', 'C8FFC0', life=1.2, size=.3, radius=1.0, spin=260, count=8, y=-.2),
           layer('orbit', 'leaf', 'B0F0A0', life=1.2, size=.26, radius=.7, spin=-300, count=6, y=.5),
           layer('arc', 'slash_strip', 'D8FFD8', life=.3, size=1.6, endSize=2.2, rotation=30, delay=.5),
           layer('arc', 'slash_strip', 'C0FFC8', life=.3, size=1.4, endSize=2.0, rotation=210, delay=.62),
           flash('F0FFE8', .4, 1.4, .16, delay=.55),
           burst('leaf', 'B8F8A8', 18, life=1.0, size=.22, speed=3.0, gravity=.2, delay=.55), duration=1.6)
    effect('job_shadow_stalker', 'Shadow Stalker: vanishes in shadow smoke, three violet blade arcs, X-slash, dark burst',
           smoke('201030', 10, .6, 1.0, .9, radius=.5),
           layer('arc', 'slash_strip', 'C8A0FF', life=.22, size=1.9, endSize=2.6, rotation=20, delay=.15),
           layer('arc', 'slash_strip', 'E0C8FF', life=.22, size=1.9, endSize=2.6, rotation=160, delay=.25),
           layer('arc', 'slash_strip', 'B080FF', life=.22, size=2.1, endSize=2.8, rotation=280, delay=.35),
           quad('slash_cross', 'D8B8FF', .3, 1.4, 2.6, delay=.45), flash('F0E0FF', .5, 1.6, .16, delay=.47),
           sparks('C090FF', 20, 5.0, .3, .28, delay=.47), smoke('180828', 8, 1.6, .9, .7, delay=.5), duration=1.5)
    # cleric -> priest -> saint
    effect('job_priest', 'Priest: blessing seal, soft light pillar, rising crosses and petals, warm bloom and sparkles',
           seal('magic_circle_f', 'D8FFE0', 2.4, life=1.6, spin=30),
           quad('beam', 'E0FFE8', 1.2, 1.2, height=3.6, y=1.0, delay=.1),
           emitter('plus', 'E8FFF0', 16, 1.0, .24, 1.4, .7, y=-.7),
           emitter('petal', 'FFE0F0', 10, 1.4, .16, 1.0, .8, y=-.7),
           quad('glow', 'E8FFF0', .6, .6, 1.4, y=.2, delay=.3),
           burst('star4', 'FFFFFF', 10, life=.8, size=.25, speed=1.5, delay=.4), duration=1.8)
    effect('job_saint', 'Saint: great halo above, heaven pillar, rain of healing light and crosses, radiant bloom',
           quad('halo', 'FFF8D8', 2.0, 1.4, horizontal=True, y=2.3, spin=40),
           seal('magic_circle_f', 'FFF2C8', 3.4, life=2.0, spin=-30),
           quad('beam', 'FFF8E0', 1.6, 1.5, height=5.0, y=1.6, delay=.1),
           emitter('light_streak', 'E8FFF0', 40, .55, 1.0, -7.5, 1.3, y=2.4, upright=True, delay=.15),
           emitter('plus', 'D8FFE8', 20, .6, .25, -3.0, 1.3, y=2.2, upright=True, delay=.2),
           quad('sunburst', 'FFF4D0', .8, .5, 3.2, y=.4, delay=.6, spin=15),
           emitter('ember', 'F0FFF4', 30, 1.0, .12, 1.5, 1.2, y=FLOOR, delay=.4), duration=2.2)
    # cleric -> exorcist -> inquisitor
    effect('job_exorcist', 'Exorcist: upright holy seal spins open, cross flash, spirits flung out, holy shock and stars',
           quad('magic_circle_f', 'FFF0C0', 1.2, .6, 2.2, spin=90, y=.3),
           quad('cross', 'FFFFFF', .8, .6, height=1.2, y=.3, delay=.2),
           burst('skull_wisp', 'E8E0FF', 6, life=.9, size=.4, speed=2.5, gravity=-.3, delay=.4),
           flash('FFF8E0', .5, 1.8, .18, delay=.45), shock('FFE8B0', .4, 2.6, .4, delay=.45),
           burst('star4', 'FFF4C0', 16, life=.6, size=.28, speed=3.0, delay=.45), duration=1.6)
    effect('job_inquisitor', 'Inquisitor: crimson sigil, judgment pillar and giant crimson cross impale the target, red shock',
           seal('magic_circle_d', 'FF5060', 3.2, life=2.0, spin=30),
           quad('speed_lines', 'FF9090', .4, 4.0, 3.0),
           quad('beam', 'FF4050', .9, 1.4, height=5.0, y=1.6, delay=.25),
           quad('cross', 'FF6070', 1.2, 1.4, height=2.8, y=.9, delay=.3),
           flash('FFE0E0', .8, 2.4, .2, delay=.35),
           seal('shockwave', 'FF6060', .5, life=.6, end=4.0, spin=0, delay=.35),
           embers('FF5050', 34, 3.0, 1.2, .13, delay=.35, gravity=-.3),
           smoke('401018', 8, 1.2, 1.0, .9, delay=.4, y=-.4), duration=2)


def skill_effects():
    """Skill expansion v2. `enchant`/`aura`/`warcry` play on the caster; `blade_*` are element weapon-art impacts;
    `area_*`, `aegis`, `drain`, `sleep_mist`, `flash_burst` and `ultimate_warrior2` are PresentationDef.area_vfx keys,
    played ONCE at the centre of the whole target group (origin 0.9 m above the floor) and authored ~5.5 m wide so a
    group spell reads as one big field event; per-hit impacts still play on every target. Near-white palettes so the
    skill's light colour tints them (same convention as the shared battle keys)."""
    # --- caster-side wind-ups ------------------------------------------------------------------------
    effect('enchant', 'Weapon enchant on the caster: spinning seal, body glow, orbiting glints and rising element embers',
           seal('magic_circle_a', 'FFFFFF', 1.3, life=1.0, spin=90), quad('glow', 'FFFFFF', .8, .6, 1.2, y=.1),
           layer('orbit', 'star4', 'FFFFFF', life=.9, size=.2, radius=.6, spin=300, count=3, y=.1),
           emitter('ember', 'FFFFFF', 30, .6, .1, 2.2, .4, y=-.6), duration=1.0)
    effect('warcry', 'Battle shout: radial focus lines, double shockwave, anger mark, rising aura flames and embers',
           quad('speed_lines', 'FFFFFF', .5, 2.0, 3.6), shock('FFFFFF', .4, 2.8, .4, delay=.05),
           shock('FFFFFF', .3, 2.2, .35, delay=.2), ground_ring('FFFFFF', .4, 3.0, .5),
           quad('anger', 'FF6784', .7, .8, 1.2, y=.9, delay=.1, alpha=True),
           emitter('flame_sheet', 'FFFFFF', 14, .6, .6, 2.0, .4, y=FLOOR, tiles=4, upright=True),
           emitter('ember', 'FFFFFF', 30, .8, .1, 2.6, .5, y=FLOOR), duration=1.2)
    effect('aura', 'Power-up aura: spinning seal, aura column and flames, orbiting chevrons, rising motes, finishing glint',
           seal('magic_circle_e', 'FFFFFF', 1.7, life=1.2, spin=80), quad('beam', 'FFFFFF', 1.0, 1.1, height=2.6, y=.4),
           emitter('flame_sheet', 'FFFFFF', 12, .7, .7, 1.6, .35, y=FLOOR, tiles=4, upright=True),
           layer('orbit', 'arrow_up', 'FFFFFF', life=1.0, size=.3, radius=.75, spin=160, count=3),
           emitter('ember', 'FFFFFF', 26, .8, .1, 2.4, .5, y=FLOOR),
           glint('FFFFFF', .35, 1.4, .25, delay=.5, y=.7, texture='star8'), duration=1.3)

    # --- element weapon arts (per-hit impact) --------------------------------------------------------
    def blade(key, description, *extra):
        effect(key, description,
               layer('arc', 'slash_strip', 'FFFFFF', life=.22, size=1.4, endSize=2.2, rotation=200),
               quad('slash_arc', 'FFFFFF', .3, 2.4, 3.0, height=1.2, rotation=-28, delay=.03),
               flash('FFFFFF', .5, 1.7, .15, delay=.03), *extra, duration=1.2)
    blade('blade_fire', 'Flame blade: white crescent cut that bursts into a cel explosion, ember spray and smoke',
          quad('explosion_sheet', 'FFD9A0', .6, 1.2, 2.2, tiles=4, delay=.05), embers('FFD090', 26, 3.0, .8, .14),
          smoke('3A2A30', 5, .8, .9, .7, delay=.15))
    blade('blade_ice', 'Frost blade: crescent cut, ice crystal erupts from the wound, shard spray and frost mist',
          quad('crystal', 'E0F8FF', .7, .6, 1.8, y=-.2, delay=.04),
          burst('ice_shard', 'C8F0FF', 16, life=.7, size=.3, speed=3.5, gravity=.6), smoke('E0F4FF', 4, .5, .9, .7, delay=.1))
    blade('blade_thunder', 'Thunder blade: crescent cut with a bolt striking the blade, crackling sparks, floor ring',
          quad('lightning_sheet', 'F0F8FF', .45, 1.4, height=3.2, y=1.0, tiles=4), sparks('F0FAFF', 24, 5.0, .3, .28),
          ground_ring('FFFFFF', .3, 2.4, .4))
    blade('blade_holy', 'Holy blade: crescent cut, radiant cross and sunburst, feather fan',
          quad('cross', 'FFFFFF', .5, .7, height=1.4, y=.3, delay=.05), quad('sunburst', 'FFF6D8', .5, .3, 2.4, delay=.05, spin=20),
          burst('feather', 'FFF8E8', 12, life=1.0, size=.22, speed=1.8, gravity=.15, delay=.08))

    # --- group / field spells (area_vfx) ----------------------------------------------------------------
    effect('area_fire', 'Hellfire field: wide rune seal and scorch, flame columns and explosions erupting across the group, '
           'giant hit flash and shock ring, ember storm, rolling smoke',
           seal('magic_circle_a', 'FFE0C0', 5.5, life=1.8, spin=25),
           seal('glow_hard', 'FFB070', 4.0, life=1.4, spin=0, end=6.0, delay=.1),
           emitter('flame_sheet', 'FFD0A0', 22, .9, 1.8, .8, 2.6, y=FLOOR + .6, tiles=4, upright=True, delay=.1),
           emitter('explosion_sheet', 'FFE0B8', 6, .7, 2.0, .2, 2.4, y=-.2, tiles=4, upright=True, delay=.15),
           flash('FFF0D0', 1.2, 4.0, .2, delay=.15), seal('shockwave', 'FFB070', .5, life=.6, end=6.5, spin=0, delay=.15),
           emitter('ember', 'FFD090', 60, 1.0, .13, 3.0, 2.8, y=FLOOR, delay=.1),
           smoke('302028', 12, 1.2, 1.4, 1.3, delay=.4, radius=1.6), duration=1.8)
    effect('area_ice', 'Glacier field: snowflake seal, ice crystals erupting across the group, falling snow, frost flash, '
           'shard spray and freezing mist',
           seal('snowflake', 'E8FCFF', 4.5, life=1.8, spin=30, end=6.0),
           seal('magic_circle_c', 'D8F4FF', 6.0, life=1.8, spin=-40, y=FLOOR + .02),
           emitter('crystal', 'E0F8FF', 16, .9, 1.4, .4, 2.5, y=FLOOR + .4, upright=True, delay=.15),
           emitter('snowflake', 'F0FCFF', 40, 1.2, .2, -2.5, 3.0, y=2.6),
           flash('E8FCFF', 1.0, 3.6, .2, delay=.2), seal('shockwave', 'C8F0FF', .5, life=.6, end=6.0, spin=0, delay=.2),
           burst('ice_shard', 'C8F0FF', 30, life=.9, size=.35, speed=4.5, gravity=.8, radius=1.0, delay=.2),
           smoke('E0F4FF', 10, 1.0, 1.2, .8, radius=2.0, delay=.3), duration=1.8)
    effect('area_thunder', 'Thunderstorm: storm cloud overhead, bolts raining down across the group, white flash, '
           'wide floor ring, crackling sparks',
           smoke('2A2A40', 10, .3, 1.6, 1.2, radius=2.2, y=2.8, gravity=0),
           seal('magic_circle_d', 'E8F0FF', 5.0, life=1.6, spin=40),
           quad('lightning_sheet', 'F0F8FF', .5, 2.0, height=4.4, y=1.3, tiles=4, delay=.15),
           emitter('lightning_sheet', 'F0F8FF', 20, .4, 2.6, 0, 2.4, y=.9, tiles=4, upright=True, delay=.15),
           flash('F0F8FF', 1.0, 3.6, .18, delay=.2), ground_ring('D0E8FF', .5, 6.0, .5, delay=.2),
           emitter('spark', 'F0FAFF', 60, .3, .25, 3.0, 2.6, y=FLOOR, delay=.15), duration=1.7)
    effect('area_holy', 'Divine judgment: floor and sky sun seals, light lances raining down, light pillars, '
           'giant sunburst, feather storm',
           seal('magic_circle_f', 'FFF4D0', 5.6, life=1.9, spin=20),
           seal('magic_circle_c', 'FFFFFF', 6.2, life=1.9, spin=-35, y=FLOOR + .02),
           seal('magic_circle_f', 'FFF0C0', 3.0, life=1.6, spin=-30, y=3.2, delay=.05),
           emitter('light_streak', 'FFF8E0', 40, .45, 1.2, -8.0, 2.6, y=3.0, upright=True, delay=.15),
           emitter('beam', 'FFF6D8', 6, .6, 2.4, 0, 2.3, y=.6, upright=True, delay=.2),
           quad('sunburst', 'FFF3C2', .7, 1.0, 5.0, delay=.3, spin=15), flash('FFFFFF', 1.0, 3.4, .2, delay=.3),
           burst('feather', 'FFF2D0', 30, life=1.4, size=.25, speed=2.5, gravity=.12, radius=1.5, delay=.3),
           emitter('ember', 'FFF8E0', 50, .9, .11, 2.4, 2.8, y=FLOOR), duration=2.0)
    effect('area_dark', 'Void field: abyss sigil, imploding ring, ground vortex and rising vortex, shadow smoke, '
           'flung spirits, violet ember storm',
           seal('magic_circle_d', 'E0C8FF', 5.6, life=1.8, spin=-30), ground_ring('C090FF', 6.0, .6, .6, y=FLOOR + .05),
           quad('swirl', 'C8A0FF', 1.2, 1.0, 5.0, horizontal=True, y=FLOOR + .1, spin=-160),
           quad('swirl', 'B080FF', .9, .6, 3.4, spin=-220, y=.4, delay=.2),
           emitter('smoke_sheet', '2A1838', 14, 1.2, 1.2, 1.0, 2.6, y=FLOOR, tiles=4, alpha=True),
           burst('skull_wisp', 'D8B8F0', 14, life=1.1, size=.45, speed=2.5, radius=1.6, delay=.25),
           flash('E8D0FF', .9, 3.2, .2, delay=.35), embers('D8B8FF', 40, 3.0, 1.0, .12, delay=.35, radius=2.0), duration=1.8)
    effect('area_quake', 'Earthquake: giant ground shockwave and floor ring, focus lines, flash, rock eruption and dust '
           'across the group, spark spray',
           seal('shockwave', 'FFE8C0', .6, life=.7, end=6.5, spin=0, delay=.05), ground_ring('E8D0A0', .5, 6.5, .6),
           quad('speed_lines', 'FFFFFF', .4, 3.0, 5.0), flash('FFF0D8', 1.0, 3.0, .18),
           quad('explosion_sheet', 'FFE8C8', .7, 1.8, 3.4, tiles=4, y=-.2),
           emitter('rock', 'A89878', 50, .9, .42, 5.0, 2.6, y=FLOOR, gravity=1.4, alpha=True),
           emitter('smoke_sheet', 'C8B898', 16, 1.0, 1.3, 1.6, 2.6, y=FLOOR + .2, tiles=4, alpha=True),
           sparks('FFE0B0', 30, 6.0, .4, .3, radius=1.5), duration=1.6)
    effect('area_slash', 'Sweeping cleave: three huge crescents sweep across the group, spark spray, wide floor ring',
           layer('arc', 'slash_strip', 'FFFFFF', life=.25, size=4.0, endSize=5.5, rotation=190),
           layer('arc', 'slash_strip', 'FFFFFF', life=.25, size=4.2, endSize=5.8, rotation=10, delay=.12),
           quad('slash_arc', 'FFFFFF', .3, 4.8, 6.0, height=2.0, rotation=-18, delay=.06),
           flash('FFFFFF', .8, 3.2, .16, delay=.05),
           burst('spark', 'F0FFFF', 30, life=.4, size=.3, speed=6.0, radius=1.2, delay=.1),
           seal('ring', 'FFFFFF', 1.0, life=.6, end=6.0, spin=0), duration=1.2)
    effect('area_wind', 'Whirlwind: wind funnel spins up in the middle of the group, crossing gale crescents, '
           'swirling leaves and wind glints, wide floor ring',
           quad('tornado', 'F0FFF8', 1.2, 2.2, 2.6, height=4.0, y=.9),
           quad('tornado', 'D8FFF0', 1.0, 1.6, 2.2, height=3.0, y=.6, delay=.15, rotation=6),
           layer('arc', 'slash_strip', 'FFFFFF', life=.25, size=4.0, endSize=5.5, rotation=190, delay=.1),
           layer('arc', 'slash_strip', 'FFFFFF', life=.25, size=3.4, endSize=5.0, rotation=20, delay=.25),
           layer('orbit', 'leaf', 'E0FFE0', life=1.2, size=.3, radius=2.0, spin=320, count=8, y=.2),
           burst('spark', 'F0FFFF', 26, life=.45, size=.3, speed=6.0, radius=1.2, delay=.1),
           seal('ring', 'FFFFFF', 1.0, life=.6, end=6.0, spin=0), duration=1.5)
    effect('area_arrows', 'Arrow storm: seal opens in the sky, a dense rain of light arrows over the whole group, '
           'ground glints, wide ring and motes',
           seal('magic_circle_b', 'E8F8FF', 3.2, life=1.4, spin=60, y=2.9),
           emitter('arrow_rain', 'F0FAFF', 70, .5, 1.2, -9.0, 2.6, y=2.7, upright=True, delay=.1),
           emitter('star4', 'FFFFFF', 30, .25, .4, .3, 2.6, y=FLOOR, delay=.4),
           ground_ring('FFFFFF', .5, 5.6, .6, delay=.4), emitter('ember', 'F0F8FF', 30, .9, .1, 1.0, 2.6, y=FLOOR, delay=.4),
           duration=1.5)
    effect('area_poison', 'Toxic miasma: curse seal, rolling cel smoke over the group, rising bubbles and specks',
           seal('magic_circle_d', 'E8FFE0', 5.0, life=1.6, spin=30),
           emitter('smoke_sheet', 'E0FFD0', 14, 1.4, 1.4, .8, 2.6, y=FLOOR + .2, tiles=4, alpha=True),
           smoke('C8E8B8', 10, 1.2, 1.2, 1.0, radius=1.8),
           emitter('bubble', 'F0FFE8', 30, 1.0, .22, 1.2, 2.6, y=FLOOR), duration=1.8)
    effect('area_heal', 'Healing rain: wide leaf seal and ring, rain of soft light, rising crosses and leaves, bloom, sparkles',
           seal('magic_circle_b', 'E0FFE8', 5.2, life=1.8, spin=30), ground_ring('E8FFF0', .5, 5.6, .6),
           emitter('light_streak', 'E8FFF0', 30, .5, 1.0, -6.0, 2.8, y=2.8, upright=True, delay=.1),
           emitter('plus', 'E8FFF0', 24, 1.0, .3, 1.5, 2.6, y=FLOOR + .1),
           emitter('leaf', 'D0FFD8', 14, 1.2, .22, 1.2, 2.6, y=FLOOR),
           seal('glow', 'E0FFE8', 2.0, life=1.0, spin=0, end=5.0, delay=.25),
           embers('F0FFF4', 40, 1.4, 1.1, radius=2.0, delay=.2), duration=1.9)
    effect('area_buff', 'Party blessing: wide golden seal and ring, chevrons circling the party, light pillars, '
           'ember fountain, finishing glint',
           seal('magic_circle_e', 'FFF2D0', 5.0, life=1.6, spin=40), ground_ring('FFFFFF', .5, 5.6, .6),
           layer('orbit', 'arrow_up', 'FFF0C0', life=1.2, size=.4, radius=2.4, spin=90, count=8, y=-.2),
           emitter('ember', 'FFF4D0', 60, .9, .12, 2.8, 2.6, y=FLOOR),
           emitter('beam', 'FFE8B0', 5, .7, 1.6, 0, 2.2, y=.4, upright=True),
           glint('FFFFFF', .6, 2.4, .3, delay=.5, y=.8, texture='star8'), duration=1.5)
    effect('area_debuff', 'Curse field: abyss seal, circling skull spirits and sinking chevrons over the group, '
           'creeping smoke, falling motes',
           seal('magic_circle_d', 'E8D0FF', 5.0, life=1.6, spin=-40),
           layer('orbit', 'skull_wisp', 'E0C8FF', life=1.4, size=.5, radius=2.2, spin=-120, count=6, y=.4),
           layer('orbit', 'arrow_down', 'E0C8FF', life=1.2, size=.4, radius=1.5, spin=90, count=5, y=.9),
           emitter('smoke_sheet', '403050', 10, 1.2, 1.0, .6, 2.6, y=FLOOR, tiles=4, alpha=True),
           emitter('ember', 'D0B0FF', 30, .9, .1, -1.5, 2.6, y=1.6), duration=1.6)
    effect('area_revive', 'Mass resurrection: double sun seal, colossal heaven pillar, unfolding great wings and halo, '
           'feather fall, rising light, white flash',
           seal('magic_circle_f', 'FFF2C8', 5.6, life=2.2, spin=20),
           seal('magic_circle_c', 'FFFFFF', 6.2, life=2.2, spin=-35, y=FLOOR + .02),
           quad('beam', 'FFF6D8', 1.8, 4.0, height=6.0, y=1.8, delay=.1),
           quad('wings', 'FFF4D2', 1.6, 3.6, 4.6, y=.8, delay=.3),
           quad('halo', 'FFFFFF', 1.6, 1.6, horizontal=True, y=2.4, delay=.4, spin=50),
           emitter('feather', 'FFF8E8', 20, 1.6, .28, -1.0, 2.8, y=3.0, gravity=.02),
           emitter('ember', 'FFF0C0', 50, 1.1, .12, 2.4, 2.8, y=FLOOR), flash('FFFFFF', 1.2, 3.6, .22, delay=.5),
           duration=2.4)
    effect('aegis', 'Aegis: a huge hexagonal dome closes over the party, blue seal and ring, glint, chips of light, motes',
           layer('sphere', 'hex', 'B8E0FF', life=1.6, size=5.6, endSize=6.0, delay=.2, spin=15),
           seal('magic_circle_b', 'C8E8FF', 5.4, life=1.8, spin=30), ground_ring('E0F4FF', .5, 6.0, .6),
           glint('FFFFFF', .8, 3.0, .3, delay=.25, texture='star8'),
           burst('square', 'D0EEFF', 30, life=.8, size=.2, speed=3.0, radius=2.0, delay=.2),
           emitter('dot', 'D8F2FF', 30, 1.2, .08, 1.0, 2.6, y=FLOOR), duration=1.9)
    effect('drain', 'Life drain: closing ring and shrinking vortex, motes and spirits sucked into the target, pop, smoke',
           ground_ring('FF80C0', 2.2, .3, .6, y=-.5), quad('swirl', 'FF90D0', 1.0, 1.6, .4, spin=-260),
           burst('dot', 'FFB0E0', 30, life=.7, size=.14, speed=-3.0, radius=1.6, delay=.1),
           burst('skull_wisp', 'F0C0E0', 6, life=.8, size=.35, speed=-1.8, radius=1.4, delay=.05),
           flash('FFE0F0', .4, 1.4, .15, delay=.5), smoke('301828', 8, 1.0, 1.0, .7, delay=.4), duration=1.3)
    effect('sleep_mist', 'Sleep mist: dreamy seal, drifting pastel mist over the group, circling Zzz, bubbles, soft stars',
           seal('magic_circle_b', 'D8E0FF', 4.6, life=1.6, spin=20),
           emitter('smoke_sheet', 'D8DCFF', 10, 1.4, 1.3, .4, 2.4, y=FLOOR + .3, tiles=4, alpha=True),
           layer('orbit', 'zzz', 'C8D0FF', life=1.4, size=.5, radius=1.8, spin=40, count=5, y=.8, alpha=True),
           emitter('bubble', 'E8ECFF', 20, 1.2, .2, .8, 2.4, y=FLOOR),
           emitter('star4', 'E0E8FF', 14, .6, .25, .6, 2.4, y=.5), duration=1.7)
    effect('flash_burst', 'Flash bang: blinding hit spark, spinning sunburst, focus lines, shock ring and star spray',
           flash('FFFFFF', 1.2, 4.5, .22), quad('sunburst', 'FFFFFF', .5, 1.0, 5.0, spin=40),
           quad('speed_lines', 'FFFFFF', .5, 3.0, 5.5), shock('FFFFFF', .6, 5.0, .45, delay=.05),
           burst('star4', 'FFFFFF', 24, life=.6, size=.35, speed=5.0, radius=1.0), duration=1.0)
    effect('ultimate_warrior2', 'Warrior ultimate II: sky and floor seals, colossal sword falls, two giant crescents and an '
           'X-slash split the field, explosion, shock ring, rock and ember storm',
           seal('magic_circle_a', 'FFE6A0', 5.0, life=2.0, spin=30),
           seal('magic_circle_e', 'FFFFFF', 3.2, life=1.6, spin=-60, y=3.6, delay=.05),
           quad('speed_lines', 'FFFFFF', .6, 6.0, 4.0),
           quad('sword', 'FFF0C0', 1.0, 2.6, height=5.4, y=2.0, delay=.15),
           layer('arc', 'slash_strip', 'FFFFFF', life=.3, size=5.0, endSize=6.5, rotation=20, delay=.5),
           layer('arc', 'slash_strip', 'FFFFFF', life=.3, size=5.0, endSize=6.5, rotation=200, delay=.62),
           quad('slash_cross', 'FFFFFF', .4, 2.4, 5.0, delay=.7), flash('FFF8E0', 1.4, 4.6, .22, delay=.7),
           quad('explosion_sheet', 'FFD8A0', .9, 2.6, 4.6, tiles=4, delay=.7),
           seal('shockwave', 'FFC060', .6, life=.7, end=7.0, spin=0, delay=.7),
           burst('rock', '806050', 24, life=1.0, size=.25, speed=5.0, gravity=1.4, y=-.5, delay=.7, alpha=True, radius=1.5),
           embers('FFD080', 60, 3.5, 1.4, .15, delay=.75, gravity=-.3, radius=1.5), duration=2.4)


def statuses_and_environment():
    status_styles = {   # orbit glyph, colour, companion particle
        'poison': ('bubble', 'B6E86F', 'bubble'), 'burn': ('flame_sheet', 'FFA35D', 'ember'),
        'bleed': ('droplet', 'F0788D', None), 'slow': ('snowflake', '99BEF4', None),
        'freeze': ('ice_shard', 'B9F2FF', 'ember'), 'silence': ('silence', 'D4B8EE', None),
        'sleep': ('zzz', 'ABBAED', None), 'blind': ('blind', 'CEB6DE', None), 'stun': ('star5', 'FFE281', None),
        'regen': ('plus', 'A2FFD1', 'ember'), 'provoke': ('anger', 'FF987E', None), 'barrier': ('hex', '9AD8FE', None),
        'mana_shield': ('magic_circle_b', 'B6B2FA', 'dot'), 'invincible': ('star8', 'FFF4BD', 'ember')
    }
    icon_alpha = {'droplet', 'silence', 'zzz', 'blind', 'star5', 'anger'}
    status_families = {0: 'poison', 1: 'stun', 4: 'burn', 5: 'bleed', 6: 'slow', 7: 'freeze', 8: 'silence',
                       11: 'regen', 12: 'barrier', 13: 'provoke', 14: 'sleep', 15: 'blind', 18: 'mana_shield', 19: 'invincible'}
    statuses = json.loads((ROOT / 'Assets/_Game/Resources/Data/statuses.json').read_text(encoding='utf-8'))
    for status in statuses:
        key = status['id']
        family = status_families.get(status['effect_type'])
        extra = None
        if family is not None:
            texture, color, extra = status_styles[family]
        elif status['effect_type'] in (9, 10, 17):
            texture, color = 'arrow_down', 'C3A2E4'
        else:
            texture, color = 'arrow_up', 'F7D299'
        layers = [layer('orbit', texture, color, life=1.2, size=.25, radius=.4, spin=55, count=3, y=1.2,
                        tiles=4 if texture == 'flame_sheet' else 1, alpha=texture in icon_alpha)]
        if extra:
            speed = -.6 if family == 'freeze' else .8
            layers.append(emitter(extra, color, 4, 1.0, .08 if extra != 'bubble' else .12, speed, .35, y=.2 if speed > 0 else 1.2))
        effect('status_' + key, status.get('display_name', key) + ' persistent orbiting status glyph', *layers, loop=True)
    for key, layers in [
        ('verdant_ruins', [emitter('leaf', 'A7CE88', 5, 4, .16, .1, 6, gravity=.015, alpha=True),
                           emitter('petal', 'F4C8D8', 2, 4, .1, .1, 6, gravity=.01, alpha=True)]),
        ('frost_grotto', [emitter('snowflake', 'DCF4FF', 6, 4, .16, .1, 6, gravity=.01, alpha=True),
                          emitter('ember', 'CFEFFF', 3, 3, .08, .05, 6)]),
        ('ember_caverns', [emitter('ember', 'FFC080', 6, 4, .12, .1, 6, gravity=-.01)]),
        ('haunted_crypt', [emitter('skull_wisp', 'B8ABDD', 5, 4, .16, .1, 6, alpha=True),
                           emitter('dot', 'A898E0', 3, 4, .05, .08, 6)])]:
        effect('environment_' + key, 'Local biome atmosphere drifting particles', *layers, loop=True)


# --- skill signatures --------------------------------------------------------------------------------
# One recipe per skill family so every named skill reads as its name: lances fly and shatter, storms rain
# bolts, meteors fall and crater, whirlwinds spin blade rings, crosses are vertical + horizontal beams, gates
# are portals, heals rise as petals, barriers are hex domes, debuffs carry their status glyph. Authored at the
# close battle camera (~10 m, FOV 42): single-target impacts ~2.5-3.5 m, group fields ~7-8 m, ultimates ~9 m.

def pillar(color, width, height, life=.8, y=None, delay=0, **values):
    """Vertical light column whose foot sits on the floor."""
    return quad('beam', color, life, width, height=height, y=FLOOR + height * .5 if y is None else y, delay=delay, **values)


def bolt(color, width, height, life=.45, delay=0, rotation=0, y=None):
    """Lightning bolt flipbook dropping from above onto the anchor."""
    return quad('lightning_sheet', color, life, width, height=height, y=height * .32 if y is None else y, tiles=4,
                delay=delay, rotation=rotation)


def charges():
    """Element casting seals (charge_vfx, played on the caster for the whole wind-up)."""
    effect('charge_fire', 'Fire casting: flame rune seal, converging ring, flame tongues licking up around the caster, embers',
           ground_ring('FFE0C0', 3.2, 1.2, .5), seal('magic_circle_a', 'FFD8B0', 2.3, life=1.4, end=2.6, spin=70),
           seal('glow_hard', 'FFB070', 1.6, life=1.2, spin=0, end=2.2),
           emitter('flame_sheet', 'FFD0A0', 12, .6, .7, 1.8, .7, y=FLOOR, tiles=4, upright=True),
           emitter('ember', 'FFD090', 36, .8, .12, 2.6, .8, y=FLOOR), quad('glow', 'FFC080', .9, .6, 1.2, y=.2), duration=1.4)
    effect('charge_ice', 'Ice casting: snowflake seal and counter-rune, ice shards spiral in, frost motes rise, cold glow',
           seal('snowflake', 'E8FCFF', 2.0, life=1.4, end=2.4, spin=40),
           seal('magic_circle_c', 'D8F4FF', 2.6, life=1.4, end=2.8, spin=-60, y=FLOOR + .02),
           burst('ice_shard', 'C8F0FF', 14, life=.8, size=.3, speed=-2.6, radius=1.6, delay=.05),
           emitter('snowflake', 'E8FCFF', 16, 1.0, .16, 1.2, .8, y=FLOOR),
           quad('glow', 'C8F0FF', 1.0, .6, 1.3, y=.2), duration=1.4)
    effect('charge_thunder', 'Thunder casting: pentagram seal, crackling sparks around the caster, small bolts flicker, static glow',
           seal('magic_circle_d', 'F0F4FF', 2.2, life=1.4, end=2.6, spin=90), ground_ring('E8F0FF', 3.0, 1.3, .45),
           emitter('spark', 'F0F8FF', 28, .25, .3, 2.0, .8, y=-.5),
           quad('lightning_sheet', 'E8F4FF', .35, .8, height=1.8, y=.2, tiles=4, delay=.15),
           quad('lightning_sheet', 'E8F4FF', .35, .8, height=1.8, y=.2, tiles=4, delay=.6, rotation=180),
           quad('glow_hard', 'E0F0FF', 1.0, .5, .9, y=.2), duration=1.4)
    effect('charge_holy', 'Holy casting: sun seal, halo above the head, motes of light falling in, rising sparkles',
           seal('magic_circle_f', 'FFF4D0', 2.4, life=1.4, end=2.7, spin=40), ground_ring('FFF8E0', 3.0, 1.2, .5),
           quad('halo', 'FFFFFF', 1.3, .7, .9, horizontal=True, y=1.0, spin=80),
           emitter('light_streak', 'FFF6D8', 14, .5, .7, -4.0, .9, y=2.2, upright=True),
           emitter('ember', 'FFF6D0', 26, .8, .1, 2.0, .7, y=FLOOR), quad('glow', 'FFF2C8', 1.0, .6, 1.3, y=.2), duration=1.4)
    effect('charge_dark', 'Dark casting: abyss sigil, imploding ring, violet motes and wisps sucked into the caster, shadow smoke',
           seal('magic_circle_d', 'D8B8FF', 2.4, life=1.4, end=2.7, spin=-60), ground_ring('C090FF', 3.2, .8, .7),
           quad('swirl', 'B080FF', 1.3, .8, 1.6, spin=-240, y=.1),
           burst('dot', 'D0B0FF', 26, life=.8, size=.12, speed=-3.0, radius=1.8),
           burst('skull_wisp', 'D8C0FF', 4, life=.9, size=.3, speed=-1.6, radius=1.4, delay=.1),
           emitter('smoke_sheet', '2A1838', 6, 1.0, .7, .8, .6, y=FLOOR, tiles=4, alpha=True), duration=1.4)
    effect('charge_heal', 'Healing casting: leaf seal, soft glow, petals and leaves rising around the caster',
           seal('magic_circle_b', 'E0FFE8', 2.3, life=1.4, end=2.6, spin=50), ground_ring('E8FFF0', 3.0, 1.2, .5),
           emitter('leaf', 'D0FFD8', 10, 1.0, .2, 1.2, .8, y=FLOOR), emitter('petal', 'FFE8F0', 8, 1.2, .16, 1.0, .8, y=FLOOR),
           emitter('plus', 'E8FFF0', 8, .9, .2, 1.4, .6, y=-.5), quad('glow', 'E0FFE8', 1.0, .6, 1.3, y=.2), duration=1.4)
    effect('charge_bow', 'Archer focus: lock-on reticle closes on the bow, converging ring and focus lines, gathering light',
           ground_ring('E8F8FF', 3.0, 1.0, .5),
           quad('reticle', 'E8F8FF', .8, 2.0, .7, spin=160, y=.3),
           quad('speed_lines', 'E0F4FF', .5, 2.8, 1.2),
           burst('dot', 'E8F8FF', 20, life=.7, size=.12, speed=-2.8, radius=1.6),
           quad('glow_hard', 'E8F8FF', 1.0, .3, .8, y=.3, delay=.4), duration=1.3)
    effect('charge_grand', 'Ultimate casting: twin grand seals, aura column, converging focus lines, orbiting stars, ember fountain',
           seal('magic_circle_e', 'FFFFFF', 3.4, life=1.8, end=3.8, spin=40),
           seal('magic_circle_c', 'FFFFFF', 4.2, life=1.8, end=4.4, spin=-60, y=FLOOR + .02),
           ground_ring('FFFFFF', 5.0, 1.4, .6), quad('speed_lines', 'FFFFFF', .6, 3.6, 1.6),
           pillar('FFFFFF', 1.4, 4.0, 1.4, delay=.1),
           layer('orbit', 'star8', 'FFFFFF', life=1.6, size=.32, radius=1.3, spin=160, count=6, y=.1),
           emitter('ember', 'FFFFFF', 50, .9, .12, 3.0, 1.2, y=FLOOR), duration=1.8)


def projectiles():
    """travel_vfx bodies (loop, aligned along the flight). Prefix decides the flight speed in BattleView:
    orb_* slow, bolt_* medium, anything else fast."""
    def shot(key, description, *layers):
        effect(key, description, *layers, duration=.5, loop=True)
    shot('lance_ice', 'Ice lance: long faceted spear of ice along its flight, cold glow, spinning snowflake, frost trail',
         quad('lance', 'E8FAFF', 1.0, .4, height=1.7, rotation=-90, align=True),
         quad('glow_hard', '9FE4FF', .6, .6), quad('snowflake', 'E8FCFF', 1.2, .4, spin=300),
         layer('trail', 'trail', 'A8E6FF', life=.28, size=.34))
    shot('lance_void', 'Void lance: black-violet spear with a spinning void swirl at its head and a smoky trail',
         quad('lance', 'D8B8FF', 1.0, .4, height=1.7, rotation=-90, align=True),
         quad('swirl', 'B080FF', 1.0, .7, spin=-480), quad('glow_hard', '8A5CFF', .6, .5),
         layer('trail', 'trail', '8A50E0', life=.3, size=.38))
    shot('orb_spark', 'Spark orb: crackling ball of lightning, flickering bolts, star glint, electric trail',
         quad('glow_hard', 'F0F8FF', .6, .55), quad('lightning_sheet', 'E8F4FF', .3, .7, height=.7, tiles=4, spin=400),
         quad('star8', 'FFFFFF', .8, .5, spin=300), layer('trail', 'trail', 'D8ECFF', life=.2, size=.3))
    shot('orb_spirit', 'Spirit fire: blue-violet will-o-wisp flame with a ghost face, ghostly trail',
         quad('flame_sheet', 'B8C8FF', .5, .8, rotation=90, tiles=4, align=True),
         quad('skull_wisp', 'D8D0FF', 1.0, .4), quad('glow_hard', '9080FF', .6, .5),
         layer('trail', 'trail', '9080FF', life=.3, size=.34))
    for key, description, color, head, trail in (
            ('arrow_fire', 'Flame arrow: burning light arrow, flame tongue streaming back, hot trail', 'FFE0B0',
             quad('flame_sheet', 'FFB070', .5, .6, rotation=90, tiles=4, align=True), 'FF9A50'),
            ('arrow_ice', 'Frost arrow: light arrow with an ice tip, frost glint, cold trail', 'E8FAFF',
             quad('ice_shard', 'E8FAFF', 1.0, .22, height=.44, rotation=-90, align=True), 'A8E6FF'),
            ('arrow_thunder', 'Thunder arrow: light arrow wrapped in crackling bolts, electric trail', 'FFF8D0',
             quad('lightning_sheet', 'F0F8FF', .3, .5, height=.9, rotation=90, tiles=4, align=True), 'F0E890'),
            ('arrow_holy', 'Holy arrow: golden light arrow, spinning star at the head, bright trail', 'FFF4D0',
             quad('star4', 'FFFFFF', .8, .42, spin=300), 'FFE9A0'),
            ('arrow_shadow', 'Shadow needle: violet light arrow with a void swirl, smoky trail', 'E0C8FF',
             quad('swirl', 'B080FF', 1.0, .45, spin=-480), '7A4ACC'),
            ('arrow_poison', 'Venom arrow: green arrow dripping toxic bubbles, green trail', 'E0FFC0',
             quad('bubble', 'D8FFB0', 1.0, .3, spin=90), '90E050'),
            ('arrow_sleep', 'Sleep arrow: pastel arrow with a soft star, dreamy pink-blue trail', 'E8E8FF',
             quad('star4', 'FFE0F8', .8, .36, spin=200), 'B8C0FF')):
        shot(key, description, quad('arrow_streak', color, 1.0, 1.15, height=.3, align=True),
             quad('glow_hard', trail, .6, .3), head, layer('trail', 'trail', trail, life=.18, size=.12))


def signature_impacts():
    """impact_vfx / area_vfx per skill family."""
    # ---- fire ---------------------------------------------------------------------------------------
    effect('fire_arrow_hit', 'Flame arrow hit: arrow streak punches in, hit spark, burst of flame, ember spray, smoke wisp',
           quad('arrow_streak', 'FFE8C0', .22, 2.6, height=.6, rotation=75), flash('FFF0D0', .6, 2.0, .15, delay=.03),
           quad('explosion_sheet', 'FFD9A0', .55, 1.2, 2.4, tiles=4, delay=.04),
           quad('flame_sheet', 'FFC890', .6, 1.2, 1.6, y=.3, tiles=4, delay=.1),
           embers('FFD090', 22, 3.2, .8, .14), smoke('3A2A30', 5, .8, .9, .7, delay=.15), duration=1.0)
    effect('blaze', 'Blaze: a spiralling fire tornado engulfs the target, flame columns, scorch ring, ember storm and smoke',
           seal('glow_hard', 'FFB060', 2.4, life=1.3, spin=0, end=3.4), seal('magic_circle_a', 'FFD0A0', 3.0, life=1.4, spin=60),
           quad('tornado', 'FFC890', 1.2, 2.0, 2.6, height=4.2, y=1.2, delay=.05),
           quad('flame_sheet', 'FFD8A8', 1.0, 2.2, height=3.6, y=.9, tiles=4, delay=.1),
           quad('flame_sheet', 'FFC080', .9, 1.8, height=3.0, y=.7, tiles=4, delay=.3, rotation=6),
           flash('FFF0D0', 1.0, 3.0, .18, delay=.1), seal('shockwave', 'FFB070', .5, life=.5, end=4.4, spin=0, delay=.1),
           emitter('ember', 'FFE0A0', 60, .9, .14, 3.4, 1.0, y=FLOOR),
           smoke('302028', 8, 1.2, 1.2, 1.0, delay=.5, radius=.6, y=.6, gravity=-.05), duration=1.6)
    effect('flame_wave', 'Flame wave: a ring of fire rolls outward across the group, flame tongues, explosions, ember storm',
           seal('magic_circle_a', 'FFE0C0', 6.0, life=1.6, spin=30),
           seal('shockwave', 'FFC080', 1.0, life=.8, end=8.0, spin=0, delay=.05), ground_ring('FFB070', 1.0, 8.0, .8, delay=.05),
           burst('flame_sheet', 'FFD0A0', 26, life=.8, size=1.6, speed=5.5, radius=.6, y=-.3, tiles=4, delay=.05),
           emitter('flame_sheet', 'FFC890', 18, .8, 1.6, .8, 3.2, y=FLOOR + .5, tiles=4, upright=True, delay=.2),
           flash('FFF0D0', 1.2, 4.0, .2, delay=.05),
           emitter('ember', 'FFD090', 70, 1.0, .14, 3.0, 3.4, y=FLOOR, delay=.1),
           smoke('302028', 12, 1.2, 1.4, 1.3, delay=.45, radius=2.0), duration=1.8)
    effect('hellfire', 'Hell flame: blood-red abyss seal, black-crimson fire geysers erupting all over the group, skulls in the '
           'flames, giant flash and double shockwave, cinder storm and black smoke',
           seal('magic_circle_d', 'FF9070', 7.0, life=2.0, spin=25), seal('magic_circle_a', 'FFC0A0', 5.0, life=2.0, spin=-40, y=FLOOR + .02),
           seal('glow_hard', 'FF6040', 5.0, life=1.6, spin=0, end=8.0, delay=.1),
           emitter('flame_sheet', 'FFB080', 30, 1.0, 2.6, 1.2, 3.4, y=FLOOR + .9, tiles=4, upright=True, delay=.1),
           emitter('explosion_sheet', 'FFC0A0', 8, .7, 2.6, .2, 3.0, y=0, tiles=4, upright=True, delay=.15),
           pillar('FF8060', 2.4, 6.0, 1.0, delay=.15),
           burst('skull_wisp', 'FFB0A0', 10, life=1.2, size=.6, speed=3.0, radius=1.8, gravity=-.3, delay=.25),
           flash('FFE0C0', 1.6, 5.0, .22, delay=.2), seal('shockwave', 'FF8060', .6, life=.7, end=9.0, spin=0, delay=.2),
           seal('shockwave', 'FFC080', .6, life=.7, end=7.0, spin=0, delay=.45),
           emitter('ember', 'FF9060', 90, 1.1, .15, 3.6, 3.6, y=FLOOR, delay=.1),
           smoke('201018', 16, 1.4, 1.6, 1.5, delay=.5, radius=2.4, y=.4), duration=2.2)
    effect('inferno', 'Inferno: wide scorch seal, flame columns and explosions erupting across the group, ember storm, smoke',
           seal('magic_circle_a', 'FFE0C0', 6.6, life=1.8, spin=25),
           seal('glow_hard', 'FFB070', 4.6, life=1.4, spin=0, end=7.2, delay=.1),
           emitter('flame_sheet', 'FFD0A0', 26, 1.0, 2.2, .9, 3.2, y=FLOOR + .7, tiles=4, upright=True, delay=.1),
           emitter('explosion_sheet', 'FFE0B8', 7, .7, 2.4, .2, 3.0, y=-.2, tiles=4, upright=True, delay=.15),
           flash('FFF0D0', 1.4, 4.6, .2, delay=.15), seal('shockwave', 'FFB070', .6, life=.6, end=7.8, spin=0, delay=.15),
           emitter('ember', 'FFD090', 70, 1.0, .14, 3.2, 3.4, y=FLOOR, delay=.1),
           smoke('302028', 14, 1.2, 1.4, 1.5, delay=.4, radius=2.0), duration=1.8)
    effect('solar_flare', 'Solar flare: a blazing sun swells overhead, scorching rays rain down, white-out flash, burning floor',
           quad('sunburst', 'FFF0C0', 1.4, 1.2, 4.6, y=3.0, spin=25), quad('glow', 'FFE8B0', 1.4, 2.0, 3.4, y=3.0),
           quad('glow_hard', 'FFFFFF', 1.0, 1.0, 1.8, y=3.0),
           emitter('light_streak', 'FFE8B0', 40, .45, 1.4, -9.0, 3.0, y=3.0, upright=True, delay=.2),
           emitter('beam', 'FFD8A0', 6, .6, 2.6, 0, 2.8, y=.9, upright=True, delay=.3),
           flash('FFFFFF', 1.6, 5.0, .22, delay=.35), seal('glow_hard', 'FFB060', 4.0, life=1.2, spin=0, end=7.0, delay=.35),
           emitter('flame_sheet', 'FFC890', 14, .8, 1.4, .8, 3.0, y=FLOOR + .4, tiles=4, upright=True, delay=.4),
           emitter('ember', 'FFE0A0', 50, 1.0, .12, 2.6, 3.2, y=FLOOR, delay=.35), duration=1.9)
    effect('fire_breath', 'Fire breath: a rolling torrent of flame washes over the group, billowing fire, cinders and black smoke',
           burst('flame_sheet', 'FFD0A0', 30, life=.9, size=2.0, speed=3.5, radius=2.0, y=0, tiles=4),
           emitter('flame_sheet', 'FFC080', 24, .8, 1.8, .8, 3.2, y=FLOOR + .5, tiles=4, upright=True, delay=.05),
           quad('explosion_sheet', 'FFD8A8', .8, 2.4, 4.4, tiles=4, delay=.1),
           flash('FFF0D0', 1.2, 4.0, .2, delay=.1), seal('glow_hard', 'FFA050', 3.6, life=1.2, spin=0, end=6.4),
           emitter('ember', 'FFD090', 60, .9, .14, 3.4, 3.4, y=FLOOR),
           smoke('201818', 16, 1.4, 1.5, 1.5, delay=.35, radius=2.2, y=.2), duration=1.8)
    effect('sun_judgment', 'Sun judgment: a solar seal opens in the sky and drops a colossal pillar of sun-fire, crater blast',
           seal('magic_circle_f', 'FFE8B0', 4.0, life=1.6, spin=40, y=3.4), quad('sunburst', 'FFF0C0', 1.2, 1.0, 4.0, y=3.2, spin=30),
           pillar('FFE0A0', 3.2, 7.0, .9, delay=.25),
           quad('explosion_sheet', 'FFD8A0', .8, 2.6, 5.0, tiles=4, delay=.35),
           flash('FFF8E0', 1.6, 5.0, .22, delay=.35), seal('shockwave', 'FFC080', .6, life=.7, end=8.0, spin=0, delay=.35),
           emitter('flame_sheet', 'FFC890', 16, .8, 1.6, .8, 3.0, y=FLOOR + .4, tiles=4, upright=True, delay=.4),
           emitter('ember', 'FFE0A0', 60, 1.0, .13, 3.2, 3.2, y=FLOOR, delay=.35),
           smoke('302028', 10, 1.2, 1.3, 1.2, delay=.6, radius=2.0), duration=2.0)
    effect('blaze_rain', 'Blazing arrow rain: a fire seal in the sky rains burning arrows and meteors, the floor erupts in flame',
           seal('magic_circle_a', 'FFD8B0', 4.0, life=1.6, spin=60, y=3.2),
           emitter('arrow_rain', 'FFD8A8', 70, .5, 1.4, -10.0, 3.0, y=3.0, upright=True, delay=.1),
           emitter('meteor', 'FFC890', 10, .5, 1.0, -9.0, 2.8, y=3.0, upright=True, delay=.2),
           emitter('explosion_sheet', 'FFE0B8', 8, .6, 1.8, .2, 3.0, y=-.3, tiles=4, upright=True, delay=.35),
           emitter('flame_sheet', 'FFC890', 14, .7, 1.4, .8, 3.0, y=FLOOR + .4, tiles=4, upright=True, delay=.4),
           ground_ring('FFB070', .6, 7.0, .7, delay=.4), emitter('ember', 'FFD090', 50, .9, .13, 2.6, 3.2, y=FLOOR, delay=.35),
           duration=1.8)
    # ---- ice ----------------------------------------------------------------------------------------
    effect('ice_lance_hit', 'Ice lance hit: the spear drives in and shatters - long frost streak, ice spike, hit spark, shard spray, '
           'snowflake bloom and frost mist',
           quad('lance', 'E8FAFF', .3, .6, .5, height=2.6, rotation=-12),
           flash('E8FCFF', .7, 2.2, .15, delay=.02), shock('C8F0FF', .5, 3.0, .32, delay=.04),
           quad('crystal', 'E0F8FF', .8, 1.0, 2.6, y=-.1, delay=.06), quad('snowflake', 'F0FCFF', .6, .5, 2.6, spin=120, delay=.04),
           burst('ice_shard', 'C8F0FF', 26, life=.8, size=.42, speed=5.0, gravity=.8),
           ground_ring('A8E8FF', .4, 3.2, .5), smoke('E0F4FF', 6, .6, 1.0, .9, delay=.12),
           embers('E0FAFF', 16, 1.0, 1.0, delay=.1, gravity=-.05), duration=1.2)
    effect('glacier_spike', 'Glacial spike: giant ice spikes burst up from the floor around and through the target, frost flash, '
           'shard spray and freezing mist',
           seal('snowflake', 'E8FCFF', 3.0, life=1.4, spin=30, end=3.8), seal('magic_circle_c', 'D8F4FF', 3.6, life=1.4, spin=-40, y=FLOOR + .02),
           quad('crystal', 'E8FCFF', 1.1, 1.0, 3.6, y=.3, delay=.05),
           burst('crystal', 'D8F4FF', 6, life=1.0, size=1.6, speed=.6, radius=1.0, y=-.4, delay=.1),
           quad('lance', 'E8FAFF', .9, .7, height=3.6, y=.4, delay=.08, rotation=8),
           flash('E8FCFF', 1.0, 3.2, .18, delay=.08), seal('shockwave', 'C8F0FF', .5, life=.6, end=5.0, spin=0, delay=.08),
           burst('ice_shard', 'C8F0FF', 30, life=.9, size=.4, speed=5.0, gravity=.8, radius=.6, delay=.1),
           smoke('E0F4FF', 8, .8, 1.2, 1.0, radius=1.0, delay=.25), duration=1.6)
    effect('frost_nova', 'Frost nova: a freezing ring explodes outward from the centre, ice crystals snap up in a ring, white flash, '
           'shards and snow mist',
           seal('snowflake', 'F0FCFF', 1.0, life=1.0, spin=90, end=7.0),
           seal('shockwave', 'D8F4FF', 1.0, life=.7, end=8.0, spin=0), ground_ring('C8F0FF', 1.0, 8.0, .7),
           burst('crystal', 'E0F8FF', 14, life=1.1, size=1.4, speed=4.0, radius=.5, y=-.4, delay=.05),
           burst('ice_shard', 'C8F0FF', 36, life=.9, size=.4, speed=7.0, gravity=.6, radius=.4, delay=.05),
           flash('E8FCFF', 1.4, 4.4, .2), emitter('snowflake', 'F0FCFF', 30, 1.2, .22, 1.2, 3.4, y=FLOOR, delay=.1),
           smoke('E0F4FF', 12, 1.4, 1.2, 1.1, radius=2.0, delay=.2), duration=1.8)
    effect('blizzard', 'Blizzard: a howling snow storm - grey-white cloud overhead, dense driving snow, swirling wind funnel, '
           'frost mist over the group',
           smoke('C8D8E8', 12, .3, 1.8, 1.4, radius=2.6, y=3.0, gravity=0),
           emitter('snowflake', 'F0FCFF', 90, 1.0, .26, -5.0, 3.6, y=3.0),
           emitter('ice_shard', 'E0F8FF', 30, .7, .3, -7.0, 3.4, y=3.0, upright=True, delay=.1),
           quad('tornado', 'E8F8FF', 1.6, 3.0, 3.6, height=4.6, y=1.2, delay=.1),
           layer('orbit', 'snowflake', 'F0FCFF', life=1.6, size=.4, radius=2.6, spin=260, count=10, y=.2),
           seal('magic_circle_c', 'D8F4FF', 6.0, life=1.8, spin=-40),
           emitter('smoke_sheet', 'E8F4FF', 14, 1.2, 1.4, .6, 3.2, y=FLOOR + .2, tiles=4, alpha=True), duration=1.9)
    effect('freezing_tide', 'Freezing tide: a surging wave of icy water sweeps the group and freezes - bubbles and spray, '
           'droplets, ice crystals locking up, frost ring',
           seal('magic_circle_b', 'C8ECFF', 6.0, life=1.8, spin=30),
           burst('droplet', 'B8E8FF', 50, life=.9, size=.3, speed=6.0, radius=1.0, gravity=1.2, alpha=True),
           emitter('bubble', 'D8F4FF', 40, 1.0, .3, 1.6, 3.4, y=FLOOR),
           burst('smoke_sheet', 'D8F0FF', 14, life=1.0, size=1.6, speed=4.0, radius=1.2, y=-.3, tiles=4, alpha=True),
           emitter('crystal', 'E0F8FF', 14, .9, 1.4, .3, 3.0, y=FLOOR + .4, upright=True, delay=.45),
           seal('shockwave', 'C8F0FF', .8, life=.7, end=8.0, spin=0), flash('E8FCFF', 1.2, 4.0, .2, delay=.45),
           ground_ring('A8E8FF', .8, 7.6, .7, delay=.45), duration=1.8)
    effect('absolute_zero', 'Absolute zero: a colossal snowflake seal and sky seal, the whole field crystallises into giant ice, '
           'white-out flash, then everything shatters into a storm of shards and freezing mist',
           seal('snowflake', 'F0FCFF', 6.0, life=2.2, spin=20, end=8.0), seal('magic_circle_c', 'D8F4FF', 8.0, life=2.2, spin=-30, y=FLOOR + .02),
           seal('magic_circle_e', 'E8F8FF', 4.0, life=1.8, spin=40, y=3.6),
           emitter('snowflake', 'F0FCFF', 50, 1.4, .26, -2.0, 3.8, y=3.2),
           emitter('crystal', 'E8FCFF', 24, 1.0, 2.0, .4, 3.4, y=FLOOR + .7, upright=True, delay=.15),
           quad('crystal', 'F0FCFF', 1.4, 2.0, 5.0, y=.9, delay=.2),
           flash('FFFFFF', 1.8, 5.6, .24, delay=.6), seal('shockwave', 'E0F8FF', .8, life=.7, end=10.0, spin=0, delay=.6),
           burst('ice_shard', 'D8F4FF', 60, life=1.1, size=.5, speed=8.0, gravity=.8, radius=1.6, delay=.65),
           burst('square', 'E0F8FF', 30, life=1.0, size=.3, speed=6.0, gravity=1.0, radius=1.4, delay=.65),
           smoke('E8F4FF', 16, 1.6, 1.6, 1.4, radius=2.6, delay=.7), duration=2.4)
    effect('ice_arrow_hit', 'Frost arrow hit: arrow streak, frost bloom of crystals and snowflake, hit spark, shards and mist',
           quad('arrow_streak', 'E8FAFF', .22, 2.6, height=.6, rotation=75), flash('E8FCFF', .5, 1.8, .14, delay=.03),
           quad('snowflake', 'F0FCFF', .6, .4, 2.2, spin=150, delay=.03), quad('crystal', 'E0F8FF', .7, .8, 2.0, y=-.1, delay=.05),
           burst('ice_shard', 'C8F0FF', 18, life=.7, size=.32, speed=4.0, gravity=.6), smoke('E0F4FF', 4, .5, .9, .7, delay=.1),
           duration=1.0)
    # ---- thunder ------------------------------------------------------------------------------------
    effect('spark_hit', 'Spark hit: crackling electric pop - hot core, star glint, two quick bolts, spark spray, static motes',
           quad('glow_hard', 'FFFFFF', .26, .8, 1.6), glint('FFFFFF', .5, 2.2, .22, texture='star8'),
           quad('lightning_sheet', 'F0F8FF', .35, 1.2, height=1.6, tiles=4),
           quad('lightning_sheet', 'E0F0FF', .35, 1.2, height=1.6, tiles=4, rotation=90, delay=.08),
           flash('F0F8FF', .5, 1.8, .14), sparks('F0FAFF', 26, 5.5, .32, .3),
           embers('C8E8FF', 12, 1.2, .7, gravity=0, delay=.05), duration=.9)
    effect('chain_spark_hit', 'Chain spark: arcs leap sideways into the target - horizontal bolts, crackle flash, sparks and ring',
           quad('lightning_sheet', 'F0F8FF', .4, 1.4, height=3.6, tiles=4, rotation=90),
           quad('lightning_sheet', 'D8ECFF', .4, 1.2, height=3.0, tiles=4, rotation=-60, delay=.07),
           quad('glow_hard', 'FFFFFF', .25, .7, 1.4), flash('F0F8FF', .5, 1.9, .15, delay=.02),
           shock('E0F0FF', .4, 2.6, .3, delay=.03), sparks('F0FAFF', 28, 6.0, .32, .3),
           embers('C8E8FF', 12, 1.4, .7, gravity=0, delay=.05), duration=.9)
    effect('lightning_bolt', 'Lightning bolt: one colossal bolt cracks down from the sky onto the target, double flash, scorch ring, '
           'spark fountain and static',
           smoke('3A3A50', 6, .2, 1.2, 1.0, radius=1.2, y=3.4, gravity=0),
           bolt('F8FCFF', 2.2, 6.0, .5, delay=.05), bolt('D0E4FF', 1.6, 5.2, .45, delay=.16, rotation=6),
           pillar('E8F4FF', 1.0, 6.0, .35, delay=.05), flash('FFFFFF', 1.2, 3.6, .18, delay=.06),
           quad('glow_hard', 'E0F0FF', .3, 1.2, 2.4, delay=.06),
           seal('shockwave', 'D8ECFF', .5, life=.5, end=5.0, spin=0, delay=.06), ground_ring('C0DCFF', .4, 4.0, .45, delay=.06),
           burst('spark', 'F0FAFF', 40, life=.4, size=.36, speed=7.0, radius=.3, delay=.06),
           emitter('spark', 'E8F4FF', 30, .3, .26, 2.0, 1.0, y=FLOOR, delay=.1), duration=1.3)
    effect('thunder_storm', 'Thunder storm: dark storm cloud over the group, many bolts raining down, white flashes, wide floor ring, '
           'crackling sparks',
           smoke('2A2A40', 14, .3, 1.8, 1.6, radius=2.8, y=3.2, gravity=0),
           seal('magic_circle_d', 'E8F0FF', 6.4, life=1.8, spin=40),
           bolt('F0F8FF', 2.4, 5.6, .45, delay=.15),
           emitter('lightning_sheet', 'F0F8FF', 26, .4, 3.2, 0, 3.0, y=1.4, tiles=4, upright=True, delay=.15),
           flash('F0F8FF', 1.4, 4.6, .2, delay=.2), flash('E0F0FF', 1.0, 3.6, .18, delay=.6),
           ground_ring('D0E8FF', .6, 7.6, .5, delay=.2),
           emitter('spark', 'F0FAFF', 80, .3, .3, 3.4, 3.2, y=FLOOR, delay=.15), duration=1.8)
    effect('indra', 'Indra, heavenly thunder: a divine seal opens high in the sky, a god-pillar of lightning slams the centre while '
           'a ring of bolts strikes around it, white-out flash, double shockwave and an electric storm',
           seal('magic_circle_e', 'FFF8E0', 5.0, life=2.2, spin=30, y=3.8), seal('magic_circle_d', 'F0F4FF', 7.6, life=2.2, spin=-25),
           smoke('30304A', 12, .3, 2.0, 1.6, radius=3.0, y=3.6, gravity=0),
           pillar('F8FCFF', 3.0, 8.0, .8, delay=.35), bolt('FFFFFF', 3.4, 7.0, .55, delay=.35),
           bolt('E8F0FF', 2.6, 6.0, .5, delay=.5, rotation=-8),
           emitter('lightning_sheet', 'F0F8FF', 30, .35, 3.4, 0, 3.4, y=1.4, tiles=4, upright=True, delay=.4),
           flash('FFFFFF', 2.0, 6.0, .24, delay=.38), seal('shockwave', 'E8F4FF', .8, life=.7, end=10.0, spin=0, delay=.38),
           seal('shockwave', 'FFF4C0', .8, life=.7, end=8.0, spin=0, delay=.62),
           emitter('spark', 'F0FAFF', 100, .35, .34, 4.0, 3.6, y=FLOOR, delay=.35),
           embers('E0F0FF', 40, 3.0, 1.2, .14, delay=.45, gravity=-.2, radius=2.0), duration=2.3)
    effect('thunder_arrow_hit', 'Thunder arrow hit: arrow streak, a bolt answers from the sky onto the arrow, flash, sparks, ring',
           quad('arrow_streak', 'FFF8D0', .22, 2.6, height=.6, rotation=75), bolt('F0F8FF', 1.4, 4.0, .4, delay=.05),
           flash('FFFFFF', .7, 2.2, .15, delay=.06), ground_ring('E0F0FF', .4, 3.0, .4, delay=.06),
           sparks('F0FAFF', 26, 5.5, .32, .3, delay=.06), duration=1.0)
    effect('giga_slash', 'Giga slash: a colossal lightning-charged crescent cleaves the whole field, thunder column at the centre, '
           'X-slash, white flash, shock ring and electric storm',
           quad('speed_lines', 'FFFFFF', .5, 7.0, 4.0),
           layer('arc', 'slash_strip', 'FFFFFF', life=.3, size=6.0, endSize=8.0, rotation=195),
           quad('slash_arc', 'F8FCFF', .35, 7.0, 8.6, height=3.0, rotation=-18, delay=.06),
           bolt('F8FCFF', 2.6, 6.4, .5, delay=.12), pillar('F0F8FF', 1.4, 7.0, .4, delay=.12),
           quad('slash_cross', 'FFFFFF', .35, 3.0, 6.0, delay=.2), flash('FFFFFF', 1.6, 5.0, .2, delay=.12),
           seal('shockwave', 'E8F4FF', .6, life=.6, end=9.0, spin=0, delay=.12),
           burst('spark', 'F0FAFF', 60, life=.45, size=.36, speed=8.0, radius=1.6, delay=.12),
           emitter('lightning_sheet', 'F0F8FF', 12, .35, 2.4, 0, 3.0, y=1.0, tiles=4, upright=True, delay=.2), duration=1.6)
    # ---- holy ---------------------------------------------------------------------------------------
    effect('banish', 'Banish: an upright holy seal opens over the target, it is swallowed by white light, cross flash, motes '
           'lift away as the evil is erased',
           quad('magic_circle_f', 'FFF4D0', 1.2, 1.0, 3.0, spin=80, y=.3),
           pillar('FFF8E0', 1.6, 5.0, 1.0, delay=.1), quad('glow', 'FFFFFF', .7, 1.0, 2.8, y=.2, delay=.15),
           quad('cross', 'FFFFFF', .6, 1.0, height=2.0, y=.4, delay=.2), flash('FFFFFF', .8, 2.6, .18, delay=.2),
           emitter('light_streak', 'FFF6D8', 24, .6, .8, 4.0, .8, y=FLOOR, upright=True, delay=.2),
           burst('star4', 'FFF8E0', 18, life=.9, size=.32, speed=2.6, gravity=-.4, delay=.22), duration=1.5)
    effect('holy_lance', 'Holy lance: a giant spear of light plunges from the sky into the target, cross flash, sun seal, '
           'light shockwave, feather fan and rising light',
           seal('magic_circle_f', 'FFF0C0', 3.0, life=1.4, spin=40, end=3.6),
           quad('lance', 'FFF8E0', .45, 1.1, height=4.8, y=1.6, rotation=180, delay=.05),
           pillar('FFF6D8', 1.2, 6.0, .7, delay=.2), flash('FFFFFF', 1.0, 3.2, .18, delay=.22),
           quad('cross', 'FFFFFF', .7, .9, height=1.8, y=.4, delay=.24), quad('sunburst', 'FFF3C2', .7, .6, 3.6, delay=.22, spin=20),
           seal('shockwave', 'FFE8B0', .5, life=.5, end=5.0, spin=0, delay=.22),
           burst('feather', 'FFF2D0', 22, life=1.2, size=.28, speed=2.6, gravity=.15, delay=.25),
           emitter('ember', 'FFF8E0', 34, .8, .12, 2.4, 1.0, y=FLOOR, delay=.2), duration=1.6)
    effect('judgment_cross', 'Judgment cross: a towering vertical beam and a sweeping horizontal beam form a giant cross of light '
           'over the target, cross glyph, sun seal, radiant shock and sparks',
           seal('magic_circle_f', 'FFF2C8', 4.4, life=1.8, spin=30),
           seal('cross', 'FFF8E0', 2.4, life=1.4, spin=0, height=4.8, delay=.1),
           quad('beam', 'FFF8E0', .9, 2.0, height=7.0, y=1.4, delay=.2),
           quad('beam', 'FFF8E0', .9, 2.0, height=7.0, y=.9, rotation=90, delay=.3),
           quad('cross', 'FFFFFF', 1.0, 2.0, height=4.0, y=.9, delay=.35),
           flash('FFFFFF', 1.4, 4.4, .22, delay=.35), seal('shockwave', 'FFE8B0', .6, life=.7, end=7.0, spin=0, delay=.35),
           quad('sunburst', 'FFF3C2', .8, 1.0, 5.0, y=.9, delay=.35, spin=15),
           burst('star4', 'FFF4C8', 30, life=1.0, size=.36, speed=4.0, radius=.8, delay=.36),
           emitter('ember', 'FFF8E0', 50, 1.0, .12, 2.8, 2.0, y=FLOOR, delay=.3), duration=2.0)
    effect('grand_cross', 'Grand cross: a giant cross of light burns into the ground under the group, two crossing light walls rise, '
           'a holy sword falls in the centre, radiant burst, feathers and sparks',
           seal('magic_circle_f', 'FFF2C8', 7.0, life=2.0, spin=20),
           seal('cross', 'FFF8E0', 4.0, life=1.6, spin=0, height=8.0, delay=.05),
           quad('beam', 'FFF8E0', 1.0, 2.8, height=8.0, y=1.6, delay=.2),
           quad('beam', 'FFF8E0', 1.0, 2.8, height=8.0, y=.9, rotation=90, delay=.28),
           quad('sword', 'FFF8E0', 1.0, 2.0, height=4.4, y=1.4, delay=.1),
           flash('FFFFFF', 1.8, 5.6, .22, delay=.4), seal('shockwave', 'FFE8B0', .8, life=.7, end=9.0, spin=0, delay=.4),
           quad('sunburst', 'FFF3C2', .8, 1.0, 6.0, y=.6, delay=.4, spin=15),
           burst('feather', 'FFF6E0', 36, life=1.4, size=.3, speed=3.4, gravity=.12, radius=1.6, delay=.4),
           emitter('ember', 'FFF8E0', 70, 1.0, .12, 3.0, 3.4, y=FLOOR, delay=.3), duration=2.2)
    effect('holy_arrow_hit', 'Holy arrow hit: golden streak, small light pillar, cross glint, star burst and feathers',
           quad('arrow_streak', 'FFF8E0', .22, 2.6, height=.6, rotation=75), pillar('FFF6D8', .8, 3.6, .5, delay=.04),
           quad('cross', 'FFFFFF', .45, .6, height=1.2, y=.3, delay=.05), flash('FFF8E0', .6, 2.0, .15, delay=.04),
           burst('star4', 'FFF4C8', 16, life=.6, size=.3, speed=3.4, delay=.05),
           burst('feather', 'FFF2D0', 10, life=1.0, size=.24, speed=2.0, gravity=.15, delay=.06), duration=1.1)
    effect('light_hit', 'Basic light shot hit: small golden pop, star glint, short shock ring and sparkles',
           flash('FFF8E0', .45, 1.5, .14), glint('FFFFFF', .4, 1.6, .22, texture='star8'), shock('FFF0C0', .3, 1.8, .28),
           burst('star4', 'FFF4C8', 10, life=.5, size=.24, speed=2.6), embers('FFF0C0', 8, 1.0, .6, gravity=-.2), duration=.8)
    # ---- dark ---------------------------------------------------------------------------------------
    effect('arcane_hit', 'Basic arcane shot hit: violet pop, small vortex, star glint and motes',
           flash('E8D8FF', .45, 1.5, .14), quad('swirl', 'C8A8FF', .5, .4, 1.6, spin=-300),
           glint('FFFFFF', .35, 1.5, .2, texture='star8'), shock('D0B8FF', .3, 1.8, .28),
           embers('D8C0FF', 10, 1.6, .6, gravity=0), duration=.8)
    effect('void_pierce', 'Void lance hit: the spear tears a black rift in the target - rift and glowing seam, imploding ring, '
           'hit spark, shadow burst and violet embers',
           quad('lance', 'D8B8FF', .25, .6, .5, height=2.6, rotation=-12),
           quad('rift', 'C890FF', .9, 1.0, 1.4, height=2.6, y=.3, delay=.04, alpha=True),
           quad('rift_glow', 'B070FF', .9, 1.2, 1.6, height=2.8, y=.3, delay=.04),
           flash('E8D0FF', .6, 2.2, .16, delay=.03), ground_ring('A060FF', 3.0, .4, .5, y=-.3),
           smoke('1A0C28', 10, 1.4, 1.0, .9, radius=.3, delay=.1),
           embers('D8B8FF', 20, 3.0, .9, .13, gravity=-.2, delay=.05), duration=1.3)
    effect('spirit_fire_hit', 'Spirit fire hit: ghostly blue-violet flames flare up, wailing skull wisps scatter, soft smoke',
           quad('flame_sheet', 'C8D0FF', .8, 1.4, height=2.4, y=.4, tiles=4),
           quad('flame_sheet', 'B0B8FF', .7, 1.1, height=2.0, y=.3, tiles=4, delay=.12, rotation=-6),
           flash('E0E0FF', .5, 1.8, .15), burst('skull_wisp', 'D8D0FF', 6, life=1.0, size=.4, speed=2.2, gravity=-.3, delay=.05),
           emitter('ember', 'C0C8FF', 30, .8, .12, 1.8, .5, y=-.5), smoke('201838', 6, .8, 1.0, .8, delay=.2), duration=1.3)
    effect('abyss_gate', 'Abyss gate: a colossal dark portal ring stands open over the group, the void rift tears through it, '
           'shadow tendrils and skulls lash out, everything is dragged in, then the gate implodes in a violet flash',
           seal('magic_circle_d', 'C8A0FF', 7.0, life=2.2, spin=25), ground_ring('A060FF', 8.0, 1.0, .8),
           quad('magic_circle_d', 'D8B8FF', 2.0, 2.0, 5.0, y=1.6, spin=-40),
           quad('swirl', '9060FF', 2.0, 1.4, 4.6, y=1.6, spin=-160, delay=.1),
           quad('rift', 'B8A0FF', 1.8, 2.0, 2.6, height=5.0, y=1.6, delay=.2, alpha=True),
           quad('rift_glow', '9060FF', 1.8, 2.2, 2.8, height=5.2, y=1.6, delay=.2),
           burst('thorn', '5030A0', 14, life=1.1, size=1.4, speed=3.6, radius=1.0, y=1.0, delay=.3, alpha=True),
           layer('orbit', 'skull_wisp', 'E0C8FF', life=1.6, size=.6, radius=2.6, spin=-150, count=6, y=.8, delay=.2),
           burst('dot', 'D8C0FF', 40, life=1.0, size=.16, speed=-5.0, radius=3.4, y=1.0, delay=.4),
           emitter('smoke_sheet', '180C28', 12, 1.4, 1.4, 1.0, 3.2, y=FLOOR, tiles=4, alpha=True),
           flash('E8D8FF', 1.8, 5.4, .24, delay=1.2), seal('shockwave', 'B080FF', .8, life=.7, end=9.0, spin=0, delay=1.2),
           embers('D0B0FF', 50, 4.0, 1.2, .14, delay=1.2, gravity=-.2, radius=2.0), duration=2.4)
    effect('abyss_wave', 'Abyss wave: a black-violet ring of shadow ripples outward through the group, dark smoke and spirits ride '
           'the wave, violet embers',
           seal('magic_circle_d', 'D8B8FF', 6.0, life=1.6, spin=-30),
           seal('shockwave', 'A070FF', 1.0, life=.8, end=8.4, spin=0), ground_ring('8040E0', 1.0, 8.0, .8),
           seal('shockwave', 'C090FF', 1.0, life=.8, end=7.0, spin=0, delay=.25),
           burst('smoke_sheet', '2A1838', 18, life=1.0, size=1.6, speed=5.0, radius=.6, y=-.4, tiles=4, alpha=True),
           burst('skull_wisp', 'D8B8F0', 12, life=1.0, size=.5, speed=4.0, radius=.6, delay=.1),
           flash('E0C8FF', 1.0, 3.6, .2), embers('D8B8FF', 50, 4.0, 1.0, .13, radius=1.0, delay=.1), duration=1.7)
    effect('soul_reap', 'Soul reap: giant violet scythe arcs sweep the group, souls are torn out and float upward into the dark, '
           'shadow smoke',
           layer('arc', 'slash_strip', 'E0C8FF', life=.3, size=5.0, endSize=6.6, rotation=200),
           layer('arc', 'slash_strip', 'C8A0FF', life=.3, size=4.6, endSize=6.2, rotation=20, delay=.15),
           quad('slash_arc', 'D8B8FF', .35, 5.4, 6.8, height=2.4, rotation=-20, delay=.06),
           flash('E8D8FF', 1.0, 3.4, .18, delay=.06),
           emitter('skull_wisp', 'E0D0FF', 12, 1.2, .5, 2.4, 3.0, y=-.2, delay=.2),
           emitter('dot', 'D8C0FF', 40, 1.0, .12, 2.6, 3.0, y=FLOOR, delay=.2),
           seal('magic_circle_d', 'C8A0FF', 5.6, life=1.6, spin=-40),
           smoke('201030', 12, 1.2, 1.2, 1.1, radius=2.0, delay=.2), duration=1.8)
    effect('shadow_stitch', 'Shadow stitch: shadow needles rain down and pin the target to its own shadow - dark floor pool, '
           'needle spikes, violet sparks and binding ring',
           seal('magic_circle_d', '9060E0', 2.4, life=1.2, spin=-90), quad('glow_hard', '201030', 1.0, 1.6, 2.2, horizontal=True, y=FLOOR + .02, alpha=True),
           burst('spark', 'E0C8FF', 10, life=.35, size=1.0, speed=-1.0, radius=.2, y=1.6, delay=.02),
           emitter('arrow_rain', 'D8B8FF', 30, .35, .9, -8.0, .7, y=2.0, upright=True),
           burst('thorn', '6040B0', 8, life=.9, size=.9, speed=.8, radius=.6, y=-.6, delay=.15, alpha=True),
           flash('E8D8FF', .6, 2.0, .15, delay=.15), ground_ring('A070FF', 2.6, .8, .5, delay=.15),
           sparks('D0A8FF', 18, 4.0, .35, .28, delay=.15), duration=1.3)
    # ---- physical / arrows ------------------------------------------------------------------------
    effect('pierce_triple', 'Triple shot hit: three light-arrow streaks fan into the target, hit spark, tight shock, sparks',
           quad('arrow_streak', 'E8F8FF', .22, 2.6, height=.6, rotation=87),
           quad('arrow_streak', 'E0F4FF', .22, 2.6, height=.6, rotation=63, delay=.04),
           quad('arrow_streak', 'F0FAFF', .22, 2.6, height=.6, rotation=75, delay=.08),
           flash('FFFFFF', .45, 1.6, .14, delay=.04), shock('D8F0FF', .3, 2.0, .28, delay=.05),
           sparks('E8F8FF', 18, 4.6, .3, .26, delay=.04), duration=.9)
    effect('snipe_hit', 'Weak-point snipe: lock-on reticle snaps shut, a long piercing light streak, critical burst and shock ring',
           quad('reticle', 'FFFFFF', .3, 2.4, .9, spin=200),
           quad('arrow_streak', 'FFFFFF', .25, 4.0, height=.8, rotation=75, delay=.12), quad('speed_lines', 'FFFFFF', .3, 3.4, 2.6, delay=.12),
           flash('FFFFFF', .7, 2.4, .16, delay=.14), quad('sunburst', 'FFF0C8', .4, .5, 3.0, delay=.15, spin=40),
           shock('FFFFFF', .5, 3.2, .35, delay=.15), sparks('FFFFFF', 26, 6.5, .35, .3, delay=.14), duration=1.1)
    effect('deadeye', 'Deadeye: a giant lock-on reticle and rings close on the target, time stops, then a single lance of light '
           'pierces it - focus lines, white flash, double shock, star spray',
           quad('reticle', 'F0FAFF', .6, 4.0, 1.2, spin=160), quad('ring', 'FFFFFF', .5, 3.4, .6),
           quad('magic_circle_c', 'D0F0FF', .6, 3.0, 1.0, spin=-120),
           quad('speed_lines', 'FFFFFF', .4, 6.0, 3.0, delay=.4),
           quad('arrow_streak', 'FFFFFF', .3, 6.0, height=1.0, rotation=75, delay=.45),
           flash('FFFFFF', 1.0, 3.6, .2, delay=.5), shock('E8F8FF', .6, 4.4, .4, delay=.5),
           seal('shockwave', 'D8F0FF', .6, life=.6, end=6.0, spin=0, delay=.5),
           burst('star4', 'FFFFFF', 24, life=.7, size=.36, speed=5.0, delay=.5), sparks('E0F6FF', 30, 7.0, .4, .32, delay=.5),
           duration=1.6)
    effect('arrow_rain', 'Arrow rain: a seal opens in the sky and a dense rain of arrows falls over the whole group, '
           'ground glints, dust kicks, wide ring',
           seal('magic_circle_b', 'E8F8FF', 4.0, life=1.6, spin=60, y=3.2),
           emitter('arrow_rain', 'F0FAFF', 110, .45, 1.4, -11.0, 3.2, y=3.0, upright=True, delay=.1),
           emitter('star4', 'FFFFFF', 40, .25, .5, .3, 3.2, y=FLOOR, delay=.35),
           emitter('smoke_sheet', 'D8D0C0', 12, .6, .7, 1.0, 3.2, y=FLOOR, tiles=4, alpha=True, delay=.35),
           ground_ring('FFFFFF', .6, 7.4, .6, delay=.4), duration=1.7)
    effect('piercing_gale', 'Piercing gale: a drilling spiral of wind and arrows tears straight through the group - wind funnel '
           'on its side, long streaks, focus lines, leaves and sparks',
           quad('tornado', 'F0FFF8', .9, 2.4, 3.4, height=8.0, rotation=90),
           quad('speed_lines', 'F0FFF8', .5, 6.0, 7.0),
           emitter('arrow_streak', 'F0FAFF', 30, .3, 2.6, 0, 2.6, y=.2, upright=True, delay=.05),
           layer('arc', 'slash_strip', 'FFFFFF', life=.3, size=4.6, endSize=6.0, rotation=170, delay=.1),
           flash('FFFFFF', 1.0, 3.2, .18, delay=.1),
           burst('leaf', 'D8FFD8', 24, life=1.0, size=.3, speed=5.0, gravity=.2, radius=1.0, delay=.1),
           burst('spark', 'F0FFFF', 40, life=.4, size=.32, speed=7.0, radius=1.2, delay=.1), duration=1.5)
    effect('crow_swarm', 'Crow swarm: a murder of crows circles the group in a dark whirl, diving and pecking, black feathers rain, '
           'dark smoke',
           quad('swirl', '9070D0', 1.6, 2.0, 5.0, horizontal=True, y=FLOOR + .1, spin=-200),
           quad('glow', '6040A0', 1.4, 3.0, 4.0, y=.6),
           layer('orbit', 'crow', 'A098B0', life=1.6, size=.8, radius=2.6, spin=200, count=8, y=1.0, alpha=True),
           layer('orbit', 'crow', 'B0A8C0', life=1.6, size=.7, radius=1.6, spin=-260, count=6, y=.3, alpha=True),
           burst('crow', '9890A8', 14, life=1.2, size=.7, speed=4.0, radius=1.4, y=.6, alpha=True, delay=.2),
           emitter('feather', '807890', 30, 1.4, .3, -.8, 3.0, y=2.4, alpha=True, delay=.2),
           smoke('201820', 10, .8, 1.3, 1.0, radius=2.0, delay=.3),
           burst('spark', 'FFFFFF', 30, life=.3, size=.28, speed=5.0, radius=1.6, delay=.35), duration=1.8)
    effect('gale_dance', 'Gale dance: green wind seal, gusting wind arcs whirl around the target from all sides, leaf storm, sparks',
           seal('magic_circle_b', 'C8FFD0', 3.6, life=1.6, spin=80),
           quad('tornado', 'E8FFF0', 1.4, 2.0, 2.6, height=4.0, y=1.0),
           layer('arc', 'slash_strip', 'E8FFE8', life=.3, size=3.0, endSize=4.0, rotation=30, delay=.1, spin=200),
           layer('arc', 'slash_strip', 'D8FFD8', life=.3, size=2.6, endSize=3.6, rotation=210, delay=.3, spin=-200),
           layer('arc', 'slash_strip', 'F0FFF0', life=.3, size=3.2, endSize=4.2, rotation=120, delay=.5, spin=200),
           layer('orbit', 'leaf', 'C8FFC0', life=1.4, size=.36, radius=1.6, spin=320, count=10, y=.2),
           burst('leaf', 'B8F8A8', 24, life=1.0, size=.28, speed=4.0, gravity=.2, delay=.5),
           burst('spark', 'F0FFF0', 24, life=.4, size=.3, speed=6.0, radius=.8, delay=.5), duration=1.6)
    effect('phantom_raid', 'Phantom raid: shadow clones vanish in violet smoke and strike from every side - criss-crossing blade '
           'arcs, X-slash, sparks and drifting phantom smoke',
           smoke('201030', 12, .8, 1.0, 1.0, radius=.8),
           layer('arc', 'slash_strip', 'D8B8FF', life=.22, size=2.4, endSize=3.2, rotation=20, delay=.1),
           layer('arc', 'slash_strip', 'E8D8FF', life=.22, size=2.4, endSize=3.2, rotation=160, delay=.2),
           layer('arc', 'slash_strip', 'C8A0FF', life=.22, size=2.6, endSize=3.4, rotation=280, delay=.3),
           layer('arc', 'slash_strip', 'E0C8FF', life=.22, size=2.6, endSize=3.4, rotation=100, delay=.4),
           quad('slash_cross', 'E8D8FF', .3, 2.0, 3.6, delay=.5), flash('F0E0FF', .7, 2.4, .16, delay=.52),
           sparks('D0A8FF', 30, 6.0, .35, .3, delay=.5), smoke('180828', 8, 1.6, 1.0, .9, delay=.55), duration=1.6)
    effect('poison_hit', 'Poison hit: a toxic splash - green droplets and bubbles burst out, sickly smoke puff, falling specks',
           flash('E8FFD0', .45, 1.6, .14), quad('glow_hard', 'B8F080', .4, .6, 1.6),
           burst('droplet', 'A8E070', 18, life=.8, size=.24, speed=3.6, gravity=1.0, alpha=True),
           burst('bubble', 'D0FFB0', 14, life=1.0, size=.3, speed=1.6, gravity=-.3),
           smoke('90C060', 8, 1.0, 1.1, .9, radius=.3, delay=.05), embers('C8F0A0', 10, 1.0, .8, gravity=.2), duration=1.2)
    effect('acid_spit', 'Acid spit: corrosive yellow-green glob splatters, sizzling droplets, hissing smoke and armour-melting fizz',
           flash('F0FFC0', .5, 1.8, .14), quad('explosion_sheet', 'E0F0A0', .6, 1.0, 2.0, tiles=4),
           burst('droplet', 'C8E860', 24, life=.9, size=.26, speed=4.0, gravity=1.2, alpha=True),
           emitter('bubble', 'E0FFA0', 20, .7, .2, 1.2, .5, y=-.4),
           smoke('B0C870', 10, 1.2, 1.2, .9, radius=.4, delay=.05, gravity=-.1),
           layer('orbit', 'arrow_down', 'E0F0A0', life=.9, size=.36, radius=.8, spin=-120, count=3, y=.4, delay=.2), duration=1.3)
    effect('venom_rain', 'Venom downpour: a sickly seal in the sky rains green arrows and toxic drops, the floor boils with miasma '
           'and bubbles',
           seal('magic_circle_d', 'E0FFD0', 4.0, life=1.6, spin=60, y=3.2),
           emitter('arrow_rain', 'D8FFB0', 70, .45, 1.3, -10.0, 3.2, y=3.0, upright=True, delay=.1),
           emitter('droplet', 'B0E070', 50, .5, .3, -8.0, 3.2, y=3.0, upright=True, alpha=True, delay=.15),
           emitter('smoke_sheet', 'C8F0A0', 16, 1.2, 1.6, .7, 3.2, y=FLOOR + .2, tiles=4, alpha=True, delay=.3),
           emitter('bubble', 'E0FFC0', 40, 1.0, .3, 1.4, 3.2, y=FLOOR, delay=.3),
           ground_ring('A8E070', .6, 7.0, .7, delay=.35), duration=1.8)
    effect('spore_burst', 'Poison spores: puffballs burst across the group in clouds of green spores, drifting motes and bubbles',
           seal('magic_circle_b', 'E0FFD0', 5.6, life=1.6, spin=30),
           burst('smoke_sheet', 'D0F0A0', 20, life=1.2, size=1.6, speed=2.6, radius=1.8, y=-.4, tiles=4, alpha=True),
           emitter('dot', 'E0FFB0', 60, 1.4, .14, .8, 3.2, y=FLOOR),
           emitter('bubble', 'F0FFE0', 30, 1.0, .26, 1.2, 3.0, y=FLOOR),
           smoke('B8E098', 12, 1.0, 1.4, 1.2, radius=2.2, delay=.2), duration=1.8)
    effect('sleep_hit', 'Sleep: soft pastel puff, drowsy Zzz drifting up, circling little stars, bubbles',
           smoke('E0E4FF', 8, .6, 1.1, .9, radius=.3), quad('glow', 'E0E8FF', .8, .6, 1.8),
           emitter('zzz', 'D8E0FF', 4, 1.2, .5, .9, .3, y=.3, alpha=True, upright=True),
           layer('orbit', 'star4', 'F0F0FF', life=1.2, size=.3, radius=.8, spin=120, count=4, y=.8),
           emitter('bubble', 'F0F0FF', 10, 1.0, .24, .8, .6, y=-.4), duration=1.4)
    # ---- melee ------------------------------------------------------------------------------------
    effect('strong_hit', 'Strong blow: big hit spark, heavy crescent, shock ring, floor ring, dust and spark spray',
           flash('FFF4E0', .7, 2.4, .16), quad('slash_arc', 'FFF8E8', .28, 2.4, 3.2, height=1.3, rotation=-35, delay=.02),
           shock('FFE8C0', .5, 3.0, .35, delay=.03), ground_ring('E8D0A0', .4, 3.0, .45),
           smoke('C8B898', 8, 1.6, .8, .7, radius=.3, y=-.6, gravity=.1),
           sparks('FFE8B8', 22, 5.0, .34, .3), embers('FFD08A', 12, 1.8, .6, gravity=.4, delay=.05), duration=1.0)
    effect('stun_slam', 'Stunning slam: crushing blow - hit spark, shock rings, dust, then dizzy stars circle the head',
           flash('FFF0D8', .8, 2.6, .17), shock('FFE8C0', .5, 3.0, .36), ground_ring('E8D0A0', .4, 3.4, .5),
           smoke('C8B898', 12, 1.8, .9, .8, radius=.3, y=-.6, gravity=.1),
           burst('rock', 'A89878', 10, life=.8, size=.2, speed=3.6, gravity=1.2, y=-.4, alpha=True),
           layer('orbit', 'star5', 'FFE890', life=1.1, size=.34, radius=.6, spin=260, count=4, y=.9, delay=.15, alpha=True),
           burst('star4', 'FFF0B0', 12, life=.6, size=.3, speed=3.0, delay=.05), duration=1.4)
    effect('twin_slash', 'Twin slash: two crossing crescents in quick succession, double hit spark, steel sparks',
           layer('arc', 'slash_strip', 'FFFFFF', life=.2, size=1.8, endSize=2.6, rotation=200),
           quad('slash_arc', 'E8F6FF', .25, 2.6, 3.2, height=1.3, rotation=-30, delay=.02),
           layer('arc', 'slash_strip', 'FFFFFF', life=.2, size=1.8, endSize=2.6, rotation=-20, delay=.1),
           quad('slash_arc', 'E8F6FF', .25, 2.6, 3.2, height=1.3, rotation=150, delay=.12),
           flash('FFFFFF', .45, 1.6, .13, delay=.03), flash('FFFFFF', .45, 1.6, .13, delay=.13),
           sparks('E8F7FF', 22, 4.6, .32, .28, delay=.03), duration=.9)
    effect('cleave_sweep', 'Cleave: one huge horizontal crescent sweeps across the whole row, trailing echo, spark spray, floor ring',
           layer('arc', 'slash_strip', 'FFFFFF', life=.28, size=5.6, endSize=7.4, rotation=185),
           quad('slash_arc', 'F0F8FF', .32, 6.6, 8.0, height=2.0, rotation=-8, delay=.05),
           layer('arc', 'slash_strip', 'E0F0FF', life=.3, size=5.0, endSize=6.8, rotation=190, delay=.1),
           flash('FFFFFF', 1.0, 3.6, .16, delay=.05),
           burst('spark', 'F0FFFF', 40, life=.45, size=.32, speed=7.0, radius=1.6, delay=.08),
           seal('ring', 'FFFFFF', 1.0, life=.6, end=7.4, spin=0), duration=1.2)
    effect('harvest_reap', 'Harvest scythe: a giant reaping scythe arc swings low across the group, cut leaves and chaff fly, '
           'dark green slash echo',
           layer('arc', 'slash_strip', 'E8FFD8', life=.3, size=5.0, endSize=6.8, rotation=200),
           quad('slash_arc', 'D8F0C0', .35, 6.0, 7.6, height=1.6, rotation=8, y=-.4, delay=.05),
           flash('F0FFE0', .9, 3.0, .16, delay=.05),
           burst('leaf', 'C8E890', 30, life=1.1, size=.3, speed=5.0, gravity=.3, radius=1.4, delay=.08),
           burst('spark', 'F0FFE0', 30, life=.4, size=.3, speed=6.0, radius=1.4, delay=.08),
           seal('ring', 'E8FFD8', 1.0, life=.6, end=6.6, spin=0), duration=1.3)
    effect('bleed_slash', 'Bleeding edge: a red-edged crescent cut, blood spray and drops, crimson hit spark',
           layer('arc', 'slash_strip', 'FFE0E0', life=.22, size=1.8, endSize=2.6, rotation=200),
           quad('slash_arc', 'FFC0C0', .28, 2.6, 3.2, height=1.3, rotation=-28, delay=.03),
           flash('FFE8E8', .5, 1.8, .15, delay=.03),
           burst('droplet', 'FF4050', 22, life=.8, size=.22, speed=4.0, gravity=1.2, delay=.04, alpha=True),
           sparks('FFB0B0', 16, 4.0, .3, .26, delay=.03), duration=1.0)
    effect('power_break', 'Power break: crushing downward cut, the foe\'s strength shatters - hit spark, falling chevrons, red '
           'shards and a weakening shock',
           layer('arc', 'slash_strip', 'FFFFFF', life=.22, size=1.8, endSize=2.6, rotation=230),
           flash('FFF0F0', .6, 2.2, .16, delay=.02), shock('F0C8FF', .4, 2.6, .35, delay=.04),
           burst('square', 'E0B0FF', 18, life=.8, size=.24, speed=3.6, gravity=1.0, delay=.05),
           layer('orbit', 'arrow_down', 'E8C8FF', life=1.0, size=.42, radius=.8, spin=-120, count=4, y=.6, delay=.1),
           quad('skull_wisp', 'E0C8FF', .8, .8, 1.3, y=.9, delay=.15),
           emitter('ember', 'D8B0FF', 20, .8, .1, -1.6, .7, y=1.0, delay=.1), duration=1.3)
    effect('armor_break', 'Armor break: hit spark, the guard shell shatters into flying plates, anger mark, shock and falling '
           'chevrons',
           flash('FFFFFF', .7, 2.4, .16), layer('sphere', 'hex', 'FFD8A0', life=.25, size=2.0, endSize=2.6),
           quad('crest', 'FFE0B0', .45, 1.2, 1.8, y=.2, delay=.02),
           burst('square', 'FFD8A0', 36, life=.9, size=.26, speed=5.0, gravity=1.0),
           shock('FFE0B0', .5, 3.0, .38), ground_ring('FFC080', .4, 3.2, .5),
           layer('orbit', 'arrow_down', 'FFD0A0', life=1.0, size=.4, radius=.8, spin=-120, count=3, y=.6, delay=.15), duration=1.3)
    effect('whirlwind', 'Whirlwind frenzy: spinning blade rings whirl around the group like a cyclone, wind funnel, gusting '
           'crescents, leaves and sparks',
           layer('arc', 'slash_strip', 'FFFFFF', life=.9, size=5.0, endSize=6.0, rotation=0, spin=720, horizontal=True, y=-.2),
           layer('arc', 'slash_strip', 'E8FFF8', life=.9, size=4.0, endSize=5.0, rotation=180, spin=720, horizontal=True, y=.4, delay=.1),
           layer('arc', 'slash_strip', 'F0FFF8', life=.9, size=3.2, endSize=4.4, rotation=90, spin=-720, horizontal=True, y=1.0, delay=.2),
           quad('tornado', 'F0FFF8', 1.2, 2.4, 3.2, height=5.0, y=1.4),
           layer('arc', 'slash_strip', 'FFFFFF', life=.25, size=4.6, endSize=6.0, rotation=190, delay=.3),
           layer('orbit', 'leaf', 'E0FFE0', life=1.4, size=.34, radius=2.4, spin=400, count=10, y=.2),
           burst('spark', 'F0FFFF', 40, life=.45, size=.32, speed=7.0, radius=1.6, delay=.2),
           seal('ring', 'FFFFFF', 1.0, life=.6, end=7.0, spin=0), duration=1.6)
    effect('crimson_slash', 'Crimson frenzy hit: blood-red crescent, claw rake, crimson hit spark and blood spray',
           layer('arc', 'slash_strip', 'FFE0E0', life=.2, size=2.0, endSize=2.8, rotation=200),
           quad('claw', 'FFC0C0', .28, 1.8, 2.6, rotation=15, delay=.04),
           flash('FFE0E0', .55, 2.0, .15, delay=.03),
           burst('droplet', 'FF4050', 16, life=.7, size=.2, speed=4.0, gravity=1.1, delay=.04, alpha=True),
           sparks('FFA0A0', 18, 5.0, .32, .28, delay=.03), duration=.9)
    effect('cataclysm', 'Cataclysm: the earth splits open - giant crack seal and shockwaves, a pillar of rock and dust explodes upward, '
           'boulders fly, crimson-orange flash, rolling dust',
           seal('magic_circle_d', 'FFB080', 7.4, life=2.0, spin=-25), quad('speed_lines', 'FFD0A0', .5, 7.0, 4.0),
           seal('shockwave', 'FFE0C0', .8, life=.8, end=10.0, spin=0, delay=.2), ground_ring('FFB070', .8, 9.0, .8, delay=.2),
           quad('explosion_sheet', 'FFD8B0', .9, 3.0, 6.0, tiles=4, delay=.2), pillar('FFC090', 3.0, 7.0, .7, delay=.2),
           flash('FFF0D8', 1.8, 5.6, .22, delay=.2),
           emitter('rock', 'A08870', 80, 1.0, .5, 7.0, 3.4, y=FLOOR, gravity=1.6, alpha=True, delay=.2),
           emitter('smoke_sheet', 'C0A888', 20, 1.2, 1.8, 2.0, 3.4, y=FLOOR + .2, tiles=4, alpha=True, delay=.25),
           embers('FFB060', 60, 4.0, 1.4, .15, delay=.25, gravity=-.3, radius=2.0), duration=2.3)
    effect('twin_bite', 'Twin bite: two fang-marks snap shut on the target, blood spray, impact spark',
           quad('bite', 'FFE0E0', .3, 1.8, 2.4, y=.2), flash('FFE8E8', .5, 1.8, .14, delay=.05),
           burst('droplet', 'FF4050', 16, life=.7, size=.2, speed=3.6, gravity=1.1, delay=.06, alpha=True),
           sparks('FFC0C0', 14, 4.0, .3, .24, delay=.05), duration=.9)
    effect('tentacle_crush', 'Tentacle crush: dark tentacles burst up and slam down - thorny tendrils, heavy hit spark, ink splash, '
           'shock ring and dust',
           burst('thorn', '503070', 10, life=.9, size=1.4, speed=1.2, radius=.6, y=-.5, alpha=True),
           flash('F0E0FF', .8, 2.6, .17, delay=.1), shock('E0C8FF', .5, 3.2, .38, delay=.1), ground_ring('C0A0E0', .4, 3.4, .5, delay=.1),
           burst('droplet', '302040', 20, life=.8, size=.26, speed=4.0, gravity=1.2, alpha=True, delay=.1),
           smoke('302838', 10, 1.6, .9, .8, radius=.3, y=-.6, gravity=.1, delay=.1), duration=1.3)
    effect('root_bind', 'Root bind: thorned roots erupt from the ground and coil around the target, leaves, a binding ring tightens',
           seal('magic_circle_b', 'D0F0B0', 2.4, life=1.2, spin=60),
           burst('thorn', '608040', 12, life=1.1, size=1.3, speed=.8, radius=.7, y=-.6, alpha=True),
           layer('orbit', 'thorn', '709050', life=1.1, size=.8, radius=.7, spin=200, count=4, y=-.1, alpha=True, delay=.1),
           ground_ring('C8F0A0', 2.6, .8, .6, delay=.1), burst('leaf', 'B8E890', 14, life=1.0, size=.24, speed=2.4, gravity=.2),
           smoke('A89870', 6, 1.2, .8, .7, radius=.3, y=-.6, gravity=.1), duration=1.3)
    effect('vine_lash', 'Vine lash: whipping green vine crescents lash the target, thorny snap, leaves and sap droplets',
           layer('arc', 'slash_strip', 'D8FFC0', life=.22, size=2.2, endSize=3.2, rotation=200),
           layer('arc', 'slash_strip', 'C0F0A0', life=.22, size=2.0, endSize=3.0, rotation=20, delay=.1),
           quad('thorn', '80A060', .5, .8, 1.6, rotation=-60, alpha=True, delay=.05),
           flash('F0FFE0', .5, 1.8, .14, delay=.05),
           burst('leaf', 'B8E890', 20, life=1.0, size=.26, speed=3.6, gravity=.2, delay=.05),
           burst('droplet', 'A0D070', 10, life=.7, size=.16, speed=3.0, gravity=1.0, alpha=True, delay=.06), duration=1.0)
    effect('sandstorm', 'Sandstorm: a tan dust funnel swirls over the group, driving sand and grit, blinding dust clouds',
           quad('tornado', 'F0D8A8', 1.8, 3.0, 3.6, height=5.0, y=1.4),
           emitter('smoke_sheet', 'D8C090', 20, 1.4, 1.6, .9, 3.4, y=FLOOR + .2, tiles=4, alpha=True),
           layer('orbit', 'smoke_sheet', 'D0B888', life=1.6, size=1.4, radius=2.4, spin=220, count=6, y=.2, tiles=4, alpha=True),
           emitter('dot', 'F0D8A0', 80, .8, .1, 2.0, 3.4, y=FLOOR),
           burst('rock', 'A89070', 20, life=1.0, size=.2, speed=5.0, gravity=.6, radius=1.4, alpha=True),
           ground_ring('E0C890', .8, 7.0, .8), duration=1.8)
    # ---- support ----------------------------------------------------------------------------------
    effect('protect', 'Protect: a blue shield crest flashes up, a hex dome closes over the ally, ring pulse and light chips',
           quad('crest', 'D8ECFF', 1.0, .8, 1.6, y=.3), layer('sphere', 'hex', 'B8E0FF', life=1.2, size=2.0, endSize=2.4, delay=.1, spin=20),
           seal('magic_circle_b', 'C8E8FF', 2.4, life=1.2, spin=40), ground_ring('E0F4FF', .4, 3.0, .5),
           glint('FFFFFF', .4, 1.6, .25, delay=.15, texture='star8'),
           burst('square', 'D0EEFF', 12, life=.6, size=.18, speed=2.4, delay=.1), duration=1.3)
    effect('blessing', 'Blessing: golden light pours down from above onto the ally, rising chevrons, halo and glint',
           emitter('light_streak', 'FFF6D8', 24, .5, .9, -6.0, .8, y=2.6, upright=True),
           pillar('FFF0C0', 1.2, 4.0, 1.0, delay=.05), quad('halo', 'FFFFFF', 1.2, .8, 1.0, horizontal=True, y=1.0, spin=90, delay=.1),
           layer('orbit', 'arrow_up', 'FFF0C0', life=1.0, size=.4, radius=.9, spin=150, count=4, y=-.1, delay=.1),
           seal('magic_circle_e', 'FFF2D0', 2.2, life=1.2, spin=60),
           glint('FFFFFF', .5, 1.6, .28, delay=.45, y=.7, texture='star8'), duration=1.4)
    effect('haste', 'Haste: wind ring spins up at the feet, speed lines rush past, fast-orbiting feathers and chevrons, wing flash',
           seal('magic_circle_b', 'E0FFF4', 2.2, life=1.0, spin=240), quad('speed_lines', 'F0FFF8', .4, 3.0, 1.6),
           layer('arc', 'slash_strip', 'E8FFF8', life=.8, size=2.0, endSize=2.4, spin=900, horizontal=True, y=-.4),
           layer('orbit', 'feather', 'F0FFF8', life=1.0, size=.32, radius=.9, spin=600, count=5, y=.2),
           layer('orbit', 'arrow_up', 'E0FFF0', life=1.0, size=.32, radius=.6, spin=-400, count=3, y=.6),
           quad('wings', 'F0FFF8', .8, 1.6, 2.2, y=.4, delay=.2), duration=1.2)
    effect('regen', 'Regen: a spiral of leaves and green crosses winds up around the ally, soft glow, sparkles',
           seal('magic_circle_b', 'E0FFE8', 2.2, life=1.4, spin=50),
           layer('orbit', 'leaf', 'D0FFD8', life=1.4, size=.32, radius=.9, spin=240, count=6, y=-.3),
           layer('orbit', 'plus', 'E8FFF0', life=1.4, size=.3, radius=.7, spin=-200, count=4, y=.5),
           emitter('plus', 'E8FFF0', 10, 1.0, .24, 1.4, .5, y=-.6), quad('glow', 'E0FFE8', .8, .7, 1.6, y=.2, delay=.2),
           embers('F0FFF4', 16, 1.0, 1.0, delay=.1, gravity=-.2), duration=1.5)
    effect('barrier', 'Barrier: rune seal, a large hexagonal dome assembles around the ally, ring pulse, chips of light',
           seal('magic_circle_c', 'C8E8FF', 2.6, life=1.4, spin=60),
           layer('sphere', 'hex', 'A8D8FF', life=1.4, size=1.4, endSize=2.6, spin=30),
           layer('sphere', 'hex', 'D0ECFF', life=.4, size=2.6, endSize=2.8, delay=.5),
           quad('ring', 'E0F4FF', .4, .8, 2.6, delay=.5), glint('FFFFFF', .4, 1.6, .25, delay=.5, texture='star8'),
           burst('square', 'D0EEFF', 14, life=.6, size=.18, speed=2.6, delay=.5), duration=1.5)
    effect('cleanse', 'Cleanse: purifying droplets and bubbles wash upward, white ring pulse, sparkle and soft glow',
           seal('magic_circle_c', 'E8FFF8', 2.2, life=1.2, spin=60), ground_ring('FFFFFF', .4, 2.8, .5),
           emitter('bubble', 'E8FFFF', 18, 1.0, .26, 1.4, .6, y=-.6), burst('droplet', 'D8F8FF', 12, life=.8, size=.2, speed=2.4, gravity=-.6, alpha=True),
           pillar('E8FFF8', 1.0, 3.6, .8, delay=.05), glint('FFFFFF', .4, 1.6, .25, delay=.3, y=.4, texture='star8'), duration=1.3)
    effect('heal_bloom', 'Heal: leaf seal blooms under the ally, green petals and crosses rise, soft pillar, sparkles',
           seal('magic_circle_b', 'E0FFE8', 2.4, life=1.2, spin=40, end=2.8),
           emitter('petal', 'E8FFE8', 14, 1.2, .2, 1.6, .7, y=FLOOR), emitter('plus', 'E8FFF0', 12, .9, .26, 1.6, .6, y=-.6),
           pillar('C8FFE0', 1.0, 3.4, 1.0, delay=.05), embers('F0FFF4', 16, 1.2, 1.0, delay=.1, gravity=-.2), duration=1.4)
    effect('greater_heal', 'Greater heal: wide blessing seal, tall heaven pillar, a bloom of petals and leaves spirals up, '
           'small wings of light and a radiant glow',
           seal('magic_circle_f', 'E0FFE8', 3.2, life=1.6, spin=30, end=3.6), ground_ring('E8FFF0', .5, 3.6, .6),
           pillar('D8FFE8', 1.8, 5.0, 1.2, delay=.05),
           layer('orbit', 'petal', 'F0FFF0', life=1.4, size=.32, radius=1.0, spin=200, count=8, y=-.2),
           emitter('leaf', 'D0FFD8', 14, 1.2, .24, 1.8, .8, y=FLOOR), emitter('plus', 'E8FFF0', 16, 1.0, .3, 1.8, .7, y=-.6),
           quad('wings', 'E8FFF0', 1.0, 1.8, 2.6, y=.5, delay=.25), quad('glow', 'E0FFE8', .8, 1.0, 2.2, y=.2, delay=.3),
           duration=1.7)
    effect('rebirth_flame', 'Rebirth flame: golden phoenix flames rise around the group and heal - warm fire seal, gentle flame '
           'tongues, phoenix wings, feathers and crosses',
           seal('magic_circle_a', 'FFE8C0', 5.6, life=1.8, spin=30),
           emitter('flame_sheet', 'FFE0A0', 16, 1.0, 1.4, 1.4, 3.0, y=FLOOR + .4, tiles=4, upright=True),
           quad('wings', 'FFD8A0', 1.4, 3.0, 4.4, y=.8, delay=.2),
           emitter('feather', 'FFE8C0', 20, 1.4, .28, -.8, 3.0, y=2.6, delay=.2),
           emitter('plus', 'E8FFF0', 20, 1.0, .3, 1.6, 3.0, y=FLOOR), emitter('ember', 'FFE0A0', 50, 1.0, .12, 2.4, 3.0, y=FLOOR),
           duration=1.9)
    effect('purify_light', 'Purifying light: white seal over the party, soft pillars of light, rising bubbles and droplets, '
           'ring pulses and sparkles',
           seal('magic_circle_c', 'F0FFF8', 6.0, life=1.8, spin=30), ground_ring('FFFFFF', .6, 7.0, .7),
           emitter('beam', 'F0FFF8', 6, .7, 2.0, 0, 2.8, y=.6, upright=True),
           emitter('bubble', 'E8FFFF', 40, 1.2, .3, 1.6, 3.0, y=FLOOR), emitter('star4', 'FFFFFF', 30, .6, .3, 1.0, 3.0, y=-.2),
           seal('glow', 'F0FFF8', 2.4, life=1.0, spin=0, end=6.0, delay=.25), duration=1.8)
    effect('sanctuary', 'Sanctuary: a holy sanctuary seal on the floor and a great halo above the party, light pillars '
           'around it, soft floor glow, green motes and crosses drift up',
           seal('magic_circle_f', 'FFF6E0', 6.4, life=2.0, spin=20), seal('magic_circle_b', 'E8FFE8', 5.0, life=2.0, spin=-30, y=FLOOR + .02),
           quad('halo', 'FFF8E0', 1.6, 3.6, 4.4, horizontal=True, y=2.4, spin=30, delay=.1),
           seal('glow', 'FFF4D8', 3.0, life=1.4, spin=0, end=6.4, delay=.2),
           emitter('beam', 'FFF8E0', 6, .8, 2.4, 0, 3.0, y=.6, upright=True, delay=.1),
           emitter('plus', 'E8FFF0', 24, 1.0, .3, 1.4, 3.0, y=FLOOR), emitter('ember', 'F0FFF0', 40, 1.0, .12, 2.0, 3.0, y=FLOOR),
           duration=2.0)
    effect('hymn_swift', 'Hymn of swiftness: musical notes and hymn glyphs whirl around the party on a gust of wind, speed lines, '
           'feathers and a wind ring',
           seal('magic_circle_b', 'E8FFF4', 5.6, life=1.8, spin=120),
           layer('orbit', 'note', 'F0FFF8', life=1.6, size=.5, radius=2.6, spin=200, count=8, y=.6, alpha=True),
           layer('orbit', 'hymn', 'E8FFF0', life=1.6, size=.5, radius=1.8, spin=-160, count=5, y=1.2),
           layer('arc', 'slash_strip', 'E8FFF8', life=1.2, size=5.0, endSize=5.6, spin=600, horizontal=True, y=-.4),
           quad('speed_lines', 'F0FFF8', .6, 5.0, 3.0), emitter('feather', 'F0FFF8', 16, 1.2, .26, 1.6, 3.0, y=FLOOR),
           duration=1.9)
    effect('protect_all', 'Protect all: a wide blue seal, shield crests circle the party and lock into a great hex dome, glint',
           seal('magic_circle_b', 'C8E8FF', 6.0, life=1.8, spin=30), ground_ring('E0F4FF', .6, 7.0, .6),
           layer('orbit', 'crest', 'D8ECFF', life=1.4, size=.8, radius=2.6, spin=90, count=6, y=.4),
           layer('sphere', 'hex', '98C8F0', life=1.4, size=6.0, endSize=6.4, delay=.35, spin=15),
           glint('FFFFFF', .8, 3.0, .3, delay=.4, texture='star8'),
           burst('square', 'D0EEFF', 24, life=.8, size=.22, speed=3.0, radius=2.0, delay=.35), duration=1.9)
    effect('iron_wall', 'Iron wall: heavy steel plates slam down around the party, a grey hex wall, crests and a dust ring',
           seal('magic_circle_a', 'E0E8F0', 6.0, life=1.8, spin=20),
           layer('orbit', 'crest', 'E8F0F8', life=1.4, size=1.0, radius=2.6, spin=30, count=8, y=.2),
           layer('sphere', 'hex', 'A8B0C0', life=1.4, size=6.2, endSize=6.0, delay=.2, spin=5),
           burst('square', 'C8D0E0', 30, life=.8, size=.3, speed=-3.0, radius=3.0, delay=.1),
           shock('E8F0FF', .6, 5.0, .4, delay=.3), smoke('C8C0B8', 10, 1.4, .9, .9, radius=2.0, y=-.6, delay=.3), duration=1.9)
    effect('war_cry_party', 'Battle cry: radial focus lines, three roaring sound waves, anger marks over the party, rising red aura '
           'flames and embers',
           quad('speed_lines', 'FFE0D0', .6, 4.0, 7.0), quad('soundwave', 'FFE8D8', .6, 1.6, 6.0),
           shock('FFD0C0', .5, 6.0, .4, delay=.05), shock('FFD0C0', .4, 5.0, .38, delay=.25),
           layer('orbit', 'anger', 'FF8070', life=1.2, size=.6, radius=2.2, spin=60, count=4, y=1.2, alpha=True),
           emitter('flame_sheet', 'FFB090', 20, .7, 1.0, 2.0, 3.0, y=FLOOR, tiles=4, upright=True),
           emitter('ember', 'FFC0A0', 50, .9, .12, 2.8, 3.0, y=FLOOR), duration=1.6)
    effect('blood_rage', 'Blood rage: crimson aura flames erupt around the warrior, blood droplets spin up, anger mark, red '
           'shock and focus lines',
           quad('speed_lines', 'FF8080', .5, 3.0, 2.0), seal('magic_circle_d', 'FF8070', 2.6, life=1.2, spin=120),
           emitter('flame_sheet', 'FF9080', 18, .7, .9, 2.4, .6, y=FLOOR, tiles=4, upright=True),
           layer('orbit', 'droplet', 'FF5060', life=1.0, size=.24, radius=.8, spin=360, count=6, y=0, alpha=True),
           quad('anger', 'FF6784', .8, 1.0, 1.4, y=1.0, delay=.1, alpha=True),
           shock('FFB0A0', .4, 3.0, .38, delay=.1), emitter('ember', 'FF7060', 40, .8, .12, 2.6, .6, y=FLOOR), duration=1.4)
    effect('provoke_roar', 'Provoking roar: sonic roar rings blast out, a huge anger mark, red focus lines and shock',
           quad('soundwave', 'FFE0D8', .5, 1.2, 4.0), quad('speed_lines', 'FFC0B0', .5, 3.0, 2.0),
           shock('FFC8B8', .4, 3.4, .38, delay=.05), shock('FFC8B8', .3, 2.8, .32, delay=.22),
           quad('anger', 'FF6784', .9, 1.0, 1.6, y=1.0, delay=.1, alpha=True),
           emitter('ember', 'FF9080', 26, .8, .1, 2.4, .5, y=FLOOR), duration=1.3)
    effect('harden', 'Harden: stone plates gather and lock onto the body, grey hex shell, dust puff',
           burst('rock', 'B0A890', 16, life=.7, size=.3, speed=-2.4, radius=1.4, alpha=True),
           layer('sphere', 'hex', 'D8D0C0', life=1.2, size=1.4, endSize=1.8, delay=.3, spin=10),
           quad('crest', 'E8E0D0', .8, .7, 1.4, y=.3, delay=.35), seal('magic_circle_a', 'E0D8C8', 2.0, life=1.2, spin=30),
           smoke('C0B8A0', 6, 1.0, .8, .7, radius=.3, y=-.6, delay=.3), duration=1.4)
    effect('abyss_wall', 'Abyss wall: a dark violet hex shell rises, void swirl at its heart, shadow smoke at the feet',
           seal('magic_circle_d', 'C8A0FF', 2.4, life=1.4, spin=-50), quad('swirl', 'A070FF', 1.2, .6, 1.8, spin=-200, y=.2),
           layer('sphere', 'hex', '9060E0', life=1.4, size=1.6, endSize=2.0, delay=.1, spin=-20),
           emitter('smoke_sheet', '201030', 6, 1.0, .8, .8, .6, y=FLOOR, tiles=4, alpha=True),
           emitter('ember', 'C8A0FF', 20, .8, .1, 1.6, .6, y=FLOOR), duration=1.5)
    effect('photosynthesis', 'Photosynthesis: sunbeams shine down, leaves unfurl and spin up, green crosses, warm glow',
           emitter('light_streak', 'FFF8D0', 18, .6, .9, -5.0, .9, y=2.6, upright=True), pillar('FFF8D0', 1.4, 4.0, 1.2),
           layer('orbit', 'leaf', 'C8FFB0', life=1.4, size=.36, radius=.9, spin=180, count=6, y=-.2),
           emitter('plus', 'E8FFE0', 12, 1.0, .24, 1.4, .6, y=-.6), quad('sunburst', 'FFF4C0', .9, .5, 1.8, y=1.4, spin=30),
           duration=1.5)
    effect('sun_aegis', 'Sun aegis: a blazing sun halo opens behind the caster, golden seal, warm sphere of light, rising embers',
           quad('sunburst', 'FFE8B0', 1.2, .8, 2.8, y=.5, spin=30), quad('halo', 'FFFFFF', 1.2, 1.2, 1.4, y=.5, spin=60),
           seal('magic_circle_f', 'FFE8B0', 2.4, life=1.4, spin=40),
           layer('sphere', 'hex', 'FFE0A0', life=1.2, size=1.8, endSize=2.0, delay=.2, spin=20),
           emitter('ember', 'FFE0A0', 30, .8, .12, 2.4, .6, y=FLOOR), duration=1.5)
    effect('hawk_eye', 'Hawk eye: a glowing eye opens above, a reticle spins down, feathers swirl, focus lines',
           quad('eye', 'E0FFF0', 1.0, .8, 1.4, y=1.2), quad('reticle', 'E8FFF4', .8, 2.4, 1.0, spin=200, y=.3, delay=.1),
           layer('orbit', 'feather', 'E8FFF0', life=1.2, size=.3, radius=.9, spin=220, count=5, y=0),
           quad('speed_lines', 'E8FFF4', .4, 2.6, 1.4, delay=.2), glint('FFFFFF', .4, 1.6, .25, delay=.4, y=1.2, texture='star8'),
           duration=1.4)
    effect('mana_focus', 'Mana focus: arcane motes stream in from all around, a seal spins up, inner glow swells, star glint',
           seal('magic_circle_e', 'E0D0FF', 2.4, life=1.4, spin=90),
           burst('dot', 'E0D0FF', 40, life=.9, size=.14, speed=-3.6, radius=2.0),
           layer('orbit', 'star4', 'F0E8FF', life=1.2, size=.26, radius=.8, spin=300, count=4, y=.2),
           quad('glow', 'E0D0FF', .9, .6, 1.8, y=.2, delay=.3), glint('FFFFFF', .5, 2.0, .28, delay=.7, y=.3, texture='star8'),
           duration=1.4)
    # ---- debuffs -----------------------------------------------------------------------------------
    effect('hunter_mark', 'Hunter\'s mark: a red lock-on reticle spins down onto the target and stamps, weak-point glint, '
           'falling chevrons',
           quad('reticle', 'FFE0D0', .7, 3.0, 1.2, spin=220, y=.2), quad('reticle', 'FFFFFF', .3, 1.2, 1.6, delay=.6, y=.2),
           glint('FFFFFF', .4, 1.8, .25, delay=.62, y=.2, texture='star8'),
           layer('orbit', 'arrow_down', 'FFD0C0', life=1.0, size=.36, radius=.8, spin=-120, count=3, y=.6, delay=.3),
           ground_ring('FFC0B0', 2.6, .8, .6), duration=1.4)
    effect('dread_stare', 'Dread stare: a giant evil eye opens over the target, dark rays, a skull wisp rises and the target '
           'is chilled with fear',
           quad('eye', 'E0C8FF', 1.2, 1.0, 2.0, y=1.4), quad('sunburst', '9060E0', .8, .6, 2.6, y=1.4, spin=-30),
           quad('skull_wisp', 'D8B8FF', .9, .8, 1.3, y=.5, delay=.3),
           smoke('201030', 8, .6, 1.1, .9, radius=.4), emitter('ember', 'C8A0FF', 16, .8, .1, -1.2, .6, y=1.0), duration=1.5)
    effect('curse_screech', 'Cursed screech: violet sound waves blast the target, silence glyph, skulls and shadow smoke',
           quad('soundwave', 'E0C8FF', .5, 1.2, 3.6), shock('D0B0FF', .4, 3.0, .38, delay=.08),
           shock('D0B0FF', .3, 2.4, .32, delay=.22), quad('silence', 'D8C0FF', .9, .8, 1.2, y=1.0, delay=.2, alpha=True),
           burst('skull_wisp', 'D8C0FF', 5, life=.9, size=.36, speed=2.2, delay=.1), smoke('2A1838', 6, .8, 1.0, .8, delay=.1),
           duration=1.3)
    effect('screech', 'Ultrasonic screech: rapid pale sound rings ripple out, blind glyph, dizzy sparkles',
           quad('soundwave', 'F0F0FF', .4, 1.0, 3.6), quad('soundwave', 'F0F0FF', .4, 1.0, 3.6, delay=.15),
           shock('E8E8FF', .3, 3.0, .35, delay=.05), shock('E8E8FF', .3, 3.0, .35, delay=.2),
           quad('blind', 'E0D8F0', .9, .8, 1.2, y=1.0, delay=.25, alpha=True),
           burst('star4', 'FFFFFF', 12, life=.6, size=.26, speed=2.6, delay=.1), duration=1.3)
    effect('ink_cloud', 'Ink cloud: a black ink burst splatters the target, inky droplets, dark cloud and a blind glyph',
           flash('E8E0F8', .5, 1.8, .14), burst('smoke_sheet', '242030', 12, life=1.2, size=1.4, speed=1.8, radius=.3, tiles=4, alpha=True),
           burst('droplet', '202028', 24, life=.9, size=.28, speed=4.0, gravity=1.0, alpha=True),
           quad('blind', 'D8D0E8', .9, .8, 1.2, y=1.0, delay=.25, alpha=True), duration=1.4)
    effect('lullaby', 'Lullaby light: a soft pastel seal, music notes float in a lazy circle, Zzz drifts up, dreamy motes',
           seal('magic_circle_b', 'E0E4FF', 2.4, life=1.4, spin=20), quad('glow', 'E8E8FF', 1.0, 1.0, 2.0, y=.3),
           layer('orbit', 'note', 'E8E8FF', life=1.4, size=.4, radius=1.0, spin=80, count=4, y=.6, alpha=True),
           emitter('zzz', 'D8E0FF', 4, 1.2, .5, .9, .3, y=.5, alpha=True, upright=True, delay=.3),
           emitter('star4', 'F0F0FF', 12, .8, .22, .8, .8, y=-.2), duration=1.6)
    effect('riddle_silence', 'Silent riddle: an upright rune circle spins before the target, glyph sigils orbit, a silence mark '
           'seals the mouth',
           quad('magic_circle_e', 'E0D8FF', 1.2, 1.4, 2.4, y=.4, spin=120),
           layer('orbit', 'hymn', 'E0D8FF', life=1.2, size=.34, radius=1.0, spin=-160, count=5, y=.4),
           quad('silence', 'E0D0FF', .9, .8, 1.3, y=1.0, delay=.3, alpha=True), shock('E0D8FF', .4, 2.6, .35, delay=.3),
           duration=1.5)
    effect('silence_hit', 'Silence: a silence glyph stamps over the target, muffled ring and drifting violet motes',
           quad('silence', 'E0D0FF', .9, .7, 1.3, y=1.0, alpha=True), shock('E0D8FF', .4, 2.6, .35, delay=.05),
           ground_ring('D0C8F0', 2.4, .8, .6), emitter('ember', 'D8C8FF', 14, .8, .1, -1.0, .6, y=1.0), duration=1.3)
    effect('silence_field', 'Silence field: a muting seal under the group, silence glyphs circle above, muffled shock ring, '
           'drifting grey-violet mist',
           seal('magic_circle_e', 'E0D8FF', 6.0, life=1.8, spin=-30),
           layer('orbit', 'silence', 'E8E0FF', life=1.6, size=.7, radius=2.6, spin=60, count=6, y=1.0, alpha=True),
           shock('E0D8FF', .8, 6.0, .4, delay=.2),
           emitter('smoke_sheet', 'C8C0E0', 10, 1.2, 1.2, .5, 3.0, y=FLOOR + .2, tiles=4, alpha=True), duration=1.8)
    # ---- arcane ultimates ------------------------------------------------------------------------------
    effect('arcana_nova', 'Akashic nova: four stacked arcane seals (floor, air, sky), motes of every colour stream into the centre, '
           'then a prismatic star goes nova - blinding flash, giant star burst, double shockwave, star spray and rising light',
           seal('magic_circle_e', 'E8D8FF', 6.6, life=2.4, spin=25), seal('magic_circle_c', 'FFFFFF', 7.6, life=2.4, spin=-40, y=FLOOR + .02),
           seal('magic_circle_a', 'F0E0FF', 3.4, life=2.0, spin=-60, y=1.6, delay=.1),
           seal('magic_circle_b', 'F8F0FF', 2.4, life=1.8, spin=90, y=3.4, delay=.2),
           burst('dot', 'F0E0FF', 50, life=.9, size=.18, speed=-6.0, radius=4.0, y=.8, delay=.1),
           layer('orbit', 'star8', 'FFFFFF', life=1.0, size=.45, radius=2.6, spin=240, count=8, y=.8, delay=.1),
           quad('glow_hard', 'FFFFFF', .8, 1.0, 4.4, y=.8, delay=.85),
           quad('sunburst', 'F0E8FF', 1.0, 1.4, 8.0, y=.8, delay=.9, spin=25),
           quad('star8', 'FFFFFF', .7, 2.0, 7.0, y=.8, delay=.9, spin=-40),
           flash('FFFFFF', 2.2, 7.0, .26, delay=.9), seal('shockwave', 'E0D0FF', .8, life=.8, end=11.0, spin=0, delay=.9),
           seal('shockwave', 'FFE8F8', .8, life=.8, end=8.0, spin=0, delay=1.1),
           burst('star4', 'FFE0F0', 30, life=1.0, size=.4, speed=8.0, radius=.8, delay=.9),
           burst('star4', 'D8F0FF', 30, life=1.0, size=.4, speed=7.0, radius=.8, delay=.95),
           emitter('light_streak', 'F0E8FF', 30, .6, 1.2, 6.0, 3.4, y=FLOOR, upright=True, delay=.95),
           embers('F0E0FF', 60, 4.0, 1.4, .14, delay=.95, gravity=-.3, radius=2.0), duration=2.6)
    rays = [('FF7070', -48), ('FFB050', -29), ('FFF070', -10), ('70FF90', 10), ('70C8FF', 29), ('B080FF', 48)]
    effect('prism_ray', 'Prism ray: a crystal prism hangs over the group and splits light into a fan of rainbow beams that rake '
           'the field, white flash, coloured star bursts',
           seal('magic_circle_e', 'FFFFFF', 5.6, life=1.8, spin=40),
           quad('ice_shard', 'FFFFFF', 1.8, 1.0, 1.2, height=2.0, y=2.6, spin=40),
           quad('glow_hard', 'FFFFFF', 1.6, .8, 1.4, y=2.6),
           *[quad('beam', c, .7, .7, height=8.0, y=1.4, rotation=r, delay=.25 + i * .05) for i, (c, r) in enumerate(rays)],
           flash('FFFFFF', 1.4, 4.6, .22, delay=.3), quad('sunburst', 'FFFFFF', .8, 1.0, 5.0, y=.4, delay=.3, spin=20),
           *[burst('star4', c, 10, life=.8, size=.34, speed=6.0, radius=1.4, delay=.35) for c, _ in rays[::2]],
           seal('shockwave', 'FFFFFF', .6, life=.6, end=8.0, spin=0, delay=.3), duration=2.0)
    effect('prism_hit', 'Prism hit: white pop with red, green and blue sparkles and a thin shock ring',
           flash('FFFFFF', .5, 1.8, .14), glint('FFFFFF', .4, 1.8, .22, texture='star8'),
           sparks('FF9090', 10, 4.6, .32, .28), sparks('90FFA0', 10, 4.6, .32, .28, delay=.03),
           sparks('90C8FF', 10, 4.6, .32, .28, delay=.06), shock('FFFFFF', .3, 2.4, .3), duration=.9)


# Close-camera size pass: the recipes authored before the signature set were ~half the size they need to read at
# ~10 m on a phone, and single-target hits get one more punch-up. Charges, fields, the rewritten ultimates and loops
# are authored at their final size.
GROW = dict(
    impact=1.6, slash=1.6, critical=1.6, spark=1.3, fire=1.6, flame=1.5, ice=1.6, ring=1.4, magic_circle=1.25,
    heal=1.35, revive=1.4, smoke=1.5, buff=1.45, debuff=1.5, guard=1.4, **{'break': 1.3}, summon=1.3, dark=1.6, holy=1.5,
    pierce=1.6, blunt=1.6, thunder=1.5, enchant=1.3, warcry=1.3, aura=1.3, blade_fire=1.5, blade_ice=1.5,
    blade_thunder=1.5, blade_holy=1.5, aegis=1.25, drain=1.5, sleep_mist=1.35, ultimate_warrior2=1.3,
    arrow=1.35, bolt_ice=1.4, bolt_holy=1.4, bolt_dark=1.4, orb_fire=1.5,
    **{k: 1.3 for k in ('area_fire', 'area_ice', 'area_thunder', 'area_holy', 'area_dark', 'area_quake', 'area_slash',
                        'area_wind', 'area_arrows', 'area_poison', 'area_heal', 'area_buff', 'area_debuff', 'area_revive')},
    **{'job_' + k: 1.35 for k in ('knight', 'paladin', 'berserker', 'warlord', 'elementalist', 'archmage', 'warlock',
                                  'abyssal', 'sniper', 'divine_archer', 'ranger', 'shadow_stalker', 'priest', 'saint',
                                  'exorcist', 'inquisitor')},
    # single-target signature hits: one more punch-up after the game-camera preview (they read at ~1 body width)
    fire_arrow_hit=1.3, ice_lance_hit=1.25, ice_arrow_hit=1.3, spark_hit=1.4, chain_spark_hit=1.3, thunder_arrow_hit=1.25,
    banish=1.2, holy_arrow_hit=1.25, light_hit=1.3, arcane_hit=1.3, void_pierce=1.3, spirit_fire_hit=1.3, shadow_stitch=1.2,
    pierce_triple=1.4, snipe_hit=1.3, poison_hit=1.4, acid_spit=1.35, sleep_hit=1.35, strong_hit=1.35, stun_slam=1.3,
    twin_slash=1.35, bleed_slash=1.35, power_break=1.3, armor_break=1.3, crimson_slash=1.35, twin_bite=1.35,
    tentacle_crush=1.3, root_bind=1.25, vine_lash=1.35, prism_hit=1.3, hunter_mark=1.2, dread_stare=1.2,
    curse_screech=1.3, screech=1.3, ink_cloud=1.3, silence_hit=1.3, phantom_raid=1.3)
SKY = 3.6   # highest anchor offset that stays on screen at the battle camera


def grow(recipe, factor):
    """Scale a recipe uniformly: sizes, radii and particle speeds; anchor offsets too (floor layers stay pinned,
    sky layers are capped at SKY); particle counts and rates densify a little so bigger effects do not look sparse."""
    for item in recipe['layers']:
        for field in ('size', 'endSize', 'height', 'radius', 'speed'):
            if field in item:
                item[field] = round(item[field] * factor, 3)
        y = item.get('y', 0)
        if y > FLOOR + .12:
            item['y'] = round(min(y * factor, max(y, SKY)), 3)
        for field in ('count', 'rate'):
            if field in item and item['kind'] != 'orbit' and item[field] > 2:
                item[field] = round(item[field] * (1 + (factor - 1) * .6)) if field == 'count' else round(item[field] * (1 + (factor - 1) * .6), 2)


# Enemy rows span up to ~10.4 m (5 lanes, 2.6 m apart), so group fields get extra floor coverage without growing
# taller: floor seals/rings, emitter/burst/orbit radii and densities widen; flat billboards widen a little.
WIDEN = {k: 1.35 for k in (
    'area_fire', 'area_ice', 'area_thunder', 'area_holy', 'area_dark', 'area_quake', 'area_slash', 'area_wind',
    'area_arrows', 'area_poison', 'area_debuff', 'sleep_mist', 'flame_wave', 'hellfire', 'inferno', 'solar_flare',
    'fire_breath', 'sun_judgment', 'blaze_rain', 'frost_nova', 'blizzard', 'freezing_tide', 'absolute_zero',
    'thunder_storm', 'indra', 'giga_slash', 'grand_cross', 'abyss_gate', 'abyss_wave', 'soul_reap', 'arrow_rain',
    'piercing_gale', 'crow_swarm', 'venom_rain', 'spore_burst', 'cleave_sweep', 'harvest_reap', 'whirlwind', 'cataclysm',
    'sandstorm', 'silence_field', 'ultimate_mage', 'ultimate_archer', 'ultimate_warrior2', 'arcana_nova', 'prism_ray',
    'job_divine_archer', 'job_warlock')}


def widen(recipe, factor):
    for item in recipe['layers']:
        flat = item.get('horizontal') or item['kind'] == 'ring'
        if flat or item['kind'] in ('quad', 'arc') and item['texture'] in ('shockwave', 'speed_lines', 'slash_strip', 'slash_arc',
                                                                           'ring', 'hit_flash', 'sunburst'):
            f = factor if flat else factor ** .5
            for field in ('size', 'endSize'):
                if field in item:
                    item[field] = round(item[field] * f, 3)
        if item['kind'] in ('burst', 'emitter', 'orbit') and 'radius' in item and item['radius'] >= .5:
            item['radius'] = round(item['radius'] * factor, 3)
            for field in ('count', 'rate'):
                if field in item and item['kind'] != 'orbit':
                    item[field] = round(item[field] * factor) if field == 'count' else round(item[field] * factor, 2)


def readable_impacts(recipe):
    """Keep the authored elemental shapes and timings, but expose the actor beneath hot billboard cores.
    Floor telegraphs, projectiles, directional slash/arrow silhouettes and ultimate coverage stay authored.
    Dense bursts use fewer small particles so phones spend less fill on overlapping glints.
    """
    for item in recipe['layers']:
        if item['kind'] == 'quad' and not item.get('horizontal') and item['texture'] in (
                'glow', 'glow_hard', 'hit_flash', 'star4', 'sunburst'):
            for field in ('size', 'endSize'):
                if field in item:
                    item[field] = round(item[field] * .82, 3)
        if item['kind'] == 'burst' and item.get('count', 0) >= 24:
            item['count'] = max(18, round(item['count'] * .8))


def main():
    battle_effects()
    ultimates()
    jobs()
    skill_effects()
    statuses_and_environment()
    charges()
    projectiles()
    signature_impacts()
    # Hand-authored recipes (aligned projectiles, looping guard/BREAK markers) live beside this script.
    for recipe in json.loads((ROOT/'Tools/vfx/effects_extra.json').read_text(encoding='utf-8'))['effects']:
        EFFECTS[recipe['key']] = recipe
    for key, factor in GROW.items():
        grow(EFFECTS[key], factor)
    for key, factor in WIDEN.items():
        widen(EFFECTS[key], factor)
    for recipe in EFFECTS.values():
        readable_impacts(recipe)
    required = {p[k] for p in json.loads((ROOT/'Assets/_Game/Resources/Data/presentation.json').read_text(encoding='utf-8'))
                for k in ('charge_vfx', 'travel_vfx', 'impact_vfx', 'area_vfx') if p.get(k)}
    missing = required - EFFECTS.keys()
    if missing:
        raise ValueError('Missing authored recipes: ' + ', '.join(sorted(missing)))
    allowed = {'kind', 'texture', 'color', 'life', 'size', 'endSize', 'height', 'speed', 'gravity', 'rate', 'radius',
               'delay', 'y', 'spin', 'rotation', 'count', 'tiles', 'alpha', 'horizontal', 'upright', 'align'}
    kinds = {'quad', 'orbit', 'burst', 'emitter', 'ring', 'sphere', 'trail', 'arc'}
    for recipe in EFFECTS.values():
        for item in recipe['layers']:
            if not (ROOT/'Assets/_Game/Resources/Vfx/Textures' / (item['texture']+'.png')).is_file():
                raise FileNotFoundError(item['texture'])
            unknown = set(item) - allowed
            if unknown or item['kind'] not in kinds:
                raise ValueError(f"{recipe['key']}: unsupported layer field/kind {unknown or item['kind']}")
            if not recipe['loop'] and item.get('delay', 0) >= recipe['duration']:
                raise ValueError(f"{recipe['key']}: layer delay {item['delay']} never starts (duration {recipe['duration']})")
    dest = ROOT/'Assets/_Game/Resources/Vfx/effects.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(dict(effects=list(EFFECTS.values())), ensure_ascii=False, indent=2), encoding='utf-8')
    print('Published', len(EFFECTS), 'authored VFX recipes; all presentation keys covered')


if __name__ == '__main__':
    main()
