# GPT-6 Pro code review — claude/motion-polish-pr9 vs claude/visual-overhaul-pr8

Source: chatgpt.com (Claude desktop built-in browser), GPT-6 Pro, 2026-10-15, about 31 minutes of processing. The reviewer read the public repo over the web; findings are code-reading results, not Unity runs. Prompt: strict correctness review of the 18 changed scripts in this branch, severity-sorted with minimal fixes.

Reviewed 6a59bc2 → 7d20749 (claude/visual-overhaul-pr8 → claude/motion-polish-pr9), including all 18 requested files and the relevant callers. CONFIRMED below means established from the code, not reproduced in Unity. I did not run Unity import/PlayMode or rerun the logic tests.

Findings

High — CONFIRMED: review battles overwrite the normal campaign autosave.

Files/methods:
Assets/_Game/Scripts/Runtime/ReviewBoot.cs — Boot(), Start()
Assets/_Game/Scripts/Runtime/GameApp.cs — BeginReview()
Assets/_Game/Scripts/Runtime/Battle/BattleView.cs — Finish()

Scenario: A player who already has progress opens the same installation/browser origin with ?review=battle. ReviewBoot creates a synthetic campaign, but BeginReview() leaves Saves pointing at the normal campaign directory. When the review battle finishes, BattleView.Finish() resolves that synthetic campaign and calls _app.Save() before result acknowledgement. The default slot is autosave.json, so the existing autosave is replaced. This does not require clicking a save button and does not overwrite manual slots automatically.

The runtime initialization hook also has no build restriction. It is query/command-line gated, but the comment “Review builds only” does not enforce that restriction.

Minimal fix: Isolate persistence before adopting the review state. Insert these lines at the beginning of BeginReview(), before assigning State:

C#
saveDirectory = Path.Combine(
    Application.persistentDataPath, "review-campaign");
Saves = new SaveRepository(saveDirectory, DB);

Also wrap the existing ReviewBoot.Boot() method and its attribute in:

C#
#if UNITY_EDITOR || DEVELOPMENT_BUILD || ABYSS_REVIEW
// Existing Boot attribute and method.
#endif

Use ABYSS_REVIEW only for intentionally enabled review players. The separate save directory is still needed in those builds; the build guard alone does not protect developers’ existing saves.

Medium — CONFIRMED: an accepted review-speed parameter can stall the battle indefinitely.

Files/methods:
Assets/_Game/Scripts/Runtime/ReviewBoot.cs — Start()
Assets/_Game/Scripts/Runtime/Battle/BattleView.cs — Speed, Dt, Wait()

Scenario: ?review=battle&speed=0 is accepted by float.Parse() and assigned directly to Preferences.BattleSpeed. Dt becomes zero, so the first positive-duration battle wait never finishes. Negative speed makes elapsed time run backward. Non-finite values are accepted without validation as well. This is an actual non-termination path, not merely an unusually slow animation.

Minimal fix: Replace the direct float.Parse() assignment with validation and the supported battle-speed bounds:

C#
if (!float.TryParse(
        Arg("speed", "1"),
        System.Globalization.NumberStyles.Float,
        System.Globalization.CultureInfo.InvariantCulture,
        out float speed)
    || float.IsNaN(speed)
    || float.IsInfinity(speed)
    || speed <= 0f)
{
    speed = 1f;
}

app.Preferences.BattleSpeed = Mathf.Clamp(speed, 1f, 2f);

Validate at this input boundary rather than attempting to make every coroutine recover from an invalid clock.

Medium — CONFIRMED: AUTO’s charge-interrupt planner does not count the new BreakPower mechanic.

Files/methods:
Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs — BestWeakAction(), SuggestChargeBreak()
Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs — DealHit()

Scenario: A charging enemy has two shield points remaining and is known to be weak to blunt damage. A warrior who acts before the release can use the new sk_w_shield_crush. On a landed hit, it removes two shield points: one for weakness and one from BreakPower.

BestWeakAction() instead counts only HitCount, so it treats this as one point. It also excludes non-weak skills entirely, although a neutral shield-crusher can remove the last shield point. Consequently, SuggestChargeBreak() can conclude that an interrupt is unavailable when the new mechanic makes one available. The weakness-only assumption was valid before this mechanic was introduced; the integration is now incomplete.

Minimal fix: In the skill loop inside BestWeakAction(), remove the weakness-only eligibility check. Count shield points rather than raw hits, preserving the existing target and random-target checks:

C#
if (!option.Usable || skill.Kind != SkillKind.Damage)
    continue;

long perHit =
    (KnownAffinity(enemy, DamageFormula.ElementOf(actor, skill))
        == PreviewAffinity.Weak ? 1L : 0L)
    + Math.Max(0, skill.BreakPower);

if (perHit == 0)
    continue;

// Keep the existing valid-target and random-target checks here.

int hits = (int)Math.Min(
    int.MaxValue,
    Math.Max(1L, skill.HitCount) * perHit);

// Keep the existing bestHits comparison and command assignment.

