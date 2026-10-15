"""Tripo API runner for the asset list in Tools/tripo/assets.json (stdlib only).

Flow per asset:
  candidates  4 text-to-image tasks -> Blender/tripo/source/<id>/candidates/cand_<n>.*
  pick        record the chosen candidate (and why) in state.json
  model       image-to-model from the picked image -> Blender/tripo/source/<id>/model.glb
then convert with Blender (see Tools/tripo/README.md).

Needs TRIPO_API_KEY (tsk_...). API: https://openapi.tripo3d.ai/v3 (override with TRIPO_BASE_URL).

  python Tools/tripo/tripo_run.py balance
  python Tools/tripo/tripo_run.py candidates town_fountain town_forge   # or --all
  python Tools/tripo/tripo_run.py pick town_fountain 3 --why "실루엣이 가장 선명"
  python Tools/tripo/tripo_run.py model town_fountain                    # or --all
  python Tools/tripo/tripo_run.py model town_fountain --image my.png     # own image instead
  python Tools/tripo/tripo_run.py status
  python Tools/tripo/tripo_run.py import D:/tripo_downloads   # GLBs made on the Tripo website, named <id>.glb
"""
import argparse
import glob
import json
import shutil
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
MANIFEST = os.path.join(HERE, "assets.json")
SOURCE = os.path.join(REPO, "Blender", "tripo", "source")
BASE_URL = os.environ.get("TRIPO_BASE_URL", "https://openapi.tripo3d.ai").rstrip("/")
DEFAULT_MODEL = os.environ.get("TRIPO_MODEL_VERSION", "v3.1-20260211")
TERMINAL = {"success", "failed", "cancelled", "banned", "expired"}


# ---------------------------------------------------------------- manifest / state

def load_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def asset_dir(aid):
    return os.path.join(SOURCE, aid)


def load_state(aid):
    p = os.path.join(asset_dir(aid), "state.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"id": aid}


def save_state(aid, st):
    os.makedirs(asset_dir(aid), exist_ok=True)
    with open(os.path.join(asset_dir(aid), "state.json"), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
        f.write("\n")


def select(man, ids, all_):
    by_id = {a["id"]: a for a in man["assets"]}
    if all_:
        return man["assets"]
    unknown = [i for i in ids if i not in by_id]
    if unknown or not ids:
        sys.exit("unknown or missing asset id: %s (ids: %s)" % (unknown, ", ".join(by_id)))
    return [by_id[i] for i in ids]


# ---------------------------------------------------------------- http

def api_key():
    key = os.environ.get("TRIPO_API_KEY", "")
    if not key.startswith("tsk_"):
        sys.exit("TRIPO_API_KEY is not set (expected a key starting with tsk_)")
    return key


def _envelope(raw):
    body = json.loads(raw.decode("utf-8")) if raw else {}
    if isinstance(body, dict) and body.get("code") not in (None, 0):
        raise RuntimeError("Tripo API error %s: %s %s" % (body.get("code"), body.get("message"), body.get("suggestion") or ""))
    return body.get("data", body) if isinstance(body, dict) else body


def call(method, path, payload=None, data=None, content_type=None):
    headers = {"Authorization": "Bearer " + api_key(), "Accept": "application/json",
               "X-Tripo-Trace-ID": str(uuid.uuid4())}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        content_type = "application/json"
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(BASE_URL + path, data=data, method=method, headers=headers)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return _envelope(r.read())
        except urllib.error.HTTPError as e:
            raw = e.read()
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt * 2)
                continue
            try:
                _envelope(raw)
            except RuntimeError as api_err:
                raise RuntimeError("HTTP %s %s: %s" % (e.code, path, api_err)) from None
            raise RuntimeError("HTTP %s %s: %s" % (e.code, path, raw[:300])) from None
        except urllib.error.URLError:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt * 2)


