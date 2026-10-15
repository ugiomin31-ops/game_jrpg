# Bounded campaign balance repair — 2026-10-15 (Asia/Seoul)

Completed in one adjustment iteration. Isolated CampaignBalance filter: baseline exit 1 (0/1), adjusted exit 0 (1/1). No second tuning iteration.

## Scope and routing
Only Tools/content/world/enemies.py, Assets/_Game/Resources/Data/enemies.json and this evidence folder were written. Existing dirty changes were snapshotted before editing and preserved. No agents, broad tests, Unity editor, browser, commit, reset or checkout were used. The harness used bundled Roslyn/Mono without launching Unity.
Requested model/effort: Astra High. Backend model identity/effort cannot be switched or attested from this session; no substitute worker was launched.

## Design and rationale
Read docs/CONTENT_DESIGN.md (damage model, boss phases, expected preparation and boss pacing) and the current generator BOSS_TUNE / CHARGE_SKILLS / SKILL_MP_BUDGETS tables. The older design bible describes the original campaign; current CampaignBalanceTests defines the expanded campaign acceptance bands. No assertions, fixtures, skills, player costs or runtime code changed.
The existing MP fix keeps scrap_colossus at 20 MP and plague_lich at 8 MP. EnemyAI.IsAffordable makes their positive-cost authored moves reachable. The baseline reproduces the reported regression; no MP rollback/causal A-B was performed. This repair compensates through ordinary actor stats.
Scrap colossus remains a slow, armored physical boss: HP, defense, resistance, speed, break shield, phase threshold, skill weights and sk_titan_crash charge identity remain intact. Reduce its existing common offense multiplier by about 5.4% to moderate newly available burst pressure.
Plague lich retains its magic/poison, summon phases and sk_spirit_fire charge identity. Increase only HP by about 8.3% to give the ninth-zone boss an encounter length consistent with adjacent zones. This does not assume HP monotonically lowers simulated win rate; phase timing and surviving samples matter.

## Exact data changes
| Enemy | Field | Before | After |
|---|---|---:|---:|
| scrap_colossus | BOSS_TUNE (HP, offense) | (1.5, 1.85) | (1.5, 1.75) |
| scrap_colossus | attack | 205 | 194 |
| scrap_colossus | magic | 128 | 121 |
| plague_lich | BOSS_TUNE (HP, offense) | (1.2, 2.0) | (1.3, 2.0) |
| plague_lich | max_hp | 24132 | 26143 |

## Simulation metrics
Each row uses the unchanged 60 fixed seeds per boss and preparation. Rounds are averaged over wins, as defined by CampaignSim.Result.AvgRounds.
| Party / zone | Wins before → after | Win % before → after | Mean winning rounds before → after |
|---|---|---|---|
| under-zone3 | 10/60 → 15/60 | 16.666667 → 25.000000 | 13.400000000 → 13.466666667 |
| expected-zone3 | 35/60 → 41/60 | 58.333333 → 68.333333 | 11.171428571 → 11.560975610 |
| under-zone9 | 21/60 → 22/60 | 35.000000 → 36.666667 | 14.428571429 → 14.454545455 |
| expected-zone8 | 45/60 → 45/60 | 75.000000 → 75.000000 | 11.533333333 → 11.533333333 |
| expected-zone9 | 47/60 → 48/60 | 78.333333 → 80.000000 | 8.957446809 → 9.812500000 |
| expected-zone10 | 49/60 → 49/60 | 81.666667 → 81.666667 | 9.673469388 → 9.673469388 |

Zone 9 minus zone 8 average rounds: -2.575886525 → -1.720833333 (minimum permitted -2.5). All other campaign boss metric rows match the reproduced baseline exactly. Both affected bosses have zero timeouts before and after. Complete resource metrics and winning-round totals are in metrics.json.
Fixed-seed limitation: scrap under-prepared wins are exactly the 25% acceptance floor (15/60); no claim of extra statistical margin or unseen-seed validation. Coarse existing balance multipliers were chosen for gameplay pressure/pacing before the first rerun; there was no seed search or seed-conditioned code.

## Verification and handoff
- Read-only review: repair-only.patch contains exactly two generator entries and three JSON numbers.
- verification.json proves every other enemy field is unchanged and both complete affected rows match generated output.
- preexisting.patch and enemies.before.* preserve the dirty baseline; current file SHA-256 hashes are in verification.json.
- baseline.log and iteration1.log contain the full narrow runs. run_campaign.py loads the existing harness and sets OUT to this folder/build, then passes only CampaignBalance.
- Scope is green. Parent owns the single integrated full-suite run after this handoff; it has not been run here.
