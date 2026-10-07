"""Quaternion motion library, posed around character-space axes (X = the character's left, -Y = its front).

Heroes (create_actions(H)) get layered, eased motion:
- a combat-ready stance per hero (knees bent, weight between staggered feet, weapon held forward) is the
  base of Idle and the start/end pose of every one-shot clip, so cross-fades never pass through a T/A pose;
- feet are planted with a two-bone leg IK that runs on every frame (weight shift, lunges, crouches and
  pivots keep the soles fixed on the floor); hands reach authored targets through a small arm solver,
  so weapons point where the choreography says (sword edge on the target, bow vertical, staff forward);
- keys are interpolated with monotone cubic (eased, never overshooting between keys: every overshoot is an
  authored key), and each bone samples the timeline with its own lag (hips lead, chest/arms/head follow)
  for overlapping action;
- every frame is baked (LINEAR keys) and grounded: planted clips sit on the rest sole height, falling and
  locomotion clips on the evaluated skinned mesh.
Timing contract: Attack contact frame 12 / 30 (40 %), Cast release frame 24 / 40 (60 %), Skill contact 18 / 36
(50 %), Ultimate power-up 0-28 then finisher at 44 / 66 (resume_normalized 28 / 66), Die holds the
pose of frame 30 lying on the floor, Revive starts at Die:30 and ends at Idle:0, Guard returns to Idle:0.
NPCs (create_actions(H, npc=True)) keep their original clips (_legacy_actions).
"""
import math
import bpy
import numpy as np
from mathutils import Euler, Vector, Quaternion, Matrix

LENGTHS = dict(Idle=60, Walk=32, Run=20, Attack=30, Cast=40, Hit=12, Die=30, Victory=48, Talk=48,
               Guard=36, Revive=60, Skill=36, Ultimate=66)
LEGACY_LENGTHS = dict(Idle=48, Walk=32, Run=20, Attack=25, Cast=35, Hit=12, Die=30, Victory=42, Talk=48,
                      Guard=36, Revive=60)
LOOPS = ('Idle', 'Walk', 'Run', 'Talk')
ATTACK_HIT, CAST_RELEASE = 12, 24
# Signature moves: Skill contacts at 18 / 36 (50 %); Ultimate powers up (0-28, under the cut-in), then
# crouches, leaps or levitates and lands its finisher at 44 / 66.
SKILL_HIT, ULT_RESUME, ULT_HIT = 18, 28, 44
CONTACT = dict(Attack=ATTACK_HIT / 30, Cast=CAST_RELEASE / 40, Skill=SKILL_HIT / 36, Ultimate=ULT_HIT / 66)
# Promoted job outfits move like the hero they grew from.
STYLE_OF = dict(knight='warrior', paladin='warrior', berserker='warrior', warlord='warrior',
                elementalist='mage', archmage='mage', warlock='mage', abyssal='mage',
                sniper='archer', divine_archer='archer', ranger='archer', shadow_stalker='archer',
                priest='cleric', saint='cleric', exorcist='cleric', inquisitor='cleric')
ID = Quaternion()


def create_actions(H, npc=False):
    if npc:
        return _legacy_actions(H, npc=True)
    return HeroMotion(H).build()


def E(x=0.0, y=0.0, z=0.0):
    """Character-space rotation from XYZ Euler degrees."""
    return Euler((math.radians(x), math.radians(y), math.radians(z)), 'XYZ').to_quaternion()


def _frame(d, f):
    """Orthonormal basis (columns) from a direction and a perpendicular hint."""
    d = d.normalized()
    f = (f - d * f.dot(d))
    if f.length < 1e-8:
        f = Vector((0, 0, 1)) if abs(d.z) < .9 else Vector((0, -1, 0))
        f = f - d * f.dot(d)
    f.normalize()
    s = d.cross(f)
    return Matrix((d, f, s)).transposed()


def _map(d0, f0, d1, f1):
    """Rotation taking the rest (direction, hint) frame onto the posed one."""
    return (_frame(d1, f1) @ _frame(d0, f0).transposed()).to_quaternion()


def _smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- monotone cubic tracks

class Track:
    """Channels sampled at authored key frames; monotone cubic (PCHIP) between keys, eased at both ends."""

    def __init__(self, frames, values):
        self.x = np.asarray(frames, float)
        self.y = np.asarray(values, float)
        n = len(self.x)
        h = np.diff(self.x)
        d = np.diff(self.y, axis=0) / h[:, None]
        m = np.zeros_like(self.y)
        for i in range(1, n - 1):
            a, b = d[i - 1], d[i]
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            same = a * b > 0
            with np.errstate(divide='ignore', invalid='ignore'):
                hm = (w1 + w2) / (w1 / a + w2 / b)
            m[i] = np.where(same, hm, 0.0)
        self.m = m

    def __call__(self, t):
        x = self.x
        t = min(max(t, x[0]), x[-1])
        i = min(int(np.searchsorted(x, t, side='right')) - 1, len(x) - 2)
        h = x[i + 1] - x[i]
        s = (t - x[i]) / h
        h00, h10 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s
        h01, h11 = -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
        return h00 * self.y[i] + h10 * h * self.m[i] + h01 * self.y[i + 1] + h11 * h * self.m[i + 1]


# ---------------------------------------------------------------- skeleton maths

class Skel:
    """Rest data of the game rig and a pure-Python forward kinematics in the motion's q convention:
    a bone's accumulated rotation A = A_parent @ q, its head = head_parent + A_parent @ (rest offset)."""

    def __init__(self, rig):
        bones = rig.data.bones
        self.names = []

        def visit(b):
            self.names.append(b.name)
            for c in b.children:
                visit(c)
        for b in bones:
            if b.parent is None:
                visit(b)
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in bones}
        self.basis = {b.name: b.matrix_local.to_quaternion() for b in bones}
        self.head = {b.name: b.head_local.copy() for b in bones}
        self.tail = {b.name: b.tail_local.copy() for b in bones}
        self.chain = {}
        for n in self.names:
            c, p = [], n
            while p is not None:
                c.append(p)
                p = self.parent[p]
            self.chain[n] = c[::-1]

    def fk(self, q, loc, upto=None):
        A, P = {}, {}
        for n in (self.chain[upto] if upto else self.names):
            p = self.parent[n]
            qn = q.get(n, ID)
            if p is None:
                A[n], P[n] = qn.copy(), self.head[n] + loc
            else:
                A[n] = A[p] @ qn
                P[n] = P[p] + A[p] @ (self.head[n] - self.head[p])
        return A, P

    def seg(self, a, b):
        return (self.head[b] - self.head[a]).length


# ---------------------------------------------------------------- the hero motion set

