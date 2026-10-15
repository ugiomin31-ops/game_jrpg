# 56-package-consistency

- Scope: bounded, read-only Unity package and Editor dependency audit; only this report was written.
- Checkout verified: `codex/astra-enrichment-20261015`, HEAD/base `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- Requested execution: `gpt-6-astra`, reasoning `high`, Fast/priority. Actual model/effort and service tier are not independently exposed by the tools used; priority is requested, not verified. No configuration or model changes, nested agents, or relay access.
- Method: local JSON inspection, focused source searches and reads. No installs, tests, builds, Unity/editor/browser actions, network requests, Library scans, or authentication reads.

## Finding (1)

### P3 — Newtonsoft direct dependency and checked-in lock disagree

**Locations:** `Packages/manifest.json:40`; `Packages/packages-lock.json:73-75`.

The manifest directly declares `com.unity.nuget.newtonsoft-json` at `3.2.1`, but the lock records `3.2.2` with `depth: 1` (an indirect dependency). This is the only direct-dependency version/depth mismatch: the other 42 direct entries match. The lock's only incoming dependency for Newtonsoft is `com.unity.pipeline` requesting `3.0.2` at `Packages/packages-lock.json:90`, which does not explain the differing direct declaration. The dependency is used by the game's save codec (`Assets/_Game/Scripts/Logic/Game/SaveCodec.cs:6-9`).

**Static reproduction:** read `dependencies["com.unity.nuget.newtonsoft-json"]` in the manifest, then the corresponding lock object's `version` and `depth`: results are `3.2.1` versus `3.2.2` / `1`. This mismatch exists in the current checkout without modifying any input.

**Impact:** the committed lock does not faithfully describe the manifest's dependency graph, so it cannot serve as consistent evidence of the intended save-serialization package version. A normal Unity package-resolution pass needs to reconcile this entry. No runtime serialization failure or package-resolution failure was demonstrated or claimed.

**Coordinator action:** confirm the intended Newtonsoft version, then reconcile manifest and lock using the pinned Editor. No fix was applied in this audit.

## Completed checks and limits

- [x] Both JSON documents parse; 43 direct dependencies and 55 lock entries inspected.
- [x] Every direct dependency has a lock entry; every lock dependency edge targets an existing lock entry.
- [x] No `file:` dependencies or local/embedded/git lock sources; `Packages` contains only manifest and lock. No missing required local package identified within this scope.
- [x] Editor pin read: `ProjectSettings/ProjectVersion.txt:1-2` specifies `6000.3.25f1` (`e1dba0a9aba4`). Actual installed Editor compatibility was not exercised.
- [x] Reviewed dependency imports and package references in `Assets/_Game/Scripts/Editor/AbyssProjectSetup.cs`, `AbyssFontSetup.cs`, and `AbyssArtImporter.cs`; inspected relevant runtime imports and assembly-definition filenames. No second concrete missing Editor/package dependency identified. A UniVRM comment alone was not treated as proof of a required missing package.
- [x] Consulted available reports 01–06 with package-focused searches for duplicate findings; report 07 was absent from the matching file list.
- [x] No game/source/configuration changes; integration remains with the main coordinator.

This is static package-consistency evidence, not proof that package download, Editor import, compilation, or runtime execution succeeds.
