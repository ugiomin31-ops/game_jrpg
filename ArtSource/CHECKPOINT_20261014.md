# Tripo source checkpoint — 2026-10-14

This is a source-material checkpoint for PR #8, NOT an approved gameplay release.

## Included

- Original downloaded hunter motion bundles (20261014 and 20261014b).
- Original monster motion bundles for forest_guardian, sprout, mushroom and pixie, including the guardian's later bundle.
- All six concept candidates and the original sheet for aid_kit, gate_keycard and riot_shield, their prompts, Tripo exports, textures and downloaded ZIPs.
- Pre-install motion and key-item backups.
- Motion plan, installation work notes, feature observations and credit ledger.
- `CHECKPOINT_20261014.sha256`: hashes and relative paths of the scoped material and records (excluding this manifest itself).

These files are explicitly staged despite the existing ArtSource binary ignore rules. No source geometry or image was reduced to fit Git. This checkpoint does not include unrelated earlier ArtSource batches, tool installers, credentials, user saves, logs, caches or local QA output.

## Review and unfinished implementation

Astra's interrupted-work review: CHANGES REQUIRED for the full implementation. Offline runtime/editor compilation and 195 engine-independent tests passed, and the current effect references resolve. However:

1. The generator's presentation-reference validation does not yet include the new `heal_vfx` field.
2. Final Unity import, animation retargeting and in-game verification after the interrupted edits are incomplete.
3. aid_kit and gate_keycard were produced with Smart Mesh P2.0 as quad meshes, textured and exported. A separate Triangle Retopo step is NOT recorded. They are preserved as delivered, not represented as having completed that step.
4. Installation notes describe work performed; they do not constitute final QA approval. Uncommitted runtime code and installed Assets remain outside this checkpoint.

Claude implementation work stopped at its weekly usage limit. No replacement implementation worker was authorized for this checkpoint. The reviewed runtime baseline before this source-only commit is `7fede68b6c45414f18e634604c99f56322b931ae`.

## Credits

Starting balance for this batch: 590. Recorded spending: 480 on 24 paid motion clips, 20 on textures for two free Smart Mesh trial objects, and 80 on HD generation plus Smart Mesh retopology for the shield. Last recorded balance: **10**, not zero. No additional spend occurred while creating this checkpoint.

## Restore/use

Use the preserved FBX files with their adjacent texture folders. ZIPs are retained as downloaded backups; they are untrusted input and should be extracted into separate empty directories, not used as script execution directories. Preserve original geometry, UVs and native-resolution textures. Apply only necessary axis/pivot and uniform-size transforms for game integration. Keep Unity GUIDs when replacing existing installed assets.
