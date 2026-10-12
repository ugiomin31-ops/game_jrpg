using System;
using System.Collections.Generic;
using Abyss.Logic.Battle;
using Abyss.Runtime.Art;
using Abyss.UI.Battle;
using UnityEngine;

namespace Abyss.Runtime.Battle
{
    public enum CameraEase { Linear, OutCubic, InOutCubic, OutExpo, InOutSine }

    /// <summary>Battle shot list (floor-1 polish brief, W2). S3/S4/S5/S7 are hooks only until the skill-VFX pass.</summary>
    public enum BattleShotKind { Establishing, Command, Target, StrikeFollow, Cast, CutIn, EnemyTurn, HitReaction, Victory, Defeat, Action, Boss, Intro }

    /// <summary>Camera pose without the additive layers (shake, FOV punch). Rotation already carries the dutch roll.</summary>
    public struct CameraPose
    {
        public Vector3 Position;
        public Quaternion Rotation;
        public float Fov;
        public CameraPose(Vector3 position, Quaternion rotation, float fov) { Position = position; Rotation = rotation; Fov = fov; }
    }

    /// <summary>
    /// One camera shot: a designed pose (world space, built from arena-space offsets), its blend in and the units it must
    /// keep fully visible. <see cref="BattleCameraDirector"/> fits the designed pose to the subjects and the HUD-free viewport.
    /// </summary>
    public sealed class BattleShot
    {
        public BattleShotKind Kind;
        /// <summary>Identity for idempotent requests: asking for the shot already playing does not restart its blend.</summary>
        public string Key;
        public Vector3 Position, Look;
        public float Fov, Dutch, Blend;
        public CameraEase Ease = CameraEase.OutCubic;
        /// <summary>Units whose whole bodies must stay inside the HUD-free viewport (living ones only).</summary>
        public readonly List<BattleDisplayUnit> Required = new List<BattleDisplayUnit>();
        /// <summary>Extra world boxes the frame must hold (e.g. where a melee enemy will strike), fitted like bodies.</summary>
        public readonly List<Bounds> Extra = new List<Bounds>();
        /// <summary>
        /// Bystander reference: false compares bystanders with the foreground subject (S1/S2: the hero); true with the
        /// tallest of the other required bodies (S6: the targeted heroes), so a nearer enemy never dominates a reverse angle.
        /// </summary>
        public bool BystanderVsTargets;
        /// <summary>A unit left out of the clearance checks (S6: the acting enemy, framed at its strike mark instead).</summary>
        public BattleDisplayUnit Ignore;
        public bool Fit = true;
        /// <summary>Dolly range along the view axis, as a multiple of the designed camera-to-look distance.</summary>
        public float MinDolly = 1f, MaxDolly = 1.8f;
        /// <summary>FOV the fitter may add (2° steps) when the dolly range is exhausted.</summary>
        public float MaxWiden = 8f;
        /// <summary>Extra horizontal inset of the fitting rect (orbits sweep the subjects sideways).</summary>
        public float ExtraInset;
        /// <summary>Top of the fitting rect as a viewport fraction (S8 keeps the party under the centre-screen VICTORY call-out).</summary>
        public float MaxViewportY = 1f;
        /// <summary>FOV change applied after arrival over <see cref="PushTime"/> (negative pushes in).</summary>
        public float Push, PushTime;
        /// <summary>Orbit around <see cref="OrbitPivot"/>: total degrees swept over <see cref="OrbitTime"/> battle seconds, centred on the fitted pose.</summary>
        public float Orbit, OrbitTime;
        public Vector3 OrbitPivot;
        /// <summary>Validate against arena geometry (walls, props) and fall back to the establishing shot when blocked.</summary>
        public bool CheckOcclusion = true;
        /// <summary>
        /// Close-shot clearance: no body nearer the camera may cover a required body, and no bystander may read larger than
        /// the shot's foreground subject (<see cref="Required"/>[0]).
        /// </summary>
        public bool Clearance;
        /// <summary>
        /// Every living unit is required, re-read at each fit (S0 and the hero-action framing), so summons, revives and
        /// deaths change the subjects instead of a list frozen when the shot was requested.
        /// </summary>
        public bool AllLiving;
        /// <summary>Horizontal padding (metres) on each required body while fitting (S6: room for the targets' hit recoil).</summary>
        public float Pad;
        /// <summary>
        /// A unit that moves during the shot (S6: the acting enemy). Its live body is checked every frame once the blend
        /// has settled; if it stays out of frame the director holds the establishing shot instead.
        /// </summary>
        public BattleDisplayUnit Track;
    }

