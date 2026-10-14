using System.Collections;
using System.Collections.Generic;
using Abyss.Logic.Battle;
using Abyss.Runtime.Art;
using UnityEngine;

namespace Abyss.Runtime.Battle
{
    /// <summary>
    /// Motion variety (<see cref="MotionStyles"/>): how monsters close in (pounce, charge, body slam, dive, blink, burrow,
    /// bounce, skitter, spin), the body motion over their casts, and the hero takes / flourishes per skill (leaping smash,
    /// spinning cut, lunging thrust, backstep shot, levitating spell, combo strikes). Every routine runs on the battle clock
    /// (pause, speed), touches only the acting unit's root transform / dissolve, and puts them back when it ends.
    /// Reduced motion never reaches these routines (StartAction keeps the plain staging there).
    /// </summary>
    public sealed partial class BattleView
    {
        /// <summary>Melee / action counter per unit, so consecutive actions pick different moves.</summary>
        readonly Dictionary<BattleDisplayUnit, int> _moveUses = new Dictionary<BattleDisplayUnit, int>();
        /// <summary>How a unit that left its mark gets back (blink and burrow return their own way).</summary>
        readonly Dictionary<BattleDisplayUnit, EnemyMove> _returnMove = new Dictionary<BattleDisplayUnit, EnemyMove>();
        /// <summary>Cast flourishes still moving their unit; the action end waits for them before the unit turns home.</summary>
        readonly HashSet<BattleDisplayUnit> _flourishing = new HashSet<BattleDisplayUnit>();
        /// <summary>Hero take plan of the current action (null for enemies and non-hero actions).</summary>
        HeroMotionPlan _plan;
        /// <summary>Root scale of each unit as spawned (squash and stretch always settles back to it).</summary>
        readonly Dictionary<BattleDisplayUnit, Vector3> _restScale = new Dictionary<BattleDisplayUnit, Vector3>();

        void RememberScale(BattleDisplayUnit unit) { if (unit?.Model != null) _restScale[unit] = unit.Model.transform.localScale; }

        int NextUse(BattleDisplayUnit unit)
        {
            _moveUses.TryGetValue(unit, out int uses);
            _moveUses[unit] = uses + 1;
            return uses;
        }

        /// <summary>
        /// The authored shared take in place of a library take of <paramref name="original"/>'s name, unless the hero's class /
        /// own layer ships that take (a bespoke Tripo motion always wins). Enemies and models without the take keep the original.
        /// </summary>
        static string HeroTake(BattleDisplayUnit unit, string original, string authored)
        {
            if (unit == null || unit.Side != BattleSide.Party || unit.Model == null) return original;
            if (unit.Model.HasClassClip(original) || !unit.Model.Anim.HasClip(authored)) return original;
            return authored;
        }

        string HitTake(BattleDisplayUnit unit) => HeroTake(unit, "Hit", "Flinch");
        string GuardTake(BattleDisplayUnit unit) => HeroTake(unit, "Guard", "Brace");

        EnemyMove EnemyMoveFor(ActionStartEvent e, BattleDisplayUnit actor)
        {
            if (!_app.DB.Enemies.TryGetValue(actor.DefId, out var def)) return EnemyMove.Dash;
            string model = string.IsNullOrEmpty(def.Model) ? def.Id : def.Model;
            return MotionStyles.EnemyApproach(model, def.Archetype, def.IsBoss, e.SkillId, NextUse(actor));
        }

        CastFlourish EnemyFlourishFor(ActionStartEvent e, BattleDisplayUnit actor)
        {
            if (!_app.DB.Enemies.TryGetValue(actor.DefId, out var def)) return CastFlourish.None;
            string model = string.IsNullOrEmpty(def.Model) ? def.Id : def.Model;
            return MotionStyles.EnemyCast(model, def.Archetype, e.SkillId);
        }

        static bool Lists(IReadOnlyList<string> ids, string id)
        {
            if (ids == null) return false;
            for (int i = 0; i < ids.Count; i++) if (ids[i] == id) return true;
            return false;
        }

        static string Pick(BattleDisplayUnit unit, string want, string fallback) => unit.Model.Anim.HasClip(want) ? want : fallback;
        static bool SupportTake(string take) => take == "Channel" || take == "Rally" || take == "Kneel";

