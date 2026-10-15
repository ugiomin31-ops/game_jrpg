# 32-gear-display — bounded source audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service tier: Fast/priority. Actual model, effort and service tier were not independently exposed by the audit tools; no configuration or model changes were made.
- Verified branch: `codex/astra-enrichment-20261015`.
- Verified HEAD/base: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Scope: `GearDisplay.cs`, its attachment implementation in `CharacterModel.cs`, and direct town/battle callers. Prior source evidence was reused after reconnection.

## Findings

None. The inspected sources did not establish a concrete, reachable defect in hand attachment, duplicate weapon handling, missing-transform handling or orientation. This is a bounded static-review result, not runtime or visual acceptance.

## Evidence and coverage

- **Hand selection:** `Assets/_Game/Scripts/Runtime/World/TownWorld.cs:216` and `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:592` both select `weapon.L` for archers and `weapon.R` otherwise. `Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:146-152` prefers an authored socket and falls back to the matching Humanoid hand.
- **Duplicate weapons / clearing:** `Assets/_Game/Scripts/Runtime/Art/GearDisplay.cs:89-92` delegates attachment and only dresses a non-null result. `Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:212-220` removes the previous attachment's renderer entries, immediately deactivates the old object before deferred destruction, and removes its socket entry. A null prefab clears that socket; a new attachment is registered at line 234. The inspected callers consistently use the same class-derived socket, so no reachable opposite-hand accumulation was established.
- **Missing transforms:** `Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:221-222` returns null for a missing socket; `GearDisplay.cs:90` handles that return. Battle explicitly checks for the socket at `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:593`. Missing required finger transforms return false at `CharacterModel.cs:179`; attachment then uses zero position and identity rotation at lines 227-229. No affected shipped rig was established, so this fallback is not reported as a demonstrated visual defect.
- **Orientation:** `Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:173-194` selects the appropriate hand's finger bones, mirrors the palm normal for the left hand, and converts the derived world grip to hand-local position/rotation. Authored sockets retain identity orientation at lines 224-229. Source inspection alone does not establish how a particular mesh sits in the hand during animation.

## Acceptance checklist

- [x] Confirmed requested branch and base commit.
- [x] Inspected all four assigned concerns and direct attachment callers.
- [x] Reported zero concrete findings; did not promote hypothetical rig/input conditions to defects.
- [x] Used focused local source reads only; no tests, builds, Unity/editor/browser actions, network, nested agents, auth reads or source changes.
- [x] Wrote only this assigned report. Integration and runtime acceptance remain with the main coordinator.
