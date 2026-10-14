"""Key poses of the authored shared hunter takes (see motion_author.py for the frame and the solver).

Character frame: x = the character's right, y = forward, z = up, metres from the floor under the rest hips.
Rest landmarks of the library skeleton (1.09 m tall): hips 0.587; right shoulder (0.071, -0.036, 0.805);
right hand at rest (0.19, 0.006, 0.543); right ankle (0.12, -0.036, 0.09); arm reach about 0.29 m from the shoulder.
Keys: (frame at 24 fps, pose). A key inherits every value of the previous key that it does not set; "ease" shapes the
segment that ends at the key. `weaponR` / `weaponL` point the held weapon's shaft (CharacterModel.TryHumanoidGrip) in the
character frame. Every take starts and ends in STANCE (the battle ready stance) so it blends both ways.

CONTACT: strike / release point as a fraction of the take, (frame - 1) / (last - 1), the same normalisation as Unity's
normalized time. BattleView.DefaultContact mirrors these values.
"""

STANCE = dict(
    hips=(0.0, 0.0, -0.018), hips_rot=(3, 0, 0), spine=(2, 0, 0), chest=(2, 0, 0), chest2=(0, 0, 0), neck=(-3, 0, 0), head=(-2, 0, 0),
    handR=(0.15, 0.10, 0.60), poleR=(0.7, -0.3, -0.5), weaponR=(0.15, 0.75, 0.65), gripR=1.0,
    handL=(-0.155, 0.07, 0.58), poleL=(-0.7, -0.3, -0.5), gripL=0.55,
    footR=(0.115, -0.04, 0.09), footL=(-0.115, 0.05, 0.09), footYawR=-12, footYawL=10,
    kneeR=(0.3, 1, 0), kneeL=(-0.3, 1, 0), shoulderR=(0, 0, 0), shoulderL=(0, 0, 0),
)


def st(**over):
    p = dict(STANCE)
    p.update(over)
    return p


TAKES = {}
CONTACT = {}


def contact(name, frame):
    CONTACT[name] = round((frame - 1) / (TAKES[name][-1][0] - 1), 3)


# Spell (stands in for the shared Tripo "Cast", a martial-arts pointing squat): upright spell release. The weapon hand gathers up and back over the shoulder while the open off hand aims at the
# target, then the weapon drives forward and points at the target (release) and the body follows through.
TAKES["Spell"] = [
    (1, st()),
    (9, dict(hips=(0.0, -0.02, -0.035), hips_rot=(0, 12, 0), chest=(-6, 6, 0), chest2=(-4, 4, 0), head=(-4, -10, 0),
             handR=(0.16, -0.05, 0.87), poleR=(0.9, 0.1, -0.2), weaponR=(0.1, -0.35, 1.0),
             handL=(-0.07, 0.22, 0.72), poleL=(-0.8, 0, -0.4), gripL=0.1)),
    (13, dict(handR=(0.17, -0.07, 0.89), chest=(-8, 8, 0), ease="out")),
    (19, dict(hips=(0.0, 0.035, -0.04), hips_rot=(6, -12, 0), chest=(10, -8, 0), chest2=(4, -6, 0), head=(-6, 12, 0),
              handR=(0.05, 0.28, 0.79), poleR=(0.7, -0.2, -0.6), weaponR=(-0.05, 1.0, 0.3),
              handL=(-0.18, -0.02, 0.62), poleL=(-0.7, -0.4, -0.4), gripL=0.55, ease="in")),
    (24, dict(handR=(0.06, 0.29, 0.77), chest=(11, -9, 0), ease="out")),
    (33, st(ease="inout")),
]
contact("Spell", 19)

# Brace (stands in for the shared Tripo "Guard", fists at the face): the weapon braced across the body (blade toward the off side, off hand on the flat), knees bent, chin tucked;
# the brace holds with a breath and settles back.
_guard = dict(hips=(0.0, -0.02, -0.055), hips_rot=(8, 6, 0), chest=(6, 4, 0), chest2=(2, 0, 0), head=(8, -4, 0),
              handR=(0.12, 0.17, 0.73), poleR=(0.9, -0.2, -0.3), weaponR=(-1.0, 0.15, 0.45),
              handL=(-0.09, 0.19, 0.76), poleL=(-0.9, -0.2, -0.2), gripL=0.25,
              footR=(0.13, -0.08, 0.09), footL=(-0.13, 0.08, 0.09), footYawR=-25, footYawL=15)
