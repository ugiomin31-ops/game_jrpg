"""Reference-led layered costumes. Geometry is authored in metres, facing -Y."""
import math
from humanoid import (A, V, Humanoid, ellipsoid, sweep, lock, lathe, shell, ring, gem, decal, bvh_of,
                      diamond, fleur, cross_motif, leaf, shade, mix, chain, blend2, GRIP_DIR)
import body as B

GOLD = '#edbe62'
DARK = '#423027'
CREAM = '#fff0ce'


def orb(H, bone, name, c, r, color, seg=14, rings=8):
    return H.add(bone, ellipsoid(name, c, r, color, seg=seg, rings=rings))


def line(H, bone, name, pts, r, color):
    return H.add(bone, sweep(name, pts, r, color, seg=6))


def jewel(H, bone, c, size, color, normal=(0, -1, 0)):
    H.add(bone, *gem('jewel', c, normal, size, color, GOLD))


def motif(H, obj, bone, c, shape, color=GOLD, normal=(0, -1, 0), size=(1, 1)):
    return H.add(bone, decal('embroidery', shape, bvh_of([obj]), c, normal, color, size=size, offset=.004))


def hair(H, color, style='short'):
    B.hair_cap(H, color, front=.47, back=-.55 if style == 'short' else -.8, color_lo=shade(color, .73))
    # Swept, separated fringe locks leave both iris silhouettes readable.
    for i in range(7):
        x = -.84 + i * .26
        end = x - .10 if i < 4 else x - .26
        B.hair_lock(H, [(x * .6, -.52, .88), (x, -.98, .52), (end, -1.01, .14 + .10 * abs(x))],
                    .32, .075, mix(color, '#fff0b0', .06 * (i % 3)), out=(0, -1, .1), n=6, seg=5,
                    color_tip=shade(color, .86))
    for s in (-1, 1):
        for i in range(3):
            B.hair_lock(H, [(s * .83, -.1 + i * .2, .46), (s * 1.07, -.25 + i * .15, .02),
                            (s * (.88 + .14 * i), -.18 + i * .16, -.42 - i * .09)],
                        .25, .12, shade(color, .94), n=5, seg=5)
    if style == 'spiky':
        for i in range(6):
            a = math.radians(25 + i * 54)
            x, y = math.sin(a), math.cos(a)
            B.hair_lock(H, [(x * .55, y * .5, .65), (x * .94, y * .82, .96),
                            (x * 1.16, y * 1.0, .81 + .18 * (i % 2))], .32, .12, color, n=5, seg=5)
        B.hair_lock(H, [(-.2, .04, .95), (.12, -.03, 1.28), (.24, -.10, 1.10)], .32, .1, color, n=5, seg=5)
    if style in ('long', 'bob'):
        for s in (-1, 1):
            bn = 'hair.' + ('L' if s > 0 else 'R')
            p = B.hp(H, s * .8, .35, -.12)
            end = B.hp(H, s * .86, .44, -1.5 if style == 'long' else -.83)
            H.add_bone(bn, p, end, 'head')
            for i in range(4):
                d = .19 * i
                B.hair_lock(H, [(s * (.68 + d), .36, .18), (s * (1.16 + d * .12), .50, -.72),
                                (s * (.96 + .14 * math.sin(i)), .56, -1.64 if style == 'long' else -.9)],
                            .33, .16, mix(color, '#ffffff', .04 * i), bone=bn, n=6, seg=5,
                            color_tip=shade(color, .84))
        for i in range(5):
            x = -.7 + i * .35
            B.hair_lock(H, [(x, .7, .3), (x * 1.1, 1.03, -.45),
                            (x * 1.13, .86, -1.55 if style == 'long' else -.85)], .4, .13,
                        shade(color, .85), n=5, seg=5)
    if style == 'braids':
        for s in (-1, 1):
            bn = 'braid.' + ('L' if s > 0 else 'R')
            p = B.hp(H, s * .83, .1, -.35)
            H.add_bone(bn, p, p + V((s * .02, .01, -.24)), 'head')
            for i in range(5):
                c = p + V((s * (.015 * math.sin(i * 2)), -.006 * i, -.034 * i))
                orb(H, bn, 'braid_plait', c, (.026, .026, .032), mix(color, '#ffe3b4', .1 * (i % 2)), seg=10, rings=6)
            line(H, bn, 'braid_tie', [p + V((-.026, 0, -.145)), p + V((.026, 0, -.145))], .009, '#ba3b39')
    if style == 'bun':
        c = B.hp(H, .10, .72, .82)
        orb(H, 'head', 'hair_bun', c, (.115, .09, .115), color, seg=20, rings=12)
        H.add('head', ring('bun_ribbon', c, (0, 1, .3), .09, .012, CREAM, seg=20, minor=5))


