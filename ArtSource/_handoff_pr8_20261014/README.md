# PR8 handoff checkpoint

Status: source preservation and work-in-progress handoff; NOT final gameplay approval.

## Baseline

- Parent branch: `claude/visual-overhaul-pr8`.
- Last reviewed gameplay baseline: `7fede68`.
- Original motion/object material checkpoint already pushed: `b8ff7c5` (98 files, approximately 188 MiB).
- Next branch: `claude/motion-polish-pr9`, branched from the PR8 handoff, not from main. PR8 is not implicitly merged.

## Backups

- `artsource_full.zip` (2,644,358,969 bytes, SHA-256 3039829c5f68d9274d565b22c1fc40534db5c09d63407f506cda1251b4cee749): full ArtSource snapshot (2,615 files: every downloaded Tripo export, native textures, ChatGPT candidates, motion archives, sidecars). Most ArtSource binaries are git-ignored, so this archive is the only copy outside this PC. It is uploaded in two parts to the DRAFT GitHub release `artsource-20261014` of this repository (draft = visible only to repo collaborators). Rejoin: concatenate `artsource_full.zip.part1` + `.part2` in order, check the SHA-256, then extract into an empty folder. Per-file inventory with SHA-256: `artsource_full_manifest.json` (committed).
- Runtime work in progress is committed as normal files on branch `claude/motion-polish-pr9` (commit "WIP: ..."), so another computer can continue from the branch. `runtime_wip_manifest.json` lists the exact files and hashes at handoff time.
- `incidental_local.zip`: LOCAL ONLY (this PC) logs/settings/cache/older QA leftovers; not needed to continue.
- Extract archives into a new empty directory. Never run scripts from downloaded asset directories. Do not overwrite a newer working tree blindly.

No source geometry/texture has been reduced for archival.

## Next actions

1. Verify the interrupted per-hero motion and aid_kit/gate_keycard/riot_shield integration in Unity. The last worker stopped near `heal_vfx` integration/importer work; do not assume final play-mode verification.
2. Include `heal_vfx` in Tools/vfx/gen_effects.py presentation-reference validation. Consumer/schema already exist; validate against current files.
3. Confirm per-hero retargeting, strike/end/loop timings, original geometry/UV/native texture preservation, pause/2x playback and NPC/monster clips. Keep existing safe fallbacks for rejected generated motions.
4. Rerun generator reproducibility, engine tests, compilation and full game checks, then review with GPT-6 Astra high. Earlier offline compile and 195 engine tests passed, but final Unity QA did not.
5. Smart Mesh P2.0 aid_kit/keycard were exported as quads; separate Triangle Retopo is not documented. Preserve delivered originals; do not mislabel or reduce them.
6. Tripo: the account used for this batch ended at a recorded balance of 10 (ledger). At handoff time the Chrome session already showed a different balance (22,300), i.e. the user had switched to another Tripo account, so the old account's export list could not be re-audited live. Everything recorded in the ledger as exported is saved locally and in the archive above. New account: account-3 rigs (hero base 5de41bd4, monster rigs) are NOT available there; new motions need an uploaded FBX + Auto Rig (20).
7. DCC Bridge add-on installed but Studio connection and original-vs-bridge comparison remain unverified. Do not use API-key plugins or bypass browser/desktop permission refusals.

## Rules to retain

- Implementation/verification by Claude, review by Astra 6 high; do not silently substitute Sol, GLM or DeepSeek for implementation after quota failure.
- Keep downloaded Tripo originals unchanged: no polygon reduction, non-uniform reshaping, UV replacement or native-texture quality reduction.
- One Unity owner at a time. Close owned Tripo viewport tabs after export; preserve all completed exports before account switch. No duplicate paid generation.
- Answer user in Korean. Do not merge PR8 without an explicit merge request.
