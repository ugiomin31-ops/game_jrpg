# Tripo Studio spell motion pilot — 2026-10-15

Status: raw FBX downloaded and skin deformation verified. Rig passes. Generated motion is retained as a source candidate and NOT installed over the existing shared Spell: the inspected sequence lacks the requested distinct forward palm release and relaxed upright recovery.

- Source site: https://studio.tripo3d.ai/ko
- Uploaded Studio asset: e6b794c1-a873-400a-863f-25fc43740a65
- Input: Assets/_Game/Resources/Art/Characters/h_dohyun/h_dohyun.fbx
- Input SHA256: E7E7432BE409C159DC9BBD9E75A1F56141A374AE45DB49108A0C140FD5B9F878
- Existing concept/pick/retopo provenance: ArtSource/hunters/h_dohyun/candidates/prompts.md. Candidate C; Tripo Triangle Smart Mesh P1.0 target 16000, actual 9435 triangles. No new concept or model generation needed for this animation carrier.
- Studio upload orientation: Y rotation 90 degrees, visually checked front A-pose. Original UV preservation enabled.
- Baseline Blender 5.2.1: Body 4711 vertices, 9435 triangles, zero unweighted vertices, Rig 65 bones. RightArm 45 degree pose moves 788 vertices, max displacement 0.551075; no asset saved by diagnostic.
- Balance before work: 3500 subscription credits.
- Rig screen: Humanoid, Mixamo preset, displayed cost 20 credits; balance 3500 -> 3480 confirmed after completion.
- Motion: Text to Motion, duration 3 seconds, displayed cost 20 credits. First task 560485d7-9744-4c97-a8b0-f14e65dd97b2 failed with Studio notification "Motion Generation Failed" and a full refund (3460 -> 3480). Same prompt retried once; successful "Casting a Spell" result, final balance 3460. Net spend: rig 20 + motion 20 = 40 subscription credits. No specific motion model version is exposed by the UI.
- Export: FBX, Mixamo preset, skeleton on, current-frame-only off, exactly one animation, in-place on. Web export saved unchanged as h_dohyun_spell_tripo_20261015.zip; ZIP SHA256 E39BB0A6D499F775C581AC375DFFF746E672328977FE73FDD119F347DE6AF8BB. Raw FBX is raw/tripo_convert_64175365-296b-49c6-aea7-0fd0019234dd.fbx. Tripo tab closed immediately after download.
- Exported rig check: mesh 4711 vertices, 9435 triangles, 65 bones, zero unweighted vertices. RightArm 45 degree rotation moves 791 vertices; max displacement 0.303212. Raw source was never re-exported or edited.
- Motion inspection: one take, 24 FPS, frames 0..71 (about 2.96 seconds). Five rendered poses at 0/25/50/75/100 percent reviewed. Hands remain near the chest/waist or spread sideways, and the end returns to the bent ready pose instead of the requested relaxed recovery. This does not meet the shared Spell replacement brief. No extra paid generation for variety was performed.
- Exact motion prompt: A standing human casts one powerful spell forward. Start upright with both feet planted shoulder-width apart. Raise both hands to chest height, draw the hands slightly inward to gather energy, then extend both open palms forward in one clear decisive release. Keep the torso upright and the knees only slightly bent. Finish by smoothly lowering both arms back to a relaxed upright standing pose. Stay in the same place facing forward throughout. No walking, jumping, kneeling, spinning, or crouching.
- Purpose: evaluate a readable upright spell-release motion for shared Spell. Keep existing animation until a downloaded Studio result passes skin deformation, humanoid retarget and Unity playback checks.
- Requested agent route for evaluation: gpt-6-astra / high; priority configured. The Tripo UI does not expose reasoning effort.

## Acceptance

- [x] Record exact motion prompt and displayed motion model.
- [x] Record paid step balances and costs.
- [x] Download raw FBX with skeleton unchanged into this directory; hash it.
- [x] Verify exported skin weights and bone-driven deformation in Blender.
- [x] Inspect wind-up, release, recovery, feet and silhouette in five Blender rendered frames; motion quality gate failed before Unity import.
- [x] Preserve existing game animation because the candidate did not satisfy the replacement brief. No runtime asset was overwritten.