def base(H, skin, eye, hair_color, style='short', happy=False, glasses=None, outfit='#f5e8d1', pants='#493a31',
         boot_color='#805339', boot_top=.20, gloves=None):
    B.head(H, skin=skin, eye=eye, eye_style='happy' if happy else 'open', mouth='grin' if happy else 'smile',
           brow=shade(hair_color, .58), glasses=glasses, lash_flick=not happy)
    hair(H, hair_color, style)
    B.torso(H, outfit, pants, H.j['hip'].z)
    for s in (-1, 1):
        B.arm(H, s, outfit, seg=12)
        B.hand(H, s, gloves or skin, cuff=GOLD if gloves else outfit)
        B.leg(H, s, pants, seg=12)
        B.boot(H, s, boot_color, top=boot_top, cuff=GOLD if gloves else shade(boot_color, 1.25), heel=False)


def collar(H, color, trim=GOLD):
    z = H.j['neck'].z
    o = lathe('collar', [(.042, z + .026), (.052, z + .01), (.085, z - .027), (.127, z - .055)], color,
              sy=.8, seg=24, thick=.008, caps=False)
    H.add('chest', o)
    H.add('chest', lathe('collar_trim', [(.121, z - .051), (.131, z - .064)], trim, sy=.81,
                        seg=24, thick=.006, caps=False))
    jewel(H, 'chest', (0, -.084, z - .046), (.021, .028, .014), '#30c8ed')


def cape(H, color, hem=.28, width=.22, trim=GOLD, split=False):
    z = H.j['neck'].z - .027
    H.add_bone('cape', (0, .055, z), (0, .12, hem), 'chest')
    o = B.skirt(H, z, hem, .095, width, color, sy=.8, a0=68, a1=292, seg=22,
                yshift=lambda zz: .035 + (z - zz) * .18, hem_wave=.012, waves=6, rows=6, share=0, bone='cape', name='cape')
    t = B.skirt(H, hem + .025, hem, width - .008, width + .006, trim, sy=.8, a0=68, a1=292, seg=22,
                yshift=lambda zz: .035 + (z - zz) * .18, share=0, bone='cape', rows=1, name='cape_border')
    for a in (68, 292):
        ar = math.radians(a)
        pts = []
        for i in range(7):
            q = i / 6
            r = .095 + (width - .095) * q
            zz = z + (hem - z) * q
            pts.append((math.sin(ar) * r, -math.cos(ar) * r * .8 + .035 + (z - zz) * .18, zz))
        line(H, 'cape', 'cape_edge', pts, .008, trim)
    return o


def shoulder_plate(H, s, steel='#aabed4'):
    S = 'L' if s > 0 else 'R'
    c = H.j['shoulder.' + S] + V((s * .005, -.005, .013))
    orb(H, 'upper_arm.' + S, 'pauldron_gold', c, (.075, .069, .054), GOLD)
    orb(H, 'upper_arm.' + S, 'pauldron_steel', c + V((0, -.003, .009)), (.068, .065, .049), steel)
    jewel(H, 'upper_arm.' + S, c + V((0, -.068, -.005)), (.014, .014, .009), '#45b5e6')
    for d in (-1, 1):
        orb(H, 'upper_arm.' + S, 'pauldron_rivet', c + V((d * .038, -.048, .014)), (.005, .004, .005), GOLD, 8, 5)


