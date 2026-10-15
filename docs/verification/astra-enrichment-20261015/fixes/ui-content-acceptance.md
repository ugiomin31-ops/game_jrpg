# UI/content acceptance — parent execution handoff

Ready source: `Tools/AstraUIContentAcceptance.eval.cs`. This slice writes only that file and this note. `Tools/AstraWorldAcceptance.eval.cs` and production sources are untouched. Requested model/effort: `gpt-6-astra` / `high`; Fast/priority requested where supported, actual routing/tier not independently exposed.

## Requirements / invocation

- Parent owns the shared Unity instance and runs serially, after importing/recompiling the current checkout. This worker did not launch or control Unity, compile, run tests, or generate screenshots.
- Project must be `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`, active scene `Main`, **fresh Play at Title with `GameApp.State == null`**, no active battle, pause, other eval or user input. Stop/start Play after another QA fixture. Do not run against an unsaved live campaign.
- Final handoff order: parent finishes the town fixture and its restoration, then starts fresh Play at Title for this eval. Parent reports CLI `editor_focus` is available: use it to give the Unity Editor actual foreground focus before invoking the eval; the fixture then selects/focuses GameView and checks `Application.isFocused`.
- Use the same Unity Pipeline `eval_file` environment as the world fixture (UnityEngine/System.Linq imports, Editor/TMP/Input/UI/project references). Run:

```text
unity command eval_file --file Tools/AstraUIContentAcceptance.eval.cs --timeout 20000
```

- Parent confirms the inner `eval_file --timeout 20000` option is available. Allow its 20-second compile/evaluation response budget instead of treating the default five-second timeout as a compiler failure; any outer command wrapper must allow that response time. This does not extend or complete the asynchronous acceptance run. If a transport timeout occurs, inspect scheduling/output/BUSY state before retrying to avoid overlapping fixtures.
- The call schedules an async run and returns the output directory. Poll its `DONE` in at most 25-second slices; `result.json` updates at each phase/capture. A successful scheduling response is not completion. Do not stop Play, change files, resize manually or interact while running.
- Outputs: `docs/verification/astra-enrichment-20261015/runtime/ui-content-<UTC timestamp>/result.json`, actual GameView PNGs, isolated `qa-save/`, and `DONE`. Each wait times out in 25 seconds or less; a failed precondition aborts to cleanup. Runtime errors/asserts fail the report.

## Authored acceptance checks

Both **1280×720 and 915×412**:

- Battle: a legal QA level-30 mage retains its actual learned skills, with TP seeded to its legal 100 limit. Real skill-menu buttons enter `Targets`; no fabricated action/cost/element string is passed in. Actual TMP glyph/viewport checks and screenshots require **MP 6 + 화염** for fireball, including another target's first-click preview, and **TP 100 + 화염** for meteor group confirmation. Cancellation preserves combat resources/RNG. Attack does not inherit prior skill cost. A pass-through observer verifies one accepted real fireball submission, one MP payment, and duplicate callback rejection. “SP cost” is interpreted as this game's actual MP/TP labels.
- Settings: real pause → settings menu → battle-speed row submission. The HUD text is checked **synchronously in the settings callback's frame**, before any yield or manual refresh, for 1.5x → 2x → 1x. QA preference persistence and the visible resumed HUD are checked/captured.
- Gear: real authored EXP/gold charms, production `PartyStats.Equip`, and the actual `ShowGear` menu. Capture negative unequip verdicts, **30% → 0% / −30%p EXP**, **25% → 0% / −25%p gold**, and EXP-to-gold tradeoff. Checks include the party gold-cap wording, the unchanged-gear verdict, and real confirmation cancellation with unchanged serialized campaign state. Bonus lines are scrolled into view before glyph checks/captures.
- Rescue: **subway_2 and school_2** represent the long/compact story layouts. A detached QA state starts on each authored event cell; production `DungeonRun.Interact` and `GameApp.HandleDungeonStep` create the real story and reward popup. The complete story is captured across bounded scroll positions; accumulated visible glyph coverage checks every non-whitespace character. Assert actual reward/spent marker and isolated autosave before the story, actual story→loot transition, visible item name and no second reward.
- Postgame: seeded main-story completion and earned joins use the real town-entry notice flow. Capture the complete corrected stair hint through `GameStoryScreen`, then assert return to town and notice-seen flag.

Loaded content contracts, separate from rendered evidence:

