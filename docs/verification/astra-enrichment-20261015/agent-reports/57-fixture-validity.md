# 57 — Logic fixture validity audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`.
- Requested service tier: Fast/priority. Actual model, effort, and service tier are not independently attested by available runtime metadata; no routing/configuration changes or nested agents were used.
- Verified checkout: `codex/astra-enrichment-20261015`, HEAD `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Method: bounded static inspection of the logic launcher, reflection harness, CI entry point, relevant fixture declarations, and existing reports 01–06. No tests, builds, editor/browser actions, network requests, or source changes.
- Result: **one concrete finding**. Reproduction below is derived from source and was not executed.

## [P2] A misspelled or obsolete test filter succeeds with zero tests

**Location:** `Tools/LogicTests/TestMain.cs:44–58`, particularly the filter at line 48 and success return at line 58.

**Reproduction:** With the normal data/dependencies available, invoke `python Tools/logic_test.py BattleRegressionTests.UnknownCommandCannotSilentlyAttak` (the final `c` in `Attack` is missing). The actual fixture is `UnknownCommandCannotSilentlyAttack` at `Tools/LogicTests/BattleRegressionTests.cs:43–44`; the misspelled filter matches no current fixture.

**Trace:** Discovery selects static methods marked `[LogicTest]`, applies a case-insensitive substring filter, and materializes the list (`TestMain.cs:45–49`). With no matches, the loop does not execute, `fail` remains zero, the summary is `0/0 passed`, and the process returns 0 (`:50–58`). Both launcher paths propagate that success (`Tools/logic_test.py:54,85–86`).

**Impact:** A focused verification command can report process success without exercising the intended regression after a typo or test rename. Any caller using exit status alone accepts this false positive. The current CI workflow uses no filter, so this example does not establish that its existing full-suite invocation omits tests.

**Suggested correction for the coordinator:** Treat zero discovered/selected tests as a nonzero exit and print the supplied filter. No correction was applied here.

## Discovery and rebuild observations

- Source collection includes all recursive `.cs` files under both `Assets/_Game/Scripts/Logic` and `Tools/LogicTests` (`Tools/logic_test.py:41–49,61–62`). Reflection discovers attributed static public and nonpublic methods, without a manually maintained fixture list (`TestMain.cs:45–49`).
- The Unity/Mono launcher compiles those sources on every invocation and exits on a nonzero compiler result before launching the executable (`Tools/logic_test.py:69–85`). There is no fallback to an older executable after a failed compilation in this path.
- The portable path writes the project with those source globs and calls `dotnet run` without `--no-build` (`Tools/logic_test.py:39–54`). It requests the normal build-before-run behavior, which may use up-to-date incremental outputs; it does not deliberately bypass building.
- CI calls the launcher (`.github/workflows/logic-check.yml:17–18`), and the handoff also documents it (`HANDOFF_20261015.md:54`). No stale-binary defect was established in those entry points.
- Existing `06-auto-battle.md` explicitly reports directly running `Temp/LogicTests/LogicTests.exe` without a rebuild and without establishing binary/source correspondence. Those recorded passes cannot verify current source changes. This is a limitation of that earlier evidence, not proof that its binary was stale or that its tests falsely passed; this audit did not execute or inspect the binary.
- No second concrete reachable discovery/rebuild defect was established within this scope.

## Acceptance

- [x] Checked test discovery, filtering, return status, and both compile/run paths.
- [x] Recorded one finding with exact source lines, reproducible input, and impact.
- [x] Distinguished requested routing/tier from independently verified metadata.
- [x] No tests/builds/nested agents or prohibited application actions performed.
- [x] Only this assigned report was written; game fixes and integration remain with the coordinator.