def tabard(H, color, hem=.24, trim=GOLD):
    top = H.j['hip'].z + .015
    for a0, a1 in ((-44, 44), (137, 223)):
        o = B.skirt(H, top, hem, .121 * H.P['girth'], .20 * H.P['girth'], color, sy=.79,
                    a0=a0, a1=a1, seg=10, hem_wave=.004, rows=4, share=.35, name='tabard')
        B.skirt(H, hem + .026, hem, .19 * H.P['girth'], .205 * H.P['girth'], trim, sy=.79,
                a0=a0, a1=a1, seg=10, rows=1, share=.35, name='tabard_hem')
        if a0 < 0:
            motif(H, o, 'hips', (0, -.18, hem + .085), fleur(.028), trim)
    for s in (-1, 1):
        ar = math.radians(s * 44)
        line(H, 'hips', 'tabard_side_trim', [(math.sin(ar) * .128, -math.cos(ar) * .128 * .79, top),
                                           (math.sin(ar) * .202, -math.cos(ar) * .202 * .79, hem)], .006, trim)


def hood(H, color, trim=GOLD):
    c, r = H.j['head_c'], H.P['head_r']
    # Opening is deliberately wide enough to show cheek and iris highlights.
    o = shell('hood', c + V((0, .02, .012)), r, color, scale=(1.19 * H.P['head_sx'], 1.19, 1.17),
              cut=lambda d: d.y < -.12 and d.z < .69, thick=.012, seg=28, rings=16)
    H.add('head', o)
    pts = [B.hp(H, *p) for p in [(-1.02, -.63, -.50), (-1.08, -.71, .12), (-.85, -.79, .60),
                                (-.45, -.88, .89), (0, -.86, 1.02), (.45, -.88, .89),
                                (.85, -.79, .60), (1.08, -.71, .12), (1.02, -.63, -.50)]]
    line(H, 'head', 'hood_gilding', pts, .014, trim)
    return o


def sash(H, color=DARK, buttons=True):
    z = H.j['hip'].z
    pts = [(-.083, -.062, z + .254), (-.060, -.083, z + .206), (0, -.094, z + .136),
           (.084, -.085, z + .055), (.119, -.041, z + .01)]
    o = sweep('crossbody_sash', pts, [(.024, .006)] * len(pts), color, seg=6, up=(0, -1, 0))
    H.add_blend(o, chain([('hips', z + .04), ('spine', z + .12), ('chest', z + .22)]))
    if buttons:
        for p in pts[1:-1]:
            orb(H, 'chest' if p[2] > z + .17 else 'spine', 'sash_stud', V(p) + V((0, -.008, 0)),
                (.004, .004, .004), GOLD, 8, 5)


def shield(H):
    c = H.j['grip.L'] + V((.058, -.031, .085))
    # Shield stays body-owned, strapped to left forearm; no hero weapon mesh.
    o = orb(H, 'forearm.L', 'shield_rim', c, (.136, .027, .182), '#adbdce', 24, 14)
    orb(H, 'forearm.L', 'shield_wood', c + V((0, -.014, 0)), (.119, .025, .160), '#965731', 24, 14)
    for x in (-.055, 0, .055):
        line(H, 'forearm.L', 'shield_plank', [c + V((x, -.040, -.129)), c + V((x, -.046, .129))], .003, '#663b28')
    orb(H, 'forearm.L', 'shield_boss_gold', c + V((0, -.045, 0)), (.052, .023, .064), GOLD)
    orb(H, 'forearm.L', 'shield_boss', c + V((0, -.059, 0)), (.039, .026, .049), '#d5e0ea')
    for i in range(12):
        a = i * math.tau / 12
        orb(H, 'forearm.L', 'shield_rivet', c + V((.126 * math.sin(a), -.024, .171 * math.cos(a))),
            (.006, .006, .006), GOLD, 8, 5)


