# Tripo motion and skill presentation improvement

- Status: verified bounded improvement pass complete, 2026-10-15 KST.
- Base: claude/motion-polish-pr9, 7d20749ef1ef12b120330fd4cac79f3ce850f20c.
- Report: docs/verification/tripo-motion-20261015/README.md.
- Baselines, worker logs and failed attempts: .git/codex-runs/20261015-165918-tripo-motion/.

## Acceptance

- [x] Preserve initial 232 dirty status entries, patches and 339 hashes. Final: no missing, 334 identical, five intentionally edited.
- [x] Inspect existing design contract, Unity baseline and Tripo access.
- [x] Split into 30 review scopes; 27 added CLI workers and eight follow-up fix workers completed with reports and exit 0. Requested Astra/high/priority recorded; actual server tier receipt unavailable.
- [x] Follow subsequently supplied AGENTS policy for final independent review: one Sol high worker. Restore original global Luna/high/one defaults. Close all workers.
- [x] Baseline logic 215/215 passed.
- [x] Apply bounded combat preview, trail timing, enemy MP/balance, reserve services, equipment, overflow, quest recovery, damage feedback, input, HUD, revive eligibility, resource cleanup and spent-kit map fixes.
- [x] Reproduce failures narrowly, then final integrated logic 259/259 passed without weakening tests.
- [x] Studio-only pilot: existing retopologized hunter, Humanoid/Mixamo rig and one successful motion. Exact prompt, displayed costs, balances and raw source hashes recorded in ArtSource.
- [x] Blender confirms 9435 triangles, 65 bones, zero unweighted vertices and real bone-driven deformation.
- [x] Inspect five motion poses. Motion fails intended release/recovery brief; retain as source candidate, preserve existing game Spell. No further generation for variety.
- [x] Unity runtime: VFX42, input43, atmosphere32, HUD121 per layout, compact transition13, revival25, battle/animation/framing67 passed.
- [x] Inspect four battle screenshots at1280x720 and915x412 and two arrow VFX captures at1x/2x.
- [x] Fresh final console compilationFailed=false, errors0, warnings0. Final battle callback issues0.
- [x] Preserve player saves through QA isolation, restore preferences/GameView settings, stop Play, close Tripo after download.

## Decisions and limits

Tripo net cost40 subscription credits: rig20 + successful motion20. First motion failed/refunded; same prompt retried once. Balance3500->3460. Rig passes; motion candidate rejected before game import.

Command camera intentionally frames the active hero and enemies; off-duty teammates can leave the frame. Establishing and command shots were verified separately against the HUD-free viewport. No production camera change was needed.

First integrated suite258/259 failed campaign balance. One bounded stat adjustment restored the unchanged gate, then full259/259 passed. Scrap colossus under-prepared25% is exactly the fixed60-seed floor. Existing25 unrelated generator/data row differences remain; affected rows match.

Deferred unproven current-player cases: damaging random-ally retarget, missing-resource audio fallback, tween cancellation API, Android batch invocation. Physical-device touch and whole-campaign visual coverage are not claimed. Native trail timestamps are not retimed or fully frozen by local zero speed.

No checkout/reset/clean, commit or push. Local changes and raw assets are reviewable through the report.
