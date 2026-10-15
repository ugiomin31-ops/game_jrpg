# 40-battle-target-ui — bounded source audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service tier: Fast/priority. Actual model, effort and service tier are not independently attested by the available tool results; no configuration or routing was changed.
- Verified checkout: `codex/astra-enrichment-20261015`, HEAD/base `efdc1517`.
- Scope: battle target preview/confirmation, allied/enemy candidates, duplicate submissions and disabled choices. Static source inspection only; no tests, builds, editor/browser actions, network requests, nested agents or game changes.
- Consulted reports 01 and 06 and searched available reports 01–07 for overlapping cost/description findings; no duplicate of the finding below was found.

## Finding 1 — P2: skill cost and element disappear at target confirmation

**Location:** `Assets/_Game/Scripts/UI/Battle/BattleHUD.Menu.cs:123-124`, supported by `:59-65`, `:134-137` and `:406-410`.

The skill list displays MP/TP cost in `choice.Right` and element in `choice.ChipText`, but its target callback passes only the skill name and description. `Targets` replaces the header with name plus target rule, replaces the right-hand value with the damage/healing preview, and does not populate an element chip. Although element text exists later in the description, `Focus` explicitly discards everything after the first newline. The cost is not included in that description at all. The description widget is a plain label with ellipsis (`Assets/_Game/Scripts/UI/Battle/BattleHUD.cs:155-157`), so the discarded text cannot be recovered by scrolling.

**Ordinary reproduction path (source-derived, not executed):** enter manual combat with a hunter who has learned 파이어볼 and has at least 6 MP; choose 스킬 → 파이어볼 → an enemy target. The skill list shows MP 6 and 화염, but the confirmation screen shows 파이어볼 · 적 하나 and the target estimate without the cost or element field. First-click preview does not restore either. The shipped skill is defined at `Assets/_Game/Resources/Data/skills.json:46-57` with element 4 and MP cost 6.

**Impact:** players cannot review the pending resource spend or explicit element while choosing/confirming the target; they must cancel back to the skill list. This affects ordinary paid skills, not only long names or extreme inputs. Target selection remains executable; this is a missing decision-context finding, not an assertion of incorrect damage or duplicated expenditure.

## Other inspected paths — no additional concrete finding

- Pointer target confirmation: `BattleHUD.Menu.cs:428-444` arms the target on the first pointer selection and submits on a subsequent selection; changing focus to another target clears the armed ID at `:404`. Card taps resolve only current target choices at `:169-176`. Keyboard confirmation uses the currently previewed choice at `BattleHUD.cs:670-680`.
- Allied/enemy eligibility: `Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs:105-126` uses fallen allies for revival, living allies for other allied actions and living opponents for offensive targets, including provoke restrictions. The HUD builds its choices from this result at `BattleHUD.Menu.cs:120-138`.
- Duplicate actions: `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:192-197` rejects submissions during replay and synchronously locks the HUD/sets `Playing` before engine submission. HUD selection also checks `_input`, pause and the menu-open frame (`BattleHUD.Menu.cs:418`, `:430`). No reachable duplicate action was established.
- Disabled controls: `BattleHUD.Menu.cs:349-350` passes enabled state and reason into the button; keyboard selection checks `choice.Enabled` at `:418-424`. `Assets/_Game/Scripts/UI/Kit/UISlant.cs:479-484` rejects disabled pointer clicks and presents their reason; hover still updates focus at `:534-539`.

## Acceptance

- [x] Original task and scope rechecked after reconnection; original checkout retained.
- [x] Relevant current source lines reread; exactly one concrete reachable finding recorded.
- [x] Requested model/effort and unverified Fast/priority tier distinguished.
- [x] Only this assigned report written; integration and any fixes remain with the main coordinator.
- [x] No runtime reproduction claimed. Visual correctness and timing behavior were not exercised.