def warrior():
    H = Humanoid('warrior', shoulder_w=.143, chest=1.10, limb=1.09, hand_scale=1.05)
    base(H, B.SKIN, '#c17e22', '#91502e', 'spiky', outfit='#8fa9c5', pants='#34323b',
         boot_color='#697a92', boot_top=.25, gloves='#714732')
    collar(H, '#d53c36', '#f47146')
    cape(H, '#be303e', hem=.24, width=.25, trim='#ec6450')
    # Sculpted cuirass / breastplate layered over the articulated torso.
    z = H.j['hip'].z
    breast = lathe('cuirass', [(.119, z + .045), (.116, z + .12), (.126, z + .2), (.111, z + .247)],
                   '#c5d6e8', sy=.84, seg=24, thick=.008, caps=False)
    H.add_blend(breast, blend2('spine', 'chest', z + .12, z + .23))
    motif(H, breast, 'chest', (0, -.116, z + .173), fleur(.04))
    B.belt(H, z + .014, '#774c32', GOLD, width=.035)
    sash(H)
    tabard(H, '#234d9e', hem=.20)
    for s in (-1, 1):
        shoulder_plate(H, s)
        S = 'L' if s > 0 else 'R'
        c = H.j['knee.' + S] + V((0, -.047, .002))
        orb(H, 'shin.' + S, 'knee_gold', c, (.047, .019, .054), GOLD)
        orb(H, 'shin.' + S, 'knee_steel', c + V((0, -.01, .002)), (.039, .015, .045), '#bacade')
        line(H, 'shin.' + S, 'greave_trim', [(c.x - .033, -.049, .12), (c.x, -.060, .21), (c.x + .033, -.049, .12)], .006, GOLD)
    B.pouch(H, (-.133, -.066, z -.055), (.085, .045, .072), '#935b36', '#b17443', button=GOLD)
    shield(H)
    return H


def mage():
    H = Humanoid('mage', shoulder_w=.12, leg=.39, girth=.94, hand_scale=.94)
    base(H, '#ffe5db', '#358ed4', '#c4b7e1', 'long', outfit='#fff0dd', pants='#5c3b3b', boot_color='#6b4435', boot_top=.25)
    z = H.j['hip'].z
    cape(H, '#3d286c', hem=.12, width=.267)
    tabard(H, '#fff3db', hem=.225)
    corset = lathe('corset', [(.102, z + .025), (.095, z + .12), (.106, z + .20)], '#63422e', sy=.85,
                   seg=24, thick=.006, caps=False)
    H.add_blend(corset, blend2('hips', 'spine', z + .06, z + .14))
    for i in range(4):
        zz = z + .045 + i * .034
        line(H, 'spine', 'corset_lace', [(-.027, -.093, zz), (.027, -.098, zz + .025)], .0038, GOLD)
        line(H, 'spine', 'corset_lace', [(.027, -.093, zz), (-.027, -.098, zz + .025)], .0038, GOLD)
    collar(H, '#493071')
    for s in (-1, 1):
        S = 'L' if s > 0 else 'R'
        a, b = H.j['elbow.' + S], H.j['wrist.' + S]
        from humanoid import along
        sleeve = along('bell_sleeve', a, b, [(.037, 0), (.047, .35), (.077, .88), (.073, 1)], '#4d347f',
                       seg=18, thick=.007, caps=False)
        H.add('forearm.' + S, sleeve)
        H.add('forearm.' + S, along('sleeve_trim', a, b, [(.078, .86), (.08, 1)], GOLD, seg=18, thick=.006, caps=False))
    B.belt(H, z + .026, '#63442f', GOLD)
    B.pouch(H, (.127, -.045, z -.02), (.072, .046, .065), '#85583b', '#a16c44', button=GOLD)
    # Broad witch brim and asymmetric drooping crown are signature silhouette.
    cz = H.j['head_c'].z + H.P['head_r'] * .67
    brim = lathe('witch_brim', [(.21, -.012), (.365, -.019), (.38, -.007), (.23, .016)], '#39285f',
                 center=(0, .016, cz), sy=.90, seg=36, thick=.008, caps=False)
    H.add('head', brim)
    H.add('head', lathe('hat_gold_edge', [(.373, -.011), (.383, -.008)], GOLD, center=(0, .016, cz),
                        sy=.90, seg=36, thick=.006, caps=False))
    H.add('head', lathe('witch_crown', [(.23, 0), (.223, .045), (.174, .14), (.113, .24), (.057, .30), (.016, .285)],
                        '#463273', center=(0, .016, cz), seg=28, xshift=lambda zz: .30 * (zz / .30) ** 3))
    H.add('head', lathe('hat_band', [(.234, .01), (.224, .06)], '#ad7847', center=(0, .016, cz), seg=28, caps=False, thick=.006))
    jewel(H, 'head', (0, -.216, cz + .040), (.028, .032, .015), '#29c5ed')
    return H


