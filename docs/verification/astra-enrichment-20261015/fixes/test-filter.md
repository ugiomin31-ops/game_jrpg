# Report 57 fix — Reject an empty test selection

- Requested model/effort: `gpt-6-astra` / `high`; runtime routing and service tier are not independently attested. No model/configuration changes or nested agents.
- Changed only `Tools/LogicTests/TestMain.cs` and this note.
- After discovery and filtering, a zero-count selection now writes an error to stderr containing the supplied filter in quotes and returns exit code `2`. The message explains that an empty filter selects all discovered tests, so an empty discovered suite also fails instead of reporting `0/0 passed`.
- Case-insensitive substring matching, ordering, test invocation, ordinary pass/fail summaries, success exit `0`, and assertion-failure exit `1` remain unchanged for nonempty selections.
- Static verification: inspected the patch and checked its whitespace with `git diff --check`. No compiler, tests, builds, or new test fixtures were executed or added.
- Parent verification pending: run an intentionally missing filter and require the filter-bearing error plus exit `2`; then run a real focused suite and the full suite. This note does not claim runtime verification.
