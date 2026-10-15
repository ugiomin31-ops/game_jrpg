# 31 — ArtLibrary bounded read-only audit

- Requested model: `gpt-6-astra`; requested reasoning effort: `high`; requested service tier: Fast/priority.
- Observed model/effort/tier: this session exposes no independently verifiable serving metadata. Requested settings are not asserted as verified. No model or configuration changes and no child agents.
- Verified repository: branch `codex/astra-enrichment-20261015`, HEAD `efdc1517`.
- Result: **0 concrete reachable findings established** within the inspected scope.

## Evidence and disposition

- `Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:28–33,58–62`: prefab lookup caches successful loads; hero lookup explicitly tries the hero, then supplied job, then base class. Inspected character filenames include the 20 individual hunter models and four base class models. Missing optional job outfits therefore do not establish a reachable missing-model failure for these hunters. Base-class resolution was checked at `Assets/_Game/Scripts/Logic/Data/GameData.cs:435–436`.
- `Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:88–94,116–138`: enemy variants resolve their model before selecting animation exceptions; humanoid models without an Idle take use shared/class/hero layers. `:163–185` overlays class then hero by clip name; `:285–293` keeps authored model takes ahead of supplemental moves. Inspected shared/class/hero filenames are consistent with these resource paths; this is source evidence, not proof of imported clip contents.
- Intentional disablement is not a defect: `Assets/_Game/Resources/Art/Enemies/bat/bat.fbx.meta:306,325` disables animation import and the rig despite retained legacy clip settings. `Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:120,266` explicitly permits this model's rigless flyer route, and `Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:69–78` installs its dedicated animator. The explicit blob/crawler exception lists and corresponding setup branches were also inspected. No runtime mesh/rig correctness claim is made.
- `Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:105,306` intentionally throws for absent required character/static art rather than silently substituting geometry. `Assets/_Game/Scripts/Runtime/Art/GearDisplay.cs:68–74` similarly rejects missing equipped weapon art. No concrete normal-flow missing resource was established by the focused reads; this was not an exhaustive asset inventory.

## Acceptance / limits

- [x] Focused source/resource filename/import-metadata reads, restricted to the assigned workspace; branch/base checked.
- [x] At most two reachable findings; none reported without sufficient evidence.
- [x] No nested agents, tests, builds, editor/browser execution, network, source fixes, binary/configuration changes, authentication reads, or conversation-history reads.
- [x] Only this assigned report written.
- Runtime Resources resolution, imported Avatar/skin weights and rendered animation remain unverified because application execution and Library inspection were excluded by the audit authorization.
