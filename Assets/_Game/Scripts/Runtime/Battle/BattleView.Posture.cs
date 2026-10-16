using System.Collections;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Runtime.Art;
using UnityEngine;

namespace Abyss.Runtime.Battle
{
    /// <summary>
    /// Body states that outlast a single take: a fallen hero lying on the floor and standing up again, a held guard, and the
    /// slowed or frozen body of a unit under a disabling status. Everything runs on the battle clock (pause, speed, hit-stop).
    /// </summary>
    public sealed partial class BattleView
    {
        /// <summary>
        /// Hero fall staged in code when the Die take never reaches the floor (Tripo <c>defeat_02</c>, see
        /// <see cref="ArtLibrary.DefeatTakeMinLength"/>): the slump window plays faster while the body tips over backwards.
        /// </summary>
        const float HeroFallTime = .55f, HeroFallTilt = 80f, HeroFallRoll = 10f, HeroFallPush = .25f, HeroDieRate = 2.5f;
        /// <summary>Standing back up in code: the shared Revive starts prone, which neither fall ends in.</summary>
        const float HeroRiseTime = .5f;
        /// <summary>The shared Humanoid Die (Tripo <c>fall</c>) takes 2 s to reach the floor at 1x; battle plays it faster.</summary>
        const float SharedFallRate = 1.4f;
        /// <summary>Longest the replay waits on an authored Revive take; the rest plays out beside the next beats.</summary>
        const float ReviveWaitCap = 1.5f, ReviveFade = .12f;
        /// <summary>Where a guard take holds (fraction): Brace holds frames 6-32 of 40, the Blender-rig Guard 1/3-2/3 of its length.</summary>
        const float GuardHold = .5f, GuardJoltFrom = .3f, GuardKnockScale = .5f;
        /// <summary>Body playback rate under a disabling status (sleep, stun, BREAK); freeze stops it.</summary>
        const float DazedRate = .35f;

        /// <summary>True when the unit's Die take is the standing Tripo defeat preset, which must be toppled in code to read as a fall.</summary>
        static bool StandingDefeat(BattleDisplayUnit unit) =>
            unit.Model.Anim is ClipAnimator && unit.Model.Anim.Length("Die") >= ArtLibrary.DefeatTakeMinLength;

        /// <summary>
        /// True when a revived hero stands up in code instead of playing its Revive take: the shared Humanoid Revive starts prone
        /// (face down, head forward) while the shared fall ends on the back and side, and a code topple ends wherever it tips.
        /// Blender-rig hunters own a Revive that starts from their own Die.
        /// </summary>
        static bool RisesInCode(BattleDisplayUnit unit) =>
            unit.Side == BattleSide.Party && (StandingDefeat(unit) || unit.Model.SharedHumanoidTakes);

        static Quaternion FallenRotation(BattleDisplayUnit unit) =>
            unit.Facing * Quaternion.Euler(-HeroFallTilt, 0f, ((unit.Slot & 1) == 0 ? 1f : -1f) * HeroFallRoll);

        static Vector3 FallenPosition(BattleDisplayUnit unit) => unit.Home + unit.Facing * Vector3.back * HeroFallPush;

        /// <summary>A fallen hero goes down: its own falling Die take, or the standing defeat take under a code topple.</summary>
        void HeroDown(BattleDisplayUnit unit)
        {
            if (!StandingDefeat(unit))
            {
                if (unit.Model.SharedHumanoidTakes) unit.DeathRate = SharedFallRate;   // ReviveEvent restores 1
                unit.Model.Play("Die", .075f);
                return;
            }
            if (Reduced) { LayFallen(unit); return; }
            unit.DeathRate = HeroDieRate;   // the 2.7 s slump window reads inside the fall; ReviveEvent restores 1
            unit.Model.Play("Die", .075f);
            StartCoroutine(HeroFall(unit));
        }

        /// <summary>Puts a fallen hero straight into its lying pose (spawned down, placed home, reduced motion).</summary>
        void LayFallen(BattleDisplayUnit unit)
        {
            unit.KnockTime = 0;
            if (!StandingDefeat(unit))
            {
                // An authored falling Die ends on the floor with a grounded root: hold its last pose on the mark.
                unit.Model.transform.SetPositionAndRotation(unit.Home, unit.Facing);
                unit.Model.Anim.PlayFrom("Die", 1f, 0f, null);
                return;
            }
            ((ClipAnimator)unit.Model.Anim).PlayFrom("Die", ArtLibrary.DefeatWindowHold, 0f, null);
            unit.Model.transform.SetPositionAndRotation(FallenPosition(unit), FallenRotation(unit));
        }

        IEnumerator HeroFall(BattleDisplayUnit unit)
        {
            var t = unit.Model.transform;
            unit.KnockTime = 0;   // the recoil must not keep writing the falling body's position
            Vector3 from = t.position, to = FallenPosition(unit);
            Quaternion start = t.rotation, end = FallenRotation(unit);
            float elapsed = 0;
            while (elapsed < HeroFallTime)
            {
                if (unit.Alive) yield break;   // revived mid-fall: the rise owns the body
                if (!_app.Paused && !_hitstop)
                {
                    elapsed += Dt;
                    float k = Mathf.Clamp01(elapsed / HeroFallTime);
                    // The knees give first, then the body tips over and accelerates into the floor.
                    float tip = Mathf.Clamp01((k - .15f) / .85f);
                    t.SetPositionAndRotation(Vector3.Lerp(from, to, Mathf.SmoothStep(0f, 1f, k)), Quaternion.Slerp(start, end, tip * tip));
                }
                yield return null;
            }
            if (unit.Alive) yield break;
            t.SetPositionAndRotation(to, end);
            if (!Reduced) Dust(unit, to, .35f);
        }

