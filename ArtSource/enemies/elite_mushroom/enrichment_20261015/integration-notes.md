# Elite mushroom — measured motion handoff, 2026-10-15

**Decision: do not split this export into seven clips.** The existing FBX has one short changing sequence followed by a static hold, not seven measurable consecutive motions. No replacement FBX, synthetic animation, Unity import or data edit was made. The parent can obtain the seven existing presets individually from Studio without another model/retopo/rig generation.

This supersedes the *concatenated seven motions* interpretation in `SOURCE.md:27` and the earlier audit, without changing those historical records. The action's combined name is metadata, not evidence of seven motion intervals.

## Source identity and fresh rig evidence

- Raw FBX: `raw/tripo_convert_d949cdaa-e88a-49f9-895a-cfd278c89c81.fbx`, 24,791,728 bytes.
- SHA256: `aacefeab5b92ebc51ee2be873739280bc8bb25aff456e4569082afb47f87be7c`.
- The original ZIP, FBX and five textures all match the seven entries of `raw-hashes.json`. Before/after confirmations are in `processed/raw-hashes-before.json`, `processed/raw-hashes-after-analysis.json`, `processed/raw-hashes-after-render.json`, and `processed/motion-evidence.json`.
- Fresh Blender **5.2.1 LTS** run: 65 bones, 5,836 vertices, 11,662 triangles; all vertices weighted; zero unweighted or invalid weights; all 12 major-limb deformation probes PASS, no failures. See `processed/rig-verification.json` and `.log`. This is actual mesh deformation evidence, not a skeleton-presence check.
- No raw bytes or original animations were saved back. Inspection lighting, camera, floor and simplified basecolor material exist only in temporary Blender sessions and rendered PNGs.

## Measured timeline and exact uncertainty

Every integer frame 0..368 was evaluated at 24 FPS, including all 65 bone-head positions, normalized local bone rotations, evaluated mesh bounds and weighted foot-surface markers. The binary FBX was also parsed directly, independently of Blender's action-name interpretation.

| Evidence | Result |
|---|---|
| Binary AnimationStack / AnimationLayer | Exactly 1 / 1 |
| Binary AnimationCurve objects | 585; each has 369 samples, native key frames -1..367 |
| Nonconstant binary curves | 369 |
| Last changing native key | Frame 52; Blender importer presents this as frame 53 |
| Curves changing after native frame 60 | 0 |
| Blender imported take | 0..368, 24 FPS, 650 F-curves |
| Observed changing motion envelope | Blender 0..53 inclusive: 54 sampled poses, 2.208333 seconds between endpoints |
| Constant tail | Blender 53..368; bone-head positions and tracked foot markers do not move |

`processed/raw-animation-curves.json` contains the direct binary-channel measurements. `processed/motion-evidence.json`, `frame-metrics.json`, and `motion-samples.npz` hold the measurements and thresholds. Pose-change detection uses 0.01 degrees or 0.000001 world-unit bone-head displacement; the static tail's quaternion residual is only about 0.0000024 degrees from floating-point conversion.

The short sequence shows an upper-body/arm movement and weight shift before returning to its initial stance. The combined take name ends in `box_01`, so an attack interpretation is plausible, but the export supplies no independent seven-segment markers or per-preset actions. **Only the changing envelope and static tail are verified; seven semantic boundaries are unavailable.** In particular, there is no measured death collapse or separate locomotion/cheer/cast interval. A static tail must not be relabeled as an animated Idle.

## Foot contact and seam measurements

Units below are imported Blender world units, not a confirmed Unity meter scale. Frame-0 mesh height is **0.9716505334**. The reference floor is the lower foot surface at frame 0: **Z = -0.0470462963** (full precision in JSON). It is an estimated reference, not authored ground. We tracked the fixed lowest 20% of each foot-weighted mesh region, with foot/toe weight sum >0.5. A near-floor sample is within 2% of model height above the reference; a low-speed candidate is at most 5% of height per second in XY.