    /// <summary>
    /// Owns the battle camera: shot selection, eased blends from the current pose, subject framing against the HUD-free
    /// viewport and arena occlusion, plus the additive layers (trauma shake, FOV punch). Hit-stop never touches it: blends
    /// run on unscaled time scaled only by the battle-speed setting. Ticked by <see cref="BattleView"/> from LateUpdate,
    /// before the HUD (execution order 200) places its tags, so tags never feed back into the framing.
    /// </summary>
    public sealed class BattleCameraDirector
    {
        // ---- shot values (arena space: party z -3 .. -4.6, enemies z +2.2 .. +4) -------------------------------------
        /// <summary>S0 Establishing: lowered home, all living units in the free viewport.</summary>
        public static readonly Vector3 HomePosition = new Vector3(0f, 2.6f, -8.6f), HomeAim = new Vector3(.6f, 1f, 1.2f);
        public const float HomeFov = 40f, HomeBlend = .5f;
        /// <summary>S1 Command: over the active hero's right shoulder toward the enemy group centre at 0.9 m.</summary>
        public static readonly Vector3 CommandOffset = new Vector3(1.05f, 1.45f, -2.3f);
        /// <summary>S1 candidates in order: the brief's shoulder, then tighter / higher variants that clear a teammate standing beside the hero.</summary>
        static readonly Vector3[] CommandOffsets =
        {
            CommandOffset, new Vector3(.7f, 1.9f, -2.8f), new Vector3(1.3f, 2.3f, -3.1f), new Vector3(.45f, 2.7f, -3.5f),
            new Vector3(-1.05f, 1.6f, -2.5f), new Vector3(-.7f, 2.3f, -3.1f)
        };
        public const float CommandFov = 36.5f, CommandBlend = .45f, CommandPush = -1.5f, CommandPushTime = .12f, EnemyGroupHeight = .9f;
        /// <summary>S2 Target select: S1 dollied 35 % toward the target's chest.</summary>
        public const float TargetDolly = .35f, TargetFov = 33f, TargetBlend = .25f, TargetHeroClearance = 1.8f;
        /// <summary>S2 enemy target: camera offset to the right of the hero-to-target line (then the left side as a last resort).</summary>
        static readonly float[] TargetLaterals = { 1.15f, 1.7f, .7f, -1.15f };
        /// <summary>S2 ally target: reverse angle over the target ally, from in front of the party.</summary>
        static readonly Vector3[] AllyOffsets =
        {
            new Vector3(-1.05f, 1.45f, 2.3f), new Vector3(1.05f, 1.45f, 2.3f), new Vector3(-.8f, 2.1f, 3f), new Vector3(.8f, 2.1f, 3f)
        };
        /// <summary>S6 Enemy turn: reverse angle from behind the acting enemy toward the target hero's chest.</summary>
        public static readonly Vector3 EnemyOffset = new Vector3(-1.4f, 1.6f, 2.6f);
        /// <summary>S6 candidates: the brief's reverse angle, mirrored, higher / farther back, then wider side angles.</summary>
        static readonly Vector3[] EnemyOffsets =
        {
            EnemyOffset, new Vector3(1.4f, 1.6f, 2.6f), new Vector3(-1f, 2.3f, 3.2f), new Vector3(1f, 2.3f, 3.2f), new Vector3(0f, 2.9f, 3.8f),
            // Shorter and wider: beside a melee strike mark, clear of the enemy line behind it and of the struck hero.
            new Vector3(-2.3f, 1.8f, 2f), new Vector3(2.3f, 1.8f, 2f), new Vector3(-1.8f, 2.6f, 1.5f), new Vector3(1.8f, 2.6f, 1.5f),
            // Tight and high, for a long run whose strike mark sits just ahead of the enemy line.
            new Vector3(-.9f, 2.5f, 1.1f), new Vector3(.9f, 2.5f, 1.1f), new Vector3(0f, 3.3f, 1.6f)
        };
        public const float EnemyFov = 40f, EnemyBlend = .35f;
        /// <summary>S6 fitting room: hit recoil on the targets (BattleView caps it near 0.4 m) and the hop of a return trip.</summary>
        const float RecoilPad = .4f, HopPad = .45f;
        /// <summary>A tracked S6 actor may leave the frame this long (battle seconds) before the director holds S0.</summary>
        const float TrackGrace = .2f;
        /// <summary>
        /// S0 search: the brief's lowered home first, then the previous home and two higher, wider fallbacks. Each one is
        /// fitted and checked against the arena; the first that holds every living unit wins.
        /// </summary>
        static readonly (Vector3 Position, Vector3 Aim, float Fov)[] HomeCandidates =
        {
            (HomePosition, HomeAim, HomeFov),
            (new Vector3(0f, 3.6f, -10.2f), new Vector3(.6f, 1.05f, .6f), 42f),
            (new Vector3(0f, 5f, -11.5f), new Vector3(.6f, .8f, .5f), 44f),
            (new Vector3(0f, 7f, -12f), new Vector3(.6f, .5f, 0f), 46f)
        };
        /// <summary>Victory orbit sweeps tried in order: the brief's 25°, a shorter sweep, then a still hold.</summary>
        static readonly float[] VictorySweeps = { VictoryOrbit, 12f, 0f };
        /// <summary>Extra side insets for fitting the orbit's centre pose (room for the sweep).</summary>
        static readonly float[] VictoryInsets = { .05f, .1f, .15f };
        const int OrbitSamples = 5;
        /// <summary>S8 Victory: in front of the party at 1.4 m, a slow 25° orbit over 2.4 s.</summary>
        public static readonly Vector3 VictoryOffset = new Vector3(.6f, 1.4f, 5.2f);
        /// <summary>The call-out band (BattleHUD.Announce) spans roughly 0.45-0.68 of the screen height; the party stands below it.</summary>
        public const float VictoryTop = .45f;
        public const float VictoryFov = 40f, VictoryBlend = .6f, VictoryOrbit = 25f, VictoryOrbitTime = 2.4f, PartyChest = .85f;
        // Fitting: inset of the HUD-free viewport, fill aim, iteration caps and the re-fit hysteresis.
        const float InsetX = .02f, InsetY = .025f, FillAim = .97f, AcceptFill = .86f;
        // Clearance: share of a required body a nearer body may cover, and how much larger than the foreground a bystander may read.
        const float MaxCover = .3f, MaxBystander = 1.1f, MaxBystanderVsTargets = 1.6f;
        const int FitIterations = 14, CentreIterations = 3;
        const float RefitMove = .12f, RefitAngle = .8f, RefitFov = .4f, RefitBlend = .3f;
        // Additive layers (unchanged feel from the pre-director BattleView).
        const float TraumaDecay = 1.6f, ShakeOffset = .22f, ShakeRoll = .6f, ShakeFrequency = 24f, PunchRecover = 9f;

        readonly Camera _camera;
        readonly Transform _arena;
        readonly BattleHUD _hud;
        readonly IEnumerable<BattleDisplayUnit> _units;
        readonly Vector3 _oldPosition;
        readonly Quaternion _oldRotation;
        readonly float _oldFov;
        readonly Dictionary<CharacterModel, BodyParts> _bodies = new Dictionary<CharacterModel, BodyParts>();
        readonly List<Bounds> _boxes = new List<Bounds>(8);
        readonly List<Bounds> _props = new List<Bounds>();
        readonly Vector3[] _corners = new Vector3[8];
        Transform _geometry;
        bool _interiorKnown;
        Vector3 _interiorCentre;
        float _interiorRadius = float.PositiveInfinity, _ceiling = float.PositiveInfinity;

        BattleShot _shot;
        List<BattleShot> _candidates;
        readonly List<Bounds> _all = new List<Bounds>(10);
        readonly List<bool> _allRequired = new List<bool>(10);
        CameraPose _from, _to, _base;
        float _blendElapsed, _blendLength, _shotElapsed;
        CameraEase _ease;
        int _resolvedVersion = -1, _signature;
        float _trackMiss;
        bool _lastBlocked;
        float _trauma, _punch, _speed = 1f;
        bool _reduced, _restored;

        public BattleShot Current => _shot;
        /// <summary>Diagnostics: which candidate the last request picked and why earlier ones were rejected.</summary>
        public string LastChoice { get; private set; } = "";
        string _reason = "";
        public CameraPose Pose => _base;
        /// <summary>True while a blend toward the current shot is still running.</summary>
        public bool Blending => _blendElapsed < _blendLength;

        public BattleCameraDirector(Camera camera, Transform arena, BattleHUD hud, IEnumerable<BattleDisplayUnit> units)
        {
            _camera = camera ?? throw new ArgumentNullException(nameof(camera));
            _arena = arena ?? throw new ArgumentNullException(nameof(arena));
            _hud = hud; _units = units ?? throw new ArgumentNullException(nameof(units));
            _oldPosition = camera.transform.position; _oldRotation = camera.transform.rotation; _oldFov = camera.fieldOfView;
            _base = new CameraPose(_oldPosition, _oldRotation, _oldFov);
        }

        /// <summary>Arena environment root used for occlusion checks (walls, ceiling, props, colliders).</summary>
        public void SetArenaGeometry(Transform geometry) { _geometry = geometry; _interiorKnown = false; }

        // ---- shot requests -----------------------------------------------------------------------------------------

        /// <summary>S0: all living units. <paramref name="instant"/> cuts; otherwise blends over <paramref name="blend"/> (default 0.5 s InOutCubic).</summary>
        public void Establishing(bool instant = false, float blend = HomeBlend, CameraEase ease = CameraEase.InOutCubic)
        {
            var shots = EstablishingShots();
            foreach (var shot in shots) { shot.Blend = blend; shot.Ease = ease; }
            if (instant) Cut(shots); else PlayFirst(shots);
        }

        /// <summary>S1: menu open for <paramref name="hero"/> (also menu reopen and cancel back to the root).</summary>
        public void Command(BattleDisplayUnit hero)
        {
            if (hero == null || hero.Model == null) { Establishing(); return; }
            PlayFirst(CommandShots(hero));
        }

