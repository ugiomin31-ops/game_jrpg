"""Anime face on the MakeHuman head.

Real 3D anime characters (Genshin Impact, Blue Protocol, VRoid models) keep a believable skull, jaw,
cheeks and ears, but flatten the eye sockets and lips and paint the eyes, brows and mouth as flat,
crisp shapes, because toon shading turns small sculpted features into noise. This does the same:
it relaxes the eye, nose and mouth sculpt with a masked Laplacian smooth and then lays decal
eyes (sclera, gradient iris, pupil, two highlights, heavy upper lash line), brows and a small mouth.
"""
import math

import bmesh
import numpy as np
from mathutils import Vector

from humanoid import V, arc_band, bvh_of, decal, ellipse, mix, shade, zgrad

LASH = "#2a1a1e"


def _smooth(co, edges, mask, iterations):
    """Masked Laplacian relaxation; with mask 1 inside a zone it converges to a smooth (harmonic) fill."""
    a, b = edges[:, 0], edges[:, 1]
    deg = np.bincount(a, minlength=len(co)) + np.bincount(b, minlength=len(co))
    deg = np.maximum(deg, 1)[:, None]
    m = mask[:, None]
    for _ in range(iterations):
        acc = np.zeros_like(co)
        np.add.at(acc, a, co[b])
        np.add.at(acc, b, co[a])
        co = co + (acc / deg - co) * m
    return co


def relax_face(H, body, iterations=300):
    """Fills the eye sockets and closes the lips (removing the mouth cavity) so painted features sit on a
    smooth, gently curved face, as on anime models; the nose keeps a soft bridge and tip."""
    eL, _ = H.eyes["L"]
    ez = eL.z
    hc = H.j["head_c"]
    me = body.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    # 1. Mouth cavity: vertices near the lips that sit behind another surface seen from the front.
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromBMesh(bm)
    lips_z = ez - 0.075
    cavity = []
    for v in bm.verts:
        c = v.co
        if abs(c.x) < 0.035 and abs(c.z - lips_z) < 0.03 and c.y > hc.y - 0.12 and c.y < hc.y:
            hit = tree.ray_cast(Vector((c.x, c.y - 0.2, c.z)), Vector((0, 1, 0)), 0.2)
            if hit[0] is not None and hit[0].y < c.y - 0.004:
                cavity.append(v)
    bmesh.ops.delete(bm, geom=cavity, context="VERTS")
    holes = [e for e in bm.edges if e.is_boundary]
    if holes:
        bmesh.ops.holes_fill(bm, edges=holes, sides=0)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    co = np.array([v.co for v in bm.verts])
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    front = np.clip((hc.y - 0.02 - y) / 0.03, 0, 1)
    side = np.clip((0.060 - np.abs(x)) / 0.012, 0, 1)
    face_m = front * side
    mask = np.zeros(len(co))
    for sx in (1, -1):
        d = np.sqrt(((x - sx * abs(eL.x)) / 0.024) ** 2 + ((z - ez) / 0.017) ** 2)
        mask = np.maximum(mask, face_m * np.clip((1.35 - d) / 0.35, 0, 1))
    mouth = np.sqrt((x / 0.030) ** 2 + ((z - lips_z) / 0.015) ** 2)
    mask = np.maximum(mask, face_m * np.clip((1.35 - mouth) / 0.35, 0, 1))
    nose = np.sqrt((x / 0.020) ** 2 + ((z - (ez - 0.045)) / 0.014) ** 2)
    mask = mask * np.clip((nose - 0.9) / 0.4, 0, 1)  # leave the bridge and tip alone
    nostrils = np.sqrt((x / 0.020) ** 2 + ((z - (ez - 0.052)) / 0.010) ** 2)
    mask = np.maximum(mask, face_m * 0.9 * np.clip((1.3 - nostrils) / 0.3, 0, 1))
    edges = np.array([(e.verts[0].index, e.verts[1].index) for e in bm.edges])
    co = _smooth(co, edges, mask * 0.9, iterations)
    for v, c in zip(bm.verts, co):
        v.co = Vector(c)
    bm.to_mesh(me)
    bm.free()
    me.update()
    for p in me.polygons:
        p.use_smooth = True