For the changing interval 0..53:

| Metric | Left foot | Right foot |
|---|---:|---:|
| Near-floor samples | 54/54 | 54/54 |
| Low-speed near-floor transitions | 10/53 | 12/53 |
| Maximum tracked sole XY speed | 0.829350953 /s | 0.556424521 /s |
| Maximum surface depth below neutral reference | 0.038668536 | 0.027066685 |
| Maximum surface height above reference | 0.004130255 | 0.008027807 |
| Endpoint sole distance, frame 0 to 53 | 0.0000001824 | 0.0000000984 |

These are movement/contact candidates, **not a planted-foot PASS**. The feet slide/rotate and the sampled surface crosses the neutral reference. No foot correction or procedural motion was added. The render floor uses the separate 5th-percentile foot-height estimate (-0.0594591586), so render shadows must not be substituted for the numeric contact result.

Frame 0→53 endpoint pose seam: maximum local bone angle **0.000820153°**, RMS **0.000153810°**, maximum bone-head distance **0.00000117993**. The maximum bone-head endpoint velocity mismatch is **0.180460759 /s**. Matching endpoint poses therefore do not prove a smooth looping action. The entire take also ends in the starting pose, but looping it would introduce approximately 13 seconds of static hold. No loop setting is approved.

## Actual rendered evidence for parent review

- [22-pose overview, 1920×1280](processed/contact-sheet-verified-overview-front.png): frames 0, 6, 12, 18, 24, 30, 36, 42, 48, 52, 53, 54, 60, 72, 96, 120, 168, 216, 264, 312, 360, 368.
- [12-pose oblique detail, 1920×640](processed/contact-sheet-motion-detail-three-quarter.png): frames 0, 8, 12, 18, 24, 30, 36, 42, 48, 52, 53, 368.
- Individual full-resolution tiles: `processed/renders/verified-overview/front-*.png` and `processed/renders/motion-detail/three-quarter-*.png`; the render-index JSONs list exact paths.
- These are Cycles CPU renders of the original evaluated skin and original basecolor texture, 320×320 per tile, 12 samples, four threads. The label `front` denotes the fixed +Y inspection view, not a verified Unity forward direction; oblique uses (+0.85,+1,+0.10). Geometry, UVs and animation were not edited. Cap occlusion limits judging facial detail, but feet, silhouette and upper-body changes are visible.
- `processed/renders/overview/front-0000.png` and `contact-sheet-overview-front.png` are the **superseded -Y camera smoke check**, not the accepted overview. Early logs preserve the corrected missing-world/parser-import failures; successful runs and final acceptance are separate.

## Proposed Unity mapping — blocked until distinct existing presets are exported

Machine-readable version: `processed/proposed-unity-clip-ranges.json`. Generic rig, original skin/skeleton, no HUMANOID conversion assumed. Blender imported frames have a +1 offset from native FBX key times; Unity's take origin/FPS has not been tested, so no importer-ready range is approved.

| Slot | Current-file range | Parent's next existing-preset export | Gate |
|---|---|---|---|
| Idle | None verified | `idle`, alone | Real breathing/idle movement and seam review; do not use static 53..368 |
| Walk | None verified | `walk`, alone | Verify foot cadence, in-place/root travel and seam |
| Run | None verified | None justified by this source | Do not relabel walk as run; select a genuinely existing run preset only if needed |
| Attack | Candidate Blender 0..53 only; not approved | `box_01`, alone | Compare the isolated preset against this short sequence and review contact timing |
| Cast | None verified | `cast_a_spell`, alone | Identify wind-up, release, recovery |
| Hit | None verified | `hit_to_body_01`, alone | Verify distinct impact/recovery |
| Die | None verified | The existing selected defeat preset, alone | Resolve UI `defeat_02` versus exported name `defeat_03` by visible playback |
| Victory | None verified | `cheer`, alone | Confirm complete cheer and ending/loop intent |

