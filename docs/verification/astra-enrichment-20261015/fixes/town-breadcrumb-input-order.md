# Town breadcrumbs, input order and enrichment hookup

2026-10-15, approved plan `plan/2026-10-15-astra-enrichment.md`. Requested model/effort: `gpt-6-astra` / `high`; Fast/priority requested. Actual model, effort and service tier were not independently attested by the available tool results. No configuration changes or nested agents.

This follow-up addresses both findings in `reviews/world-input.md` and supersedes the direct-pursuit limitation and roster-reset description in `fixes/town-input-motion.md`. Existing pending-talk, consumed-input, follower collision and sale-limit repairs are preserved. Only the two sources below and this note were edited in this follow-up; no helper, art, layout, generator or acceptance-fixture edits.

## Changes

- `Assets/_Game/Scripts/Runtime/World/TownWorld.cs:30`: each follower owns a 256-point ring containing the actual post-`CharacterController.Move` positions of the member immediately ahead. The first follower records the leader; subsequent followers record their predecessor. Forward collinear segments merge, while turns and reversals remain queued. No unvisited point is overwritten. Each ring's Vector3 storage is 3 KiB (9 KiB for three followers), plus fixed bookkeeping.
- `TownWorld.cs:418,435`: leader movement is subdivided into at most 0.1 m requested horizontal steps; followers visit queued points in order through their existing collision controllers. Delta time is capped at 0.1 s; leader sweeps and follower path iterations are each capped at 32 per frame. Followers retain about 0.95 m of route distance, accept arrival within 0.015 m, and continue catching up after the leader stops. Facing/Walk/Run/Idle use actual horizontal displacement. Gravity still applies at rest and is the last follower sweep, preserving grounded feedback.
- `TownWorld.cs:405,451`: when a downstream ring fills, its predecessor waits rather than losing a corner or teleporting. Near capacity, the retained spacing gradually shrinks to allow the ring to drain. This is bounded backpressure: unusually dense paths can temporarily slow the party, rather than consume unbounded memory.
- `TownWorld.cs:159,202,233,259`: roster changes preserve each occupied spatial slot's position, rotation and unvisited trail; outfit replacement reuses that slot's trail with its replacement controller. Removed slots release their state; new members start at the preceding member's current safe position instead of an invented offset through an obstacle. Initial town formation retains its authored spawn behavior. Pairwise collision ignores are rebuilt for the live controllers.
- `TownWorld.cs:481,489`: ordinary movement, menu pauses and position-preserving replacements retain the trails. An externally changed member position more than 0.1 m from the last controlled position invalidates the old route; reset seeds current predecessor positions and clears vertical velocity without moving any member. There is no catch-up warp.
- `Assets/_Game/Scripts/UI/Screens/GameUI.cs:13`: `[DefaultExecutionOrder(-100)]` runs global pause/map keyboard handling before default-order town/dungeon `Update`. The inspected three script `.meta` files have no order override. `ShowPause` and `OpenMapFromHud` consume and block movement before raw world polling, covering held W plus Tab/Escape (both worlds) or M (dungeon). No change to public dungeon actions: HUD `PadAction` still consumes before invoking them. This does not impose a new ordering on EventSystem pointer callbacks.
- `TownWorld.cs:111`: `TownEnrichment.Apply(town)` now runs immediately before `EnvironmentProcessor.Process`, also before camera collection. The other worker's public helper signature/namespace were read and match the call. The helper, tree coordinates and station art were not edited here. The parent must supply the approved Resources asset at `Art/Props/GuildFieldStation/guild_field_gear_station` before town initialization.

## Parent fixture hooks and pending checks

No new public test API is needed. Reflection can invoke the following private production methods with a minimal party/controller fixture:

- `MoveLeader(Vector3 motion, float speed, float dt)` returns actual horizontal displacement and records each successful sweep.
- `UpdateFollowers(float speed, bool running, float dt)` advances the chain independently of camera/UI setup.
- `CheckFollowerTrails()` detects external relocation; `ResetFollowerTrails()` reseeds explicitly.
- Nested `FollowTrail.Reset(Vector3)`, `Append(Vector3)` and `Arrive()`, with `Count`, `Length`, `First`, `Last` and `Capacity`, allow deterministic ring-bound, turn/reversal and distance-accounting checks. Runtime state is available through `followers[i].Trail`, `followers[i].LastPosition` and `lastLeaderPosition`.
- `RefreshRoster()` / `RefreshJobModels()` exercise actual replacement lifecycle; GameUI's execution-order attribute can be inspected independently.

Pending acceptance scenarios for the parent (not executed here):

1. Four-member party, ground plus the 3.4 m square fountain collider: lead around tight corners clockwise and counterclockwise, then stop beyond the obstacle. All followers must finish the recorded route to the retained spacing without penetrating the obstacle or warping. Repeat around bench/cart ends, on steps, walking/running, and reversing direction.
2. Zero delta must not translate members; slow motion and low-frame-rate input must remain bounded. Fill a ring with turns/reversals: count stays at or below 256, no pending corner disappears, upstream movement waits when full and resumes as followers consume points. Straight slow movement should coalesce; inspect approximate route spacing after catch-up.
3. With a corner still queued, replace/reorder hunters and change leader/follower outfits. Retained slots keep their positions and queued turns; added/removed slots have correct controllers and no stale-body exceptions. Relocate the whole party into a valid formation: old trails reset once, and subsequent normal movement preserves the new trail. Pause/NPC-delay frames stop motion/animation; resume retains the route.
4. In town and dungeon hold W and open pause with Tab/Escape; in dungeon also open map with M. Opening-frame position/facing and dungeon turn count must not advance. Closing-frame consumption still blocks raw input. Each HUD move/turn/interact/wait button still executes its requested public action once after consuming input. Include gamepad menu and reduced-motion modes.
5. After the parent installs the FBX, initialize title and town: enrichment applies before collider processing/camera collection. The environment worker/parent owns checking station placement and corrected tree collision against the actual imported asset.

## Verification and limits

Focused source/diff/call-site inspection and scoped `git diff --check` passed. No tests, fixture execution, source compilation, Unity, browser or builds were run, and `Tools/AstraWorldAcceptance` was not touched. Parent owns serial compilation, runtime fixtures, independent review and final acceptance; no runtime-pass claim is made here.

This follows recorded traversable routes through static town geometry; it is not general navigation around an obstacle introduced after recording. External teleporting only the leader across a wall cannot supply missing traversable history: relocation callers must provide a valid party formation. The code discards stale history without warping followers or disabling collisions. Full-buffer slowdown and close-spacing recovery need the pending runtime checks above.
