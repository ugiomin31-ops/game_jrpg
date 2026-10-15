# Executable animation regression eval

Prepared `Tools/AstraAnimationRegression.eval.cs` in Unity Pipeline statement/local-function format matching `Tools/TripoBattleAcceptance.eval.cs`. No NUnit/test assembly required. Requested model/effort: `gpt-6-astra` / `high`; priority tier not independently verified.

Parent invocation, serially after the editor has compiled the owned production changes and entered Play mode:

```text
eval_file --file Tools/AstraAnimationRegression.eval.cs
```

Returns synchronous JSON with `status`, boolean `error`, `completedCases`, `completedEntryCases`, `skippedCases`, named assertion `checks`, and exceptions/Unity error logs in `issues`. Preserve the returned JSON as execution evidence. Success requires `error: false`, `status: passed`, `completedCases: 11`, `completedEntryCases: 8`, no skipped cases, and every check passing. No background task, polling, scene change, save read/write, network request or production setting mutation.

Play mode is the only prerequisite for the eight entry cases and manual graph-output case: they run independently of death-frame eligibility or earlier assertion failures. Only the two death cases require an actual unscaled delta of 0.001–0.1 seconds (inclusive). Outside that range their names appear in `skippedCases`, `error` stays true, and the nine independent case results are retained. The lower bound keeps the real nested HitStop.Wait within its existing 32-step cap.

Slow-frame revision: parent reported the first attempt in `animation-eval-result.json` stopped before any cases because delta was 0.0639047, above the old 0.05 bound. That observed delta now qualifies. QA's `Application.targetFrameRate = 20` is left unchanged; no temporary 60-fps setting, frame wait, timeScale change or substituted Time delta is used. The worker has not executed the revised fixture.

- Eight original fixture cases: five incoming/seam reserve cases (1x/2x/paused global rate, independent 1.6x clip rate, zero incoming fade), explicit offset preservation, uncorrected loop phase and distinct unit phases.
- One real PlayableGraph check: a generated in-memory Transform curve must change the actual child Transform and clip time; speed zero must freeze both. Uses real CharacterModel.Setup and ClipAnimator; no copied implementation or stubs.
- Two death cases at 1x/2x: call real private HitStop and DeathRoutine iterators through reflection on temporary runtime objects. Check elapsed time, root, dissolve and skeletal time remain frozen during hitstop, then advance after its actual nested Wait completes. Also check Reduced Motion retains the current clip at zero DeathRate, advances dissolve, and remains frozen after real HitStop speed restoration.

Each death case reads the real BattleView.Dt getter and the production DeathDissolveAt/ReducedDeathDissolve constants through reflection. At the 0.1-second maximum, 2x yields one actual 0.2-second step, before normal VFX at 0.3 and reduced fade completion at 0.25. Only one unpaused step is advanced per normal/reduced routine, with exact actual-clock assertions and a check that no completion/VFX beat was crossed. Three frozen probes still run; if any probe advances, the case fails immediately before a second broken step could enter VFX. The existing real seven-second Die clip remains long enough for these graph probes. No production timings or coroutine elapsed state are rewritten.

The temporary GameApp remains inactive for its entire lifetime, so Awake does not initialize persistence/UI or replace the live singleton. Only its own preference backing field is populated. The temporary BattleView never calls Initialize or drives the real battle; its director uses a temporary inactive camera. All iterators are disposed and all temporary GameObjects (including their real playable graphs) and AnimationClips are destroyed in finally; JSON also checks cleanup and unchanged production singleton.

Limits: compiler-generated DeathRoutine elapsed-field reflection is deliberately checked and fails explicitly if its name changes. Coroutine steps and graph evaluations are bounded and manually driven on Unity's thread; this proves actual method/graph behavior, not PlayerLoop ordering, LateUpdate integration, rendered mesh quality, full encounter completion or revive flow. Existing bounded game recipes still cover those. This eval does not alter production sources or add a fake Unity harness.

Preparation verification only: focused source review and whitespace check. **No Unity invocation, compilation or test execution performed by this worker.** Parent owns the focused retry and acceptance. Only this note and the assigned eval file were written; the parent's saved failed result was not modified.