def archer():
    H = Humanoid('archer', girth=.94, chest=.94, shoulder_w=.122)
    base(H, '#ffe3c5', '#76b139', '#e2ad4e', 'short', outfit='#f4e8cb', pants='#4b4438', boot_color='#735039',
         boot_top=.255, gloves='#6b442e')
    z = H.j['hip'].z
    cape(H, '#356042', hem=.235, width=.245)
    hood(H, '#527536')
    collar(H, '#527536')
    vest = lathe('forest_vest', [(.102, z), (.108, z + .08), (.109, z + .19), (.089, z + .245)],
                 '#506447', sy=.84, seg=24, thick=.008, caps=False)
    H.add_blend(vest, chain([('hips', z), ('spine', z + .10), ('chest', z + .20)]))
    sash(H)
    B.belt(H, z + .01, '#765034', GOLD)
    tabard(H, '#4e6c3d', hem=.29)
    B.pouch(H, (-.13, -.062, z -.018), (.081, .045, .070), '#825636', '#9c6c40', button=GOLD)
    # Empty leather quiver: no bow/arrows embedded in hero weapon-free mesh.
    from humanoid import cyl
    p0, p1 = V((-.11, .105, z + .03)), V((-.15, .145, z + .33))
    H.add('chest', cyl('quiver', p0, p1, .035, .045, '#71492f', seg=16))
    H.add('chest', ring('quiver_rim', p1, p1 - p0, .044, .006, GOLD, seg=18, minor=5))
    for s in (-1, 1):
        S = 'L' if s > 0 else 'R'
        c = H.j['knee.' + S] + V((0, -.048, 0))
        jewel(H, 'shin.' + S, c, (.025, .034, .009), '#bc8f46')
    return H


