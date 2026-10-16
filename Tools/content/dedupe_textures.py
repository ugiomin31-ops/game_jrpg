"""Keep one copy of each byte-identical model texture and repoint the materials that used the others.

VRoid hunters ship the same skin, face and eye PNGs in every <id>_tex folder, and the subway floor/wall b and c variants
repeat the a variant's texture. The kept VRoid copy moves (with its .meta, so its GUID) to Characters/_SharedVRoid/; the
subway copy stays in the a variant's folder. Every .mat that referenced a duplicate GUID is repointed to the kept one, and
the duplicates are removed with git rm (git history keeps them). Each model keeps its own .mat in <id>_mat, which is what
AbyssArtImporter's TexturedMaterials.Existing remaps from, so the FBX bindings do not change.

Run from the repo root: python Tools/content/dedupe_textures.py            (dry run: prints the plan)
                        python Tools/content/dedupe_textures.py --apply    (moves, repoints, deletes)
Then open Unity, let it reimport, and run Abyss > Validate Production Content.
"""
import hashlib, os, re, sys, collections, uuid, subprocess
APPLY = '--apply' in sys.argv
ART = 'Assets/_Game/Resources/Art'
SHARED = ART + '/Characters/_SharedVRoid'
def guid(p): return re.search(r'^guid: ([0-9a-f]{32})', open(p + '.meta', encoding='utf-8').read(), re.M).group(1)
def strip_guid(t): return re.sub(r'^guid: .*$', '', t, flags=re.M)
# a regenerated texture may be untracked or modified in git, so fall back to plain file operations
def move(a, b):
    if subprocess.run(['git', 'mv', a, b], capture_output=True).returncode: os.replace(a, b)
def drop(p):
    subprocess.run(['git', 'rm', '-q', '-f', '--ignore-unmatch', p], check=True)
    if os.path.exists(p): os.remove(p)
groups = collections.defaultdict(list)
for root in (ART + '/Characters', ART + '/Environment/subway'):
    for d, _, fs in os.walk(root):
        d = d.replace('\\', '/')
        for f in fs:
            # include the shared copies, so a rerun after a generator recreates <id>_tex textures folds them back in
            if f.endswith('.png') and (d.endswith('_tex') or d == SHARED):
                p = f'{d}/{f}'; groups[hashlib.sha1(open(p, 'rb').read()).hexdigest()].append(p)
# every text asset that can hold a texture GUID
texts = [os.path.join(d, f) for d, _, fs in os.walk('Assets') for f in fs if f.endswith(('.mat', '.meta', '.prefab', '.asset', '.unity', '.controller'))]
plan, saved, names = [], 0, {}
for h, ps in groups.items():
    if len(ps) < 2: continue
    ps.sort(key=lambda p: (not p.startswith(SHARED + '/'), p))  # an existing shared copy stays the kept one
    metas = {strip_guid(open(p + '.meta', encoding='utf-8').read()) for p in ps}
    if len(metas) != 1: print('import settings differ, skipped:', ps); continue
    keep = ps[0]
    dest = keep if '/Environment/' in keep or keep.startswith(SHARED + '/') else f'{SHARED}/{os.path.basename(keep)}'
    if (dest in names and names[dest] != h) or (dest != keep and os.path.exists(dest)): sys.exit('name clash ' + dest)
    names[dest] = h
    plan.append((keep, dest, ps[1:]))
    saved += os.path.getsize(keep) * (len(ps) - 1)
print(len(plan), 'groups,', sum(len(x[2]) for x in plan), 'duplicates,', round(saved / 1e6, 1), 'MB')
refs = 0
for keep, dest, dups in plan:
    kg = guid(keep); dg = {guid(d): d for d in dups}
    for t in texts:
        if t.endswith('.png.meta'): continue
        s = open(t, encoding='utf-8', errors='surrogateescape').read()
        hit = [g for g in dg if g in s]
        if not hit: continue
        if not t.endswith('.mat'): sys.exit(f'unexpected reference in {t}')
        refs += len(hit)
        if APPLY:
            for g in hit: s = s.replace(g, kg)
            open(t, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(s)
    if APPLY:
        if dest != keep:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            move(keep, dest); move(keep + '.meta', dest + '.meta')
        for d in dups: drop(d); drop(d + '.meta')
    else:
        print(f'  keep {keep} -> {dest}  drop {len(dups)}')
print('material references repointed:', refs)
if APPLY:
    # folder meta for the shared folder
    m = SHARED + '.meta'
    if not os.path.exists(m):
        open(m, 'w', encoding='utf-8', newline='\n').write('fileFormatVersion: 2\nguid: ' + uuid.uuid5(uuid.NAMESPACE_URL, 'abyss:' + SHARED).hex + '\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
    # git rm drops a folder it empties; its folder .meta would be left behind
    for d, _, fs in list(os.walk(ART)):
        for f in fs:
            t = os.path.join(d, f[:-5])
            if f.endswith('_tex.meta') and (not os.path.isdir(t) or not os.listdir(t)):
                if os.path.isdir(t): os.rmdir(t)
                drop(os.path.join(d, f)); print('removed empty', t)