        /// <summary>S2: target preview. Enemy targets: S1 dollied toward the target. Ally targets: reverse over the target ally.</summary>
        public void Target(BattleDisplayUnit actor, BattleDisplayUnit target)
        {
            if (actor == null || actor.Model == null) { Establishing(); return; }
            if (target == null || target.Model == null) { Command(actor); return; }
            string key = "target:" + actor.Id + ">" + target.Id;
            var shots = new List<BattleShot>();
            Vector3 chest = Chest(target);
            if (target.Side == actor.Side)
            {
                // Reverse over the target ally: from the enemy side, heroes seen from the front (mirrored, then higher).
                foreach (var offset in AllyOffsets)
                {
                    var shot = NewShot(BattleShotKind.Target, key, TargetFov, TargetBlend, CameraEase.OutCubic);
                    shot.Position = _arena.TransformPoint(Local(target.Home) + offset);
                    shot.Look = target.Id == actor.Id ? chest : Vector3.Lerp(chest, Chest(actor), .35f);
                    shot.Required.Add(actor);
                    if (target.Id != actor.Id) shot.Required.Add(target);
                    shots.Add(shot);
                }
            }
            else
            {
                // Same side as S1, the camera beside the hero-to-target line so the hero never covers the target, then a
                // dolly toward the target that stops short of passing the hero (hero stays at the frame edge).
                Vector3 from = Local(actor.Home), to = Local(target.Home), dir = to - from; dir.y = 0f;
                dir = dir.sqrMagnitude > 1e-4f ? dir.normalized : Vector3.forward;
                Vector3 side = Vector3.Cross(Vector3.up, dir);
                foreach (var lateral in TargetLaterals)
                {
                    Vector3 local = from + side * lateral + Vector3.up * CommandOffset.y + dir * CommandOffset.z;
                    Vector3 start = _arena.TransformPoint(local);
                    Vector3 axis = chest - start;
                    float ahead = Vector3.Dot(Chest(actor) - start, axis.normalized);
                    float dolly = Mathf.Min(axis.magnitude * TargetDolly, Mathf.Max(0f, ahead - TargetHeroClearance));
                    var shot = NewShot(BattleShotKind.Target, key, TargetFov, TargetBlend, CameraEase.OutCubic);
                    shot.Position = start + axis.normalized * dolly;
                    shot.Look = chest;
                    shot.Required.Add(actor); shot.Required.Add(target);
                    shots.Add(shot);
                }
            }
            PlayFirst(shots);
        }

        /// <summary>
        /// S6: enemy turn (and charge announcements). Reverse angle from behind the acting enemy toward its targets, heroes
        /// seen from the front. <paramref name="strikeFrom"/> is where a melee enemy will stand when it strikes: the shot
        /// is then built behind that mark (the enemy runs into the composition instead of out of it).
        /// </summary>
        public void EnemyTurn(BattleDisplayUnit enemy, IReadOnlyList<BattleDisplayUnit> targets, Vector3? strikeFrom = null)
        {
            if (enemy == null || enemy.Model == null) { Establishing(); return; }
            // Identity includes the composition inputs (strike mark or home), so a cast after a melee strike on the same
            // target gets its own framing; an identical request stays idempotent.
            string key = "enemy:" + enemy.Id + (strikeFrom.HasValue
                ? "@" + Mathf.RoundToInt(strikeFrom.Value.x * 10f) + "," + Mathf.RoundToInt(strikeFrom.Value.z * 10f) : "@home");
            var aimed = new List<BattleDisplayUnit>();
            Vector3 look = Vector3.zero; int count = 0;
            if (targets != null)
                foreach (var target in targets)
                {
                    if (target == null || target.Model == null || target.Id == enemy.Id || !target.Alive) continue;
                    aimed.Add(target); look += Chest(target); count++; key += ">" + target.Id;
                }
            if (count == 0)
            {
                // No hero target (self buff, summon): look at the party centre.
                foreach (var unit in _units)
                    if (unit.Side != enemy.Side && unit.Alive && unit.Model != null) { look += Chest(unit); count++; }
            }
            look = count > 0 ? look / count : _arena.TransformPoint(new Vector3(0f, PartyChest, -3.6f));
            // The enemy's mark for this shot: its home, or the melee strike point. A melee enemy runs a straight line from
            // home to the mark and back: the frame holds its body at both ends (plus the return hop), and since the view
            // volume is convex the whole approach and return stay inside it.
            Vector3 mark = strikeFrom ?? enemy.Home;
            Bounds? atHome = null, atMark = null;
            if (strikeFrom.HasValue && BodyBox(enemy, out var body))
            {
                body.max += Vector3.up * HopPad;
                atHome = body;
                body.center += strikeFrom.Value - enemy.Home; atMark = body;
            }
            // Enemy-facing frame: forward toward the look point; table offsets are authored for an enemy facing arena -z.
            Vector3 forward = look - mark; forward.y = 0f;
            forward = forward.sqrMagnitude > 1e-4f ? forward.normalized : -_arena.forward;
            Vector3 right = Vector3.Cross(Vector3.up, forward);
            var shots = new List<BattleShot>();
            foreach (var offset in EnemyOffsets)
            {
                var shot = NewShot(BattleShotKind.EnemyTurn, key, EnemyFov, EnemyBlend, CameraEase.OutCubic);
                shot.BystanderVsTargets = true; shot.Pad = RecoilPad; shot.Track = enemy;
                if (atMark.HasValue)
                {
                    // The moving enemy is held as its path ends (home and strike mark), not as one unit box.
                    shot.Required.AddRange(aimed); shot.Extra.Add(atHome.Value); shot.Extra.Add(atMark.Value); shot.Ignore = enemy;
                }
                else { shot.Required.Add(enemy); shot.Required.AddRange(aimed); }
                shot.Position = mark - right * offset.x + Vector3.up * offset.y - forward * offset.z;
                shot.Look = look;
                shots.Add(shot);
            }
            PlayFirst(shots);
        }

        /// <summary>
        /// Hero action until the S3/S4/S5 pass lands: the establishing framing (every living unit) eased a little toward
        /// the action, as before the director.
        /// </summary>
        public void Action(BattleDisplayUnit actor, BattleDisplayUnit target, bool ultimate)
        {
            if (actor == null || actor.Model == null) return;
            Vector3 centre = target != null && target.Model != null ? (Chest(actor) + Chest(target)) * .5f : Chest(actor);
            Vector3 local = _arena.InverseTransformPoint(centre);
            Vector3 emphasis = new Vector3(Mathf.Clamp(local.x - HomeAim.x, -3f, 3f) * .16f, 0f, Mathf.Clamp(local.z, -3f, 3f) * .1f);
            var shot = EstablishingShots()[0];
            shot.Kind = BattleShotKind.Action;
            shot.Key = "action:" + actor.Id + ">" + (target != null ? target.Id : "") + (ultimate ? "!" : "");
            shot.Position += _arena.TransformVector(emphasis); shot.Look += _arena.TransformVector(emphasis);
            shot.Fov = HomeFov - (ultimate ? 5f : 2f); shot.Blend = .4f; shot.Ease = CameraEase.OutCubic; shot.MinDolly = .9f;
            Play(shot);
        }

        static BattleShot NewShot(BattleShotKind kind, string key, float fov, float blend, CameraEase ease) =>
            new BattleShot { Kind = kind, Key = key, Fov = fov, Blend = blend, Ease = ease, Clearance = true };

        /// <summary>Boss entrance / phase push toward <paramref name="boss"/> from the establishing framing (no fitting: a deliberate push).</summary>
        public void BossPush(BattleDisplayUnit boss, float blend)
        {
            if (boss == null || boss.Model == null) return;
            ChooseEstablishing(EstablishingShots(), out _, out var home);
            Vector3 focus = boss.Model.CenterPoint;
            Vector3 look = home.Position + home.Rotation * Vector3.forward * Vector3.Distance(home.Position, focus);
            var shot = new BattleShot
            {
                Kind = BattleShotKind.Boss, Key = "boss:" + boss.Id, Fit = false, CheckOcclusion = false,
                Position = Vector3.Lerp(home.Position, focus, .22f), Look = Vector3.Lerp(look, focus, .65f),
                Fov = home.Fov - 4f, Blend = blend, Ease = CameraEase.OutCubic
            };
            Play(shot);
        }

