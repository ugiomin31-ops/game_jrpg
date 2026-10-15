# Tripo enrichment acceptance (parent-run only)

This external Unity Pipeline eval is not player code. Its implementation has been
reviewed statically only; no new Unity execution, asset import, screenshot or test
result is claimed. Requested worker routing: GPT-6 Astra / high / priority; this is
request metadata, not an attestation of the actual model route.

1. After the parent imports the approved assets, populate `Manifest` in
   `Tools/TripoEnrichmentAcceptance.eval.cs`. Each tuple is
   `(Kind, Id, ResourcePath, Motions, MinTriangles, MaxTriangles)`.
   Kinds: `Character`, `Monster`, `SkillMotion`, `Prop`.
   Paths are extensionless, relative to Resources. SkillMotion rows identify the
   character model that consumes the take, not a standalone animation FBX.
   Animated rows require exact named takes exposed by production ArtLibrary;
   props require `new string[0]`. Empty manifest **fails**.
2. Choose asset-specific triangle budgets: small enemy/prop 3000–6000;
   normal enemy/NPC 6000–10000; hero/elite/boss 10000–20000. Counts include
   every mesh/LOD in the hierarchy; the hard ceiling is 20000. No auto-discovery,
   importer changes or automatic exemptions are performed.
3. Parent prepares an idle Play session, no other QA running, layer 31 unused by
   unrelated renderers. Use a fresh Play session after import to avoid stale
   ArtLibrary clip caches. Mesh weight/bake access must be available; errors fail
   the run instead of changing import settings. The script never starts Play.
4. From the project root run:

   ```text
   unity command eval_file --file Tools/TripoEnrichmentAcceptance.eval.cs
   ```

5. Poll the returned directory's `DONE` in slices no longer than 25 seconds.
   The script yields to the Unity synchronization context; each frame wait has
   a 20-second deadline. Do not invoke another copy while one is running.
   Missing `DONE`, an eval error or an output/lock error is not success.
6. Read `checks.json` and Unity console/player log, then inspect every generated
   PNG. `ENRICHMENT_FAIL` rejects the run. The only passing technical status is
   `ENRICHMENT_PASS_VISUAL_REVIEW_REQUIRED`; it is never visual approval.
   Stop Play after review before normal gameplay.

The checks cover explicit Resources loading and production prefab identity;
source and instance mesh/submesh/material/shader validation; finite nonzero
bounds and declared triangle limits; complete normalized per-vertex weights,
bone indices, clone-local bones and finite bindposes. Every valid skin receives
a synchronous weighted-bone translation probe restored in `finally`. Each named
take is sampled through production `ClipAnimator.PlayFrom` at 0, .15, .30, .50,
.70 and .90, with `BakeMesh` comparisons in renderer-local space. Vertex-count
changes or nonfinite vertices fail. At least one skin must change for each take;
all skins must pass weight and bone-probe checks. This samples poses, not full
continuous playback or gameplay integration; a deliberately static take fails
the deformation gate and needs explicit parent review.

Evidence is under `.git/codex-runs/20261015-enrichment/acceptance-<UTC>/`.
No player save, scene asset, importer or shared material is written. When the
parent runs it, the harness does create temporary runtime clones, cameras,
meshes and textures; it changes clone layers/poses only and schedules cleanup.
Cloned prefab scripts may execute normally, so use trusted imported art in an
idle session. PNG lighting uses the current scene; framing/nonblank pixels are
not automatically accepted. This does not verify original Tripo credit usage,
Blender export acceptance, texture resolution, art quality or battle integration.
