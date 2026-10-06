"""Packs the MakeHuman assets lib_anime/mh_base.py needs into mh_data.npz (run once, plain Python + numpy).

Sources (all CC0, see README.md):
  base.obj             makehuman/data/3dobjs/base.obj           (github.com/makehumancommunity/makehuman)
  default.mhskel       makehuman/data/rigs/default.mhskel
  default_weights.mhw  makehuman/data/rigs/default_weights.mhw
  targets.npz          makehuman/data/targets.npz in the `makehuman` wheel on PyPI (compiled .target files)

Usage: python extract.py <dir holding the four files>
"""
import json
import os
import re
import sys

import numpy as np

KEEP = re.compile(r"targets/(macrodetails/(height/|proportions/)?(universal-|african-|asian-|caucasian-)?(fe)?male-young"
                  r"|eyes/|nose/|mouth/|chin/|head/|cheek/|eyebrows/|neck/|forehead/|ears/|torso/|hip/|armslegs/|measure/)")


def main(src):
    V, faces, groups = [], [], []
    g = None
    for line in open(os.path.join(src, "base.obj")):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("g "):
            g = line.split()[1]
        elif line.startswith("f "):
            faces.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
            groups.append(g)
    body = np.array([f for f, gg in zip(faces, groups) if gg == "body"], np.int32)
    out = {"base": np.array(V, np.float32), "body_faces": body}
    for key, grp in (("eye_l", "helper-l-eye"), ("eye_r", "helper-r-eye")):
        out[key] = np.unique(np.array([f for f, gg in zip(faces, groups) if gg == grp], np.int32))
    skel = json.load(open(os.path.join(src, "default.mhskel")))
    w = json.load(open(os.path.join(src, "default_weights.mhw")))
    out["joints"] = np.frombuffer(json.dumps(skel["joints"]).encode(), np.uint8)
    out["bones"] = np.frombuffer(json.dumps({k: {"head": b["head"], "tail": b["tail"], "parent": b["parent"]}
                                             for k, b in skel["bones"].items()}).encode(), np.uint8)
    out["weights"] = np.frombuffer(json.dumps(w["weights"]).encode(), np.uint8)
    z = np.load(os.path.join(src, "targets.npz"))
    names = []
    for k in z.files:
        n, ext = k.rsplit(".", 1)
        if KEEP.match(n) and z[n + ".index"].size:
            short = n[len("targets/"):]
            out["t/" + short + "." + ext] = z[k]
            if ext == "index":
                names.append(short)
    out["targets"] = np.array(sorted(names))
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mh_data.npz")
    np.savez_compressed(dst, **out)
    print(dst, os.path.getsize(dst), "bytes,", len(names), "targets")


if __name__ == "__main__":
    main(sys.argv[1])
