# 50-validation-infrastructure — bounded read-only audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`; requested service tier: Fast/priority where supported.
- Observed routing: the available session/tool metadata does not independently attest model, effort, or server service tier. Requested priority is not verified priority. No model/configuration changes or nested agents were invoked.
- Repository: `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`.
- Observed branch: `codex/astra-enrichment-20261015`; HEAD: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c` (matches requested base).
- Method: focused source/document/log reads only. No test, build, Unity/editor/browser action, network request, Library scan, secret read, or game-source edit. Commands below are instructions for the coordinator, not commands executed by this audit.
- Result: **one concrete validation finding**, established statically; no runtime reproduction claimed.

## Finding 1 — P2: a nonmatching test filter reports success without testing anything

- Location: `Tools/LogicTests/TestMain.cs:44-58`, especially filter selection at lines 48-49 and unconditional zero-failure success at lines 57-58. `Tools/logic_test.py:54` and `:85-86` propagate that exit code.
- Reachable reproduction, once the documented compiler prerequisites are available: run `python Tools/logic_test.py BreakRecoveryTests.cs`. This is an ordinary filename-style filter a caller can copy from the test file; the harness actually matches `Class.Method` strings. The two methods in `Tools/LogicTests/BreakRecoveryTests.cs:40,55` are `LethalPoisonDoesNotRecoverBreak` and `SurvivingPoisonStillRecoversBreak`, so neither matches the filename filter.
- Source-determined outcome: the test list is empty, `fail` remains zero, output is `0/0 passed`, and exit status is 0. A typo or filename-based targeted rerun can therefore falsely satisfy an automated success gate while skipping the intended regression.
- Coordinator remediation: reject an empty selection with a nonzero exit and print the unmatched filter; preserve the existing case-insensitive substring behavior for valid filters. No fix applied here.

## Exact available entry points and prerequisites

Run from the repository root. Availability below means implemented/documented entry point, not a verified installed executable or a successful run on this host.

| Purpose | Exact command or action | Contract / source |
|---|---|---|
| Complete engine-free regression | `python Tools/logic_test.py` | Compiles all Logic and LogicTests C# sources; loads real JSON through `ABYSS_DATA_DIR`. `Tools/logic_test.py:41-54,61-86`. |
| Narrow break recovery regression | `python Tools/logic_test.py BreakRecoveryTests` | First positional argument is a case-insensitive substring of `Class.Method`; additional arguments do not add filters. `Tools/LogicTests/TestMain.cs:44-49`. |
| Single regression | `python Tools/logic_test.py BreakRecoveryTests.LethalPoisonDoesNotRecoverBreak` | Exact known class/method name at `Tools/LogicTests/BreakRecoveryTests.cs:40`. |
| Connected-editor compile check | `python Tools/unity_check.py --project-path "C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015" --warnings` | Requires `unity` CLI on PATH and the intended connected editor. Clears console, requests recompile, waits for status, then requires compilation ground truth. `Tools/unity_check.py:17-58`. |
| Existing console verdict only | `python Tools/unity_check.py --project-path "C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015" --no-recompile --warnings` | Does not establish that current sources were recompiled. Warnings print but do not alone fail; compilation failure, console error entries or ground-truth console error count do fail. `Tools/unity_check.py:36,59-68`. |
| Floor-one runtime QA | `powershell -ExecutionPolicy Bypass -File Tools/run_floor1.ps1` | Optional `-KeepPlaying`; requires connected Pipeline editor. Opens Main, starts Play and executes `Tools/Floor1Playthrough.eval.cs`; writes `docs/verification/floor1/`. This is a state-changing runtime operation, not a read-only checker. |
| Imported-asset acceptance | `unity command eval_file --file Tools/TripoEnrichmentAcceptance.eval.cs` | Documented in `Tools/TripoEnrichmentAcceptance.md:8-36`: populate explicit manifest, prepare idle Play session, wait for DONE, read checks and visually inspect PNGs. Technical pass explicitly still requires visual review. |
| Manual game run | Open `Assets/_Game/Scenes/Main.unity`, then Play | `README.md`, source run/build instructions: Unity 6000.3.25f1, `Abyss > Prepare Game`, `Abyss > Validate Production Content`. Windows player target is `Build/Windows/AbyssLabyrinth.exe`; binary availability was not checked. |

Compiler paths: `Tools/logic_test.py:16-19` defaults to `C:\Program Files\Unity 6000.3.25f1\Editor\Data`, overridable with `ABYSS_UNITY_DATA`. Its Unity path also invokes `dotnet` to run Roslyn and Mono to execute tests (`:70,85`). If Roslyn or Mono is missing, it creates a net8.0 project and uses .NET SDK 8+ with Newtonsoft.Json 13.0.3 (`:33-59`); package restoration may require network/cache. This audit did not inspect installed tools or resolve dependencies.

Historical portable command in PowerShell syntax, for a coordinator-authorized future run only:

```powershell
$env:ABYSS_UNITY_DATA = '__portable_dotnet__'
python Tools/logic_test.py
```

This changes the invoking shell environment and deliberately chooses the portable path. It is not needed when the default Unity compiler path is valid; no such environment change was made here.

## Prior verification evidence and limits

- `docs/verification/tripo-enrichment-20261015/portable-logic-result.json:2-9` records **259/259, exit 0**, .NET SDK 8.0.426, at **d924ec40bd9ba8bfa4ff95aeccc35d5128741fe6**. This is historical evidence for that checkpoint, not a fresh result for current dirty files/HEAD.
- `docs/verification/tripo-enrichment-20261015/HANDOFF_VERIFICATION.md:25,29,39` distinguishes the portable run from fresh Unity import/Play and leaves new-model integration, full campaign visuals and actual Android verification outstanding.
- Current audit-folder `baseline-logic.log:5` records **No .NET SDKs were found**. `baseline-unity-compiler.log:1-48` records missing Newtonsoft types and `:49` says **BUILD FAILED**. These are failed attempts, not passing baselines; no inference is made that their original environment failure still exists.
- `docs/verification/astra-enrichment-20261015/break-recovery-before.log:1-7` records 1/2 with the lethal-poison failure; `break-recovery-after.log:1-3` records 2/2. This later narrow evidence neither erases the baseline failures nor proves a full-suite/current-editor pass.
- `docs/verification/tripo-motion-20261015/README.md:19-29` documents earlier 259/259 logic and Unity runtime checks, plus zero final console errors/warnings. Its `:63` explicitly excludes actual Android touch and full campaign visual coverage. These are prior report claims inspected here, not independently rerun results.
- Logic compilation covers `Assets/_Game/Scripts/Logic` and `Tools/LogicTests`, not Runtime/UI/Presentation; `unity_check.py` proves a compilation/console verdict, not playable interaction, rendering, asset skinning or visual acceptance.
- Focused report lookup found 01-06; 07 was absent at inspection. The command-validation report did not overlap this test-selection defect.

## Baseline screenshot inventory

Existing files were located; this audit did not open images, validate pixels/dimensions, or capture new screens. Sizes below are filename labels, not newly measured dimensions.

| Historical context | Existing project-relative files |
|---|---|
| Title / guild | `docs/verification/floor1/01_title.png`, `docs/verification/floor1/02_town.png` |
| Town compact / tablet | `docs/verification/town-915x412.png`, `docs/verification/town-1024x768.png` |
| Battle command selection | `docs/verification/tripo-motion-20261015/battle-1280x720.png`, `docs/verification/tripo-motion-20261015/battle-915x412.png` |
| Battle overall framing | `docs/verification/tripo-motion-20261015/overview-1280x720.png`, `docs/verification/tripo-motion-20261015/overview-915x412.png` |
| Arrow speed comparison | `docs/verification/tripo-motion-20261015/arrow-1x.png`, `docs/verification/tripo-motion-20261015/arrow-2x.png` |

`docs/verification/tripo-motion-20261015/README.md:31-39` links these battle captures and the prior visual-review/source-hash records. `docs/UNITY_ASSET_REVIEW.md:7` identifies its older PR context and excludes an obsolete preview. No top-level PNG was present in `docs/verification/astra-enrichment-20261015` at inspection; a same-build, matched-resolution title/guild/roster/battle baseline for current changes is therefore **not established by this bounded audit**. No roster screenshot was located in the focused inventories; absence elsewhere is not asserted. Current visual acceptance remains the coordinator's task.

## Acceptance checklist

- [x] Checked requested branch/base without changing Git state.
- [x] Read both assigned scripts, the directly related test harness and targeted prior verification records.
- [x] Recorded exact commands, prerequisites, evidence limits and baseline screenshot paths.
- [x] Reported one concrete reachable finding with exact lines, reproduction and impact; no speculative second finding.
- [x] Distinguished requested Astra/high/Fast metadata from independently verified routing/tier.
- [x] No tests/builds/editor/browser/network/configuration/source changes or nested agents; only this assigned report written.