TAKES["Brace"] = [
    (1, st()),
    (6, dict(_guard, ease="snap")),
    (20, dict(hips=(0.0, -0.02, -0.062), chest=(7, 4, 0))),
    (32, dict(hips=(0.0, -0.02, -0.055), chest=(6, 4, 0))),
    (40, st(ease="inout")),
]
contact("Brace", 6)

# Flinch (stands in for the shared Tripo "Hit", a boxing crouch): upright flinch. The blow snaps the chest and head back and throws the arms out, the body folds forward to absorb
# it and recovers into the stance (0.6 s).
TAKES["Flinch"] = [
    (1, st()),
    (3, dict(hips=(0.0, -0.06, -0.035), hips_rot=(-9, 8, 0), chest=(-16, 6, 4), chest2=(-8, 0, 0), head=(-20, 12, 5),
             handR=(0.23, 0.0, 0.64), poleR=(0.9, -0.3, -0.2), weaponR=(0.6, 0.3, 0.75),
             handL=(-0.22, -0.02, 0.66), poleL=(-0.9, -0.3, -0.2), ease="snap")),
    (6, dict(chest=(-18, 8, 5), head=(-24, 14, 7), hips=(0.0, -0.08, -0.045), ease="out")),
    (10, dict(hips=(0.0, -0.04, -0.05), hips_rot=(8, 2, 0), chest=(8, 2, 0), head=(10, 3, 0),
              handR=(0.17, 0.06, 0.6), handL=(-0.17, 0.05, 0.6), weaponR=(0.2, 0.7, 0.6))),
    (16, st(ease="inout")),
]
contact("Flinch", 3)

# Slash: horizontal forehand cut. Coil to the right with the blade back, sweep through the front (contact) and follow
# through to the left before recovering.
TAKES["Slash"] = [
    (1, st()),
    (8, dict(hips=(0.0, -0.03, -0.04), hips_rot=(4, -28, 0), chest=(2, -14, 0), chest2=(0, -6, 0), head=(0, 22, 0),
             handR=(0.29, -0.05, 0.73), poleR=(0.6, -0.6, -0.3), weaponR=(0.7, -0.6, 0.35),
             handL=(-0.15, 0.17, 0.68), poleL=(-0.8, 0, -0.5), footR=(0.13, -0.09, 0.09))),
    (12, dict(hips=(0.0, 0.05, -0.05), hips_rot=(8, 6, 0), chest=(8, 8, 0), chest2=(2, 4, 0), head=(0, -6, 0),
              handR=(0.02, 0.28, 0.71), poleR=(0.7, -0.3, -0.5), weaponR=(-0.35, 1.0, 0.05),
              handL=(-0.2, 0.0, 0.64), poleL=(-0.8, -0.3, -0.4), ease="in")),
    (16, dict(hips_rot=(8, 26, 0), chest=(8, 16, 0), chest2=(2, 6, 0), head=(0, -18, 0),
              handR=(-0.16, 0.17, 0.69), poleR=(0.4, -0.2, -0.9), weaponR=(-1.0, -0.25, 0.1), ease="out")),
    (21, dict(handR=(-0.15, 0.15, 0.66), weaponR=(-0.9, -0.4, -0.1))),
    (30, st(ease="inout")),
]
contact("Slash", 12)

