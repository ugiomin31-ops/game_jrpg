# Town follow trail — parent runtime evidence review

2026-10-15. Requested model/effort: `gpt-6-astra` / `high`, Fast/priority requested; actual routing/effort/tier were not independently attested. Follow-up to `town-breadcrumb-input-order.md` and `reviews/world-input.md` under the approved enrichment plan.

**Disposition: no additional production repair.** The parent-run result contains 49 checks: 48 passed, one failed. All 18 checks in the three `L-route-*` phases passed. The sole failure is `actual-tree-proxy-and-former-location / former proxy location is traversable`: the controller moved 1.27192783 m of a requested 1.80000055 m and reported `Sides`. That separate collision-location failure is left to its environment/fixture owner; it is not evidence of a follower-trail defect. Overall result status remains **failed**.

## Reviewed evidence

- Original: `docs/verification/astra-enrichment-20261015/runtime/town-trail-20261015-140442-560/result.json`; SHA-256 `93ff2a452fd5e32e746b3407cee44d8b29496844d298d349308c982724a8d65c`.
- Parent-run Unity version: `6000.3.25f1`; recorded assembly SHA-256 `a1e8147c28458312ab485befb9d11b1f612e2b96c64c5fe39faf348aa54e52c1`.
- Recorded `build.town` equals the current `Assets/_Game/Scripts/Runtime/World/TownWorld.cs` SHA-256: `bf735c7c519c23ce4e5ede1a789b6df91661a29f0b88d7687377d5ad0862d136`. This source was not changed after inspecting the result.
- Read all check records and re-aggregated the recorded position/count/delta samples without rerunning the fixture. No evidence, fixture, `TownWorld.cs`, `GameUI.cs`, helper or asset was edited during this review. This note is the only write.

| Recorded profile | Ticks | Peak points per follower | Largest sampled horizontal displacement | Final adjacent gaps |
|---|---:|---|---:|---|
| 60 Hz L route | 242 | 16 / 32 / 46 | 0.058391 m | 0.950044–0.950097 m |
| Mirrored L route, 250 ms delta | 46 | 7 / 14 / 14 | 0.350067 m | 0.950027–0.950063 m |
| L route, 100 ms delta every third frame | 46 | 6 / 14 / 14 | 0.350067 m | 0.950028–0.950079 m |

Each profile reports all four members beyond the obstacle, retained spacing, zero endpoint and swept-capsule intersections with the fixture's skin allowance, and zero longest leader-lock duration. The trace sample maxima reproduce the reported queue bounds. Every recorded delta matches its profile; final samples have input `None` and the gaps above. The 250 ms profile's approximately 0.35 m displacement is consistent with production's 0.1 s movement cap at walking speed. These are whole-tick measurements, not individual controller substeps.

## Scope of the conclusion

The recorded three corner routes support the implemented fix for direct-pursuit stalling, including mirrored turns and delayed/sparse updates. No concrete follower defect was found in this evidence or the corresponding movement methods (`MoveLeader`, `UpdateFollowers`, `MoveMember`, `FollowTrail`). Keep the implementation unchanged.

These traces peak at 46 of 256 points; they do not establish full-buffer backpressure recovery. They also do not establish zero-delta behavior, running/reversal coverage, roster/outfit path preservation, relocation recovery, pause/input-order behavior or all authored town obstacles. Those pending checks and reflection hooks remain documented in `town-breadcrumb-input-order.md`. No screenshots were reviewed for visual acceptance in this follow-up, and no station/tree approval is inferred from the trail checks.

No Unity, compiler, tests, browser or child agents were run here. Parent owns the next execution and final acceptance; focused fixture owner `01a13f91-a03e` retains fixture ownership. The original failed run and traces remain preserved.