        /// <summary>S8: victory orbit in front of the party.</summary>
        public void Victory()
        {
            var shot = new BattleShot
            {
                Kind = BattleShotKind.Victory, Key = "victory", Fov = VictoryFov, Blend = VictoryBlend, Ease = CameraEase.InOutCubic,
                Orbit = VictoryOrbit, OrbitTime = VictoryOrbitTime, MinDolly = .6f, MaxViewportY = VictoryTop
            };
            Vector3 party = Vector3.zero; int count = 0;
            foreach (var unit in _units)
                if (unit.Side == BattleSide.Party && unit.Alive) { party += Local(unit.Home); count++; shot.Required.Add(unit); }
            party = count > 0 ? party / count : new Vector3(0f, 0f, -3f);
            Vector3 pivot = new Vector3(party.x, PartyChest, party.z);
            shot.OrbitPivot = _arena.TransformPoint(pivot);
            shot.Position = _arena.TransformPoint(new Vector3(party.x + VictoryOffset.x, VictoryOffset.y, party.z + VictoryOffset.z));
            shot.Look = shot.OrbitPivot;
            // Validate bounded samples across the sweep (framing and arena), shortening it, then holding still, if needed.
            // The centre pose is fitted inside a narrower rect (extra side inset) so the sweep has room; the samples are
            // checked against the normal rect. The first inset / sweep pair that holds wins.
            bool ok = false; float sweep = 0f, inset = VictoryInsets[0];
            foreach (float candidate in VictorySweeps)
            {
                if (candidate == 0f) break;
                foreach (float tryInset in VictoryInsets)
                {
                    shot.ExtraInset = tryInset;
                    var pose = Resolve(shot, out ok);
                    if (ok && OrbitHolds(shot, pose, candidate)) { sweep = candidate; inset = tryInset; break; }
                }
                if (sweep > 0f) break;
            }
            shot.ExtraInset = inset;
            if (sweep == 0f) Resolve(shot, out ok);
            shot.Orbit = sweep;
            string note = " orbit " + sweep + (ok ? "" : " (centre pose failed: " + _reason + ")");
            Play(shot);
            LastChoice += note;
        }

        /// <summary>True when every sampled pose of a <paramref name="sweep"/>° orbit still frames the bodies and clears the arena.</summary>
        bool OrbitHolds(BattleShot shot, CameraPose pose, float sweep)
        {
            Rect rect = FitRect(0f);
            if (shot.MaxViewportY < rect.yMax && shot.MaxViewportY - rect.yMin > .2f) rect.yMax = shot.MaxViewportY;
            for (int i = 0; i < OrbitSamples; i++)
            {
                float angle = Mathf.Lerp(-.5f, .5f, i / (OrbitSamples - 1f)) * sweep;
                var spin = Quaternion.AngleAxis(angle, _arena.up);
                Vector3 position = shot.OrbitPivot + spin * (pose.Position - shot.OrbitPivot);
                var sample = new CameraPose(position, spin * pose.Rotation, pose.Fov);
                if (!Frames(sample, rect) || (shot.CheckOcclusion && Blocked(position))) return false;
            }
            return true;
        }

        /// <summary>True when the current fitting boxes all project inside <paramref name="rect"/> (viewport) at <paramref name="pose"/>.</summary>
        bool Frames(CameraPose pose, Rect rect)
        {
            var e = Measure(pose.Position, pose.Rotation);
            if (!e.Valid) return false;
            float tanV = Mathf.Tan(pose.Fov * .5f * Mathf.Deg2Rad), tanH = tanV * Mathf.Max(.1f, _camera.aspect);
            return e.X0 >= (2f * rect.xMin - 1f) * tanH - 1e-3f && e.X1 <= (2f * rect.xMax - 1f) * tanH + 1e-3f
                && e.Y0 >= (2f * rect.yMin - 1f) * tanV - 1e-3f && e.Y1 <= (2f * rect.yMax - 1f) * tanV + 1e-3f;
        }

        /// <summary>Defeat: lift away over the fallen party.</summary>
        public void Defeat()
        {
            Vector3 party = Vector3.zero; int count = 0;
            foreach (var unit in _units) if (unit.Side == BattleSide.Party) { party += Local(unit.Home); count++; }
            party = count > 0 ? party / count : new Vector3(0f, 0f, -3f);
            Play(new BattleShot
            {
                Kind = BattleShotKind.Defeat, Key = "defeat", Fit = false, CheckOcclusion = false,
                Position = _arena.TransformPoint(new Vector3(0f, 8.5f, -12.5f)), Look = _arena.TransformPoint(party),
                Fov = HomeFov, Blend = 1.4f, Ease = CameraEase.InOutCubic
            });
        }

        /// <summary>Hard cut to an arena-space pose (battle intro start). The next Play blends from it.</summary>
        public void CutTo(Vector3 localPosition, Vector3 localLook, float fov)
        {
            Cut(new BattleShot
            {
                Kind = BattleShotKind.Intro, Key = "intro", Fit = false, CheckOcclusion = false,
                Position = _arena.TransformPoint(localPosition), Look = _arena.TransformPoint(localLook), Fov = fov
            });
        }

        // ---- W2-T3 hooks (S3 / S4 / S5 / S7). Safe no-ops until the skill-VFX pass implements them. ----------------
        /// <summary>S3 strike follow (melee approach). Not implemented yet: keeps the current shot.</summary>
        public void StrikeFollow(BattleDisplayUnit actor, BattleDisplayUnit target) { }
        /// <summary>S4 shot/cast with a whip to the impact framing. Not implemented yet: keeps the current shot.</summary>
        public void CastShot(BattleDisplayUnit actor, BattleDisplayUnit target, bool release) { }
        /// <summary>S5 skill cut-in push on the caster (tier ≥ 2, ultimates). Not implemented yet: keeps the current shot.</summary>
        public void SkillCutIn(BattleDisplayUnit caster, int tier, bool ultimate) { }
        /// <summary>S7 hit reaction hold on a hero. Not implemented yet: keeps the current shot.</summary>
        public void HitReaction(BattleDisplayUnit target) { }

        // ---- additive layers ---------------------------------------------------------------------------------------
        public void AddTrauma(float shake) { if (!_reduced) _trauma = Mathf.Clamp01(_trauma + shake * 1.5f); }
        /// <summary>FOV punch: keeps the strongest (most negative) request, recovers exponentially.</summary>
        public void Punch(float fov) { if (!_reduced) _punch = Mathf.Min(_punch, fov); }

        // ---- playback ----------------------------------------------------------------------------------------------

        /// <summary>Blends to <paramref name="shot"/> from the current pose. Re-requesting the playing shot keeps its blend.</summary>
        public void Play(BattleShot shot) { if (shot != null) PlayFirst(new List<BattleShot> { shot }); }

        /// <summary>
        /// Blends to the first candidate that fits, clears and is not blocked by the arena; the establishing shot when none
        /// does. Candidates share one key: re-requesting the playing request keeps its blend.
        /// </summary>
        public void PlayFirst(List<BattleShot> candidates)
        {
            if (_restored || candidates == null || candidates.Count == 0) return;
            if (_reduced && candidates[0].Kind != BattleShotKind.Establishing) candidates = EstablishingShots();
            string key = candidates[0].Key;
            // The same request again keeps its blend; a changed set of living units is picked up by Tick's re-fit.
            if (_shot != null && key != null && key == _shot.Key) return;
            if (!Choose(candidates, out var shot, out var pose))
            {
                var fallback = EstablishingShots();
                foreach (var f in fallback) { f.Blend = candidates[0].Blend; f.Ease = candidates[0].Ease; }
                if (_shot != null && _shot.Key == fallback[0].Key) return;
                candidates = fallback;
                Choose(candidates, out shot, out pose);
            }
            _candidates = candidates;
            Begin(shot, pose, _reduced ? 0f : shot.Blend, shot.Ease);
        }

        /// <summary>
        /// First candidate whose fitted pose is valid. Close shots return false when none is (the caller falls back to
        /// S0); an establishing list always resolves, see <see cref="ChooseEstablishing"/>.
        /// </summary>
        bool Choose(List<BattleShot> candidates, out BattleShot shot, out CameraPose pose)
        {
            if (candidates[0].Kind == BattleShotKind.Establishing) return ChooseEstablishing(candidates, out shot, out pose);
            string rejected = "";
            for (int i = 0; i < candidates.Count; i++)
            {
                var candidate = candidates[i];
                pose = Resolve(candidate, out bool ok);
                if (ok) { shot = candidate; LastChoice = candidate.Kind + "#" + i + rejected; return true; }
                rejected += " #" + i + ":" + _reason;
            }
            shot = candidates[0]; pose = default;
            LastChoice = candidates[0].Kind + " -> establishing" + rejected;
            return false;
        }

