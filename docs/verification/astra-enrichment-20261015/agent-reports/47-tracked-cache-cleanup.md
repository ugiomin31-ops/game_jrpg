# 47 — Tracked cache cleanup audit

- Scope: independent, bounded read-only audit in `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`; only this report written.
- Verified branch: `codex/astra-enrichment-20261015`.
- Verified HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Requested model/effort: `gpt-6-astra` / `high`. Actual serving model and effort were not independently exposed by the audit tools; no model/persona/configuration changes made.
- Requested service tier: Fast/priority. Actual tier was not independently verified; a requested tier is not execution evidence.
- No nested agents, tests, builds, Unity/editor/browser actions, network requests, secret-value reads, or cleanup mutations performed.

## Finding 1 — P3: Ignored Unity logs and personal editor state remain tracked

**Locations:** `.gitignore:14-16`; concrete serialized editor-layout state at `UserSettings/Layouts/default-6000.dwlt:24-25`.

`git ls-files -- Logs UserSettings Temp Build Builds build .cache obj` returns the following ten tracked files, totaling **1,168,554 bytes**. `git check-ignore --no-index -v -- <each exact path>` confirms that all six logs match `.gitignore:14` and all four UserSettings files match `.gitignore:15`. These existing ignore rules do not remove already tracked files from the index.

| Exact tracked path | Bytes |
| --- | ---: |
| `Logs/AssetImportWorker0.log` | 15,368 |
| `Logs/shadercompiler-AssetImportWorker0-0.log` | 364 |
| `Logs/shadercompiler-UnityShaderCompiler.exe-0.log` | 266,274 |
| `Logs/shadercompiler-UnityShaderCompiler.exe-1.log` | 288,126 |
| `Logs/shadercompiler-UnityShaderCompiler.exe-2.log` | 278,596 |
| `Logs/shadercompiler-UnityShaderCompiler.exe-3.log` | 271,435 |
| `UserSettings/EditorUserSettings.asset` | 1,207 |
| `UserSettings/Layouts/default-6000.dwlt` | 46,149 |
| `UserSettings/Search.index` | 299 |
| `UserSettings/Search.settings` | 736 |

**Reachable impact:** A checkout carries historical import/shader logs and one user's editor state. Ordinary editor writes to these tracked paths remain eligible for diffs and commits despite the ignore rules, adding irrelevant changes to source reviews. This is repository hygiene, not a demonstrated runtime defect; no editor was launched to reproduce writes.

**Safe coordinator action:** Remove only these exact paths from Git tracking, retaining local copies and existing ignore rules. Preserve any required diagnostic evidence before a cleanup commit; keep committed history and all verification reports. Do not recursively delete `Logs` or `UserSettings`, and do not inspect or rewrite personal settings values as part of this cleanup.

## Finding 2 — P3: Generated Python bytecode remains tracked alongside its source

**Locations:** `.gitignore:112-113` (`__pycache__/` and `*.pyc`); exact binary paths below (binary files have no meaningful source-line number).

Focused index queries found **39 CPython bytecode files, totaling 1,119,279 bytes**. Each maps to an existing `.py` file by removing `/__pycache__` and its `.cpython-311` or `.cpython-313` filename tag. A separate `git ls-files -- <mapped source paths>` query confirms all **38 distinct sources are tracked**; `Tools/ui/asset_import.py` has two interpreter-version cache files. No source is missing or untracked among these mappings.