class HeroMotion:
    def __init__(self, H):
        self.H = H
        self.rig = H.rig
        self.K = Skel(H.rig)
        self.style = STYLE_OF.get(H.name, H.name if H.name in ('warrior', 'archer', 'mage', 'cleric') else 'warrior')
        self.W = 'L' if self.style == 'archer' else 'R'          # weapon hand
        self.F = 'R' if self.W == 'L' else 'L'                   # free hand
        K = self.K
        self.arm_len = K.seg('upper_arm.R', 'forearm.R') + K.seg('forearm.R', 'hand.R')
        self.leg_len = K.seg('thigh.R', 'shin.R') + K.seg('shin.R', 'foot.R')
        # Offsets are authored for the 1.70 m warrior; other builds scale by their own limbs.
        self.sa = self.arm_len / .459
        self.sl = self.leg_len / .827
        self.bones = [n for n in K.names]
        self.secondary = [n for n in getattr(H, 'secondary', []) if n in K.head]
        self.weapon_rest = {S: (K.tail['weapon.' + S] - K.head['weapon.' + S]).normalized() for S in 'LR'}
        self.ball = {S: K.tail['foot.' + S].copy() for S in 'LR'}
        self.fore_axis = {S: (K.head['hand.' + S] - K.head['forearm.' + S]).normalized() for S in 'LR'}

    # ------------------------------------------------------------ helpers
    def side(self, S, v):
        """(out, forward, up) for side S -> character space."""
        sg = 1 if S == 'L' else -1
        return Vector((v[0] * sg, -v[1], v[2]))

    def leg_targets(self, ch):
        """World ball-of-foot position and foot rotation from a foot channel (out, fwd, up, heel pitch, yaw out)."""
        out = {}
        yaw_root = ch['@yaw'][0]
        Rr = E(0, 0, yaw_root)
        for S in 'LR':
            o, f, u, pitch, yaw = ch['@ik.' + S]
            sg = 1 if S == 'L' else -1
            d = Vector((o * sg, -f, u)) * self.sl
            ball = Rr @ (self.ball[S] + d)
            Rf = Rr @ E(0, 0, yaw * sg) @ E(pitch, 0, 0)
            out[S] = (ball, Rf)
        return out

    def solve_legs(self, q, loc, ch):
        K = self.K
        A, P = K.fk(q, loc, upto='hips')
        res = {}
        for S, (ball, Rf) in self.leg_targets(ch).items():
            th, sh, ft = 'thigh.' + S, 'shin.' + S, 'foot.' + S
            hip = P['hips'] + A['hips'] @ (K.head[th] - K.head['hips'])
            ankle = ball + Rf @ (K.head[ft] - self.ball[S])
            a, b = K.seg(th, sh), K.seg(sh, ft)
            v = ankle - hip
            dist = min(max(v.length, abs(a - b) + 1e-4), (a + b) * .9995)
            u = v.normalized()
            pole = Rf @ Vector((.12 * (1 if S == 'L' else -1), -1, 0))
            pole = (pole - u * pole.dot(u)).normalized()
            ca = (a * a + dist * dist - b * b) / (2 * a * dist)
            sa = math.sqrt(max(0.0, 1 - ca * ca))
            knee = hip + (u * ca + pole * sa) * a
            fwd = Vector((0, -1, 0))
            Rt = _map(K.head[sh] - K.head[th], fwd, knee - hip, pole)
            Rs = _map(K.head[ft] - K.head[sh], fwd, ankle - knee, pole)
            res[th] = A['hips'].inverted() @ Rt
            res[sh] = Rt.inverted() @ Rs
            res[ft] = Rs.inverted() @ Rf
        return res

    def reach(self, q, loc, S, hand=None, aim=None, elbow=(1, -.3, -.6), guess=None, hand_reg=22.0, along=None):
        """Solves upper arm / forearm (flex + twist) / hand of side S so the wrist reaches `hand`
        ((out, fwd, up) from the rest shoulder, arm-length scaled) and the weapon socket points along `aim`."""
        K = self.K
        sh, ua, fa, hd = 'shoulder.' + S, 'upper_arm.' + S, 'forearm.' + S, 'hand.' + S
        A, P = K.fk(q, loc, upto=sh)
        Rroot = A['root']
        if along is not None:
            # On the other hand's weapon line (two-handed staff/blade grips).
            o, dist = along
            Ao, Po = K.fk(q, loc, upto='hand.' + o)
            target = Po['hand.' + o] + (Ao['hand.' + o] @ self.weapon_rest[o]) * dist * self.sa
        else:
            target = loc + Rroot @ (K.head[ua] + self.side(S, hand) * self.sa)
        aim_v = (Rroot @ self.side(S, aim)).normalized() if aim is not None else None
        hint = (Rroot @ self.side(S, elbow)).normalized()
        sgn = 1 if S == 'L' else -1
        g = list(guess) if guess is not None else [-35, -8 * sgn, 0, -60, 0, 0, 0, 0]
        g0 = np.array(g, float)
        scale = np.array([70, 50, 50, 80, 30, hand_reg, hand_reg, hand_reg], float)
        axis = self.fore_axis[S]
        A_sh, P_sh = A[sh], P[sh]
        o_ua = K.head[ua] - K.head[sh]
        o_fa = K.head[fa] - K.head[ua]
        o_hd = K.head[hd] - K.head[fa]
        wrest = self.weapon_rest[S]

        def quats(x):
            r = [math.radians(v) for v in x]
            qu = Euler(r[0:3], 'XYZ').to_quaternion()
            qf = Quaternion((1, 0, 0), r[3]) @ Quaternion(axis, r[4])
            qh = Euler(r[5:8], 'XYZ').to_quaternion()
            return qu, qf, qh

        def resid(x):
            qu, qf, qh = quats(x)
            Au = A_sh @ qu
            Pu = P_sh + A_sh @ o_ua
            Af = Au @ qf
            Pf = Pu + Au @ o_fa
            Ah = Af @ qh
            Ph = Pf + Af @ o_hd
            r = list((Ph - target) / .008)
            if aim_v is not None:
                r += list((Ah @ wrest - aim_v) / .06)
            line = (Ph - Pu)
            if line.length > 1e-6:
                ln = line.normalized()
                off = (Pf - Pu) - ln * (Pf - Pu).dot(ln)
                hp = (hint - ln * hint.dot(ln))
                if off.length > 1e-6 and hp.length > 1e-6:
                    r += list((off.normalized() - hp.normalized()) * .7)
            r += list((x - g0) / scale)
            # Elbow hinge range, forearm twist and wrist range.
            r.append(max(0.0, x[3] - 2) / 2 + max(0.0, -150 - x[3]) / 2)
            r.append(max(0.0, abs(x[4]) - 75) / 2)
            r += [max(0.0, abs(v) - 55) / 3 for v in x[5:8]]
            return np.array(r)

        best = None
        starts = [g0] + ([] if guess is not None else
                         [np.array(v, float) for v in ([-150, -10 * sgn, 0, -40, 0, 0, 0, 0],
                                                        [-80, 0, -30 * sgn, -70, 0, 0, 0, 0],
                                                        [10, 0, 0, -110, 0, 0, 0, 0])])
        for x0 in starts:
            x, cost = self._lm(resid, x0)
            if best is None or cost < best[1]:
                best = (x, cost)
        x = best[0]
        qu, qf, qh = quats(x)
        q[ua], q[fa], q[hd] = qu, qf, qh
        return x

    @staticmethod
    def _lm(resid, x0):
        x = x0.copy()
        mu = 1e-2
        f = resid(x)
        cost = f @ f
        for _ in range(80):
            J = np.empty((len(f), 8))
            for i in range(8):
                dx = np.zeros(8)
                dx[i] = .25
                J[:, i] = (resid(x + dx) - f) / .25
            JTJ, JTf = J.T @ J, J.T @ f
            while True:
                step = np.linalg.solve(JTJ + mu * np.diag(np.diag(JTJ) + 1e-6), -JTf)
                xn = x + step
                fn = resid(xn)
                cn = fn @ fn
                if cn < cost:
                    x, f, cost, mu = xn, fn, cn, max(mu / 3, 1e-7)
                    break
                mu *= 4
                if mu > 1e8:
                    break
            if mu > 1e8 or np.abs(step).max() < 1e-3:
                break
        return x, cost

    # ------------------------------------------------------------ keys
    def key(self, base=None, rot=None, add=None, loc=None, feet=None, arms=None, yaw=None, air=None,
            g=None, ikw=None):
        """One authored pose as channels. base: another key (copied). rot: absolute Euler per bone.
        add: Euler offsets composed onto the base. arms: {S: reach kwargs}. feet: {S: (out, fwd, up, pitch, yaw)}."""
        ch = {n: v.copy() if hasattr(v, 'copy') else v for n, v in (base or self.neutral()).items()}
        for bn, e in (rot or {}).items():
            ch[bn] = E(*e)
        for bn, e in (add or {}).items():
            ch[bn] = E(*e) @ ch[bn]
        if loc is not None:
            ch['@loc'] = tuple(v * self.sl for v in loc)
        for k, v in (('@yaw', yaw), ('@air', air), ('@g', g), ('@ikw', ikw)):
            if v is not None:
                ch[k] = (v * self.sl,) if k == '@air' else (v,)
        for S, v in (feet or {}).items():
            ch['@ik.' + S] = tuple(v)
        if arms:
            q = {n: ch[n] for n in self.bones}
            q['root'] = E(0, 0, ch['@yaw'][0]) @ q['root']
            locv = Vector(ch['@loc'])
            if ch['@ikw'][0] > 0:
                q.update(self.solve_legs(q, locv, ch))
            for S, spec in sorted(arms.items(), key=lambda kv: 'along' in kv[1]):
                self.reach(q, locv, S, **spec)
                for bn in ('upper_arm.', 'forearm.', 'hand.'):
                    ch[bn + S] = q[bn + S]
        return ch

    def neutral(self):
        ch = {n: Quaternion() for n in self.bones}
        ch.update({'@loc': (0, 0, 0), '@yaw': (0,), '@air': (0,), '@g': (0,), '@ikw': (1,),
                   '@ik.L': (0, 0, 0, 0, 0), '@ik.R': (0, 0, 0, 0, 0)})
        return ch

    def resolved(self, ch, **kw):
        """Copy of a key whose legs carry the IK solution as plain rotations (for FK clips such as Die/Revive)."""
        out = dict(ch)
        q = {n: ch[n] for n in self.bones}
        q['root'] = E(0, 0, ch['@yaw'][0]) @ q['root']
        if ch['@ikw'][0] > 0:
            for bn, v in self.solve_legs(q, Vector(ch['@loc']), ch).items():
                out[bn] = v
        out.update({k: (v,) for k, v in kw.items()})
        return out

    # ------------------------------------------------------------ sampling + baking
    LAGS = {'root': 0, 'hips': -.6, 'spine': 0, 'chest': .5, 'neck': 1.0, 'head': 1.6,
            'shoulder.L': .6, 'shoulder.R': .6, 'upper_arm.L': .8, 'upper_arm.R': .8,
            'forearm.L': 1.3, 'forearm.R': 1.3, 'hand.L': 1.8, 'hand.R': 1.8}

    def keyed(self, keys, lags=None, still=()):
        """Sampler over authored keys [(frame, channels)] with per-bone lag (frames; window-faded at both ends)."""
        frames = [f for f, _ in keys]
        names = list(keys[0][1].keys())
        sizes = {n: (4 if isinstance(keys[0][1][n], Quaternion) else len(keys[0][1][n])) for n in names}
        rows = []
        prev = {}
        for _, ch in keys:
            row = []
            for n in names:
                v = ch[n]
                if isinstance(v, Quaternion):
                    v = v.normalized()
                    if n in prev and prev[n].dot(v) < 0:
                        v = -v
                    prev[n] = v
                    row += list(v)
                else:
                    row += list(v)
            rows.append(row)
        track = Track(frames, rows)
        offs, o = {}, 0
        for n in names:
            offs[n] = (o, o + sizes[n])
            o += sizes[n]
        lag = dict(self.LAGS)
        lag.update(lags or {})
        for bn in still:
            lag[bn] = 0
        L = frames[-1]

        def sample(t):
            w = min(_smooth(t / 4.0), _smooth((L - t) / 6.0))
            cache = {}
            ch = {}
            for n in names:
                lg = 0 if n.startswith('@') else lag.get(n, 1.0 if n in self.secondary else 0)
                tt = t - lg * w
                if tt not in cache:
                    cache[tt] = track(tt)
                a, b = offs[n]
                v = cache[tt][a:b]
                ch[n] = Quaternion(v).normalized() if sizes[n] == 4 and isinstance(keys[0][1][n], Quaternion) \
                    else tuple(v)
            return ch
        return sample

    def ground_mesh(self):
        body = self.H.body
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = ev.to_mesh()
        co = np.empty(len(mesh.vertices) * 3)
        mesh.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        M = np.array(ev.matrix_world)
        z = co @ M[2, :3] + M[2, 3]
        ev.to_mesh_clear()
        return float(z.min())

    def apply(self, q, loc):
        rig, K = self.rig, self.K
        for pb in rig.pose.bones:
            b = K.basis[pb.name]
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = b.inverted() @ q.get(pb.name, ID) @ b
            pb.location = b.inverted() @ loc if pb.name == 'root' else Vector((0, 0, 0))
            pb.scale = (1, 1, 1)

    def realize(self, ch):
        q = {n: ch[n] for n in self.bones}
        q['root'] = E(0, 0, ch['@yaw'][0]) @ q['root']
        for n in ('weapon.L', 'weapon.R'):
            q[n] = ID
        loc = Vector(ch['@loc'])
        w = ch['@ikw'][0]
        if w > 1e-4:
            for bn, v in self.solve_legs(q, loc, ch).items():
                q[bn] = v if w >= .9999 else q[bn].slerp(v, w)
        return q, loc

    def secondary_pass(self, q, loc, ch, prev):
        """Cloth bones (cape): hang toward gravity when the torso tips forward (only away from the body), drag
        behind the motion of their parent, lift while falling."""
        if not self.secondary:
            return
        K = self.K
        A, P = K.fk(q, loc)
        g = min(1.0, max(0.0, ch['@g'][0]))
        for bn in self.secondary:
            p = K.parent[bn]
            rest = (K.tail[bn] - K.head[bn]).normalized()
            Ap = A[p]
            f = Ap @ Vector((0, -1, 0))
            yaw = E(0, 0, math.degrees(math.atan2(-f.x, -f.y)) if f.xy.length > 1e-6 else 0)
            d = Ap.inverted() @ (yaw @ rest)
            delta = math.degrees(math.atan2(d.y, -d.z) - math.atan2(rest.y, -rest.z))
            delta = (delta + 180) % 360 - 180
            swing = max(0.0, delta) * .75 * (1 - g)
            if prev is not None:
                v = P[p] - prev[p]
                fwd = (yaw @ Vector((0, -1, 0))).dot(v)
                drag = fwd * 350 + max(0.0, -v.z * 200) * (1 - g)
                swing += min(22.0, max(-6.0, drag))
            q[bn] = E(min(swing, 40.0), 0, 0) @ q[bn]

    def bake(self, name, sample, extra=None):
        rig = self.rig
        length = LENGTHS[name]
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        act.use_frame_range = True
        act.frame_range = (0, length)
        rig.animation_data.action = act
        prev = {}
        heights = []
        loop = name in LOOPS
        for f in range(length + 1):
            ch = sample(float(f))
            q, loc = self.realize(ch)
            if self.secondary:
                tp = (f - 1) % length if loop else max(0, f - 1)
                qp, lp = self.realize(sample(float(tp)))
                before = self.K.fk(qp, lp)[1] if (loop or f > 0) else None
                self.secondary_pass(q, loc, ch, before)
            gm = min(1.0, max(0.0, ch['@g'][0]))
            floor = self.rest_floor
            if gm > 1e-4:
                self.apply(q, loc)
                bpy.context.view_layer.update()
                floor = gm * self.ground_mesh() + (1 - gm) * self.rest_floor
            loc = Vector((loc.x, loc.y, loc.z - floor + ch['@air'][0]))
            for n in q:
                if n in prev and prev[n].dot(q[n]) < 0:
                    q[n] = -q[n]
                prev[n] = q[n]
            self.apply(q, loc)
            heights.append(loc.z)
            for pb in rig.pose.bones:
                pb.keyframe_insert('rotation_quaternion', frame=f, group=pb.name)
                pb.keyframe_insert('location', frame=f, group=pb.name)
                pb.keyframe_insert('scale', frame=f, group=pb.name)
        for curve in act.layers[0].strips[0].channelbag(rig.animation_data.action_slot).fcurves:
            for k in curve.keyframe_points:
                k.interpolation = 'LINEAR'
        act['root_height_keys'] = heights
        act['contact_normalized'] = CONTACT.get(name, -1.0)
        act['loop'] = name in LOOPS
        act['authored_keyframes'] = list((extra or {}).get('keys', range(length + 1)))
        for k, v in (extra or {}).items():
            if k != 'keys':
                act[k] = v
        self.actions[name] = act
        return act

    # ------------------------------------------------------------ build
    def build(self):
        rig = self.rig
        rig.animation_data_create()
        self.actions = {}
        self.apply({}, Vector())
        bpy.context.view_layer.update()
        self.rest_floor = self.ground_mesh()
        stance = self.stance()
        self.st = stance
        self.idle(stance)
        self.locomotion(stance)
        self.attack(stance)
        self.cast(stance)
        self.skill(stance)
        self.ultimate(stance)
        self.hit(stance)
        collapse = self.die(stance)
        self.guard(stance)
        self.revive(stance, collapse)
        self.victory(stance)
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
            pb.scale = (1, 1, 1)
        return self.actions

    # ------------------------------------------------------------ choreography
    # Hand targets: (out, forward, up) from the rest shoulder of that side, in metres of a 1.70 m hero.
    # Weapon aims: (out, forward, up) directions of the socket (blade / staff head / upper bow limb).
    # Feet: (out, forward, up, heel lift deg, toe-out deg) of the ball of the foot from its rest position.
    STANCES = dict(
        warrior=dict(loc=(0, .015, -.075), feet={'L': (.04, .13, 0, 0, 10), 'R': (.04, -.12, 0, 0, 28)},
                     add={'hips': (0, 0, -14), 'spine': (5, 0, 5), 'chest': (4, 0, 5), 'neck': (-2, 0, 2),
                          'head': (-3, 0, 2), 'shoulder.L': (0, 0, -3), 'shoulder.R': (0, 0, 3)},
                     arms={'R': dict(hand=(.05, .26, -.33), aim=(-.25, .75, .62), elbow=(.5, -.3, -.6)),
                           'L': dict(hand=(-.04, .24, -.26), elbow=(.6, -.2, -.6))}),
        archer=dict(loc=(0, .01, -.06), feet={'L': (.03, .11, 0, 0, 12), 'R': (.04, -.10, 0, 0, 26)},
                    add={'hips': (0, 0, -10), 'spine': (4, 0, 4), 'chest': (3, 0, 4), 'neck': (-1, 0, 1),
                         'head': (-3, 0, 1)},
                    arms={'L': dict(hand=(0, .22, -.30), aim=(.08, .25, 1), elbow=(.6, -.2, -.6)),
                          'R': dict(hand=(0, .16, -.34), elbow=(.6, -.3, -.6))}),
        mage=dict(loc=(0, 0, -.045), feet={'L': (.02, .08, 0, 0, 10), 'R': (.03, -.08, 0, 0, 20)},
                  add={'hips': (0, 0, -8), 'spine': (3, 0, 3), 'chest': (2, 0, 3), 'head': (-3, 0, 2)},
                  arms={'R': dict(hand=(.10, .20, -.30), aim=(.22, .12, 1), elbow=(.5, -.3, -.6)),
                        'L': dict(hand=(-.02, .30, -.20), elbow=(.7, -.2, -.5))}),
        cleric=dict(loc=(0, 0, -.045), feet={'L': (.02, .08, 0, 0, 8), 'R': (.03, -.07, 0, 0, 18)},
                    add={'hips': (0, 0, -8), 'spine': (3, 0, 3), 'chest': (2, 0, 3), 'head': (-3, 0, 2)},
                    arms={'R': dict(hand=(.04, .22, -.32), aim=(-.15, .6, .78), elbow=(.5, -.3, -.6)),
                          'L': dict(hand=(-.12, .22, -.14), elbow=(.8, -.2, -.4))}),
    )

    def stance(self):
        sp = self.STANCES[self.style]
        return self.key(add=sp['add'], loc=sp['loc'], feet=sp['feet'], arms=sp['arms'])

    def k(self, add=None, feet=None, base=None, **kw):
        """Key relative to the stance: Euler offsets on the stance pose, feet merged per side."""
        st = self.st
        f = {S: st['@ik.' + S] for S in 'LR'}
        f.update(feet or {})
        return self.key(base=base or st, add=add, feet=f, **kw)

    def stance_feet(self, S, **kw):
        v = list(self.STANCES[self.style]['feet'][S])
        for i, n in enumerate(('out', 'fwd', 'up', 'pitch', 'yaw')):
            if n in kw:
                v[i] = kw[n]
            if 'd' + n in kw:
                v[i] += kw['d' + n]
        return tuple(v)

    # ---- Idle: breathing, weight shift, look-around, relaxed weapon sway on the ready stance
    def idle(self, st):
        L = LENGTHS['Idle']
        Wd, Fd = self.W, self.F
        sg = {'L': 1, 'R': -1}
        sa, sl = self.sa, self.sl

        def sample(t):
            p = math.tau * t / L
            b = math.sin(2 * p)
            b01 = .5 - .5 * math.cos(2 * p)
            w = math.sin(p)
            h = math.sin(p - 1.1)
            off = {
                'hips': (0, -2.4 * w, 1.6 * math.sin(p + .6)),
                'spine': (.6 * b, .8 * w, 0),
                'chest': (-1.6 * b, 1.4 * w, -.9 * math.sin(p + .6)),
                'neck': (.5 * math.sin(2 * p + .5), -.6 * w, 1.5 * h),
                'head': (1.4 * math.sin(2 * p + .9), -.9 * w, 4.5 * h),
                'shoulder.L': (0, -2.2 * b01, 0), 'shoulder.R': (0, 2.2 * b01, 0),
                'upper_arm.' + Wd: (2.2 * math.sin(p + 1.0), 0, 0),
                'forearm.' + Wd: (-3.2 * math.sin(p + 1.4), 0, 0),
                'hand.' + Wd: (3.5 * math.sin(p + 1.9), 0, 1.5 * math.sin(p + 2.2)),
                'upper_arm.' + Fd: (1.6 * math.sin(2 * p + .9), sg[Fd] * -1.2 * b01, 0),
                'forearm.' + Fd: (-2.6 * math.sin(2 * p + 1.3), 0, 0),
                'hand.' + Fd: (2.4 * math.sin(2 * p + 1.7), 0, 0),
            }
            ch = dict(st)
            for bn, e in off.items():
                ch[bn] = E(*e) @ st[bn]
            for i, bn in enumerate(self.secondary):
                ch[bn] = E(math.sin(p + i * .8) * 2, math.sin(p + i) * 1.2, 0) @ st[bn]
            x0, y0, z0 = st['@loc']
            ch['@loc'] = (x0 + .03 * sl * w, y0 + .006 * sl * math.sin(p + 1.3), z0 - .010 * sl * b01)
            return ch
        self.bake('Idle', sample, dict(keys=list(range(0, L + 1, 6))))

    # ---- Walk / Run: heel-toe legs, pelvis yaw and drop, chest counter-rotation, arm swing, run flight
    def locomotion(self, st):
        Wd = self.W
        for name, A, Kn, base_k, arm, fore, yaw, counter, lean, air in (
                ('Walk', 24, 42, 6, 18, -22, 6, 9, 3, 0.0),
                ('Run', 34, 92, 16, 38, -78, 10, 14, 11, .035)):
            L = LENGTHS[name]

            def sample(t, A=A, Kn=Kn, base_k=base_k, arm=arm, fore=fore, yaw=yaw, counter=counter, lean=lean,
                       air=air, L=L, name=name):
                phi = math.tau * t / L
                s, c = math.sin(phi), math.cos(phi)
                rot = {}
                for S, ph in (('L', phi), ('R', phi + math.pi)):
                    sn, cs = math.sin(ph), math.cos(ph)
                    thigh = -A * sn - (3 if name == 'Walk' else 9)
                    shin = base_k + Kn * max(0.0, cs) ** 1.4 + (6 if name == 'Run' else 3) * max(0.0, -cs)
                    net = 8 - 20 * sn + 8 * cs if name == 'Walk' else 14 - 26 * sn + 10 * cs
                    rot['thigh.' + S] = (thigh, 0, 0)
                    rot['shin.' + S] = (shin, 0, 0)
                    rot['foot.' + S] = (net - thigh - shin - lean * .5, 0, 0)
                    sgn = 1 if S == 'L' else -1
                    swing = arm * sn * (.75 if S == Wd else 1)          # opposite to the same-side leg
                    rot['upper_arm.' + S] = (swing, -sgn * (6 if name == 'Walk' else 10), 0)
                    rot['forearm.' + S] = (fore - (8 if name == 'Walk' else 20) * max(0.0, -sn), 0, 0)
                    rot['shoulder.' + S] = (0, 0, sgn * -2.5 * sn)
                rot['hand.' + Wd] = (25 if name == 'Run' else 10, 0, 0)
                rot['hips'] = (lean * .4, 2.5 * c, -yaw * s)
                rot['spine'] = (lean * .5, -1.2 * c, counter * .4 * s)
                rot['chest'] = (lean * .5 - 1.5 * math.cos(2 * phi), -1.2 * c, counter * .6 * s)
                rot['neck'] = (-lean * .4, 0, -counter * .3 * s)
                rot['head'] = (-lean * .5 + 1.5 * math.cos(2 * phi + .6), .8 * c, -counter * .35 * s + yaw * .3 * s)
                for i, bn in enumerate(self.secondary):
                    rot[bn] = (math.sin(phi + 1 + i * .8) * 6 + (14 if name == 'Run' else 4), math.sin(phi + 1 + i) * 3.5, 0)
                ch = self.neutral()
                for bn, e in rot.items():
                    ch[bn] = E(*e)
                ch['@loc'] = (-.012 * self.sl * c if name == 'Walk' else -.006 * self.sl * c, 0, 0)
                ch['@air'] = (air * self.sl * max(0.0, abs(s) - .25) / .75,)
                ch['@g'] = (1.0,)
                ch['@ikw'] = (0.0,)
                return ch
            self.bake(name, sample, dict(keys=list(range(0, L + 1, L // 8))))

    # ---- Attack: anticipation, fast strike at 40 %, follow-through overshoot, recovery
    def attack(self, st):
        k, sf, W, F = self.k, self.stance_feet, self.W, self.F
        style = self.style
        keys = [(0, st)]
        if style == 'warrior':
            # Big diagonal slash: sword cocked over the right shoulder, lunge step, cut down to the left.
            keys += [
                (4, k(add={'hips': (0, 0, -10), 'spine': (-3, 0, -4), 'chest': (-5, 0, -6), 'head': (0, 0, 10),
                           'shoulder.R': (0, 6, 0)},
                      loc=(0, .03, -.065),
                      arms={'R': dict(hand=(.08, -.02, .10), aim=(.3, -.45, .85), elbow=(.6, .2, -.3)),
                            'L': dict(hand=(-.02, .34, -.12), elbow=(.6, -.2, -.5))})),
                (8, k(add={'hips': (0, 0, -18), 'spine': (-4, 0, -6), 'chest': (-6, 0, -10), 'head': (2, 0, 16),
                           'shoulder.R': (0, 10, 0)},
                      loc=(0, .04, -.075),
                      arms={'R': dict(hand=(.04, -.06, .26), aim=(.2, -.8, .5), elbow=(.7, .1, .1)),
                            'L': dict(hand=(-.06, .42, -.02), elbow=(.6, -.2, -.5))})),
                (10, k(add={'hips': (2, 0, 2), 'spine': (2, 0, 0), 'chest': (-2, 0, -6), 'head': (0, 0, 6),
                            'shoulder.R': (0, 8, 0)},
                       loc=(0, -.03, -.085), feet={'L': sf('L', dfwd=.08, up=.06)},
                       arms={'R': dict(hand=(.0, .06, .22), aim=(.1, -.3, .95), elbow=(.8, -.1, 0)),
                             'L': dict(hand=(-.02, .30, -.12), elbow=(.6, -.2, -.5))})),
                (ATTACK_HIT, k(add={'hips': (6, 0, 26), 'spine': (8, 0, 8), 'chest': (10, 0, 10), 'neck': (0, 0, -4),
                                    'head': (4, 0, -14)},
                               loc=(0, -.11, -.10), feet={'L': sf('L', dfwd=.14)},
                               arms={'R': dict(hand=(-.14, .44, -.20), aim=(-.5, .8, -.25), elbow=(.6, -.3, -.6)),
                                     'L': dict(hand=(.06, -.06, -.34), elbow=(.5, -.8, -.2))})),
                (15, k(add={'hips': (8, 0, 34), 'spine': (10, 0, 10), 'chest': (12, 0, 14), 'neck': (0, 0, -5),
                            'head': (6, 0, -18)},
                       loc=(0, -.12, -.11), feet={'L': sf('L', dfwd=.14)},
                       arms={'R': dict(hand=(-.30, .30, -.40), aim=(-.75, .35, -.55), elbow=(.6, -.3, -.6)),
                             'L': dict(hand=(.08, -.10, -.30), elbow=(.5, -.8, -.2))})),
            ]
        elif style == 'archer':
            # Turn side-on, raise the bow, draw to the cheek, release at 40 % (string hand flies back), lower.
            bow = lambda h, a: dict(hand=h, aim=a, elbow=(.7, .1, -.5))  # noqa: E731
            keys += [
                (4, k(add={'hips': (0, 0, -22), 'spine': (0, 0, -10), 'chest': (-2, 0, -12), 'neck': (0, 0, 10),
                           'head': (2, 0, 30)},
                      feet={'R': sf('R', yaw=40)},
                      arms={'L': bow((-.10, .44, 0), (.15, .05, 1)),
                            'R': dict(hand=(-.16, .36, -.02), elbow=(.6, -.2, .2))})),
                (7, k(add={'hips': (0, 0, -24), 'spine': (-1, 0, -10), 'chest': (-3, 0, -14), 'neck': (0, 0, 11),
                           'head': (2, 0, 33)},
                      feet={'R': sf('R', yaw=44)},
                      arms={'L': bow((-.10, .46, .02), (.15, .05, 1)),
                            'R': dict(hand=(-.10, .12, .08), elbow=(.5, -.8, .3))})),
                (10, k(add={'hips': (0, 0, -25), 'spine': (-3, 0, -10), 'chest': (-5, 0, -15), 'neck': (0, 0, 11),
                            'head': (0, 0, 34)},
                       feet={'R': sf('R', yaw=45)},
                       arms={'L': bow((-.10, .46, .02), (.15, .05, 1)),
                             'R': dict(hand=(-.11, .06, .11), elbow=(.5, -.85, .15))})),
                (ATTACK_HIT, k(add={'hips': (0, 0, -25), 'spine': (-4, 0, -10), 'chest': (-8, 0, -17),
                                    'neck': (0, 0, 11), 'head': (-1, 0, 35)},
                               loc=(0, -.01, -.04), feet={'R': sf('R', yaw=45)},
                               arms={'L': bow((-.10, .47, -.01), (.1, .35, .93)),
                                     'R': dict(hand=(.02, -.06, .13), elbow=(.5, -.8, 0))})),
                (16, k(add={'hips': (0, 0, -24), 'spine': (-2, 0, -10), 'chest': (-5, 0, -15), 'neck': (0, 0, 10),
                            'head': (0, 0, 33)},
                       loc=(0, -.015, -.045), feet={'R': sf('R', yaw=44)},
                       arms={'L': bow((-.10, .45, -.02), (.12, .25, .96)),
                             'R': dict(hand=(.06, -.10, .06), elbow=(.5, -.8, -.2))})),
                (22, k(add={'hips': (0, 0, -10), 'spine': (0, 0, -4), 'chest': (0, 0, -6), 'head': (0, 0, 12)},
                       feet={'R': sf('R', yaw=34)},
                       arms={'L': bow((-.02, .32, -.18), (.1, .2, 1)),
                             'R': dict(hand=(0, .12, -.25), elbow=(.6, -.3, -.6))})),
            ]
        elif style == 'mage':
            # Two-handed staff thrust: pull back to the hip, lunge, drive the staff head into the target.
            keys += [
                (5, k(add={'hips': (0, 0, -18), 'spine': (-4, 0, -6), 'chest': (-4, 0, -6), 'head': (0, 0, 14)},
                      loc=(0, .04, -.05),
                      arms={'R': dict(hand=(.10, -.10, -.24), aim=(-.10, .95, .30), elbow=(.5, -.6, -.3)),
                            'L': dict(along=('R', .30), elbow=(.6, -.2, -.6))})),
                (9, k(add={'hips': (0, 0, -22), 'spine': (-5, 0, -7), 'chest': (-5, 0, -8), 'head': (0, 0, 17)},
                      loc=(0, .05, -.06), feet={'L': sf('L', dfwd=.04, up=.04)},
                      arms={'R': dict(hand=(.12, -.14, -.22), aim=(-.10, .95, .30), elbow=(.5, -.6, -.3)),
                            'L': dict(along=('R', .30), elbow=(.6, -.2, -.6))})),
                (ATTACK_HIT, k(add={'hips': (4, 0, 16), 'spine': (8, 0, 6), 'chest': (8, 0, 6), 'head': (2, 0, -10)},
                               loc=(0, -.10, -.08), feet={'L': sf('L', dfwd=.10)},
                               arms={'R': dict(hand=(-.02, .40, -.14), aim=(-.05, .97, .22), elbow=(.5, -.3, -.6)),
                                     'L': dict(along=('R', .30), elbow=(.6, -.2, -.6))})),
                (15, k(add={'hips': (5, 0, 20), 'spine': (9, 0, 7), 'chest': (9, 0, 7), 'head': (2, 0, -12)},
                       loc=(0, -.12, -.09), feet={'L': sf('L', dfwd=.10)},
                       arms={'R': dict(hand=(-.03, .46, -.12), aim=(-.05, .95, .30), elbow=(.5, -.3, -.6)),
                             'L': dict(along=('R', .30), elbow=(.6, -.2, -.6))})),
            ]
        else:
            # Cleric: horizontal mace swing from behind the right shoulder through the target to the left.
            keys += [
                (6, k(add={'hips': (0, 0, -24), 'spine': (-2, 0, -8), 'chest': (-3, -2, -10), 'head': (0, 0, 18),
                           'shoulder.R': (0, 6, 0)},
                      loc=(0, .03, -.06),
                      arms={'R': dict(hand=(.22, -.10, -.02), aim=(.55, -.45, .70), elbow=(.6, .1, -.4)),
                            'L': dict(hand=(-.05, .36, -.10), elbow=(.6, -.2, -.5))})),
                (9, k(add={'hips': (2, 0, -10), 'spine': (0, 0, -6), 'chest': (-2, -2, -8), 'head': (0, 0, 12),
                           'shoulder.R': (0, 6, 0)},
                      loc=(0, -.01, -.075), feet={'L': sf('L', dfwd=.06, up=.05)},
                      arms={'R': dict(hand=(.24, .10, -.06), aim=(.85, .2, .5), elbow=(.6, -.1, -.4)),
                            'L': dict(hand=(-.02, .30, -.14), elbow=(.6, -.2, -.5))})),
                (ATTACK_HIT, k(add={'hips': (6, 0, 22), 'spine': (6, 0, 8), 'chest': (8, 0, 10), 'head': (2, 0, -12)},
                               loc=(0, -.09, -.08), feet={'L': sf('L', dfwd=.11)},
                               arms={'R': dict(hand=(-.10, .42, -.12), aim=(-.25, .95, .15), elbow=(.6, -.3, -.6)),
                                     'L': dict(hand=(.08, -.06, -.30), elbow=(.5, -.8, -.2))})),
                (15, k(add={'hips': (8, 0, 34), 'spine': (8, 0, 10), 'chest': (10, 0, 14), 'head': (4, 0, -16)},
                       loc=(0, -.10, -.09), feet={'L': sf('L', dfwd=.11)},
                       arms={'R': dict(hand=(-.34, .26, -.18), aim=(-.95, .15, .05), elbow=(.6, -.3, -.6)),
                             'L': dict(hand=(.10, -.10, -.28), elbow=(.5, -.8, -.2))})),
            ]
        if style != 'archer':
            # Recover: ease the torso back, bring the lead foot home, settle into the stance.
            keys += [
                (21, k(add={'hips': (3, 0, 12), 'spine': (4, 0, 4), 'chest': (4, 0, 4), 'head': (2, 0, -6)},
                       loc=(0, -.06, -.075), feet={'L': sf('L', dfwd=.06, up=.045)},
                       arms={W: dict(hand=(-.02, .30, -.30), aim=(-.25, .8, .45) if style != 'mage'
                                     else (-.05, .3, .95), elbow=(.5, -.3, -.6)),
                             F: dict(hand=(-.02, .26, -.24), elbow=(.6, -.2, -.6))})),
                (25, k(add={'hips': (0, 0, 3), 'chest': (1, 0, 1)}, loc=(0, .005, -.055))),
            ]
        keys.append((LENGTHS['Attack'], st))
        lags = {'upper_arm.' + W: 0, 'forearm.' + W: 0, 'hand.' + W: 0}
        if style == 'archer':
            lags.update({'upper_arm.L': 0, 'forearm.L': .3, 'hand.L': .5, 'upper_arm.R': 0, 'forearm.R': 0,
                         'hand.R': 0})
        self.bake('Attack', self.keyed(keys, lags), dict(keys=[f for f, _ in keys]))

    # ---- Cast: gather (arms in, crouch), rise on the toes leaning back, release forward/up at 60 %, settle
    AIMS = dict(warrior=((0, .1, 1), (0, -.5, .87), (0, .75, .66)),
                archer=((.1, .05, 1), (.1, -.2, 1), (.05, .45, .9)),
                mage=((0, .1, 1), (0, -.35, .94), (0, .75, .66)),
                cleric=((0, .1, 1), (0, -.45, .9), (0, .7, .7)))

    def cast(self, st):
        k, sf, W, F = self.k, self.stance_feet, self.W, self.F
        a_in, a_up, a_rel = self.AIMS[self.style]
        toes = lambda p: {S: sf(S, pitch=p) for S in 'LR'}  # noqa: E731
        fwd = {'shoulder.L': (0, 0, -8), 'shoulder.R': (0, 0, 8)}
        keys = [
            (0, st),
            (8, k(add=dict(fwd, hips=(2, 0, 8), spine=(6, 0, 2), chest=(8, 0, 2), neck=(4, 0, 0), head=(10, 0, -2)),
                  loc=(0, .01, -.09),
                  arms={W: dict(hand=(-.12, .20, -.22), aim=a_in, elbow=(.7, -.2, -.5)),
                        F: dict(hand=(-.12, .22, -.18), elbow=(.7, -.2, -.5))})),
            (16, k(add={'hips': (-2, 0, 6), 'spine': (-4, 0, 0), 'chest': (-6, 0, 0), 'neck': (-4, 0, 0),
                        'head': (-8, 0, 0), 'shoulder.L': (0, -4, 0), 'shoulder.R': (0, 4, 0)},
                   loc=(0, .02, -.01), feet=toes(10),
                   arms={W: dict(hand=(-.04, .18, .02), aim=a_in, elbow=(.8, -.1, -.4)),
                         F: dict(hand=(.02, .20, .04), elbow=(.8, -.1, -.4))})),
            (21, k(add={'hips': (-3, 0, 6), 'spine': (-8, 0, 0), 'chest': (-12, 0, 0), 'neck': (-4, 0, 0),
                        'head': (-12, 0, 0), 'shoulder.L': (0, -8, 0), 'shoulder.R': (0, 8, 0)},
                   loc=(0, .04, .005), feet=toes(16),
                   arms={W: dict(hand=(.10, .02, .42), aim=a_up, elbow=(.9, -.1, .1)),
                         F: dict(hand=(.14, .04, .36), elbow=(.9, -.1, .1))})),
            (22, k(add={'hips': (-1, 0, 7), 'spine': (-6, 0, 0), 'chest': (-9, 0, 0), 'neck': (-3, 0, 0),
                        'head': (-10, 0, 0), 'shoulder.L': (0, -7, 0), 'shoulder.R': (0, 7, 0)},
                   loc=(0, .02, -.01), feet={'L': sf('L', dfwd=.04, up=.04, pitch=8), 'R': sf('R', pitch=12)},
                   arms={W: dict(hand=(.09, .06, .40), aim=a_up, elbow=(.9, -.1, .1)),
                         F: dict(hand=(.13, .08, .34), elbow=(.9, -.1, .1))})),
            (CAST_RELEASE, k(add=dict(fwd, hips=(2, 0, 10), spine=(6, 0, 0), chest=(8, 0, -2), neck=(-2, 0, 0),
                                      head=(-10, 0, 0)),
                             loc=(0, -.07, -.05), feet={'L': sf('L', dfwd=.08)},
                             arms={W: dict(hand=(.02, .44, .0), aim=a_rel, elbow=(.6, -.2, -.6)),
                                   F: dict(hand=(.0, .46, -.02), elbow=(.6, -.2, -.6))})),
            (28, k(add=dict(fwd, hips=(3, 0, 11), spine=(7, 0, 0), chest=(10, 0, -2), neck=(-2, 0, 0),
                            head=(-9, 0, 0)),
                   loc=(0, -.08, -.06), feet={'L': sf('L', dfwd=.08)},
                   arms={W: dict(hand=(.02, .47, -.03), aim=a_rel, elbow=(.6, -.2, -.6)),
                         F: dict(hand=(-.01, .48, -.05), elbow=(.6, -.2, -.6))})),
            (33, k(add={'hips': (1, 0, 6), 'spine': (5, 0, 0), 'chest': (7, 0, -1), 'head': (0, 0, 0)},
                   loc=(0, -.05, -.06), feet={'L': sf('L', dfwd=.04, up=.04)},
                   arms={W: dict(hand=(-.02, .36, -.10), aim=a_in, elbow=(.6, -.2, -.6)),
                         F: dict(hand=(-.04, .32, -.12), elbow=(.6, -.2, -.6))})),
            (LENGTHS['Cast'], st),
        ]
        lags = {'upper_arm.' + W: 0, 'forearm.' + W: 0, 'hand.' + W: 0}
        self.bake('Cast', self.keyed(keys, lags), dict(keys=[f for f, _ in keys]))

    # ---- Skill: each hero's signature technique (contact at 50 %), bigger than the basic Attack
    def skill(self, st):
        k, sf, W, F = self.k, self.stance_feet, self.W, self.F
        style = self.style
        toes = lambda p: {S: sf(S, pitch=p) for S in 'LR'}  # noqa: E731
        two = lambda h, a: {W: dict(hand=h, aim=a, elbow=(.7, -.1, -.3)), F: dict(along=(W, .26), elbow=(.6, -.2, -.6))}  # noqa: E731
        H = SKILL_HIT
        if style in ('warrior', 'cleric'):
            # Leaping overhead smash: drop into a crouch, spring up with the weapon raised in both hands,
            # arch back at the apex and drive it down as the feet land.
            lift = .30 if style == 'warrior' else .22
            keys = [
                (0, st),
                (5, k(add={'hips': (10, 0, -8), 'spine': (10, 0, -2), 'chest': (10, 0, -4), 'head': (-6, 0, 4)},
                      loc=(0, .04, -.17),
                      arms={W: dict(hand=(.12, -.12, -.26), aim=(.3, -.7, -.6), elbow=(.6, .2, -.4)),
                            F: dict(hand=(-.04, .30, -.22), elbow=(.6, -.2, -.5))})),
                (9, k(add={'hips': (-4, 0, 0), 'spine': (-6, 0, 0), 'chest': (-8, 0, 0), 'head': (-8, 0, 0)},
                      loc=(0, -.04, 0), air=lift * .7, feet=toes(20),
                      arms=two((.02, .08, .40), (0, -.25, .97)))),
                (13, k(add={'hips': (-6, 0, 0), 'spine': (-8, 0, 0), 'chest': (-14, 0, 0), 'neck': (-4, 0, 0),
                            'head': (-10, 0, 0)},
                       loc=(0, -.10, 0), air=lift, feet={'L': sf('L', dfwd=.06, up=.08, pitch=14),
                                                         'R': sf('R', up=.12, pitch=24)},
                       arms=two((.02, -.04, .44), (0, -.85, .5)))),
                (16, k(add={'hips': (4, 0, 0), 'spine': (6, 0, 0), 'chest': (6, 0, 0), 'head': (2, 0, 0)},
                       loc=(0, -.16, -.04), air=lift * .45, feet={'L': sf('L', dfwd=.12, up=.04)},
                       arms=two((.0, .30, .30), (0, .35, .94)))),
                (H, k(add={'hips': (10, 0, 0), 'spine': (10, 0, 0), 'chest': (14, 0, 0), 'neck': (-2, 0, 0),
                           'head': (-4, 0, 0)},
                      loc=(0, -.20, -.19), feet={'L': sf('L', dfwd=.16)},
                      arms=two((.0, .42, -.26), (0, .65, -.76)))),
                (23, k(add={'hips': (12, 0, 0), 'spine': (12, 0, 0), 'chest': (16, 0, 0), 'head': (-2, 0, 0)},
                       loc=(0, -.21, -.21), feet={'L': sf('L', dfwd=.16)},
                       arms=two((.0, .44, -.30), (0, .6, -.8)))),
                (29, k(add={'hips': (6, 0, 6), 'spine': (6, 0, 2), 'chest': (6, 0, 2), 'head': (2, 0, -2)},
                       loc=(0, -.09, -.09), feet={'L': sf('L', dfwd=.07, up=.04)})),
                (LENGTHS['Skill'], st),
            ]
        elif style == 'archer':
            # Power shot: hop back into a wide low stance, heave the draw past the ear, hold, loose with a recoil.
            bow = lambda h, a: dict(hand=h, aim=a, elbow=(.7, .1, -.5))  # noqa: E731
            wide = {'L': sf('L', dfwd=.06, dout=.06), 'R': sf('R', dfwd=-.06, dout=.08, yaw=50)}
            keys = [
                (0, st),
                (4, k(add={'hips': (6, 0, -18), 'spine': (4, 0, -8), 'chest': (2, 0, -10), 'head': (0, 0, 24)},
                      loc=(0, .10, -.04), air=.10, feet=toes(16),
                      arms={'L': bow((-.06, .36, -.06), (.15, .1, 1)), 'R': dict(hand=(-.14, .30, -.06), elbow=(.6, -.2, .2))})),
                (8, k(add={'hips': (8, 0, -30), 'spine': (2, 0, -12), 'chest': (-2, 0, -16), 'neck': (0, 0, 12),
                           'head': (0, 0, 38)},
                      loc=(0, .14, -.17), feet=wide,
                      arms={'L': bow((-.10, .48, .04), (.18, .05, 1)), 'R': dict(hand=(-.10, .14, .10), elbow=(.5, -.8, .3))})),
                (13, k(add={'hips': (8, 0, -32), 'spine': (0, 0, -12), 'chest': (-6, 0, -18), 'neck': (0, 0, 12),
                            'head': (-2, 0, 40)},
                       loc=(0, .14, -.18), feet=wide,
                       arms={'L': bow((-.10, .50, .05), (.15, .3, .94)), 'R': dict(hand=(.06, -.12, .14), elbow=(.5, -.85, .1))})),
                (16, k(add={'hips': (8, 0, -32), 'spine': (0, 0, -12), 'chest': (-7, 0, -18), 'neck': (0, 0, 12),
                            'head': (-2, 0, 40)},
                       loc=(0, .145, -.185), feet=wide,
                       arms={'L': bow((-.10, .50, .05), (.15, .3, .94)), 'R': dict(hand=(.07, -.14, .14), elbow=(.5, -.85, .1))})),
                (H, k(add={'hips': (4, 0, -28), 'spine': (-6, 0, -12), 'chest': (-12, 0, -18), 'neck': (0, 0, 12),
                           'head': (-4, 0, 38)},
                      loc=(0, .20, -.15), feet=wide,
                      arms={'L': bow((-.10, .50, .08), (.1, .45, .89)), 'R': dict(hand=(.16, -.26, .10), elbow=(.4, -.8, .2))})),
                (24, k(add={'hips': (2, 0, -26), 'spine': (-4, 0, -10), 'chest': (-8, 0, -16), 'neck': (0, 0, 10),
                            'head': (-2, 0, 34)},
                       loc=(0, .19, -.14), feet=wide,
                       arms={'L': bow((-.08, .46, .02), (.12, .3, .95)), 'R': dict(hand=(.18, -.24, -.06), elbow=(.5, -.8, -.2))})),
                (30, k(add={'hips': (0, 0, -10), 'spine': (0, 0, -4), 'chest': (0, 0, -6), 'head': (0, 0, 12)},
                       loc=(0, .06, -.07), feet={'R': sf('R', yaw=34)},
                       arms={'L': bow((-.02, .32, -.18), (.1, .2, 1)), 'R': dict(hand=(0, .12, -.25), elbow=(.6, -.3, -.6))})),
                (LENGTHS['Skill'], st),
            ]
        else:
            # Mage: staff whirled overhead with a twist of the body, then slammed head-first into the floor (shockwave).
            keys = [
                (0, st),
                (5, k(add={'hips': (4, 0, -10), 'spine': (4, 0, -4), 'chest': (2, 0, -6), 'head': (-4, 0, 8)},
                      loc=(0, .02, -.08),
                      arms=two((.10, .10, .30), (.3, .2, .93)))),
                (9, k(add={'hips': (-2, 0, 0), 'chest': (-8, 0, 0), 'head': (-12, 0, 0)},
                      loc=(0, 0, -.01), yaw=55, air=.06, feet=toes(16),
                      arms=two((.04, .06, .44), (.9, .1, .4)))),
                (13, k(add={'hips': (-2, 0, 0), 'chest': (-10, 0, 0), 'head': (-12, 0, 0)},
                       loc=(0, 0, -.01), yaw=-45, air=.10, feet=toes(20),
                       arms=two((.04, .02, .46), (-.9, -.2, .4)))),
                (16, k(add={'hips': (2, 0, 0), 'spine': (2, 0, 0), 'chest': (-4, 0, 0), 'head': (-6, 0, 0)},
                       loc=(0, -.04, -.04), yaw=0, air=.04,
                       arms=two((.0, .16, .42), (0, -.4, .92)))),
                (H, k(add={'hips': (16, 0, 0), 'spine': (14, 0, 0), 'chest': (16, 0, 0), 'head': (6, 0, 0)},
                      loc=(0, -.14, -.20), feet={'L': sf('L', dfwd=.12)},
                      arms=two((.0, .40, -.24), (0, .45, -.89)))),
                (24, k(add={'hips': (18, 0, 0), 'spine': (16, 0, 0), 'chest': (18, 0, 0), 'head': (8, 0, 0)},
                       loc=(0, -.15, -.22), feet={'L': sf('L', dfwd=.12)},
                       arms=two((.0, .42, -.28), (0, .4, -.92)))),
                (30, k(add={'hips': (6, 0, 4), 'spine': (5, 0, 2), 'chest': (5, 0, 2)},
                       loc=(0, -.06, -.08), feet={'L': sf('L', dfwd=.06, up=.04)})),
                (LENGTHS['Skill'], st),
            ]
        lags = {'upper_arm.' + W: 0, 'forearm.' + W: 0, 'hand.' + W: 0}
        if style == 'archer':
            lags.update({'upper_arm.L': 0, 'forearm.L': .3, 'hand.L': .5, 'upper_arm.R': 0, 'forearm.R': 0, 'hand.R': 0})
        self.bake('Skill', self.keyed(keys, lags), dict(keys=[f for f, _ in keys]))

    # ---- Ultimate: power up (0-28, plays under the cut-in), crouch, launch, finisher at 44, settle
    def ultimate(self, st):
        k, sf, W, F = self.k, self.stance_feet, self.W, self.F
        style = self.style
        toes = lambda p: {S: sf(S, pitch=p) for S in 'LR'}  # noqa: E731
        two = lambda h, a: {W: dict(hand=h, aim=a, elbow=(.7, -.1, -.3)), F: dict(along=(W, .26), elbow=(.6, -.2, -.6))}  # noqa: E731
        wide = {'L': sf('L', dout=.07, dfwd=.04), 'R': sf('R', dout=.07, dfwd=-.04)}
        up_aim = (.1, .3, 1) if style == 'archer' else (0, .1, 1)
        # 1) gather: fold inward, head down, weapon low
        gather = k(add={'hips': (12, 0, 0), 'spine': (12, 0, 0), 'chest': (14, 0, 0), 'neck': (6, 0, 0), 'head': (16, 0, 0),
                        'shoulder.L': (0, 0, -8), 'shoulder.R': (0, 0, 8)},
                   loc=(0, .02, -.16), feet=wide,
                   arms={W: dict(hand=(-.14, .18, -.30), aim=(0, .3, -.95) if style != 'archer' else (.1, .2, 1), elbow=(.6, -.2, -.6)),
                         F: dict(hand=(-.14, .20, -.28), elbow=(.6, -.2, -.6))})
        # 2) burst: chest thrown open, arms flung up and out in a V, chin up (the aura flare)
        burst = k(add={'hips': (-6, 0, 0), 'spine': (-8, 0, 0), 'chest': (-16, 0, 0), 'neck': (-6, 0, 0), 'head': (-14, 0, 0),
                       'shoulder.L': (0, -10, 6), 'shoulder.R': (0, 10, -6)},
                  loc=(0, .03, -.08), feet=wide,
                  arms={W: dict(hand=(.30, .08, .30), aim=up_aim if style != 'warrior' else (.5, .2, .84), elbow=(.7, -.2, -.5)),
                        F: dict(hand=(.30, .08, .30), elbow=(.7, -.2, -.5))})
        burst2 = k(base=burst, add={'chest': (-3, 0, 0), 'head': (-2, 0, 0)}, loc=(0, .03, -.075), feet=wide,
                   arms={W: dict(hand=(.31, .10, .35), aim=up_aim if style != 'warrior' else (.5, .2, .84), elbow=(.7, -.2, -.5)),
                         F: dict(hand=(.31, .10, .35), elbow=(.7, -.2, -.5))})
        crouch = k(add={'hips': (14, 0, -6), 'spine': (12, 0, 0), 'chest': (12, 0, -4), 'head': (-8, 0, 4)},
                   loc=(0, .05, -.20), feet=wide,
                   arms={W: dict(hand=(.14, -.12, -.24), aim=(.3, -.7, -.6) if style in ('warrior', 'cleric') else up_aim, elbow=(.6, .2, -.4)),
                         F: dict(hand=(-.02, .30, -.24), elbow=(.6, -.2, -.5))})
        keys = [(0, st), (8, gather), (14, gather), (18, burst), (24, burst2), (ULT_RESUME, burst2), (32, crouch)]
        if style in ('warrior', 'cleric'):
            # Sky-splitting leap: launch, weapon high overhead, arch, plunge into a crater-making strike.
            keys += [
                (36, k(add={'hips': (-4, 0, 0), 'chest': (-10, 0, 0), 'head': (-10, 0, 0)}, loc=(0, -.06, 0), air=.42,
                       feet=toes(24), arms=two((.02, .06, .44), (0, -.3, .95)))),
                (40, k(add={'hips': (-8, 0, 0), 'spine': (-10, 0, 0), 'chest': (-18, 0, 0), 'neck': (-6, 0, 0), 'head': (-12, 0, 0)},
                       loc=(0, -.12, 0), air=.55, feet={'L': sf('L', dfwd=.08, up=.10, pitch=16), 'R': sf('R', up=.16, pitch=28)},
                       arms=two((.02, -.08, .46), (0, -.92, .38)))),
                (42, k(add={'hips': (6, 0, 0), 'spine': (8, 0, 0), 'chest': (10, 0, 0)}, loc=(0, -.18, -.02), air=.25,
                       feet={'L': sf('L', dfwd=.12, up=.06)}, arms=two((.0, .34, .34), (0, .4, .92)))),
                (ULT_HIT, k(add={'hips': (13, 0, 0), 'spine': (12, 0, 0), 'chest': (16, 0, 0), 'neck': (-2, 0, 0), 'head': (-4, 0, 0)},
                            loc=(0, -.22, -.24), feet={'L': sf('L', dfwd=.18), 'R': sf('R', dfwd=-.06)},
                            arms=two((.0, .44, -.30), (0, .6, -.8)))),
                (52, k(add={'hips': (14, 0, 0), 'spine': (13, 0, 0), 'chest': (17, 0, 0), 'head': (-2, 0, 0)},
                       loc=(0, -.23, -.26), feet={'L': sf('L', dfwd=.18), 'R': sf('R', dfwd=-.06)},
                       arms=two((.0, .46, -.32), (0, .58, -.81)))),
            ]
        elif style == 'archer':
            # Heaven shot: spring high, turn side-on in the air, full draw aimed down-range, loose at the top.
            bow = lambda h, a: dict(hand=h, aim=a, elbow=(.7, .1, -.5))  # noqa: E731
            keys += [
                (36, k(add={'hips': (0, 0, -20), 'chest': (-6, 0, -10), 'head': (0, 0, 24)}, loc=(0, .02, 0), air=.40,
                       feet=toes(24), arms={'L': bow((-.08, .40, .10), (.15, .1, 1)), 'R': dict(hand=(-.12, .30, .06), elbow=(.6, -.2, .2))})),
                (40, k(add={'hips': (0, 0, -28), 'spine': (-2, 0, -10), 'chest': (-6, 0, -16), 'neck': (0, 0, 12), 'head': (0, 0, 36)},
                       loc=(0, .04, 0), air=.58, feet={'L': sf('L', up=.14, pitch=20), 'R': sf('R', up=.10, pitch=16, yaw=44)},
                       arms={'L': bow((-.10, .48, .06), (.15, .3, .94)), 'R': dict(hand=(.06, -.12, .14), elbow=(.5, -.85, .1))})),
                (ULT_HIT, k(add={'hips': (0, 0, -28), 'spine': (-6, 0, -10), 'chest': (-12, 0, -16), 'neck': (0, 0, 12), 'head': (-2, 0, 36)},
                            loc=(0, .08, 0), air=.52, feet={'L': sf('L', up=.12, pitch=20), 'R': sf('R', up=.10, pitch=16, yaw=44)},
                            arms={'L': bow((-.10, .50, .08), (.1, .5, .86)), 'R': dict(hand=(.18, -.28, .10), elbow=(.4, -.8, .2))})),
                (50, k(add={'hips': (8, 0, -16), 'spine': (6, 0, -6), 'chest': (4, 0, -8), 'head': (0, 0, 18)},
                       loc=(0, .10, -.18), feet=wide,
                       arms={'L': bow((-.06, .40, -.04), (.1, .3, .95)), 'R': dict(hand=(.16, -.20, -.10), elbow=(.5, -.8, -.2))})),
                (54, k(add={'hips': (6, 0, -14), 'spine': (4, 0, -6), 'chest': (2, 0, -8), 'head': (0, 0, 16)},
                       loc=(0, .10, -.16), feet=wide,
                       arms={'L': bow((-.06, .38, -.06), (.1, .3, .95)), 'R': dict(hand=(.10, -.10, -.18), elbow=(.5, -.8, -.2))})),
            ]
        else:
            # Mage: rise off the floor, staff and free hand raised to the sky, then thrust forward to unleash.
            keys += [
                (36, k(add={'hips': (-4, 0, 0), 'chest': (-10, 0, 0), 'head': (-14, 0, 0)}, loc=(0, 0, -.02), air=.16,
                       feet=toes(30), arms={W: dict(hand=(.06, .04, .46), aim=(0, .05, 1), elbow=(.8, -.1, -.2)),
                                            F: dict(hand=(.10, .06, .44), elbow=(.8, -.1, -.2))})),
                (40, k(add={'hips': (-6, 0, 0), 'spine': (-6, 0, 0), 'chest': (-14, 0, 0), 'head': (-18, 0, 0)}, loc=(0, .02, -.02),
                       air=.30, feet=toes(36), arms={W: dict(hand=(.08, .0, .48), aim=(0, -.1, 1), elbow=(.8, -.1, -.2)),
                                                    F: dict(hand=(.14, .02, .46), elbow=(.8, -.1, -.2))})),
                (ULT_HIT, k(add={'hips': (4, 0, 0), 'spine': (8, 0, 0), 'chest': (10, 0, 0), 'head': (-6, 0, 0),
                                 'shoulder.L': (0, 0, -8), 'shoulder.R': (0, 0, 8)},
                            loc=(0, -.10, -.02), air=.26, feet=toes(30),
                            arms={W: dict(hand=(.04, .48, .04), aim=(0, .8, .6), elbow=(.6, -.2, -.6)),
                                  F: dict(hand=(-.02, .50, .02), elbow=(.6, -.2, -.6))})),
                (52, k(add={'hips': (5, 0, 0), 'spine': (9, 0, 0), 'chest': (11, 0, 0), 'head': (-5, 0, 0)},
                       loc=(0, -.11, -.03), air=.22, feet=toes(28),
                       arms={W: dict(hand=(.04, .50, .02), aim=(0, .8, .6), elbow=(.6, -.2, -.6)),
                             F: dict(hand=(-.02, .52, 0), elbow=(.6, -.2, -.6))})),
            ]
        keys += [
            (58, k(add={'hips': (6, 0, 4), 'spine': (6, 0, 2), 'chest': (6, 0, 2), 'head': (2, 0, -2)},
                   loc=(0, -.08, -.10), feet={'L': sf('L', dfwd=.06, up=.03)})),
            (LENGTHS['Ultimate'], st),
        ]
        lags = {'upper_arm.' + W: 0, 'forearm.' + W: 0, 'hand.' + W: 0}
        if style == 'archer':
            lags.update({'upper_arm.L': 0, 'forearm.L': .3, 'hand.L': .5, 'upper_arm.R': 0, 'forearm.R': 0, 'hand.R': 0})
        self.bake('Ultimate', self.keyed(keys, lags), dict(keys=[f for f, _ in keys],
                                                           resume_normalized=ULT_RESUME / LENGTHS['Ultimate']))

    # ---- Hit: sharp recoil (head snaps back, arms fly), quick recovery with a small forward overshoot
    def hit(self, st):
        k = self.k
        flail = {'shoulder.L': (0, -7, 0), 'shoulder.R': (0, 7, 0),
                 'upper_arm.L': (14, -16, 0), 'upper_arm.R': (14, 16, 0),
                 'forearm.L': (-14, 0, 0), 'forearm.R': (-14, 0, 0), 'hand.L': (-10, 0, 0), 'hand.R': (-10, 0, 0)}
        keys = [
            (0, st),
            (2, k(add=dict(flail, hips=(-6, 0, 4), spine=(-8, 0, 3), chest=(-14, 4, 6), neck=(-6, 0, 0),
                           head=(-16, 0, 10)), loc=(0, .07, -.07))),
            (4, k(add=dict(flail, hips=(-7, 0, 5), spine=(-9, 0, 4), chest=(-16, 4, 8), neck=(-7, 0, 0),
                           head=(-20, 0, 12)), loc=(0, .08, -.08))),
            (7, k(add={'spine': (3, 0, 0), 'chest': (4, 0, -2), 'neck': (2, 0, 0), 'head': (6, 0, -3),
                       'upper_arm.L': (4, -4, 0), 'upper_arm.R': (4, 4, 0)}, loc=(0, .015, -.065))),
            (LENGTHS['Hit'], st),
        ]
        self.bake('Hit', self.keyed(keys, {'head': 2.0, 'neck': 1.2}), dict(keys=[f for f, _ in keys]))

    # ---- Die: recoil, stagger, knees buckle, fall forward, lie still (held)
    COLLAPSE = {'root': (90, 0, -7), 'chest': (6, 0, 0), 'head': (-8, 0, 0),
                'upper_arm.L': (16, -22, 0), 'upper_arm.R': (12, 24, 0),
                'forearm.L': (-18, 0, 0), 'forearm.R': (-22, 0, 0), 'shin.L': (17, 0, 0),
                'hand.L': (60, 0, 0), 'hand.R': (60, 0, 0)}

    def die(self, st):
        k = self.k
        rst = self.resolved(st)
        collapse = self.key(rot=self.COLLAPSE, loc=(0, 0, 0), g=1, ikw=0)
        for n in self.bones:
            if n not in self.COLLAPSE:
                collapse[n] = Quaternion()
        kneel = self.key(base=collapse, rot={
            'root': (0, 0, 0), 'hips': (24, 0, 6), 'spine': (14, 0, 0), 'chest': (10, 0, 4), 'neck': (8, 0, 0),
            'head': (22, 0, 8), 'thigh.L': (-24, 0, -4), 'thigh.R': (-12, 0, 6), 'shin.L': (98, 0, 0),
            'shin.R': (104, 0, 0), 'foot.L': (-6, 0, 0), 'foot.R': (-2, 0, 0),
            'upper_arm.L': (10, -8, 0), 'upper_arm.R': (6, 8, 0), 'forearm.L': (-14, 0, 0),
            'forearm.R': (-16, 0, 0), 'hand.L': (20, 0, 0), 'hand.R': (20, 0, 0)}, loc=(0, -.04, 0), g=1, ikw=0)
        tip = self.key(base=kneel, rot={
            'root': (52, 0, -5), 'hips': (10, 0, 4), 'spine': (8, 0, 0), 'chest': (4, 0, 2), 'head': (-14, 0, 0),
            'thigh.L': (-10, 0, -3), 'thigh.R': (-6, 0, 4), 'shin.L': (64, 0, 0), 'shin.R': (70, 0, 0),
            'upper_arm.L': (-50, -20, 0), 'upper_arm.R': (-46, 22, 0), 'forearm.L': (-24, 0, 0),
            'forearm.R': (-26, 0, 0), 'hand.L': (40, 0, 0), 'hand.R': (40, 0, 0)}, loc=(0, -.06, 0), g=1, ikw=0)
        impact = self.key(base=collapse, add={'chest': (6, 0, 0), 'head': (-6, 0, 0), 'shin.L': (10, 0, 0),
                                              'shin.R': (8, 0, 0)}, g=1, ikw=0)
        keys = [
            (0, rst),
            (3, k(add={'hips': (-8, 0, 6), 'spine': (-10, 0, 3), 'chest': (-18, 4, 8), 'neck': (-8, 0, 0),
                       'head': (-22, 0, 14), 'upper_arm.L': (16, -18, 0), 'upper_arm.R': (16, 18, 0),
                       'forearm.L': (-16, 0, 0), 'forearm.R': (-16, 0, 0)}, loc=(0, .09, -.08), g=1)),
            (8, k(add={'hips': (12, 0, 10), 'spine': (14, 0, 4), 'chest': (12, 0, 6), 'neck': (8, 0, 0),
                       'head': (14, 0, 6), 'upper_arm.L': (10, 4, 0), 'upper_arm.R': (10, -4, 0),
                       'forearm.L': (24, 0, 0), 'forearm.R': (24, 0, 0)}, loc=(0, .05, -.16), g=1)),
            (14, kneel), (20, tip), (24, impact), (27, collapse), (LENGTHS['Die'], collapse),
        ]
        # Rest of the hold: no lag at the end (window), so frame 30 is exactly the collapse pose.
        self.bake('Die', self.keyed(keys, {'head': 2.0}), dict(keys=[f for f, _ in keys]))
        return collapse

    # ---- Guard: brace behind the weapon (frames 12-24 hold, impact shudder at 15), back to the stance
    def guard(self, st):
        k, W, F = self.k, self.W, self.F
        if self.style == 'warrior':
            arms = {'R': dict(hand=(-.04, .42, -.10), aim=(-.95, .05, .30), elbow=(.6, -.2, -.6)),
                    'L': dict(along=('R', .32), elbow=(.6, -.2, -.6))}
        elif self.style == 'archer':
            arms = {'L': dict(hand=(-.08, .30, -.06), aim=(-.25, .05, 1), elbow=(.6, -.2, -.6)),
                    'R': dict(hand=(-.10, .26, .10), elbow=(.7, -.1, -.6))}
        else:
            arms = {'R': dict(hand=(0, .40, -.12), aim=(-.95, .05, .30), elbow=(.6, -.2, -.6)),
                    'L': dict(along=('R', .32), elbow=(.6, -.2, -.6))}
        brace_add = {'hips': (6, 0, 10), 'spine': (8, 0, 2), 'chest': (10, 0, 2), 'neck': (4, 0, 0),
                     'head': (6, 0, -2), 'shoulder.L': (0, -4, -6), 'shoulder.R': (0, 4, 6)}
        brace = k(add=brace_add, loc=(0, .02, -.11), arms=arms)
        deep = k(add=dict(brace_add, chest=(13, 0, 2), head=(8, 0, -2)), loc=(0, .025, -.13), arms=arms)
        shove = k(add=dict(brace_add, spine=(4, 0, 2), chest=(5, 0, 3), head=(2, 0, -1)), loc=(0, .05, -.12),
                  arms=arms)
        keys = [(0, st), (5, deep), (9, brace), (12, brace), (15, shove), (18, brace), (24, brace),
                (LENGTHS['Guard'], st)]
        self.bake('Guard', self.keyed(keys), dict(keys=[f for f, _ in keys], hold_normalized=[1 / 3, 2 / 3],
                                                  recovery_normalized=2 / 3))

    # ---- Revive: prone -> planted forearms -> knees -> push -> crouch -> standing stance (Idle:0)
    def revive(self, st, collapse):
        rst = self.resolved(st)
        plant = self.key(base=collapse, rot={'head': (-19, 0, 0), 'upper_arm.L': (-31, -12, 0),
                                             'upper_arm.R': (-35, 14, 0), 'forearm.L': (-56, 0, 0),
                                             'forearm.R': (-53, 0, 0), 'hand.L': (30, 0, 0), 'hand.R': (30, 0, 0)})
        knees = self.key(base=plant, rot={'root': (68, 0, -4), 'chest': (-12, 0, 0), 'head': (-27, 0, 0),
                                          'thigh.L': (-86, 0, 0), 'thigh.R': (-81, 0, 0), 'shin.L': (99, 0, 0),
                                          'shin.R': (94, 0, 0), 'foot.L': (-13, 0, 0), 'foot.R': (-13, 0, 0)})
        push = self.key(base=knees, rot={'root': (40, 0, -2), 'chest': (-10, 0, 0), 'head': (-20, 0, 0),
                                         'thigh.L': (-83, 0, 0), 'thigh.R': (-76, 0, 0), 'shin.L': (99, 0, 0),
                                         'shin.R': (91, 0, 0), 'foot.L': (-56, 0, 0), 'foot.R': (-55, 0, 0),
                                         'upper_arm.L': (-22, -14, 0), 'upper_arm.R': (-26, 15, 0),
                                         'forearm.L': (-28, 0, 0), 'forearm.R': (-32, 0, 0),
                                         'hand.L': (0, 0, 0), 'hand.R': (0, 0, 0)})
        crouch = self.key(base=rst, rot={'root': (9, 0, 0), 'hips': (0, 0, 0), 'spine': (0, 0, 0),
                                         'chest': (-3, 0, 0), 'head': (-6, 0, 0),
                                         'thigh.L': (-52, 0, 0), 'thigh.R': (-48, 0, 0), 'shin.L': (87, 0, 0),
                                         'shin.R': (79, 0, 0), 'foot.L': (-44, 0, 0), 'foot.R': (-40, 0, 0)},
                          g=1, ikw=0)
        rise = self.key(base=rst, add={'chest': (3, 0, 0), 'head': (-3, 0, 0)},
                        rot={'thigh.L': (-15, 0, 0), 'thigh.R': (-15, 0, 0), 'shin.L': (30, 0, 0),
                             'shin.R': (30, 0, 0), 'foot.L': (-15, 0, 0), 'foot.R': (-15, 0, 0)}, g=1, ikw=0)
        # Mesh grounding hands over to the stance's sole height only once the feet are planted (55 -> 60).
        stand = self.key(base=st, g=1)
        keys = [(0, collapse), (4, collapse), (10, plant), (19, knees), (29, push), (39, crouch), (49, rise),
                (55, stand), (LENGTHS['Revive'], st)]
        self.bake('Revive', self.keyed(keys), dict(keys=[f for f, _ in keys], start_pose='Die:30',
                                                   end_pose='Idle:0', recovery_normalized=55 / 60))

    # ---- Victory: crouch, jump with a full spin and the weapon thrust up, land, strike the hero's pose
    POSES = dict(
        warrior=dict(add={'hips': (0, 0, -16), 'chest': (-6, 0, 4), 'head': (-8, 0, 8)},
                     arms={'R': dict(hand=(0, .20, .38), aim=(-.1, .45, .89), elbow=(.8, -.1, -.2)),
                           'L': dict(hand=(.02, -.02, -.42), elbow=(1, .3, 0))}),
        archer=dict(add={'hips': (0, 0, -12), 'chest': (-5, 0, 4), 'head': (-6, -6, 6)},
                    arms={'L': dict(hand=(.10, .06, .40), aim=(.4, .1, .9), elbow=(.9, -.1, -.2)),
                          'R': dict(hand=(.02, -.02, -.42), elbow=(1, .3, 0))}),
        mage=dict(add={'hips': (0, 0, -10), 'chest': (-4, 0, 3), 'head': (-4, -10, 4)},
                  arms={'R': dict(hand=(.16, .16, -.06), aim=(.18, .1, 1), elbow=(.6, -.2, -.6)),
                        'L': dict(hand=(.24, .12, .02), elbow=(1, -.2, -.4))}),
        cleric=dict(add={'hips': (0, 0, -10), 'chest': (-5, 0, 3), 'head': (-6, 8, 4)},
                    arms={'R': dict(hand=(.02, .14, .36), aim=(-.1, .3, .95), elbow=(.8, -.1, -.2)),
                          'L': dict(hand=(-.13, .20, -.10), elbow=(.8, -.2, -.4))}),
    )

    def victory(self, st):
        k, sf, W, F = self.k, self.stance_feet, self.W, self.F
        pose = self.POSES[self.style]
        toes = lambda p: {S: sf(S, pitch=p) for S in 'LR'}  # noqa: E731
        up_aim = (.1, .3, 1) if self.style == 'archer' else (0, .1, 1)
        keys = [
            (0, st),
            (6, k(add={'hips': (8, 0, 8), 'spine': (10, 0, 0), 'chest': (12, 0, -2), 'head': (12, 0, -4)},
                  loc=(0, .01, -.14),
                  arms={W: dict(hand=(.06, .04, -.40), aim=(0, .5, -.8) if self.style != 'archer' else
                                (.2, -.1, 1), elbow=(.4, -.6, -.4)),
                        F: dict(hand=(.10, -.08, -.38), elbow=(.4, -.6, -.4))})),
            (10, k(add={'hips': (-2, 0, 4), 'spine': (-4, 0, 0), 'chest': (-6, 0, 0), 'head': (-8, 0, 0)},
                   loc=(0, 0, .02), feet=toes(24),
                   arms={W: dict(hand=(.02, .10, .30), aim=up_aim, elbow=(.8, -.1, -.2)),
                         F: dict(hand=(.04, .12, .28), elbow=(.8, -.1, -.2))})),
            (15, k(add={'hips': (-2, 0, 0), 'spine': (-4, 0, 0), 'chest': (-8, 0, 0), 'head': (-10, 0, 0)},
                   loc=(0, 0, 0), air=.26, yaw=180,
                   feet={'L': sf('L', dfwd=.03, up=.10, pitch=10), 'R': sf('R', dfwd=.04, up=.14, pitch=20)},
                   arms={W: dict(hand=(.04, .04, .44), aim=up_aim, elbow=(.8, -.1, -.2)),
                         F: dict(hand=(.20, .04, .20), elbow=(.8, -.1, -.2))})),
            (20, k(add={'hips': (0, 0, 0), 'spine': (-2, 0, 0), 'chest': (-5, 0, 0), 'head': (-8, 0, 0)},
                   loc=(0, 0, 0), air=.12, yaw=320,
                   feet={'L': sf('L', up=.04, pitch=12), 'R': sf('R', up=.06, pitch=14)},
                   arms={W: dict(hand=(.06, .08, .42), aim=up_aim, elbow=(.8, -.1, -.2)),
                         F: dict(hand=(.20, .06, .16), elbow=(.8, -.1, -.2))})),
            (23, k(add={'hips': (6, 0, 0), 'spine': (8, 0, 0), 'chest': (8, 0, 0), 'head': (4, 0, 0)},
                   loc=(0, 0, -.12), yaw=360,
                   arms={W: dict(hand=(.06, .12, .34), aim=up_aim, elbow=(.8, -.1, -.2)),
                         F: dict(hand=(.16, .06, -.04), elbow=(.8, -.1, -.2))})),
            (27, k(add={'hips': (4, 0, -4), 'spine': (5, 0, 0), 'chest': (4, 0, 2), 'head': (0, 0, 4)},
                   loc=(0, 0, -.10), yaw=360,
                   arms={W: dict(hand=(.04, .16, .34), aim=up_aim, elbow=(.8, -.1, -.2)),
                         F: dict(hand=(.10, .02, -.20), elbow=(.9, .1, -.2))})),
            (34, k(add=pose['add'], loc=(0, 0, -.025), yaw=360, arms=pose['arms'])),
            (39, k(add={n: tuple(v * 1.12 for v in e) for n, e in pose['add'].items()}, loc=(0, 0, -.035), yaw=360,
                   arms=pose['arms'])),
            (LENGTHS['Victory'], k(add=pose['add'], loc=(0, 0, -.03), yaw=360, arms=pose['arms'])),
        ]
        self.bake('Victory', self.keyed(keys), dict(keys=[f for f, _ in keys]))


# ---------------------------------------------------------------- NPC clips (original contract, unchanged)

def _legacy_actions(H, npc=False):
    rig = H.rig
    rig.animation_data_create()
    basis = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
    actions = {}

    def action(name, frames, grounded=False):
        length = LEGACY_LENGTHS[name]
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        act.use_frame_range = True
        act.frame_range = (0, length)
        rig.animation_data.action = act
        # Hero contact motions are baked at every frame: quaternion interpolation
        # and evaluated skinned geometry determine the floor clearance, not a
        # guessed character height. NPC motion stays on its original contract.
        if grounded:
            samples = []
            for frame in range(length + 1):
                left, right = next((a, z) for a, z in zip(frames, frames[1:])
                                   if a[0] <= frame <= z[0])
                t = (frame - left[0]) / (right[0] - left[0])
                if t == 0 or t == 1:
                    pose = dict(left[1] if t == 0 else right[1])
                    samples.append((frame, pose, left[2] if t == 0 else right[2]))
                    continue
                pose = {}
                for bn in rig.pose.bones.keys():
                    qa = Euler(tuple(math.radians(x) for x in left[1].get(bn, (0, 0, 0))), 'XYZ').to_quaternion()
                    qb = Euler(tuple(math.radians(x) for x in right[1].get(bn, (0, 0, 0))), 'XYZ').to_quaternion()
                    pose[bn] = tuple(math.degrees(x) for x in qa.slerp(qb, t).to_euler('XYZ'))
                samples.append((frame, pose, left[2] * (1 - t) + right[2] * t))
            frames = samples
        root_keys = []
        for f, pose, root_z in frames:
            for pb in rig.pose.bones:
                deg = pose.get(pb.name, (0, 0, 0))
                q = Euler(tuple(math.radians(x) for x in deg), 'XYZ').to_quaternion()
                b = basis[pb.name]
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = b.inverted() @ q @ b
                pb.location = b.inverted() @ Vector((0, 0, root_z)) if pb.name == 'root' else (0, 0, 0)
                pb.scale = (1, 1, 1)
            if grounded:
                bpy.context.view_layer.update()
                evaluated = H.body.evaluated_get(bpy.context.evaluated_depsgraph_get())
                mesh = evaluated.to_mesh()
                floor = min((evaluated.matrix_world @ v.co).z for v in mesh.vertices)
                evaluated.to_mesh_clear()
                # Exact Idle endpoints retain their original transform. Other
                # keys touch the floor without penetrating it or floating.
                root_z -= floor if abs(floor) > 1e-6 else 0
                rig.pose.bones['root'].location = basis['root'].inverted() @ Vector((0, 0, root_z))
            root_keys.append((f, root_z))
            for pb in rig.pose.bones:
                pb.keyframe_insert('rotation_quaternion', frame=f, group=pb.name)
                pb.keyframe_insert('location', frame=f, group=pb.name)
                pb.keyframe_insert('scale', frame=f, group=pb.name)
        if grounded:
            for curve in act.layers[0].strips[0].channelbag(rig.animation_data.action_slot).fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = 'LINEAR'
            act['root_height_keys'] = [value for _, value in root_keys]
        act['contact_normalized'] = .4 if name == 'Attack' else .6 if name == 'Cast' else -1.0
        act['loop'] = name in ('Idle', 'Walk', 'Run', 'Talk')
        act['authored_keyframes'] = [f for f, _, _ in frames]
        actions[name] = act

    def cloth(pose, phase, amount=1):
        for i, bn in enumerate(H.secondary):
            pose[bn] = (math.sin(phase + i * .8) * 5 * amount, math.sin(phase + i) * 3 * amount, 0)
        return pose

    frames = []
    for f in (0, 12, 24, 36, 48):
        p = f / 48 * math.tau
        pose = {'spine': (1.5 * math.sin(p), 0, 0), 'chest': (-1.1 * math.sin(p), 0, 0),
                'head': (.8 * math.sin(p), 1.7 * math.sin(p), 0),
                'upper_arm.L': (0, -3 - math.sin(p), 0), 'upper_arm.R': (0, 3 + math.sin(p), 0)}
        frames.append((f, cloth(pose, p, .4), .002 * (1 - math.cos(p))))
    idle_pose = dict(frames[0][1])
    action('Idle', frames)

    for name, length, stride, arm, bounce in (('Walk', 32, 22, 18, .011), ('Run', 20, 39, 37, .022)):
        frames = []
        for i in range(9):
            f = length * i / 8
            phase = i * math.tau / 8
            sn = math.sin(phase)
            pose = {'thigh.L': (-stride * sn, 0, 0), 'thigh.R': (stride * sn, 0, 0),
                    'shin.L': (max(0, sn) * stride * .65, 0, 0), 'shin.R': (max(0, -sn) * stride * .65, 0, 0),
                    'foot.L': (-max(0, sn) * stride * .15, 0, 0), 'foot.R': (-max(0, -sn) * stride * .15, 0, 0),
                    'upper_arm.L': (arm * sn, -4, 0), 'upper_arm.R': (-arm * sn, 4, 0),
                    'forearm.L': (-12 if name == 'Walk' else -33, 0, 0),
                    'forearm.R': (-12 if name == 'Walk' else -33, 0, 0),
                    'chest': (-5 if name == 'Run' else -1, 0, -3 * sn), 'head': (3 if name == 'Run' else 0, 0, sn)}
            frames.append((f, cloth(pose, phase + 1, 1.1), bounce * (1 - math.cos(phase * 2))))
        action(name, frames)

    # Deliberate anticipation, acceleration into exact 40%-contact, recoil, recovery.
    if H.name == 'archer':
        wind = {'chest': (0, 0, -10), 'upper_arm.L': (-81, -12, -8), 'forearm.L': (-12, 0, 0),
                'upper_arm.R': (-62, 28, 8), 'forearm.R': (-70, 0, -23), 'head': (0, 0, 8)}
        hit = dict(wind, **{'forearm.R': (-100, 0, -40), 'hand.R': (0, 0, 16), 'chest': (0, 0, -5)})
        follow = dict(wind, **{'upper_arm.R': (-45, 42, 12), 'forearm.R': (-63, 0, -30)})
    elif H.name == 'warrior':
        wind = {'upper_arm.R': (-134, 5, -18), 'forearm.R': (-29, 0, 5), 'upper_arm.L': (-47, -7, 0),
                'chest': (7, 0, -17), 'hips': (0, 0, -8), 'head': (-4, 0, 10)}
        hit = {'upper_arm.R': (-56, -18, 22), 'forearm.R': (-14, 0, 0), 'upper_arm.L': (-53, -10, 0),
               'chest': (-13, 0, 15), 'hips': (-7, 0, 9), 'head': (5, 0, -5), 'thigh.R': (-16, 0, 0)}
        follow = dict(hit, **{'upper_arm.R': (-24, -28, 25), 'chest': (-8, 0, 20)})
    else:
        wind = {'upper_arm.R': (-112, 16, 0), 'forearm.R': (-24, 0, 0), 'upper_arm.L': (-42, -20, 0),
                'chest': (4, 0, -12), 'head': (-5, 0, 5)}
        hit = {'upper_arm.R': (-61, -9, 0), 'forearm.R': (-18, 0, 0), 'upper_arm.L': (-65, -17, 0),
               'chest': (-8, 0, 9), 'head': (2, 0, -4)}
        follow = dict(hit, **{'upper_arm.R': (-38, -17, 0), 'chest': (-4, 0, 12)})
    action('Attack', [(0, {}, 0), (5, cloth(wind, 1, .7), .004), (10, cloth(hit, 2, 1.8), .008),
                      (14, cloth(follow, 3, 1.4), .007), (20, {'chest': (0, 0, 3)}, 0), (25, {}, 0)])

    gather = {'upper_arm.R': (-58, 15, 0), 'forearm.R': (-53, 0, 0), 'upper_arm.L': (-46, -23, 0),
              'forearm.L': (-31, 0, 0), 'head': (9, 0, 0), 'chest': (5, 0, 0)}
    release = {'upper_arm.R': (-143, 11, 0), 'forearm.R': (-12, 0, 0), 'upper_arm.L': (-93, -37, 0),
               'forearm.L': (-16, 0, 0), 'hand.L': (0, -13, 0), 'chest': (-7, 0, 0), 'head': (-12, 0, 0)}
    action('Cast', [(0, {}, 0), (8, cloth(gather, .4, .5), 0), (16, cloth(gather, 1, .7), .005),
                    (21, cloth(release, 2, 1.6), .012), (26, cloth(release, 3, 1.2), .006), (35, {}, 0)])
    action('Hit', [(0, {}, 0), (3, {'chest': (20, 0, -8), 'head': (13, 0, 7), 'upper_arm.L': (-21, -10, 0),
                                 'upper_arm.R': (-17, 13, 0), 'hips': (9, 0, 0)}, 0),
                   (7, {'chest': (-6, 0, 4), 'head': (-6, 0, 0)}, .003), (12, {}, 0)])
    collapse = {'root': (90, 0, -7), 'chest': (6, 0, 0), 'head': (-8, 0, 0),
                'upper_arm.L': (16, -22, 0), 'upper_arm.R': (12, 24, 0),
                'forearm.L': (-18, 0, 0), 'forearm.R': (-22, 0, 0), 'shin.L': (17, 0, 0)}
    death_frames = [(0, {}, 0), (7, {'hips': (-14, 0, 4), 'chest': (-21, 0, 0), 'head': (14, 0, 0),
                                    'shin.L': (32, 0, 0), 'shin.R': (24, 0, 0)}, 0),
                    (17, dict(collapse, root=(64, 0, -7)), .10), (24, collapse, .15), (30, collapse, .15)]
    action('Die', death_frames, grounded=not npc)
    if not npc:
        # Arms protect the torso, rather than using the spell release as guard.
        # Socket bones remain at identity relative to each existing hand.
        guard_arms = {
            'warrior': {'upper_arm.L': (-72, -17, -8), 'forearm.L': (57, 0, 5),
                        'upper_arm.R': (-29, 11, 8), 'forearm.R': (-41, 0, 0)},
            'mage': {'upper_arm.L': (-22, -16, -8), 'forearm.L': (-102, 0, 8),
                     'upper_arm.R': (-22, 9, 5), 'forearm.R': (-73, 0, 0)},
            'archer': {'upper_arm.L': (-41, -15, -9), 'forearm.L': (-40, 0, 4),
                       'upper_arm.R': (-18, 18, 8), 'forearm.R': (-105, 0, -5)},
            'cleric': {'upper_arm.L': (-24, -18, -7), 'forearm.L': (-94, 0, 8),
                       'upper_arm.R': (-26, 8, 5), 'forearm.R': (-68, 0, 0)},
        }[H.name]
        brace = dict(guard_arms, chest=(7, 0, -4), head=(-6, 0, 4),
                     **{'thigh.L': (-16, 0, 0), 'thigh.R': (-16, 0, 0),
                        'shin.L': (32, 0, 0), 'shin.R': (32, 0, 0),
                        'foot.L': (-16, 0, 0), 'foot.R': (-16, 0, 0)})
        guard_frames = []
        for f, weight, recoil in ((0, 0, 0), (3, .16, 0), (6, .5, 0), (9, .86, 0),
                                  (12, 1, 0), (15, 1, 2), (18, 1, 1), (21, 1, 0),
                                  (24, 1, 0), (27, .85, 0), (30, .5, 0),
                                  (33, .16, 0), (36, 0, 0)):
            pose = {bn: tuple(idle_pose.get(bn, (0, 0, 0))[i] * (1 - weight)
                              + brace.get(bn, (0, 0, 0))[i] * weight for i in range(3))
                    for bn in set(idle_pose) | set(brace)}
            pose['chest'] = (pose.get('chest', (0, 0, 0))[0] + recoil, 0, -4 * weight)
            guard_frames.append((f, pose, 0))
        action('Guard', guard_frames, grounded=True)
        actions['Guard']['hold_normalized'] = [1 / 3, 2 / 3]
        actions['Guard']['recovery_normalized'] = 2 / 3
        # Prone -> planted forearms -> knees under hips -> crouch -> standing.
        # No bind/rest reset is inserted between Die and Revive.
        plant = dict(collapse, head=(-19, 0, 0),
                     **{'upper_arm.L': (-31, -12, 0), 'upper_arm.R': (-35, 14, 0),
                        'forearm.L': (-56, 0, 0), 'forearm.R': (-53, 0, 0)})
        knees = dict(plant, root=(68, 0, -4), chest=(-12, 0, 0), head=(-27, 0, 0),
                     **{'thigh.L': (-86, 0, 0), 'thigh.R': (-81, 0, 0),
                        'shin.L': (99, 0, 0), 'shin.R': (94, 0, 0),
                        'foot.L': (-13, 0, 0), 'foot.R': (-13, 0, 0)})
        push = dict(knees, root=(40, 0, -2), chest=(-10, 0, 0), head=(-20, 0, 0),
                    **{'thigh.L': (-83, 0, 0), 'thigh.R': (-76, 0, 0),
                       'shin.L': (99, 0, 0), 'shin.R': (91, 0, 0),
                       'foot.L': (-56, 0, 0), 'foot.R': (-55, 0, 0),
                       'upper_arm.L': (-22, -14, 0), 'upper_arm.R': (-26, 15, 0),
                       'forearm.L': (-28, 0, 0), 'forearm.R': (-32, 0, 0)})
        crouch = dict(idle_pose, root=(9, 0, 0), chest=(-3, 0, 0), head=(-6, 0, 0),
                      **{'thigh.L': (-52, 0, 0), 'thigh.R': (-48, 0, 0),
                         'shin.L': (87, 0, 0), 'shin.R': (79, 0, 0),
                         'foot.L': (-44, 0, 0), 'foot.R': (-40, 0, 0),
                         'upper_arm.L': (-16, -9, 0), 'upper_arm.R': (-18, 10, 0)})
        rise = dict(idle_pose, chest=(3, 0, 0), head=(-3, 0, 0),
                    **{'thigh.L': (-15, 0, 0), 'thigh.R': (-15, 0, 0),
                       'shin.L': (30, 0, 0), 'shin.R': (30, 0, 0),
                       'foot.L': (-15, 0, 0), 'foot.R': (-15, 0, 0)})
        action('Revive', [(0, collapse, .15), (4, collapse, .15), (10, plant, .15),
                          (19, knees, 0), (29, push, 0), (39, crouch, 0),
                          (49, rise, 0), (55, idle_pose, 0), (60, idle_pose, 0)], grounded=True)
        actions['Revive']['start_pose'] = 'Die:30'
        actions['Revive']['end_pose'] = 'Idle:0'
        actions['Revive']['recovery_normalized'] = 55 / 60
    salute = {'upper_arm.R': (-154, 0, -6), 'forearm.R': (-15, 0, 0), 'upper_arm.L': (-66, -18, 0),
              'forearm.L': (-38, 0, 0), 'head': (-7, 0, 0), 'chest': (-5, 0, 0)}
    action('Victory', [(0, {}, 0), (7, {'thigh.L': (-9, 0, 0), 'thigh.R': (-9, 0, 0), 'shin.L': (18, 0, 0),
                                     'shin.R': (18, 0, 0), 'chest': (12, 0, 0)}, 0),
                       (13, cloth(salute, 1, 1.7), .045), (21, cloth(salute, 2, 1), .01),
                       (29, dict(salute, head=(-7, 0, -7)), .004),
                       (36, {'upper_arm.R': (-65, 0, 0), 'head': (0, 0, 3)}, 0), (42, {}, 0)])
    if npc:
        frames = []
        for f in (0, 12, 24, 36, 48):
            t = f / 48 * math.tau
            pose = {'head': (3 * math.sin(t), 0, 3 * math.sin(t)), 'chest': (math.sin(t), 0, 0),
                    'upper_arm.L': (-35 - 12 * math.sin(t), -13, 0), 'forearm.L': (-32, 0, 0),
                    'upper_arm.R': (-22 + 8 * math.sin(t), 10, 0), 'forearm.R': (-18, 0, 0)}
            frames.append((f, cloth(pose, t, .35), 0))
        action('Talk', frames)
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    return actions