# Thrust: lunging stab. Draw the weapon back to the hip, step in with the lead foot and drive the point straight at the
# target, hold the extension and step back.
TAKES["Thrust"] = [
    (1, st()),
    (9, dict(hips=(0.0, -0.04, -0.045), hips_rot=(2, -18, 0), chest=(0, -8, 0), head=(0, 16, 0),
             handR=(0.17, -0.08, 0.66), poleR=(0.7, -0.6, -0.2), weaponR=(-0.05, 1.0, 0.12),
             handL=(-0.1, 0.19, 0.72), poleL=(-0.8, 0, -0.4), gripL=0.15, footR=(0.12, -0.09, 0.09))),
    (14, dict(hips=(0.0, 0.085, -0.075), hips_rot=(12, 10, 0), chest=(10, 4, 0), chest2=(4, 2, 0), head=(-4, -10, 0),
              handR=(0.03, 0.31, 0.74), poleR=(0.8, -0.2, -0.5), weaponR=(-0.05, 1.0, 0.03),
              handL=(-0.21, -0.06, 0.63), poleL=(-0.8, -0.4, -0.3), gripL=0.55,
              footL=(-0.12, 0.17, 0.09), footR=(0.12, -0.08, 0.09), ease="in")),
    (20, dict(handR=(0.03, 0.30, 0.73), hips=(0.0, 0.08, -0.07), ease="out")),
    (30, st(ease="inout")),
]
contact("Thrust", 14)

# Smash: two-handed overhead slam. Both hands lift the weapon behind the head with the back arched, then drive it
# down in front into a deep crouch (BattleView lifts the body into a leap around it), hold the impact and stand.
TAKES["Smash"] = [
    (1, st()),
    (10, dict(hips=(0.0, -0.02, -0.005), hips_rot=(-6, 0, 0), chest=(-12, 0, 0), chest2=(-6, 0, 0), head=(-12, 0, 0),
              handR=(0.04, -0.02, 1.0), poleR=(0.8, 0.3, 0.2), weaponR=(0.0, -0.75, 0.55),
              handL=(-0.03, -0.0, 0.97), poleL=(-0.8, 0.3, 0.2), gripL=1.0, footL=(-0.12, 0.08, 0.09))),
    (16, dict(hips=(0.0, 0.05, -0.13), hips_rot=(24, 0, 0), chest=(16, 0, 0), chest2=(6, 0, 0), head=(4, 0, 0),
              handR=(0.03, 0.31, 0.43), poleR=(0.8, 0.1, -0.5), weaponR=(0.0, 0.65, -0.75),
              handL=(-0.03, 0.29, 0.45), poleL=(-0.8, 0.1, -0.5), kneeR=(0.4, 1, 0), kneeL=(-0.4, 1, 0), ease="in")),
    (22, dict(hips=(0.0, 0.05, -0.12), ease="out")),
    (34, st(ease="inout")),
]
contact("Smash", 16)

# Spin: the extended spinning cut. The weapon arm sweeps out to the side and holds level while BattleView turns the
# whole body through a full circle around the contact, then gathers back.
TAKES["Spin"] = [
    (1, st()),
    (6, dict(hips=(0.0, 0.0, -0.06), hips_rot=(6, -20, 0), chest=(4, -10, 0), head=(0, 18, 0),
             handR=(0.33, 0.06, 0.72), poleR=(0.4, -0.7, -0.4), weaponR=(0.9, 0.35, 0.05),
             handL=(-0.24, 0.05, 0.7), poleL=(-0.5, -0.6, -0.4), gripL=0.7)),
    (11, dict(handR=(0.34, 0.1, 0.74), weaponR=(0.85, 0.5, 0.0), hips_rot=(8, -24, 0), ease="out")),
    (16, dict(handR=(0.32, 0.12, 0.73))),
    (24, st(ease="inout")),
]
contact("Spin", 11)

# Channel: both hands gather at the chest with the head bowed, then rise over the head (release) as the body opens up
# toward the sky; buffs, heals and blessings.
TAKES["Channel"] = [
    (1, st()),
    (10, dict(hips=(0.0, 0.0, -0.04), hips_rot=(4, 0, 0), chest=(8, 0, 0), head=(14, 0, 0),
              handR=(0.06, 0.15, 0.71), poleR=(0.9, -0.4, -0.3), weaponR=(0.0, 0.25, 1.0),
              handL=(-0.06, 0.15, 0.72), poleL=(-0.9, -0.4, -0.3), gripL=0.1)),
    (18, dict(hips=(0.0, 0.0, 0.0), hips_rot=(-3, 0, 0), chest=(-10, 0, 0), chest2=(-4, 0, 0), head=(-20, 0, 0),
              handR=(0.1, 0.06, 1.04), poleR=(0.9, 0.1, -0.2), weaponR=(0.05, 0.12, 1.0),
              handL=(-0.1, 0.06, 1.04), poleL=(-0.9, 0.1, -0.2), gripL=0.0, ease="in")),
    (24, dict(handR=(0.11, 0.05, 1.03), handL=(-0.11, 0.05, 1.03), head=(-22, 0, 0), ease="out")),
    (32, st(ease="inout")),
]
contact("Channel", 18)