```text
Blender/bosses/__pycache__/_common.cpython-313.pyc
Blender/enemies_a/__pycache__/_common.cpython-313.pyc
Blender/enemies_a/__pycache__/creature_kit.cpython-313.pyc
Blender/enemies_b/__pycache__/_common.cpython-313.pyc
Blender/environment/__pycache__/_arenas_a.cpython-313.pyc
Blender/environment/__pycache__/_kit_common_a.cpython-313.pyc
Blender/environment/__pycache__/_kit_common_b.cpython-313.pyc
Blender/environment/__pycache__/_kit_interact_a.cpython-313.pyc
Blender/environment/__pycache__/_pipeline.cpython-313.pyc
Blender/environment/ember_caverns/__pycache__/arena.cpython-313.pyc
Blender/environment/ember_caverns/__pycache__/kit.cpython-313.pyc
Blender/environment/frost_grotto/__pycache__/kit.cpython-313.pyc
Blender/environment/haunted_crypt/__pycache__/kit.cpython-313.pyc
Blender/environment/verdant_ruins/__pycache__/build_verdant_ruins.cpython-313.pyc
Blender/lib/__pycache__/abyss_bpy.cpython-313.pyc
Blender/lib_humanoid/__pycache__/body.cpython-313.pyc
Blender/lib_humanoid/__pycache__/costumes.cpython-313.pyc
Blender/lib_humanoid/__pycache__/humanoid.cpython-313.pyc
Blender/lib_humanoid/__pycache__/motion.cpython-313.pyc
Blender/lib_humanoid/__pycache__/produce.cpython-313.pyc
Blender/props/__pycache__/equipment.cpython-313.pyc
Blender/town/__pycache__/_common.cpython-313.pyc
Blender/weapons/__pycache__/_common.cpython-313.pyc
Blender/weapons/__pycache__/arcane.cpython-313.pyc
Blender/weapons/__pycache__/bows.cpython-313.pyc
Blender/weapons/__pycache__/swords.cpython-313.pyc
Tools/audio/__pycache__/effects.cpython-311.pyc
Tools/audio/abyss_audio/__pycache__/__init__.cpython-311.pyc
Tools/audio/abyss_audio/__pycache__/dsp.cpython-311.pyc
Tools/audio/abyss_audio/__pycache__/instruments.cpython-311.pyc
Tools/audio/abyss_audio/__pycache__/master.cpython-311.pyc
Tools/audio/abyss_audio/__pycache__/music.cpython-311.pyc
Tools/audio/songs/__pycache__/__init__.cpython-311.pyc
Tools/audio/songs/__pycache__/jingles.cpython-311.pyc
Tools/audio/songs/__pycache__/motifs.cpython-311.pyc
Tools/audio/songs/__pycache__/score.cpython-311.pyc
Tools/audio/songs/__pycache__/title.cpython-311.pyc
Tools/ui/__pycache__/asset_import.cpython-311.pyc
Tools/ui/__pycache__/asset_import.cpython-313.pyc
```

**Read-only reproduction:** Run `git ls-files -- ':(glob)**/*.pyc' ':(exclude,glob,icase)library/**'`; check each mapped source with `Test-Path -LiteralPath`, then query the mapped paths with `git ls-files`. These were performed without importing or executing the Python modules.

**Reachable impact:** Every checkout includes these generated binary caches despite the explicit exclusion rules. Normal source/interpreter changes can regenerate them and create opaque binary diffs. No claim of stale-bytecode execution or game failure is made.

**Safe coordinator action:** Untrack only the 39 listed `.pyc` files, keeping their original `.py` sources, assets, license files, and existing ignore rules. Retaining local caches avoids any operational deletion; subsequent Python execution can manage them normally. Do not delete whole `Blender` or `Tools` directories.

## Preservation and acceptance checks

- [x] Exactly two concrete findings, with line anchors, exact tracked paths, and read-only reproduction evidence.
- [x] Candidate total: **49 files / 2,287,833 bytes**. This is current file size, not a promise of Git history or disk-space reclamation.
- [x] No tracked root `Temp`, `Build`, `Builds`, `build`, `.cache`, or `obj` files returned by the root query.
- [x] A focused index query for nested Temp/build/cache/obj, `__pycache__`, `.vs`, and `.gradle` paths, excluding Library, returned 79 paths: the 39 bytecode files above and 40 `Assets/Temp` image/metadata paths. The latter are **preserved**: their names include battle/title/tour screenshots and could be original visual proof. Directory naming alone does not establish that they are disposable.
- [x] Preserve `Assets`, `ArtSource`, original Blender/Python sources, licenses, all `docs/verification` evidence, and existing history. No broad repository or Library scan performed.
- [x] Reports 01–07 were searched only for overlapping cleanup terms; the relevant hit in `06-auto-battle.md:32` mentions an existing `Temp/LogicTests/LogicTests.exe` run, not a tracked cleanup candidate. No tests were rerun.
- [x] Only the assigned report was written. Integration, final cleanup decisions, and any future Git index changes belong to the main coordinator.
