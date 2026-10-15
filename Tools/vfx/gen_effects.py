"""Author resource recipes for the pooled Unity particle, mesh and trail renderer."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EFFECTS = {}


def layer(kind, texture, color, **values):
    return dict(kind=kind, texture=texture, color=color, **values)


def effect(key, description, *layers, duration=1.2, loop=False):
    EFFECTS[key] = dict(key=key, description=description, duration=duration, loop=loop, layers=list(layers))


def burst(texture, color, count=22, **values):
    return layer('burst', texture, color, count=count, life=.65, size=.22, speed=2.2, radius=.12, **values)


def circle(color, texture='magic_circle_a', size=1.6, **values):
    return layer('quad', texture, color, life=1.1, size=size, spin=60, horizontal=True, **values)


def main():
    effect('impact', 'Short radial blunt impact with a sharp contact star',
           layer('quad', 'star8', 'FFE8AF', life=.25, size=.3, endSize=1.4), burst('spark', 'FFD789', 20), duration=.8)
    effect('slash', 'Swept blade crescent and trailing steel sparks',
           layer('arc', 'slash_strip', 'D7F5FF', life=.28, size=.9, endSize=1.7, rotation=35), burst('spark', 'A1E0FF', 12), duration=.8)
    effect('critical', 'Overlapping red/gold impact star and large expansion ring',
           layer('quad', 'sunburst', 'FFAC45', life=.4, size=.3, endSize=2.4),
           layer('ring', 'trail', 'FF5364', life=.6, size=.2, endSize=2.8), burst('star4', 'FFF2BD', 28), duration=1)
    effect('spark', 'Electrical projectile core, flickering bolt sheet and ribbon trail',
           layer('quad', 'lightning_sheet', 'AADFFF', life=.6, size=.85, tiles=4),
           layer('trail', 'trail', '71BFFF', life=.25, size=.3), burst('star4', 'D3F4FF', 10), duration=.8)
    effect('fire', 'Layered fire bloom and embers around a hot projectile core',
           layer('quad', 'flame_sheet', 'FFA846', life=.7, size=1, endSize=1.8, tiles=4),
           layer('sphere', 'glow', 'FFCF6A', life=.45, size=.4, endSize=.9),
           layer('trail', 'trail', 'FF6E31', life=.22, size=.45), burst('spark', 'FFBC56', 28, gravity=.15), duration=1)
    effect('flame', 'Tall sustained flame column and drifting cinders',
           layer('quad', 'flame_sheet', 'FF963E', life=1, size=1.1, height=2.5, y=.8, tiles=4),
           layer('emitter', 'spark', 'FFC568', life=.5, size=.12, rate=35, speed=1.8, radius=.35), duration=1.5)
    effect('ice', 'Crystalline ice shards and a cold radiating snowflake seal',
           layer('quad', 'snowflake', 'D6FAFF', life=.65, size=.2, endSize=1.8, spin=45),
           burst('ice_shard', '71D9FF', 24, gravity=.3), duration=1)
    effect('ring', 'Holy seal expands with orbiting four-point motes',
           layer('ring', 'trail', 'FFF0BB', life=.7, size=.3, endSize=2.3),
           layer('orbit', 'star4', 'FFE89B', life=.8, size=.22, radius=.85, spin=180, count=6), duration=1)
    effect('magic_circle', 'Counter-rotating runic invocation rings beneath caster',
           circle('AACFFF', size=1.5), circle('F2DFAA', 'magic_circle_b', 1.9, rotation=30),
           layer('emitter', 'dot', 'BBE9FF', life=.7, size=.08, rate=20, speed=.8, radius=.6), duration=1.4)
    effect('heal', 'Emerald healing column with ascending plus glyphs',
           circle('86FFC0', 'magic_circle_c', 1.3),
           layer('emitter', 'plus', 'A5FFD2', life=.8, size=.2, rate=20, speed=1.4, radius=.45),
           layer('quad', 'beam', '74ECA7', life=.9, size=.6, height=2.5, y=.7), duration=1.5)
    effect('revive', 'Winged golden resurrection seal and rising feather burst',
           circle('FFE8AB', 'magic_circle_d', 2.2), layer('quad', 'wings', 'FFF2C5', life=1.2, size=2, endSize=2.8, y=.8),
           burst('feather', 'FFF4D5', 26), duration=1.6)
    effect('smoke', 'Soft translucent purple spore cloud with suspended poison motes',
           layer('burst', 'smoke_sheet', '8BB970', life=1, size=.7, speed=.7, count=14, radius=.4, alpha=True, tiles=4),
           layer('emitter', 'bubble', 'C4ED83', life=.6, size=.15, rate=15, speed=.6, radius=.6), duration=1.4)
    effect('buff', 'Ascending amber enhancement chevrons and expanding circle',
           layer('orbit', 'arrow_up', 'FFC86E', life=.8, size=.4, radius=.7, spin=100, count=4), circle('FFE7AC', 'magic_circle_b', 1.2), duration=1.2)
    effect('debuff', 'Descending violet weakening glyphs and dark broken seal',
           layer('orbit', 'arrow_down', 'CFA2FF', life=.8, size=.4, radius=.7, spin=-80, count=4),
           layer('quad', 'skull_wisp', 'A280C6', life=.75, size=1, y=.5), duration=1.2)
    effect('guard', 'Blue hexagonal protective ward catches incoming blows',
           layer('sphere', 'hex', '8FCEFF', life=.8, size=1.6), layer('quad', 'ring', 'D2EBFF', life=.5, size=1.2), duration=1.1)
    effect('shield', 'Sustained translucent hexagonal shield shell',
           layer('sphere', 'hex', '91D8FF', life=1.5, size=1.6, spin=15), loop=True)
    effect('break', 'Shattering blue shield fragments and red interruption marker',
           burst('square', '92D4FF', 32, gravity=.5), layer('quad', 'anger', 'FF6784', life=.75, size=1.3, endSize=1.7), duration=1.2)
    effect('summon', 'Abyssal rune portal with coiling spectral skulls',
           circle('C086FF', 'magic_circle_d', 2.4), layer('orbit', 'skull_wisp', 'DDB5FF', life=1.1, size=.5, radius=.8, spin=140, count=5),
           layer('quad', 'beam', 'AC67F2', life=1, size=1.1, height=3.5, y=1), duration=1.5)
    effect('dark', 'Dark vortex and outward spectral skulls',
           layer('quad', 'swirl', '9764E3', life=.7, size=.4, endSize=2, spin=-160), burst('skull_wisp', 'BD9DE4', 15), duration=1.1)
    effect('holy', 'Holy rays and descending radiant feather fan',
           layer('quad', 'sunburst', 'FFF3C2', life=.8, size=.3, endSize=2.8), burst('feather', 'FFEAB5', 22), duration=1.3)
    effect('pierce', 'Narrow arrow streak and focused blue hit sparks',
           layer('quad', 'arrow_streak', 'BCE8FF', life=.35, size=.8, height=1.8, rotation=70), burst('spark', 'D6F1FF', 12), duration=.8)
    effect('blunt', 'Broad earth shockwave and heavy contact dust',
           layer('ring', 'trail', 'D8BE8D', life=.5, size=.2, endSize=2.4),
           layer('burst', 'smoke_sheet', 'B5A58A', life=.7, size=.6, speed=1.8, count=15, radius=.2, alpha=True, tiles=4), duration=1.1)
    effect('thunder', 'Four branching animated lightning strikes',
           layer('quad', 'lightning_sheet', 'D7F1FF', life=.7, size=1.5, height=3, tiles=4), burst('star4', '8ABFFF', 26), duration=1.1)
    for key, texture, color in [('ultimate_warrior', 'sword', 'FFE6A0'), ('ultimate_mage', 'flame_sheet', 'FFA7DA'),
                                ('ultimate_archer', 'arrow_streak', 'B5E9FF'), ('ultimate_cleric', 'wings', 'FFFFDA')]:
        effect(key, 'Hero ultimate focal emblem, runic seal and radiant particle storm',
               layer('quad', texture, color, life=1.5, size=2.8, height=4, y=1.3, tiles=4 if texture=='flame_sheet' else 1),
               circle(color, 'magic_circle_d', 4), burst('star8', color, 64), duration=2)
    status_styles = {
        'poison': ('bubble', 'B6E86F'), 'burn': ('flame_sheet', 'FFA35D'), 'bleed': ('droplet', 'F0788D'),
        'slow': ('snowflake', '99BEF4'), 'freeze': ('ice_shard', 'B9F2FF'), 'silence': ('silence', 'D4B8EE'),
        'sleep': ('zzz', 'ABBAED'), 'blind': ('blind', 'CEB6DE'), 'stun': ('star5', 'FFE281'),
        'regen': ('plus', 'A2FFD1'), 'provoke': ('anger', 'FF987E'), 'barrier': ('hex', '9AD8FE'),
        'mana_shield': ('magic_circle_b', 'B6B2FA'), 'invincible': ('star8', 'FFF4BD')
    }
    status_families = {0: 'poison', 1: 'stun', 4: 'burn', 5: 'bleed', 6: 'slow', 7: 'freeze', 8: 'silence',
                       11: 'regen', 12: 'barrier', 13: 'provoke', 14: 'sleep', 15: 'blind', 18: 'mana_shield', 19: 'invincible'}
    statuses = json.loads((ROOT / 'Assets/_Game/Resources/Data/statuses.json').read_text(encoding='utf-8'))
    for status in statuses:
        key = status['id']
        family = status_families.get(status['effect_type'])
        if family is not None:
            texture, color = status_styles[family]
        elif status['effect_type'] in (9, 10, 17):
            texture, color = 'arrow_down', 'C3A2E4'
        else:
            texture, color = 'arrow_up', 'F7D299'
        effect('status_' + key, status.get('display_name', key) + ' persistent orbiting status glyph',
               layer('orbit', texture, color, life=1.2, size=.25, radius=.4, spin=55, count=3, y=1.2, tiles=4 if texture=='flame_sheet' else 1), loop=True)
    for key, texture, color, gravity in [('verdant_ruins', 'leaf', 'A7CE88', .015), ('frost_grotto', 'snowflake', 'DCF4FF', .01),
                                        ('ember_caverns', 'spark', 'FFD09A', -.01), ('haunted_crypt', 'skull_wisp', 'B8ABDD', 0)]:
        effect('environment_' + key, 'Local biome atmosphere drifting particles',
               layer('emitter', texture, color, life=4, size=.16, rate=6, radius=6, speed=.1, gravity=gravity, alpha=True), loop=True)
    required = {p[k] for p in json.loads((ROOT/'Assets/_Game/Resources/Data/presentation.json').read_text(encoding='utf-8'))
                for k in ('charge_vfx', 'travel_vfx', 'impact_vfx') if p.get(k)}
    missing = required - EFFECTS.keys()
    if missing:
        raise ValueError('Missing authored recipes: ' + ', '.join(sorted(missing)))
    for recipe in EFFECTS.values():
        for item in recipe['layers']:
            if not (ROOT/'Assets/_Game/Resources/Vfx/Textures'/ (item['texture']+'.png')).is_file():
                raise FileNotFoundError(item['texture'])
    dest = ROOT/'Assets/_Game/Resources/Vfx/effects.json'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(dict(effects=list(EFFECTS.values())), ensure_ascii=False, indent=2), encoding='utf-8')
    print('Published', len(EFFECTS), 'authored VFX recipes; all presentation keys covered')


if __name__ == '__main__':
    main()