This preserves the planner’s existing knowledge restrictions and avoids overflowing the intermediate multiplication.

Medium — CONFIRMED: AUTO’s damage estimate omits execute damage and can miss a guaranteed finisher.

Files/methods:
Assets/_Game/Scripts/Logic/Battle/BattleEngine.Commands.cs — ExpectedHit(), AttackScore()
Assets/_Game/Scripts/Logic/Battle/DamageFormula.cs — ApplyTargetMultipliers(), IsExecute()

Scenario: The new sk_m_soul_burn has power 1.15 and a 1.6× execute multiplier at or below 30% HP. Consider a neutral, unguarded target with zero resistance, 150/1,000 HP, and a caster with 100 effective magic. Its damage before variance is 184, and even the low variance result is approximately 169. ExpectedHit() instead calculates 115, because it duplicates the damage calculation without the new execute term.

This means AUTO’s scoring does not recognize the kill and can prefer a non-finishing alternative. The actual resolver does apply the multiplier; the error is in the command policy, not the damage dealt.

Minimal fix: In ExpectedHit(), immediately after the existing bonus-versus-status multiplier and before guard:

C#
if (DamageFormula.IsExecute(skill, target))
    dmg *= Math.Max(0.0, Gd.D(skill.ExecuteMult));

Do not replace the whole estimate with an unrestricted affinity lookup: that would change AUTO’s existing hidden-weakness behavior.

Medium — CONFIRMED: styled movement can fight lingering recoil and capture the wrong “home.”

Files/methods:
Assets/_Game/Scripts/Runtime/Battle/BattleView.cs — StartAction(), LateUpdate(), ReturnHome()
Assets/_Game/Scripts/Runtime/Battle/BattleView.Moves.cs — Travel(), EnemyApproach(), CastFlourishRoutine()

Scenario: An enemy acts immediately after surviving a ranged basic attack. When it is already facing its target, there need not be a turning delay to let recoil expire. The old Move() explicitly clears KnockTime and restores Home before starting movement. The new styled paths bypass Move() and do neither. A charge’s initial backward movement, for example, immediately writes the transform through Travel(), while LateUpdate() still writes its recoil position. The result is movement that is overwritten until recoil expires, followed by a jump onto the path.

There is also a position-retention variant: CastFlourishRoutine() saves the current, potentially recoiled position as its local home and restores it afterward. A small residual offset can then fall below ReturnHome()’s translation threshold and remain.

Minimal fix: In StartAction(), after the actor/target flourish waits but before staging, turning, or calculating movement positions:

C#
if (actor.KnockTime > 0f)
{
    actor.KnockTime = 0f;
    actor.Model.transform.position = actor.Home;
}

Putting this only inside Travel() is insufficient: callers have already captured from, destination, or home before entering it.

Medium — CONFIRMED: monster body-family basic-attack effects are unreachable with the shipped presentation data.

Files/methods:
Assets/_Game/Scripts/Runtime/Battle/BattleView.Moves.cs — PlanEnemyStrike()
Assets/_Game/Scripts/Runtime/Battle/BattleView.cs — StartAction(), Damage()
Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs — AttackPresentation()

Scenario: A monster performs a normal basic attack. AttackPresentation() supplies "attack_enemy" because that row exists. StartAction() loads it into _presentation, then PlanEnemyStrike() immediately returns whenever _presentation != null. Therefore the newly added bite/claw/slam/sting selection does not execute for ordinary monster attacks in this data set. Even removing that early return alone would not fix the impact, because Damage() currently gives the generic presentation’s impact precedence.

Minimal fix: Allow the generic enemy presentation while continuing to respect bespoke presentations:

C#
// PlanEnemyStrike(): replace the current early-return condition.
if (actor.Side != BattleSide.Enemy
    || e.Kind != ActionKind.Attack
    || (_presentation != null
        && e.PresentationId != "attack_enemy"))
    return;

Then, in Damage(), prefer the planned family effect and its palette:

C#
Color tint = strike && _strikeImpact != null
    ? Color.white
    : PresentationColor(e.Element);

string impact = strike && _strikeImpact != null
    ? _strikeImpact
    : _presentation != null
        ? _presentation.ImpactVfx
        : "impact";

Keep _presentation intact so its hit-stop and shake settings are retained. The existing sound fallback can use _strikeSfx once the planner is actually reached.

Medium — CONFIRMED: new flourishes advance through hit-stop while their animation and action timer are frozen.

Files/methods:
Assets/_Game/Scripts/Runtime/Battle/BattleView.Moves.cs — especially CastFlourishRoutine(), SpinBody(), Step()
Assets/_Game/Scripts/Runtime/Battle/BattleView.cs — HitStop(), LateUpdate()

Scenario: A levitating caster or spinning attacker is still performing its flourish when damage starts hit-stop. The animator is set to speed zero and _actionElapsed stops advancing, but the flourish checks only _app.Paused and continues adding Dt. Its root therefore keeps rising, falling, or rotating through the frozen pose. When hit-stop ends, the animation and root motion are at different points in the action.