def cleric():
    H = Humanoid('cleric', girth=.93, leg=.385, shoulder_w=.116, hand_scale=.93)
    base(H, '#ffe3d5', '#c86346', '#e69aa8', 'bob', outfit=CREAM, pants='#ffe3d5', boot_color='#795140', boot_top=.23)
    z = H.j['hip'].z
    cape(H, '#a73a49', hem=.17, width=.25)
    hood(H, '#fff0cf')
    collar(H, '#fff1d8')
    dress = B.skirt(H, z + .035, .23, .112, .195, CREAM, sy=.83, seg=24, hem_wave=.008, rows=5, share=.35)
    B.skirt(H, .257, .228, .19, .201, GOLD, sy=.83, rows=1, share=.35, seg=24)
    for s in (-1, 1):
        ar = math.radians(s * 56)
        line(H, 'hips', 'dress_piping', [(s * .07, -.08, z + .024), (s * .155, -.095, .24)], .006, GOLD)
    motif(H, dress, 'hips', (0, -.164, .29), cross_motif(.025))
    # Red stole hangs as two independent cloth panels over ivory dress.
    for s in (-1, 1):
        pts = [(s * .073, -.055, z + .235), (s * .084, -.11, z + .11), (s * .132, -.139, .18)]
        bn = 'stole.' + ('L' if s > 0 else 'R')
        H.add_bone(bn, pts[0], pts[-1], 'chest')
        H.add(bn, sweep('stole', pts, [(.025, .006), (.029, .006), (.04, .006)], '#b3414c', seg=6, up=(0, -1, 0)))
        line(H, bn, 'stole_trim', [V(p) + V((s * .023, -.006, 0)) for p in pts], .0055, GOLD)
        S = 'L' if s > 0 else 'R'
        from humanoid import along
        a, b = H.j['elbow.' + S], H.j['wrist.' + S]
        H.add('forearm.' + S, along('white_bell_sleeve', a, b, [(.037, 0), (.05, .5), (.065, 1)],
                                  CREAM, seg=16, thick=.007, caps=False))
        H.add('forearm.' + S, along('cleric_cuff', a, b, [(.066, .86), (.068, 1)], GOLD, seg=16, thick=.006, caps=False))
    B.belt(H, z + .017, '#7a5438', GOLD)
    B.pouch(H, (-.128, -.040, z -.03), (.071, .040, .066), '#89623c', '#a17c4b', button=GOLD)
    return H


NPCS = {
    'innkeeper': dict(skin='#ffe1cc', eye='#a06b34', hair='#a0653f', style='bun', happy=True, outfit='#fff0d6',
                      pants='#764735', boot_color='#74513c', girth=1.17, leg=.38, torso=.31),
    'shopkeeper': dict(skin='#ffe3c9', eye='#b67d2c', hair='#b78750', style='braids', outfit='#f7e9cc',
                       pants='#5c4d38', boot_color='#71533d', girth=.94, leg=.36, head_r=.229),
    'smith': dict(skin='#e7ae7c', eye='#4cabb6', hair='#b9602e', style='short', outfit='#ede2c9',
                  pants='#4a3930', boot_color='#533b30', girth=1.33, chest=1.17, limb=1.2, shoulder_w=.165,
                  leg=.35, torso=.32, hand_scale=1.15),
    'guild_clerk': dict(skin='#ffe1c8', eye='#6b9d41', hair='#654332', style='spiky', glasses=GOLD,
                        outfit='#fff1d6', pants='#3b465e', boot_color='#644832', girth=.92, leg=.40),
    'elder': dict(skin='#f2cfb1', eye='#829085', hair='#e4e1d7', style='short', happy=True, outfit='#516542',
                  pants='#d7c6a3', boot_color='#66543e', girth=1.06, leg=.36, torso=.29, neck=.035),
    'villager_a': dict(skin='#efc09b', eye='#87634d', hair='#48352a', style='short', outfit='#b37b40',
                       pants='#42534a', boot_color='#654333', girth=1.08, leg=.40),
    'villager_b': dict(skin='#ffe1d0', eye='#548795', hair='#7f4931', style='braids', outfit='#fff0d5',
                       pants='#8f5363', boot_color='#80543a', girth=.97, leg=.37),
    'villager_c': dict(skin='#ffe2b8', eye='#799d53', hair='#bf8437', style='short', outfit='#5992a0',
                       pants='#705844', boot_color='#815f41', girth=.91, leg=.29, torso=.245, head_r=.215,
                       shoulder_w=.11, upper_arm=.115, forearm=.10, hand_scale=.85, foot_scale=.85),
}


def apron(H, color, hem=.17):
    z = H.j['hip'].z
    o = B.skirt(H, z + .02, hem, .128 * H.P['girth'], .175 * H.P['girth'], color, a0=-57, a1=57,
                seg=14, sy=.8, share=.3, rows=4, name='apron')
    # Pocket and stitching provide medium scale readable detailing.
    B.pouch(H, (0, -.133 * H.P['girth'], z -.12), (.115, .012, .06), shade(color, .88), button=GOLD)
    for s in (-1, 1):
        line(H, 'chest', 'apron_strap', [(s * .059, -.081, z + .025), (s * .069, -.077, z + .225),
                                      (s * .085, -.022, z + .27)], .012, color)
    return o