        /// <summary>
        /// S0 search: the first candidate that fits every living unit and clears the arena. When the layout cannot be
        /// satisfied (every candidate fails), it says so in <see cref="LastChoice"/> and takes the first best-effort pose
        /// that is still inside the arena, else the designed home pose (inside by construction), never a blocked one.
        /// </summary>
        bool ChooseEstablishing(List<BattleShot> candidates, out BattleShot shot, out CameraPose pose)
        {
            string rejected = "";
            var poses = new CameraPose[candidates.Count];
            var blocked = new bool[candidates.Count];
            for (int i = 0; i < candidates.Count; i++)
            {
                poses[i] = Resolve(candidates[i], out bool ok);
                if (ok) { shot = candidates[i]; pose = poses[i]; LastChoice = "Establishing#" + i + rejected; return true; }
                rejected += " #" + i + ":" + _reason;
                blocked[i] = _lastBlocked || (candidates[i].CheckOcclusion && Blocked(poses[i].Position));
            }
            for (int i = 0; i < candidates.Count; i++)
                if (!blocked[i]) { shot = candidates[i]; pose = poses[i]; LastChoice = "Establishing unsatisfiable, best effort #" + i + rejected; return true; }
            shot = candidates[0];
            Vector3 axis = shot.Look - shot.Position;
            pose = new CameraPose(shot.Position, Quaternion.LookRotation(axis.sqrMagnitude > 1e-4f ? axis.normalized : _arena.forward, Vector3.up), shot.Fov);
            LastChoice = "Establishing unsatisfiable, designed home" + rejected;
            return true;
        }

        /// <summary>Cuts straight to <paramref name="shot"/> (no blend).</summary>
        public void Cut(BattleShot shot) { if (shot != null) Cut(new List<BattleShot> { shot }); }

        /// <summary>Cuts straight to the first valid candidate (the establishing search when none is).</summary>
        public void Cut(List<BattleShot> candidates)
        {
            if (_restored || candidates == null || candidates.Count == 0) return;
            if (!Choose(candidates, out var shot, out var pose)) { candidates = EstablishingShots(); Choose(candidates, out shot, out pose); }
            _candidates = candidates;
            Begin(shot, pose, 0f, CameraEase.Linear);
            _base = Target(0f);
            Apply(_base, 0f);
        }

        void Begin(BattleShot shot, CameraPose pose, float blend, CameraEase ease)
        {
            _from = _base; _to = pose; _shot = shot; _ease = ease;
            _blendElapsed = 0f; _blendLength = Mathf.Max(0f, blend); _shotElapsed = 0f;
            _resolvedVersion = _hud != null ? _hud.OcclusionVersion : 0;
            _signature = LivingSignature(); _trackMiss = 0f;
        }

        /// <summary>Identity of the living cast (ids and models); changes on summon, death and revive.</summary>
        int LivingSignature()
        {
            unchecked
            {
                int hash = 17;
                foreach (var unit in _units)
                    if (unit.Alive && unit.Model != null) hash = hash * 31 + unit.Id.GetHashCode() + unit.Model.GetInstanceID() * 7;
                return hash;
            }
        }

        /// <summary>
        /// Per-frame update. <paramref name="speed"/> is the battle-speed setting (scales blends, pushes and orbits);
        /// <paramref name="reduced"/> forces the establishing shot and drops the shake / punch layers.
        /// </summary>
        public void Tick(float speed, bool reduced)
        {
            if (_restored) return;
            _speed = Mathf.Max(.1f, speed);
            if (reduced != _reduced)
            {
                _reduced = reduced;
                if (reduced) { _trauma = 0f; _punch = 0f; Cut(EstablishingShots()); }
            }
            float dt = Time.unscaledDeltaTime, scaled = dt * _speed;
            _blendElapsed += scaled; _shotElapsed += scaled;
            // HUD rectangles moved (menu opened, fan resized, auto notice) or the living cast changed (summon, death,
            // revive): re-fit the same request with hysteresis and blend briefly from the current pose (never a restart).
            int signature = LivingSignature();
            bool hudMoved = _hud != null && _hud.OcclusionVersion != _resolvedVersion;
            if (_shot != null && _shot.Fit && (hudMoved || signature != _signature))
            {
                if (_hud != null) _resolvedVersion = _hud.OcclusionVersion;
                _signature = signature;
                var candidates = _candidates ?? new List<BattleShot> { _shot };
                if (!Choose(candidates, out var chosen, out var pose)) { _shot = null; PlayFirst(EstablishingShots()); }
                else if (chosen != _shot || Differs(pose, _to))
                {
                    _shot = chosen;
                    _blendLength = _reduced ? 0f : Mathf.Max(RefitBlend, _blendLength - _blendElapsed);
                    _from = _base; _to = pose; _blendElapsed = 0f;
                    _ease = CameraEase.OutCubic;
                }
            }
            // A moving S6 actor must stay in frame; if it leaves for longer than the grace, hold the establishing shot.
            if (_shot != null && _shot.Track != null && !Blending && !_reduced)
            {
                var actor = _shot.Track;
                if (actor.Alive && actor.Model != null && !InView(actor)) _trackMiss += scaled; else _trackMiss = 0f;
                if (_trackMiss > TrackGrace) { LastChoice = "EnemyTurn lost its actor -> establishing"; PlayFirst(EstablishingShots()); }
            }
            var target = Target(_shotElapsed);
            float t = _blendLength <= 0f ? 1f : Mathf.Clamp01(_blendElapsed / _blendLength);
            float k = Ease(_ease, t);
            _base = new CameraPose(Vector3.LerpUnclamped(_from.Position, target.Position, k),
                Quaternion.SlerpUnclamped(_from.Rotation, target.Rotation, k), Mathf.LerpUnclamped(_from.Fov, target.Fov, k));
            Apply(_base, dt);
        }

        /// <summary>True when the unit's live body projects inside the screen (small tolerance) in front of the camera.</summary>
        bool InView(BattleDisplayUnit unit)
        {
            if (!BodyBox(unit, out var box, atHome: false)) return true;
            Quaternion inverse = Quaternion.Inverse(_base.Rotation);
            float tanV = Mathf.Tan(_base.Fov * .5f * Mathf.Deg2Rad), tanH = tanV * Mathf.Max(.1f, _camera.aspect);
            Vector3 lo = box.min, hi = box.max;
            for (int k = 0; k < 8; k++)
            {
                var c = inverse * (new Vector3((k & 1) == 0 ? lo.x : hi.x, (k & 2) == 0 ? lo.y : hi.y, (k & 4) == 0 ? lo.z : hi.z) - _base.Position);
                if (c.z < _camera.nearClipPlane) return false;
                if (Mathf.Abs(c.x / c.z) > tanH * 1.04f || Mathf.Abs(c.y / c.z) > tanV * 1.04f) return false;
            }
            return true;
        }

        /// <summary>Puts the camera back where the battle found it.</summary>
        public void Restore()
        {
            if (_restored) return;
            _restored = true;
            if (_camera != null) { _camera.transform.SetPositionAndRotation(_oldPosition, _oldRotation); _camera.fieldOfView = _oldFov; }
        }

