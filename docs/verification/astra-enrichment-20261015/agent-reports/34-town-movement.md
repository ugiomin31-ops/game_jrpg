# 34-town-movement — bounded read-only audit

- Scope: TownWorld.cs player locomotion, facing, NPC interaction and natural motion; environment art excluded.
- Verified checkout: `codex/astra-enrichment-20261015`, HEAD/base `efdc1517`.
- Requested model: `gpt-6-astra`; requested reasoning effort: `high`; requested service tier: Fast/priority. Actual model, effort and service tier were not independently exposed/verified by the audit tools. No model or configuration changes were made.
- Method: focused source reads only. No runtime reproduction, tests, builds, Unity/editor/browser actions, network requests or nested agents. Reports 01–07 were searched for overlapping town/movement findings; no match found.

## Finding 1 — P2: Followers retain locomotion animation while NPC interaction stops their movement

**Primary location:** `Assets/_Game/Scripts/Runtime/World/TownWorld.cs:262–270` (especially lines 262 and 267).

When world input is blocked or `pendingTalk` is active, `Update()` sets only `party[0]` to Idle and returns before updating the followers. Moving followers were last assigned Walk/Run at `TownWorld.cs:298–302`; their transforms stop updating, but their animation state is never changed to Idle. `CharacterModel.cs:332` delegates Play without an automatic return clip, while `ClipAnimator.cs:171–173,193–196,209–237` keeps the selected animation active independently of TownWorld movement. The playable graph uses game time (`ClipAnimator.cs:107`). Starting an NPC interaction does not pause game time: `TownWorld.cs:318–321` schedules a normal 0.8-second pending interval, and `GameApp.cs:194–198` opens the service directly.

**Reachable repro (source-derived; not executed):** With at least two active hunters and reduced motion off, walk or run toward a facility NPC until a follower is moving. While still moving within the 3.2-unit interaction radius (`TownWorld.cs:412–418`), press E/Space/gamepad confirm. The interaction runs after the follower movement loop (`TownWorld.cs:307–310`). On subsequent frames, the leader changes to Idle but the moving follower retains Walk/Run at a fixed position throughout the pending conversation interval; the same omission applies when the facility UI blocks world input.

**Impact:** Party members visibly walk/run in place during the conversation transition and blocked facility view, breaking the expected natural stop behavior. This is a normal town-interaction path, without extreme input requirements.

## Acceptance checklist

- [x] Requested branch/base checked.
- [x] Locomotion, facing, NPC interaction and natural-motion branches inspected.
- [x] One concrete reachable finding with exact source lines, repro and impact; no speculative second finding.
- [x] Runtime verification limitation and requested-versus-verified execution metadata stated.
- [x] Only this assigned report written; no game fixes or other mutations performed.
