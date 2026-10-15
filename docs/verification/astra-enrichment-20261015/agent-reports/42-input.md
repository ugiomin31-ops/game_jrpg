# 42-input — bounded read-only audit

- Repository: `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`
- Verified branch / HEAD: `codex/astra-enrichment-20261015` / `efdc1517`.
- Requested model / reasoning: `gpt-6-astra` / `high`. Runtime model and effort were not independently exposed by the inspection tools; no model or configuration changes were made.
- Requested service tier: Fast / priority. Actual service tier was **not independently verified**.
- Scope: `UIInput.cs`, `UITouch.cs`, and directly relevant menu/world callers. Static source inspection only; no tests, builds, editor/browser actions, network calls, nested agents, or source changes. Reports 01–07 were searched for overlapping input findings.

## Finding 1 — [P2] Resume confirmation can also trigger a world interaction in the same frame

**Locations:** `Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:553` and `Assets/_Game/Scripts/Runtime/World/TownWorld.cs:308-310`; consumption contract at `Assets/_Game/Scripts/UI/Kit/UIInput.cs:111-112,151`.

The world reads `Keyboard.current.spaceKey.wasPressedThisFrame` / gamepad South directly, bypassing `UIInput.Consume()`. Selecting **계속하기** closes the pause screen immediately (`Assets/_Game/Scripts/UI/Screens/GameUI.cs:263,266`). `UIList` consumes the confirmation before submission (`Assets/_Game/Scripts/UI/Kit/UIList.cs:281-284`), but popping removes the screen from the stack immediately (`Assets/_Game/Scripts/UI/Kit/UIScreen.cs:197-199,212-219`) and invokes its close callback before the exit animation (`UIScreen.cs:94-102`). That callback immediately clears `app.Paused`. Consequently `BlocksWorldInput` / `CanAct` no longer block a world Update later in that frame (`GameUI.cs:16-17`; `DungeonWorld.cs:432,535`). The raw pressed flag remains true despite consumption.

**Repro from source:** In an idle dungeon, open the pause menu, select **계속하기**, release navigation keys, then confirm with Space or gamepad South. If `UIList.Update` executes before `DungeonWorld.Update` that frame, the same press resumes the game and calls `Interact()`. Neither inspected class declares an execution order, so this is an order-dependent reachable path, not a claim that every runtime ordering reproduces it. An empty interaction becomes `WaitTurn()` (`Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:173-184`), spending an unintended dungeon turn. In town, the equivalent order can restart interaction with a nearby facility. Runtime reproduction was not performed under this audit's constraints.

**Integration guidance:** Have world input honor the shared consumed-frame state, or keep world input blocked for the frame that closes the final menu. Merely consuming again in the close callback does not affect the raw device readers.

## Other inspected paths / acceptance

- Keyboard navigation emits an initial pulse, waits 0.36 seconds, then repeats every 0.075 seconds; zero direction clears the held state on refresh (`UIInput.cs:25-28,165-188`). No separate concrete repeat defect established.
- Touch end/cancel clears the tracked finger, and missing fingers are dropped; camera fingers have corresponding cleanup (`UITouch.cs:143-174`). No separate concrete stuck-touch defect established.
- Existing menus block world actions while present. The finding concerns the closing frame, not unrestricted input through an open menu.
- Acceptance: branch/base checked; relevant source paths traced; one concrete finding with exact locations, repro conditions and impact recorded; execution-order and runtime-verification limits stated; requested model/effort and unverified priority tier distinguished; only this assigned report written.