        /// <summary>Shot target at <paramref name="elapsed"/> battle seconds into the shot (orbit and arrival push applied).</summary>
        CameraPose Target(float elapsed)
        {
            var pose = _to;
            if (_shot == null) return pose;
            if (_shot.Orbit != 0f && _shot.OrbitTime > 0f && !_reduced)
            {
                float u = Ease(CameraEase.InOutSine, Mathf.Clamp01(elapsed / _shot.OrbitTime));
                var spin = Quaternion.AngleAxis(Mathf.Lerp(-.5f, .5f, u) * _shot.Orbit, _arena.up);
                pose.Position = _shot.OrbitPivot + spin * (pose.Position - _shot.OrbitPivot);
                pose.Rotation = spin * pose.Rotation;
            }
            if (_shot.Push != 0f && !_reduced)
            {
                // The fit targets the pushed-in FOV, so the push never breaks framing; arrival starts wider by |Push|.
                float u = _shot.PushTime <= 0f ? 1f : Mathf.Clamp01((elapsed - _blendLength) / _shot.PushTime);
                pose.Fov = pose.Fov - _shot.Push * (1f - Ease(CameraEase.OutCubic, u));
            }
            return pose;
        }

        void Apply(CameraPose pose, float dt)
        {
            Vector3 position = pose.Position;
            Quaternion view = pose.Rotation;
            if (!_reduced && _trauma > .001f)
            {
                // Camera-relative Perlin trauma; squared so light knocks stay subtle and big ones read.
                float shake = _trauma * _trauma, time = Time.unscaledTime * ShakeFrequency;
                float x = Mathf.PerlinNoise(time, .5f) * 2 - 1, y = Mathf.PerlinNoise(.5f, time + 37f) * 2 - 1;
                float roll = Mathf.PerlinNoise(time + 71f, 13.5f) * 2 - 1;
                position += view * new Vector3(x, y, 0) * (shake * ShakeOffset);
                view *= Quaternion.Euler(0, 0, roll * ShakeRoll * shake);
                _trauma = Mathf.MoveTowards(_trauma, 0, dt * TraumaDecay);
            }
            else if (_reduced) _trauma = 0f;
            _camera.transform.SetPositionAndRotation(position, view);
            _punch = _reduced ? 0f : Mathf.Lerp(_punch, 0, 1 - Mathf.Exp(-dt * PunchRecover));
            _camera.fieldOfView = pose.Fov + _punch;
        }

        static bool Differs(CameraPose a, CameraPose b) =>
            (a.Position - b.Position).sqrMagnitude > RefitMove * RefitMove || Quaternion.Angle(a.Rotation, b.Rotation) > RefitAngle || Mathf.Abs(a.Fov - b.Fov) > RefitFov;

        public static float Ease(CameraEase ease, float t)
        {
            t = Mathf.Clamp01(t);
            switch (ease)
            {
                case CameraEase.OutCubic: { float u = 1f - t; return 1f - u * u * u; }
                case CameraEase.InOutCubic: return t < .5f ? 4f * t * t * t : 1f - Mathf.Pow(-2f * t + 2f, 3f) * .5f;
                case CameraEase.OutExpo: return t >= 1f ? 1f : 1f - Mathf.Pow(2f, -10f * t);
                case CameraEase.InOutSine: return -(Mathf.Cos(Mathf.PI * t) - 1f) * .5f;
                default: return t;
            }
        }

        // ---- shot builders -----------------------------------------------------------------------------------------

        /// <summary>S0 candidates (one request key): every living unit, re-read at each fit.</summary>
        List<BattleShot> EstablishingShots()
        {
            var shots = new List<BattleShot>(HomeCandidates.Length);
            foreach (var home in HomeCandidates)
                shots.Add(new BattleShot
                {
                    Kind = BattleShotKind.Establishing, Key = "establishing", Position = _arena.TransformPoint(home.Position),
                    Look = _arena.TransformPoint(home.Aim), Fov = home.Fov, Blend = HomeBlend, Ease = CameraEase.InOutCubic,
                    MinDolly = .8f, MaxDolly = 2.2f, AllLiving = true
                });
            return shots;
        }

        List<BattleShot> CommandShots(BattleDisplayUnit hero)
        {
            Vector3 group = Vector3.zero; int count = 0;
            var enemies = new List<BattleDisplayUnit>();
            foreach (var unit in _units)
                if (unit.Side != hero.Side && unit.Alive && unit.Model != null) { group += Local(unit.Home); count++; enemies.Add(unit); }
            group = count > 0 ? group / count : new Vector3(0f, 0f, 3f);
            var shots = new List<BattleShot>();
            foreach (var offset in CommandOffsets)
            {
                var shot = NewShot(BattleShotKind.Command, "command:" + hero.Id, CommandFov, CommandBlend, CameraEase.OutCubic);
                shot.Push = CommandPush; shot.PushTime = CommandPushTime;
                shot.Required.Add(hero); shot.Required.AddRange(enemies);
                shot.Look = _arena.TransformPoint(new Vector3(group.x, EnemyGroupHeight, group.z));
                shot.Position = _arena.TransformPoint(Local(hero.Home) + offset);
                shots.Add(shot);
            }
            return shots;
        }

        // ---- framing -----------------------------------------------------------------------------------------------

        /// <summary>
        /// Fits <paramref name="shot"/>: dollies along its view axis (and re-aims so the subjects sit centred in the
        /// HUD-free viewport) until every required body fits, widens the FOV in 2° steps up to <see cref="BattleShot.MaxWiden"/>,
        /// and validates against arena occlusion. <paramref name="ok"/> is false when no fitted pose works.
        /// </summary>
        CameraPose Resolve(BattleShot shot, out bool ok)
        {
            ok = true; _reason = ""; _lastBlocked = false;
            if (shot.AllLiving)
            {
                shot.Required.Clear();
                foreach (var unit in _units) if (unit.Alive && unit.Model != null) shot.Required.Add(unit);
            }
            Vector3 axis = shot.Look - shot.Position;
            if (axis.sqrMagnitude < 1e-4f) axis = _arena.forward;
            var designed = new CameraPose(shot.Position, Roll(Quaternion.LookRotation(axis.normalized, Vector3.up), shot.Dutch), shot.Fov);
            if (!shot.Fit) return designed;
            _boxes.Clear();
            foreach (var unit in shot.Required)
                if (unit != null && unit.Alive && unit.Model != null && BodyBox(unit, out var box))
                {
                    if (shot.Pad > 0f) box.Expand(new Vector3(shot.Pad * 2f, 0f, shot.Pad * 2f));
                    _boxes.Add(box);
                }
            foreach (var extra in shot.Extra) _boxes.Add(extra);
            if (_boxes.Count == 0) return designed;
            Rect rect = FitRect(shot.ExtraInset);
            if (shot.MaxViewportY < rect.yMax && shot.MaxViewportY - rect.yMin > .2f) rect.yMax = shot.MaxViewportY;
            CameraPose best = designed; bool any = false;
            for (float widen = 0f; widen <= shot.MaxWiden + .01f; widen += 2f)
            {
                if (!TryFit(shot, rect, shot.Fov + widen, out var pose, out bool fits)) continue;
                best = pose; any = true;
                if (!fits) continue;
                if (shot.Clearance && !Clear(shot, pose)) { ok = false; return pose; }
                if (shot.CheckOcclusion && Blocked(pose.Position)) { ok = false; _reason = "arena"; _lastBlocked = true; return pose; }
                return pose;
            }
            ok = false; _reason = "fit";
            return any ? best : designed;
        }

        /// <summary>HUD-free viewport (normalized), inset by the framing margins.</summary>
        Rect FitRect(float extraInset)
        {
            Rect free = _hud != null ? _hud.FreeViewport : new Rect(0f, 0f, 1f, 1f);
            if (free.width < .2f || free.height < .2f) free = new Rect(0f, 0f, 1f, 1f);
            float ix = InsetX + extraInset;
            return Rect.MinMaxRect(free.xMin + ix, free.yMin + InsetY, free.xMax - ix, free.yMax - InsetY);
        }

