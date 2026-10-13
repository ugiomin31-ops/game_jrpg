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
        /// <summary>Live boxes that may not hide a required body but need not be framed (S7: the attacker where it stands).</summary>
        public readonly List<Bounds> Occluders = new List<Bounds>();
        /// <summary>
        /// Bystander reference: false compares bystanders with the foreground subject (S1/S2: the hero); true with the
        /// tallest of the other required bodies (S6: the targeted heroes), so a nearer enemy never dominates a reverse angle.
        /// </summary>
        public bool BystanderVsTargets;
        /// <summary>
        /// Bystander size limit override (0 = the director default). S4's over-the-shoulder cast pose accepts a teammate at
        /// the caster's side reading a little larger than the caster, which is the shot's natural composition.
        /// </summary>
        public float BystanderLimit;
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
        /// <summary>
        /// Orbit sweeps (degrees) to try in order, with the side insets for the centre fit. Set: every resolve (first play
        /// and every re-fit) re-selects <see cref="Orbit"/> and <see cref="ExtraInset"/> from these, validating samples
        /// across the sweep; a trailing 0 means hold still.
        /// </summary>
        public float[] Sweeps, SweepInsets;
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
        /// <summary>
        /// S6 profile fallbacks: (distance beside the home-to-target line, height, shift back toward the enemy) from the
        /// line's midpoint, aimed at <see cref="EnemySideLook"/> above it. Ordered by how often each held a melee run in QA.
        /// </summary>
        static readonly Vector3[] EnemySideOffsets =
        {
            new Vector3(5.5f, 3.2f, 0f), new Vector3(4.5f, 3.2f, 0f), new Vector3(4.5f, 3.2f, 2f), new Vector3(5.5f, 3.2f, 2f),
            new Vector3(6.5f, 3.2f, 0f), new Vector3(6.5f, 2.2f, 0f), new Vector3(4.5f, 2.2f, 2f), new Vector3(5.5f, 2.2f, 0f)
        };
        const float EnemySideLook = .9f;
        /// <summary>S6 last resort: (side, height, distance behind the targets' centre, away from the enemy), aimed at <see cref="EnemyShoulderLook"/> over the line's midpoint.</summary>
        static readonly Vector3[] EnemyShoulderOffsets =
        {
            new Vector3(1.2f, 1.6f, 3.5f), new Vector3(-1.2f, 1.6f, 3.5f), new Vector3(1.2f, 2.4f, 3.5f), new Vector3(-1.2f, 2.4f, 3.5f),
            new Vector3(1.2f, 2.4f, 4.5f), new Vector3(-1.2f, 2.4f, 4.5f), new Vector3(2.4f, 1.6f, 2.5f), new Vector3(-2.4f, 1.6f, 2.5f)
        };
        const float EnemyShoulderLook = 1.2f;
        public const float EnemyFov = 40f, EnemyBlend = .35f;
        /// <summary>S3 strike follow: outside 3/4 track 4.2 m off the run line at 1.1 m.</summary>
        public const float StrikeOffset = 4.2f, StrikeTightSide = 2.4f, StrikeTightBack = 2.8f, StrikeHeight = 1.1f, StrikeFov = 38f, StrikeBlend = .2f, StrikePunch = -4f;
        /// <summary>S4 cast pose: low (0.9 m) behind the caster, 15° off its line to the targets.</summary>
        public const float CastAngle = 15f, CastHeight = .9f, CastBack = 2.4f, CastFov = 40f, CastBlend = .3f, CastBystander = 1.45f;
        /// <summary>S4 release: 0.18 s whip to the impact framing (projectile / area / support).</summary>
        public const float ImpactBack = 3.4f, ImpactHeight = 1.3f, ImpactFov = 36f, ImpactBlend = .18f, AreaBack = 7.5f, AreaHeight = 3.2f, AreaHighHeight = 4.4f, AreaFov = 42f, AreaSide = 5.5f, AreaSideBack = 1.5f, AreaQuarter = 2.6f;
        /// <summary>S5 cut-in push onto the caster: 0.22 s OutExpo to FOV 28 (dutch 8°, ultimate 12°).</summary>
        public const float CutInDistance = 1.5f, CutInFov = 28f, CutInBlend = .22f;
        /// <summary>S7 hit reaction: 0.3 s hold on the struck hero from the front.</summary>
        public const float HitFov = 34f, HitBlend = .15f, HitDistance = 2.4f, HitSide = 2.2f, HitHold = .3f;
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
        // The view's live roster. Concrete type on purpose: foreach uses the struct enumerator (LivingSignature runs per frame).
        readonly Dictionary<string, BattleDisplayUnit>.ValueCollection _units;
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
        /// <summary>Open-air arenas (a backdrop on some sides only): allowed camera distance per compass sector; null for a wall ring.</summary>
        float[] _sectorRadius;
        const int InteriorSectors = 24;
        /// <summary>
        /// Clearance kept from the wall ring / backdrop; the height band backdrop walls are measured in (its top drops to
        /// the ceiling cap where an overhead sheet covers the arena); near-horizontal sheets (|normal.y| at least
        /// <see cref="HorizontalNormal"/>) at or above <see cref="OverheadMinHeight"/> over the centre cap the camera,
        /// <see cref="CeilingClearance"/> below them. Walls are binned per degree.
        /// </summary>
        const float WallClearance = 1.2f, BackdropBandLow = .3f, BackdropBandHigh = 6f, HorizontalNormal = .9f, OverheadMinHeight = 3f, CeilingClearance = .3f;
        const int ProfileBins = 360;

        BattleShot _shot;
        List<BattleShot> _candidates;
        /// <summary>The request a hit-reaction hold interrupted (resumed by ResumeAfterHit).</summary>
        List<BattleShot> _held;
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

        public BattleCameraDirector(Camera camera, Transform arena, BattleHUD hud, Dictionary<string, BattleDisplayUnit>.ValueCollection units)
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
            // Profile two-shots across the whole home-to-target line, tried after the reverse angles. A camera behind a
            // melee strike mark has the enemy's home behind it, so those can never hold both ends of the run; seen from
            // the side, the run crosses the frame. The side facing the arena centre goes first (room to dolly back).
            Vector3 lineEnd = new Vector3(look.x, enemy.Home.y, look.z), line = lineEnd - enemy.Home;
            Vector3 mid = (enemy.Home + lineEnd) * .5f;
            line.y = 0f;
            Vector3 lineForward = line.sqrMagnitude > 1e-4f ? line.normalized : forward, lineRight = Vector3.Cross(Vector3.up, lineForward);
            Vector3 toCentre = _arena.position - mid; toCentre.y = 0f;
            float firstSide = Vector3.Dot(lineRight, toCentre) >= 0f ? 1f : -1f;
            foreach (var side in EnemySideOffsets)
                foreach (float sign in new[] { firstSide, -firstSide })
                {
                    var shot = NewShot(BattleShotKind.EnemyTurn, key, EnemyFov, EnemyBlend, CameraEase.OutCubic);
                    shot.BystanderVsTargets = true; shot.Pad = RecoilPad; shot.Track = enemy;
                    if (atMark.HasValue) { shot.Required.AddRange(aimed); shot.Extra.Add(atHome.Value); shot.Extra.Add(atMark.Value); shot.Ignore = enemy; }
                    else { shot.Required.Add(enemy); shot.Required.AddRange(aimed); }
                    shot.Position = mid + lineRight * (sign * side.x) + Vector3.up * side.y - lineForward * side.z;
                    shot.Look = mid + Vector3.up * EnemySideLook;
                    shots.Add(shot);
                }
            // Last, the reverse of the reverse: over the targeted heroes' shoulders toward the enemy. A boss-sized body
            // fills any frame built on its own side; from behind the heroes it looms over them for the whole charge.
            foreach (var offset in EnemyShoulderOffsets)
            {
                var shot = NewShot(BattleShotKind.EnemyTurn, key, EnemyFov, EnemyBlend, CameraEase.OutCubic);
                shot.BystanderVsTargets = true; shot.Pad = RecoilPad; shot.Track = enemy;
                if (atMark.HasValue) { shot.Required.AddRange(aimed); shot.Extra.Add(atHome.Value); shot.Extra.Add(atMark.Value); shot.Ignore = enemy; }
                else { shot.Required.Add(enemy); shot.Required.AddRange(aimed); }
                shot.Position = lineEnd + lineForward * offset.z + lineRight * offset.x + Vector3.up * offset.y;
                shot.Look = mid + Vector3.up * EnemyShoulderLook;
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
            // Sweep selection (25° -> 12° -> still) runs in Resolve, so HUD / roster re-fits re-test it too.
            shot.Sweeps = VictorySweeps; shot.SweepInsets = VictoryInsets;
            Play(shot);
            LastChoice += " orbit " + shot.Orbit;
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

        // ---- skill beats: S3 strike follow / S4 cast + impact whip / S5 cut-in push / S7 hit reaction -------------

        /// <summary>
        /// S3 strike follow (melee skills). An outside 3/4 track at 1.1 m, 4.2 m off the run line: the frame holds the
        /// actor at its home mark and at its strike mark (so, being convex, the whole run and the return) plus the target.
        /// The camera does not chase: the actor runs through a composed frame. Falls back to S0 when no side clears.
        /// </summary>
        public void StrikeFollow(BattleDisplayUnit actor, BattleDisplayUnit target, Vector3 strikeFrom)
        {
            if (actor == null || actor.Model == null || target == null || target.Model == null) { Establishing(); return; }
            if (!BodyBox(actor, out var body)) { Establishing(); return; }
            Bounds atHome = body, atMark = body;
            atMark.center += strikeFrom - actor.Home;
            Vector3 run = strikeFrom - actor.Home; run.y = 0f;
            run = run.sqrMagnitude > 1e-4f ? run.normalized : _arena.forward;
            Vector3 side = Vector3.Cross(Vector3.up, run);
            // Outside first: the side away from the arena centre line, so the rest of the party stays behind the action.
            float outside = Mathf.Sign(Vector3.Dot(Local(actor.Home), _arena.InverseTransformDirection(side))) >= 0f ? 1f : -1f;
            Vector3 mid = (actor.Home + strikeFrom) * .5f;
            Vector3 look = Vector3.Lerp(mid, target.Home, .35f) + Vector3.up * (target.Model.Height * .55f);
            var shots = new List<BattleShot>();
            // A rear 3/4 first: the run is foreshortened, so run, strike and target fit with the hero ~25 % larger than the
            // flat side-on track; the side-on track (4.2 m off the line) and a higher one remain as fallbacks.
            foreach (var (sign, off, height, back) in new[] {
                (outside, StrikeTightSide, StrikeHeight + .2f, StrikeTightBack), (-outside, StrikeTightSide, StrikeHeight + .2f, StrikeTightBack),
                // Wider rear 3/4 when the hero would hide the target from straight behind.
                (outside, StrikeTightSide + 1f, StrikeHeight + .3f, StrikeTightBack - 1f), (-outside, StrikeTightSide + 1f, StrikeHeight + .3f, StrikeTightBack - 1f),
                (outside, StrikeOffset, StrikeHeight, .6f), (-outside, StrikeOffset, StrikeHeight, .6f),
                (outside, StrikeOffset + 1.2f, StrikeHeight + 1f, .6f), (-outside, StrikeOffset + 1.2f, StrikeHeight + 1f, .6f) })
            {
                var shot = NewShot(BattleShotKind.StrikeFollow, "strike:" + actor.Id + ">" + target.Id, StrikeFov, StrikeBlend, CameraEase.OutCubic);
                shot.Required.Add(target); shot.Extra.Add(atHome); shot.Extra.Add(atMark);
                shot.Ignore = actor; shot.Track = actor; shot.BystanderVsTargets = true; shot.Pad = RecoilPad;
                shot.Position = mid + side * (sign * off) + Vector3.up * height - run * back;
                shot.Look = look;
                shots.Add(shot);
            }
            PlayFirst(shots);
        }

        /// <summary>How a skill is staged after its cast pose (from presentation data, not per skill).</summary>
        public enum CastStyle { Projectile, Area, Support }

        /// <summary>
        /// S4. <paramref name="release"/> false: the cast pose, low (0.9 m) behind the caster and 15° off its line to the
        /// targets, caster and targets in frame. True: a quick whip (0.18 s) to the impact framing: the target and one
        /// neighbour from the caster's side (projectile), the whole group from higher up (area), or the healed / buffed
        /// allies from the front (support).
        /// </summary>
        public void CastShot(BattleDisplayUnit actor, IReadOnlyList<BattleDisplayUnit> targets, bool release, CastStyle style)
        {
            if (actor == null || actor.Model == null) { Establishing(); return; }
            // Intended targets are kept even while fallen (a revive's ally): the fit skips the fallen at every resolve, and a
            // re-fit after the revive frames them. With no living target a candidate fails and the next one (support: the
            // caster too) or S0 takes over.
            var aimed = new List<BattleDisplayUnit>();
            Vector3 centre = Vector3.zero;
            if (targets != null)
                foreach (var t in targets) if (t != null && t.Model != null) { aimed.Add(t); centre += t.Home; }
            if (aimed.Count == 0) { aimed.Add(actor); centre = actor.Home; }
            centre /= aimed.Count;
            string ids = ""; foreach (var t in aimed) ids += ">" + t.Id;
            Vector3 toTargets = centre - actor.Home; toTargets.y = 0f;
            toTargets = toTargets.sqrMagnitude > 1e-4f ? toTargets.normalized : actor.Facing * Vector3.forward;
            var shots = new List<BattleShot>();
            if (!release)
            {
                Vector3 look = centre + Vector3.up * .9f;
                // Then tighter over-the-shoulder variants: a caster with teammates on both sides (an archer mid-line) keeps
                // them outside the frame instead of losing the cast pose to a larger bystander.
                foreach (var (angle, height, back) in new[] { (CastAngle, CastHeight, CastBack), (-CastAngle, CastHeight, CastBack), (CastAngle, CastHeight + .8f, CastBack + .6f), (-CastAngle, CastHeight + .8f, CastBack + .6f),
                    (CastAngle * .6f, CastHeight + .3f, CastBack * .7f), (-CastAngle * .6f, CastHeight + .3f, CastBack * .7f), (0f, CastHeight + .5f, CastBack * .6f) })
                {
                    var shot = NewShot(BattleShotKind.Cast, "cast:" + actor.Id + ids, CastFov, CastBlend, CameraEase.OutCubic);
                    shot.Required.Add(actor); shot.Required.AddRange(aimed); shot.BystanderLimit = CastBystander;
                    Vector3 behind = Quaternion.AngleAxis(angle, Vector3.up) * -toTargets;
                    shot.Position = actor.Home + behind * back + Vector3.up * height;
                    shot.Look = look;
                    shots.Add(shot);
                }
                PlayFirst(shots);
                return;
            }
            string key = "impact:" + actor.Id + ids;
            Vector3 toCaster = -toTargets, right = Vector3.Cross(Vector3.up, toCaster);
            switch (style)
            {
                case CastStyle.Support:
                    // Healed / buffed allies from the front (reverse angle, the S2 ally geometry); then the same angles with
                    // the caster held too, the safe framing while the allies are still down (a revive before its event).
                    // A higher copy of each angle, pulled in toward the party line, keeps an enemy behind the camera off the lens. Every pass
                    // keeps the aimed allies required, so a re-fit after a revive (living cast changed) reacquires them.
                    for (int pass = 0; pass < 2; pass++)
                        for (int far = 0; far < 2; far++)
                            foreach (var offset in AllyOffsets)
                            {
                                var shot = NewShot(BattleShotKind.Cast, key, TargetFov, ImpactBlend, CameraEase.OutCubic);
                                shot.Required.AddRange(aimed);
                                if (pass == 1 && !aimed.Contains(actor)) shot.Required.Add(actor);
                                shot.Position = _arena.TransformPoint(Local(centre) + (far == 0 ? offset : new Vector3(offset.x * 1.3f, offset.y + .7f, offset.z * .75f)));
                                shot.Look = centre + Vector3.up * .85f;
                                shots.Add(shot);
                            }
                    // Last resort before S0: from behind the caster toward the allies (the cast-pose geometry), caster held.
                    foreach (float angle in new[] { CastAngle, -CastAngle })
                    {
                        var shot = NewShot(BattleShotKind.Cast, key, CastFov, ImpactBlend, CameraEase.OutCubic);
                        shot.Required.AddRange(aimed);
                        if (!aimed.Contains(actor)) shot.Required.Add(actor);
                        shot.Position = actor.Home + Quaternion.AngleAxis(angle, Vector3.up) * -toTargets * (CastBack + .6f) + Vector3.up * (CastHeight + .9f);
                        shot.Look = centre + Vector3.up * .85f;
                        shots.Add(shot);
                    }
                    break;
                case CastStyle.Area:
                    // Elevated 3/4 from the caster's side of the target group, so the group spreads across the frame (a camera
                    // beside the group looks down the enemy line and stacks the targets behind each other); then the straighter
                    // view, and the side angles only as a last resort.
                    // The caster-side views sit high over the party line (AreaBack puts the camera behind it, not among it).
                    foreach (var (lateral, back, height) in new[] {
                        (AreaQuarter, AreaBack, AreaHighHeight), (-AreaQuarter, AreaBack, AreaHighHeight), (0f, AreaBack + 1f, AreaHighHeight + .8f),
                        (AreaSide, AreaSideBack, AreaHeight), (-AreaSide, AreaSideBack, AreaHeight) })
                    {
                        var shot = NewShot(BattleShotKind.Cast, key, AreaFov, ImpactBlend, CameraEase.OutCubic);
                        shot.Required.AddRange(aimed); shot.BystanderVsTargets = true;
                        shot.Position = centre + toCaster * back + right * lateral + Vector3.up * height;
                        shot.Look = centre + Vector3.up * .7f;
                        shots.Add(shot);
                    }
                    break;
                default:
                    // Target plus its nearest neighbour first, then the target alone.
                    BattleDisplayUnit neighbour = null; float best = float.MaxValue;
                    foreach (var unit in _units)
                    {
                        if (!unit.Alive || unit.Model == null || unit.Side != aimed[0].Side || aimed.Contains(unit)) continue;
                        float d = (unit.Home - aimed[0].Home).sqrMagnitude;
                        if (d < best) { best = d; neighbour = unit; }
                    }
                    for (int pass = neighbour != null ? 0 : 1; pass < 2; pass++)
                        foreach (float sign in new[] { 1f, -1f })
                        {
                            var shot = NewShot(BattleShotKind.Cast, key, ImpactFov, ImpactBlend, CameraEase.OutCubic);
                            shot.Required.AddRange(aimed);
                            if (pass == 0) shot.Required.Add(neighbour);
                            shot.BystanderVsTargets = true;
                            shot.Position = centre + toCaster * ImpactBack + right * (sign * 1.1f) + Vector3.up * ImpactHeight;
                            shot.Look = centre + Vector3.up * .8f;
                            shots.Add(shot);
                        }
                    break;
            }
            PlayFirst(shots);
        }

        /// <summary>
        /// S5 skill cut-in push: a fast push (0.22 s OutExpo) onto the caster's upper body from the front, FOV 28, dutch 8°
        /// (ultimate 12°). A deliberate close-up, so not fitted to the full body; it is still checked against the arena.
        /// Returns false (nothing played) in reduced motion or when the arena blocks it.
        /// </summary>
        public bool SkillCutIn(BattleDisplayUnit caster, int tier, bool ultimate)
        {
            if (_reduced || caster == null || caster.Model == null) return false;
            Vector3 forward = caster.Facing * Vector3.forward; forward.y = 0f; forward.Normalize();
            Vector3 right = Vector3.Cross(Vector3.up, forward);
            Vector3 chest = caster.Home + Vector3.up * (caster.Model.Height * .72f);
            var shot = new BattleShot
            {
                Kind = BattleShotKind.CutIn, Key = "cutin:" + caster.Id, Fit = false, CheckOcclusion = true,
                Position = chest + forward * CutInDistance + right * .35f + Vector3.up * .12f, Look = chest + Vector3.up * .05f,
                Fov = CutInFov, Dutch = ultimate ? 12f : 8f, Blend = CutInBlend, Ease = CameraEase.OutExpo
            };
            _boxes.Clear();
            if (BodyBox(caster, out var box)) _boxes.Add(box);
            if (Blocked(shot.Position)) return false;
            Play(shot);
            return true;
        }

        /// <summary>
        /// S7 hit reaction: a 0.3 s hold on a hero who took a big hit, from the front. <see cref="ResumeAfterHit"/> goes
        /// back to the shot that was playing. Returns false (nothing played) in reduced motion or when it does not clear.
        /// </summary>
        public bool HitReaction(BattleDisplayUnit target, BattleDisplayUnit attacker = null)
        {
            if (_reduced || target == null || target.Model == null || !target.Alive || target.Hp <= 0 || _shot == null || _shot.Kind == BattleShotKind.HitReaction) return false;
            var held = _candidates;
            Vector3 forward = target.Facing * Vector3.forward; forward.y = 0f; forward.Normalize();
            var shots = new List<BattleShot>();
            // Front 3/4 from the side away from the attacker: a melee enemy still standing at the hero sits beside them, not
            // in front of the lens. The attacker's live body may not hide the hero (occluder); then the straight front.
            Vector3 across = Vector3.Cross(Vector3.up, forward);
            float away = attacker != null && attacker.Model != null && Vector3.Dot(attacker.Model.transform.position - target.Home, across) > 0f ? -1f : 1f;
            Bounds? attackerBox = null;
            if (attacker != null && attacker.Model != null && BodyBox(attacker, out var live, atHome: false)) attackerBox = live;
            foreach (var (sign, side, front) in new[] { (away, HitSide, HitDistance * .6f), (-away, HitSide, HitDistance * .6f), (away, .7f, HitDistance), (-away, .7f, HitDistance) })
            {
                var shot = NewShot(BattleShotKind.HitReaction, "hit:" + target.Id, HitFov, HitBlend, CameraEase.OutCubic);
                shot.Required.Add(target); shot.Track = target; shot.Ignore = attacker;
                if (attackerBox.HasValue) shot.Occluders.Add(attackerBox.Value);
                shot.Position = target.Home + forward * front + across * (sign * side) + Vector3.up * 1.3f;
                shot.Look = target.Home + Vector3.up * (target.Model.Height * .6f);
                shots.Add(shot);
            }
            if (!Choose(shots, out var chosen, out var pose)) return false;
            _held = held;
            _candidates = shots;
            Begin(chosen, pose, HitBlend, CameraEase.OutCubic);
            return true;
        }

        /// <summary>Back to the shot that was playing before <see cref="HitReaction"/> (re-fitted, short blend).</summary>
        public void ResumeAfterHit()
        {
            if (_shot == null || _shot.Kind != BattleShotKind.HitReaction) return;
            var held = _held; _held = null;
            if (held == null || held.Count == 0) { PlayFirst(EstablishingShots()); return; }
            foreach (var shot in held) shot.Blend = HitBlend;
            _shot = null;
            PlayFirst(held);
        }

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
                string why = LastChoice;
                var fallback = EstablishingShots();
                foreach (var f in fallback) { f.Blend = candidates[0].Blend; f.Ease = candidates[0].Ease; }
                if (_shot != null && _shot.Key == fallback[0].Key) return;
                candidates = fallback;
                Choose(candidates, out shot, out pose);
                LastChoice = why + " => " + LastChoice;   // keep why the request fell back (diagnostics)
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
                // Resolve may re-select the active shot's orbit sweep (25° / 12° / still): a changed sweep moves the camera
                // even with the same centre pose, so it also blends from the current pose (the orbit clock keeps running).
                float orbit = _shot.Orbit;
                if (!Choose(candidates, out var chosen, out var pose))
                {
                    string why = "refit(" + (hudMoved ? "hud" : "cast") + "): " + LastChoice;
                    _shot = null; PlayFirst(EstablishingShots());
                    LastChoice = why + " => " + LastChoice;
                }
                else if (chosen != _shot || Differs(pose, _to) || !Mathf.Approximately(orbit, chosen.Orbit))
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
            if (shot.Sweeps == null || shot.Sweeps.Length == 0 || !shot.Fit) return ResolveFixed(shot, out ok);
            // Orbit shots: the first sweep / inset pair whose centre pose fits and whose sampled sweep still frames the
            // bodies and clears the arena; otherwise hold still with the first inset. The orbit clock is not touched here.
            var insets = shot.SweepInsets != null && shot.SweepInsets.Length > 0 ? shot.SweepInsets : new[] { shot.ExtraInset };
            foreach (float sweep in shot.Sweeps)
            {
                if (sweep <= 0f) break;
                foreach (float inset in insets)
                {
                    shot.ExtraInset = inset;
                    var pose = ResolveFixed(shot, out ok);
                    if (ok && OrbitHolds(shot, pose, sweep)) { shot.Orbit = sweep; return pose; }
                }
            }
            shot.Orbit = 0f; shot.ExtraInset = insets[0];
            return ResolveFixed(shot, out ok);
        }

        /// <summary>Fit of one fixed shot (no orbit selection): see <see cref="Resolve"/>.</summary>
        CameraPose ResolveFixed(BattleShot shot, out bool ok)
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
            if (_boxes.Count == 0)
            {
                // Nothing left to frame (every subject fallen): only the establishing shot may keep its designed pose; a
                // subject-dependent shot fails so the caller falls back to S0 (or its next candidate).
                if (shot.Kind == BattleShotKind.Establishing) return designed;
                ok = false; _reason = "no subjects";
                return designed;
            }
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
                Vector3 p = look - axis * d;
                return WithinInterior(p) && p.y <= _ceiling;
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
            int lead = -1, track = -1;
            var first = shot.Required.Count > 0 ? shot.Required[0] : null;
            foreach (var unit in _units)
            {
                if (!unit.Alive || unit.Model == null || unit == shot.Ignore || !BodyBox(unit, out var box)) continue;
                if (unit == first) lead = _all.Count;
                if (unit == shot.Track) track = _all.Count;
                _all.Add(box); _allRequired.Add(shot.Required.Contains(unit));
            }
            // Extra boxes (a melee enemy at its strike mark) can hide a required body, but are never bystanders.
            int units = _all.Count;
            foreach (var extra in shot.Extra) { _all.Add(extra); _allRequired.Add(false); }
            foreach (var occluder in shot.Occluders) { _all.Add(occluder); _allRequired.Add(false); }
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
            float foreground = lead >= 0 && visible[lead] ? rects[lead].height : 0f, limit = shot.BystanderLimit > 0f ? shot.BystanderLimit : MaxBystander;
            if (shot.BystanderVsTargets)
            {
                foreground = 0f; limit = MaxBystanderVsTargets;
                // Reference: the tallest required body other than the acting enemy (Track). A melee S6 holds only the
                // targeted heroes as required units, so the first of them must count too.
                for (int i = 0; i < n; i++) if (_allRequired[i] && i != track && visible[i]) foreground = Mathf.Max(foreground, rects[i].height);
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
            if (!WithinInterior(camera) || camera.y > _ceiling || camera.y < _geometry.position.y + .25f) return true;
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
        /// The merged props shell is one renderer, so its bounds say nothing about the single posts, machines and pillars inside it.
        /// Welded connected triangle groups of a readable shell give those objects their own boxes (same compact-prop rule as
        /// separate renderers); big connected groups (walls, floor trim) stay out. One-time cost per arena.
        /// </summary>
        void AddShellProps(MeshFilter filter)
        {
            var mesh = filter.sharedMesh;
            if (mesh == null || !mesh.isReadable) return;
            var local = mesh.vertices; var triangles = mesh.triangles;
            var toWorld = filter.transform.localToWorldMatrix;
            var parent = new int[local.Length]; var world = new Vector3[local.Length];
            var welded = new Dictionary<(int, int, int), int>(local.Length);
            for (int i = 0; i < local.Length; i++)
            {
                parent[i] = i; world[i] = toWorld.MultiplyPoint3x4(local[i]);
                var key = (Mathf.RoundToInt(world[i].x * 50f), Mathf.RoundToInt(world[i].y * 50f), Mathf.RoundToInt(world[i].z * 50f));
                if (welded.TryGetValue(key, out int first)) parent[i] = first; else welded.Add(key, i);
            }
            int Find(int i) { while (parent[i] != i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; }
            for (int t = 0; t + 2 < triangles.Length; t += 3)
            {
                int a = Find(triangles[t]), b = Find(triangles[t + 1]), c = Find(triangles[t + 2]);
                parent[b] = a; parent[Find(c)] = Find(a);
            }
            var groups = new Dictionary<int, Bounds>();
            for (int t = 0; t < triangles.Length; t++)
            {
                int v = triangles[t], root = Find(v);
                if (groups.TryGetValue(root, out var box)) { box.Encapsulate(world[v]); groups[root] = box; }
                else groups.Add(root, new Bounds(world[v], Vector3.zero));
            }
            foreach (var box in groups.Values)
            {
                if (box.size.x >= 3.5f || box.size.z >= 3.5f || box.size.y <= .3f) continue;
                var prop = box; prop.Expand(.2f);
                _props.Add(prop);
            }
        }

        /// <summary>
        /// Arena interior from its renderers: the wall ring (backdrop) bounds give the radius, the ceiling its height.
        /// Backdrops are measured from their triangles (<see cref="MeasureBackdrop"/>), once per arena: a backdrop is a
        /// wall ring only when its bounds are centred and its walls close the full circle; otherwise (open-air kits,
        /// the U-shaped school) the camera may go as far as the nearest wall in each compass sector, and past the floor
        /// edge where the backdrop is open. Near-horizontal sheets over the arena centre (the hospital's merged ceiling
        /// and light strips) cap the camera height instead of counting as walls. Compact standalone props (benches, bins,
        /// crates) become occluder boxes; the merged shells are too coarse for that.
        /// </summary>
        void LearnInterior()
        {
            _interiorKnown = true; _props.Clear(); _sectorRadius = null;
            _interiorCentre = _geometry.position; _interiorRadius = float.PositiveInfinity; _ceiling = float.PositiveInfinity;
            float floorRadius = float.PositiveInfinity;
            var backdrops = new List<Renderer>();
            foreach (var r in _geometry.GetComponentsInChildren<Renderer>(false))
            {
                if (r is ParticleSystemRenderer || !r.enabled) continue;
                string name = r.name;
                var b = r.bounds;
                if (name.Contains("backdrop")) backdrops.Add(r);
                else if (name == "arena" || name == "arena_floor") floorRadius = Mathf.Min(b.extents.x, b.extents.z);   // both FBX floor conventions
                else if (name.Contains("ceiling")) _ceiling = Mathf.Min(_ceiling, b.min.y - CeilingClearance);
                else if (name.Contains("props") && r.TryGetComponent(out MeshFilter shell)) AddShellProps(shell);
                else if (b.size.x < 3.5f && b.size.z < 3.5f && b.size.y > .3f)
                {
                    b.Expand(.2f);
                    _props.Add(b);
                }
            }
            Vector3 centre = _geometry.position;
            // Pass 1: overhead sheets over the centre cap the camera height (and so the top of the wall band).
            var meshes = new List<(Renderer Renderer, Vector3[] World, int[] Triangles)>();
            foreach (var r in backdrops)
            {
                if (!r.TryGetComponent(out MeshFilter filter) || filter.sharedMesh == null || !filter.sharedMesh.isReadable) { meshes.Add((r, null, null)); continue; }
                var local = filter.sharedMesh.vertices; var world = new Vector3[local.Length];
                var toWorld = filter.transform.localToWorldMatrix;
                for (int i = 0; i < local.Length; i++) world[i] = toWorld.MultiplyPoint3x4(local[i]);
                var triangles = filter.sharedMesh.triangles;
                meshes.Add((r, world, triangles));
                float overhead = OverheadUnderside(world, triangles, centre, centre.y + OverheadMinHeight);
                if (!float.IsInfinity(overhead)) _ceiling = Mathf.Min(_ceiling, overhead - CeilingClearance);
            }
            float bandLow = centre.y + BackdropBandLow, bandHigh = Mathf.Min(centre.y + BackdropBandHigh, _ceiling);
            // Pass 2: walls in the band below that cap.
            foreach (var (r, world, triangles) in meshes)
            {
                var b = r.bounds;
                Vector3 offset = b.center - centre; offset.y = 0f;
                float ring = Mathf.Min(b.extents.x, b.extents.z);
                Vector3 boundsCentre = new Vector3(b.center.x, centre.y, b.center.z);
                bool centred = offset.magnitude < ring * .25f;
                // Unreadable meshes keep the bounds-only rule.
                bool closed = world == null || (centred && MeasureBackdrop(world, triangles, boundsCentre, bandLow, bandHigh).Closed);
                if (centred && closed)
                {
                    _interiorCentre = boundsCentre;
                    _interiorRadius = Mathf.Min(_interiorRadius, ring - WallClearance);
                }
                else if (world != null) LearnOpenBackdrop(MeasureBackdrop(world, triangles, centre, bandLow, bandHigh), floorRadius);
            }
        }

        /// <summary>Per-sector camera limit from an open backdrop's measured walls (neighbour sectors included); open sectors reach past the floor edge.</summary>
        void LearnOpenBackdrop(BackdropProfile profile, float floorRadius)
        {
            var nearest = new float[InteriorSectors];
            for (int i = 0; i < InteriorSectors; i++) nearest[i] = float.PositiveInfinity;
            for (int bin = 0; bin < ProfileBins; bin++)
            {
                int sector = bin * InteriorSectors / ProfileBins;
                nearest[sector] = Mathf.Min(nearest[sector], profile.Nearest[bin]);
            }
            float open = float.IsInfinity(floorRadius) ? float.PositiveInfinity : floorRadius + WallClearance;
            if (_sectorRadius == null) { _sectorRadius = new float[InteriorSectors]; for (int i = 0; i < InteriorSectors; i++) _sectorRadius[i] = float.PositiveInfinity; }
            for (int i = 0; i < InteriorSectors; i++)
            {
                float near = Mathf.Min(nearest[i], Mathf.Min(nearest[(i + 1) % InteriorSectors], nearest[(i + InteriorSectors - 1) % InteriorSectors]));
                _sectorRadius[i] = Mathf.Min(_sectorRadius[i], float.IsInfinity(near) ? open : Mathf.Max(1f, near - WallClearance));
            }
        }

        /// <summary>Walls of a backdrop seen from a centre: nearest wall distance per 1° bin (infinity = open) and whether they close the circle.</summary>
        internal sealed class BackdropProfile
        {
            public readonly float[] Nearest = new float[ProfileBins];
            public readonly bool[] Covered = new bool[ProfileBins];
            public bool Closed { get { foreach (bool covered in Covered) if (!covered) return false; return true; } }
        }

        /// <summary>
        /// Measures backdrop walls from world-space triangles: every non-horizontal triangle is clipped to the height band
        /// [<paramref name="low"/>, <paramref name="high"/>] (a wall spanning the band counts even with no vertex inside
        /// it); the clipped piece, seen from <paramref name="centre"/>, occupies an angular interval, and each 1° bin in it
        /// takes the distance where a ray at that angle meets the piece. Pure; called once per arena (and by QA).
        /// </summary>
        internal static BackdropProfile MeasureBackdrop(Vector3[] world, int[] triangles, Vector3 centre, float low, float high)
        {
            var profile = new BackdropProfile();
            for (int i = 0; i < ProfileBins; i++) profile.Nearest[i] = float.PositiveInfinity;
            if (high <= low) return profile;
            var poly = new Vector3[8]; var clipped = new Vector3[8]; var flat = new Vector2[8]; var angles = new float[8];
            float binSize = 360f / ProfileBins;
            for (int t = 0; t + 2 < triangles.Length; t += 3)
            {
                Vector3 a = world[triangles[t]], b = world[triangles[t + 1]], c = world[triangles[t + 2]];
                Vector3 normal = Vector3.Cross(b - a, c - a);
                float area = normal.magnitude;
                if (area < 1e-8f || Mathf.Abs(normal.y) / area >= HorizontalNormal) continue;   // degenerate, or a floor / ceiling sheet
                if (Mathf.Max(a.y, Mathf.Max(b.y, c.y)) < low || Mathf.Min(a.y, Mathf.Min(b.y, c.y)) > high) continue;
                poly[0] = a; poly[1] = b; poly[2] = c;
                int n = ClipY(poly, 3, clipped, low, true);
                n = ClipY(clipped, n, poly, high, false);
                if (n < 2) continue;
                for (int i = 0; i < n; i++) { flat[i] = new Vector2(poly[i].x - centre.x, poly[i].z - centre.z); angles[i] = Mathf.Repeat(Mathf.Atan2(flat[i].x, flat[i].y) * Mathf.Rad2Deg, 360f); }
                if (n >= 3 && ContainsOrigin(flat, n)) continue;   // a piece over the centre itself cannot bound a radius
                // Angular interval: the complement of the largest gap between the sorted vertex angles.
                Array.Sort(angles, 0, n);
                float gap = 360f - angles[n - 1] + angles[0], from = angles[0];
                for (int i = 1; i < n; i++) if (angles[i] - angles[i - 1] > gap) { gap = angles[i] - angles[i - 1]; from = angles[i]; }
                float span = 360f - gap;
                int first = Mathf.FloorToInt(from / binSize), last = Mathf.FloorToInt((from + span) / binSize);
                for (int k = first; k <= last; k++)
                {
                    int bin = ((k % ProfileBins) + ProfileBins) % ProfileBins;
                    profile.Covered[bin] = true;
                    float angle = Mathf.Clamp((k + .5f) * binSize, from, from + span) * Mathf.Deg2Rad;
                    float d = RayDistance(flat, n, new Vector2(Mathf.Sin(angle), Mathf.Cos(angle)));
                    if (d < profile.Nearest[bin]) profile.Nearest[bin] = d;
                }
            }
            return profile;
        }

        /// <summary>Lowest point of the near-horizontal triangles at or above <paramref name="minY"/> whose XZ projection contains the centre (infinity = none).</summary>
        internal static float OverheadUnderside(Vector3[] world, int[] triangles, Vector3 centre, float minY)
        {
            float lowest = float.PositiveInfinity;
            var p = new Vector2(centre.x, centre.z);
            for (int t = 0; t + 2 < triangles.Length; t += 3)
            {
                Vector3 a = world[triangles[t]], b = world[triangles[t + 1]], c = world[triangles[t + 2]];
                float y = Mathf.Min(a.y, Mathf.Min(b.y, c.y));
                if (y < minY || y >= lowest) continue;
                Vector3 normal = Vector3.Cross(b - a, c - a);
                float area = normal.magnitude;
                if (area < 1e-8f || Mathf.Abs(normal.y) / area < HorizontalNormal) continue;
                Vector2 a2 = new Vector2(a.x, a.z), b2 = new Vector2(b.x, b.z), c2 = new Vector2(c.x, c.z);
                float d1 = Cross2(b2 - a2, p - a2), d2 = Cross2(c2 - b2, p - b2), d3 = Cross2(a2 - c2, p - c2);
                bool negative = d1 < 0f || d2 < 0f || d3 < 0f, positive = d1 > 0f || d2 > 0f || d3 > 0f;
                if (!(negative && positive)) lowest = y;
            }
            return lowest;
        }

        /// <summary>Sutherland-Hodgman clip of a polygon against the plane y = <paramref name="level"/> (keeps the side above when <paramref name="keepAbove"/>).</summary>
        static int ClipY(Vector3[] input, int count, Vector3[] output, float level, bool keepAbove)
        {
            int n = 0;
            for (int i = 0; i < count; i++)
            {
                Vector3 current = input[i], next = input[(i + 1) % count];
                bool inCurrent = keepAbove ? current.y >= level : current.y <= level;
                bool inNext = keepAbove ? next.y >= level : next.y <= level;
                if (inCurrent) output[n++] = current;
                if (inCurrent != inNext) output[n++] = Vector3.Lerp(current, next, (level - current.y) / (next.y - current.y));
            }
            return n;
        }

        /// <summary>Distance along <paramref name="direction"/> (from the origin) to the polygon's edges; the nearest edge point when the ray grazes past.</summary>
        static float RayDistance(Vector2[] polygon, int count, Vector2 direction)
        {
            float best = float.PositiveInfinity, nearest = float.PositiveInfinity;
            for (int i = 0; i < count; i++)
            {
                Vector2 p = polygon[i], e = polygon[(i + 1) % count] - p;
                float denom = Cross2(direction, e);
                if (Mathf.Abs(denom) > 1e-8f)
                {
                    float t = Cross2(p, e) / denom, u = Cross2(p, direction) / denom;
                    if (t >= 0f && u >= -1e-4f && u <= 1f + 1e-4f && t < best) best = t;
                }
                float along = e.sqrMagnitude > 1e-12f ? Mathf.Clamp01(Vector2.Dot(-p, e) / e.sqrMagnitude) : 0f;
                nearest = Mathf.Min(nearest, (p + e * along).magnitude);
            }
            return float.IsInfinity(best) ? nearest : best;
        }

        static bool ContainsOrigin(Vector2[] polygon, int count)
        {
            bool negative = false, positive = false;
            for (int i = 0; i < count; i++)
            {
                float d = Cross2(polygon[(i + 1) % count] - polygon[i], -polygon[i]);
                if (d < -1e-6f) negative = true; else if (d > 1e-6f) positive = true;
            }
            return negative != positive;   // strictly inside a non-degenerate piece (a vertical wall projects to a segment)
        }

        static float Cross2(Vector2 a, Vector2 b) => a.x * b.y - a.y * b.x;

        static int Sector(Vector3 flat) =>
            Mathf.Clamp((int)(Mathf.Repeat(Mathf.Atan2(flat.x, flat.z) * Mathf.Rad2Deg, 360f) / (360f / InteriorSectors)), 0, InteriorSectors - 1);

        /// <summary>Camera position inside the arena interior (wall ring radius, or the open-air sector limit).</summary>
        bool WithinInterior(Vector3 position)
        {
            Vector3 flat = position - _interiorCentre; flat.y = 0f;
            if (flat.magnitude > _interiorRadius) return false;
            return _sectorRadius == null || flat.magnitude <= _sectorRadius[Sector(flat)];
        }
    }
}
