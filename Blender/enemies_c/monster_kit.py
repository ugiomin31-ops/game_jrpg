"""Kit for the v2 monster roster (enemies_c): the enemies_a `Creature` builder plus
surface-aware anime faces, gems, petals and a richer seven-clip animator.

Conventions are those of creature_kit: the creature stands on z=0 and faces -Y, every bone
points +Z, `Motion` keys rotations in world axes (+ax = top tips forward, +ay = top leans to
the creature's left (+X), +az = turns its face toward +X). Parts are rigidly bound to one bone.

Bone names the animator understands (anything else is only moved by its parent or `extra`):
  root, body, head, eyes (blink pivot = eye centre), jaw, crest, lid (hinged lid/jaw that opens up),
  arm.L/R, leg.L/R, leg.FL/FR/BL/BR (quadruped), legN.L/R (crawler, N = 1..4 front to back),
  wing.L/R, wing2.L/R, tail1..tailN, antenna.L/R, ear.L/R, orbit* (spins about Z),
  flame* (flicker), cape (sway), weapon.R/L (held items; follow the arm).
Kinds: biped, heavy, quad, crawler, fly (wings), float (no wings, hovers), hop (no legs, bounces).
"""
import json
import math
import os
import sys

import bpy  # noqa: E402  (must precede bmesh when running as the bpy module)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'enemies_a'))
from creature_kit import Creature, CLIPS, Motion, A  # noqa: E402
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
import creature_face as F  # noqa: E402
from mathutils import Vector  # noqa: E402

PREVIEWS = [('', 'Idle', 0, (70, 0, 25)), ('_side', 'Idle', 0, (80, 0, 90)), ('_attack', 'Attack', 10, (75, 0, 35)),
            ('_cast', 'Cast', 21, (70, 0, 25)), ('_die', 'Die', 30, (65, 0, 35))]

INK = '#1b1326'


def hexmix(a, b, t):
    ca, cb = A._as_rgba(a), A._as_rgba(b)
    return tuple(ca[i] * (1 - t) + cb[i] * t for i in range(3)) + (1.0,)


class Head:
    """Ellipsoid used to place face features exactly on its front surface."""

    def __init__(self, center, radii):
        self.c = Vector(center)
        self.r = Vector(radii)

    def point(self, x, z, out=0.0):
        """Front (-Y) surface point at world x, z, pushed `out` metres along the normal."""
        dx, dz = (x - self.c.x) / self.r.x, (z - self.c.z) / self.r.z
        u = min(dx * dx + dz * dz, 0.97)
        y = self.c.y - self.r.y * math.sqrt(1.0 - u)
        p = Vector((x, y, z))
        n = self.normal(p)
        return p + n * out, n

    def normal(self, p):
        d = p - self.c
        return Vector((d.x / self.r.x ** 2, d.y / self.r.y ** 2, d.z / self.r.z ** 2)).normalized()

    def bvh(self):
        """Surface the painted face decals are projected onto (built once)."""
        if getattr(self, '_bvh', None) is None:
            self._bvh = F.ellipsoid_bvh(self.c, self.r)
        return self._bvh

    @property
    def k(self):
        """Decal offset scale relative to a hero head (radius 0.235 m)."""
        return max(0.4, min(self.r.x, self.r.z) / 0.235)


