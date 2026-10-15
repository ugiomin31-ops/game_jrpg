# Astra High audit execution evidence

Verified: **50 unique successful spawns**, **50 matching recorded model/effort observations**, and **50 delivered report files** for assignments 08–57. This does not verify 50 simultaneous inference streams, delivered Fast service, or 50 terminal child-completion events.

Requested model/effort: `gpt-6-astra` / `high`; requested service tier: `priority` (Fast). No agents, tests, builds, gameplay changes or configuration changes were executed by this consolidation task.

## Sources and joins

The four runtime files are under repository-relative `../agent-runtime-50-20261015/`. [concurrency-proof.json](concurrency-proof.json) preserves their byte counts/SHA-256 values, all 50 child IDs, task/report joins, event line anchors, observation record numbers and report hashes. Its UTC timestamp defines the inspected snapshot; later parent activity is not silently folded into it.

| Check | Observed evidence | Meaning |
| --- | --- | --- |
| Successful spawns | `events.jsonl`: 50 completed `spawn_agent` calls, each returning one unique child ID; IDs exactly match `agents.json` | Actual tool results, not configured capacity |
| Task coverage | 50 unique tasks, integers 08 through 57 | No duplicate assignment substituted for a missing task |
| First / 50th spawn | Event lines **14 / 195**, item IDs `item_6` / `item_99` | Recorded event ordering |
| Registered interval | **2026-10-15 12:23:36.016–12:38:05.011 UTC** | Registry timestamps; event entries have no wall-clock timestamps |
| Closure before 50th | No `close_agent`/`close_agents` call in the stream; all 50 registry `closed` flags false; status agrees | No recorded early closure; not proof all children were actively inferring |
| Spawn failures in this run | 0 failed spawn results; 50 complete start/result pairs; empty `spawn_errors` | Separate from transport errors and earlier cap-1 attempt |
| Model/effort observations | 50 unique observation rows, same IDs/tasks, every row `gpt-6-astra` / `high` | Supplied observation file verified; no fresh provider receipt or reread of child turn contexts |
| Priority request / delivery | 50 priority requests; 50 observation `service_tier: null` | Requested; actual serving tier **unverified** |
| Delivered reports | 50 nonempty files, exact task-name match, reports 08–57 | Audit artifact completion; not a test/runtime pass |

## CLI interruption and native-parent recovery

CLI coordinator thread: `01a13f83-6c5f-7712-acdb-b67c8bb9418a`. Reconnect/network errors occur at event lines **197, 213, 214, 215 and 216**, after the 50th successful spawn at line 195. No `turn.completed` record exists in the supplied stream.

`status.json` remains a **launching** snapshot (updated `2026-10-15T12:38:25.731Z`): `spawn_succeeded=50`, `spawn_failed=0`, `active_or_uncollected=50`, `closed=0`, but audit `succeeded=0` and `failed=0`. These are uncollected outcomes, not zero successful spawns or zero delivered reports.

The explicit user handoff states that the native parent **resumed 30 existing audits** to finish reports after the CLI interruption. That count is preserved as handoff evidence. The supplied four runtime files do not contain those native resume calls or their independently recoverable ID list; none is invented. Resumed turns are not new workers: the aggregate remains 50 original spawns, and all 50 final report artifacts are present.

Status also records a Windows command-length persistence problem at 28+ agents, followed by bounded chunk writes retaining all returned IDs. The event-to-registry join confirms no ID was lost. This was not a failed spawn.

## Earlier cap-1 rejection: separate inventory

The pre-update plan documented rejection of a second simultaneous child with **`agent thread limit reached`**, followed by sequential queuing. Preserve this as **one documented historical rejection / effective cap-1 observation**. No raw failure event, original child ID or configured-cap receipt for that attempt is included in the four supplied files. The proof JSON preserves the pre-update plan hash and line 27 as its source.

Do not combine that earlier rejection with this run's zero spawn failures or retain its sequential-only conclusion after 50 actual returned IDs. The later `config_observed.max_concurrent_threads_per_session=50` is supporting metadata; event ordering and returned IDs are the operative evidence.

## Acceptance and limits

- [x] 50 successful results, unique IDs/tasks, model/effort observations and report artifacts reconciled.
- [x] No recorded closure before spawn 50 established from event ordering plus registry/status fields.
- [x] Historical rejection, interruption, native-parent recovery and stale status distinguished.
- [x] 32 finding entries reduced to 31 bounded items by merging reports 50/57; see [audit-index.md](audit-index.md).
- [x] JSON includes all actual child IDs and artifact hashes without reproducing prompts or unrelated logs.
- [ ] Simultaneous inference count: **not independently verified**.
- [ ] Fast/priority served receipt: **not available**.
- [ ] Current game/test/runtime acceptance: **not established by concurrency evidence**.
