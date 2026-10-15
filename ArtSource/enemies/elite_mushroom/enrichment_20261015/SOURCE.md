# Elite mushroom — Studio raw source, 2026-10-15

Status: downloaded and skin deformation verified; NOT installed into Unity gameplay.

Source: https://studio.tripo3d.ai/ko/workspace/animate/92cbf8f4-18e0-4471-8332-c6c315f35102
Browser: Codex in-app browser, explicitly authorized by user. Studio subscription only; no API/key.
Reference: existing ChatGPT web GPT-6 Extra High candidates from 2026-10-13. Exact original prompt and chat URL: candidates/original-prompts.md. No new image prompt this pass. Studio image-to-3D input was candidate_D.png unchanged, with no extra text prompt.

All four candidates A-D were viewed. D chosen for taller conical cap, arm/shoulder spore nodules, assertive brow and separated limbs. B is the normal mushroom already in game; C is too similar to B; A fur detail is less robust at game mesh resolution. The original prompt file also records historical B production, which is not evidence of this new D model.

## Paid steps and output

| Step | Selected settings | Displayed cost | Balance |
|---|---|---:|---|
| Image to 3D | H3.1 highest quality, candidate D | 55 | 3460 -> 3405 |
| Retopo | Triangle, Smart Mesh P1.0, target 12000 | 35 | 3405 -> 3370 |
| Rig | Humanoid, Mixamo | 20 | 3370 -> 3350 |

One generation per step. Raw model displayed 1,934,274 triangles; retopo displayed 11,662 triangles / 11,382 vertices. Net paid110 credits. Seven free presets: walk, hit_to_body_01, idle, cheer, cast_a_spell, defeat_02 (UI), box_01. No further observed balance change.

Export: FBX / Mixamo / skeleton ON / texture2k / all7 selected / in-place ON. Settings in export-settings.jpg; export confirmation in export-complete.jpg. Downloaded elite_mushroom_tripo_20261015.zip through Studio; original ZIP and its extracted raw directory are unchanged. Download was requested again to capture its local path after a browser handler timeout; no new generation or credits. Studio tab closed immediately after the confirmed download and proof capture.

## Actual Blender checks

Blender5.2.1 LTS imported the FBX. 1 mesh, 11,662 triangles, 5,836 mesh vertices, 65 bones. Studio displayed vertices and Blender mesh vertices use different counting. All 5,836 vertices weighted, invalid weights0, unweighted0. Twelve major limb probes moved vertices: rig-validation.json. Textures read as 2048x2048: export-inventory.json. verify_tripo_rig.py reads/imports and temporarily poses bones; it does not save or re-export the source.

IMPORTANT: the 7 selected presets are concatenated into ONE FBX take, frame0..368, named Armature|walk_hit_to_body_01_idle_cheer_cast_a_spell_defeat_03_box_01|Base Layer. They are not seven independent game clips. UI defeat_02 vs exported defeat_03 needs visual identification. Split after measuring each boundary, or export individual existing Studio presets. Motion quality and Unity integration remain unverified.

## Next integration

Keep raw files unchanged. Preserve the existing elite_mushroom runtime FBX and meta GUID until a verified replacement is ready. Work on a copy. Need seven Generic clips Idle/Run/Attack/Cast/Hit/Die/Victory, TRIPO import marker (not HUMANOID), basecolor material and measured scale/feet/contact. Review whether walk is appropriate for Run. Change both Resources/Data/enemies.json and Tools/content/world/base_enemies.json model mapping together. Existing own-model tint semantics and scale_mult must be inspected; do not assume violet tint will apply automatically. Capture actual Unity combat and matching bestiary icon before claiming applied.

SHA256 archive and extracted bytes: raw-hashes.json. Exact prompt/model provenance and all candidates are preserved beside this record.