def face(H, body, eye="#5fa83a", brow="#8a5a20", male=True, mouth="smile", blush=None, eye_scale=1.08):
    """Decal eyes, brows, mouth; registered on the head bone."""
    bvh = bvh_of([body])
    eL, _ = H.eyes["L"]
    ez = eL.z
    ex = abs(eL.x) * 1.06
    fy = eL.y - 0.02  # just in front of the face; decals ray-cast back onto it
    W = 0.030 * eye_scale
    Hh = (0.026 if male else 0.031) * eye_scale
    dark = shade(eye, 0.40)
    made = []
    blush = (not male) if blush is None else blush

    def D(*a, **k):
        o = decal(*a, **k)
        made.append(o)
        return o

    for s in (1, -1):
        n = V((s * 0.30, -1, 0.02)).normalized()
        C = V((s * ex, fy, ez + 0.002))
        tilt = -s * (4 if male else 2)
        D("eye_w", ellipse(W, Hh, 28), bvh, C, n, "#fbf8f6", offset=0.0006, rot=tilt)
        ir = D("eye_i", ellipse(W * 0.56, Hh * 0.98, 24, cy=-Hh * 0.02), bvh, C, n, eye, offset=0.0011, rot=tilt)
        zgrad(ir, ez - Hh * 0.45, mix(eye, "#ffffff", 0.30), ez + Hh * 0.35, dark)
        D("eye_p", ellipse(W * 0.22, Hh * 0.46, 16, cy=-Hh * 0.02), bvh, C, n, shade(eye, 0.22), offset=0.0015,
          rot=tilt)
        D("eye_g", arc_band(W * 0.44, Hh * 0.74, Hh * 0.10, 210, 330, n=12, cy=-Hh * 0.06, taper=0.8), bvh, C, n,
          mix(eye, "#ffffff", 0.5), offset=0.0018, rot=tilt)
        D("eye_h1", ellipse(W * 0.15, Hh * 0.20, 12, cx=-W * 0.08, cy=Hh * 0.17), bvh, C, n, "#ffffff",
          offset=0.0022, mat="M_Emit", rot=tilt)
        D("eye_h2", ellipse(W * 0.07, Hh * 0.08, 8, cx=W * 0.10, cy=-Hh * 0.20), bvh, C, n, "#ffffff",
          offset=0.0022, mat="M_Emit", rot=tilt)
        # Upper lid: a heavy lash line that thickens and flicks outward, the anime eye's main read.
        D("lash_u", arc_band(W * 1.12, Hh * 1.12, 0.0042, 10 if s > 0 else 22, 158 if s > 0 else 170, n=18,
                             cy=Hh * 0.02, taper=0.45), bvh, C, n, LASH, offset=0.0025, rot=tilt)
        fx = s * W * 0.56
        D("lash_f", [(fx, Hh * 0.10), (fx + s * W * 0.16, Hh * 0.20), (fx - s * W * 0.04, Hh * 0.30)], bvh, C, n,
          LASH, offset=0.0025, rings=1, rot=tilt)
        D("lash_l", arc_band(W * 0.94, Hh * 1.0, 0.0012, 235 if s < 0 else 265, 275 if s < 0 else 305, n=6,
                             taper=0.6), bvh, C, n, shade(LASH, 1.7), offset=0.0025, rot=tilt)
        # Brows: thin, slightly arched, set high.
        D("brow", arc_band(W * 1.25, Hh * 0.7, 0.0030 if male else 0.0022, 30, 150, n=12,
                           cx=s * W * 0.05, cy=Hh * 1.05, taper=0.75), bvh, C, V((s * 0.25, -1, 0.25)).normalized(),
          brow, offset=0.0016, rot=-s * (6 if male else 3))
        if blush:
            D("blush", ellipse(W * 0.8, Hh * 0.30, 14, cx=s * W * 0.15, cy=-Hh * 1.05), bvh, C, n,
              mix("#ffe6d6", "#ff8a96", 0.35), offset=0.0005)
    # Small mouth and a soft shadow under the nose tip.
    mzz = ez - 0.075
    n = V((0, -1, -0.10)).normalized()
    C = V((0, fy, mzz))
    if mouth == "smile":
        D("mouth", arc_band(0.020, 0.010, 0.0016, 200, 340, n=12, cy=0.002, taper=0.5), bvh, C, n, "#8a3a40",
          offset=0.0008)
    else:
        D("mouth", arc_band(0.016, 0.004, 0.0013, 190, 350, n=10, taper=0.5), bvh, C, n, "#8a3a40", offset=0.0008)
    D("nose_s", ellipse(0.006, 0.0022, 10), bvh, V((0, fy, ez - 0.043)), V((0, -1, -0.5)).normalized(),
      shade("#ffe6d6", 0.86), offset=0.0006)
    for o in made:
        H.add("head", o)
    return made
