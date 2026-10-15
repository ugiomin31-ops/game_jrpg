# 49-rig-evidence — bounded read-only audit

- Scope: existing Tripo export evidence and `Tools/verify_tripo_rig.py`; no game fixes.
- Verified checkout: `codex/astra-enrichment-20261015`, HEAD `efdc1517`.
- Requested model: `gpt-6-astra`; requested reasoning: `high`; requested service tier: Fast/priority. The provided tools expose no independent inference-routing or served-tier receipt, so actual model/effort/tier are not independently verified. No model, persona or configuration was changed; no child agents were launched.
- Method: focused source/sidecar/JSON reads and file existence/size checks. Existing Blender results below are historical artifacts, not checks rerun by this audit. No tests, builds, Blender/Unity/browser execution, network requests, image generation or authentication reads.

## Findings (2 existing asset-acceptance gaps)

### 1. Elite mushroom skin PASS does not supply the seven usable animation clips

**Exact evidence:** `ArtSource/enemies/elite_mushroom/enrichment_20261015/export-inventory.json:13-20` records a single action named `Armature|walk_hit_to_body_01_idle_cheer_cast_a_spell_defeat_03_box_01|Base Layer`. `ArtSource/enemies/elite_mushroom/enrichment_20261015/SOURCE.md:27` explicitly records one concatenated take, frames 0..368, unresolved boundaries, and the UI `defeat_02` versus export `defeat_03` mismatch. The required seven slots and outstanding integration are at `SOURCE.md:31`.

**Reproduction by inspection:** compare that one-action inventory with `rig-validation.json:5` (`passed: true`) and `Tools/verify_tripo_rig.py:91` (`use_anim=False`). The verifier deliberately imports without animation. Its static rotation probes cannot validate take splitting, death identity, locomotion suitability or playback timing.

**Impact:** this downloaded candidate is not yet ready to replace the elite's animation set. Promoting its skin PASS to animation acceptance would skip the required Idle/Run/Attack/Cast/Hit/Die/Victory validation. This is an existing integration blocker, not evidence that the currently installed elite is broken: `SOURCE.md:3` expressly says this source is not installed.

**Bounded follow-up:** preserve raw bytes; on a working copy, measure all seven segment boundaries, identify the actual death motion, and inspect whether walk is acceptable for Run. Validate each resulting slot independently before any runtime replacement. Reuse the already exported motions first; this finding does not justify another paid model or rig generation.

### 2. Spell candidate's skin evidence is narrower than a whole-rig check, and its motion already failed the replacement brief

**Exact evidence:** `ArtSource/hunters/_anim_library/tripo_spell_20261015/inspection/rig-check.json:6-8` records 4,711 vertices and zero unweighted vertices; lines 18-21 contain only the `mixamorig:RightArm` probe, 791 moved vertices, and stable vertex count. `ArtSource/hunters/_anim_library/tripo_spell_20261015/SOURCE.md:3,17-19` records the missing distinct forward palm release and relaxed upright recovery, and explicitly retains the existing shared Spell. `inspection/motion-report.json:3-16` records one take, 24 FPS, frames approximately 0..71.

**Reproduction by inspection:** read the entire 22-line rig-check JSON: it contains one posed bone, not a per-limb probe list. Compare this with the multi-limb selection in `Tools/verify_tripo_rig.py:130-134`, then compare the documented inspected poses with the exact spell brief at `SOURCE.md:18`.

**Impact:** the record establishes real right-arm skin deformation; it does not independently establish deformation of the other limbs or an acceptable shared spell animation. The required replacement remains undelivered. No current gameplay regression is claimed, because the source was deliberately not installed. The recorded visual rejection was not independently re-rendered in this audit.

**Bounded follow-up:** retain this source as a rejected motion candidate. If reconsidered, run the existing verifier once on this FBX for bilateral arm/forearm/hand and leg/foot evidence. Required motion remains a planted upright wind-up, distinct forward open-palm release, and smooth relaxed upright recovery. Rig PASS alone must not override the recorded motion rejection or trigger replacement of the existing shared animation.

## Proposed verification boundary for the coordinator (not executed)

1. Start only with the two exact FBXs already located: spell `raw/tripo_convert_64175365-296b-49c6-aea7-0fd0019234dd.fbx` (1,569,664 bytes), and elite `raw/tripo_convert_d949cdaa-e88a-49f9-895a-cfd278c89c81.fbx` (24,791,728 bytes), under their respective source folders above. Record current hashes against the retained provenance; the historical JSONs point to the earlier `game_jrpg-pr9` checkout, not this audit checkout.
2. Keep three separate decisions: source identity, static skin deformation, and animation/playback acceptance. The elite already has a recorded 12-limb PASS, 5,836 weighted vertices and zero unweighted/invalid vertices (`rig-validation.json:10-13,67-80,266`). Reuse that evidence if byte identity is established; rerun only when identity or provenance is unresolved. The spell's single-arm evidence warrants the bounded multi-limb check if it proceeds toward integration.
3. Inspect the verifier's full output, not only its exit status. `Tools/verify_tripo_rig.py:117,210` intentionally reports partial unweighted vertices without rejecting them. Both reviewed exports report zero unweighted vertices; no partial-weight defect was found in these exports. Any future nonzero result requires a mesh-region review before acceptance. Bone displacement does not establish anatomically correct weights or good animation.
4. After the source gates, the coordinator can separately authorize actual target-rig playback: elite Generic slot mapping; spell Humanoid retarget on its intended recipients; wind-up/release/recovery, foot contact, loop seams and gameplay event alignment. Keep raw exports and existing runtime assets unchanged until that evidence exists. No such execution occurred here.

## Acceptance checklist

- [x] Expected branch/base checked.
- [x] Relevant script, export sidecars and stored rig/motion evidence inspected; no Library or broad repository scan.
- [x] At most two concrete findings, with exact source locations, inspection reproduction and bounded impact.
- [x] Historical evidence distinguished from fresh runtime verification; no independently proven runtime rig defect claimed.
- [x] Requested model/effort recorded; priority request distinguished from independently verified tier.
- [x] Only this assigned report written; no game/source/configuration changes. Integration remains with the main coordinator.