- **Exactly 12 frozen expectations** in the eval source compare full title, full text, event cell, `E` map marker, empty battle group, exact gold, one healing potion and no equipment. Regions: subway, E gate, factory, D gate, cave, C gate, school, B gate, hospital, A gate, guild street, S gate. Expected strings were frozen while authoring from the reviewed content changes, not derived from the runtime DB during acceptance. Report entries include expected and actual strings. Also checks 39 floors / 13 total rescues.
- `postgame_unlocked` equals the complete approved string, with `gate_s_3` at index 35, a downward stair, and adjacent `red_gate_1` at index 36.
- `sk_e_mirror_strike` equals **거울 마탄** / **거울에 모은 마력으로 적 하나에게 무속성 마법 피해를 1회 줍니다.**, and retains Damage/Magic/Enemy/Single/None, power 1.5, one hit, MP 6 / TP 0. This is loaded content proof, **not mirror-enemy AI or rendered attack proof**.

## Isolation, restoration and evidence limits

- Reuses the world fixture's BeginReview isolation pattern, async frame waits, private GameView sizing APIs and `ScreenCapture.CaptureScreenshot`/PNG dimension checks without editing it. Current APIs were checked against source: `_plates` are `UISlantButton`s and `_submit` is `Func<BattleCommand,bool>` (the older PR6 fixture has obsolete types).
- Original save repository/directory and preferences are retained. All QA saves/preferences use the per-run project directory. Original directory files are hashed before/after without copying save contents into the report; an unexpected difference fails preservation proof rather than overwriting a concurrent user change.
- No user campaign is adopted or rewritten. Restoring the normal Title UI can read existing save summaries through its ordinary display code.
- `finally` clears QA screens/world, returns to Title, removes the QA state, restores the original repository/directory/preferences, and then restores GameView selection/removes temporary sizes, focus, time scale, frame/background/vSync settings. Restoration is reported separately. A failure before safe routing restoration leaves persistence isolated; parent must stop Play and inspect `result.json`. Do not resume gameplay from a failed fixture.
- Reflection accesses existing runtime components/methods only. Direct widget calls bypass physical pointer hit testing and keyboard/controller delivery; seeded progression/stock/resources/positions do not prove acquisition, balance or traversal. The submit observer delegates unchanged to the original callback and restores it in its own `finally`.
- Only two rescues receive rendered flow coverage; the other ten get exact loaded-content assertions. No portrait support, all-platform support, unknown-weakness audit or mirror battle behavior is claimed.
- File/source hashes, runtime assembly SHA-256 and module ID are recorded, and source stability during the run is checked. These fingerprints identify the evidence; they cannot independently prove Unity compiled all current sources. Parent must ensure compilation before running.
- `visualAccepted` stays **false**. `automated-checks-passed-visual-review-required` means only automated checks completed, including save restoration. Parent must inspect **every PNG** for legibility, clipping, overlap, nonblank content and composition. Glyph bounds alone cannot prove occlusion or visual quality.

## Author-side status

- [x] Current production APIs and world fixture inspected; only assigned source/note authored.
- [x] Static review corrected legacy PR6 delegate/button assumptions, unsupported LINQ default-value overload and Resume floor/location setup.
- [x] `git diff --no-index --check` found no whitespace errors in either new file (Git emitted only its existing LF-to-CRLF normalization warning).
- [ ] Unity eval compilation, execution, actual PNG inspection and final acceptance remain parent-owned. No runtime pass or screenshot evidence is claimed by this authoring slice.

## Compile failure and repair — 2026-10-15

- Parent reported eval compilation failed **before execution** at generated lines 39, 414 and 452: `UIRoot.ReducedMotion` was unavailable to the generated assembly. Parent reports fresh Play at Title remains intact; this worker did not inspect or operate Unity.
- Factual source: `Assets/_Game/Scripts/UI/Kit/UIRoot.cs:24` declares `internal bool ReducedMotion { get; set; }`. The property exists but is inaccessible through a direct reference from the separately compiled eval. The earlier author-side API review missed this visibility boundary.
- Changed only `Tools/AstraUIContentAcceptance.eval.cs` and this note. Resolve that exact property once with instance/public/nonpublic binding flags, check that its type is `bool` with both accessors **before scheduling or mutation**, and use `PropertyInfo.GetValue/SetValue` for all three snapshot/setup/`finally` restoration accesses. The public `GamePreferences.ReducedMotion` field remains directly accessible and unchanged. No production API was exposed or modified; no exception fallback silently skips restoration.
- Additional static source comparison covered `GameApp` lifecycle/persistence properties, `GamePreferences.Read/Apply`, `SaveRepository` constructor/read/directory, `BattleView.Engine/Playing/CanOpenPause`, `BattleHUD` choice/button/delegate fields and paging/back/target methods, `UIList` selection/submission, `UISlantButton`/`UIButton`, modal/story/menu/loot fields and inherited close/stack APIs, and the used game-state/roster/equipment/dungeon/battle entry points. No further mismatch found in those project APIs. Nonpublic `HandleDungeonStep`, `StartBattle` and `ShowGear` already use reflection. GameView/ScreenCapture calls were compared with the current world fixture; Unity Editor private API compatibility remains a runtime requirement.
- This repair is QA-only reflection, not production behavior evidence. Save isolation, finally restoration, content assertions and capture coverage are unchanged. No Unity launch/action, compilation, tests, screenshots or runtime pass performed by this worker. Parent must recompile this eval in its current fresh Title session and execute serially; the previous compile failure provides no rendered acceptance evidence.
- Handoff ready: parent has observed the repaired reflection source and will run after the town fixture. Invocation above incorporates the parent-confirmed focus/timeout capabilities. This is source handoff readiness; compilation, execution, save-restoration proof and PNG acceptance remain pending parent results.

