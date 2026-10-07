"""Kit for the v2 monster roster (enemies_c): the enemies_a `Creature` builder plus
surface-aware anime faces, gems, petals and the shared seven-clip `Animator` (every regular monster,
v2/v3 kits and the enemies_b creatures, is animated by it).

Conventions are those of creature_kit: the creature stands on z=0 and faces -Y, every bone
points +Z, `Motion` keys rotations in world axes (+ax = top tips forward, +ay = top leans to
the creature's left (+X), +az = turns its face toward +X). Parts are rigidly bound to one bone.

Bone names the animator understands (anything else is only moved by its parent or `extra`):
  root, body, head, eyes (blink pivot = eye centre), jaw, crest, lid (hinged lid/jaw that opens up),
  arm.L/R, leg.L/R, leg.FL/FR/BL/BR (quadruped), legN.L/R (crawler, N = 1..4 front to back),
  wing.L/R, wing2.L/R, tail1..tailN, antenna.L/R, ear.L/R, orbit* (spins about Z),
  flame* (flicker), cape (sway), weapon.R/L (held items; follow the arm, wrist flick on attacks),
  tentacle* (sway/whip). Tails, ears, antennae, crest, cape, tentacles, flames and wing2 lag their parent.
Kinds: biped, heavy, quad, crawler, fly (wings, hovers), float (hovers), hop (bounces; legless = jelly).
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
from mathutils import Matrix, Vector  # noqa: E402

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


# ---------------------------------------------------------------- motion curves
# Every clip is sampled on every frame from the eased envelopes below (no linear tweening between a dozen
# keys): anticipation -> fast strike -> overshoot -> damped settle, with secondary parts lagging their parent.
TAU = math.tau
DIE_HOLD = 0.87  # Die is frozen from here to the last frame (collapsed and held)


def _cl(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def sstep(x):
    x = _cl(x)
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    """Smooth 0 -> 1 between a and b."""
    return sstep((t - a) / (b - a))


def ease_in(x, p=2.0):
    return _cl(x) ** p


def ease_out(x, p=2.0):
    return 1 - (1 - _cl(x)) ** p


def window(t, a, b, c, d):
    """Smooth rise a -> b, hold, smooth fall c -> d."""
    return ramp(t, a, b) * (1 - ramp(t, c, d))


def bump(t, c, w):
    """Compact cos^2 bump: 1 at c, exactly 0 beyond c +- w."""
    x = (t - c) / w
    return math.cos(x * math.pi / 2) ** 2 if -1 < x < 1 else 0.0


def arc(t, a, b):
    """Jump height: 0 outside (a, b), a sine arc peaking at 1 between."""
    return math.sin(math.pi * (t - a) / (b - a)) if a < t < b else 0.0


def kick(t, t0, rise, freq=1.4, decay=4.5):
    """Recoil: 0 -> 1 in `rise` (ease out), then a damped rebound that overshoots past 0 and settles."""
    x = t - t0
    if x <= 0:
        return 0.0
    if x < rise:
        return ease_out(x / rise, 2.2)
    y = x - rise
    return math.exp(-decay * y) * math.cos(TAU * freq * y)


def dsin(t, t0, freq, decay):
    """Damped oscillation starting at t0 (0 before)."""
    x = t - t0
    return math.exp(-decay * x) * math.sin(TAU * freq * x) if x > 0 else 0.0


def soft(x, lim):
    """Soft clamp to +-lim (keeps follow-through from flipping parts over)."""
    return lim * math.tanh(x / lim)


def attack_env(t):
    """Attack envelopes (anticipation, strike, impact, wobble); the strike lands on t = 0.4 exactly."""
    ant = window(t, 0.0, 0.25, 0.30, 0.38)
    if t < 0.29:
        strike = 0.0
    elif t < 0.40:
        strike = ease_in((t - 0.29) / 0.11, 2.0)
    else:
        strike = (1 + 0.16 * dsin(t, 0.40, 3.0, 8.0)) * (1 - ramp(t, 0.50, 0.92))
    imp = math.exp(-(t - 0.40) * 16) * (1 - ramp(t, 0.6, 0.8)) if t >= 0.40 else 0.0
    wob = dsin(t, 0.48, 2.2, 4.0) * (1 - ramp(t, 0.82, 1.0))
    return ant, strike, imp, wob


def cast_env(t):
    """Cast envelopes (gather, charge shake, burst, pop, settle); the release bursts at t = 0.6."""
    gather = window(t, 0.03, 0.45, 0.54, 0.61)
    shake = math.sin(TAU * t * 8) * window(t, 0.2, 0.42, 0.52, 0.58)
    if t < 0.55:
        burst = 0.0
    elif t < 0.60:
        burst = ease_out((t - 0.55) / 0.05, 2.0)
    else:
        burst = math.exp(-(t - 0.6) * 5.0) * (1 - ramp(t, 0.8, 1.0))
    pop = bump(t, 0.61, 0.05)
    settle = dsin(t, 0.62, 2.0, 5.0) * (1 - ramp(t, 0.85, 1.0))
    return gather, shake, burst, pop, settle


def hit_env(t):
    """Hit envelopes (recoil with rebound, decaying shake)."""
    rec = kick(t, 0.0, 0.17, 1.3, 4.0) * (1 - ramp(t, 0.7, 1.0))
    shake = math.sin(TAU * t * 3.0) * math.exp(-t * 2.5) * (1 - ramp(t, 0.6, 0.95))
    return rec, shake


def die_env(t):
    """Die envelopes (stagger, sway, fall with bounce, thud, limp); constant from DIE_HOLD on."""
    t = min(t, DIE_HOLD)
    stag = kick(t, 0.0, 0.09, 1.6, 6.0) * (1 - ramp(t, 0.22, 0.34))
    sway = math.sin(TAU * (t - 0.08) * 2.2) * window(t, 0.08, 0.16, 0.26, 0.36)
    if t < 0.3:
        fall = 0.0
    elif t < 0.62:
        fall = ease_in((t - 0.3) / 0.32, 2.2)
    else:
        fall = 1 - 0.14 * abs(math.sin(math.pi * (t - 0.62) / 0.11)) * math.exp(-(t - 0.62) * 9) * (1 - ramp(t, 0.78, 0.86))
    thud = bump(t, 0.63, 0.04) + 0.45 * bump(t, 0.735, 0.035)
    limp = ramp(t, 0.5, 0.8)
    return stag, sway, fall, thud, limp


class Pose:
    """One sampled pose. Rotations in degrees with the Motion axis convention."""

    def __init__(self):
        self.rl = [0.0, 0.0, 0.0]      # root location
        self.rr = [0.0, 0.0, 0.0]      # root rotation
        self.rs = 1.0                  # root uniform scale
        self.br = [0.0, 0.0, 0.0]      # body rotation
        self.bs = [1.0, 1.0, 1.0]      # body scale (x, y, z)
        self.hr = [0.0, 0.0, 0.0]      # head rotation
        self.jaw = 0.0                 # jaw open (deg)
        self.lid = 0.0                 # hinged lid (negative opens)
        self.blink = 1.0               # eyes z scale
        self.arm = {'L': [0.0, 0.0, 0.0], 'R': [0.0, 0.0, 0.0]}  # (raise forward, abduct outward, twist outward)
        self.leg = {}                  # bone -> rotation
        self.flap = 0.0                # wing angle (+ down)
        self.sweep = 0.0               # wing sweep (+ back)
        self.twist = 0.0               # wing pitch
        self.ear = [0.0, 0.0]          # (tip back -, splay out +)
        self.tail = [0.0, 0.0]         # whole-tail curl (lift, wag)
        self.tent = [0.0, 0.0]         # tentacle swing (ax, ay)
        self.glow = 1.0                # flame scale
        self.crest = 1.0               # crest scale
        self.spin = 0.0                # orbit spin (deg)
        self.weapon = 0.0              # wrist flick of held items
        self.cape = 0.0
        self.drop = 0.0                # Die: gravity drop of flyers (0..1)
        self.ground = False            # Die: keep the rotated body on the floor


class Animator:
    """Procedural seven-clip animator shared by every regular monster kit (v2 Monster, v3 Sculpt and the
    enemies_b Creature builds). Kinds: biped, heavy, quad, crawler, hop (legless = jelly), fly, float.

    Body-type behaviour (readable from a mid-distance phone camera):
      Idle    breathing squash/stretch, slime jiggle, head look + tilt, blinks, ear flicks, leg taps, wing-beat bob.
      Run     bouncy gait with contact squash, hip twist, opposite arm swing, hop arcs, gallop rock, skitter.
      Attack  anticipation -> strike at 40 % -> overshoot/squash -> settle: biters lunge and snap the jaw, clawers
              swipe with a torso twist, heavies double-slam, slimes jump-slam, flyers dive, bugs rear up and stab.
      Cast    rear up and gather with a building shake, burst at 60 %, damped settle.
      Hit     strong recoil + squash with a rebound and shake, eyes shut, limbs flung.
      Die     stagger, accelerating collapse with a bounce, held on the floor (flyers fall, slimes melt).
      Victory hops + spin + roar (heavies pound and roar, quads bow and howl, bugs dance and spin, flyers flip).
    Secondary parts (tails, ears, antennae, crests, capes, tentacles, flames, wing2) follow their parent with a
    lag, so motion overlaps instead of every bone moving in lock step.
    """

    def __init__(self, bones, parts, kind='biped', masses=(), follow=None, arm_limit=None):
        kind = {'wisp': 'float', 'jelly': 'float', '': 'biped', None: 'biped'}.get(kind, kind)
        self.kind = kind
        self.names = names = set(parts)
        self.rest = {b[0]: Vector(b[1]) for b in bones}
        self.parent = {b[0]: b[3] for b in bones}
        self.air = kind in ('fly', 'float')
        self.fly = kind == 'fly'
        self.float = kind == 'float'
        self.heavy = kind == 'heavy'
        self.quad = kind == 'quad'
        self.crawler = kind == 'crawler'
        self.hop = kind == 'hop'
        self.biped = kind in ('biped', 'heavy')
        self.legs = sorted(n for n in names if n.startswith('leg'))
        self.jelly = self.hop and not self.legs
        self.wings = sorted(n for n in names if n.startswith(('wing.', 'wing2.')))
        self.arms = [s for s in ('L', 'R') if 'arm.' + s in names]
        self.weapon = 'weapon.R' in names
        self.tails = sorted((n for n in names if n[:4] == 'tail' and n[4:].isdigit()), key=lambda n: int(n[4:]))
        self.abdomen = len(self.tails) == 1 and kind in ('crawler', 'fly')
        legn = [n for n in names if n[:3] == 'leg' and n[3:4].isdigit()]
        self.nlegn = max([int(n[3:n.index('.')]) for n in legn] or [1])
        self.hb = self.rest['body'].z if 'body' in self.rest else 0.0
        self.follow = dict(follow or {})
        self.arm_limit = arm_limit  # (raise, abduct) soft limits: fused sculpted shoulders tear past ~90 deg
        self._points(parts, masses)
        self._cache = {}

    # ------------------------------------------------------------ geometry for grounding
    def _points(self, parts, masses):
        bpy.context.view_layer.update()
        pts = []
        for objs in parts.values():
            for o in objs:
                if o.type == 'MESH':
                    mw = o.matrix_world
                    pts += [mw @ Vector(c) for c in o.bound_box]
        for m in masses:
            if m.get('ghost') or m.get('neg'):
                continue
            r = m['r']
            for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                pts.append(m['co'] + m['q'] @ Vector((v[0] * r.x, v[1] * r.y, v[2] * r.z)))
        if not pts:
            pts = [Vector((0, 0, 0)), Vector((0, 0, 0.5))]
        step = max(1, len(pts) // 1500)
        self.pts = pts[::step]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        self.center = (lo + hi) / 2
        self.zmin = lo.z
        self.H = max(0.2, hi.z - lo.z)
        self.S = _cl(self.H / 0.8, 0.6, 1.5)  # translation scale: small critters move less in metres
        self.floor = 0.0 if self.air else lo.z
        # how far the ground contacts reach in front of / behind the body pivot: pitching the body about its pivot
        # would push them into the floor, so the root is raised to compensate
        by = self.rest['body'].y if 'body' in self.rest else 0.0
        feet = [p for p in pts if p.z < lo.z + 0.2 * self.H] or [Vector((0, by, 0))]
        self.back = max(0.0, max(p.y for p in feet) - by)
        self.front = max(0.0, by - min(p.y for p in feet))

    def _ground(self, P):
        """Translation that keeps a Die pose (root rotated about the floor origin) resting on the floor."""
        ax, ay, az = (math.radians(v) for v in P.rr)
        m = (Matrix.Rotation(ay, 3, 'Y') @ Matrix.Rotation(az, 3, 'Z') @ Matrix.Rotation(ax, 3, 'X')) * P.rs
        low = min((m @ p).z for p in self.pts)
        c = m @ self.center
        keep = 1.0 if self.air else 0.9 if self.crawler else 0.85 if self.quad or self.hop else 0.3
        tx, ty = (self.center.x - c.x) * keep, (self.center.y - c.y) * keep
        lift = self.floor - low - 0.008 * self.S
        if self.air:
            if not hasattr(self, '_final_lift'):
                q = self.at('Die', 1.0)
                fx, fy, fz = (math.radians(v) for v in q.rr)
                mf = (Matrix.Rotation(fy, 3, 'Y') @ Matrix.Rotation(fz, 3, 'Z') @ Matrix.Rotation(fx, 3, 'X')) * q.rs
                self._final_lift = -min((mf @ p).z for p in self.pts) - 0.008 * self.S
            tz = max(self._final_lift * P.drop, lift)
        else:
            tz = max(0.0, lift)
        return tx, ty, tz

    # ------------------------------------------------------------ sampling
    def at(self, clip, t):
        t = (t % 1.0) if clip in ('Idle', 'Run') else _cl(t)
        key = (clip, round(t, 5))
        p = self._cache.get(key)
        if p is None:
            p = self._cache[key] = getattr(self, '_' + clip.lower())(t)
        return p

    # ------------------------------------------------------------ clips
    def _idle(self, t):
        P, S = Pose(), self.S
        w = math.sin(TAU * t)
        look = window(t, 0.48, 0.58, 0.74, 0.84)
        huff = math.sin(TAU * 3 * (t - 0.17)) * bump(t, 0.24, 0.07)
        P.blink = 1 - 0.9 * (bump(t, 0.33, 0.025) + bump(t, 0.86, 0.025))
        P.hr = [3 * math.sin(TAU * t - 1.0) + 5 * bump(t, 0.92, 0.06), 8 * window(t, 0.55, 0.63, 0.7, 0.78),
                18 * look + 7 * huff]
        if self.fly:
            n = 3
            beat = math.sin(TAU * n * t)
            P.flap = 34 * beat
            P.sweep = 8 * math.cos(TAU * n * t)
            P.twist = 12 * math.cos(TAU * n * t)
            P.rl = [0, 0, S * (0.035 * math.sin(TAU * n * t - 0.9) + 0.02 * w)]
            P.br = [4 - 4 * math.cos(TAU * n * t - 0.5), 3 * math.sin(TAU * t + 1), 4 * math.sin(TAU * t + 2) + 6 * look]
            P.bs = [1 - 0.012 * beat, 1 - 0.012 * beat, 1 + 0.025 * math.sin(TAU * n * t - 0.6)]
        elif self.float:
            P.rl = [0.01 * S * math.sin(TAU * t + 2), 0, 0.045 * S * w]
            P.br = [3 * math.sin(TAU * t - 1), 4 * math.sin(TAU * t + 0.5), 5 * math.sin(TAU * t + 2) + 6 * look]
            P.bs = [1 - 0.015 * w, 1 - 0.015 * w, 1 + 0.03 * w]
            P.flap = 26 * math.sin(TAU * 6 * t)
            P.sweep = 6 * math.cos(TAU * 6 * t)
            P.tent = [14 * math.sin(TAU * t), 10 * math.sin(TAU * t + 1)]
        elif self.jelly:
            P.bs = [1 - 0.035 * w + 0.02 * math.sin(TAU * 2 * t + 1.3), 1 - 0.035 * w - 0.02 * math.sin(TAU * 2 * t + 1.3),
                    1 + 0.055 * w + 0.015 * math.sin(TAU * 3 * t + 0.7)]
            P.br = [3 * math.sin(TAU * 2 * t + 0.3), 3 * math.sin(TAU * 2 * t + 2.0), 5 * math.sin(TAU * t + 1.5) + 8 * look]
        else:
            k = 0.018 if self.heavy else 0.02 if self.quad else 0.03 if self.crawler else 0.026
            P.bs = [1 - 0.5 * k * w, 1 - 0.5 * k * w, 1 + k * w]
            P.br = [2.5 * math.sin(TAU * t - 0.6) + (1.5 if self.heavy else 0), 2 * math.sin(TAU * t + 1.2),
                    3 * math.sin(TAU * t + 2) + 5 * look]
            if self.hop:  # legged hopper: quick nose sniffs
                P.hr[0] += 3 * math.sin(TAU * 8 * t) * window(t, 0.08, 0.13, 0.3, 0.36)
                P.lid = -6 * (0.5 + 0.5 * math.sin(TAU * t - 1.2)) - 30 * window(t, 0.6, 0.66, 0.72, 0.8)
        if not self.fly and not self.float and self.wings:  # folded wings breathe
            P.flap = 8 * math.sin(TAU * t - 0.5) + 14 * bump(t, 0.4, 0.1) * math.sin(TAU * 4 * t)
            P.sweep = 10
        P.jaw = 3 * (0.5 + 0.5 * w) + (4 + 4 * math.sin(TAU * 4 * t) if self.quad else 0)
        for s in ('L', 'R'):
            ph = 0 if s == 'R' else 0.4
            P.arm[s] = [5 * math.sin(TAU * t - 0.8 + ph) - (8 if self.float else 3), 5 + 3 * math.sin(TAU * t + 0.3 + ph), 0]
        self._legs_idle(P, t)
        P.tail = [0, 0]
        P.spin = 360 * t
        P.cape = 3 * math.sin(TAU * t + 0.3)
        return P

    def _run(self, t):
        P, S = Pose(), self.S
        w = math.sin(TAU * t)
        if self.fly:
            beat = math.sin(TAU * 2 * t)
            P.flap = 48 * beat
            P.sweep = 10 + 10 * math.cos(TAU * 2 * t)
            P.twist = 16 * math.cos(TAU * 2 * t)
            P.rl = [0, 0, S * 0.05 * math.sin(TAU * 2 * t - 0.9)]
            P.br = [18 + 5 * math.cos(TAU * 2 * t), 0, 4 * w]
            P.hr = [-10 - 4 * math.cos(TAU * 2 * t - 0.6), 0, -3 * w]
            P.bs = [1, 1 + 0.03 * beat, 1 - 0.02 * beat]
        elif self.float:
            P.rl = [0.02 * S * w, 0, 0.04 * S * math.sin(TAU * 2 * t)]
            P.br = [16 + 3 * math.sin(TAU * 2 * t), 3 * w, 6 * w]
            P.hr = [-8, 0, -4 * w]
            P.bs = [1, 1 + 0.03 * math.sin(TAU * 2 * t), 1 - 0.02 * math.sin(TAU * 2 * t)]
            P.flap = 32 * math.sin(TAU * 4 * t)
            P.tent = [25 + 10 * math.sin(TAU * 2 * t), 6 * w]
            P.cape = 18
        elif self.hop:
            u = (2 * t) % 1.0
            h = math.sin(math.pi * _cl((u - 0.08) / 0.84))
            contact = bump(u, 0.0, 0.12) + bump(u, 1.0, 0.12)
            rise = window(u, 0.06, 0.16, 0.3, 0.5)
            P.rl = [0, 0, S * (0.12 if self.jelly else 0.1) * h]
            k = 1.0 if self.jelly else 0.6
            sz = 1 - 0.2 * k * contact + 0.14 * k * rise
            P.bs = [1 / math.sqrt(sz), 1 / math.sqrt(sz), sz]
            P.br = [8 + 8 * math.sin(TAU * u - 0.4), 0, 4 * w]
            P.hr = [-4 * math.sin(TAU * u - 0.2), 0, 0]
            P.lid = -35 * h
        elif self.quad:
            bounce = abs(math.sin(TAU * t))
            P.rl = [0, 0, S * 0.045 * bounce]
            P.br = [5 * math.sin(TAU * t + 0.8), 0, 3 * w]
            P.bs = [1, 1 + 0.05 * math.sin(TAU * t), 1 - 0.035 * math.sin(TAU * t)]
            P.hr = [-6 * math.sin(TAU * t + 0.3) - 4, 0, -2 * w]
            P.jaw = 10 + 6 * math.sin(TAU * 2 * t)
            P.ear = [-25, 0]
            P.tail = [14, 0]
        elif self.crawler:
            P.rl = [0, 0, S * 0.02 * abs(math.sin(TAU * 2 * t))]
            P.br = [6 + 2 * math.sin(TAU * 4 * t), 2 * math.sin(TAU * 2 * t), 4 * math.sin(TAU * 2 * t)]
            P.hr = [4 * math.sin(TAU * 2 * t - 0.4), 0, -3 * math.sin(TAU * 2 * t)]
            P.tail = [10, 0]
        else:  # biped / heavy
            bounce = abs(math.sin(TAU * t))
            contact = (1 - bounce) ** 4
            hv = 0.65 if self.heavy else 1.0
            P.rl = [0.012 * S * w, 0, S * 0.055 * hv * bounce]
            sz = 1 - 0.07 * hv * contact + 0.03 * bounce
            P.bs = [1 + 0.04 * hv * contact, 1 + 0.04 * hv * contact, sz]
            P.br = [12 + 4 * math.cos(TAU * 2 * t), 5 * w, 7 * w]
            P.hr = [-8 - 4 * math.cos(TAU * 2 * (t - 0.05)), 0, -5 * w]
            P.jaw = 8 + 6 * bounce
            P.cape = 22 + 6 * abs(math.sin(TAU * t + 0.4))
            P.ear = [-15, 0]
        if not self.fly and self.wings and not self.float:
            P.flap = 10 * math.sin(TAU * 2 * t)
            P.sweep = 25
        for s in ('L', 'R'):
            side = 1 if s == 'L' else -1
            swing = 36 * side * math.sin(TAU * (t - 0.04)) * (0.6 if self.heavy else 1.0)
            if self.air:
                P.arm[s] = [25 + 8 * math.sin(TAU * 2 * t + side), 12, 0]
            elif self.crawler or (self.quad and not self.biped):
                P.arm[s] = [-15 + 10 * math.sin(TAU * 2 * t + side), 10, 0]
            elif self.hop:
                P.arm[s] = [-25 + 15 * math.sin(TAU * 2 * t), 10, 0]
            elif s == 'R' and self.weapon:
                P.arm[s] = [-30 + 0.35 * swing, 12, 0]
            else:
                P.arm[s] = [swing, 10 + 6 * abs(w), 0]
        self._legs_run(P, t)
        P.spin = 720 * t
        return P

    def _attack(self, t):
        P, S = Pose(), self.S
        ant, st, imp, wob = attack_env(t)
        lunge = window(t, 0.29, 0.36, 0.40, 0.47)
        P.blink = 1 - 0.35 * ant - 0.4 * imp
        if self.quad:  # biter: crouch back, lunge, jaw snaps shut on the hit frame
            P.rl = [0, S * (0.10 * ant - 0.34 * st), S * (-0.04 * ant + 0.05 * lunge)]
            P.br = [-10 * ant + 14 * st + 5 * wob, 0, 4 * wob]
            P.bs = [1 + 0.04 * ant + 0.07 * imp, 1 + 0.08 * lunge, 1 - 0.06 * ant - 0.08 * imp]
            P.hr = [-18 * ant + 22 * st - 8 * imp + 6 * wob, 0, 5 * wob]
            P.jaw = 42 * window(t, 0.18, 0.33, 0.38, 0.41) + 14 * window(t, 0.45, 0.52, 0.62, 0.8)
            P.ear = [-30 * st + 10 * ant, 0]
            P.tail = [25 * ant - 10 * st, 0]
        elif self.crawler:  # rear up, then stab/slam forward
            P.rl = [0, S * (0.06 * ant - 0.22 * st), S * 0.05 * ant]
            P.br = [-24 * ant + 16 * st + 5 * wob, 0, 3 * wob]
            P.bs = [1 + 0.07 * imp, 1 + 0.05 * lunge, 1 - 0.1 * imp + 0.03 * ant]
            P.hr = [-12 * ant + 18 * st - 6 * imp, 0, 0]
            P.jaw = 30 * window(t, 0.2, 0.32, 0.38, 0.41)
            P.tail = [30 * ant - 25 * st, 0]
        elif self.jelly or self.hop:  # jump-slam
            air = arc(t, 0.29, 0.40)
            k = 1.0 if self.jelly else 0.55
            sz = 1 - 0.25 * k * ant + 0.25 * k * air - 0.35 * k * imp + 0.08 * k * wob
            P.bs = [1 / math.sqrt(sz), 1 / math.sqrt(sz), sz]
            P.rl = [0, S * (0.05 * ant - 0.3 * st), S * 0.16 * air]
            P.br = [-8 * ant + 14 * air + (22 * st if not self.jelly else 4 * st) + 4 * wob, 0, 5 * wob]
            P.hr = [-10 * ant + 18 * st, 0, 0]
            P.lid = -75 * window(t, 0.04, 0.24, 0.33, 0.40) - 12 * max(0.0, dsin(t, 0.42, 3, 8))
            P.ear = [-40 * st + 12 * ant, 10 * ant]
        elif self.heavy:  # overhead double slam / club smash with a ground-pound shake
            P.rl = [0, S * (0.05 * ant - 0.16 * st), S * (0.03 * ant - 0.03 * imp)]
            P.br = [-16 * ant + 26 * st + 4 * wob, 4 * dsin(t, 0.4, 6, 10), -6 * ant + 4 * st]
            P.bs = [1 + 0.07 * imp, 1 + 0.07 * imp, 1 - 0.1 * imp + 0.03 * ant]
            P.hr = [-14 * ant + 16 * st, 0, 0]
            P.jaw = 35 * window(t, 0.15, 0.3, 0.38, 0.5)
        elif self.fly:  # rise and cock the wings, dive with talons/bite, flap back up
            P.rl = [0, S * (0.10 * ant - 0.36 * st), S * (0.14 * ant - 0.12 * st)]
            P.br = [-22 * ant + 32 * st + 6 * wob, 0, 4 * wob]
            P.bs = [1 + 0.05 * imp, 1 + 0.08 * lunge, 1 - 0.06 * imp]
            P.hr = [-8 * ant + 15 * st, 0, 0]
            rec = window(t, 0.45, 0.55, 0.85, 1.0)
            P.flap = -55 * ant + 20 * st + 45 * math.sin(TAU * 3 * (t - 0.45)) * rec
            P.sweep = -10 * ant + 35 * st
            P.jaw = 35 * window(t, 0.25, 0.34, 0.38, 0.42)
            P.tail = [-20 * ant + 15 * st, 0]
        elif self.float:  # pull back and swell, lunge with a stretch and a swipe
            P.rl = [0, S * (0.08 * ant - 0.3 * st), S * (0.06 * ant - 0.04 * st)]
            P.br = [-14 * ant + 20 * st + 5 * wob, 0, -8 * ant + 10 * st]
            P.bs = [1 + 0.08 * ant - 0.04 * lunge + 0.06 * imp, 1 + 0.08 * ant + 0.12 * lunge, 1 + 0.08 * ant - 0.08 * imp]
            P.hr = [-10 * ant + 12 * st, 0, 0]
            P.tent = [30 * ant - 45 * st, 0]
            P.flap = -40 * ant + 30 * st + 20 * math.sin(TAU * 5 * t) * (1 - ant)
            P.jaw = 25 * window(t, 0.25, 0.34, 0.4, 0.5)
            P.cape = -10 * st
        else:  # biped: torso twist wind-up, swipe/slash across, step in
            P.rl = [0, S * (0.06 * ant - 0.24 * st), -0.02 * S * imp]
            P.br = [-10 * ant + 18 * st + 4 * wob, 0, -28 * ant + 30 * st - 6 * wob]
            P.bs = [1 + 0.03 * ant + 0.05 * imp, 1 + 0.03 * ant + 0.05 * imp, 1 - 0.04 * ant - 0.06 * imp]
            P.hr = [-6 * ant + 10 * st, 0, 10 * ant - 12 * st]
            P.jaw = 30 * window(t, 0.25, 0.33, 0.40, 0.5)
            P.weapon = -30 * ant + 30 * st
            P.cape = 15 * ant - 10 * st
            P.ear = [-20 * st, 0]
            P.tail = [15 * ant - 10 * st, 20 * ant - 25 * st]
        if not self.fly and self.wings:
            P.flap = -35 * ant + 25 * st - (25 * math.sin(TAU * 4 * t) if self.float else 0)
            P.sweep = 15 * st
        self._arms_attack(P, t, ant, st, imp, wob)
        self._legs_attack(P, t, ant, st, imp, lunge)
        return P

    def _cast(self, t):
        P, S = Pose(), self.S
        g, sh, burst, pop, settle = cast_env(t)
        sh2 = math.cos(TAU * t * 8) * window(t, 0.2, 0.42, 0.52, 0.58)
        if self.air:
            P.rl = [0.006 * S * sh, 0, S * (0.14 * g + 0.04 * burst)]
        else:
            P.rl = [0.008 * S * sh, 0, S * 0.03 * g]
        rear = 28 if self.crawler else 22 if self.quad else 16
        P.br = [-rear * g + 14 * burst + 6 * settle, 3.5 * sh, 2.5 * sh2]
        sw = (0.12 if self.jelly else 0.05) * g
        sz = 1 + sw + 0.10 * pop - 0.06 * bump(t, 0.68, 0.04) + 0.03 * settle
        if self.jelly:
            sz -= 0.25 * pop
            P.bs = [1 + sw + 0.15 * pop, 1 + sw + 0.15 * pop, sz]
        else:
            P.bs = [1 + sw, 1 + sw, sz]
        head_up = 35 if self.quad else 22
        P.hr = [-head_up * g + 16 * burst + 2 * sh, 0, 2 * sh2]
        P.jaw = 10 * g + 38 * burst
        P.lid = -25 * g - 60 * burst
        P.blink = 1 - 0.3 * g + 0.1 * burst
        P.flap = -55 * g + 40 * burst + 10 * math.sin(TAU * 5 * t) * g
        if self.fly:
            P.flap += 20 * math.sin(TAU * 3 * t) * (1 - g)
        P.sweep = -10 * g + 10 * burst
        P.ear = [-10 * g + 10 * burst, 15 * g]
        P.tail = [20 * g - 10 * burst, 0]
        P.tent = [-25 * g + 35 * burst, 0]
        P.glow = 1 + 0.25 * g + 0.6 * burst
        P.crest = 1 + 0.12 * burst
        P.spin = 720 * t + 180 * ramp(t, 0.55, 0.7)
        P.cape = -10 * g + 18 * burst
        for s in ('L', 'R'):
            side = 1 if s == 'L' else -1
            if self.crawler or self.quad:
                P.arm[s] = [-45 * g - 15 * burst + 3 * sh, 30 * g - 10 * burst, 15 * g]
            else:
                P.arm[s] = [-120 * g - 85 * burst + 4 * sh * side, 35 * g + 5 * burst, 0]
        self._legs_cast(P, t, g, burst, sh)
        return P

    def _hit(self, t):
        P, S = Pose(), self.S
        rec, sh = hit_env(t)
        rl, _ = hit_env(t - 0.05)  # head/limbs lag the body by a frame or two
        P.rl = [0.01 * S * sh, S * 0.14 * rec, -S * 0.06 * rec if self.air else 0.0]
        P.br = [-24 * rec, 10 * rec + 4 * sh, 6 * sh]
        k = 1.8 if self.jelly else 1.0
        P.bs = [1 + 0.08 * k * rec, 1 + 0.08 * k * rec, 1 - 0.13 * k * rec]
        P.hr = [-20 * rl, -6 * rl, 6 * sh]
        P.blink = 1 - 0.85 * window(t, 0.02, 0.08, 0.35, 0.45)
        P.jaw = 20 * rl
        P.lid = -30 * rl
        P.flap = -45 * rec + 20 * sh
        P.sweep = 10 * rec
        P.ear = [-35 * rl, 10 * rl]
        P.tail = [25 * rl, 10 * sh]
        P.tent = [30 * rl, 10 * sh]
        P.cape = -12 * rl
        P.glow = 1 - 0.3 * rec
        for s in ('L', 'R'):
            P.arm[s] = [35 * rl, 32 * rl, 10 * sh]
        for n in self.legs:
            side = 1 if n.endswith('L') else -1
            if n in ('leg.L', 'leg.R'):
                P.leg[n] = [(-15 if side > 0 else 10) * rl, 0, 0]
            elif n[4:5] in ('F', 'B'):
                P.leg[n] = [(-20 if n[4] == 'F' else 15) * rl, -side * 6 * rl, 0]
            else:
                P.leg[n] = [0, -side * 25 * rl, 0]
        return P

    def _die(self, t):
        P, S = Pose(), self.S
        tt = min(t, DIE_HOLD)
        stag, sway, fall, thud, limp = die_env(t)
        P.ground = True
        P.blink = 1 - 0.85 * window(tt, 0.02, 0.06, 0.2, 0.3) - 0.9 * ramp(tt, 0.45, 0.6) * (1 - window(tt, 0.02, 0.06, 0.2, 0.3))
        P.br = [-18 * stag, 10 * sway, 8 * sway]
        P.hr = [-20 * stag, 0, 25 * limp]
        P.rl = [0, S * 0.06 * stag, -S * 0.03 * window(tt, 0.2, 0.3, 0.38, 0.5)]
        squash = 1 - 0.14 * thud - 0.05 * stag
        P.bs = [1 + 0.1 * thud, 1 + 0.1 * thud, squash]
        P.jaw = 25 * limp + 15 * stag
        P.lid = -70 * limp
        P.ear = [20 * limp - 20 * stag, -25 * limp]
        P.tail = [-10 * limp, 20 * limp]
        P.tent = [20 * limp, 0]
        P.cape = 10 * limp
        P.glow = max(0.05, 1 - 0.95 * ramp(tt, 0.3, 0.8))
        P.crest = 1 - 0.1 * limp
        fl = 50 * math.sin(TAU * 5 * tt) * window(tt, 0.02, 0.1, 0.5, 0.62)
        if self.jelly:  # melts into a puddle with a wobble
            melt = ramp(tt, 0.28, 0.7)
            sz = 1 - 0.62 * melt + 0.12 * math.sin(TAU * 2.5 * (tt - 0.45)) * window(tt, 0.45, 0.55, 0.75, 0.86) - 0.2 * thud
            sxy = 1 + 0.5 * melt + 0.12 * thud
            P.bs = [sxy, sxy, sz]
            P.br = [-14 * stag + 6 * melt, 10 * sway, 8 * sway]
            P.ground = False
        elif self.fly:
            P.rr = [70 * fall, 10 * fall, -15 * fall]
            P.drop = ease_in(ramp(tt, 0.25, 0.62), 1.6) if tt < 0.62 else 1.0
            P.flap = fl - 8 * limp  # wings splay flat on the floor
            P.sweep = -10 * limp
        elif self.float:
            P.rr = [-75 * fall, 0, 20 * fall]
            P.rs = 1 - 0.15 * fall
            P.drop = ease_in(ramp(tt, 0.2, 0.62), 1.6) if tt < 0.62 else 1.0
            P.flap = fl - 20 * limp
        elif self.crawler:  # knocked onto its back, legs curled
            P.rr = [0, 165 * fall, 0]
        elif self.quad or self.hop:
            P.rr = [0, 88 * fall, 0]
            P.lid = -70 * limp
        else:  # biped / heavy fall backwards
            P.rr = [-88 * fall, 0, 14 * fall]
        if not self.air and self.wings:
            P.flap = fl * 0.5 - 30 * limp
            P.sweep = -10 * limp
        flail = window(tt, 0.3, 0.42, 0.55, 0.65)
        for s in ('L', 'R'):
            P.arm[s] = [30 * stag - 60 * flail + 30 * limp, 25 * stag + 32 * limp, 0]
        for n in self.legs:
            side = 1 if n.endswith('L') else -1
            if n in ('leg.L', 'leg.R'):
                P.leg[n] = [(-25 if side > 0 else 10) * limp - 15 * flail, -side * 15 * limp, 0]
            elif n[4:5] in ('F', 'B'):
                front = n[4] == 'F'
                kick_ = 12 * math.sin(TAU * 4 * tt) * window(tt, 0.6, 0.66, 0.78, 0.86)
                P.leg[n] = [(-28 if front else 28) * limp + kick_, -side * 10 * stag, 0]
            else:
                try:
                    k = int(n[3:n.index('.')])
                except ValueError:
                    k = 1
                tw = 14 * math.sin(TAU * 4 * tt + k) * window(tt, 0.6, 0.66, 0.78, 0.86)
                P.leg[n] = [0, side * (50 * limp + tw) - side * 20 * stag, side * 10 * limp]
        return P

    def _victory(self, t):
        P, S = Pose(), self.S
        w = math.sin(TAU * t)
        pose = window(t, 0.68, 0.77, 0.9, 0.99)
        cheer = 12 * math.sin(TAU * 8 * t) * pose
        P.tail = [15 * pose, 0]
        P.blink = 1 - 0.45 * pose
        P.spin = 720 * t
        P.glow = 1 + 0.3 * pose + 0.1 * math.sin(TAU * 6 * t)
        P.ear = [8 * pose, 12 * pose]
        if self.heavy:  # chest pounds, stomp, roar
            beats = [(0.1, 'R'), (0.2, 'L'), (0.3, 'R'), (0.4, 'L')]
            stomp = bump(t, 0.52, 0.05)
            P.rl = [0, 0, S * (0.04 * arc(t, 0.44, 0.52) - 0.02 * stomp)]
            P.bs = [1 + 0.06 * stomp, 1 + 0.06 * stomp, 1 - 0.08 * stomp - 0.03 * sum(bump(t, c, 0.04) for c, _ in beats)]
            P.br = [-14 * pose + 4 * sum(bump(t, c, 0.04) for c, _ in beats), 3 * math.sin(TAU * 7 * t) * pose,
                    sum((8 if s == 'R' else -8) * bump(t, c, 0.06) for c, s in beats)]
            P.hr = [-30 * pose - 8 * window(t, 0.05, 0.1, 0.4, 0.45), 0, 4 * math.sin(TAU * 7 * t) * pose]
            P.jaw = 40 * pose + 10 * window(t, 0.05, 0.1, 0.4, 0.45)
            for s in ('L', 'R'):
                pound = sum(bump(t, c, 0.06) for c, ss in beats if ss == s)
                P.arm[s] = [-70 * pound - 30 * window(t, 0.06, 0.1, 0.42, 0.48) - 150 * pose + cheer, 10 + 45 * pose - 25 * pound, 0]
        elif self.quad:  # play bow, little hop, howl
            bow = window(t, 0.04, 0.14, 0.24, 0.32)
            hop = arc(t, 0.34, 0.5)
            P.rl = [0, 0, S * (-0.03 * bow + 0.12 * hop)]
            P.br = [16 * bow - 10 * hop - 14 * pose, 0, 4 * w]
            P.bs = [1, 1 + 0.06 * hop, 1 - 0.08 * bump(t, 0.33, 0.03) - 0.08 * bump(t, 0.51, 0.03)]
            P.hr = [-10 * bow - 45 * pose, 0, 8 * bow * math.sin(TAU * 3 * t)]
            P.jaw = 8 * bow + 32 * pose
            P.tail = [20, 0]
            P.ear = [10 * bow - 15 * pose, 0]
        elif self.crawler:  # rear-up dance, spin in place
            rear = window(t, 0.04, 0.14, 0.28, 0.36)
            P.br = [-25 * rear - 14 * pose, 6 * math.sin(TAU * 6 * t) * rear, 0]
            P.rr = [0, 0, 360 * sstep((t - 0.38) / 0.3)]
            P.rl = [0, 0, S * 0.05 * arc(t, 0.7, 0.8)]
            P.bs = [1, 1, 1 - 0.08 * bump(t, 0.81, 0.03)]
            P.hr = [-15 * rear - 10 * pose, 0, 8 * math.sin(TAU * 4 * t) * rear]
            P.jaw = 25 * pose
        else:  # hop, spin hop, cheer
            h1, h2 = arc(t, 0.08, 0.27), arc(t, 0.4, 0.66)
            crouch = bump(t, 0.06, 0.035) + bump(t, 0.29, 0.035) + bump(t, 0.38, 0.035) + bump(t, 0.68, 0.045)
            inair = (1.0 if 0.08 < t < 0.27 or 0.4 < t < 0.66 else 0.0) - h1 - h2
            k = 1.6 if self.jelly else 1.0
            alt = 1.6 if self.air else 1.0
            P.rl = [0, 0, S * alt * (0.13 * h1 + 0.2 * h2)]
            sz = 1 - 0.13 * k * crouch + 0.08 * k * inair
            P.bs = [1 / math.sqrt(sz), 1 / math.sqrt(sz), sz]
            if self.fly:
                P.br = [-360 * sstep((t - 0.4) / 0.24) - 10 * pose, 0, 6 * w]
            else:
                P.rr = [0, 0, 360 * sstep((t - 0.42) / 0.22)]
                P.br = [-6 * (h1 + h2) - 12 * pose + 6 * crouch, 4 * math.sin(TAU * 4 * t) * pose, 0]
            P.hr = [-28 * pose + 8 * crouch, 0, 10 * math.sin(TAU * 2 * t) * pose]
            P.jaw = 35 * pose + 15 * (h1 + h2)
            P.lid = -50 * pose - 30 * (h1 + h2)
            for s in ('L', 'R'):
                P.arm[s] = [-100 * max(h1, h2) - 160 * pose + cheer, 25 * max(h1, h2) + 30 * pose, 0]
        if self.wings:
            P.flap = -40 * pose + 30 * math.sin(TAU * 6 * t) * (pose + 0.4) + (25 * math.sin(TAU * 4 * t) if self.air else 0)
            P.sweep = -10 * pose
        if self.crawler or self.quad:
            for s in ('L', 'R'):
                side = 1 if s == 'L' else -1
                P.arm[s] = [-40 * pose - 20 * math.sin(TAU * 6 * t + side) * (pose + 0.3), 35 * pose, 20 * pose]
        self._legs_victory(P, t, pose)
        return P

    # ------------------------------------------------------------ limbs
    def _legn(self, n):
        try:
            return int(n[3:n.index('.')])
        except ValueError:
            return 1

    def _legs_idle(self, P, t):
        for n in self.legs:
            side = 1 if n.endswith('L') else -1
            if n in ('leg.L', 'leg.R'):
                if self.fly:
                    P.leg[n] = [10 + 8 * math.sin(TAU * 3 * (t - 0.06)), 0, 0]
                else:
                    P.leg[n] = [1.5 * math.sin(TAU * t + side), 0, 0]
            elif n[4:5] in ('F', 'B'):
                paw = bump(t, 0.2 if n == 'leg.FL' else 0.62, 0.05) if n[4] == 'F' else 0.0
                P.leg[n] = [2 * math.sin(TAU * t + (0 if n[4] == 'F' else 1)) - 18 * paw, 0, 0]
            else:
                k = self._legn(n)
                c = (0.08 + 0.83 * ((k - 1) * 2 + (side < 0)) / (2 * self.nlegn) + 0.37) % 1.0
                tap = bump(t, min(max(c, 0.06), 0.94), 0.05)
                P.leg[n] = [0, -side * (22 * tap - 2 * math.sin(TAU * (t + k * 0.15))), -side * 6 * tap]

    def _legs_run(self, P, t):
        for n in self.legs:
            side = 1 if n.endswith('L') else -1
            if n in ('leg.L', 'leg.R'):
                if self.fly:
                    P.leg[n] = [30 + 6 * math.sin(TAU * 2 * t), 0, 0]
                elif self.hop:
                    u = (2 * t) % 1.0
                    P.leg[n] = [45 * window(u, 0.0, 0.08, 0.16, 0.35) - 30 * window(u, 0.55, 0.75, 0.9, 1.0), 0, 0]
                else:
                    amp = 24 if self.heavy else 38
                    P.leg[n] = [-amp * side * math.sin(TAU * t), 0, 0]
            elif n[4:5] in ('F', 'B'):
                ph = {'leg.FL': 0.0, 'leg.FR': 0.1, 'leg.BL': 0.5, 'leg.BR': 0.6}.get(n, 0.0)
                P.leg[n] = [-42 * math.sin(TAU * (t + ph)), 0, 0]
            else:
                k = self._legn(n)
                psi = TAU * (2 * t + ((k + (0 if side > 0 else 1)) % 2) * 0.5)
                P.leg[n] = [0, -side * 20 * max(0.0, -math.cos(psi)), side * 24 * math.sin(psi)]

    def _arms_attack(self, P, t, ant, st, imp, wob):
        over = 0.12 * wob
        for s in self.arms:
            side = 1 if s == 'L' else -1
            if self.crawler or self.quad:  # pincers open wide, then clamp forward
                P.arm[s] = [-20 * ant - 35 * st, 35 * ant - 15 * st, 30 * ant - 20 * st]
                continue
            if self.heavy:
                lead = s == 'R' or not self.weapon
                wind, strike = ([-165, 15, 0], [-40, -5, 0]) if lead else ([-120, 25, 0], [-30, 10, 0])
            elif self.air:
                wind, strike = ([30, 35, 0], [-80, -20, 0]) if (s == 'R' or not self.weapon) else ([20, 30, 0], [-50, -10, 0])
            elif self.hop:
                wind, strike = [-30, 10, 0], [-50, 0, 0]
            elif s == 'R':
                wind, strike = ([-155, 25, -20], [-45, -10, 25]) if self.weapon else ([-110, 50, -30], [-60, -30, 30])
            else:
                wind, strike = [20, 20, 0], [25, 25, 0]
            P.arm[s] = [ant * wind[i] + st * strike[i] * (1 + over) for i in range(3)]

    def _legs_attack(self, P, t, ant, st, imp, lunge):
        for n in self.legs:
            side = 1 if n.endswith('L') else -1
            if n in ('leg.L', 'leg.R'):
                if self.fly:
                    P.leg[n] = [10 - 20 * ant - 55 * st, 0, 0]
                elif self.hop:
                    P.leg[n] = [-15 * ant + 50 * lunge, 0, 0]
                else:
                    P.leg[n] = [(8 * ant - 25 * st) if side > 0 else (-5 * ant + 15 * st), 0, 0]
            elif n[4:5] in ('F', 'B'):
                if n[4] == 'F':
                    P.leg[n] = [20 * ant - 40 * st, 0, 0]
                else:
                    P.leg[n] = [-15 * ant + 35 * window(t, 0.29, 0.36, 0.4, 0.6), 0, 0]
            else:
                k = self._legn(n)
                if k == 1:
                    lift = 50 * ant - 8 * st
                    P.leg[n] = [0, -side * lift, -side * (25 * ant + 10 * st)]
                else:
                    P.leg[n] = [0, side * 8 * ant, side * 6 * st]

    def _legs_cast(self, P, t, g, burst, sh):
        for n in self.legs:
            side = 1 if n.endswith('L') else -1
            if n in ('leg.L', 'leg.R'):
                P.leg[n] = [(15 * g if self.fly else 0) - 6 * burst * side, 0, 0]
            elif n[4:5] in ('F', 'B'):
                P.leg[n] = [(-15 * g + 10 * burst) if n[4] == 'F' else 8 * g, 0, 0]
            else:
                k = self._legn(n)
                lift = (40 * g + 6 * sh - 20 * burst) if k == 1 else (8 * g if k == 2 else -6 * g)
                P.leg[n] = [0, -side * lift, -side * 10 * g * (k == 1)]

    def _legs_victory(self, P, t, pose):
        for n in self.legs:
            side = 1 if n.endswith('L') else -1
            if n in ('leg.L', 'leg.R'):
                if self.fly:
                    P.leg[n] = [15 + 10 * math.sin(TAU * 4 * t), 0, 0]
                elif self.heavy:
                    P.leg[n] = [-35 * window(t, 0.42, 0.46, 0.48, 0.53) * (side > 0), 0, 0]
                else:
                    tuck = arc(t, 0.08, 0.27) + arc(t, 0.4, 0.66)
                    P.leg[n] = [-20 * tuck * side, 0, 0]
            elif n[4:5] in ('F', 'B'):
                bow = window(t, 0.04, 0.14, 0.24, 0.32)
                P.leg[n] = [(-40 * bow - 15 * pose) if n[4] == 'F' else 10 * bow, 0, 0]
            else:
                k = self._legn(n)
                psi = TAU * (4 * t + ((k + (0 if side > 0 else 1)) % 2) * 0.5)
                spin = window(t, 0.38, 0.42, 0.64, 0.68)
                wave = window(t, 0.04, 0.14, 0.28, 0.36) * (k == 1)
                P.leg[n] = [0, -side * (18 * spin * max(0.0, -math.cos(psi)) + 45 * wave + 12 * wave * math.sin(TAU * 6 * t)),
                            side * 20 * spin * math.sin(psi)]

    # ------------------------------------------------------------ writing
    def _chain_rot(self, P, bone):
        """Accumulated rotation (ax, az) of the core bones above `bone` (root tilt, body, head)."""
        ax = 0.5 * P.rr[0]
        az = 0.0
        b = self.parent.get(bone)
        while b:
            if b == 'body':
                ax += P.br[0]
                az += P.br[2]
            elif b == 'head':
                ax += P.hr[0]
                az += P.hr[2]
            b = self.parent.get(b)
        return ax, az

    def _drag(self, clip, t, bone, d, gain):
        """Follow-through of `bone`: its parent's rotation and the root's travel, delayed by d."""
        P, Q = self.at(clip, t), self.at(clip, t - d)
        pa, pz = self._chain_rot(P, bone)
        qa, qz = self._chain_rot(Q, bone)
        dz = (P.rl[2] - Q.rl[2]) / self.S
        dy = (P.rl[1] - Q.rl[1]) / self.S
        return gain * (qa - pa), gain * (qz - pz), dz, dy

    def write(self, a, clip, f, length):
        t = f / length
        if clip == 'Die':
            t = min(t, DIE_HOLD)  # every channel, lagged followers included, is frozen for the held end
        P = self.at(clip, t)
        names = self.names
        loop = clip in ('Idle', 'Run')
        rl = list(P.rl)
        if not self.air and 'body' in names:
            rl[2] += self.hb * (P.bs[2] - 1)  # squash toward the floor, feet stay planted
            pitch = math.radians(P.br[0])
            rl[2] += 0.85 * max(0.0, self.back * math.sin(-pitch), self.front * math.sin(pitch))  # rear-ups stay on the floor
        if P.ground:
            gx, gy, gz = self._ground(P)
            rl = [rl[0] + gx, rl[1] + gy, rl[2] + gz]
        a.l('root', f, rl)
        a.r('root', f, P.rr)
        if self.float:
            a.s('root', f, (P.rs, P.rs, P.rs))
        if 'body' in names:
            a.r('body', f, P.br)
            a.s('body', f, P.bs)
        if 'head' in names:
            a.r('head', f, P.hr)
        if 'jaw' in names:
            a.r('jaw', f, (P.jaw, 0, 0))
        if 'lid' in names:
            a.r('lid', f, (P.lid, 0, 0))
        if 'eyes' in names:
            a.s('eyes', f, (1, 1, max(0.08, P.blink)))
        for s in self.arms:
            side = 1 if s == 'L' else -1
            ax, abd, tw = P.arm[s]
            if self.arm_limit:
                ax, abd = soft(ax, self.arm_limit[0]), soft(abd, self.arm_limit[1])
            if s == 'L' and 'weapon.L' in names and self.biped and clip in ('Cast', 'Victory'):
                ax *= 0.55  # a shield arm stays low instead of covering the face
            a.r('arm.' + s, f, (ax, -side * abd, side * tw))
        for n in self.legs:
            a.r(n, f, P.leg.get(n, (0, 0, 0)))
        for n in self.wings:
            side = 1 if n.endswith('L') else -1
            Q = self.at(clip, t - 0.035) if n.startswith('wing2') else P
            a.r(n, f, (Q.twist, side * Q.flap, side * Q.sweep))
        # ---- follow-through parts
        n_t = len(self.tails)
        for k, n in enumerate(self.tails, 1):
            d = 0.06 if loop or clip == 'Victory' else 0.05
            g = 0.4 if self.abdomen else self.follow.get('tail', 1.0)
            Pa = self.at(clip, t - (k - 1) * d)
            Qa = self.at(clip, t - k * d)
            pa, pz = self._chain_rot(Pa, n)
            qa, qz = self._chain_rot(Qa, n)
            dz = (Pa.rl[2] - Qa.rl[2]) / self.S
            ax = g * (qa - pa) - g * 220 * dz
            az = g * (qz - pz)
            if clip == 'Idle':
                ax += g * 4 * math.sin(TAU * (2 * t - 0.1 * k))
                az += g * (16 if self.quad else 11) * math.sin(TAU * (t - 0.12 * k))
            elif clip == 'Run':
                ax += g * 6 * math.sin(TAU * (2 * t - 0.12 * k))
                az += g * 16 * math.sin(TAU * (2 * t - 0.12 * k))
            elif clip == 'Victory':
                az += g * 22 * math.sin(TAU * (5 * t - 0.1 * k))
            ax += g * P.tail[0] / n_t
            az += g * P.tail[1] / n_t
            a.r(n, f, (soft(ax, 45), 0, soft(az, 45)))
        for n in ('ear.L', 'ear.R', 'antenna.L', 'antenna.R'):
            if n not in names:
                continue
            side = 1 if n.endswith('L') else -1
            ant = n.startswith('antenna')
            dax, daz, dz, dy = self._drag(clip, t, n, 0.08 if ant else 0.06, self.follow.get('antenna' if ant else 'ear', 1.5 if ant else 1.2))
            ax = dax - 130 * dz + 70 * dy + P.ear[0]
            ay = side * P.ear[1]
            if clip == 'Idle':
                flick = bump(t, 0.72 if side > 0 else 0.76, 0.03)
                ax += -25 * flick
                ay += side * 10 * flick
                if ant:
                    ax += 8 * math.sin(TAU * 2 * t + side)
                    ay += side * 6 * math.sin(TAU * 3 * t + 1)
            elif clip == 'Run' and ant:
                ax += 6 * math.sin(TAU * 2 * t + side)
            a.r(n, f, (soft(ax, 50), soft(ay, 40), soft(-side * daz * 0.5, 20)))
        if 'crest' in names:
            g = self.follow.get('crest', 0.6)
            dax, daz, dz, dy = self._drag(clip, t, 'crest', 0.07, g)
            lim = 30 if g > 1 else 12
            ax = dax - g * 100 * dz + g * 50 * dy
            if clip == 'Idle':
                ax += g * 3 * math.sin(TAU * (t - 0.15))
            a.r('crest', f, (soft(ax, lim), 0, soft(daz, lim)))
            a.s('crest', f, (P.crest, P.crest, P.crest))
        if 'cape' in names:
            dax, daz, dz, dy = self._drag(clip, t, 'cape', 0.08, 1.0)
            ax = P.cape + dax - 60 * dz - 60 * dy
            if clip == 'Run':
                ax += 5 * math.sin(TAU * 2 * t)
            a.r('cape', f, (soft(ax, 45), 0, soft(daz * 0.5, 20)))
        for n in names:
            if n.startswith('tentacle'):
                try:
                    ph = int(n.replace('tentacle', '')) * 0.62
                except ValueError:
                    ph = 0.0
                dax, daz, dz, dy = self._drag(clip, t, n, 0.1, 1.4)
                ax = P.tent[0] + dax + 60 * dy - 80 * dz
                ay = P.tent[1]
                if loop:
                    m = 1 if clip == 'Idle' else 2
                    ax += 14 * math.sin(TAU * m * t + ph)
                    ay += 10 * math.sin(TAU * m * t + ph + 1)
                else:
                    ax += 8 * (math.sin(TAU * t + ph) - math.sin(ph))
                a.r(n, f, (soft(ax, 50), soft(ay, 40), 0))
            elif n.startswith('flame'):
                k = P.glow * (1 + 0.13 * math.sin(TAU * 4 * t + len(n)) + 0.06 * math.sin(TAU * 7 * t + 2 * len(n)))
                dax, daz, dz, dy = self._drag(clip, t, n, 0.06, 1.0)
                a.s(n, f, (1 + 0.5 * (k - 1), 1 + 0.5 * (k - 1), k))
                a.r(n, f, (soft(dax - 120 * dz + 80 * dy, 30), 0, soft(daz, 20)))
            elif n.startswith('orbit'):
                a.r(n, f, (0, 0, P.spin))
            elif n.startswith('weapon.'):
                a.r(n, f, (P.weapon if n == 'weapon.R' else 0.4 * P.weapon, 0, 0))


class Monster(Creature):
    def __init__(self, eid):
        super().__init__(eid)
        self.elite = eid.startswith('elite_')
        self.follow = {}  # follow-through gains per part family ('crest', 'tail'); springy plants raise 'crest'
        self.arm_limit = None  # soft (raise, abduct) arm limits in degrees, for skinned shoulders

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
        """Key the seven clips on every frame with the shared Animator. `extra(a, clip, f, t, i, names)` runs
        after the kit on each frame and may override any bone; `a.anim` is the Animator and `a.P` the kit pose of
        that frame (use the module envelopes attack_env/cast_env/... for timing that matches the kit)."""
        rig = A.armature(self.bones)
        anim = Animator(self.bones, self.parts, kind, getattr(self, 'masses', ()), self.follow, self.arm_limit)
        names = anim.names
        for clip, length in CLIPS.items():
            with Motion(rig, clip, length) as a:
                a.anim = anim
                for f in range(length + 1):
                    anim.write(a, clip, f, length)
                    if extra:
                        t = min(f / length, DIE_HOLD) if clip == 'Die' else f / length  # extras hold the Die end too
                        a.P = anim.at(clip, t)
                        extra(a, clip, f, t, f, names)
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