        bool TryFit(BattleShot shot, Rect rect, float fov, out CameraPose pose, out bool fits)
        {
            fits = false;
            Vector3 axis = (shot.Look - shot.Position).normalized;
            float designed = Mathf.Max(.5f, Vector3.Distance(shot.Look, shot.Position));
            float maxD = MaxInside(shot.Look, axis, designed * shot.MaxDolly), minD = Mathf.Min(designed * shot.MinDolly, maxD);
            float d = Mathf.Clamp(designed, minD, maxD);
            float aspect = Mathf.Max(.1f, _camera.aspect), tanV = Mathf.Tan(fov * .5f * Mathf.Deg2Rad), tanH = tanV * aspect;
            float rx0 = (2f * rect.xMin - 1f) * tanH, rx1 = (2f * rect.xMax - 1f) * tanH, ry0 = (2f * rect.yMin - 1f) * tanV, ry1 = (2f * rect.yMax - 1f) * tanV;
            Vector3 rectCentre = new Vector3((rx0 + rx1) * .5f, (ry0 + ry1) * .5f, 1f);
            Quaternion q = Roll(Quaternion.LookRotation(axis, Vector3.up), shot.Dutch);
            pose = new CameraPose(shot.Position, q, fov);
            for (int i = 0; i < FitIterations; i++)
            {
                Vector3 p = shot.Look - axis * d;
                Extents e = default;
                for (int j = 0; j < CentreIterations; j++)
                {
                    e = Measure(p, q);
                    if (!e.Valid) break;
                    // Re-aim so the subjects' projected centre lands on the rect centre (no roll beyond the dutch).
                    Vector3 want = q * new Vector3((e.X0 + e.X1) * .5f, (e.Y0 + e.Y1) * .5f, 1f);
                    Vector3 have = q * rectCentre;
                    var turned = Quaternion.FromToRotation(have, want) * q;
                    q = Roll(Quaternion.LookRotation(turned * Vector3.forward, Vector3.up), shot.Dutch);
                }
                e = Measure(p, q);
                pose = new CameraPose(p, q, fov);
                if (!e.Valid)
                {
                    // A body crosses the near plane or sits behind the camera: back off.
                    if (d >= maxD - 1e-3f) return true;
                    d = Mathf.Min(maxD, d * 1.25f + .25f);
                    continue;
                }
                float ratio = Mathf.Max((e.X1 - e.X0) / Mathf.Max(1e-4f, rx1 - rx0), (e.Y1 - e.Y0) / Mathf.Max(1e-4f, ry1 - ry0));
                bool inside = e.X0 >= rx0 - 1e-4f && e.X1 <= rx1 + 1e-4f && e.Y0 >= ry0 - 1e-4f && e.Y1 <= ry1 + 1e-4f;
                if (inside && (ratio >= AcceptFill || d <= minD + 1e-3f)) { fits = true; return true; }
                // Apparent size ~ 1 / depth: move so the mean depth scales by ratio / fill aim.
                float next = Mathf.Clamp(d + e.Depth * (ratio / FillAim - 1f), minD, maxD);
                if (Mathf.Abs(next - d) < .005f) { fits = inside; return true; }
                d = next;
            }
            var last = Measure(pose.Position, pose.Rotation);
            fits = last.Valid && last.X0 >= rx0 - 1e-3f && last.X1 <= rx1 + 1e-3f && last.Y0 >= ry0 - 1e-3f && last.Y1 <= ry1 + 1e-3f;
            return true;
        }

        /// <summary>Longest dolly (from the look point back along the axis) that keeps the camera inside the arena interior.</summary>
        float MaxInside(Vector3 look, Vector3 axis, float limit)
        {
            if (_geometry == null) return limit;
            if (!_interiorKnown) LearnInterior();
            bool Inside(float d)
            {
                Vector3 p = look - axis * d, flat = p - _interiorCentre; flat.y = 0f;
                return flat.magnitude <= _interiorRadius && p.y <= _ceiling;
            }
            if (Inside(limit)) return limit;
            float lo = 0f, hi = limit;
            for (int i = 0; i < 12; i++) { float mid = (lo + hi) * .5f; if (Inside(mid)) lo = mid; else hi = mid; }
            return Mathf.Max(.5f, lo);
        }

        struct Extents { public bool Valid; public float X0, X1, Y0, Y1, Depth; }

        /// <summary>Projected eight-corner extents of the fitting boxes in tangent space of a camera at p / q.</summary>
        Extents Measure(Vector3 p, Quaternion q)
        {
            var e = new Extents { Valid = true, X0 = float.MaxValue, Y0 = float.MaxValue, X1 = float.MinValue, Y1 = float.MinValue };
            Quaternion inverse = Quaternion.Inverse(q);
            float near = _camera.nearClipPlane + .15f, depth = 0f; int n = 0;
            foreach (var box in _boxes)
            {
                Vector3 lo = box.min, hi = box.max;
                for (int k = 0; k < 8; k++)
                {
                    var c = inverse * (new Vector3((k & 1) == 0 ? lo.x : hi.x, (k & 2) == 0 ? lo.y : hi.y, (k & 4) == 0 ? lo.z : hi.z) - p);
                    if (c.z < near) { e.Valid = false; return e; }
                    float x = c.x / c.z, y = c.y / c.z;
                    if (x < e.X0) e.X0 = x; if (x > e.X1) e.X1 = x;
                    if (y < e.Y0) e.Y0 = y; if (y > e.Y1) e.Y1 = y;
                    depth += c.z; n++;
                }
            }
            e.Depth = n > 0 ? depth / n : 1f;
            return e;
        }

        static Quaternion Roll(Quaternion q, float dutch) => dutch == 0f ? q : q * Quaternion.Euler(0f, 0f, dutch);

        // ---- subjects ----------------------------------------------------------------------------------------------

        sealed class BodyParts
        {
            public readonly List<Transform> Bones = new List<Transform>();
            public readonly List<Renderer> Rigid = new List<Renderer>();
            public int Scanned = -1000;
        }

        /// <summary>
        /// World box of a unit's body at its home mark: the padded animated skeleton plus rigid meshes (weapons, flyers,
        /// blobs), the same measure the HUD uses for its tags. Measured at home so action poses never shift a shot.
        /// </summary>
        bool BodyBox(BattleDisplayUnit unit, out Bounds box, bool atHome = true)
        {
            var model = unit.Model;
            box = default;
            if (!_bodies.TryGetValue(model, out var parts)) { parts = new BodyParts(); _bodies.Add(model, parts); }
            if (Time.frameCount - parts.Scanned > 40) Scan(model, parts);
            Vector3 lo = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue), hi = -lo;
            bool any = false;
            if (parts.Bones.Count > 0)
            {
                Vector3 blo = lo, bhi = hi;
                foreach (var bone in parts.Bones)
                {
                    if (bone == null) continue;
                    Vector3 p = bone.position; blo = Vector3.Min(blo, p); bhi = Vector3.Max(bhi, p);
                }
                if (blo.x <= bhi.x)
                {
                    float h = Mathf.Max(.5f, model.Height);
                    blo -= new Vector3(h * .14f, h * .08f, h * .14f); bhi += new Vector3(h * .14f, h * .2f, h * .14f);
                    lo = Vector3.Min(lo, blo); hi = Vector3.Max(hi, bhi); any = true;
                }
            }
            foreach (var r in parts.Rigid)
            {
                if (r == null || !r.enabled || !r.gameObject.activeInHierarchy) continue;
                var b = r.bounds; lo = Vector3.Min(lo, b.min); hi = Vector3.Max(hi, b.max); any = true;
            }
            if (!any)
            {
                Vector3 root = model.transform.position;
                lo = root - new Vector3(model.Radius, 0f, model.Radius); hi = root + new Vector3(model.Radius, model.Height + .15f, model.Radius);
            }
            box = new Bounds((lo + hi) * .5f, hi - lo);
            if (atHome) box.center += unit.Home - model.transform.position;
            return true;
        }