class Monster(Creature):
    def __init__(self, eid):
        super().__init__(eid)
        self.elite = eid.startswith('elite_')

    # ------------------------------------------------------------ placement helpers
    def orb(self, bone, name, point, radii, color, mat='M_Toon', seg=None, rings=None):
        """Ellipsoid with a segment count scaled to its size (keeps small parts cheap)."""
        big = max(radii)
        if seg is None:
            seg, rings = (22, 12) if big > .17 else (16, 8) if big > .08 else (12, 6) if big > .035 else (8, 5)
        return super().orb(bone, name, point, radii, color, mat, seg=seg, rings=rings or max(5, seg // 2))

    def disc(self, bone, name, p, n, size, color, mat='M_Toon', seg=14, rings=7, roll=0.0):
        """Flattened ellipsoid (w, depth, h) whose thin axis follows normal n (outward)."""
        o = A.sphere(name, r=1, loc=tuple(p), scale=size, color=color, mat=mat, seg=seg, rings=rings)
        q = Vector(n).to_track_quat('-Y', 'Z')
        if roll:
            from mathutils import Quaternion
            q = q @ Quaternion((0, 1, 0), math.radians(roll))
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = q
        return self.add(bone, o)

    def chunk(self, bone, name, point, radii, color, mat='M_Toon', seed=1, seg=8, rings=6, jitter=.12):
        """Faceted, flat-shaded rock/ice chunk: a low-poly ellipsoid with deterministic vertex jitter."""
        import random
        rnd = random.Random(seed)
        o = A.sphere(name, r=1, loc=point, scale=radii, color=color, mat=mat, seg=seg, rings=rings)
        for v in o.data.vertices:
            k = 1 + rnd.uniform(-jitter, jitter)
            v.co *= k
        for p in o.data.polygons:
            p.use_smooth = False
        return self.add(bone, o)

    def aim(self, o, direction, up='Z'):
        """Rotate an object built along +Z so that +Z follows direction."""
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = Vector(direction).to_track_quat('Z', 'Y' if up == 'Z' else up)
        return o

    def cone_to(self, bone, name, base, tip, r, color, mat='M_Toon', seg=10, r2=0.0):
        base, tip = Vector(base), Vector(tip)
        o = A.cyl(name, r=r, depth=(tip - base).length, loc=tuple((base + tip) / 2), r2=r2, color=color, mat=mat, seg=seg)
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = (tip - base).to_track_quat('Z', 'Y')
        return self.add(bone, o)

    def stubby_leg(self, bone, name, hip, foot, r, color, foot_color=None, lift=.04):
        """Short chunky leg (two soft segments) ending in a round foot ball. Used instead of thin jointed
        arthropod legs, which read as creepy at battle-camera distance."""
        hip, foot = Vector(hip), Vector(foot)
        knee = hip.lerp(foot, .5) + Vector((0, 0, lift))
        self.tube(bone, name, [tuple(hip), tuple(knee), tuple(foot)], r, color, taper=.85)
        self.orb(bone, name + '_knee', tuple(knee), (r * 1.08, r * 1.08, r * 1.08), color)
        self.orb(bone, name + '_foot', (foot.x, foot.y - r * .25, max(foot.z, r * .8)), (r * 1.25, r * 1.4, r * .95),
                 foot_color or color)

    def gem(self, bone, name, base, direction, r, h, light, dark, mat='M_Emit', sides=6):
        """Faceted bipyramid crystal from base along direction, two-tone facets, flat shaded."""
        prof = [(0.0, -h * 0.12), (r, h * 0.1), (r * 0.82, h * 0.7), (0.0, h)]
        o = A.lathe(name, prof, color=light, mat=mat, seg=sides)
        for p in o.data.polygons:
            p.use_smooth = False
        attr = o.data.color_attributes['Col']
        for p in o.data.polygons:
            k = (math.atan2(p.normal.y, p.normal.x) / math.tau + 1.0) % 1.0
            shade = 0.5 + 0.5 * math.cos(math.tau * (k - 0.15))
            if p.center.z > h * 0.7:
                shade = min(1.0, shade + 0.3)
            c = hexmix(dark, light, shade)
            for li in p.loop_indices:
                attr.data[li].color_srgb = c
        o.location = base
        self.aim(o, direction)
        return self.add(bone, o)

    def petal(self, bone, name, base, direction, length, width, color, tip=None, mat='M_Toon', thick=0.018, cup=0.25, n=7):
        """Cupped petal/leaf/feather blade from base along direction (built in XZ then aimed)."""
        pts = []
        for i in range(n + 1):
            t = i / n
            w = width * 0.5 * math.sin(math.pi * min(1.0, t ** 0.75)) ** 0.9
            pts.append((w, t * length))
        outline = pts + [(-x, z) for x, z in reversed(pts[1:-1])]
        o = A.extrude_shape(name, outline, depth=thick, color=color, mat=mat)
        # cup: bend the blade so its edges curl toward -Y (the outward face)
        for v in o.data.vertices:
            v.co.y -= cup * (abs(v.co.x) / max(width * 0.5, 1e-4)) ** 2 * width * 0.5
            v.co.y += 0.25 * cup * (v.co.z / length) ** 2 * length * 0.4
        if tip:
            attr = o.data.color_attributes['Col']
            for p in o.data.polygons:
                t = max(0.0, min(1.0, p.center.z / length))
                c = hexmix(color, tip, max(0.0, (t - 0.45) / 0.55))
                for li in p.loop_indices:
                    attr.data[li].color_srgb = c
        o.location = base
        o.rotation_mode = 'QUATERNION'
        d = Vector(direction).normalized()
        o.rotation_quaternion = d.to_track_quat('Z', 'Y')
        return self.add(bone, o)

    def flame(self, bone, name, base, height, r, outer='#ff7a1f', inner='#ffe36a', lean=(0, 0), seg=10):
        """Two-layer emissive flame tongue (lathe teardrop) leaning by (dx, dy) at the tip."""
        prof = [(0.0, -r * 0.4), (r * 0.8, 0.0), (r, height * 0.18), (r * 0.7, height * 0.5), (r * 0.25, height * 0.82), (0.0, height)]
        o = A.lathe(name, prof, color=outer, mat='M_Emit', seg=seg)
        i = A.lathe(name + '_in', [(x * 0.55, z * 0.72) for x, z in prof], color=inner, mat='M_Emit', seg=seg)
        for ob in (o, i):
            for v in ob.data.vertices:
                t = max(0.0, v.co.z / height)
                v.co.x += lean[0] * t * t
                v.co.y += lean[1] * t * t
            ob.location = base
            self.add(bone, ob)
        i.location = (base[0], base[1] - r * 0.35, base[2])
        return o

    # ------------------------------------------------------------ faces
    # Faces are painted like the heroes' (creature_face.py): flat decals on the head, toon iris with a soft
    # gradient, two tiny highlights. No bulging discs, ink rings or glowing irises.
    def anime_eye(self, bone, head, x, z, w, h, iris, iris_lo, side, angry=0.0, lash=True, glow=True,
                  sclera='#fdfaf7', pupil=None, tag='', lid_color=None, slit=False):
        """Hero-style eye on `head` (Head). w, h are half-sizes; side=+1 creature's left (+X).
        angry 0..1 tilts a brow; lid_color paints a heavy upper lid. `glow` is ignored (irises never glow)."""
        p, _ = head.point(x, z, 0.0)
        n = head.normal(p)
        parts = F.eye(f'eye{tag}{side:+d}', head.bvh(), p, n, w * 1.7, h * 1.7, iris, iris_lo, side=side, k=head.k,
                      pupil=pupil, sclera=sclera, lash_weight=1.0 if lash else 0.6, slit=slit, angry=angry, lid=lid_color)
        for o in parts:
            self.add(bone, o)

    def eye_pair(self, bone, head, z, spacing, w, h, iris, iris_lo, **kw):
        for s in (-1, 1):
            self.anime_eye(bone, head, head.c.x + s * spacing, z, w, h, iris, iris_lo, s, **kw)

    def glow_eyes(self, bone, head, z, spacing, w, h, color, slant=0.0, tag=''):
        """Glowing slit eyes for helmets, skulls and elementals (flat, painted on)."""
        for s in (-1, 1):
            p, _ = head.point(head.c.x + s * spacing, z, 0.0)
            for o in F.glow_eye(f'gloweye{tag}{s:+d}', head.bvh(), p, head.normal(p), w * 2, h * 2, color,
                                slant=-s * slant, k=head.k):
                self.add(bone, o)

    def blush(self, bone, head, z, spacing, w=0.05, color='#f29aa4'):
        for s in (-1, 1):
            p, _ = head.point(head.c.x + s * spacing, z, 0.0)
            for o in F.blush(f'blush{s:+d}', head.bvh(), p, head.normal(p), w * 1.6, color, k=head.k):
                self.add(bone, o)

    def open_mouth(self, bone, head, z, w, h, fangs=None, tongue='#e0707e', inner='#5a1a24', tag=''):
        p, _ = head.point(head.c.x, z, 0.0)
        for o in F.mouth_open('mouth' + tag, head.bvh(), p, head.normal(p), w * 2, h * 2, inner, tongue, k=head.k):
            self.add(bone, o)
        if fangs:
            for s in (-1, 1):
                a, _ = head.point(head.c.x + s * w * 0.55, z + h * 0.62, 0.004)
                b, _ = head.point(head.c.x + s * w * 0.5, z + h * 0.1, 0.01)
                self.spike(bone, f'fang{tag}{s:+d}', tuple(a), tuple(b), w * 0.16, fangs)

    def cat_mouth(self, bone, head, z, w, color=INK, tag=''):
        """Small closed mouth line."""
        p, _ = head.point(head.c.x, z, 0.0)
        for o in F.mouth_line('wmouth' + tag, head.bvh(), p, head.normal(p), w * 2, color, k=head.k):
            self.add(bone, o)

    # ------------------------------------------------------------ animation
    def animate(self, kind='biped', extra=None):
        rig = A.armature(self.bones)
        names = set(self.parts)
        flying = kind in ('fly', 'float')
        heavy = kind == 'heavy'
        tails = sorted(n for n in names if n.startswith('tail'))
        for clip, length in CLIPS.items():
            with Motion(rig, clip, length) as a:
                frames = {round(i * length / 12) for i in range(13)}
                frames.add(round(length * .4) if clip == 'Attack' else round(length * .6) if clip == 'Cast' else 0)
                for i, f in enumerate(sorted(frames)):
                    t = f / length
                    wave = math.sin(math.tau * t)
                    pulse = math.sin(math.pi * t)
                    hit = max(0.0, 1 - abs(t - .4) / .16)
                    wind = max(0.0, 1 - abs(t - .2) / .16)
                    release = max(0.0, 1 - abs(t - .6) / .2)
                    recoil = max(0.0, 1 - abs(t - .22) / .22)
                    fall = min(1.0, max(0.0, (t - .12) / .6))
                    fall = fall * fall * (3 - 2 * fall)
                    # ---------------- root & body
                    if clip == 'Idle':
                        a.l('root', f, (0, 0, .035 * wave if flying else 0))
                        if 'body' in names:
                            br = .025 if kind != 'heavy' else .015
                            a.s('body', f, (1 + br * wave, 1 + br * wave, 1 - br * wave))
                            if flying:
                                a.r('body', f, (3 * wave, 0, 2 * math.sin(math.tau * t + 1)))
                    elif clip == 'Run':
                        if kind in ('hop', 'biped', 'heavy') and not flying:
                            a.l('root', f, (0, 0, (.07 if kind == 'hop' else .045) * abs(math.sin(math.tau * t))))
                        elif kind in ('quad', 'crawler'):
                            a.l('root', f, (0, 0, .02 * abs(math.sin(math.tau * t * 2))))
                        else:
                            a.l('root', f, (0, 0, .04 * math.sin(math.tau * t * 2)))
                        if 'body' in names:
                            a.r('body', f, (10 if not flying else 14, 0, 4 * wave if kind == 'biped' else 0))
                        if kind == 'hop' and 'body' in names:
                            sq = math.cos(math.tau * t * 2)
                            a.s('body', f, (1 + .06 * sq, 1 + .06 * sq, 1 - .08 * sq))
                    elif clip == 'Attack':
                        a.l('root', f, (0, .09 * wind - .32 * hit, (.10 if flying else .03 if kind != 'hop' else .12) * hit))
                        if 'body' in names:
                            a.r('body', f, (-14 * wind + 26 * hit, 0, -10 * wind + 6 * hit))
                    elif clip == 'Cast':
                        a.l('root', f, (0, 0, (.12 * pulse) if flying else .03 * release))
                        if 'body' in names:
                            a.r('body', f, (-10 * pulse + 8 * release, 0, 0))
                            a.s('body', f, (1 + .05 * release, 1 + .05 * release, 1 + .04 * release))
                    elif clip == 'Hit':
                        a.l('root', f, (0, .14 * recoil, 0))
                        if 'body' in names:
                            a.r('body', f, (-24 * recoil, 9 * recoil, 0))
                            a.s('body', f, (1 + .06 * recoil, 1 + .06 * recoil, 1 - .07 * recoil))
                    elif clip == 'Die':
                        if kind == 'float':
                            # sinks backwards to the floor and fades smaller
                            a.r('root', f, (-80 * fall, 0, 20 * fall))
                            a.s('root', f, (1 - .3 * fall, 1 - .3 * fall, 1 - .3 * fall))
                        elif flying:
                            a.r('root', f, (84 * fall, 0, -10 * fall))
                            a.l('root', f, (0, .12 * fall, 0))
                        elif kind == 'crawler' or kind == 'quad':
                            a.r('root', f, (0, 86 * fall, 0))
                            a.l('root', f, (.1 * fall, 0, .06 * fall))
                        else:
                            a.r('root', f, (-84 * fall, 0, 10 * fall))
                            a.l('root', f, (0, .16 * fall, .07 * fall))
                    elif clip == 'Victory':
                        jump = abs(math.sin(math.tau * t * 1.5))
                        a.l('root', f, (0, 0, (.06 if heavy else .12) * jump))
                        if 'body' in names:
                            a.r('body', f, (0, 6 * wave, 14 * math.sin(math.tau * t)))
                    if 'head' in names:
                        if clip == 'Idle':
                            a.r('head', f, (3 * math.sin(math.tau * t + .7), 4 * wave, 0))
                        elif clip == 'Cast':
                            a.r('head', f, (-18 * pulse, 0, 0))
                        elif clip == 'Hit':
                            a.r('head', f, (-16 * recoil, -6 * recoil, 0))
                        elif clip == 'Victory':
                            a.r('head', f, (-12 * pulse, 10 * wave, 0))
                        elif clip == 'Attack':
                            a.r('head', f, (-10 * wind + 14 * hit, 0, 0))
                    # ---------------- appendages
                    for name in names:
                        side = 1 if name.endswith('L') else -1
                        if name.startswith(('wing.', 'wing2.')):
                            amp = 26 if clip == 'Idle' else 42
                            speed = 3 if clip == 'Run' else 2
                            ph = .25 if name.startswith('wing2') else 0.0
                            flap = amp * math.sin(math.tau * (t * speed + ph))
                            if clip == 'Die':
                                flap = -60 * fall
                            elif clip == 'Cast':
                                flap = 55 * pulse + 15 * math.sin(math.tau * t * 3)
                            elif clip == 'Victory':
                                flap = 45 * math.sin(math.tau * t * 3)
                            a.r(name, f, (0, side * flap, side * 10 * pulse))
                        elif name.startswith('tentacle'):
                            ph = int(name.replace('tentacle', '')) * .62
                            sway = math.sin(math.tau * t + ph) - math.sin(ph)
                            a.r(name, f, (18 * sway, 12 * sway, 5 * sway))
                        elif name.startswith('arm.'):
                            ax, ay = 0.0, 0.0
                            weapon = name == 'arm.R'
                            if clip == 'Idle':
                                ax = 5 * math.sin(math.tau * t + (0 if weapon else .5))
                            elif clip == 'Run':
                                ax = (-30 if not heavy else -18) * side * wave
                            elif clip == 'Attack':
                                if weapon:
                                    ax = -120 * wind - 30 * hit
                                    ay = 20 * wind * side
                                else:
                                    ax = -40 * hit
                            elif clip == 'Cast':
                                ax = -100 * pulse
                                ay = 28 * pulse * side
                            elif clip == 'Hit':
                                ax = 25 * recoil
                                ay = 25 * recoil * side
                            elif clip == 'Die':
                                ax = 35 * fall
                                ay = 30 * fall * side
                            elif clip == 'Victory':
                                ax = -150 * pulse * (1 if weapon else .8)
                                ay = 10 * side * wave
                            a.r(name, f, (ax, ay, 0))
                        elif name.startswith('leg'):
                            if name in ('leg.L', 'leg.R'):
                                ph = 0 if side > 0 else .5
                                if clip == 'Run':
                                    a.r(name, f, ((-34 if not heavy else -20) * math.sin(math.tau * (t + ph)), 0, 0))
                                elif clip == 'Die':
                                    a.r(name, f, (-25 * fall, 0, 0))
                                elif clip == 'Victory':
                                    a.r(name, f, (-12 * pulse * (1 if side > 0 else 0), 0, 0))
                                elif clip == 'Attack':
                                    a.r(name, f, (-18 * hit * (1 if side < 0 else -.4), 0, 0))
                                else:
                                    a.r(name, f, (0, 0, 0))
                            elif name[4:5] in ('F', 'B'):
                                front = name[4] == 'F'
                                ph = (0 if (front == (side > 0)) else .5)
                                if clip == 'Run':
                                    a.r(name, f, (-38 * math.sin(math.tau * (t + ph)), 0, 0))
                                elif clip == 'Attack':
                                    a.r(name, f, ((-30 if front else 20) * wind + (25 if front else -15) * hit, 0, 0))
                                elif clip == 'Die':
                                    a.r(name, f, (0, side * 30 * fall, 0))
                                elif clip == 'Victory':
                                    a.r(name, f, ((-28 if front else 0) * abs(math.sin(math.tau * t * 1.5)), 0, 0))
                                elif clip == 'Idle':
                                    a.r(name, f, (2 * wave, 0, 0))
                                else:
                                    a.r(name, f, (0, 0, 0))
                            else:  # crawler legN.S
                                try:
                                    k = int(name[3:name.index('.')])
                                except ValueError:
                                    k = 1
                                ph = ((k + (0 if side > 0 else 1)) % 2) * .5
                                if clip == 'Run':
                                    sw = math.sin(math.tau * (t * 2 + ph))
                                    a.r(name, f, (0, side * 14 * max(0, math.cos(math.tau * (t * 2 + ph))), side * 22 * sw))
                                elif clip == 'Idle':
                                    a.r(name, f, (0, side * 3 * math.sin(math.tau * (t + k * .2)), 0))
                                elif clip == 'Die':
                                    a.r(name, f, (0, side * (-45) * fall, 0))
                                elif clip == 'Attack':
                                    a.r(name, f, (0, side * (12 * wind) * (1 if k == 1 else .3), 0))
                                elif clip == 'Victory':
                                    a.r(name, f, (0, side * 18 * abs(math.sin(math.tau * (t * 2 + ph))), 0))
                                elif clip == 'Hit':
                                    a.r(name, f, (0, side * 15 * recoil, 0))
                                else:
                                    a.r(name, f, (0, side * 8 * pulse, 0))
                        elif name.startswith('tail'):
                            idx = tails.index(name)
                            lag = idx * .12
                            amp = 18 if clip != 'Die' else 4
                            if clip == 'Run':
                                amp = 26
                            sway = math.sin(math.tau * (t - lag) * (2 if clip == 'Run' else 1))
                            a.r(name, f, (6 * math.sin(math.tau * (t - lag)), 0, amp * sway))
                        elif name.startswith('antenna.'):
                            a.r(name, f, (10 * math.sin(math.tau * t * 2 + side), side * 8 * math.sin(math.tau * t * 3), 0))
                        elif name.startswith('ear.'):
                            tw = 1 if (clip == 'Idle' and i in (4, 5)) else 0
                            if clip == 'Hit':
                                tw = recoil
                            a.r(name, f, (-15 * tw, side * 12 * tw + (side * -20 * fall if clip == 'Die' else 0), 0))
                        elif name == 'jaw':
                            open_ = 22 * pulse if clip in ('Cast', 'Victory') else 28 * hit + 8 * wind if clip == 'Attack' else 3 * wave
                            a.r(name, f, (open_, 0, 0))
                        elif name == 'lid':
                            if clip == 'Attack':
                                ang = -60 * wind - 10 * hit
                            elif clip in ('Cast', 'Victory'):
                                ang = -45 * pulse
                            elif clip == 'Idle':
                                ang = -10 * max(0, math.sin(math.tau * t * 2))
                            elif clip == 'Hit':
                                ang = -25 * recoil
                            elif clip == 'Die':
                                ang = -70 * fall
                            else:
                                ang = -18 * abs(math.sin(math.tau * t * 2))
                            a.r(name, f, (ang, 0, 0))
                        elif name.startswith('orbit'):
                            spin = {'Idle': 1, 'Run': 2, 'Cast': 2, 'Victory': 2}.get(clip, 0)
                            a.r(name, f, (0, 0, 360 * spin * t))
                        elif name.startswith('flame'):
                            k = 1 + .12 * math.sin(math.tau * t * 4 + len(name)) + (.35 * release if clip == 'Cast' else 0)
                            if clip == 'Die':
                                k = max(.05, 1 - fall)
                            a.s(name, f, (1 + .5 * (k - 1), 1 + .5 * (k - 1), k))
                        elif name == 'cape':
                            a.r(name, f, (-6 - 6 * abs(wave) if clip == 'Run' else -3 * wave, 0, 3 * math.sin(math.tau * t + .3)))
                        elif name == 'eyes' and clip in ('Idle', 'Hit', 'Die'):
                            blink = .1 if (clip == 'Idle' and i == 9) or (clip == 'Hit' and i in (2, 3)) or (clip == 'Die' and i > 7) else 1
                            a.s(name, f, (1, 1, blink))
                    if extra:
                        extra(a, clip, f, t, i, names)
        sizes = sorted(((sum(len(p.vertices) - 2 for p in o.data.polygons), o.name) for ps in self.parts.values() for o in ps), reverse=True)
        print('TRI_TOP ' + ', '.join(f'{n}:{t}' for t, n in sizes[:10]), flush=True)
        body = self.skin(rig)
        return rig, body

    def skin(self, rig):
        """Join every part into the skinned Body (rigid one-bone parts). Sculpted kits override this."""
        return A.skin(self.parts, rig)

    def finish(self, kind='biped', extra=None, previews=PREVIEWS):
        rig, body = self.animate(kind, extra)
        A.volume_shade(body)  # same grounded, solid read as the heroes
        tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
        if not all(name in bpy.data.actions for name in CLIPS):
            raise RuntimeError('Missing creature action')
        mats = [m.name for m in body.data.materials]
        if any(m not in A.MATERIALS for m in mats):
            raise RuntimeError(f'Unexpected materials {mats}')
        rig.animation_data.action = bpy.data.actions['Idle']
        bpy.context.scene.frame_set(0)
        path = A.export_fbx(f'Enemies/{self.eid}/{self.eid}.fbx', [rig, body], animated=True)
        A.save_blend('enemy_' + self.eid)
        for suffix, clip, frame, angle in previews:
            A.render_preview('enemy_' + self.eid + suffix, objects=[rig, body], action=clip, frame=frame, angle=angle, size=480)
        dims = [round(v, 3) for v in body.dimensions]
        manifest = {'id': self.eid, 'fbx': path, 'triangles': tris, 'bones': list(self.parts), 'dimensions': dims,
                    'clips': {n: list(bpy.data.actions[n].frame_range) for n in CLIPS}, 'materials': mats}
        print('ENEMY_EXPORT ' + json.dumps(manifest), flush=True)
        return manifest