# Throw: an underhand toss with the off hand (item use); the weapon hand stays down at the side.
TAKES["Throw"] = [
    (1, st()),
    (8, dict(hips=(0.0, -0.02, -0.045), hips_rot=(6, 14, 0), chest=(6, 6, 0), head=(4, -10, 0),
             handL=(-0.19, -0.15, 0.6), poleL=(-0.6, -0.4, -0.6), gripL=0.8,
             handR=(0.17, 0.06, 0.6), weaponR=(0.3, 0.8, 0.2))),
    (13, dict(hips=(0.0, 0.04, -0.03), hips_rot=(4, -8, 0), chest=(2, -6, 0), head=(-6, 4, 0),
              handL=(-0.06, 0.28, 0.82), poleL=(-0.8, -0.1, -0.6), gripL=0.0, ease="in")),
    (17, dict(handL=(-0.05, 0.27, 0.86), ease="out")),
    (26, st(ease="inout")),
]
contact("Throw", 13)

# Rally: war cry. Crouch and clench, then burst upright with the chest out, arms flung down and out and the head
# thrown back (the shout), hold it and settle.
TAKES["Rally"] = [
    (1, st()),
    (8, dict(hips=(0.0, 0.0, -0.065), hips_rot=(10, 0, 0), chest=(14, 0, 0), head=(10, 0, 0),
             handR=(0.13, 0.11, 0.66), weaponR=(0.1, 0.4, 1.0), handL=(-0.13, 0.11, 0.66), gripL=1.0,
             footR=(0.13, -0.05, 0.09), footL=(-0.13, 0.05, 0.09))),
    (13, dict(hips=(0.0, 0.0, 0.0), hips_rot=(-6, 0, 0), chest=(-14, 0, 0), chest2=(-6, 0, 0), head=(-16, 0, 0),
              handR=(0.3, 0.05, 0.63), poleR=(0.4, -0.6, -0.5), weaponR=(0.9, 0.2, 0.5),
              handL=(-0.3, 0.05, 0.63), poleL=(-0.4, -0.6, -0.5), shoulderR=(0, 0, -6), shoulderL=(0, 0, 6),
              ease="snap")),
    (19, dict(head=(-18, 3, 0), chest=(-15, 2, 0))),
    (24, dict(head=(-16, -3, 0), chest=(-14, -2, 0))),
    (33, st(ease="inout")),
]
contact("Rally", 13)

# Kneel: drop to one knee beside an ally (revive / the biggest heals): the weapon is planted, the open off hand reaches
# down and forward (release) and the hunter stands back up.
TAKES["Kneel"] = [
    (1, st()),
    (11, dict(hips=(0.0, 0.0, -0.24), hips_rot=(10, -6, 0), chest=(12, 0, 0), head=(16, 0, 0),
              footR=(0.12, -0.23, 0.09), footL=(-0.12, 0.15, 0.09), kneeR=(0.15, 0.3, -1), kneeL=(-0.2, 1, 0.2),
              handR=(0.2, 0.12, 0.42), poleR=(0.8, -0.4, -0.2), weaponR=(0.05, 0.2, -1.0),
              handL=(-0.05, 0.3, 0.38), poleL=(-0.8, -0.2, -0.4), gripL=0.0)),
    (16, dict(handL=(-0.04, 0.32, 0.36), head=(18, 0, 0), ease="out")),
    (22, dict(handL=(-0.05, 0.31, 0.37))),
    (34, st(ease="inout")),
]
contact("Kneel", 16)