## First runtime diagnosis and bounded fixture repair

Evidence directory: `runtime/ui-content-20261015-144522-441/` relative to this verification directory. Read `result.json`: 385 checks, 373 passed, 12 failed; `issues=[]`, `restored=true`, `bodyCompleted=true`. All four restoration/preservation checks passed, including original save byte hashes. Both battle/settings phases (75 checks each) and all 28 loaded-content checks passed. The failed result is preserved; it is not a visual acceptance pass.

Exact failures (all are `visible glyphs` or accumulated story-glyph visibility assertions):

| Resolution / phase | Failed token or coverage assertion | Count |
| --- | --- | --- |
| 1280 gear / EXP unequip | `획득 경험치 보너스` | 1 |
| 1280 gear / EXP-to-gold comparison | EXP label; gold label including cap; `(+25%p)` | 3 |
| 1280 gear / gold unequip | Gold label including cap; `(-25%p)` | 2 |
| 915 gear / EXP unequip, swap EXP, swap gold, gold unequip | Each corresponding bonus label | 4 |
| 1280 subway story | Full-body coverage: 1 unseen character | 1 |
| 1280 postgame story | Full-body coverage: 2 unseen characters | 1 |

Worker personally inspected all ten PNGs corresponding to these failures: `acc_exp_charm-remove-bonus`, `gear-swap-exp`, `gear-swap-gold`, `acc_gold_charm-remove-bonus` at both sizes, plus `rescue-subway_2-story-page-0-1280x720.png` and `postgame-stair-hint-page-0-1280x720.png`.

- All tested gear labels/deltas are rendered in those images (the 1280 gold delta wraps onto the following line); the subway screenshot contains the complete story. No production text loss is established. The old helper checked full TMP quad corners against an unpadded viewport. Those quads include transparent SDF effect padding, making line-start glyphs and wrapped deltas susceptible to false failures. Existing logs omit failed character indices/bounds, so that precise geometric cause remains to be confirmed by the narrow run. The old parsed string was already one-for-one with `characterInfo`; no raw-rich-text index mismatch was found.
- **Confirmed fixture timing defect:** the 1280 postgame PNG is entirely the cyan `새벽 길드` town-entry card, not evidence of a readable story. `GameApp.EnterTown` constructs notices inside the covered callback (`GameApp.cs:157–164`), before the area card finishes. Finding a story on the stack plus a fixed 0.4-second delay is insufficient. `UIAreaCard.Active` covers the outgoing phase too, unlike `Blocking` (`UIAreaCard.cs:73–76`). No production change is indicated.
- Minimal QA repair is confined to the eval: wait for `!UIAreaCard.Active`, `!Fader.IsBusy` and `!Fader.IsOpaque` before story inspection and captures, and assert the transition remains clear at capture. Use actual TMP character entries (whitespace excluded only by their rendered character), check nonempty font glyph ink bounds using glyph metrics/origin/baseline/scale rather than transparent SDF padding, and keep rendered/alpha/ancestor-mask/full-ink containment checks. Test all four corners, honor mask padding, and retain exact expected strings and all non-whitespace glyphs. Failure details now include glyph/source indices, Unicode character, rejection reason, quad and ink bounds. This is not a token-presence-only relaxation; decorative shadow/glow extents are outside ink coverage and remain for PNG review.
- `NarrowGearStory = true` is currently the default at the top of the same eval file. It runs gear, the two representative rescue flows and the postgame story at **both** sizes, with the same isolation/restoration checks; battle/settings and loaded-content contracts are skipped. `result.json.scope` identifies `gear-story-only`, and its success status is `narrow-checks-passed-visual-review-required`, never a full pass. Run the invocation above now. After narrow passes and its PNGs are inspected, parent sets that single constant to `false`, starts fresh Play at Title, and runs the full fixture **once**.
- Parent reports an old Pipeline `MainThread5000ms` timeout and GraphicsRingBuffer warning with `compilationFailed=false`, and will preserve that console before clearing it for final fixtures. These reports are separate from this run's empty `issues`; clearing old output does not excuse new runtime errors. Worker did not operate Unity, compile, or rerun either mode. Narrow and final broad results remain pending; no new production scope or fix is proposed.