Minimal fix: In the new motion routines, gate elapsed-time advancement and transform updates on both conditions:

C#
if (!_app.Paused && !_hitstop)
{
    elapsed += Dt;
    // Existing motion calculation and transform writes.
}

Apply the same condition to the WaitFlourish() timeout budget so it measures progressing flourish time.

Do not make the global Dt zero during hit-stop, or globally change Wait() to stop on _hitstop. HitStop() itself uses Wait(seconds) to clear the flag; that change would introduce a permanent hit-stop.

Medium — CONFIRMED: dash/leap impact timing fails when the clip’s wind-up exceeds travel time.

File/methods:
Assets/_Game/Scripts/Runtime/Battle/BattleView.Moves.cs — Travel(), HeroDash(), HeroLeap()

Scenario: HeroDash() passes time - contact as the swing start time. The authored Thrust is approximately 1.208 seconds long with contact at 0.448, giving approximately 0.541 seconds to contact. Dash duration is capped at 0.4 seconds. Thus swingAt is negative.

Travel() treats every nonpositive value as “start immediately,” but does not account for the missing wind-up. The actor reaches the target at least approximately 0.14 seconds before contact and then waits there. Short leaping smashes have the same mismatch: landing effects can happen substantially before the damage event.

Minimal fix: Preserve the intended travel speed, but spend the excess wind-up before movement. Replace Travel()’s initial immediate-swing block with:

C#
if (!swung && swingAt <= 0f)
{
    Swing(actor, clip, cast);
    swung = true;

    if (swingAt < 0f)
        yield return Wait(-swingAt);
}

Now pre-movement wind-up + travel duration reaches the intended contact time instead of silently discarding the negative offset.

Low — CONFIRMED: a defeat leaves the automated review sequence waiting for an unreachable dungeon state.

Files/methods:
Assets/_Game/Scripts/Runtime/ReviewBoot.cs — Start(), ClickContinue()
Assets/_Game/Scripts/Runtime/GameApp.cs — FinishBattle(), RecoverFromDefeat()

Scenario: One configured review group defeats the party. The next iteration waits for app.Screen == GameScreen.Dungeon, and the full-vitals reset is located after that wait. Defeat routes to the defeat menu. Even manually selecting recovery routes to town, not back into the dungeon. The harness therefore stops progressing indefinitely instead of completing or reporting a failed review. This is confined to the new review runner, not a normal-game battle deadlock.

Minimal fix: Make a lost/exited review an explicit failure rather than silently polling forever. Insert this at the beginning of the while (app.Screen != GameScreen.Dungeon) body:

C#
bool defeated = state.Party.Count > 0
    && state.Party.TrueForAll(hero => hero.Hp <= 0);

if (defeated
    || app.Screen == GameScreen.Town
    || app.Screen == GameScreen.Title)
{
    Debug.LogError(
        "REVIEW aborted: party defeated or review route exited.");
    yield break;
}

This is the smallest safe fix. Continuing automatically after defeat would instead require an explicit review-only recovery route; clicking buttons by label does not provide one.

Low — CONFIRMED: combo follow-up damage is scheduled 40 ms before the new clip’s contact point.

Files/methods:
Assets/_Game/Scripts/Runtime/Battle/BattleView.Moves.cs — ComboWave()
Assets/_Game/Scripts/Runtime/Battle/BattleView.cs — PrepareHit()

Scenario: A multi-hit hero attack enters its second combo wave. ComboWave() starts the selected take 0.14 seconds before contact, but PrepareHit() waits only 0.10 seconds before returning to the damage/impact code. Damage numbers and hit VFX therefore precede contact by approximately 40 ms at 1×, subject to frame quantization. This mismatch is introduced by the new combo path, rather than the older plain-Attack restart path.

Minimal fix: Replace the combo-specific fixed wait with the remaining contact time:

C#
if (newWave && _wave > 1 && ComboWave(actor))
{
    yield return Wait(Mathf.Max(
        0f,
        _actionLength * Contact(actor.Model, _strikeClip)
            - _actionElapsed));
}

Leave the following else if for the existing plain-Attack restart attached to this condition.

Compatibility and verification boundary

Both pinned branches declare Unity 6000.3.25f1, not Unity 2021.3. That mismatch predates this branch, so I have not counted it as a PR regression. I did not establish a new C# 9 syntax blocker; this review is not certification that the project imports or builds in Unity 2021.3.

I have also not promoted hypothetical missing-FBX/null-reference failures, integer-overflow inputs, or a ClipAnimator loop deadlock into findings without a demonstrated path. Actual imported clip binding, mesh bounds, and Playables behavior still need Unity verification.

Top 5 fixes to do first
Isolate review persistence and gate review boot — prevent normal autosave loss.
Validate review speed — remove the confirmed non-terminating input path.
Update AUTO for BreakPower and execute — make the new mechanics participate in command decisions.
Clear recoil before styled-action position capture — eliminate competing transform writers and residual offsets.
Correct the motion clock/contact waits — freeze flourishes during hit-stop and synchronize dash, leap, and combo impacts.