def upload(path):
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        blob = f.read()
    body = (("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
             % (boundary, os.path.basename(path), ctype)).encode("utf-8") + blob +
            ("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    data = call("POST", "/v3/files", data=body, content_type="multipart/form-data; boundary=" + boundary)
    return data["file_token"]


def submit(path, payload):
    data = call("POST", path, payload)
    tid = data.get("task_id") if isinstance(data, dict) else None
    if not tid:
        raise RuntimeError("no task_id from %s: %r" % (path, data))
    return tid


def wait(task_ids, label):
    """Poll until every task is terminal; returns {task_id: task}."""
    done, interval = {}, 3.0
    while len(done) < len(task_ids):
        for tid in task_ids:
            if tid in done:
                continue
            t = call("GET", "/v3/tasks/" + tid)
            if str(t.get("status", "")).lower() in TERMINAL:
                done[tid] = t
        if len(done) < len(task_ids):
            print("  %s: %d/%d done" % (label, len(done), len(task_ids)), flush=True)
            time.sleep(interval)
            interval = min(interval * 1.5, 20.0)
    return done


def first(d, *keys):
    for k in keys:
        if d.get(k):
            return d[k]
    return None


def download(url, dest_noext, default_ext):
    ext = os.path.splitext(url.split("?")[0])[1] or default_ext
    dest = dest_noext + ext
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def rel(p):
    return os.path.relpath(p, REPO).replace(os.sep, "/")


# ---------------------------------------------------------------- commands

def cmd_balance(_args):
    print(json.dumps(call("GET", "/v3/account/balance"), indent=2))


def cmd_candidates(args):
    man = load_manifest()
    for a in select(man, args.ids, args.all):
        st = load_state(a["id"])
        if st.get("candidates") and not args.force:
            print("%s: candidates exist (use --force to regenerate)" % a["id"])
            continue
        suffix = man["groups"][a["group"]]["style_suffix"]
        prompts = [c + ", " + suffix for c in a["candidates"]]
        tids = []
        for p in prompts:
            payload = {"prompt": p, "negative_prompt": man["negative_prompt"]}
            if args.image_model:
                payload["model"] = args.image_model
            tids.append(submit("/v3/generation/text-to-image", payload))
        tasks = wait(tids, a["id"])
        cands = []
        for n, (tid, prompt) in enumerate(zip(tids, prompts), 1):
            t = tasks[tid]
            entry = {"n": n, "task_id": tid, "status": t.get("status"), "prompt": prompt}
            url = first(t.get("output") or {}, "generated_image_url", "generated_image", "image_url", "image")
            if t.get("status") == "success" and url:
                entry["file"] = rel(download(url, os.path.join(asset_dir(a["id"]), "candidates", "cand_%d" % n), ".png"))
            cands.append(entry)
            print("  cand_%d %s %s" % (n, entry["status"], entry.get("file", "")))
        st["candidates"] = cands
        st.pop("pick", None)
        save_state(a["id"], st)


def cmd_pick(args):
    st = load_state(args.id)
    cands = {c["n"]: c for c in st.get("candidates", [])}
    if args.n not in cands or not cands[args.n].get("file"):
        sys.exit("%s has no successful candidate %d" % (args.id, args.n))
    st["pick"] = {"n": args.n, "task_id": cands[args.n]["task_id"], "file": cands[args.n]["file"], "why": args.why}
    save_state(args.id, st)
    print("%s -> cand_%d" % (args.id, args.n))


def cmd_model(args):
    man = load_manifest()
    jobs = []
    for a in select(man, args.ids, args.all):
        st = load_state(a["id"])
        if st.get("model", {}).get("file") and not args.force:
            print("%s: model exists (use --force to regenerate)" % a["id"])
            continue
        if args.image:
            source = upload(args.image)
            st["pick"] = {"n": None, "file": args.image, "why": "user-supplied image"}
        elif st.get("pick"):
            source = st["pick"]["task_id"]
        else:
            print("%s: no pick yet, skipped" % a["id"])
            continue
        payload = {
            "input": source,
            "model": args.model_version,
            "face_limit": int(a["tri_budget"] * args.face_factor),
            "texture": True,
            "pbr": False,
            "texture_alignment": "original_image",
        }
        tid = submit("/v3/generation/image-to-model", payload)
        jobs.append((a, st, tid, payload))
        print("%s: submitted %s" % (a["id"], tid))
    if not jobs:
        return
    tasks = wait([j[2] for j in jobs], "image-to-model")
    for a, st, tid, payload in jobs:
        t = tasks[tid]
        out = t.get("output") or {}
        entry = {"task_id": tid, "status": t.get("status"), "model_version": payload["model"],
                 "face_limit": payload["face_limit"]}
        url = first(out, "model_url", "pbr_model_url", "model", "pbr_model")
        if t.get("status") == "success" and url:
            entry["file"] = rel(download(url, os.path.join(asset_dir(a["id"]), "model"), ".glb"))
            img = first(out, "rendered_image_url", "rendered_image")
            if img:
                entry["rendered"] = rel(download(img, os.path.join(asset_dir(a["id"]), "tripo_render"), ".webp"))
        st["model"] = entry
        save_state(a["id"], st)
        print("%s: %s %s" % (a["id"], entry["status"], entry.get("file", "")))


def cmd_import(args):
    """Take GLBs made on the Tripo website (no API credits needed) named <id>.glb."""
    ids = {a["id"] for a in load_manifest()["assets"]}
    for path in sorted(glob.glob(os.path.join(args.dir, "*.glb"))):
        aid = os.path.splitext(os.path.basename(path))[0]
        if aid not in ids:
            print("skip %s (name is not an asset id)" % os.path.basename(path))
            continue
        os.makedirs(asset_dir(aid), exist_ok=True)
        dest = os.path.join(asset_dir(aid), "model.glb")
        shutil.copyfile(path, dest)
        st = load_state(aid)
        st["model"] = {"status": "success", "source": "tripo-web", "file": rel(dest)}
        save_state(aid, st)
        print("%s <- %s" % (aid, os.path.basename(path)))


def cmd_status(_args):
    for a in load_manifest()["assets"]:
        st = load_state(a["id"])
        cands = sum(1 for c in st.get("candidates", []) if c.get("file"))
        pick = st.get("pick", {}).get("n")
        model = st.get("model", {}).get("status", "-")
        print("%-24s candidates %d/4  pick %-4s model %s" % (a["id"], cands, pick or "-", model))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("balance").set_defaults(fn=cmd_balance)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    c = sub.add_parser("candidates")
    c.add_argument("ids", nargs="*")
    c.add_argument("--all", action="store_true")
    c.add_argument("--force", action="store_true")
    c.add_argument("--image-model", default=None, help="text-to-image model; omitted = server default")
    c.set_defaults(fn=cmd_candidates)
    p = sub.add_parser("pick")
    p.add_argument("id")
    p.add_argument("n", type=int)
    p.add_argument("--why", default="")
    p.set_defaults(fn=cmd_pick)
    m = sub.add_parser("model")
    m.add_argument("ids", nargs="*")
    m.add_argument("--all", action="store_true")
    m.add_argument("--force", action="store_true")
    m.add_argument("--image", default=None, help="model from this local image instead of the picked candidate")
    m.add_argument("--model-version", default=DEFAULT_MODEL)
    m.add_argument("--face-factor", type=float, default=2.0,
                   help="face_limit = tri_budget * factor; convert.py decimates to the budget afterwards")
    m.set_defaults(fn=cmd_model)
    i = sub.add_parser("import")
    i.add_argument("dir")
    i.set_defaults(fn=cmd_import)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