        static void Scan(CharacterModel model, BodyParts parts)
        {
            parts.Scanned = Time.frameCount; parts.Bones.Clear(); parts.Rigid.Clear();
            foreach (var r in model.GetComponentsInChildren<Renderer>(false))
            {
                if (r is SkinnedMeshRenderer smr)
                {
                    foreach (var bone in smr.bones) if (bone != null && !parts.Bones.Contains(bone)) parts.Bones.Add(bone);
                }
                else if (r is MeshRenderer) parts.Rigid.Add(r);
            }
        }

        Vector3 Local(Vector3 world) => _arena.InverseTransformPoint(world);
        static Vector3 Chest(BattleDisplayUnit unit) => unit.Home + Vector3.up * (unit.Model.Height * .6f);

        /// <summary>
        /// Close-shot clearance at <paramref name="pose"/> (bodies at their home marks): a body nearer the camera may cover
        /// at most <see cref="MaxCover"/> of a required body, nothing may cross the near plane, and no bystander inside the
        /// frame may read taller than <see cref="MaxBystander"/> × the foreground subject.
        /// </summary>
        bool Clear(BattleShot shot, CameraPose pose)
        {
            _all.Clear(); _allRequired.Clear();
            int lead = -1;
            var first = shot.Required.Count > 0 ? shot.Required[0] : null;
            foreach (var unit in _units)
            {
                if (!unit.Alive || unit.Model == null || unit == shot.Ignore || !BodyBox(unit, out var box)) continue;
                if (unit == first) lead = _all.Count;
                _all.Add(box); _allRequired.Add(shot.Required.Contains(unit));
            }
            // Extra boxes (a melee enemy at its strike mark) can hide a required body, but are never bystanders.
            int units = _all.Count;
            foreach (var extra in shot.Extra) { _all.Add(extra); _allRequired.Add(false); }
            Quaternion inverse = Quaternion.Inverse(pose.Rotation);
            float aspect = Mathf.Max(.1f, _camera.aspect), tanV = Mathf.Tan(pose.Fov * .5f * Mathf.Deg2Rad), tanH = tanV * aspect;
            var frame = Rect.MinMaxRect(-tanH, -tanV, tanH, tanV);
            int n = _all.Count;
            var rects = new Rect[n]; var depth = new float[n]; var visible = new bool[n];
            float near = _camera.nearClipPlane + .05f;
            for (int i = 0; i < n; i++)
            {
                Vector3 lo = _all[i].min, hi = _all[i].max;
                float x0 = float.MaxValue, y0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue; int behind = 0;
                for (int k = 0; k < 8; k++)
                {
                    var c = inverse * (new Vector3((k & 1) == 0 ? lo.x : hi.x, (k & 2) == 0 ? lo.y : hi.y, (k & 4) == 0 ? lo.z : hi.z) - pose.Position);
                    if (c.z < near) { behind++; continue; }
                    float x = c.x / c.z, y = c.y / c.z;
                    if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
                }
                // A bystander straddling the near plane is a body right against the lens.
                if (behind > 0 && behind < 8) { _reason = "lens"; return false; }
                visible[i] = behind == 0;
                depth[i] = (inverse * (_all[i].center - pose.Position)).z;
                rects[i] = visible[i] ? Rect.MinMaxRect(x0, y0, x1, y1) : default;
            }
            // The foreground subject is the shot's first required unit.
            float foreground = lead >= 0 && visible[lead] ? rects[lead].height : 0f, limit = MaxBystander;
            if (shot.BystanderVsTargets)
            {
                foreground = 0f; limit = MaxBystanderVsTargets;
                for (int i = 0; i < n; i++) if (_allRequired[i] && i != lead && visible[i]) foreground = Mathf.Max(foreground, rects[i].height);
            }
            for (int i = 0; i < n; i++)
            {
                if (!visible[i]) continue;
                if (_allRequired[i])
                {
                    // Only the foreground subject or a bystander can hide a required body; a group of required bodies
                    // (enemies in S1, heroes in S6) may stagger in depth. Boxes are padded, so compare their cores.
                    var core = Shrink(rects[i]);
                    float area = Mathf.Max(1e-6f, core.width * core.height);
                    for (int j = 0; j < n; j++)
                        if (j != i && visible[j] && (j == lead || !_allRequired[j] || j >= units) && depth[j] < depth[i] - .3f && Overlap(core, Shrink(rects[j])) / area > MaxCover)
                        { _reason = "cover"; return false; }
                }
                else if (i < units && foreground > 0f && rects[i].height > foreground * limit)
                {
                    float area = Mathf.Max(1e-6f, rects[i].width * rects[i].height);
                    if (Overlap(rects[i], frame) / area > .25f) { _reason = "bystander"; return false; }
                }
            }
            return true;
        }

        /// <summary>Body core: the padded body rect without 15 % on each side.</summary>
        static Rect Shrink(Rect r) => new Rect(r.x + r.width * .15f, r.y + r.height * .15f, r.width * .7f, r.height * .7f);

        static float Overlap(Rect a, Rect b)
        {
            float w = Mathf.Min(a.xMax, b.xMax) - Mathf.Max(a.xMin, b.xMin), h = Mathf.Min(a.yMax, b.yMax) - Mathf.Max(a.yMin, b.yMin);
            return w > 0f && h > 0f ? w * h : 0f;
        }

        // ---- arena occlusion ---------------------------------------------------------------------------------------

        /// <summary>
        /// True when the camera at <paramref name="camera"/> sits outside the arena interior (wall ring, ceiling) or arena
        /// geometry stands between it and a required body: colliders (sphere cast) and compact props (renderer boxes).
        /// </summary>
        bool Blocked(Vector3 camera)
        {
            if (_geometry == null) return false;
            if (!_interiorKnown) LearnInterior();
            Vector3 flat = camera - _interiorCentre; flat.y = 0f;
            if (flat.magnitude > _interiorRadius || camera.y > _ceiling || camera.y < _geometry.position.y + .25f) return true;
            foreach (var prop in _props)
                if (prop.Contains(camera)) return true;
            foreach (var box in _boxes)
            {
                Vector3 from = box.center, to = camera - from;
                float length = to.magnitude;
                if (length < .01f) continue;
                var ray = new Ray(from, to / length);
                foreach (var prop in _props)
                    if (prop.IntersectRay(ray, out float distance) && distance < length && !prop.Contains(from)) return true;
                var hits = Physics.SphereCastAll(ray, .15f, length, ~0, QueryTriggerInteraction.Ignore);
                foreach (var hit in hits)
                    if (hit.collider != null && hit.transform.IsChildOf(_geometry) && !hit.collider.name.StartsWith("Col_Ground", StringComparison.Ordinal)) return true;
            }
            return false;
        }

        /// <summary>
        /// Arena interior from its renderers: the wall ring (backdrop) bounds give the radius, the ceiling its height.
        /// Compact standalone props (benches, bins, crates) become occluder boxes; the merged shells are too coarse for that.
        /// </summary>
        void LearnInterior()
        {
            _interiorKnown = true; _props.Clear();
            _interiorCentre = _geometry.position; _interiorRadius = float.PositiveInfinity; _ceiling = float.PositiveInfinity;
            foreach (var r in _geometry.GetComponentsInChildren<Renderer>(false))
            {
                if (r is ParticleSystemRenderer || !r.enabled) continue;
                string name = r.name;
                var b = r.bounds;
                if (name.Contains("backdrop"))
                {
                    _interiorCentre = new Vector3(b.center.x, _geometry.position.y, b.center.z);
                    _interiorRadius = Mathf.Min(_interiorRadius, Mathf.Min(b.extents.x, b.extents.z) - 1.2f);
                }
                else if (name.Contains("ceiling")) _ceiling = Mathf.Min(_ceiling, b.min.y - .3f);
                else if (b.size.x < 3.5f && b.size.z < 3.5f && b.size.y > .3f)
                {
                    b.Expand(.2f);
                    _props.Add(b);
                }
            }
        }
    }
}