For each individual export: choose exactly one existing preset, FBX with skeleton on, retain raw download, verify source hash/weights, measure its actual take duration and contact/seam before filling final Unity ranges. No paid step was used or authorized by this delivery. This run did not open Studio or a browser.

## Reproduction and acceptance

Run only `C:\Users\User\Tools\Blender\blender.exe` headlessly. Successful later runs use `--background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1` (session flags only; no saved configuration change). Invoke `Tools/inspect_elite_mushroom_motions.py` with `-- analyze`, then `-- evidence`; render commands and exact samples are recorded in `processed/delivery-verification.json`. The existing `Tools/verify_tripo_rig.py` independently produced the skin report. No other compiler was used.

- Requested execution: `gpt-6-astra` / `high`, Fast/priority requested. No independent served-model/effort/tier receipt is exposed here; none was inferred from configuration. No nested agents, model changes, reset or commit.
- Completed: actual rig/weight recheck, raw-hash confirmations, full-frame motion/channel measurements, contact/seam metrics, two actual contact sheets and explicit blocked Unity mapping.
- Intentionally withheld: fabricated seven-way split, an unverified Attack extraction, new motion, Unity import, runtime/data edits. This follows the user's explicit fallback when reliable boundaries cannot be recovered.
- Remaining parent action: individually export existing presets and review them; this file cannot supply the missing intervals. All work stayed in `processed/`, this note and the permitted inspection script.

## Parent disposition — 2026-10-15

The parent reviewed both standalone Cast contact sheets and **declined Unity integration**: the approximately 19.6 cm recovery contact drift does not meet the user's requested naturalness. Preserve the standalone raw source and `individual-motion-exports/cast/verification.md` as evidence; the worker's technical motion-validity result is not final asset acceptance. Do not replace or regress the existing game asset, import this Cast, or perform further cleanup in this bounded finish. Parent already added the `.gitignore` rule excluding reproducible `processed/source-input/` staging; original `raw/` exports remain retained. This dated parent decision leaves the historical measurements above unchanged.

## Game install — 2026-10-15 (PR #11)

Six single-preset Tripo Studio exports (Blender FBX preset, skeleton and in-place on, 0 credits) are kept unchanged under `individual-motion-exports/<preset>/elite_mushroom_<preset>.zip`. Studio lists no `defeat_03`; the `defeat_02` export's take is named `defeat_03` inside the FBX. `Tools/merge_tripo_enemy_takes.py` merged them into `Assets/_Game/Resources/Art/Enemies/elite_mushroom/elite_mushroom.fbx` (existing `.meta` and GUID kept) with a `TRIPO` marker and `elite_mushroom_tex/elite_mushroom.png` (basecolor, 2048). Report: `merge-report.json`.

| Game clip | Source | Frames | Notes |
|---|---|---|---|
| Idle | idle | 369 | loops (first/last pose within 0.8 mm) |
| Run | walk | 57 | loops; no run preset, the game scales Run's rate to travel speed |
| Attack | box_01 | 54 | |
| Cast | standalone cast_a_spell, Blender 0..88 | 89 | ends before the B89+ recovery whose ~19.6 cm foot drift was rejected; the game crossfades back to Idle |
| Hit | hit_to_body_01 | 32 | |
| Die | defeat_02 (take defeat_03) | 134 | collapse sank parts up to ~0.18 below the frame-0 floor; merged with `+ground`, the root is lifted on 122 frames (max 0.187) so the lowest point stays at the Idle floor (-0.027); pose unchanged |
| Victory | cheer | 291 | |

Every take was compared against its source after the FBX round trip: evaluated skin matches within 0.000001 units at start, middle and end frames. The Cast source uses Tripo's Mixamo preset (armature scale 0.01), so its bone translations are rescaled to the Blender preset's unit armature by the merge script. `enemies.json` now gives `elite_mushroom` its own model (no `model` alias, neutral tint; `scale_mult` 1.35 unchanged). Unity import and in-game playback are not yet verified.