        /// <summary>A revived hero with no Revive take that starts from its fall pushes itself back up onto its mark into the stance.</summary>
        IEnumerator HeroRise(BattleDisplayUnit unit)
        {
            var t = unit.Model.transform;
            unit.KnockTime = 0;
            unit.Model.Play("Idle", Reduced ? 0f : HeroRiseTime * .8f);
            Vector3 from = t.position; Quaternion start = t.rotation;
            float elapsed = 0, seconds = Reduced ? 0f : HeroRiseTime;
            while (elapsed < seconds)
            {
                if (!unit.Alive) yield break;
                if (!_app.Paused && !_hitstop)
                {
                    elapsed += Dt;
                    float k = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(elapsed / seconds));
                    t.SetPositionAndRotation(Vector3.Lerp(from, unit.Home, k), Quaternion.Slerp(start, unit.Facing, k));
                }
                yield return null;
            }
            if (unit.Alive) t.SetPositionAndRotation(unit.Home, unit.Facing);
        }

        /// <summary>Guard: the hero braces and holds it (the take is windowed to stop at its hold) until its next turn starts.</summary>
        void HoldGuard(BattleDisplayUnit unit)
        {
            string guard = GuardTake(unit);
            unit.Model.Anim.Play(guard, .18f, true, null);
            _actionLength = unit.Model.Anim.Length(guard) * GuardHold;
        }

        /// <summary>Windows the hero's guard take at spawn so it holds the brace instead of settling back into the stance.</summary>
        void PrepareGuard(BattleDisplayUnit unit)
        {
            if (unit.Side != BattleSide.Party || !(unit.Model.Anim is ClipAnimator clips)) return;
            string guard = GuardTake(unit);
            if (clips.HasClip(guard)) clips.SetClipWindow(guard, 0f, GuardHold);
        }

        /// <summary>A blow on a braced hero: a short jolt inside the held guard instead of the open flinch.</summary>
        bool GuardedHit(BattleDisplayUnit unit)
        {
            if (!unit.Guarding || unit.Side != BattleSide.Party) return false;
            string guard = GuardTake(unit);
            if (!unit.Model.Anim.HasClip(guard)) return false;
            unit.Model.Anim.PlayFrom(guard, GuardJoltFrom, .06f, null);
            return true;
        }

        /// <summary>The guard ends with the hero's next turn: back into the stance.</summary>
        void ReleaseGuard(BattleDisplayUnit unit)
        {
            if (unit.Side == BattleSide.Party && unit.Alive && unit.Model.Anim.CurrentClip == GuardTake(unit)) unit.Model.Play("Idle", .25f);
        }

        /// <summary>Body rate a status leaves: frozen solid, slowed while asleep, stunned or broken; dead units keep their own rate.</summary>
        static float Posture(BattleDisplayUnit unit)
        {
            if (!unit.Alive) return 1f;
            bool dazed = unit.Broken;
            foreach (var status in unit.Statuses.Values)
            {
                if (status.Type == StatusEffectType.Freeze) return 0f;
                if (status.Type == StatusEffectType.Sleep || status.Type == StatusEffectType.Stun) dazed = true;
            }
            return dazed ? DazedRate : 1f;
        }

        /// <summary>
        /// Playback rate the unit's status puts on its takes: a frozen body stops whatever it plays; a dazed one only slows its
        /// standing loop, so hit reactions (a BREAK combo) still read at full speed.
        /// </summary>
        static float BodyRate(BattleDisplayUnit unit)
        {
            if (unit.PostureRate <= 0f || unit.PostureRate >= 1f) return unit.PostureRate;
            var anim = unit.Model.Anim; string clip = anim.CurrentClip;
            bool resting = clip == "Idle" || (anim is ClipAnimator clips && clip == clips.RestClip);
            return resting ? unit.PostureRate : 1f;
        }

        /// <summary>Normalized progress (0..1) of a move that travels at a steady speed, then eases to a stop over its last <paramref name="settle"/> seconds.</summary>
        static float SettleCurve(float elapsed, float seconds, float settle)
        {
            settle = Mathf.Clamp(settle, 0f, seconds);
            float cruise = seconds - settle * .5f;   // distance in units of the cruise speed
            if (cruise <= 0f) return 1f;
            float t = Mathf.Clamp(elapsed, 0f, seconds), steady = seconds - settle;
            if (t <= steady) return t / cruise;
            float u = t - steady;
            return (steady + u - u * u / (2f * settle)) / cruise;
        }

        /// <summary>Approach run that eases to a stop as the strike's wind-up plays (the strike lands just after the feet plant).</summary>
        IEnumerator ApproachRun(BattleDisplayUnit unit, Vector3 destination, float seconds, float settle, float arc)
        {
            if (unit.KnockTime > 0) { unit.KnockTime = 0; unit.Model.transform.position = unit.Home; }
            Vector3 from = unit.Model.transform.position; float elapsed = 0;
            while (elapsed < seconds)
            {
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float t = Mathf.Clamp01(elapsed / seconds);
                    unit.Model.transform.position = Vector3.Lerp(from, destination, SettleCurve(elapsed, seconds, settle)) + Vector3.up * (Mathf.Sin(Mathf.PI * t) * arc);
                }
                yield return null;
            }
            unit.Model.transform.position = destination;
        }
    }
}