        /// <summary>
        /// Sets the hero's take plan for this action and returns the take to swing instead of <paramref name="clip"/> (the
        /// class / signature choice StartAction made). Bespoke takes stay: an ultimate, a signature skill's own Skill take and
        /// a class / hero Cast keep playing; the authored shared takes replace the library's generic ones and add variety.
        /// </summary>
        string PlanHeroTake(ActionStartEvent e, BattleDisplayUnit actor, BattleDisplayUnit target, string clip, bool approach)
        {
            string cls = _app.DB.ClassOf(actor.DefId);
            bool allies = target != null && target.Side == actor.Side;
            int tier = _presentation != null ? _presentation.Tier : 1;
            _plan = MotionStyles.Hero(cls, e.Kind, e.SkillId, _presentation?.ActorAction, approach, allies, e.HitCount, tier, NextUse(actor));
            if (Reduced) { _plan.Flourish = HeroFlourish.None; }
            string spell = HeroTake(actor, "Cast", "Spell");
            switch (clip)
            {
                case "Cast":
                    if (e.Kind == ActionKind.Item) return Pick(actor, "Throw", spell);
                    // Support casts: kneel for a revive, rally for a war cry; a hero with its own Cast keeps it for blessings.
                    if (SupportTake(_plan.Take) && (_plan.Take != "Channel" || spell != "Cast")) return Pick(actor, _plan.Take, spell);
                    return spell;
                case "Skill":
                    if (!approach) return SupportTake(_plan.Take) ? Pick(actor, _plan.Take, clip) : clip;
                    // A hero's own Skill take stays the signature move; its other physical skills use the varied takes.
                    return IsSignature(e) ? clip : Pick(actor, _plan.Take, clip);
                case "Attack":
                    if (approach) return Pick(actor, _plan.Take, clip);
                    return SupportTake(_plan.Take) ? Pick(actor, _plan.Take, clip) : clip;
                default:
                    return clip;
            }
        }

        // ------------------------------------------------------------------ shared helpers

        /// <summary>Seconds from starting <paramref name="clip"/> to its strike point.</summary>
        static float ContactSeconds(BattleDisplayUnit unit, string clip) => unit.Model.Anim.Length(clip) * Contact(unit.Model, clip);

        /// <summary>Yaw of a unit's current facing with a pitch (forward lean, degrees) on top.</summary>
        static Quaternion Lean(Quaternion yaw, float pitch) => yaw * Quaternion.Euler(pitch, 0f, 0f);

        static Quaternion YawOnly(Quaternion rotation)
        {
            Vector3 forward = rotation * Vector3.forward; forward.y = 0;
            return forward.sqrMagnitude > 1e-4f ? Quaternion.LookRotation(forward) : rotation;
        }

        /// <summary>
        /// Moves the actor along <paramref name="path"/> (t 0..1 -> world position) over <paramref name="seconds"/>, calling
        /// Swing when <paramref name="swingAt"/> seconds have passed (once), with an optional lean / squash curve.
        /// </summary>
        IEnumerator Travel(BattleDisplayUnit actor, float seconds, System.Func<float, Vector3> path, float swingAt, string clip, bool cast,
            System.Func<float, float> lean = null, bool swing = true)
        {
            var t = actor.Model.transform; Quaternion yaw = YawOnly(t.rotation);
            float elapsed = 0; bool swung = !swing;
            if (!swung && swingAt <= 0f) { Swing(actor, clip, cast); swung = true; }
            while (elapsed < seconds)
            {
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float k = Mathf.Clamp01(elapsed / seconds);
                    t.position = path(k);
                    if (lean != null) t.rotation = Lean(yaw, lean(k));
                    if (!swung && elapsed >= swingAt) { Swing(actor, clip, cast); swung = true; }
                }
                yield return null;
            }
            t.position = path(1f);
            if (lean != null) t.rotation = Lean(yaw, lean(1f));
            if (!swung) Swing(actor, clip, cast);
        }