def beard(H, color, long=False):
    for i in range(7):
        x = -.6 + i * .2
        B.hair_lock(H, [(x, -.79, -.49), (x * 1.15, -.9, -.90),
                        (x * .62, -.78, -1.55 if long else -1.21)], .32, .11, mix(color, '#ffffff', .03 * (i % 3)),
                    out=(0, -1, 0), n=5, seg=5)
    for s in (-1, 1):
        B.hair_lock(H, [(0, -.92, -.37), (s * .35, -1.02, -.39), (s * .68, -.85, -.34)],
                    .17, .1, color, out=(0, -1, 0), n=5, seg=5)


def npc(name):
    cfg = dict(NPCS[name])
    keys = set(__import__('humanoid').DEFAULT)
    H = Humanoid(name, **{k: cfg.pop(k) for k in list(cfg) if k in keys})
    base(H, cfg.pop('skin'), cfg.pop('eye'), cfg.pop('hair'), cfg.pop('style'), **cfg)
    z = H.j['hip'].z
    if name == 'innkeeper':
        B.skirt(H, z + .025, .11, .13, .22, '#963b3a', sy=.82, seg=26, hem_wave=.009, share=.25)
        B.skirt(H, .13, .108, .212, .226, '#fff0d6', sy=.82, rows=1, seg=26, share=.25)
        apron(H, '#efdfb7', .15)
        # Frilled maid headband follows forehead and does not cover eyes.
        pts = [B.hp(H, math.sin(a) * .87, -.20, math.cos(a) * .96) for a in [i * math.pi / 12 - math.pi / 2 for i in range(13)]]
        line(H, 'head', 'headband', pts, .022, CREAM)
        for p in pts[1:-1]:
            orb(H, 'head', 'headband_frill', p + V((0, -.007, .007)), (.024, .025, .025), '#fff7df', 10, 6)
        B.belt(H, z + .015, '#633b2b', GOLD)
    elif name == 'shopkeeper':
        tabard(H, '#557257', .24)
        vest = lathe('merchant_vest', [(.113, z), (.104, z + .16), (.078, z + .24)], '#526c58', sy=.84,
                     seg=22, thick=.006, caps=False)
        H.add_blend(vest, blend2('hips', 'chest', z + .05, z + .20))
        B.belt(H, z + .017, '#744d32', GOLD)
        for s in (-1, 1):
            B.pouch(H, (s * .123, -.056, z -.025), (.063, .042, .071), '#96653c', '#ba8b51', button=GOLD)
        cz = H.j['head_c'].z + .17
        H.add('head', ellipsoid('merchant_beret', (0, .025, cz), (.27, .24, .13), '#4c6254', seg=26, rings=14))
        H.add('head', ring('beret_band', (0, .01, cz -.075), (0, 0, 1), .227, .014, CREAM, seg=28, minor=5,
                           scale=(1.06, .9, 1)))
        jewel(H, 'head', (-.15, -.187, cz -.025), (.018, .018, .01), '#f0c671')
        collar(H, '#b94a3d', '#d99155')
    elif name == 'smith':
        beard(H, '#b86330')
        apron(H, '#6b4030', .16)
        B.belt(H, z + .015, '#412f26', GOLD, r=.15)
        c = H.j['head_c'] + V((0, .012, .085))
        band = lathe('smith_bandanna', [(.25, -.026), (.246, .042)], '#a74039', center=c, sy=.94,
                     seg=28, thick=.007, caps=False)
        H.add('head', band)
        motif(H, band, 'head', c + V((0, -.235, .003)), fleur(.027), '#efcf83')
        for s in (-1, 1):
            B.pouch(H, (s * .16, -.040, z -.04), (.063, .042, .084), '#52392b', '#825035', button=GOLD)
        # Belt tongs rather than held hammer keep gestures unobstructed.
        for s in (-1, 1):
            line(H, 'hips', 'belt_tongs', [(.151 + s * .008, .002, z + .012), (.148 + s * .012, -.017, z -.135)],
                 .006, '#8c9298')
    elif name == 'guild_clerk':
        vest = lathe('guild_waistcoat', [(.113, z + .005), (.10, z + .13), (.106, z + .22), (.084, z + .25)],
                     '#2d4b7d', sy=.85, seg=24, thick=.008, caps=False)
        H.add_blend(vest, chain([('hips', z + .02), ('spine', z + .12), ('chest', z + .21)]))
        for i in range(4):
            orb(H, 'spine', 'guild_buttons', (.017, -.095, z + .025 + .037 * i), (.005, .005, .005), GOLD, 8, 5)
        collar(H, '#b44136', CREAM)
        sash(H, '#76503b', False)
        B.pouch(H, (.13, -.036, z -.03), (.08, .041, .096), '#7c5436', '#aa794d', button=GOLD)
        jewel(H, 'chest', (-.055, -.096, z + .19), (.013, .017, .009), '#42baea')
    elif name == 'elder':
        B.skirt(H, z + .027, .105, .124, .18, '#60704d', sy=.83, seg=24, share=.16)
        B.skirt(H, .13, .104, .17, .189, GOLD, sy=.83, rows=1, seg=24, share=.16)
        cape(H, '#384f37', hem=.18, width=.225)
        hood(H, '#526741')
        beard(H, '#e4e1d6', True)
        B.belt(H, z + .01, '#806548', GOLD)
        B.pouch(H, (-.131, -.018, z -.075), (.058, .042, .077), '#8e7551', '#ad9269', button=GOLD)
    elif name == 'villager_a':
        apron(H, '#806240', .22)
        B.belt(H, z + .01, '#5c412c', GOLD)
        sash(H, '#526344')
        cz = H.j['head_c'].z + .17
        H.add('head', lathe('farmer_hat', [(.19, 0), (.30, -.018), (.304, -.005), (.21, .016), (.205, .07), (.16, .14), (0, .16)],
                            '#d3b573', center=(0, .015, cz), sy=.93, seg=28))
        H.add('head', lathe('farmer_hat_band', [(.211, .02), (.206, .055)], '#66553b', center=(0, .015, cz), seg=28,
                            sy=.93, caps=False, thick=.005))
    elif name == 'villager_b':
        B.skirt(H, z + .02, .14, .115, .205, '#9c5566', sy=.83, seg=24, hem_wave=.01, share=.25)
        B.skirt(H, .16, .137, .197, .212, '#e3b491', sy=.83, seg=24, rows=1, share=.25)
        apron(H, '#e4c8a5', .21)
        B.belt(H, z + .02, '#795039', GOLD)
        for s in (-1, 1):
            p = B.hp(H, s * .87, -.05, -.28)
            orb(H, 'head', 'braid_bow', p, (.027, .016, .018), '#bb6c7c')
        collar(H, '#eadac1', '#ae7950')
    else:
        B.belt(H, z + .02, '#78553a', GOLD, width=.025, r=.107)
        collar(H, '#e6be71', '#cc873f')
        B.pouch(H, (.116, -.036, z -.025), (.063, .035, .065), '#946a3c', '#b68b52', button=GOLD)
        # Little explorer's tied scarf / cloth cap.
        c = H.j['head_c']
        H.add('head', ellipsoid('child_cap', c + V((0, .033, .135)), (.225, .218, .117), '#547d87', seg=24, rings=12))
        H.add('head', ellipsoid('child_cap_brim', c + V((0, -.174, .107)), (.173, .092, .017), '#426573', seg=18, rings=8))
    return H


HERO_BUILDERS = {'warrior': warrior, 'mage': mage, 'archer': archer, 'cleric': cleric}
