using System;
using System.Collections;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Logic.Game;
using Abyss.Presentation.Audio;
using Abyss.Presentation.Vfx;
using Abyss.Runtime.Art;
using Abyss.Runtime.Persistence;
using Abyss.Runtime.World;
using Abyss.UI;
using Abyss.UI.Battle;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.Runtime.Battle
{
    /// <summary>
    /// Owns one 3D encounter. The engine resolves a whole batch immediately, but presentation replays
    /// only event snapshots. Commands and completion are exposed after their preceding visuals finish.
    /// </summary>
    public sealed partial class BattleView : MonoBehaviour
    {
        public BattleEngine Engine { get; private set; }
        public bool Playing { get; private set; }
        public bool Auto { get; private set; }
        /// <summary>Cancel may open pause only at the command root, never instead of submenu back.</summary>
        public bool CanOpenPause => _initialized && !_finished && !Playing && _hud != null && _hud.CommandRootOpen;
        readonly Dictionary<string, BattleDisplayUnit> _units = new Dictionary<string, BattleDisplayUnit>();
        readonly Dictionary<string, Dictionary<string, VfxHandle>> _auras = new Dictionary<string, Dictionary<string, VfxHandle>>();
        readonly List<VfxHandle> _effects = new List<VfxHandle>();
        readonly Dictionary<string, int> _hitCounts = new Dictionary<string, int>();
        readonly Dictionary<string, int> _hitTotals = new Dictionary<string, int>();
        readonly HashSet<string> _impactTargets = new HashSet<string>();
        readonly HashSet<string> _waveTargets = new HashSet<string>();
        readonly List<string> _order = new List<string>();
        readonly Dictionary<string, Color> _desiredAuras = new Dictionary<string, Color>();
        readonly List<string> _removedAuras = new List<string>();
        readonly bool[] _occupiedLanes = new bool[BattleEngine.MaxLivingEnemies];
        GameApp _app;
        BattleSetup _setup;
        BattleHUD _hud;
        UIRoot _ui;
        VfxLibrary _vfx;
        Camera _camera;
        Action<BattleOutcome> _completed;
        ActionStartEvent _action;
        PresentationDef _presentation;
        VfxHandle _charge;
        Image _flash, _dim;
        /// <summary>Shot selection, blends, framing and the shake / FOV-punch layers (see <see cref="BattleCameraDirector"/>).</summary>
        BattleCameraDirector _director;
        /// <summary>Hero whose command menu is open (S1 / S2 camera); null while replaying or in auto battle.</summary>
        string _commandUnit;
        /// <summary>Set once Finish stages the outcome: target-preview resets no longer move the camera.</summary>
        bool _outcome;
        /// <summary>
        /// How the current hero skill is staged (from presentation data): melee strike, projectile, area or support.
        /// None for basic attacks, items, guard and every enemy action.
        /// </summary>
        enum SkillBeat { None, Melee, Projectile, Area, Support }
        SkillBeat _beat;
        /// <summary>One S7 hit-reaction hold per action at most.</summary>
        bool _hitHeld;
        /// <summary>First qualifying hero of the current hit wave (big or critical, survives the hit); consumed after the wave's hit-stop.</summary>
        BattleDisplayUnit _pendingHit;
        /// <summary>Signature cut-in hold (the ultimate keeps its 0.95 s) and the aftermath hold before the camera returns.</summary>
        const float SignatureHold = .45f, AftermathHold = .15f;
        /// <summary>
        /// Pacing: the longest a hero waits on its follow-through before running home (the run itself no longer blocks the
        /// next turn), the beat after an action's last hit, and the tier-2 speed-ups (projectile flight, multi-hit interval).
        /// </summary>
        const float RecoveryCap = .3f, LastHitBeat = .05f, Tier2Flight = .8f, Tier2HitInterval = .85f;
        /// <summary>Units running home after an action; the next action waits only for the ones it involves.</summary>
        readonly HashSet<BattleDisplayUnit> _returning = new HashSet<BattleDisplayUnit>();
        /// <summary>Ownership token per returning unit; cancelled (down / revive / teardown / new action) so a cosmetic return never fights the next take.</summary>
        readonly Dictionary<BattleDisplayUnit, object> _returnTokens = new Dictionary<BattleDisplayUnit, object>();
        /// <summary>Longest a status tick / outcome waits for a cosmetic return (battle seconds) before the return is cancelled.</summary>
        const float ReturnWaitCap = 1.5f;
        /// <summary>Battle intro: one eased sweep from the low enemy-side angle into the establishing shot.</summary>
        const float IntroSweep = 1.2f;
        /// <summary>Battle intro run-on: total seconds, of which the last <see cref="IntroSettle"/> ease onto the mark.</summary>
        const float IntroRun = .8f, IntroSettle = .24f;
        float _flashAlpha, _dimAlpha, _dimTarget, _actionElapsed, _actionLength, _actionEnd, _waveStop;
        /// <summary>Battle time (speed-scaled, stopped by pause and hit-stop), the clock the takes themselves run on.</summary>
        float _clock;
        // Recoil: out over KnockOut, settle home over the rest.
        const float KnockLength = .25f, KnockOut = .05f;
        /// <summary>Share of normal speed that effect playback keeps while a hit-stop freezes the units.</summary>
        const float HitStopVfxRate = .1f;
        // Enemy death staging (seconds at 1x battle speed, from the UnitDown event). A death never queues the replay: the unit
        // collapses and dissolves beside it, so simultaneous deaths overlap, and the replay only waits for stragglers at action end
        // and at the outcome (WaitDeaths). A regular enemy reads in ~DeathDissolveAt + DeathDissolve; a boss gets a longer finish.
        // The collapse follows the Die take's own length within [DeathCollapse, DeathCollapseMax] (sped up only past the cap), and
        // the dissolve starts DeathLand after the body is down, never before DeathDissolveAt: starting it at a fixed .3 s hid most falls.
        const float DeathCollapse = .5f, DeathCollapseMax = .9f, DeathDissolveAt = .6f, DeathDissolve = .4f;
        const float BossDeathCollapse = .8f, BossDeathCollapseMax = 1.6f, BossDeathDissolveAt = .9f, BossDeathDissolve = .7f;
        const float DeathLand = .1f;
        const float ReducedDeathDissolve = .25f;
        /// <summary>A Die take longer than this is a held pose (Tripo / Mixamo take): the fall is staged in code instead of waited out.</summary>
        const float StaticDieTake = 2f;
        /// <summary>Where a falling Die take (Tripo `fall`) starts: the stagger before it, so the body is down before the dissolve.</summary>
        const float FallTakeStart = .3f;
        const float DeathRateMax = 3f;
        /// <summary>Death routines still running; the replay waits for them only where the next beat needs the field clear.</summary>
        int _dying;
        int _round, _wave, _eventIndex, _displayChain;
        string _active, _strikeClip;
        IReadOnlyList<BattleEvent> _events;
        bool _initialized, _finished, _restored, _hitstop, _fleeSucceeded, _perHitProjectile, _flashed;
        AtmospherePreset _oldAtmosphere;
        Abyss.Runtime.Art.OutlineContext _oldOutline;
        FloorDef _floor;
        // Battle-local readability: enemies render larger than their authored ScaleMult so silhouettes read on a phone.
        // Bosses get more so they dominate the frame; heroes and HP plates are untouched.
        const float EnemyReadabilityScale = 1.25f, BossReadabilityScale = 1.5f;
        // Boss entrance: camera push in toward the boss and back (each leg), and the cap on the whole entrance.
        const float BossPushLeg = .3f, BossEntranceMax = 1.6f;
        // Battle-only lighting: the arena's stage anchor (5 m over the centre) blew out the cream floor, so it is dropped,
        // the four edge anchors (flank walls, 2.2 m up, outside the floor disc) only wash the walls evenly, bloom only catches
        // real highlights, and a cool + warm directional rim pair separates the units without ever pooling on the floor.
        // The rim lights are owned by this view and removed in Restore(); dungeon and town lighting never reach this code.
        const float BattleEdgeLightIntensity = 1.6f, BattleEdgeLightRange = 14f, BattleBloomThreshold = 1.05f, BattleRimIntensity = .5f, BattleWarmRimIntensity = .7f;
        static readonly Color BattleRimColor = new Color(.5f, .7f, 1f), BattleWarmRimColor = new Color(1f, .74f, .46f);
        Light _rim, _warmRim;
        static bool BattleLightPolicy(string anchor, ref float intensity, ref float range)
        {
            if (anchor == "LightAnchor_stage") return false;
            if (anchor.StartsWith("LightAnchor_edge", StringComparison.Ordinal)) { intensity = BattleEdgeLightIntensity; range = BattleEdgeLightRange; }
            return true;
        }
        /// <summary>
        /// Safety net only. Arena FBXs exported before the export_arena_turned fix (Blender/environment/_kit_common_b.py)
        /// had every empty collapsed to the arena origin, so the four "edge" lights stacked into one white pool on the
        /// floor. The arenas are re-exported with real anchor positions; an anchor light that still sits at the origin
        /// (an arena that was not re-exported) has no authored position and is dropped. Anchors with a real position keep their light.
        /// </summary>
        static void DropCollapsedAnchorLights(IList<Light> lights)
        {
            for (int i = lights.Count - 1; i >= 0; i--)
            {
                var light = lights[i];
                if (light == null || light.transform.position.sqrMagnitude > .01f) continue;
                Destroy(light);
                lights.RemoveAt(i);
            }
        }
        bool Reduced => _app.Preferences != null && _app.Preferences.ReducedMotion;
        /// <summary>Battle pacing multiplier from settings (1x, 1.5x, 2x): scales waits, unit animation and action timers.</summary>
        float Speed => _app.Preferences != null ? _app.Preferences.BattleSpeed : 1f;
        float Dt => Time.unscaledDeltaTime * Speed;

        public void Initialize(GameApp app, BattleSetup setup, Action<BattleOutcome> completed)
        {
            if (_initialized) throw new InvalidOperationException("BattleView already initialized.");
            _initialized = true; _app = app ?? throw new ArgumentNullException(nameof(app));
            _setup = setup ?? throw new ArgumentNullException(nameof(setup)); _completed = completed;
            _camera = app.MainCamera;
            if (_camera == null) throw new InvalidOperationException("BattleView requires the application camera.");
            _oldAtmosphere = app.Atmosphere.Current;
            var outlineCamera = Abyss.Runtime.Art.OutlineCamera.Ensure(_camera); _oldOutline = outlineCamera.Context;
            FloorDef floor = null;
            foreach (var candidate in app.DB.Floors) if (candidate.Id == setup.FloorId) { floor = candidate; break; }
            if (floor == null) throw new InvalidOperationException("Battle floor not found: " + setup.FloorId);
            _floor = floor;
            var atmosphere = AtmospherePreset.ForFloor(floor, battle: true);
            // A fresh preset per battle: the battle threshold is local to this view and Restore() re-applies the old look.
            atmosphere.BloomThreshold = BattleBloomThreshold;
            app.Atmosphere.Apply(atmosphere); app.Atmosphere.SetupCamera(_camera, Abyss.Runtime.Art.OutlineContext.Battle);
            var arena = ArtLibrary.SpawnStatic(ArtLibrary.EnvPath(floor.Tileset, "arena"), transform);
            var arenaLights = EnvironmentProcessor.Process(arena, atmosphere.TorchColor, anchorPolicy: BattleLightPolicy);
            DropCollapsedAnchorLights(arenaLights.Lights);
            _rim = CreateRimLight("Battle rim light", BattleRimColor, BattleRimIntensity, new Vector3(0f, -.35f, -1f));
            _warmRim = CreateRimLight("Battle warm rim light", BattleWarmRimColor, BattleWarmRimIntensity, new Vector3(.55f, -.3f, -1f));
            _ui = UIRoot.Create(); _ui.Numbers.Camera = _camera;
            _vfx = VfxLibrary.Create(); _vfx.Camera = _camera;
            // Created before the HUD so the ultimate dim sits over the arena but under the cut-in and gauges.
            _dim = UIFactory.Fill(app.UI.Content, new Color(0, 0, 0, 0), "Battle dim");
            _hud = gameObject.AddComponent<BattleHUD>();
            _hud.Initialize(app.UI.Content, _camera, app.DB, Submit, ToggleAuto, PreviewTarget, () => _app != null && _app.Paused);
            _director = new BattleCameraDirector(_camera, transform, _hud, _units.Values);
            _director.SetArenaGeometry(arena.transform);
            _hud.EnableSpeedToggle(SpeedLabel, ToggleSpeed);
            _flash = UIFactory.Fill(app.UI.Content, new Color(1, 1, 1, 0), "Battle flash");
            Engine = new BattleEngine(app.DB, setup);
            Auto = app.Preferences.AutoBattle; _hud.SetAuto(Auto);
            AudioManager.Instance.PlayBgm(BattleMusicPolicy.Select(setup.Kind, setup.EnemyGroup));
            Establishing(true);
            Playing = true;
            StartCoroutine(Replay(Engine.Start(), true));
        }

        /// <summary>
        /// Starts the replay for a player command. False when the view is not accepting input (paused, already
        /// replaying, finished or not awaiting a command); the HUD then keeps its menu open. True means this view owns
        /// the replay, including an engine rejection, which is replayed and then reopens the commands.
        /// </summary>
        public bool Submit(BattleCommand command)
        {
            if (_finished || Playing || _app.Paused || Engine.State != BattleEngineState.AwaitingCommand) return false;
            _commandUnit = null; _hud.Lock(); Playing = true;
            StartCoroutine(Replay(Engine.Submit(command), false));
            return true;
        }
        public void SetAuto(bool enabled)
        {
            if (_finished) return;
            Auto = enabled; _hud.SetAuto(enabled);
            _app.Preferences.AutoBattle = enabled; _app.SavePreferences();
            if (enabled && !Playing && Engine.State == BattleEngineState.AwaitingCommand)
            {
                _commandUnit = null; _hud.Lock(); Playing = true; Establishing(false); StartCoroutine(AutoInput());
            }
        }
        public void ToggleAuto() => SetAuto(!Auto);
        string SpeedLabel => $"속도 {Speed:0.#}x";
        void ToggleSpeed()
        {
            var p = _app.Preferences;
            if (p == null) return;
            var speeds = GamePreferences.BattleSpeeds;
            int next = 0;
            for (int i = 0; i < speeds.Length; i++) if (p.BattleSpeed < speeds[i] - 0.01f) { next = i; break; }
            p.BattleSpeed = speeds[next];
            _app.SavePreferences();
            _hud.SetSpeedLabel(SpeedLabel);
        }
        IEnumerator AutoInput()
        {
            yield return Wait(.4f);
            if (_finished) yield break;
            if (!Auto) { Playing = false; OpenCommands(); yield break; }
            yield return Replay(Engine.Submit(Engine.SuggestCommand(Engine.ActiveHero)), false);
        }
        IEnumerator Replay(IReadOnlyList<BattleEvent> events, bool initial)
        {
            _hud.Lock();
            for (int i = 0; i < events.Count; i++)
            {
                yield return Wait(0);
                _events = events; _eventIndex = i;
                yield return Present(events[i]);
                if (_finished) yield break;
                if (initial && events[i] is BattleStartEvent) yield return Reduced ? ReducedIntro() : Intro();
            }
            yield return WaitDeaths();   // deaths from a status tick or a counter have no action end to wait at
            Playing = false;
            if (Engine.State == BattleEngineState.AwaitingCommand)
            {
                // The command shot requested by CommandRequestedEvent stays: no establishing shot in between.
                if (Auto) { Establishing(false); Playing = true; StartCoroutine(AutoInput()); }
                else OpenCommands();
            }
        }
        /// <summary>Opens (or reopens) the command menu and frames the active hero over the shoulder (S1).</summary>
        void OpenCommands()
        {
            _hud.ShowCommands(Engine);
            var hero = Engine.ActiveHero;
            _commandUnit = hero != null ? hero.Id : null;
            if (hero != null && Find(hero.Id, out var unit)) _director.Command(unit); else Establishing(false);
        }
        /// <summary>
        /// True when the next camera-bearing event of this replay is another action or (manual) command request with only
        /// bookkeeping in between, so the camera goes straight there instead of passing through the establishing shot.
        /// </summary>
        bool NextShotFollows()
        {
            if (_events == null) return false;
            for (int i = _eventIndex + 1; i < _events.Count; i++)
            {
                switch (_events[i])
                {
                    case ActionStartEvent _: return true;
                    case CommandRequestedEvent _: return !Auto;
                    case TurnEndEvent _: case TurnStartEvent _: case RoundStartEvent _: case EnemyIntentPlannedEvent _:
                    case IntentClearedEvent _: case TpChangeEvent _: case MpChangeEvent _: case StatusRemovedEvent _:
                    case ChainChangedEvent _: case MessageEvent _:
                        continue;
                    default: return false;
                }
            }
            return false;
        }
        /// <summary>Display units of an action's targets (living or not; the director skips the fallen).</summary>
        List<BattleDisplayUnit> Targets(ActionStartEvent e)
        {
            var list = new List<BattleDisplayUnit>();
            if (e.TargetIds != null) foreach (string id in e.TargetIds) if (Find(id, out var unit)) list.Add(unit);
            return list;
        }

        IEnumerator Present(BattleEvent battleEvent)
        {
            switch (battleEvent)
            {
                case BattleStartEvent e:
                    foreach (var snapshot in e.Units) Spawn(snapshot);
                    break;
                case RoundStartEvent e:
                    _round = e.Round; _order.Clear(); _order.AddRange(e.TurnOrder); RefreshOrder();
                    _hud.Log("ROUND " + _round); yield return Wait(.15f);
                    break;
                case TurnStartEvent e:
                    _active = e.UnitId;
                    if (Find(e.UnitId, out var turn)) { if (turn.Guarding) ReleaseGuard(turn); turn.Guarding = false; Sync(turn); }
                    RefreshOrder();
                    break;
                case TurnEndEvent e:
                    if (Find(e.Unit.Id, out var ended)) { ended.Apply(e.Unit); Sync(ended); }
                    break;
                case CommandRequestedEvent e:
                    _active = e.UnitId; RefreshOrder();
                    // S1 starts with the request; the replay's end opens the menu on the same shot (never re-establishes).
                    if (Auto) Establishing(false);
                    else if (Find(e.UnitId, out var commander)) _director.Command(commander);
                    break;
                case TurnSkippedEvent e:
                    Popup(e.UnitId, e.Broken ? "BREAK · 행동 불가" : "행동 불가", new Color(1, .7f, .25f));
                    yield return Wait(.35f); break;
                case ActionStartEvent e:
                    if (e.IsChargeAnnounce)
                    {
                        // Capture announcement scope for ChargeStarted, but never stage an attack or reuse a stale take.
                        _action = e; _presentation = null; _actionElapsed = _actionLength = _actionEnd = 0;
                        _hitCounts.Clear(); _hitTotals.Clear(); _impactTargets.Clear();
                        _hud.Log((Find(e.ActorId, out var announcer) ? announcer.Name + " · " : "") + e.DisplayName + " · 준비 중!");
                        if (announcer != null && announcer.Side == BattleSide.Enemy) _director.EnemyTurn(announcer, Targets(e));
                        break;
                    }
                    yield return StartAction(e); break;
                case ActionEndEvent e:
                    yield return EndAction(e);
                    yield return WaitDeaths(); break;
                case DamageEvent e:
                    yield return Damage(e); break;
                case MissEvent e:
                    if (Find(e.TargetId, out var missed))
                    {
                        bool strike = _action != null && e.SourceId == _action.ActorId;
                        if (strike) yield return PrepareHit(missed);
                        _ui.Numbers.Spawn(missed.Model.HeadPoint, 0, UINumberStyle.Miss);
                        if (strike && Find(e.SourceId, out var dodged)) StartCoroutine(Dodge(missed, dodged));
                        _impactTargets.Add(e.TargetId);
                        PlaySound("sfx_miss");
                        if (strike && NextHitJoinsWave()) { yield return Wait(.03f); break; }
                        // A miss can close a group wave whose earlier targets were hit: finish that wave's shared
                        // hit-stop and its S7 beat here, exactly as the damage path does.
                        if (strike && _waveStop > 0f) { yield return HitStop(_waveStop); yield return ConsumeHitReaction(); }
                        yield return Wait(strike && !NextStrikeFollows() ? LastHitBeat : HitInterval());
                    }
                    break;
                case HealEvent e:
                    if (Find(e.TargetId, out var healed))
                    {
                        healed.Hp = e.HpAfter; healed.MaxHp = e.MaxHp; Sync(healed);
                        _ui.Numbers.Spawn(healed.Model.HeadPoint, e.Amount, UINumberStyle.Heal);
                        _impactTargets.Add(e.TargetId);
                        Effect(_presentation != null && !string.IsNullOrEmpty(_presentation.HealVfx) ? _presentation.HealVfx : "heal", healed.Model.CenterPoint, new Color(.35f, 1, .6f), 1, 0, null, healed.Home.y);
                        PlaySound("sfx_heal"); yield return Wait(.25f);
                    }
                    break;
                case MpChangeEvent e:
                    if (Find(e.UnitId, out var mp))
                    {
                        mp.Mp = e.Mp; mp.MaxMp = e.MaxMp; Sync(mp);
                        if (e.Delta > 0) _ui.Numbers.Spawn(mp.Model.HeadPoint, e.Delta, UINumberStyle.Mp);
                    }
                    break;
                case TpChangeEvent e:
                    if (Find(e.UnitId, out var tp)) { tp.Tp = e.Tp; tp.MaxTp = e.MaxTp; Sync(tp); }
                    if (e.MaxTp > 0 && e.Tp >= e.MaxTp && Find(e.UnitId, out var fullTp) && fullTp.Side == BattleSide.Party)
                        _app.NotifyTip("first_tp_full");
                    break;
                case StatusAppliedEvent e:
                    if (Find(e.UnitId, out var applied))
                    {
                        applied.Statuses[e.StatusId] = new DisplayStatus { Id = e.StatusId, Name = e.DisplayName,
                            Type = e.EffectType, Turns = e.Turns, Beneficial = e.Beneficial };
                        Sync(applied); Popup(e.UnitId, e.DisplayName, e.Beneficial ? new Color(.4f, 1, .75f) : new Color(1, .5f, .7f));
                        // A damage skill's self buff (SkillDef.SelfStatus) lands on its actor, which the action never targeted:
                        // a buff glow there, not the strike's impact.
                        bool targeted = _action != null && Lists(_action.TargetIds, e.UnitId);
                        if (_action != null && !targeted && e.UnitId == _action.ActorId)
                        { if (_vfx.Supports("buff")) Effect("buff", applied.Model.CenterPoint, new Color(.4f, 1, .75f), 1, 0, null, applied.Home.y); }
                        else if (_impactTargets.Add(e.UnitId) && _action != null && _presentation != null && !string.IsNullOrEmpty(_presentation.ImpactVfx))
                            Impact(_presentation.ImpactVfx, applied, PresentationColor(_action.Element), !e.Beneficial, FacingFrom(_action.ActorId, applied));
                        PlaySound(e.Beneficial ? "sfx_buff" : StatusSound(e.EffectType)); yield return Wait(.16f);
                    }
                    break;
                case StatusRemovedEvent e:
                    if (Find(e.UnitId, out var removed)) { removed.Statuses.Remove(e.StatusId); Sync(removed); }
                    break;
                case StatusImmuneEvent e:
                    Popup(e.UnitId, "면역", Color.gray); yield return Wait(.12f); break;
                case ShieldChangeEvent e:
                    if (Find(e.UnitId, out var shield)) { shield.Shield = e.Shield; shield.MaxShield = e.MaxShield; Sync(shield); }
                    break;
                case BreakEvent e:
                    if (Find(e.UnitId, out var broken))
                    {
                        broken.Broken = true; Sync(broken);
                        // A pending charge gets one bounded combined interruption call-out at cancellation.
                        // Ordinary BREAK retains its world popup; never inspect future engine state here.
                        if (broken.DisplayCharge == null) Popup(e.UnitId, "BREAK!", new Color(1, .75f, .2f), 64f);
                        Effect("break", HitPoint(broken), new Color(1, .65f, .15f), 1.4f * ImpactScale(broken) / 1.2f, 0, null, broken.Home.y);
                        PlaySound("sfx_critical");
                        if (!Reduced) { AddTrauma(.5f); _director.Punch(-3f); ScreenFlash(new Color(1, .7f, .25f), .35f); }
                        yield return HitStop(.065f); yield return Wait(.28f);
                    }
                    break;
                case RecoverEvent e:
                    if (Find(e.UnitId, out var recovered))
                    { recovered.Broken = false; recovered.Shield = e.Shield; recovered.MaxShield = e.MaxShield; Sync(recovered); }
                    break;
                case UnitDownEvent e:
                    if (Find(e.UnitId, out var down))
                    {
                        CancelReturn(down);   // a cosmetic return must never keep writing a fallen body's transform or Idle
                        down.Alive = false; down.Hp = 0; down.Guarding = false; down.ClearWarnings(); Sync(down);
                        PlaySound("sfx_death");
                        if (down.Side == BattleSide.Enemy)
                        {
                            // Staged beside the replay: the next event (another hit, the action's end, the outcome) goes on at once.
                            StartCoroutine(DeathRoutine(down)); RefreshOrder();
                            break;
                        }
                        // A fallen hero lies down (a code topple under the standing Tripo defeat take), but a long held Die take must not stall the turn.
                        HeroDown(down);
                        yield return Wait(StandingDefeat(down) ? HeroFallTime : Mathf.Clamp(down.Model.Anim.Length("Die"), .35f, 1.2f));
                        RefreshOrder();
                    }
                    break;
                case ReviveEvent e:
                    if (Find(e.UnitId, out var revived))
                    {
                        CancelReturn(revived);   // a revive take owns the body next, not a stale cosmetic return
                        yield return WaitDeaths();   // a fallen enemy is mid-collapse: let it land before it stands again
                        revived.Alive = true; revived.Hp = e.Hp; revived.MaxHp = e.MaxHp;
                        revived.DeathRate = 1;
                        // A hero toppled in code stands back up from where it lies; the shared Revive starts prone and matches no code fall.
                        bool rise = RisesInCode(revived);
                        if (!rise) revived.Model.transform.SetPositionAndRotation(revived.Home, revived.Facing);
                        revived.Model.SetDissolve(0);
                        if (rise) StartCoroutine(HeroRise(revived));
                        else if (revived.Side == BattleSide.Party)
                            // A Blender-rig hero's Revive starts from its own Die end pose (lying at frame 30).
                            revived.Model.Anim.PlayOnce("Revive", "Idle", ReviveFade);
                        else revived.Model.Play("Idle", .25f);
                        Sync(revived);
                        // Revive skills already burst their own impact on the target; items and passives need this one.
                        bool skillBurst = _presentation != null && !string.IsNullOrEmpty(_presentation.ImpactVfx) && _presentation.ImpactVfx.Contains("revive");
                        if (!skillBurst) Effect("revive", revived.Model.CenterPoint, new Color(1, .9f, .55f), 1, 0, null, revived.Home.y);
                        Popup(e.UnitId, "부활", new Color(1, .95f, .6f)); PlaySound("sfx_revive");
                        yield return Wait(rise ? HeroRiseTime : revived.Side == BattleSide.Party ? Mathf.Min(revived.Model.Anim.Length("Revive"), ReviveWaitCap) : .4f);
                    }
                    break;
                case WeaknessDiscoveredEvent e:
                    foreach (var enemy in _units.Values)
                    {
                        if (enemy.Side != BattleSide.Enemy || enemy.DefId != e.EnemyId) continue;
                        if (!enemy.Weaknesses.Contains(e.Element)) enemy.Weaknesses.Add(e.Element);
                        _hud.Sync(enemy);
                    }
                    Popup(e.UnitId, BattleHUD.ElementName(e.Element) + " 약점 발견", new Color(1, .9f, .35f));
                    break;
                case SummonEvent e:
                    yield return WaitDeaths();   // the summon may take the lane of an enemy that is still dissolving
                    var summon = Spawn(e.Unit); summon.Model.SetDissolve(1);
                    Effect("summon", summon.Model.CenterPoint, new Color(.7f, .35f, 1), 1.2f, 0, null, summon.Home.y);
                    _hud.Log(summon.Name + " 등장!"); PlaySound("sfx_dark");
                    yield return summon.Model.DissolveIn(Reduced ? .15f : .45f);
                    yield return Wait(.2f);
                    break;
                case BossPhaseEvent e:
                    if (Find(e.UnitId, out var boss))
                    {
                        _director.Action(boss, null, true);
                        boss.Model.PlayOnce("Cast");
                        float phaseStarted = _clock;
                        _hud.CutIn(boss.Name + " · PHASE " + (e.PhaseIndex + 1), e.Line);
                        PlaySound("sfx_debuff");
                        if (!string.IsNullOrEmpty(e.Line))
                        {
                            yield return _ui.Dialog.Say(boss.Name, e.Line);
                            _ui.Dialog.Close();
                        }
                        else yield return Wait(1.1f);
                        // Both sides in battle time: the take plays at battle speed, so real seconds would over- or under-wait.
                        yield return Wait(Mathf.Max(0, boss.Model.Anim.Length("Cast") - (_clock - phaseStarted)));
                        _hud.HideCutIn(); Establishing(false);
                    }
                    break;
                case EnrageEvent e:
                    Popup(e.UnitId, "격노", new Color(1, .2f, .15f));
                    if (Find(e.UnitId, out var enraged)) enraged.Model.Flash(new Color(1, .2f, .1f), .3f);
                    PlaySound("sfx_buff"); yield return Wait(.3f); break;
                case MessageEvent e:
                    _hud.Log(e.Text); break;
                case CommandRejectedEvent e:
                    SetAuto(false); _hud.Log(e.Text); _ui.Toast.Show(e.Text);
                    yield return Wait(.3f); break;
                case FleeEvent e:
                    _hud.Log(e.Success ? "도주 성공" : "도주 실패");
                    _fleeSucceeded = e.Success;
                    if (e.Success)
                    {
                        foreach (var fleeing in _units.Values)
                        {
                            if (fleeing.Side != BattleSide.Party || !fleeing.Alive) continue;
                            // A teammate still jogging home must not turn back to the foe over the retreat.
                            CancelReturn(fleeing);
                            fleeing.Model.transform.rotation = transform.rotation * Quaternion.Euler(0, 180, 0);
                            SetRunRate(fleeing, FleeSpeed); fleeing.Model.Play("Run");
                        }
                    }
                    else if (_action != null && Find(_action.ActorId, out var stayer) && stayer.Alive)
                    {
                        stayer.Model.Play("Idle", ClipAnimator.ReturnFade);   // the flee attempt's looping Run settles back to the stance
                        StartCoroutine(Face(stayer, stayer.Facing));          // and the hero turns back to the foe
                    }
                    yield return Wait(.5f); break;
                case EnemyIntentPlannedEvent e:
                    if (Find(e.EnemyUnitId, out var planner)) { planner.Plan(e.Intent); _hud.Sync(planner); }
                    break;
                case IntentClearedEvent e:
                    if (Find(e.EnemyUnitId, out var cleared)) { cleared.ClearIntent(e.Slot); _hud.Sync(cleared); }
                    break;
                case ChargeStartedEvent e:
                    if (Find(e.EnemyUnitId, out var charger))
                    {
                        charger.StartCharge(e.SkillId, e.TargetUnitId, _round, _action != null && _action.ActorId == e.EnemyUnitId ? _action.Scope : Scope.Single);
                        _hud.Sync(charger); Popup(e.EnemyUnitId, "준비 중!", UITheme.Warning);
                        yield return Wait(.35f);
                    }
                    break;
                case ChargeReleasedEvent e:
                    if (Find(e.EnemyUnitId, out var released)) { released.ClearCharge(); _hud.Sync(released); }
                    break;
                case ChargeCancelledEvent e:
                    if (Find(e.EnemyUnitId, out var cancelled))
                    {
                        if (e.Reason == ChargeCancelReason.Removed) cancelled.ClearWarnings(); else cancelled.CancelCharge();
                        _hud.Sync(cancelled);
                    }
                    if (e.Reason == ChargeCancelReason.Break)
                    {
                        _hud.HideSkillBanner(); _hud.Log("BREAK! · 저지!");
                        yield return CeremonyWait(.5f);
                    }
                    break;
                case ChainChangedEvent e:
                    _displayChain = e.NewValue; _hud.SetChain(_displayChain);
                    break;
                case BattleEndEvent e:
                    yield return WaitDeaths();
                    yield return Finish(e.Outcome); break;
                default:
                    throw new InvalidOperationException("Unsupported battle event: " + battleEvent.GetType().Name);
            }
        }

        BattleDisplayUnit Spawn(UnitSnapshot snapshot)
        {
            var unit = new BattleDisplayUnit(); unit.Apply(snapshot);
            unit.Model = snapshot.Side == BattleSide.Party ? ArtLibrary.SpawnHero(snapshot.DefId, transform, _app.State?.Hero(snapshot.DefId)?.Job) : ArtLibrary.SpawnEnemy(_app.DB, snapshot.DefId, transform);
            // Heroes with a BattleIdle take stand in that ready stance for the whole battle: every "Idle" request resolves to it,
            // so Attack/Cast/Skill/Hit start and end near the loop they fade back into.
            if (unit.Model.Anim is ClipAnimator clips && clips.HasClip("BattleIdle")) { clips.RestClip = "BattleIdle"; clips.Play("Idle", 0f, false); }
            // The shared Hit take is 1.3 s (it starts and ends crouched); a reaction should be over in about 0.8 s.
            if (snapshot.Side == BattleSide.Party && unit.Model.Anim is ClipAnimator hitClips && hitClips.HasClip("BattleIdle")) hitClips.SetClipRate("Hit", HeroHitRate);
            if (snapshot.Side == BattleSide.Enemy)
            {
                var def = _app.DB.Enemies[snapshot.DefId];
                unit.Model.transform.localScale = Vector3.one * (def.ScaleMult * (def.IsBoss ? BossReadabilityScale : EnemyReadabilityScale));
                unit.Model.RecomputeBounds();
            }
            int lane = snapshot.Slot;
            if (snapshot.Side == BattleSide.Enemy)
            {
                // Summon indices never reset, but arena positions can reuse a defeated enemy's lane.
                var occupied = _occupiedLanes; Array.Clear(occupied, 0, occupied.Length);
                foreach (var existing in _units.Values)
                    if (existing.Side == BattleSide.Enemy && existing.Alive)
                        occupied[existing.ArenaLane] = true;
                int count = _setup.EnemyGroup.Count;
                if (snapshot.Slot < count)
                    lane = count == 1 ? 2 : count == 2 ? 1 + snapshot.Slot * 2 :
                        count == 3 ? 1 + snapshot.Slot : count == 4 && snapshot.Slot >= 2 ? snapshot.Slot + 1 : snapshot.Slot;
                else lane = SummonLane(occupied);
                if (lane >= occupied.Length || occupied[lane]) throw new InvalidOperationException("No free arena lane for " + snapshot.Id);
                unit.ArenaLane = lane;
            }
            float x;
            if (snapshot.Side == BattleSide.Party) x = (snapshot.Slot - (_setup.Party.Count - 1) * .5f) * 2.05f;
            else x = (lane - 2) * 2.6f;
            unit.Home = transform.TransformPoint(new Vector3(x, 0, snapshot.Side == BattleSide.Party ? -3.0f - snapshot.Row * 1.55f : 2.2f + snapshot.Row * 1.8f));
            unit.Facing = transform.rotation * Quaternion.Euler(0, snapshot.Side == BattleSide.Party ? 0 : 180, 0);
            unit.Model.transform.SetPositionAndRotation(unit.Home, unit.Facing);
            if (snapshot.Side == BattleSide.Party)
            {
                var spec = _setup.Party[snapshot.Slot];
                GearDisplay.DressBody(unit.Model, GearDisplay.Rank(_app.DB, spec.ArmorId), GearDisplay.Rank(_app.DB, spec.AccessoryId));
                if (!string.IsNullOrEmpty(spec.WeaponId))
                {
                    string socket = _app.DB.ClassOf(snapshot.DefId) == "archer" ? "weapon.L" : "weapon.R";
                    if (unit.Model.FindBone(socket) == null) throw new InvalidOperationException("Missing weapon socket: " + snapshot.DefId + "/" + socket);
                    GearDisplay.AttachWeapon(_app.DB, unit.Model, socket, spec.WeaponId);
                }
            }
            PrepareGuard(unit);
            if (!unit.Alive) { if (snapshot.Side == BattleSide.Party) LayFallen(unit); else unit.Model.Play("Die"); }
            RememberScale(unit);
            _units.Add(unit.Id, unit); _hud.AddUnit(unit); Sync(unit);
            return unit;
        }

        /// <summary>
        /// Free lane for a summon. With a living boss on the field, the lane farthest from it comes first so the larger
        /// boss model and its plate keep clear neighbours; otherwise the lowest free lane, as before.
        /// </summary>
        int SummonLane(bool[] occupied)
        {
            int bossLane = -1;
            foreach (var existing in _units.Values)
                if (existing.Side == BattleSide.Enemy && existing.Alive && existing.Boss) { bossLane = existing.ArenaLane; break; }
            int best = occupied.Length, bestDistance = -1;
            for (int lane = 0; lane < occupied.Length; lane++)
            {
                if (occupied[lane]) continue;
                int distance = bossLane < 0 ? 0 : Mathf.Abs(lane - bossLane);
                if (distance > bestDistance) { best = lane; bestDistance = distance; }
            }
            return best;
        }

        IEnumerator StartAction(ActionStartEvent e)
        {
            _action = e; _presentation = null; _hitCounts.Clear(); _hitTotals.Clear(); _impactTargets.Clear();
            _waveTargets.Clear(); _wave = 0; _waveStop = 0; _strikeClip = null; _perHitProjectile = false; _flashed = false; _plan = null;
            _strikeImpact = _strikeSfx = null;
            if (!string.IsNullOrEmpty(e.PresentationId))
            {
                if (!_app.DB.Presentations.TryGetValue(e.PresentationId, out _presentation))
                    throw new InvalidOperationException("Missing action presentation: " + e.PresentationId);
            }
            if (!Find(e.ActorId, out var actor)) yield break;
            // A monster's plain attack lands with its body family's blow (bite, claw, slam, sting...), not the shared spark.
            PlanEnemyStrike(e, actor);
            _actionElapsed = 0; _actionLength = 0; _actionEnd = 0;
            BattleDisplayUnit target = null;
            if (e.TargetIds != null && e.TargetIds.Count > 0) Find(e.TargetIds[0], out target);
            _hud.Log(actor.Name + " · " + (e.DisplayName ?? ActionName(e.Kind)));
            // The previous actor may still be jogging home: wait only when it is this action's actor or one of its targets,
            // so its cosmetic return finishes before this take reuses the same body (token ownership makes that wait safe).
            while (Involved(e, actor)) yield return null;
            // A dodge or a cast flourish still moving this actor (or a target) settles first; bounded.
            yield return WaitFlourish(actor);
            if (target != null) yield return WaitFlourish(target);
            // A recoil still running on the actor would keep writing its position over this action's staging: end it on the mark.
            if (actor.KnockTime > 0) { actor.KnockTime = 0; actor.Model.transform.position = actor.Home; }
            _beat = actor.Side == BattleSide.Party ? Beat(e, actor, target) : SkillBeat.None;
            _hitHeld = false; _pendingHit = null;
            if (actor.Side == BattleSide.Enemy) _director.EnemyTurn(actor, Targets(e), StrikePoint(e, actor, target));
            else if (_beat == SkillBeat.None) _director.Action(actor, target, e.IsUltimate);
            if (e.Kind == ActionKind.Skill && !string.IsNullOrEmpty(e.DisplayName))
                _hud.SkillBanner(e.DisplayName, PresentationColor(e.Element));
            bool grand = e.IsUltimate || (_presentation != null && _presentation.Tier >= 3);
            if (grand && !Reduced) _dimTarget = e.IsUltimate ? .62f : .4f;
            // Heroes power up with their own Ultimate take under the cut-in (frames 0-28), then leap / levitate into
            // the finisher; models without it fall back to the Cast wind-up and their normal strike.
            bool ultimateTake = e.IsUltimate && actor.Model.Anim.HasClip("Ultimate");
            int tier = _presentation != null ? _presentation.Tier : 1;
            if (e.IsUltimate)
            {
                if (ultimateTake) Swing(actor, "Ultimate", false);
                else if (actor.Model.Anim.HasClip("Cast")) actor.Model.Anim.Play("Cast", .2f);
                // S5: push onto the caster under the portrait band. Reduced motion: no band, no camera move.
                if (actor.Side == BattleSide.Party) _director.SkillCutIn(actor, tier, true);
                if (!Reduced)
                {
                    if (actor.Side == BattleSide.Party)
                        _hud.UltimateCutIn(actor.DefId, actor.Name, e.DisplayName ?? "궁극기", PresentationColor(e.Element));
                    else _hud.CutIn(actor.Name, e.DisplayName ?? "궁극기");
                }
                // Only the four hunter classes have an ultimate cue (an enemy TP skill would name a missing one).
                if (actor.Side == BattleSide.Party)
                {
                    string cls = _app.DB.ClassOf(actor.DefId);
                    PlaySound("sfx_ultimate_" + (cls == "archer" ? "ranger" : cls));
                }
                yield return Wait(Reduced ? .3f : .95f); _hud.HideCutIn();
            }
            else if (_beat != SkillBeat.None && IsSignature(e) && !Reduced)
            {
                // Signature skill: the charge builds at the feet while the camera pushes in under the slanted portrait band.
                StartCharge(e, actor, PresentationColor(e.Element));
                _director.SkillCutIn(actor, tier, false);
                _hud.PlayCutIn(true, actor.DefId, actor.Name, e.DisplayName ?? "", PresentationColor(e.Element));
                yield return Wait(SignatureHold); _hud.HideCutIn();
            }
            if (grand && _dimTarget > .4f) _dimTarget = .4f;   // keep framing the wind-up after the cut-in
            if (_beat != SkillBeat.None) StageBeat(e, actor, target);
            if (e.Kind == ActionKind.Guard)
            {
                actor.Guarding = true; Sync(actor);
                if (actor.Side == BattleSide.Party) HoldGuard(actor);
                Popup(actor.Id, "방어", new Color(.55f, .8f, 1)); PlaySound("sfx_guard");
                yield return Wait(.3f); yield break;
            }
            if (e.Kind == ActionKind.Flee)
            {
                // Turn away from the foe into the run (never a backwards jog facing it).
                SetRunRate(actor, FleeSpeed); actor.Model.Play("Run");
                yield return Face(actor, actor.Facing * Quaternion.Euler(0, 180, 0));
                yield return Wait(.08f); yield break;
            }
            bool cast = e.Kind == ActionKind.Item || e.Kind == ActionKind.Summon ||
                (_presentation != null && _presentation.ActorAction == "cast");
            // Physical skills use the hero's signature technique (leap smash, power shot, staff slam) instead of the basic swing.
            string clip = ultimateTake ? "Ultimate" : cast ? "Cast"
                : e.Kind == ActionKind.Skill && actor.Model.Anim.HasClip("Skill") ? "Skill" : "Attack";
            // A caster whose class / hero layer ships a Skill take (the mage's two-handed channel) but no Cast of its own uses
            // it for its bigger spells (group scope, tier 3 or the signature); quick single-target spells keep the shared Cast.
            if (clip == "Cast" && e.Kind == ActionKind.Skill && actor.Side == BattleSide.Party &&
                actor.Model.HasClassClip("Skill") && !actor.Model.HasClassClip("Cast") &&
                (e.Scope != Scope.Single || IsSignature(e) || (_presentation != null && _presentation.Tier >= 3))) clip = "Skill";
            bool rangedBasic = e.Kind == ActionKind.Attack &&
                actor.Side == BattleSide.Party && _app.DB.ClassOf(actor.DefId) != "warrior";
            // A mage has no authored basic Attack: the shared Cast (forward palm release) reads better than the melee swing.
            if (clip == "Attack" && rangedBasic && _app.DB.ClassOf(actor.DefId) == "mage" &&
                !actor.Model.HasClassClip("Attack") && actor.Model.Anim.HasClip("Cast")) clip = "Cast";
            bool approach = !Reduced && !cast && !rangedBasic && target != null && actor.Id != target.Id &&
                ((_presentation != null && _presentation.Approach != "none") ||
                (_presentation == null && e.Kind == ActionKind.Attack));
            if (actor.Side == BattleSide.Party && !ultimateTake && e.Kind != ActionKind.Guard && e.Kind != ActionKind.Flee)
                clip = PlanHeroTake(e, actor, target, clip, approach);
            // A lunge is the sweep of a group strike; a single-target strike closes the whole gap instead of swinging at air.
            bool lunge = approach && _presentation != null && _presentation.Approach == "lunge" && e.Scope != Scope.Single;
            Vector3 destination = actor.Model.transform.position;
            bool swung = false;
            if (approach)
            {
                Vector3 direction = target.Model.transform.position - actor.Model.transform.position;
                direction.y = 0;
                float distance = direction.magnitude;
                float travel = Mathf.Max(0, distance - actor.Model.Radius - target.Model.Radius - .45f);
                direction = distance > .001f ? direction / distance : Vector3.zero;
                destination += direction * (lunge ? Mathf.Min(.7f, travel) : travel);
                bool run = !lunge && travel > .01f;
                // Styled approaches: monsters pounce / charge / slam / dive / blink / burrow / bounce / skitter, heroes leap or dash.
                var move = run && actor.Side == BattleSide.Enemy ? EnemyMoveFor(e, actor) : EnemyMove.Dash;
                var flourish = run && actor.Side == BattleSide.Party && !ultimateTake && _plan != null ? _plan.Flourish : HeroFlourish.None;
                bool styled = move != EnemyMove.Dash || flourish == HeroFlourish.Leap || flourish == HeroFlourish.Dash;
                // The run eases to a stop over its last `settle` seconds while the strike winds up, so the blow lands just after the
                // feet plant: no constant-speed slide in the strike pose and no standing pause before the blade arrives.
                float runTime = ApproachTime(actor, travel);
                float settle = StrikeSettle(actor, ultimateTake ? null : clip, runTime);
                if (styled)
                {
                    if (direction.sqrMagnitude > .01f) yield return Face(actor, Quaternion.LookRotation(direction));
                    if (move != EnemyMove.Dash) yield return EnemyApproach(move, actor, target, destination, clip, cast);
                    else if (flourish == HeroFlourish.Leap) yield return HeroLeap(actor, destination, clip);
                    else yield return HeroDash(actor, destination, clip);
                    swung = true; run = false;
                }
                // The run starts blending in while the body turns toward the foe (no standing pivot, no pop into the sprint).
                if (run) { SetRunRate(actor, travel / (runTime - settle * .5f)); actor.Model.Anim.Play("Run", RunFade, false); }
                if (!styled && direction.sqrMagnitude > .01f) yield return Face(actor, Quaternion.LookRotation(direction));
                if (run)
                {
                    StartCoroutine(ApproachRun(actor, destination, runTime, settle, PounceArc(actor, travel)));
                    yield return Wait(runTime - settle);
                    // The wind-up plays over the deceleration so the blade lands as the feet plant.
                    if (ultimateTake) Resume(actor, "Ultimate", UltimateResume); else Swing(actor, clip, cast);
                    swung = true;
                    yield return Wait(settle);
                }
            }
            if (!swung && target != null && actor.Id != target.Id)
            {
                Vector3 facing = target.Model.transform.position - actor.Model.transform.position; facing.y = 0;
                if (facing.sqrMagnitude > .01f) yield return Face(actor, Quaternion.LookRotation(facing));
            }
            if (!swung && !ultimateTake && actor.Side == BattleSide.Party && _plan != null && _plan.Flourish == HeroFlourish.Backstep && !Reduced)
                yield return Backstep(actor);
            if (!swung && !ultimateTake) Swing(actor, clip, cast);
            if (!Reduced && !ultimateTake && e.Kind != ActionKind.Guard && e.Kind != ActionKind.Flee)
            {
                float release = Mathf.Max(0f, _actionLength * Contact(actor.Model, _strikeClip ?? clip) - _actionElapsed);
                if (!swung && actor.Side == BattleSide.Enemy && !approach && target != null)
                    StartCoroutine(CastFlourishRoutine(actor, EnemyFlourishFor(e, actor), release));
                else if (!swung && actor.Side == BattleSide.Party && _plan != null && _plan.Flourish == HeroFlourish.Levitate)
                    StartCoroutine(CastFlourishRoutine(actor, CastFlourish.Hover, release));
                else if (!swung && actor.Side == BattleSide.Party && _plan != null && _plan.Flourish == HeroFlourish.Hop)
                    StartCoroutine(CastFlourishRoutine(actor, CastFlourish.Jump, Mathf.Max(.25f, release)));
                // A spinning cut turns the whole body through the strike (monster Spin moves start their own turn on arrival).
                if (actor.Side == BattleSide.Party && _plan != null && _plan.Flourish == HeroFlourish.Spin && approach)
                    StartCoroutine(SpinBody(actor, release - .12f, .36f));
            }
            Color tint = PresentationColor(e.Element);
            if (!_charge.IsPlaying) StartCharge(e, actor, tint);
            PlaySound(_presentation != null && !string.IsNullOrEmpty(_presentation.SfxCast) ? _presentation.SfxCast :
                e.Kind == ActionKind.Item ? "sfx_item" : cast ? ElementSound(e.Element) : _strikeSfx != null ? "sfx_wind" : WeaponSound(actor));
            float contactTime = _actionLength * Contact(actor.Model, _strikeClip ?? clip);
            // The authored Attack contacts at 40%; the lunge belongs to that strike, not a tiny Run.
            if (lunge) yield return Move(actor, destination, Mathf.Max(.05f, contactTime - _actionElapsed));
            else yield return Wait(Mathf.Max(0, contactTime - _actionElapsed));
            // S4 release: whip to the impact framing as the spell / shot leaves the hand.
            if (_beat == SkillBeat.Projectile || _beat == SkillBeat.Area || _beat == SkillBeat.Support)
                _director.CastShot(actor, Targets(e), true, CastStyleOf(_beat));
            // Enemy / ally name tags step aside while a skill's impact plays (restored at the action's end).
            if (_beat != SkillBeat.None) _hud.SetTagsHidden(true);
            bool projectile = _presentation != null && !string.IsNullOrEmpty(_presentation.TravelVfx) && e.TargetIds != null;
            // Multi-hit shots send one projectile per hit; area spells keep a single opening volley under the big effect.
            _perHitProjectile = projectile && e.HitCount > 1 && string.IsNullOrEmpty(_presentation.AreaVfx);
            if (projectile && !_perHitProjectile)
            {
                float longest = 0;
                foreach (string id in e.TargetIds)
                    if (Find(id, out var projectileTarget)) longest = Mathf.Max(longest, Shoot(actor, projectileTarget, tint));
                yield return Wait(longest);
            }
            if (grand) _dimTarget = Mathf.Min(_dimTarget, .2f);
            if (_presentation != null && !string.IsNullOrEmpty(_presentation.AreaVfx) && e.TargetIds != null && AreaCenter(e.TargetIds, out var center))
            {
                // Field / group spells: one big effect over the whole target group, then the per-hit impacts.
                Effect(_presentation.AreaVfx, center, tint, Mathf.Max(.1f, _presentation.AreaScale), 0, null, center.y - .9f, AreaFacing(actor, center));
                _dimTarget = Mathf.Min(_dimTarget, .12f);   // the effect itself plays over a near-full-bright arena
                if (!Reduced && _presentation.ScreenFlash) ScreenFlash(tint, .45f);
                if (!Reduced) AddTrauma(_presentation.Shake * .6f);
                float lead = Reduced ? Mathf.Min(.12f, _presentation.AreaWait) : _presentation.AreaWait;
                if (lead > 0) yield return Wait(lead);
            }
        }
        /// <summary>
        /// Staging family of a hero skill from its presentation data: allies targeted = support; a dash / lunge approach =
        /// melee; an area effect or a group scope = area; anything else (shots, bolts, direct casts) = projectile.
        /// </summary>
        SkillBeat Beat(ActionStartEvent e, BattleDisplayUnit actor, BattleDisplayUnit target)
        {
            if (e.Kind != ActionKind.Skill) return SkillBeat.None;
            if (target != null && target.Side == actor.Side) return SkillBeat.Support;
            bool cast = _presentation != null && _presentation.ActorAction == "cast";
            if (!cast && target != null && target.Id != actor.Id && _presentation != null && _presentation.Approach != "none") return SkillBeat.Melee;
            if ((_presentation != null && !string.IsNullOrEmpty(_presentation.AreaVfx)) || e.Scope != Scope.Single) return SkillBeat.Area;
            return SkillBeat.Projectile;
        }
        static bool IsSignature(ActionStartEvent e) => e.SkillId != null && e.SkillId.StartsWith("sig_", StringComparison.Ordinal);
        static BattleCameraDirector.CastStyle CastStyleOf(SkillBeat beat) =>
            beat == SkillBeat.Area ? BattleCameraDirector.CastStyle.Area : beat == SkillBeat.Support ? BattleCameraDirector.CastStyle.Support : BattleCameraDirector.CastStyle.Projectile;
        /// <summary>Camera for the cast pose: S3 strike follow for melee, S4 behind the caster for everything else.</summary>
        void StageBeat(ActionStartEvent e, BattleDisplayUnit actor, BattleDisplayUnit target)
        {
            if (_beat == SkillBeat.Melee && target != null)
            {
                Vector3 from = actor.Model.transform.position, direction = target.Model.transform.position - from; direction.y = 0;
                float distance = direction.magnitude;
                float travel = Mathf.Max(0, distance - actor.Model.Radius - target.Model.Radius - .45f);
                bool lunge = _presentation != null && _presentation.Approach == "lunge" && e.Scope != Scope.Single;
                Vector3 mark = distance > .001f ? from + direction / distance * (lunge ? Mathf.Min(.7f, travel) : travel) : from;
                _director.StrikeFollow(actor, target, mark);
            }
            else _director.CastShot(actor, Targets(e), false, CastStyleOf(_beat));
        }
        /// <summary>
        /// Charge at the caster's feet: the presentation's charge effect, or for a signature / ultimate without one a
        /// class default (bow glint for archers, grand aura for ultimates, aura otherwise) when the library has it.
        /// </summary>
        void StartCharge(ActionStartEvent e, BattleDisplayUnit actor, Color tint)
        {
            string key = _presentation != null ? _presentation.ChargeVfx : null;
            if (string.IsNullOrEmpty(key) && _beat != SkillBeat.None && (IsSignature(e) || e.IsUltimate))
            {
                key = e.IsUltimate ? "charge_grand" : _app.DB.ClassOf(actor.DefId) == "archer" ? "charge_bow" : "aura";
                if (!_vfx.Supports(key)) key = null;
            }
            if (!string.IsNullOrEmpty(key))
                _charge = Effect(key, actor.Model.CenterPoint, tint, 1, _actionLength, actor.Model.transform, actor.Home.y);
        }
        /// <summary>
        /// Where a melee enemy will strike from (the run's end mark), predicted with the same rules as the approach below,
        /// so the S6 reverse angle frames the strike instead of the spot the enemy leaves. Null for casts, lunges, guard,
        /// flee and reduced motion (the enemy acts from its mark).
        /// </summary>
        Vector3? StrikePoint(ActionStartEvent e, BattleDisplayUnit actor, BattleDisplayUnit target)
        {
            if (Reduced || target == null || actor.Id == target.Id || e.Kind == ActionKind.Guard || e.Kind == ActionKind.Flee) return null;
            bool cast = e.Kind == ActionKind.Item || e.Kind == ActionKind.Summon || (_presentation != null && _presentation.ActorAction == "cast");
            bool approach = !cast && ((_presentation != null && _presentation.Approach != "none") || (_presentation == null && e.Kind == ActionKind.Attack));
            if (!approach || (_presentation != null && _presentation.Approach == "lunge" && e.Scope != Scope.Single)) return null;
            Vector3 from = actor.Model.transform.position, direction = target.Model.transform.position - from;
            direction.y = 0;
            float distance = direction.magnitude;
            if (distance < .001f) return null;
            float travel = Mathf.Max(0, distance - actor.Model.Radius - target.Model.Radius - .45f);
            return from + direction / distance * travel;
        }
        void Swing(BattleDisplayUnit actor, string clip, bool cast)
        {
            float length = actor.Model.Anim.Length(clip);
            // 0.15-0.25 s out of the stance (the strike must still be reached at full weight: cap by the time to contact).
            float fade = Mathf.Min(cast ? .25f : .2f, Mathf.Max(.08f, length * Contact(actor.Model, clip) * .6f));
            actor.Model.Anim.PlayOnce(clip, "Idle", fade);
            _actionLength = length; _actionElapsed = 0; _strikeClip = clip; _actionEnd = length * EndFraction(actor, clip);
        }
        /// <summary>Continues a take from a normalized point (the Ultimate finisher after the dash to the target).</summary>
        void Resume(BattleDisplayUnit actor, string clip, float normalized)
        {
            actor.Model.Anim.PlayFrom(clip, normalized, .08f);
            _actionLength = actor.Model.Anim.Length(clip); _actionElapsed = _actionLength * normalized; _strikeClip = clip; _actionEnd = 0;
        }
        // Contact / release points authored in Blender/lib_humanoid/motion.py (CONTACT).
        const float UltimateResume = 28f / 66f;
        static float EndFraction(BattleDisplayUnit unit, string clip) => unit.Model.Anim is ClipAnimator clips ? clips.EndFraction(clip) : 1f;
        static float DefaultContact(string clip)
        {
            switch (clip)
            {
                case "Cast": return .6f;
                case "Skill": return .5f;
                case "Ultimate": return 44f / 66f;
                // Authored shared takes (Blender/hunters_tripo/motion_takes.py CONTACT).
                case "Spell": return .562f;
                case "Slash": return .379f;
                case "Thrust": return .448f;
                case "Smash": return .455f;
                case "Spin": return .435f;
                case "Channel": return .548f;
                case "Throw": return .48f;
                case "Rally": return .375f;
                case "Kneel": return .455f;
                default: return .4f;
            }
        }
        /// <summary>Strike point of a take: the per-class value when the model ships its own take, else the shared default.</summary>
        static float Contact(CharacterModel model, string clip) => model.ContactFraction(clip, DefaultContact(clip));

        // Locomotion: the hero Run take covers about ArtLibrary.StrideSpeed m/s of ground at 1x (measured in Unity on the 1.3 m hero scale: stance-foot speed 2.9-3.3 m/s); the
        // approach and the return trip move at ApproachSpeed and play Run at the matching rate, so the feet do not skate.
        const float HeroHitRate = 1.6f;
        // (ArtLibrary.StrideSpeed: the Blender-rig hunters' own Run strides further.)
        const float ApproachSpeed = 5.5f, RunFade = .15f;
        /// <summary>Hero strike lands this long after the feet plant; the wind-up may overlap at most this much of the run.</summary>
        const float StrikeAfterPlant = .05f, MaxStrikeSettle = .35f, FleeSpeed = 4f;
        /// <summary>
        /// Seconds of deceleration at the end of an approach run, during which the strike winds up. A hero's lead follows its take's
        /// contact (bounded so the slide stays short); enemies keep the short overlap their pounce arc was tuned for.
        /// </summary>
        float StrikeSettle(BattleDisplayUnit unit, string clip, float runTime)
        {
            float lead = Mathf.Min(.2f, runTime * .3f);
            if (unit.Side != BattleSide.Party) return lead;
            float contact = clip != null ? ContactSeconds(unit, clip) : unit.Model.Anim.Length("Ultimate") * (DefaultContact("Ultimate") - UltimateResume);
            return Mathf.Clamp(contact - StrikeAfterPlant, lead, Mathf.Max(lead, Mathf.Min(MaxStrikeSettle, runTime * .6f)));
        }
        static float ApproachTime(BattleDisplayUnit unit, float distance) =>
            unit.Side == BattleSide.Party ? Mathf.Max(.25f, distance / ApproachSpeed) : MovementTime(distance);
        static void SetRunRate(BattleDisplayUnit unit, float groundSpeed)
        {
            if (!(unit.Model.Anim is ClipAnimator clips)) return;
            if (unit.Side == BattleSide.Party) clips.SetClipRate("Run", Mathf.Clamp(groundSpeed / ArtLibrary.StrideSpeed(unit.Model, "Run"), .6f, 3f));
            else clips.SetClipRate("Run", Mathf.Clamp(groundSpeed / EnemyStrideSpeed, 1f, EnemyRunRateMax));
        }
        // Enemies cross the arena in MovementTime (0.22-0.36 s, 10-16 m/s), several times faster than any stride their Run take
        // covers (Tripo presets: 1.3-1.7 m/s at battle scale), so a matched rate would be a blur. Design choice: the dash is a
        // pounce. The body arcs off the floor (no foot is planted while it travels, so nothing can glide) and the Run take churns
        // at up to 3x underneath it. The return trip uses the same arc.
        const float EnemyStrideSpeed = 1.6f, EnemyRunRateMax = 3f;
        static float PounceArc(BattleDisplayUnit unit, float travel) =>
            unit.Side == BattleSide.Party ? 0f : Mathf.Clamp(travel * .06f, .12f, .4f);
        /// <summary>Fires the presentation's projectile from the weapon socket at the target's hit point; returns its flight time.</summary>
        float Shoot(BattleDisplayUnit actor, BattleDisplayUnit target, Color tint)
        {
            string key = _presentation.TravelVfx;
            Vector3 from = actor.Model.MuzzlePoint(_app.DB.ClassOf(actor.DefId) == "archer" ? "weapon.L" : "weapon.R"), to = HitPoint(target);
            float time = Reduced ? .08f : TravelTime(key, Vector3.Distance(from, to)) * (_presentation.Tier >= 2 ? Tier2Flight : 1f);
            TrackEffect(_vfx.Travel(key, from, to, time, tint));
            return time;
        }
        static float TravelTime(string key, float distance) =>
            key.StartsWith("orb", StringComparison.Ordinal) ? Mathf.Clamp(distance / 12f, .2f, .6f) :
            key.StartsWith("bolt", StringComparison.Ordinal) ? Mathf.Clamp(distance / 16f, .16f, .36f) :
            Mathf.Clamp(distance / 22f, .14f, .3f);
        /// <summary>Ground-level centre of the living targets (origin 0.9 m up, like CenterPoint). Allocation-free.</summary>
        bool AreaCenter(IReadOnlyList<string> ids, out Vector3 center)
        {
            center = Vector3.zero; int count = 0;
            for (int i = 0; i < ids.Count; i++)
            {
                if (!Find(ids[i], out var unit)) continue;
                center += unit.Home; count++;
            }
            if (count == 0) return false;
            center = center / count + Vector3.up * .9f;
            return true;
        }
        IEnumerator EndAction(ActionEndEvent e)
        {
            _charge.Stop(); _charge = default;
            _hud.HideSkillBanner(); _dimTarget = 0;
            if (_action != null && (e.Kind == ActionKind.Skill || e.Kind == ActionKind.Item) &&
                _presentation != null && !string.IsNullOrEmpty(_presentation.ImpactVfx))
                foreach (string id in _action.TargetIds)
                    if (_impactTargets.Add(id) && Find(id, out var affected) && Find(_action.ActorId, out var source))
                        Impact(_presentation.ImpactVfx, affected, PresentationColor(_action.Element), affected.Side != source.Side, FacingFrom(_action.ActorId, affected));
            foreach (var pair in _hitCounts)
                if (pair.Value > 1 && Find(pair.Key, out var hit)) _ui.Numbers.SpawnHits(hit.Model.HeadPoint, pair.Value, _hitTotals[pair.Key]);
            if (_beat != SkillBeat.None && !Reduced)
            {
                // Aftermath: the impact framing holds briefly (overlapping the recovery pose when the take is still playing).
                float end = _actionEnd > 0 ? Mathf.Min(_actionEnd, _actionLength) : _actionLength;
                float remain = Mathf.Max(0f, end - _actionElapsed);
                if (remain < AftermathHold) yield return Wait(AftermathHold - remain);
            }
            _hud.SetTagsHidden(false);
            if (!_fleeSucceeded && Find(e.ActorId, out var actor) && actor.Alive)
            {
                yield return WaitFlourish(actor);
                // Hit-stop freezes the take, so its held time must not steal the recovery pose; a hero away from its mark
                // shows at most RecoveryCap of follow-through before it turns home. At its mark the take simply plays out
                // into its idle (PlayOnce) while the battle moves on.
                Vector3 back = actor.Home - actor.Model.transform.position; back.y = 0;
                float end = _actionEnd > 0 ? Mathf.Min(_actionEnd, _actionLength) : _actionLength;
                if (back.sqrMagnitude > .01f)
                {
                    float until = Mathf.Min(end, _actionElapsed + RecoveryCap);
                    while (_actionElapsed < until) yield return null;
                }
                StartCoroutine(ReturnHome(actor, back));
            }
            _action = null; _presentation = null; _actionLength = 0; _actionEnd = 0; _strikeClip = null; _perHitProjectile = false;
            _beat = SkillBeat.None; _pendingHit = null; _hitHeld = false; _plan = null; _strikeImpact = _strikeSfx = null;
            // The camera goes back to S0 / S1 while the hero is still running home.
            if (!NextShotFollows()) Establishing(false);
            yield return Wait(.06f);
        }
        /// <summary>Runs (or hops) a unit back to its mark and turns it to face the foe, beside the replay.</summary>
        IEnumerator ReturnHome(BattleDisplayUnit actor, Vector3 back)
        {
            if (actor == null || actor.Model == null) yield break;
            // Per-unit ownership token: a down / revive / teardown cancels it, so this cosmetic run can never be the last
            // writer of a fallen body's transform or animation. Any writing loop checks the token before it commits.
            var token = new object();
            CancelReturn(actor);
            _returning.Add(actor); _returnTokens[actor] = token;
            bool Owned() => _returnTokens.TryGetValue(actor, out var t) && ReferenceEquals(t, token);
            try
            {
                bool special = SpecialReturn(actor, out var returnMove);
                _returnMove.Remove(actor);
                if (back.sqrMagnitude > .01f && special && !Reduced)
                {
                    yield return SpecialHome(actor, returnMove, Owned);
                    if (!Owned()) yield break;
                }
                else if (back.sqrMagnitude > .01f)
                {
                    if (Reduced || !actor.Model.Anim.HasClip("Run"))
                    {
                        actor.Model.Play("Idle", .1f);
                        yield return HopHome(actor, Owned);
                    }
                    else
                    {
                        // Turn toward the mark and jog home at the same stride as the approach, then turn back to the foe.
                        float distance = back.magnitude, time = ApproachTime(actor, distance);
                        SetRunRate(actor, distance / time);
                        actor.Model.Anim.Play("Run", RunFade, false);
                        yield return TurnTo(actor, Quaternion.LookRotation(back / distance), Owned);
                        if (!Owned()) yield break;
                        yield return TraverseHome(actor, time, Owned, PounceArc(actor, distance));
                        if (!Owned()) yield break;
                        if (actor.Model.Anim.HasClip("Idle")) actor.Model.Play("Idle", ClipAnimator.ReturnFade);
                    }
                }
                if (!Owned()) yield break;
                yield return TurnTo(actor, actor.Facing, Owned);
            }
            finally
            {
                // Clear only this return's records; ownership may already have moved to another action's cancel.
                if (Owned()) { _returning.Remove(actor); _returnTokens.Remove(actor); }
                else if (!_returning.Contains(actor)) _returnTokens.Remove(actor);
            }
        }
        /// <summary>Cancels a pending cosmetic return for <paramref name="actor"/> (down / revive / teardown / new take) and snaps it to its Home / facing.</summary>
        void CancelReturn(BattleDisplayUnit actor)
        {
            if (actor == null || !_returnTokens.Remove(actor)) return;
            _returning.Remove(actor);
            // A blink / burrow return may be half faded or under the floor: the snap home also makes the body whole again.
            if (actor.Model != null) { actor.Model.transform.SetPositionAndRotation(actor.Home, actor.Facing); actor.Model.SetDissolve(0); }
        }
        void CancelAllReturns()
        {
            _returning.Clear();
            _returnTokens.Clear();
        }
        /// <summary>Token-checked easing turn; commits a rotation step only while this return still owns the unit, else yields out.</summary>
        IEnumerator TurnTo(BattleDisplayUnit actor, Quaternion facing, System.Func<bool> owned)
        {
            var model = actor.Model.transform; Quaternion from = model.rotation;
            if (!Reduced && Quaternion.Angle(from, facing) > 1f)
            {
                float elapsed = 0;
                while (elapsed < .12f)
                {
                    if (!owned()) yield break;
                    if (!_app.Paused)
                    {
                        elapsed += Dt;
                        model.rotation = Quaternion.Slerp(from, facing, Mathf.SmoothStep(0, 1, elapsed / .12f));
                    }
                    yield return null;
                }
            }
            if (owned()) model.rotation = facing;
        }
        /// <summary>Token-checked walk home; never commits a position step once the return is cancelled.</summary>
        IEnumerator TraverseHome(BattleDisplayUnit actor, float seconds, System.Func<bool> owned, float arc = 0f)
        {
            var model = actor.Model.transform; Vector3 from = model.position, destination = actor.Home;
            float elapsed = 0;
            while (elapsed < seconds)
            {
                if (!owned()) yield break;
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float t = Mathf.Clamp01(elapsed / seconds);
                    model.position = Vector3.Lerp(from, destination, t) + Vector3.up * (Mathf.Sin(Mathf.PI * t) * arc);
                }
                yield return null;
            }
            if (owned()) model.position = destination;
        }
        /// <summary>Token-checked settle home for reduced / clip-less models.</summary>
        IEnumerator HopHome(BattleDisplayUnit actor, System.Func<bool> owned)
        {
            var model = actor.Model.transform; Vector3 from = model.position, destination = actor.Home;
            float seconds = Reduced ? 0f : .3f, elapsed = 0;
            while (elapsed < seconds)
            {
                if (!owned()) yield break;
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float t = Mathf.Clamp01(elapsed / seconds);
                    model.position = Vector3.Lerp(from, destination, 1 - (1 - t) * (1 - t)) + Vector3.up * (Mathf.Sin(Mathf.PI * t) * .4f);
                }
                yield return null;
            }
            if (owned()) model.position = destination;
        }
        /// <summary>Waits (battle clock, bounded by <see cref="ReturnWaitCap"/>) for a unit's cosmetic return to finish; cancels it on timeout.</summary>
        IEnumerator WaitReturn(BattleDisplayUnit unit)
        {
            float elapsed = 0;
            while (_returning.Contains(unit) && elapsed < ReturnWaitCap)
            { if (!_app.Paused) elapsed += Dt; yield return null; }
            CancelReturn(unit);
        }
        /// <summary>True while the actor or one of the action's targets is still on its way home.</summary>
        bool Involved(ActionStartEvent e, BattleDisplayUnit actor)
        {
            if (_returning.Count == 0) return false;
            if (_returning.Contains(actor)) return true;
            if (e.TargetIds != null) foreach (string id in e.TargetIds) if (Find(id, out var unit) && _returning.Contains(unit)) return true;
            return false;
        }
        /// <summary>True when the current action has another strike (damage or miss from its actor) before it ends.</summary>
        bool NextStrikeFollows()
        {
            if (_action == null || _events == null) return false;
            for (int i = _eventIndex + 1; i < _events.Count; i++)
            {
                switch (_events[i])
                {
                    case ActionEndEvent _: return false;
                    case DamageEvent next: if (next.StatusId == null && next.SourceId == _action.ActorId) return true; break;
                    case MissEvent next: if (next.SourceId == _action.ActorId) return true; break;
                }
            }
            return false;
        }
        /// <summary>
        /// Wave bookkeeping before a strike lands. Hits on fresh targets of a group action share a wave; a repeat target
        /// opens the next one, which re-strikes from mid-swing and (multi-hit shots) looses another projectile.
        /// </summary>
        IEnumerator PrepareHit(BattleDisplayUnit target)
        {
            bool newWave = _action.Scope == Scope.Single || _waveTargets.Count == 0 || _waveTargets.Contains(target.Id);
            if (newWave) { _waveTargets.Clear(); _wave++; _waveStop = 0; }
            _waveTargets.Add(target.Id);
            if (!Find(_action.ActorId, out var actor) || !actor.Alive) yield break;
            if (newWave && _wave > 1 && ComboWave(actor))
                yield return Wait(Mathf.Max(0f, _actionLength * Contact(actor.Model, _strikeClip) - _actionElapsed));
            else if (newWave && _wave > 1 && _strikeClip == "Attack" && !Reduced)
            {
                float length = actor.Model.Anim.Length("Attack");
                actor.Model.Anim.PlayFrom("Attack", .25f, .1f);
                _actionLength = length; _actionElapsed = length * .25f; _actionEnd = length * EndFraction(actor, "Attack");
                yield return Wait(Mathf.Min(.1f, length * .15f));
            }
            if (_perHitProjectile) yield return Wait(Shoot(actor, target, PresentationColor(_action.Element)));
        }
        /// <summary>True when the next strike of this action lands on a target not yet hit in the current wave.</summary>
        bool NextHitJoinsWave()
        {
            if (_action == null || _action.Scope == Scope.Single || _events == null) return false;
            for (int i = _eventIndex + 1; i < _events.Count; i++)
            {
                switch (_events[i])
                {
                    case DamageEvent next: return next.StatusId == null && next.SourceId == _action.ActorId && !_waveTargets.Contains(next.TargetId);
                    case MissEvent next: return next.SourceId == _action.ActorId && !_waveTargets.Contains(next.TargetId);
                    case MpChangeEvent _: case TpChangeEvent _: case ShieldChangeEvent _: case StatusRemovedEvent _:
                    case MessageEvent _: case WeaknessDiscoveredEvent _:
                    case EnemyIntentPlannedEvent _: case IntentClearedEvent _: case ChargeStartedEvent _: case ChargeReleasedEvent _:
                    case ChargeCancelledEvent _: case ChainChangedEvent _:
                        continue;
                    default: return false;
                }
            }
            return false;
        }
        IEnumerator Damage(DamageEvent e)
        {
            if (!Find(e.TargetId, out var target)) yield break;
            bool strike = _action != null && e.StatusId == null && e.SourceId == _action.ActorId;
            // A turn-end poison / burn tick (or a counter) on a unit still jogging home lands once it is back on its mark,
            // instead of snapping it there mid-stride; the cancel below stays the hard guarantee.
            if (!strike && _returning.Contains(target)) yield return WaitReturn(target);
            if (strike) yield return PrepareHit(target);
            target.Hp = e.HpAfter; target.MaxHp = e.MaxHp; Sync(target);
            _impactTargets.Add(e.TargetId);
            bool weak = e.ShowEffectiveness && e.Effectiveness == Effectiveness.Weak;
            _ui.Numbers.Spawn(target.Model.HeadPoint, e.Amount, e.Critical ? UINumberStyle.Critical : UINumberStyle.Damage,
                weak, e.ShowEffectiveness && e.Effectiveness == Effectiveness.Resist);
            if (e.Absorbed > 0) Popup(e.TargetId, "흡수 " + e.Absorbed, new Color(.55f, .8f, 1));
            if (_action != null)
            {
                _hitCounts.TryGetValue(e.TargetId, out int count); _hitCounts[e.TargetId] = count + 1;
                _hitTotals.TryGetValue(e.TargetId, out int total); _hitTotals[e.TargetId] = total + e.Amount;
            }
            // A frozen body cannot flinch: a take started under Freeze would sit queued and play turns later when it thaws.
            if (target.Alive && e.Amount > 0 && target.PostureRate > 0f && !GuardedHit(target)) target.Model.Anim.PlayOnce(HitTake(target), "Idle", .15f);
            // A family blow keeps its own palette (venom green, spirit purple); everything else is tinted by the element.
            bool familyBlow = strike && _strikeImpact != null;
            Color tint = familyBlow ? Color.white : PresentationColor(e.Element);
            if (e.Amount > 0) target.Model.Flash(e.Critical ? Color.white : tint, e.Critical ? .2f : Reduced ? .2f : .12f);
            // A hit owns the target's body from here: cancel any cosmetic return so it cannot overwrite the recoil or the fall.
            CancelReturn(target);
            // Recoil away from the attacker side; only from the home mark so it never fights a Move.
            if (!Reduced && e.Amount > 0 && target.Alive && (target.KnockTime > 0 || (target.Model.transform.position - target.Home).sqrMagnitude < .01f))
            {
                float push = Mathf.Clamp((_presentation != null ? _presentation.Shake : .25f) * .32f, .05f, .26f) * (e.Critical ? 1.5f : 1)
                    * (target.Guarding && target.Side == BattleSide.Party ? GuardKnockScale : 1f);   // a braced hero gives less ground
                bool knocked = target.KnockTime > 0;
                float k = knocked ? KnockCurve(KnockLength - target.KnockTime) : 0;
                target.KnockAmount = Mathf.Max(knocked ? target.KnockAmount : 0, push * (target.Boss ? .35f : 1));
                // Re-hits continue outward from the current recoil instead of snapping home first.
                target.KnockTime = KnockLength - KnockOut * (1 - Mathf.Sqrt(1 - Mathf.Clamp01(k)));
            }
            string impact = familyBlow ? _strikeImpact : _presentation != null ? _presentation.ImpactVfx : "impact";
            if (!string.IsNullOrEmpty(impact))
                Effect(impact, HitPoint(target), tint, ImpactScale(target) * (e.Critical ? 1.3f : 1), 0, null, target.Home.y, FacingFrom(e.SourceId, target));
            PlaySound(e.Critical ? "sfx_critical" : _presentation != null && !string.IsNullOrEmpty(_presentation.SfxImpact) ? _presentation.SfxImpact
                : strike && _strikeSfx != null ? _strikeSfx : "sfx_hit");
            if (!Reduced)
            {
                AddTrauma((_presentation != null ? _presentation.Shake : .08f) * (e.Critical ? 1.4f : 1));
                if (strike) _director.Punch(_beat == SkillBeat.Melee ? BattleCameraDirector.StrikePunch : e.Critical ? -3f : -1.5f);
                if (e.Critical) ScreenFlash(Color.white, .22f);
                else if (strike && !_flashed && _presentation != null && _presentation.ScreenFlash) ScreenFlash(tint, .3f);
            }
            if (strike) _flashed = true;
            float stop = _presentation != null ? _presentation.HitStop : .035f;
            if (e.Critical) stop *= 1.6f;
            else if (weak) stop *= 1.3f;
            _waveStop = Mathf.Max(_waveStop, stop);
            // S7 candidate: a hero who survives a big or critical enemy hit. Recorded before a group wave returns early, so
            // an earlier victim of the wave is not lost; consumed once after the wave's shared hit-stop.
            if (!Reduced && !_hitHeld && _pendingHit == null && strike && target.Side == BattleSide.Party && e.HpAfter > 0 && e.Amount > 0 &&
                (e.Critical || e.Amount >= target.MaxHp * .25f) && Find(_action.ActorId, out var striker) && striker.Side == BattleSide.Enemy)
                _pendingHit = target;
            // Group hits land together: stagger the rest of the wave, then freeze once for all of it.
            if (strike && NextHitJoinsWave()) { yield return Wait(.03f); yield break; }
            // Let the recoil enter before freezing it; otherwise hit-stop freezes the untouched pose.
            if (!Reduced && e.Amount > 0) yield return Wait(KnockOut);
            yield return HitStop(strike ? _waveStop : stop);
            yield return ConsumeHitReaction();
            // A killing blow flows straight into the fall; the beat between hits would only delay the death.
            if (e.HpAfter <= 0 && target.Side == BattleSide.Enemy) yield break;
            // The full interval only separates strikes; after the last one a short beat hands over to the aftermath.
            yield return Wait(strike && !NextStrikeFollows() ? LastHitBeat : HitInterval());
        }

        /// <summary>
        /// S7: the closed wave's recorded victim (still standing, HP above zero) gets a short hold, then the enemy-turn
        /// shot resumes. Always consumes the record; never runs without an action (a later status tick has none).
        /// </summary>
        IEnumerator ConsumeHitReaction()
        {
            if (_pendingHit == null) yield break;
            var victim = _pendingHit; _pendingHit = null;
            if (_hitHeld || _action == null || Reduced) yield break;
            Find(_action.ActorId, out var attacker);
            if (victim.Alive && victim.Hp > 0 && _director.HitReaction(victim, attacker))
            {
                _hitHeld = true;
                yield return Wait(BattleCameraDirector.HitHold);
                _director.ResumeAfterHit();
            }
        }
        /// <summary>
        /// Enemy death: the Die take plays fast enough to fit the fall, a held take (Tripo / Mixamo) is replaced by a knock-back and
        /// topple staged in code, a smoke burst marks the moment the body starts to dissolve, and a boss finishes with a stronger
        /// burst and shake. Reduced motion skips the motion and burst and only fades. Runs beside the replay (see <see cref="_dying"/>).
        /// </summary>
        IEnumerator DeathRoutine(BattleDisplayUnit unit)
        {
            _dying++;
            var model = unit.Model; var t = model.transform;
            bool boss = unit.Boss, reduced = Reduced;
            float dissolve = reduced ? ReducedDeathDissolve : boss ? BossDeathDissolve : DeathDissolve;
            float length = model.Anim.Length("Die");
            // Take kinds: short authored deaths (<= 2 s) play as they are; Tripo `defeat_02` (>= 6 s) never falls, so its
            // slump window plays under a code topple; Tripo `fall` (2-6 s) falls by itself: no topple (it would double the
            // rotation), and it starts at the stagger so the body is down before the dissolve.
            bool standingDefeat = length >= ArtLibrary.DefeatTakeMinLength;
            bool fallingTake = length > StaticDieTake && !standingDefeat;
            bool held = standingDefeat;
            float span = fallingTake ? length * (1f - FallTakeStart) : length;   // what is left of the take to play
            float collapse = boss ? Mathf.Clamp(span, BossDeathCollapse, BossDeathCollapseMax) : Mathf.Clamp(span, DeathCollapse, DeathCollapseMax);
            float dissolveAt = reduced ? 0 : Mathf.Max(boss ? BossDeathDissolveAt : DeathDissolveAt, collapse + DeathLand);
            // Zero also survives LateUpdate / hit-stop speed restoration; revive restores DeathRate to one.
            unit.DeathRate = reduced ? 0f : Mathf.Clamp(span / collapse, 1f, DeathRateMax);
            unit.KnockTime = 0;
            if (reduced) model.Anim.SetSpeed(0);   // hold the visible pose: even the first Die keys contain motion
            else if (fallingTake && model.Anim is ClipAnimator dieClips) dieClips.PlayFrom("Die", FallTakeStart, .075f, null);
            else model.Play("Die", .075f);
            Vector3 from = t.position, back = unit.Facing * Vector3.back;
            float push = reduced ? 0 : boss ? .12f : .4f;
            float tilt = reduced || !held ? 0 : boss ? 70f : 80f, roll = (unit.Slot % 2 == 0 ? 1f : -1f) * 12f;
            if (!reduced)
            {
                AddTrauma(boss ? .7f : .25f);
                if (boss) { ScreenFlash(new Color(1, .95f, .8f), .3f); _director.Punch(-3f); }
            }
            bool burst = false;
            float elapsed = 0, total = dissolveAt + dissolve;
            while (elapsed < total || _app.Paused || _hitstop)
            {
                // Match the skeletal clock when a later hit freezes every unit during this concurrent death.
                if (!_app.Paused && !_hitstop)
                {
                    elapsed += Dt;
                    float k = Mathf.Clamp01(elapsed / collapse), knock = Mathf.Clamp01(elapsed / (collapse * .5f));
                    t.position = from + back * (push * (1 - (1 - knock) * (1 - knock)));
                    if (tilt > 0) t.rotation = unit.Facing * Quaternion.Euler(-tilt * k * k * (3 - 2 * k), 0, roll * k);
                    if (!burst && elapsed >= dissolveAt)
                    {
                        burst = true;
                        if (!reduced)
                            Effect(boss ? "break" : "smoke", model.CenterPoint, boss ? new Color(1, .8f, .45f) : new Color(.82f, .84f, .92f),
                                ImpactScale(unit) * (boss ? 1.3f : .6f), 0, null, unit.Home.y);
                    }
                    model.SetDissolve((elapsed - dissolveAt) / dissolve);
                }
                yield return null;
            }
            model.SetDissolve(1);
            _dying--;
        }
        /// <summary>Waits until every staged enemy death has finished (they run concurrently, so this is the slowest one's remainder).</summary>
        IEnumerator WaitDeaths()
        {
            while (_dying > 0) yield return null;
        }

        /// <summary>
        /// Battle entrance: both sides run onto their marks while the camera sweeps from a low enemy-side angle into
        /// the establishing shot, under an ENCOUNTER / F.O.E call-out. Boss battles use <see cref="BossEntrance"/> instead.
        /// </summary>
        IEnumerator Intro()
        {
            if (_setup.Kind == BattleKind.Boss) { yield return BossEntrance(); yield break; }
            var movers = new List<(BattleDisplayUnit Unit, Vector3 From)>();
            foreach (var unit in _units.Values)
            {
                if (!unit.Alive) continue;
                Vector3 from = unit.Home + unit.Facing * Vector3.back * (unit.Side == BattleSide.Party ? 3.4f : 4.6f);
                unit.Model.transform.position = from;
                // Steady stride, then a short settle onto the mark (the Run rate matches the steady stretch).
                SetRunRate(unit, (unit.Side == BattleSide.Party ? 3.4f : 4.6f) / (IntroRun - IntroSettle * .5f)); unit.Model.Play("Run");
                movers.Add((unit, from));
            }
            // Low enemy-side angle, then one eased sweep into the establishing shot while both sides run onto their marks.
            _director.CutTo(new Vector3(-7.8f, 1.5f, 5.2f), new Vector3(0f, 1.3f, 2.2f), BattleCameraDirector.HomeFov + 10f);
            _director.Establishing(false, IntroSweep, CameraEase.InOutCubic);
            _flashAlpha = .6f; _flash.color = new Color(1, 1, 1, _flashAlpha);
            var names = new List<string>();
            // The encounter call-out names each kind once (display letters are for telling units apart later).
            foreach (var unit in _units.Values) if (unit.Side == BattleSide.Enemy && !names.Contains(unit.BaseName)) names.Add(unit.BaseName);
            bool foe = _setup.Kind == BattleKind.Foe;
            _hud.Announce(foe ? "F.O.E" : "ENCOUNTER", string.Join(" · ", names) + (foe ? " 출현!" : " 이(가) 나타났다!"),
                foe ? UITheme.Danger : UITheme.Dawn, .8f);
            AudioManager.Instance.PlaySfx("sfx_encounter"); AudioManager.Instance.PlaySfx("sfx_wind", .55f, 1.2f);
            float elapsed = 0f;
            bool settling = false;
            while (elapsed < IntroRun)
            {
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float k = SettleCurve(elapsed, IntroRun, IntroSettle);
                    foreach (var (unit, from) in movers) unit.Model.transform.position = Vector3.Lerp(from, unit.Home, k);
                    // The legs blend out of the run while the body slows, instead of running on the spot after it stopped.
                    if (!settling && elapsed >= IntroRun - IntroSettle)
                    { settling = true; foreach (var (unit, _) in movers) unit.Model.Play("Idle", IntroSettle); }
                }
                yield return null;
            }
            foreach (var (unit, _) in movers)
            {
                unit.Model.transform.position = unit.Home;
                unit.Model.Play(unit.Side == BattleSide.Enemy && foe ? "Cast" : "Idle");
            }
            yield return Wait(foe ? .9f : .55f);
            foreach (var (unit, _) in movers) unit.Model.Play("Idle");
        }

        /// <summary>Reduced motion: no run-on or camera move. Boss battles still get a short static name card.</summary>
        IEnumerator ReducedIntro()
        {
            if (_setup.Kind != BattleKind.Boss) { yield return Wait(.35f); yield break; }
            PlaceAtHomes();
            AnnounceBoss(EntranceBoss(), .5f);
            AudioManager.Instance.PlaySfx("sfx_encounter");
            yield return Wait(.6f);
        }

        /// <summary>
        /// Boss entrance, capped at <see cref="BossEntranceMax"/> seconds of battle time: everyone already stands on their
        /// marks, the boss roars (or strikes) under its name card and the area name, and the camera pushes in toward it
        /// and back. Replaces the run-on intro for boss battles; it is never stacked on it.
        /// </summary>
        IEnumerator BossEntrance()
        {
            var boss = EntranceBoss();
            PlaceAtHomes();
            AnnounceBoss(boss, .8f);
            AudioManager.Instance.PlaySfx("sfx_encounter");
            if (boss == null) { yield return Wait(.55f); yield break; }
            float clip = PlayEntranceClip(boss);
            _flashAlpha = .3f; _flash.color = new Color(UITheme.Danger.r, UITheme.Danger.g, UITheme.Danger.b, _flashAlpha);
            AddTrauma(.2f);
            // Push in toward the boss and back out, each leg one eased blend (blends already scale with battle speed).
            _director.BossPush(boss, BossPushLeg);
            yield return Wait(BossPushLeg);
            _director.Establishing(false, BossPushLeg, CameraEase.InOutCubic);
            yield return Wait(BossPushLeg);
            // Let the roar read, but never run the entrance past its cap.
            yield return Wait(Mathf.Min(BossEntranceMax - 2f * BossPushLeg, Mathf.Max(.15f, clip - 2f * BossPushLeg)));
        }
        /// <summary>The unit whose data is a boss (EnemyDef.IsBoss); the first living enemy if the group has none.</summary>
        BattleDisplayUnit EntranceBoss()
        {
            BattleDisplayUnit first = null;
            foreach (var unit in _units.Values)
            {
                if (unit.Side != BattleSide.Enemy || !unit.Alive) continue;
                if (_app.DB.Enemies.TryGetValue(unit.DefId, out var def) && def.IsBoss) return unit;
                if (first == null) first = unit;
            }
            return first;
        }
        void PlaceAtHomes()
        {
            foreach (var unit in _units.Values)
            {
                unit.KnockTime = 0;
                if (!unit.Alive && unit.Side == BattleSide.Party) { LayFallen(unit); continue; }   // a fallen hero stays down
                unit.Model.transform.SetPositionAndRotation(unit.Home, unit.Facing);
                if (unit.Alive && unit.Model.Anim.HasClip("Idle")) unit.Model.Anim.Play("Idle", .1f, false);
            }
        }
        /// <summary>Roar when the rig has one, else Attack, then back to Idle. Returns the take's length (0 when none).</summary>
        static float PlayEntranceClip(BattleDisplayUnit boss)
        {
            var anim = boss.Model.Anim;
            string take = anim.HasClip("Roar") ? "Roar" : anim.HasClip("Attack") ? "Attack" : null;
            string idle = anim.HasClip("Idle") ? "Idle" : null;
            if (take == null) return 0f;
            anim.PlayOnce(take, idle, .1f);
            return anim.Length(take);
        }
        void AnnounceBoss(BattleDisplayUnit boss, float hold)
        {
            string area = _floor != null && !string.IsNullOrEmpty(_floor.AreaName) ? _floor.AreaName : "BOSS BATTLE";
            // The card runs on unscaled UI time; shorten its hold so it clears with the faster entrance at 1.5x / 2x.
            _hud.Announce(boss != null ? boss.Name : "BOSS BATTLE", area, UITheme.Danger, hold / Mathf.Max(1f, Speed));
        }

        IEnumerator Finish(BattleOutcome outcome)
        {
            _commandUnit = null; _hud.Lock(); _outcome = true;
            // Heroes still jogging home reach their marks before the outcome is staged.
            float settle = 0;
            while (_returning.Count > 0 && settle < ReturnWaitCap) { if (!_app.Paused) settle += Dt; yield return null; }
            CancelAllReturns();
            // Resolve exactly once and use that cached report for both routing and the result UI. Save before
            // any ceremony/toast/acknowledgement; never compute eligibility by applying the outcome again.
            var resolution = _app.Dungeon.ResolveBattle(outcome);
            _app.Save();
            bool fast = PartyStats.CanUseFastResults(_app.DB, _setup, outcome, resolution.Report);
            if (!Reduced && !fast) StageOutcome(outcome.Result); else Establishing(false);
            foreach (var unit in _units.Values)
                if (unit.Side == BattleSide.Party && unit.Alive)
                {
                    unit.PostureRate = 1f;   // the battle is over: nobody stays frozen or dazed through the victory pose
                    unit.Model.Play(outcome.Result == BattleResult.Victory ? "Victory" : outcome.Result == BattleResult.Fled ? "Run" : "Idle");
                }
            if (outcome.Result != BattleResult.Fled)
                AudioManager.Instance.PlayJingle(outcome.Result == BattleResult.Victory ? "jingle_victory" : "jingle_defeat");
            if (outcome.Result == BattleResult.Fled)
            {
                float elapsed = 0;
                while (elapsed < .65f)
                {
                    if (!_app.Paused)
                    {
                        elapsed += Dt;
                        foreach (var unit in _units.Values)
                            if (unit.Side == BattleSide.Party && unit.Alive)
                                unit.Model.transform.position += transform.TransformDirection(Vector3.back) * (Dt * FleeSpeed);
                    }
                    yield return null;
                }
            }
            else if (fast) yield return CeremonyWait(.8f);
            else yield return Wait(Reduced ? .6f : 2.1f);
            bool acknowledged = false;
            Action acknowledge = () => { if (!acknowledged) acknowledged = true; };
            if (fast) _hud.FastRewards(resolution.Report, acknowledge);
            else _hud.Rewards(outcome, resolution.Report, acknowledge);
            while (!acknowledged) yield return null;
            yield return Wait(.12f);
            _finished = true; Playing = false;
            Restore();
            var callback = _completed; _completed = null;
            callback?.Invoke(outcome);
        }
        IEnumerator CeremonyWait(float seconds)
        {
            float elapsed = 0;
            while (elapsed < seconds || _app.Paused)
            { if (!_app.Paused) elapsed += Time.unscaledDeltaTime; yield return null; }
        }
        /// <summary>Victory: the camera swings round in front of the party for their poses. Defeat: it lifts away and the arena dims.</summary>
        void StageOutcome(BattleResult result)
        {
            switch (result)
            {
                case BattleResult.Victory:
                    _director.Victory();
                    _hud.Announce("VICTORY", "전투에서 승리했다!", UITheme.GoldBright, 1.2f);
                    break;
                case BattleResult.Defeat:
                    _director.Defeat();
                    _dimTarget = .45f;
                    _hud.Announce("전멸…", "파티가 쓰러졌다", UITheme.Danger, 1.2f);
                    break;
                case BattleResult.Fled:
                    Establishing(false);
                    _hud.Announce("도주 성공", "무사히 빠져나왔다", UITheme.TextDim, .5f);
                    break;
            }
        }

        void Sync(BattleDisplayUnit unit) { _hud.Sync(unit); UpdateAuras(unit); unit.PostureRate = Posture(unit); }
        void UpdateAuras(BattleDisplayUnit unit)
        {
            if (!_auras.TryGetValue(unit.Id, out var handles))
            { handles = new Dictionary<string, VfxHandle>(); _auras.Add(unit.Id, handles); }
            var desired = _desiredAuras; desired.Clear();
            if (unit.Alive)
            {
                if (unit.Guarding) desired["guard_loop"] = new Color(.45f, .75f, 1);
                if (unit.Broken) desired["break_loop"] = new Color(1, .65f, .15f);
                foreach (var status in unit.Statuses.Values)
                {
                    if (status.Type == StatusEffectType.Barrier || status.Type == StatusEffectType.ManaShield || status.Type == StatusEffectType.Invincible)
                    {
                        if (_app.DB.Statuses.TryGetValue(status.Id, out var def) && def.Tint != null && def.Tint.Length >= 3)
                            desired["shield"] = new Color(def.Tint[0], def.Tint[1], def.Tint[2]);
                        else desired["shield"] = new Color(.55f, .85f, 1);
                    }
                    // Looping per-status glyph recipes carry their own colours.
                    string key = "status_" + status.Id;
                    if (!_vfx.Supports(key)) key = status.Beneficial ? "status_attack_up" : "status_attack_down";
                    if (_vfx.Supports(key)) desired[key] = Color.white;
                }
            }
            var remove = _removedAuras; remove.Clear();
            foreach (var pair in handles)
                if (!desired.ContainsKey(pair.Key)) { pair.Value.Stop(); remove.Add(pair.Key); }
            foreach (string key in remove) handles.Remove(key);
            foreach (var pair in desired)
                if (!handles.ContainsKey(pair.Key))
                {
                    // Stack several status glyph rings instead of orbiting them through each other.
                    int stacked = 0;
                    if (pair.Key.StartsWith("status_", StringComparison.Ordinal))
                        foreach (string key in handles.Keys) if (key.StartsWith("status_", StringComparison.Ordinal)) stacked++;
                    handles.Add(pair.Key, Effect(pair.Key, unit.Model.CenterPoint + Vector3.up * (stacked * .16f), pair.Value,
                        Mathf.Max(.7f, unit.Model.Radius * 1.4f), 0, unit.Model.transform, unit.Home.y));
                }
        }
        VfxHandle Effect(string key, Vector3 position, Color tint, float scale = 1, float duration = 0, Transform follow = null, float ground = float.NaN,
            Vector3? facing = null)
        {
            var handle = _vfx.Play(key, position, tint, scale, duration, follow, ground, facing); TrackEffect(handle); return handle;
        }
        /// <summary>Direction of a blow (acting unit toward the target) for impact meshes that point along it; null when unknown or the same unit.</summary>
        Vector3? FacingFrom(string sourceId, BattleDisplayUnit target)
        {
            if (string.IsNullOrEmpty(sourceId) || target == null || target.Model == null || !Find(sourceId, out var source) || source.Model == null) return null;
            // A self-cast faces where its caster faces (no recipe aligns a self-cast layer except the ones placed `ahead`).
            if (source == target) return source.Facing * Vector3.forward;
            Vector3 direction = target.Model.CenterPoint - source.Model.CenterPoint;
            return direction.sqrMagnitude > .01f ? direction : (Vector3?)null;
        }
        /// <summary>Direction from the caster to a group effect's center for `align` layers; null when the caster stands on it.</summary>
        static Vector3? AreaFacing(BattleDisplayUnit actor, Vector3 center)
        {
            if (actor == null || actor.Model == null) return null;
            Vector3 direction = center - actor.Model.CenterPoint;
            return direction.sqrMagnitude > .01f ? direction : (Vector3?)null;
        }
        /// <summary>Hostile impacts sit on the camera side of the body so sparks are not buried in large models.</summary>
        void Impact(string key, BattleDisplayUnit unit, Color tint, bool hostile, Vector3? facing = null) =>
            Effect(key, hostile ? HitPoint(unit) : unit.Model.CenterPoint, tint, ImpactScale(unit), 0, null, unit.Home.y, facing);
        Vector3 HitPoint(BattleDisplayUnit unit)
        {
            Vector3 center = unit.Model.CenterPoint;
            return center + (_camera.transform.position - center).normalized * (unit.Model.Radius * .8f + .1f);
        }
        static float ImpactScale(BattleDisplayUnit unit) => Mathf.Clamp(unit.Model.Height / 1.3f, 1f, 2f) * 1.2f;
        void AddTrauma(float shake) => _director.AddTrauma(shake);
        void ScreenFlash(Color color, float alpha)
        {
            _flash.color = new Color(color.r, color.g, color.b, alpha); _flashAlpha = alpha; _flashed = true;
        }
        /// <summary>Recoil displacement (0..1) at <paramref name="elapsed"/> seconds: quick ease-out, then a slower settle.</summary>
        static float KnockCurve(float elapsed)
        {
            if (elapsed < KnockOut) { float t = elapsed / KnockOut; return 1 - (1 - t) * (1 - t); }
            return 1 - Mathf.SmoothStep(0, 1, (elapsed - KnockOut) / (KnockLength - KnockOut));
        }
        void TrackEffect(VfxHandle handle)
        {
            for (int i = _effects.Count - 1; i >= 0; i--)
                if (!_effects[i].IsPlaying) _effects.RemoveAt(i);
            _effects.Add(handle);
        }
        bool Find(string id, out BattleDisplayUnit unit)
        {
            if (id == null) { unit = null; return false; }
            return _units.TryGetValue(id, out unit);
        }
        void Popup(string id, string text, Color color, float size = 34f)
        { if (Find(id, out var unit)) _ui.Numbers.SpawnText(unit.Model.HeadPoint, text, color, size); }
        void RefreshOrder() => _hud.ShowOrder(_round, _order, _active);
        /// <summary>
        /// HUD target focus. A focused target frames actor and target (S2); clearing the focus goes back to the command
        /// shot while the menu is open (cancel / back), else to the establishing shot.
        /// </summary>
        void PreviewTarget(string id)
        {
            foreach (var unit in _units.Values) unit.Model.SetTint(unit.Id == id ? new Color(1.12f, 1.05f, .8f) : Color.white);
            // The outcome shot (victory orbit / defeat lift) holds through the results; the HUD's Lock must not end it.
            if (_director == null || _outcome) return;
            BattleDisplayUnit actor = null;
            bool commanding = _commandUnit != null && !Playing && Find(_commandUnit, out actor);
            if (id != null && Find(id, out var target))
            {
                if (commanding) _director.Target(actor, target);
                else _director.Action(target, null, false);
            }
            else if (commanding) _director.Command(actor);
            else Establishing(false);
        }
        void Establishing(bool instant) => _director?.Establishing(instant);
        void LateUpdate()
        {
            if (!_initialized || _restored || _camera == null) return;
            foreach (var unit in _units.Values) unit.Model.Anim.SetSpeed(_app.Paused || _hitstop ? 0 : Speed * unit.DeathRate * BodyRate(unit));
            // Hit-stop freezes the units and drags effect playback to a crawl (never in reduced mode, where HitStop is skipped).
            if (_vfx != null) _vfx.TimeScale = _app.Paused ? 0 : _hitstop && !Reduced ? Speed * HitStopVfxRate : Speed;
            if (_app.Paused) return;
            if (!_hitstop) _clock += Dt;
            if (!_hitstop && _actionLength > 0) _actionElapsed += Dt;
            if (Reduced)
            {
                _dimTarget = 0;
                if (_flashAlpha > 0) { _flashAlpha = 0; _flash.color = new Color(1, 1, 1, 0); }
            }
            foreach (var unit in _units.Values)
            {
                if (unit.KnockTime <= 0) continue;
                // Ease out on contact, settle home; frozen during hit-stop.
                if (!_hitstop) unit.KnockTime = Mathf.Max(0, unit.KnockTime - Dt);
                Vector3 back = unit.Facing * Vector3.back;
                unit.Model.transform.position = unit.Home + back * (unit.KnockAmount * KnockCurve(KnockLength - unit.KnockTime));
            }
            if (_dim != null && !Mathf.Approximately(_dimAlpha, _dimTarget))
            {
                _dimAlpha = Mathf.MoveTowards(_dimAlpha, _dimTarget, Time.unscaledDeltaTime * 2.2f);
                var d = _dim.color; d.a = _dimAlpha; _dim.color = d;
            }
            // Camera framing runs here, before the HUD (execution order 200) places its tags from this frame's camera.
            _director.Tick(Speed, Reduced);
            // The signature cut-in band runs on the battle clock (speed scaled, frozen while paused: LateUpdate returned above).
            _hud.AdvanceCutIn(Dt);
            if (_flashAlpha > 0)
            {
                _flashAlpha = Mathf.MoveTowards(_flashAlpha, 0, Time.unscaledDeltaTime * 2.5f);
                var c = _flash.color; c.a = _flashAlpha; _flash.color = c;
            }
        }
        IEnumerator Wait(float seconds)
        {
            float elapsed = 0;
            while (elapsed < seconds || _app.Paused)
            { if (!_app.Paused) elapsed += Dt; yield return null; }
        }
        IEnumerator HitStop(float seconds)
        {
            if (Reduced || seconds <= 0) yield break;
            _hitstop = true;
            foreach (var unit in _units.Values) unit.Model.Anim.SetSpeed(0);
            yield return Wait(seconds);
            _hitstop = false;
            foreach (var unit in _units.Values) unit.Model.Anim.SetSpeed(_app.Paused ? 0 : Speed * unit.DeathRate * BodyRate(unit));
        }
        IEnumerator Face(BattleDisplayUnit unit, Quaternion facing)
        {
            var model = unit.Model.transform;
            Quaternion from = model.rotation;
            if (!Reduced && Quaternion.Angle(from, facing) > 1f)
            {
                float elapsed = 0;
                while (elapsed < .12f)
                {
                    if (!_app.Paused)
                    {
                        elapsed += Dt;
                        model.rotation = Quaternion.Slerp(from, facing, Mathf.SmoothStep(0, 1, elapsed / .12f));
                    }
                    yield return null;
                }
            }
            model.rotation = facing;
        }
        /// <summary>Out-quad move; <paramref name="arc"/> lifts the path into a hop.</summary>
        IEnumerator Move(BattleDisplayUnit unit, Vector3 destination, float seconds, float arc = 0, bool linear = false)
        {
            if (unit.KnockTime > 0) { unit.KnockTime = 0; unit.Model.transform.position = unit.Home; }
            Vector3 from = unit.Model.transform.position; float elapsed = 0;
            while (elapsed < seconds)
            {
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float t = Mathf.Clamp01(elapsed / seconds), k = linear ? t : 1 - (1 - t) * (1 - t);
                    unit.Model.transform.position = Vector3.Lerp(from, destination, k) + Vector3.up * (Mathf.Sin(Mathf.PI * t) * arc);
                }
                yield return null;
            }
            unit.Model.transform.position = destination;
        }
        static float MovementTime(float distance) => Mathf.Clamp(distance / 10f, .22f, .36f);
        float HitInterval() => _presentation != null && _presentation.Tier >= 2
            ? Mathf.Max(.1f, Mathf.Max(.12f, _presentation.HitInterval) * Tier2HitInterval)
            : Mathf.Max(.12f, _presentation != null ? _presentation.HitInterval : .18f);
        static string ActionName(ActionKind kind)
        {
            switch (kind)
            { case ActionKind.Attack: return "공격"; case ActionKind.Guard: return "방어"; case ActionKind.Flee: return "도주"; case ActionKind.Summon: return "소환"; default: return "행동"; }
        }
        Color PresentationColor(int element)
        {
            var color = _presentation?.LightColor;
            return color != null && color.Length >= 3 ? new Color(color[0], color[1], color[2]) : ElementColor(element);
        }
        static Color ElementColor(int element)
        {
            switch ((Element)element)
            {
                case Element.Fire: return new Color(1, .35f, .1f); case Element.Ice: return new Color(.4f, .85f, 1);
                case Element.Thunder: return new Color(1, .9f, .25f); case Element.Dark: return new Color(.7f, .35f, 1);
                case Element.Holy: return new Color(1, .94f, .6f); default: return new Color(.95f, .85f, .65f);
            }
        }
        static string ElementSound(int element)
        {
            switch ((Element)element)
            { case Element.Fire: return "sfx_fire"; case Element.Ice: return "sfx_ice"; case Element.Thunder: return "sfx_lightning"; case Element.Dark: return "sfx_dark"; case Element.Holy: return "sfx_light"; default: return "sfx_staff"; }
        }
        static string StatusSound(StatusEffectType type)
        {
            switch (type)
            {
                case StatusEffectType.Poison: return "sfx_poison"; case StatusEffectType.Burn: return "sfx_burn";
                case StatusEffectType.Freeze: return "sfx_freeze"; case StatusEffectType.Sleep: return "sfx_sleep";
                case StatusEffectType.Silence: return "sfx_silence"; case StatusEffectType.Stun: return "sfx_stun";
                default: return "sfx_debuff";
            }
        }
        static string WeaponSound(BattleDisplayUnit actor)
        {
            switch (actor.Side == BattleSide.Party ? Abyss.Logic.GameDB.Instance?.ClassOf(actor.DefId) : actor.DefId)
            { case "warrior": return "sfx_sword"; case "archer": return "sfx_bow"; case "mage": case "cleric": return "sfx_staff"; default: return "sfx_hit"; }
        }
        static void PlaySound(string id) { if (!string.IsNullOrEmpty(id)) AudioManager.Instance.PlaySfx(id); }
        /// <summary>Directional rim from behind the enemy line, aimed back over them toward the party (silhouette separation). The cool one is straight on, the warm one comes in from the side for a warm edge on the enemies.</summary>
        Light CreateRimLight(string name, Color color, float intensity, Vector3 direction)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            go.transform.rotation = Quaternion.LookRotation(direction);
            var light = go.AddComponent<Light>();
            light.type = LightType.Directional;
            light.color = color;
            light.intensity = intensity;
            light.shadows = LightShadows.None;
            return light;
        }
        void Restore()
        {
            if (_restored) return; _restored = true;
            CancelAllReturns(); _beat = SkillBeat.None; _pendingHit = null;   // no cosmetic return, skill beat or S7 record outlives the battle
            _plan = null; _returnMove.Clear(); _flourishing.Clear(); _moveUses.Clear(); _restScale.Clear();
            foreach (var effect in _effects) effect.Stop(); _effects.Clear(); _auras.Clear();
            if (_vfx != null) _vfx.TimeScale = 1;
            if (_ui != null) { _ui.Numbers.Clear(); _ui.Dialog.Close(); }
            if (_flash != null) { _flash.gameObject.SetActive(false); Destroy(_flash.gameObject); }
            if (_dim != null) { _dim.gameObject.SetActive(false); Destroy(_dim.gameObject); }
            if (_rim != null) { Destroy(_rim.gameObject); _rim = null; }
            if (_warmRim != null) { Destroy(_warmRim.gameObject); _warmRim = null; }
            if (_hud != null) { _hud.Lock(); _hud.enabled = false; }
            _director?.Restore();
            if (_app != null && _oldAtmosphere != null) { _app.Atmosphere.Apply(_oldAtmosphere); _app.Atmosphere.SetupCamera(_camera, _oldOutline); }
        }
        void OnDestroy()
        {
            StopAllCoroutines(); Playing = false; _completed = null;
            if (_initialized) Restore();
            _units.Clear();
        }
    }
}