        /// <summary>Squash and stretch of the root (y scale, xz compensates) over <paramref name="seconds"/>, back to rest at the end.</summary>
        IEnumerator Squash(BattleDisplayUnit actor, float amount, float seconds)
        {
            var t = actor.Model.transform; float elapsed = 0;
            if (!_restScale.TryGetValue(actor, out var rest)) rest = t.localScale;
            while (elapsed < seconds)
            {
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float s = Mathf.Sin(Mathf.PI * Mathf.Clamp01(elapsed / seconds)) * amount;
                    t.localScale = new Vector3(rest.x * (1 + s * .5f), rest.y * (1 - s), rest.z * (1 + s * .5f));
                }
                yield return null;
            }
            t.localScale = rest;
        }

        void Dust(BattleDisplayUnit unit, Vector3 at, float scale)
        {
            if (_vfx.Supports("smoke")) Effect("smoke", at + Vector3.up * .3f, new Color(.78f, .74f, .68f), scale, 0, null, unit.Home.y);
        }

        void Quake(BattleDisplayUnit unit, Vector3 at, float strength)
        {
            if (_vfx.Supports("area_quake")) Effect("area_quake", at + Vector3.up * .9f, new Color(.9f, .8f, .6f), .45f * strength, 0, null, unit.Home.y);
            AddTrauma(.3f * strength); PlaySound("sfx_earth");
        }

        // ------------------------------------------------------------------ monster approaches

        /// <summary>
        /// Stages a monster's approach in <paramref name="move"/> style from its position to <paramref name="destination"/>,
        /// swinging <paramref name="clip"/> so its strike lands on arrival. Leaves the unit on the mark facing the target.
        /// </summary>
        IEnumerator EnemyApproach(EnemyMove move, BattleDisplayUnit actor, BattleDisplayUnit target, Vector3 destination, string clip, bool cast)
        {
            var t = actor.Model.transform;
            Vector3 from = t.position, flat = destination - from; flat.y = 0;
            float travel = flat.magnitude;
            Vector3 dir = travel > .001f ? flat / travel : t.forward;
            Vector3 side = Vector3.Cross(Vector3.up, dir);
            float contact = ContactSeconds(actor, clip);
            float size = Mathf.Clamp(actor.Model.Height / 1.3f, .7f, 2.2f);
            _returnMove[actor] = move;
            switch (move)
            {
                case EnemyMove.Pounce:
                {
                    yield return Squash(actor, .18f, .14f);
                    float time = Mathf.Clamp(travel / 7f, .34f, .55f), height = Mathf.Clamp(.35f + travel * .12f, .5f, 1.1f) * Mathf.Sqrt(size);
                    PlaySound("sfx_wind");
                    yield return Travel(actor, time, k => Vector3.Lerp(from, destination, k) + Vector3.up * (Mathf.Sin(Mathf.PI * k) * height),
                        time - contact, clip, cast, k => Mathf.Lerp(-12f, 14f, k));
                    t.rotation = YawOnly(t.rotation);
                    Dust(actor, destination, .5f * size);
                    StartCoroutine(Squash(actor, .12f, .1f));
                    break;
                }
                case EnemyMove.Charge:
                {
                    // Paw the ground (a step back, leaning back), then rush low past the mark and skid back onto it.
                    Vector3 back = from - dir * .22f;
                    yield return Travel(actor, .16f, k => Vector3.Lerp(from, back, Mathf.SmoothStep(0, 1, k)), 0, clip, cast, k => -8f * Mathf.Sin(Mathf.PI * k), false);
                    Dust(actor, back, .45f * size); PlaySound("sfx_footstep");
                    if (actor.Model.Anim.HasClip("Run")) { SetRunRate(actor, 99f); actor.Model.Anim.Play("Run", .08f, false); }
                    float time = Mathf.Clamp((travel + .22f) / 12f, .2f, .38f);
                    Vector3 past = destination + dir * Mathf.Min(.35f, .15f * size);
                    yield return Travel(actor, time, k => Vector3.Lerp(back, past, k * k), time - contact, clip, cast, k => 16f * Mathf.Sin(Mathf.PI * Mathf.Min(1f, k * 1.2f)));
                    Dust(actor, past, .5f * size);
                    yield return Travel(actor, .12f, k => Vector3.Lerp(past, destination, Mathf.SmoothStep(0, 1, k)), 0, clip, cast, k => -6f * (1 - k), false);
                    t.rotation = YawOnly(t.rotation);
                    break;
                }
                case EnemyMove.Slam:
                {
                    yield return Squash(actor, .22f, .16f);
                    float time = Mathf.Clamp(.45f + travel * .03f, .5f, .7f), height = Mathf.Clamp(1.1f + travel * .08f, 1.2f, 1.9f) * Mathf.Sqrt(size);
                    PlaySound("sfx_wind");
                    // Rises fast, hangs at the top, then drops hard onto the mark (pitching forward on the way down).
                    yield return Travel(actor, time, k => Vector3.Lerp(from, destination, Mathf.SmoothStep(0, 1, k)) +
                        Vector3.up * (height * (1 - Mathf.Pow(2f * k - 1f, 4f))), time - contact, clip, cast, k => k < .5f ? -10f * k * 2 : Mathf.Lerp(-10f, 22f, (k - .5f) * 2));
                    t.rotation = YawOnly(t.rotation);
                    Quake(actor, destination, size);
                    StartCoroutine(Squash(actor, .2f, .14f));
                    break;
                }
                case EnemyMove.Swoop:
                {
                    // Climb up and back, then dive along a curve that comes down onto the target.
                    Vector3 high = from - dir * .3f + Vector3.up * (1.0f + .2f * size);
                    PlaySound("sfx_wind");
                    yield return Travel(actor, .22f, k => Vector3.Lerp(from, high, 1 - (1 - k) * (1 - k)), 0, clip, cast, k => -14f * k, false);
                    float time = Mathf.Clamp(travel / 11f, .26f, .42f);
                    Vector3 control = Vector3.Lerp(high, destination, .5f) + Vector3.up * .6f;
                    yield return Travel(actor, time, k =>
                    {
                        float u = k * k; Vector3 a = Vector3.Lerp(high, control, u), b = Vector3.Lerp(control, destination, u);
                        return Vector3.Lerp(a, b, u);
                    }, time - contact, clip, cast, k => Mathf.Lerp(-14f, 30f, k));
                    yield return Travel(actor, .1f, k => destination, 0, clip, cast, k => 30f * (1 - k), false);
                    t.rotation = YawOnly(t.rotation);
                    break;
                }
                case EnemyMove.Blink:
                {
                    PlaySound("sfx_warp");
                    if (_vfx.Supports("dark")) Effect("dark", actor.Model.CenterPoint, new Color(.6f, .4f, 1f), .7f * size, 0, null, actor.Home.y);
                    yield return Fade(actor, 0f, 1f, .16f);
                    Vector3 facing = target.Model.transform.position - destination; facing.y = 0;
                    t.SetPositionAndRotation(destination, facing.sqrMagnitude > .01f ? Quaternion.LookRotation(facing) : t.rotation);
                    if (_vfx.Supports("dark")) Effect("dark", actor.Model.CenterPoint, new Color(.6f, .4f, 1f), .7f * size, 0, null, actor.Home.y);
                    Swing(actor, clip, cast);
                    yield return Fade(actor, 1f, 0f, Mathf.Min(.14f, contact * .6f));
                    break;
                }
                case EnemyMove.Burrow:
                {
                    float depth = actor.Model.Height * 1.05f;
                    Dust(actor, from, .7f * size); PlaySound("sfx_earth");
                    StartCoroutine(Fade(actor, 0f, 1f, .26f));
                    yield return Travel(actor, .26f, k => from + Vector3.down * (depth * k * k), 0, clip, cast, null, false);
                    // A dust trail runs under the floor to the target, then the body erupts with the strike.
                    float time = Mathf.Clamp(travel / 10f, .2f, .35f), elapsed = 0;
                    Vector3 under = destination + Vector3.down * depth;
                    int puffs = 0;
                    while (elapsed < time)
                    {
                        if (!_app.Paused)
                        {
                            elapsed += Dt;
                            float k = Mathf.Clamp01(elapsed / time);
                            t.position = Vector3.Lerp(from + Vector3.down * depth, under, k);
                            if (k * 3 >= puffs + 1 && puffs < 3) { puffs++; Dust(actor, new Vector3(t.position.x, actor.Home.y, t.position.z), .35f * size); }
                        }
                        yield return null;
                    }
                    Vector3 face = target.Model.transform.position - destination; face.y = 0;
                    if (face.sqrMagnitude > .01f) t.rotation = Quaternion.LookRotation(face);
                    Quake(actor, destination, .7f * size);
                    StartCoroutine(Fade(actor, 1f, 0f, .14f));
                    float rise = Mathf.Max(.16f, Mathf.Min(.24f, contact));
                    yield return Travel(actor, rise, k => Vector3.Lerp(under, destination, 1 - (1 - k) * (1 - k)) + Vector3.up * (Mathf.Sin(Mathf.PI * k) * .25f),
                        rise - contact, clip, cast, k => -18f * (1 - k));
                    actor.Model.SetDissolve(0);
                    t.rotation = YawOnly(t.rotation);
                    break;
                }
                case EnemyMove.Bounce:
                {
                    int hops = travel > 2.5f ? 3 : 2;
                    Vector3 start = from;
                    for (int i = 0; i < hops; i++)
                    {
                        bool last = i == hops - 1;
                        Vector3 end = Vector3.Lerp(from, destination, (i + 1f) / hops);
                        float h = (.55f - .12f * i) * Mathf.Sqrt(size), time = .2f;
                        yield return Squash(actor, .2f, .08f);
                        Vector3 a = start, b = end;
                        yield return Travel(actor, time, k => Vector3.Lerp(a, b, k) + Vector3.up * (Mathf.Sin(Mathf.PI * k) * h),
                            last ? time - contact : 0, clip, cast, null, last);
                        start = end;
                    }
                    Dust(actor, destination, .4f * size);
                    StartCoroutine(Squash(actor, .25f, .12f));
                    break;
                }
                case EnemyMove.Zigzag:
                {
                    if (actor.Model.Anim.HasClip("Run")) { SetRunRate(actor, 99f); actor.Model.Anim.Play("Run", .08f, false); }
                    PlaySound("sfx_footstep");
                    float time = Mathf.Clamp(travel / 8f, .3f, .5f), width = Mathf.Clamp(travel * .14f, .3f, .55f);
                    yield return Travel(actor, time, k => Vector3.Lerp(from, destination, k) + side * (Mathf.Sin(3f * Mathf.PI * k) * width),
                        time - contact, clip, cast);
                    break;
                }
                case EnemyMove.Spin:
                default:
                {
                    if (actor.Model.Anim.HasClip("Run")) { SetRunRate(actor, travel / Mathf.Max(.05f, ApproachTime(actor, travel))); actor.Model.Anim.Play("Run", RunFade, false); }
                    float time = ApproachTime(actor, travel);
                    yield return Travel(actor, time, k => Vector3.Lerp(from, destination, k) + Vector3.up * (Mathf.Sin(Mathf.PI * k) * PounceArc(actor, travel)),
                        time - Mathf.Min(contact, .2f), clip, cast);
                    if (move == EnemyMove.Spin) StartCoroutine(SpinBody(actor, Mathf.Max(0f, contact - _actionElapsed) - .12f, .36f));
                    break;
                }
            }
        }

        /// <summary>Dissolve <paramref name="from"/> -> <paramref name="to"/> over the battle clock (blink / burrow).</summary>
        IEnumerator Fade(BattleDisplayUnit unit, float from, float to, float seconds)
        {
            float elapsed = 0;
            while (elapsed < seconds)
            {
                if (!_app.Paused) { elapsed += Dt; unit.Model.SetDissolve(Mathf.Lerp(from, to, Mathf.Clamp01(elapsed / seconds))); }
                yield return null;
            }
            unit.Model.SetDissolve(to);
        }

        /// <summary>One full turn of the body about its vertical axis, centred on the strike (starts after <paramref name="delay"/>).</summary>
        IEnumerator SpinBody(BattleDisplayUnit unit, float delay, float seconds)
        {
            float waited = 0;
            while (waited < delay) { if (!_app.Paused) waited += Dt; yield return null; }
            var t = unit.Model.transform; Quaternion start = YawOnly(t.rotation); float elapsed = 0;
            PlaySound("sfx_wind");
            while (elapsed < seconds)
            {
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float k = Mathf.Clamp01(elapsed / seconds);
                    t.rotation = start * Quaternion.Euler(0f, 360f * (1 - (1 - k) * (1 - k)), 0f);
                }
                yield return null;
            }
            t.rotation = start;
        }

        /// <summary>A monster's way back after a blink or burrow strike; false when it returns the ordinary way (run / hop).</summary>
        bool SpecialReturn(BattleDisplayUnit actor, out EnemyMove move) =>
            _returnMove.TryGetValue(actor, out move) && (move == EnemyMove.Blink || move == EnemyMove.Burrow);

        /// <summary>Token-owned blink / burrow home for <see cref="ReturnHome"/>; never writes once the return was cancelled.</summary>
        IEnumerator SpecialHome(BattleDisplayUnit actor, EnemyMove move, System.Func<bool> owned)
        {
            var t = actor.Model.transform; float depth = actor.Model.Height * 1.05f;
            Vector3 from = t.position;
            float elapsed = 0, seconds = move == EnemyMove.Burrow ? .22f : .14f;
            if (move == EnemyMove.Burrow) Dust(actor, from, .5f);
            else if (_vfx.Supports("dark")) Effect("dark", actor.Model.CenterPoint, new Color(.6f, .4f, 1f), .6f, 0, null, actor.Home.y);
            while (elapsed < seconds)
            {
                if (!owned()) yield break;
                if (!_app.Paused)
                {
                    elapsed += Dt; float k = Mathf.Clamp01(elapsed / seconds);
                    actor.Model.SetDissolve(k);
                    if (move == EnemyMove.Burrow) t.position = from + Vector3.down * (depth * k);
                }
                yield return null;
            }
            if (!owned()) yield break;
            t.SetPositionAndRotation(actor.Home + (move == EnemyMove.Burrow ? Vector3.down * depth : Vector3.zero), actor.Facing);
            if (move == EnemyMove.Burrow) Dust(actor, actor.Home, .5f);
            elapsed = 0;
            while (elapsed < seconds)
            {
                if (!owned()) yield break;
                if (!_app.Paused)
                {
                    elapsed += Dt; float k = Mathf.Clamp01(elapsed / seconds);
                    actor.Model.SetDissolve(1 - k);
                    if (move == EnemyMove.Burrow) t.position = actor.Home + Vector3.down * (depth * (1 - k));
                }
                yield return null;
            }
            if (!owned()) yield break;
            actor.Model.SetDissolve(0);
            t.SetPositionAndRotation(actor.Home, actor.Facing);
            if (actor.Model.Anim.HasClip("Idle")) actor.Model.Play("Idle", ClipAnimator.ReturnFade);
        }

        // ------------------------------------------------------------------ cast flourishes (monsters and heroes)

        /// <summary>
        /// Body motion over a stationary cast whose release comes <paramref name="contact"/> seconds after the take starts:
        /// rear back and snap forward, hover up and settle, or hop and stamp. Restores the unit's mark and facing at the end.
        /// </summary>
        IEnumerator CastFlourishRoutine(BattleDisplayUnit unit, CastFlourish flourish, float contact)
        {
            if (flourish == CastFlourish.None || unit?.Model == null) yield break;
            _flourishing.Add(unit);
            var t = unit.Model.transform; Vector3 home = t.position; Quaternion yaw = YawOnly(t.rotation);
            float size = Mathf.Clamp(unit.Model.Height / 1.3f, .7f, 2.2f);
            float total = contact + (flourish == CastFlourish.Hover ? .5f : .35f), elapsed = 0;
            bool landed = false;
            try
            {
                while (elapsed < total)
                {
                    if (!_app.Paused)
                    {
                        elapsed += Dt;
                        float before = Mathf.Clamp01(elapsed / Mathf.Max(.05f, contact)), after = Mathf.Clamp01((elapsed - contact) / (total - contact));
                        switch (flourish)
                        {
                            case CastFlourish.Rear:
                                // Lean back while it gathers, snap forward on the release, settle.
                                float pitch = elapsed < contact ? -14f * Mathf.SmoothStep(0, 1, before)
                                    : Mathf.Lerp(12f, 0f, Mathf.SmoothStep(0, 1, after)) * Mathf.Min(1f, after * 6f + .2f);
                                t.rotation = Lean(yaw, pitch);
                                t.position = home - (yaw * Vector3.forward) * (elapsed < contact ? .12f * before : .12f * (1 - after) - .1f * Mathf.Sin(Mathf.PI * after));
                                break;
                            case CastFlourish.Hover:
                                float rise = elapsed < contact ? Mathf.SmoothStep(0, 1, before) : 1 - Mathf.SmoothStep(0, 1, after);
                                t.position = home + Vector3.up * (.45f * Mathf.Sqrt(size) * rise);
                                t.rotation = Lean(yaw, elapsed < contact ? -6f * before : Mathf.Lerp(8f, 0f, after));
                                break;
                            case CastFlourish.Stomp:
                                // Hop that lands on the release.
                                float hopStart = Mathf.Max(0f, contact - .3f);
                                float hop = elapsed < hopStart ? 0f : elapsed < contact ? Mathf.Sin(Mathf.PI * (elapsed - hopStart) / Mathf.Max(.05f, contact - hopStart)) : 0f;
                                t.position = home + Vector3.up * (.32f * Mathf.Sqrt(size) * hop);
                                if (!landed && elapsed >= contact) { landed = true; Quake(unit, home, .6f * size); StartCoroutine(Squash(unit, .18f, .12f)); }
                                break;
                        }
                    }
                    yield return null;
                }
            }
            finally
            {
                if (t != null) t.SetPositionAndRotation(home, yaw);
                _flourishing.Remove(unit);
            }
        }

        /// <summary>Waits (bounded) for a cast flourish to put its unit back before the action end moves it.</summary>
        IEnumerator WaitFlourish(BattleDisplayUnit unit)
        {
            float waited = 0;
            while (_flourishing.Contains(unit) && waited < 1f) { if (!_app.Paused) waited += Dt; yield return null; }
        }

        // ------------------------------------------------------------------ hero flourishes

        /// <summary>Leaping smash: crouch, jump in an arc and land on the mark with the strike (contact on landing).</summary>
        IEnumerator HeroLeap(BattleDisplayUnit actor, Vector3 destination, string clip)
        {
            var t = actor.Model.transform; Vector3 from = t.position, flat = destination - from; flat.y = 0;
            float travel = flat.magnitude, contact = ContactSeconds(actor, clip);
            yield return Squash(actor, .14f, .12f);
            float time = Mathf.Clamp(travel / 6.5f, .42f, .62f), height = Mathf.Clamp(.6f + travel * .12f, .7f, 1.3f);
            PlaySound("sfx_wind");
            yield return Travel(actor, time, k => Vector3.Lerp(from, destination, k) + Vector3.up * (Mathf.Sin(Mathf.PI * k) * height),
                time - contact, clip, false);
            Quake(actor, destination, .8f);
            StartCoroutine(Squash(actor, .12f, .1f));
        }

        /// <summary>Dashing thrust: a fast, low lunge onto the mark (the strike lands on arrival).</summary>
        IEnumerator HeroDash(BattleDisplayUnit actor, Vector3 destination, string clip)
        {
            var t = actor.Model.transform; Vector3 from = t.position, flat = destination - from; flat.y = 0;
            float travel = flat.magnitude, contact = ContactSeconds(actor, clip);
            float time = Mathf.Clamp(travel / (ApproachSpeed * 1.7f), .18f, .4f);
            if (actor.Model.Anim.HasClip("Run")) { SetRunRate(actor, travel / time); actor.Model.Anim.Play("Run", RunFade, false); }
            Dust(actor, from, .35f); PlaySound("sfx_wind");
            yield return Travel(actor, time, k => Vector3.Lerp(from, destination, k * k * (3 - 2 * k)), time - contact, clip, false,
                k => 10f * Mathf.Sin(Mathf.PI * k));
            t.rotation = YawOnly(t.rotation);
        }

        /// <summary>Backstep before a shot: hop back and slightly up; the hunter runs back to the mark after the action.</summary>
        IEnumerator Backstep(BattleDisplayUnit actor)
        {
            var t = actor.Model.transform; Vector3 from = t.position, back = from - YawOnly(t.rotation) * Vector3.forward * .75f;
            PlaySound("sfx_wind");
            yield return Travel(actor, .22f, k => Vector3.Lerp(from, back, 1 - (1 - k) * (1 - k)) + Vector3.up * (Mathf.Sin(Mathf.PI * k) * .3f),
                0, null, false, k => -8f * Mathf.Sin(Mathf.PI * k), false);
            Dust(actor, back, .3f);
        }

        /// <summary>
        /// Next strike wave of a hero's combo: the wave's take restarts just before its strike so the blow lands quickly.
        /// True when it played a take (PrepareHit then skips the plain Attack restart).
        /// </summary>
        bool ComboWave(BattleDisplayUnit actor)
        {
            if (_plan == null || actor.Side != BattleSide.Party || _plan.Combo.Count == 0 || Reduced) return false;
            string take = MotionStyles.WaveTake(_plan, _wave);
            if (!actor.Model.Anim.HasClip(take)) return false;
            float length = actor.Model.Anim.Length(take), contact = Contact(actor.Model, take);
            float start = Mathf.Clamp01(contact - .14f / Mathf.Max(.1f, length));
            actor.Model.Anim.PlayFrom(take, start, .08f);
            _actionLength = length; _actionElapsed = length * start; _strikeClip = take; _actionEnd = length * EndFraction(actor, take);
            // Each combo cut steps in a little (only from the strike mark, never past the target).
            var t = actor.Model.transform;
            StartCoroutine(Step(actor, YawOnly(t.rotation) * Vector3.forward * .12f, .1f));
            return true;
        }

        IEnumerator Step(BattleDisplayUnit actor, Vector3 offset, float seconds)
        {
            var t = actor.Model.transform; Vector3 from = t.position, to = from + offset; float elapsed = 0;
            while (elapsed < seconds)
            {
                if (!_app.Paused) { elapsed += Dt; t.position = Vector3.Lerp(from, to, Mathf.SmoothStep(0, 1, Mathf.Clamp01(elapsed / seconds))); }
                yield return null;
            }
            t.position = to;
        }

        /// <summary>A missed target sidesteps the blow (heroes and walking monsters; big bosses only lean).</summary>
        IEnumerator Dodge(BattleDisplayUnit unit, BattleDisplayUnit attacker)
        {
            if (Reduced || unit?.Model == null || !unit.Alive || unit.KnockTime > 0) yield break;
            var t = unit.Model.transform;
            if ((t.position - unit.Home).sqrMagnitude > .01f) yield break;
            Vector3 away = attacker != null ? unit.Home - attacker.Model.transform.position : unit.Facing * Vector3.back; away.y = 0;
            Vector3 side = Vector3.Cross(Vector3.up, away.sqrMagnitude > 1e-4f ? away.normalized : Vector3.forward);
            if ((unit.Slot & 1) == 1) side = -side;
            float amount = unit.Boss ? .15f : .55f, elapsed = 0, seconds = .3f;
            Quaternion yaw = unit.Facing;
            _flourishing.Add(unit);
            bool interrupted = false;
            try
            {
                while (elapsed < seconds)
                {
                    // A recoil, a fall or a revive owns the body from here.
                    if (unit.KnockTime > 0 || !unit.Alive) { interrupted = true; yield break; }
                    if (!_app.Paused)
                    {
                        elapsed += Dt;
                        float k = Mathf.Clamp01(elapsed / seconds), s = Mathf.Sin(Mathf.PI * k);
                        t.position = unit.Home + side * (amount * s) + Vector3.up * (.12f * s);
                        t.rotation = yaw * Quaternion.Euler(0f, 0f, (unit.Slot & 1) == 1 ? 10f * s : -10f * s);
                    }
                    yield return null;
                }
            }
            finally
            {
                _flourishing.Remove(unit);
                if (t != null && unit.Alive) { if (interrupted) t.rotation = unit.Facing; else t.SetPositionAndRotation(unit.Home, unit.Facing); }
            }
        }
    }
}
