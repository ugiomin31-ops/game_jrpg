using System;
using System.Collections;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Battle;
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
    public sealed class BattleView : MonoBehaviour
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
        Vector3 _cameraPosition, _cameraLook, _cameraBasePosition, _oldPosition;
        Quaternion _oldRotation, _cameraBaseRotation;
        float _cameraRate = 7f;
        // Establishing shot: close enough that 1.3 m heroes and the monsters read on a landscape phone.
        static readonly Vector3 CameraHome = new Vector3(0f, 3.6f, -10.2f), CameraAim = new Vector3(1.4f, 1.05f, 0.6f);
        const float CameraFov = 42f;
        float _oldFov, _fov = 43, _fovBase = 43, _fovPunch, _trauma, _flashAlpha, _dimAlpha, _dimTarget, _actionElapsed, _actionLength, _waveStop;
        // Recoil: out over KnockOut, settle home over the rest.
        const float KnockLength = .25f, KnockOut = .05f;
        int _round, _wave, _eventIndex;
        string _active, _strikeClip;
        IReadOnlyList<BattleEvent> _events;
        bool _initialized, _finished, _restored, _hitstop, _fleeSucceeded, _wasReduced, _perHitProjectile, _flashed;
        AtmospherePreset _oldAtmosphere;
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
            _oldPosition = _camera.transform.position; _oldRotation = _camera.transform.rotation; _oldFov = _camera.fieldOfView;
            _oldAtmosphere = app.Atmosphere.Current;
            FloorDef floor = null;
            foreach (var candidate in app.DB.Floors) if (candidate.Id == setup.FloorId) { floor = candidate; break; }
            if (floor == null) throw new InvalidOperationException("Battle floor not found: " + setup.FloorId);
            var atmosphere = AtmospherePreset.ForTileset(floor.Tileset);
            app.Atmosphere.Apply(atmosphere); app.Atmosphere.SetupCamera(_camera);
            var arena = ArtLibrary.SpawnStatic(ArtLibrary.EnvPath(floor.Tileset, "arena"), transform);
            EnvironmentProcessor.Process(arena, atmosphere.TorchColor);
            _ui = UIRoot.Create(); _ui.Numbers.Camera = _camera;
            _vfx = VfxLibrary.Create(); _vfx.Camera = _camera;
            // Created before the HUD so the ultimate dim sits over the arena but under the cut-in and gauges.
            _dim = UIFactory.Fill(app.UI.Content, new Color(0, 0, 0, 0), "Battle dim");
            _hud = gameObject.AddComponent<BattleHUD>();
            _hud.Initialize(app.UI.Content, _camera, app.DB, Submit, ToggleAuto, PreviewTarget);
            _hud.EnableSpeedToggle(SpeedLabel, ToggleSpeed);
            _flash = UIFactory.Fill(app.UI.Content, new Color(1, 1, 1, 0), "Battle flash");
            Engine = new BattleEngine(app.DB, setup);
            string music = setup.Kind == BattleKind.Boss ? "bgm_boss" : "bgm_battle";
            if (floor.Index == 11 && setup.Kind == BattleKind.Boss) music = "bgm_finalboss";
            AudioManager.Instance.PlayBgm(music);
            Establishing(true);
            Playing = true;
            StartCoroutine(Replay(Engine.Start(), true));
        }

        public void Submit(BattleCommand command)
        {
            if (_finished || Playing || _app.Paused || Engine.State != BattleEngineState.AwaitingCommand) return;
            _hud.Lock(); Playing = true;
            StartCoroutine(Replay(Engine.Submit(command), false));
        }
        public void SetAuto(bool enabled)
        {
            if (_finished) return;
            Auto = enabled; _hud.SetAuto(enabled);
            if (enabled && !Playing && Engine.State == BattleEngineState.AwaitingCommand)
            {
                _hud.Lock(); Playing = true; StartCoroutine(AutoInput());
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
            if (!Auto) { Playing = false; _hud.ShowCommands(Engine); yield break; }
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
                if (initial && events[i] is BattleStartEvent) yield return Reduced ? Wait(.35f) : Intro();
            }
            Playing = false;
            if (Engine.State == BattleEngineState.AwaitingCommand)
            {
                Establishing(false);
                if (Auto) { Playing = true; StartCoroutine(AutoInput()); }
                else _hud.ShowCommands(Engine);
            }
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
                    if (Find(e.UnitId, out var turn)) { turn.Guarding = false; Sync(turn); }
                    RefreshOrder();
                    break;
                case TurnEndEvent e:
                    if (Find(e.Unit.Id, out var ended)) { ended.Apply(e.Unit); Sync(ended); }
                    break;
                case CommandRequestedEvent e:
                    _active = e.UnitId; RefreshOrder();
                    break;
                case TurnSkippedEvent e:
                    Popup(e.UnitId, e.Broken ? "BREAK · 행동 불가" : "행동 불가", new Color(1, .7f, .25f));
                    yield return Wait(.35f); break;
                case ActionStartEvent e:
                    yield return StartAction(e); break;
                case ActionEndEvent e:
                    yield return EndAction(e); break;
                case DamageEvent e:
                    yield return Damage(e); break;
                case MissEvent e:
                    if (Find(e.TargetId, out var missed))
                    {
                        bool strike = _action != null && e.SourceId == _action.ActorId;
                        if (strike) yield return PrepareHit(missed);
                        _ui.Numbers.Spawn(missed.Model.HeadPoint, 0, UINumberStyle.Miss);
                        _impactTargets.Add(e.TargetId);
                        PlaySound("sfx_miss");
                        yield return strike && NextHitJoinsWave() ? Wait(.03f) : Wait(HitInterval());
                    }
                    break;
                case HealEvent e:
                    if (Find(e.TargetId, out var healed))
                    {
                        healed.Hp = e.HpAfter; healed.MaxHp = e.MaxHp; Sync(healed);
                        _ui.Numbers.Spawn(healed.Model.HeadPoint, e.Amount, UINumberStyle.Heal);
                        _impactTargets.Add(e.TargetId);
                        Effect("heal", healed.Model.CenterPoint, new Color(.35f, 1, .6f), 1, 0, null, healed.Home.y);
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
                        if (_impactTargets.Add(e.UnitId) && _action != null && _presentation != null && !string.IsNullOrEmpty(_presentation.ImpactVfx))
                            Impact(_presentation.ImpactVfx, applied, PresentationColor(_action.Element), !e.Beneficial);
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
                        broken.Broken = true; Sync(broken); Popup(e.UnitId, "BREAK!", new Color(1, .75f, .2f), 64f);
                        Effect("break", HitPoint(broken), new Color(1, .65f, .15f), 1.4f * ImpactScale(broken) / 1.2f, 0, null, broken.Home.y);
                        PlaySound("sfx_critical");
                        if (!Reduced) { AddTrauma(.5f); _fovPunch = Mathf.Min(_fovPunch, -3f); ScreenFlash(new Color(1, .7f, .25f), .35f); }
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
                        down.Alive = false; down.Hp = 0; down.Guarding = false; Sync(down);
                        down.Model.Play("Die", .075f); PlaySound("sfx_death");
                        yield return Wait(Mathf.Max(.35f, down.Model.Anim.Length("Die")));
                        if (down.Side == BattleSide.Enemy) yield return down.Model.DissolveOut(Reduced ? .15f : .45f);
                        RefreshOrder();
                    }
                    break;
                case ReviveEvent e:
                    if (Find(e.UnitId, out var revived))
                    {
                        revived.Alive = true; revived.Hp = e.Hp; revived.MaxHp = e.MaxHp;
                        revived.Model.SetDissolve(0);
                        if (revived.Side == BattleSide.Party)
                            // Authored frame zero matches the held Die endpoint, including its grounded root.
                            revived.Model.Anim.PlayOnce("Revive", "Idle", 0f);
                        else revived.Model.Play("Idle", .25f);
                        Sync(revived);
                        Effect("revive", revived.Model.CenterPoint, new Color(1, .9f, .55f), 1, 0, null, revived.Home.y);
                        Popup(e.UnitId, "부활", new Color(1, .95f, .6f)); PlaySound("sfx_revive");
                        yield return Wait(revived.Side == BattleSide.Party ? revived.Model.Anim.Length("Revive") : .4f);
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
                    var summon = Spawn(e.Unit); summon.Model.SetDissolve(1);
                    Effect("summon", summon.Model.CenterPoint, new Color(.7f, .35f, 1), 1.2f, 0, null, summon.Home.y);
                    _hud.Log(summon.Name + " 등장!"); PlaySound("sfx_dark");
                    yield return summon.Model.DissolveIn(Reduced ? .15f : .45f);
                    yield return Wait(.2f);
                    break;
                case BossPhaseEvent e:
                    if (Find(e.UnitId, out var boss))
                    {
                        ActiveShot(boss, null, true);
                        boss.Model.PlayOnce("Cast");
                        float phaseStarted = Time.time;
                        _hud.CutIn(boss.Name + " · PHASE " + (e.PhaseIndex + 1), e.Line);
                        PlaySound("sfx_debuff");
                        if (!string.IsNullOrEmpty(e.Line))
                        {
                            yield return _ui.Dialog.Say(boss.Name, e.Line);
                            _ui.Dialog.Close();
                        }
                        else yield return Wait(1.1f);
                        yield return Wait(Mathf.Max(0, boss.Model.Anim.Length("Cast") - (Time.time - phaseStarted)));
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
                    Auto = false; _hud.SetAuto(false); _hud.Log(e.Text); _ui.Toast.Show(e.Text);
                    yield return Wait(.3f); break;
                case FleeEvent e:
                    _hud.Log(e.Success ? "도주 성공" : "도주 실패");
                    _fleeSucceeded = e.Success;
                    if (e.Success)
                        foreach (var fleeing in _units.Values) if (fleeing.Side == BattleSide.Party && fleeing.Alive)
                        { fleeing.Model.transform.rotation = transform.rotation * Quaternion.Euler(0, 180, 0); fleeing.Model.Play("Run"); }
                    yield return Wait(.5f); break;
                case BattleEndEvent e:
                    yield return Finish(e.Outcome); break;
                default:
                    throw new InvalidOperationException("Unsupported battle event: " + battleEvent.GetType().Name);
            }
        }

        BattleDisplayUnit Spawn(UnitSnapshot snapshot)
        {
            var unit = new BattleDisplayUnit(); unit.Apply(snapshot);
            unit.Model = snapshot.Side == BattleSide.Party ? ArtLibrary.SpawnHero(snapshot.DefId, transform) : ArtLibrary.SpawnEnemy(snapshot.DefId, transform);
            if (snapshot.Side == BattleSide.Enemy)
            {
                var def = _app.DB.Enemies[snapshot.DefId];
                unit.Model.transform.localScale = Vector3.one * def.ScaleMult;
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
                else
                {
                    lane = 0; while (lane < occupied.Length && occupied[lane]) lane++;
                }
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
                if (!string.IsNullOrEmpty(spec.WeaponId))
                {
                    string path = ArtLibrary.WeaponPath(spec.WeaponId);
                    var weapon = ArtLibrary.LoadPrefab(path);
                    if (weapon == null) throw new InvalidOperationException("Missing equipped weapon art: " + path);
                    string socket = snapshot.DefId == "archer" ? "weapon.L" : "weapon.R";
                    if (unit.Model.FindBone(socket) == null) throw new InvalidOperationException("Missing weapon socket: " + snapshot.DefId + "/" + socket);
                    unit.Model.Attach(socket, weapon);
                }
            }
            if (!unit.Alive) unit.Model.Play("Die");
            _units.Add(unit.Id, unit); _hud.AddUnit(unit); Sync(unit);
            return unit;
        }

        IEnumerator StartAction(ActionStartEvent e)
        {
            _action = e; _presentation = null; _hitCounts.Clear(); _hitTotals.Clear(); _impactTargets.Clear();
            _waveTargets.Clear(); _wave = 0; _waveStop = 0; _strikeClip = null; _perHitProjectile = false; _flashed = false;
            if (!string.IsNullOrEmpty(e.PresentationId))
            {
                if (!_app.DB.Presentations.TryGetValue(e.PresentationId, out _presentation))
                    throw new InvalidOperationException("Missing action presentation: " + e.PresentationId);
            }
            if (!Find(e.ActorId, out var actor)) yield break;
            _actionElapsed = 0; _actionLength = 0;
            BattleDisplayUnit target = null;
            if (e.TargetIds != null && e.TargetIds.Count > 0) Find(e.TargetIds[0], out target);
            _hud.Log(actor.Name + " · " + (e.DisplayName ?? ActionName(e.Kind)));
            ActiveShot(actor, target, e.IsUltimate);
            if (e.Kind == ActionKind.Skill && !string.IsNullOrEmpty(e.DisplayName))
                _hud.SkillBanner(e.DisplayName, PresentationColor(e.Element));
            bool grand = e.IsUltimate || (_presentation != null && _presentation.Tier >= 3);
            if (grand && !Reduced) _dimTarget = e.IsUltimate ? .62f : .4f;
            if (e.IsUltimate)
            {
                if (actor.Model.Anim.HasClip("Cast")) actor.Model.Anim.Play("Cast", .12f);
                _hud.CutIn(actor.Name, e.DisplayName ?? "궁극기");
                string hero = actor.DefId == "archer" ? "ranger" : actor.DefId;
                PlaySound("sfx_ultimate_" + hero);
                yield return Wait(Reduced ? .5f : .95f); _hud.HideCutIn();
            }
            if (grand && _dimTarget > .4f) _dimTarget = .4f;   // keep framing the wind-up after the cut-in
            if (e.Kind == ActionKind.Guard)
            {
                actor.Guarding = true; Sync(actor);
                if (actor.Side == BattleSide.Party)
                {
                    actor.Model.Anim.PlayOnce("Guard", "Idle", .08f);
                    _actionLength = actor.Model.Anim.Length("Guard");
                }
                Popup(actor.Id, "방어", new Color(.55f, .8f, 1)); PlaySound("sfx_guard");
                yield return Wait(.3f); yield break;
            }
            if (e.Kind == ActionKind.Flee) { actor.Model.Play("Run"); yield return Wait(.2f); yield break; }
            bool cast = e.Kind == ActionKind.Item || e.Kind == ActionKind.Summon ||
                (_presentation != null && _presentation.ActorAction == "cast");
            string clip = cast ? "Cast" : "Attack";
            bool rangedBasic = e.Kind == ActionKind.Attack &&
                (actor.DefId == "archer" || actor.DefId == "mage" || actor.DefId == "cleric");
            bool approach = !Reduced && !cast && !rangedBasic && target != null && actor.Id != target.Id &&
                ((_presentation != null && _presentation.Approach != "none") ||
                (_presentation == null && e.Kind == ActionKind.Attack));
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
                if (direction.sqrMagnitude > .01f) yield return Face(actor, Quaternion.LookRotation(direction));
                if (!lunge && travel > .01f)
                {
                    actor.Model.Anim.Play("Run", .05f, false);
                    float time = MovementTime(travel), lead = Mathf.Min(.1f, time);
                    StartCoroutine(Move(actor, destination, time));
                    yield return Wait(time - lead);
                    // The wind-up overlaps the last strides so the blade lands as the feet plant.
                    Swing(actor, clip, cast); swung = true;
                    yield return Wait(lead);
                }
            }
            if (!swung && target != null && actor.Id != target.Id)
            {
                Vector3 facing = target.Model.transform.position - actor.Model.transform.position; facing.y = 0;
                if (facing.sqrMagnitude > .01f) yield return Face(actor, Quaternion.LookRotation(facing));
            }
            if (!swung) Swing(actor, clip, cast);
            Color tint = PresentationColor(e.Element);
            if (_presentation != null && !string.IsNullOrEmpty(_presentation.ChargeVfx))
                _charge = Effect(_presentation.ChargeVfx, actor.Model.CenterPoint, tint, 1, _actionLength, actor.Model.transform, actor.Home.y);
            PlaySound(_presentation != null && !string.IsNullOrEmpty(_presentation.SfxCast) ? _presentation.SfxCast :
                e.Kind == ActionKind.Item ? "sfx_item" : cast ? ElementSound(e.Element) : WeaponSound(actor));
            float contactTime = _actionLength * (cast ? .6f : .4f);
            // The authored Attack contacts at 40%; the lunge belongs to that strike, not a tiny Run.
            if (lunge) yield return Move(actor, destination, contactTime);
            else yield return Wait(Mathf.Max(0, contactTime - _actionElapsed));
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
                Effect(_presentation.AreaVfx, center, tint, Mathf.Max(.1f, _presentation.AreaScale), 0, null, center.y - .9f);
                _dimTarget = Mathf.Min(_dimTarget, .12f);   // the effect itself plays over a near-full-bright arena
                if (!Reduced && _presentation.ScreenFlash) ScreenFlash(tint, .45f);
                if (!Reduced) AddTrauma(_presentation.Shake * .6f);
                float lead = Reduced ? Mathf.Min(.12f, _presentation.AreaWait) : _presentation.AreaWait;
                if (lead > 0) yield return Wait(lead);
            }
        }
        void Swing(BattleDisplayUnit actor, string clip, bool cast)
        {
            actor.Model.Anim.PlayOnce(clip, "Idle", cast ? .12f : .05f);
            _actionLength = actor.Model.Anim.Length(clip); _actionElapsed = 0; _strikeClip = clip;
        }
        /// <summary>Fires the presentation's projectile from the weapon socket at the target's hit point; returns its flight time.</summary>
        float Shoot(BattleDisplayUnit actor, BattleDisplayUnit target, Color tint)
        {
            string key = _presentation.TravelVfx;
            Vector3 from = actor.Model.MuzzlePoint(actor.DefId == "archer" ? "weapon.L" : "weapon.R"), to = HitPoint(target);
            float time = Reduced ? .08f : TravelTime(key, Vector3.Distance(from, to));
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
                        Impact(_presentation.ImpactVfx, affected, PresentationColor(_action.Element), affected.Side != source.Side);
            foreach (var pair in _hitCounts)
                if (pair.Value > 1 && Find(pair.Key, out var hit)) _ui.Numbers.SpawnHits(hit.Model.HeadPoint, pair.Value, _hitTotals[pair.Key]);
            if (!_fleeSucceeded && Find(e.ActorId, out var actor) && actor.Alive)
            {
                // Hit-stop freezes the take, so its held time must not steal the recovery pose.
                while (_actionElapsed < _actionLength) yield return null;
                if ((actor.Model.transform.position - actor.Home).sqrMagnitude > .01f)
                {
                    // Hop back onto the mark still facing the foe: no about-turn, no jog.
                    actor.Model.Play("Idle", .1f);
                    yield return Move(actor, actor.Home, Reduced ? 0 : .3f, .4f);
                }
                else actor.Model.Play("Idle", .12f);
                yield return Face(actor, actor.Facing);
            }
            _action = null; _presentation = null; _actionLength = 0; _strikeClip = null; _perHitProjectile = false;
            Establishing(false); yield return Wait(.12f);
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
            if (newWave && _wave > 1 && _strikeClip == "Attack" && !Reduced)
            {
                float length = actor.Model.Anim.Length("Attack");
                actor.Model.Anim.PlayFrom("Attack", .25f, .04f);
                _actionLength = length; _actionElapsed = length * .25f;
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
            if (target.Alive && e.Amount > 0) target.Model.Anim.PlayOnce("Hit", "Idle", .045f);
            Color tint = PresentationColor(e.Element);
            if (e.Amount > 0) target.Model.Flash(e.Critical ? Color.white : tint, e.Critical ? .2f : Reduced ? .2f : .12f);
            // Recoil away from the attacker side; only from the home mark so it never fights a Move.
            if (!Reduced && e.Amount > 0 && target.Alive && (target.KnockTime > 0 || (target.Model.transform.position - target.Home).sqrMagnitude < .01f))
            {
                float push = Mathf.Clamp((_presentation != null ? _presentation.Shake : .25f) * .32f, .05f, .26f) * (e.Critical ? 1.5f : 1);
                bool knocked = target.KnockTime > 0;
                float k = knocked ? KnockCurve(KnockLength - target.KnockTime) : 0;
                target.KnockAmount = Mathf.Max(knocked ? target.KnockAmount : 0, push * (target.Boss ? .35f : 1));
                // Re-hits continue outward from the current recoil instead of snapping home first.
                target.KnockTime = KnockLength - KnockOut * (1 - Mathf.Sqrt(1 - Mathf.Clamp01(k)));
            }
            string impact = _presentation != null ? _presentation.ImpactVfx : "impact";
            if (!string.IsNullOrEmpty(impact))
                Effect(impact, HitPoint(target), tint, ImpactScale(target) * (e.Critical ? 1.3f : 1), 0, null, target.Home.y);
            PlaySound(e.Critical ? "sfx_critical" : _presentation != null && !string.IsNullOrEmpty(_presentation.SfxImpact) ? _presentation.SfxImpact : "sfx_hit");
            if (!Reduced)
            {
                AddTrauma((_presentation != null ? _presentation.Shake : .08f) * (e.Critical ? 1.4f : 1));
                if (strike) _fovPunch = Mathf.Min(_fovPunch, e.Critical ? -3f : -1.5f);
                if (e.Critical) ScreenFlash(Color.white, .22f);
                else if (strike && !_flashed && _presentation != null && _presentation.ScreenFlash) ScreenFlash(tint, .3f);
            }
            if (strike) _flashed = true;
            float stop = _presentation != null ? _presentation.HitStop : .035f;
            if (e.Critical) stop *= 1.6f;
            else if (weak) stop *= 1.3f;
            _waveStop = Mathf.Max(_waveStop, stop);
            // Group hits land together: stagger the rest of the wave, then freeze once for all of it.
            if (strike && NextHitJoinsWave()) { yield return Wait(.03f); yield break; }
            // Let the recoil enter before freezing it; otherwise hit-stop freezes the untouched pose.
            if (!Reduced && e.Amount > 0) yield return Wait(KnockOut);
            yield return HitStop(strike ? _waveStop : stop);
            yield return Wait(HitInterval());
        }

        /// <summary>
        /// Battle entrance: both sides run onto their marks while the camera sweeps from a low enemy-side angle into
        /// the establishing shot, under an ENCOUNTER / BOSS call-out.
        /// </summary>
        IEnumerator Intro()
        {
            var movers = new List<(BattleDisplayUnit Unit, Vector3 From)>();
            foreach (var unit in _units.Values)
            {
                if (!unit.Alive) continue;
                Vector3 from = unit.Home + unit.Facing * Vector3.back * (unit.Side == BattleSide.Party ? 3.4f : 4.6f);
                unit.Model.transform.position = from;
                unit.Model.Play("Run");
                movers.Add((unit, from));
            }
            _cameraPosition = transform.TransformPoint(new Vector3(-7.8f, 1.5f, 5.2f));
            _cameraLook = transform.TransformPoint(new Vector3(0f, 1.3f, 2.2f));
            _fov = 52f; SetCamera();
            _cameraRate = 2.4f; Establishing(false);
            _flashAlpha = .6f; _flash.color = new Color(1, 1, 1, _flashAlpha);
            var names = new List<string>();
            foreach (var unit in _units.Values) if (unit.Side == BattleSide.Enemy && !names.Contains(unit.Name)) names.Add(unit.Name);
            bool boss = _setup.Kind == BattleKind.Boss, foe = _setup.Kind == BattleKind.Foe;
            _hud.Announce(boss ? "BOSS BATTLE" : foe ? "F.O.E" : "ENCOUNTER", string.Join(" · ", names) + (boss || foe ? " 출현!" : " 이(가) 나타났다!"),
                boss || foe ? UITheme.Danger : UITheme.Dawn, .8f);
            AudioManager.Instance.PlaySfx("sfx_encounter"); AudioManager.Instance.PlaySfx("sfx_wind", .55f, 1.2f);
            float elapsed = 0f, length = .8f;
            while (elapsed < length)
            {
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float k = 1f - Mathf.Pow(1f - Mathf.Clamp01(elapsed / length), 3f);
                    foreach (var (unit, from) in movers) unit.Model.transform.position = Vector3.Lerp(from, unit.Home, k);
                }
                yield return null;
            }
            foreach (var (unit, _) in movers)
            {
                unit.Model.transform.position = unit.Home;
                unit.Model.Play(unit.Side == BattleSide.Enemy && (boss || foe) ? "Cast" : "Idle");
            }
            yield return Wait(boss || foe ? .9f : .55f);
            foreach (var (unit, _) in movers) unit.Model.Play("Idle");
            _cameraRate = 7f;
        }

        IEnumerator Finish(BattleOutcome outcome)
        {
            _hud.Lock(); Auto = false; _hud.SetAuto(false); Establishing(false);
            if (!Reduced) StageOutcome(outcome.Result);
            foreach (var unit in _units.Values)
                if (unit.Side == BattleSide.Party && unit.Alive)
                    unit.Model.Play(outcome.Result == BattleResult.Victory ? "Victory" : outcome.Result == BattleResult.Fled ? "Run" : "Idle");
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
                                unit.Model.transform.position += transform.TransformDirection(Vector3.back) * (Dt * 4);
                    }
                    yield return null;
                }
            }
            else yield return Wait(Reduced ? .6f : 2.1f);
            _cameraRate = 7f;
            // Commit every outcome before showing acknowledgement UI: closing the player must not replay this battle.
            var resolution = _app.Dungeon.ResolveBattle(outcome);
            _app.Save();
            bool acknowledged = false;
            _hud.Rewards(outcome, resolution.Report, () => acknowledged = true);
            while (!acknowledged) yield return null;
            yield return Wait(.12f);
            _finished = true; Playing = false;
            Restore();
            var callback = _completed; _completed = null;
            callback?.Invoke(outcome);
        }
        /// <summary>Victory: the camera swings round in front of the party for their poses. Defeat: it lifts away and the arena dims.</summary>
        void StageOutcome(BattleResult result)
        {
            Vector3 party = Vector3.zero; int count = 0;
            foreach (var unit in _units.Values)
                if (unit.Side == BattleSide.Party) { party += transform.InverseTransformPoint(unit.Home); count++; }
            party = count > 0 ? party / count : new Vector3(0f, 0f, -3f);
            _cameraRate = 2.2f;
            switch (result)
            {
                case BattleResult.Victory:
                    _cameraPosition = transform.TransformPoint(party + new Vector3(.6f, 1.55f, 5.2f));
                    _cameraLook = transform.TransformPoint(party + new Vector3(0f, .85f, 0f));
                    _fov = 40f;
                    _hud.Announce("VICTORY", "전투에서 승리했다!", UITheme.GoldBright, 1.2f);
                    break;
                case BattleResult.Defeat:
                    _cameraPosition = transform.TransformPoint(new Vector3(0f, 8.5f, -12.5f));
                    _cameraLook = transform.TransformPoint(party);
                    _dimTarget = .45f;
                    _hud.Announce("전멸…", "파티가 쓰러졌다", UITheme.Danger, 1.2f);
                    break;
                case BattleResult.Fled:
                    _hud.Announce("도주 성공", "무사히 빠져나왔다", UITheme.TextDim, .5f);
                    break;
            }
        }

        void Sync(BattleDisplayUnit unit) { _hud.Sync(unit); UpdateAuras(unit); }
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
        VfxHandle Effect(string key, Vector3 position, Color tint, float scale = 1, float duration = 0, Transform follow = null, float ground = float.NaN)
        {
            var handle = _vfx.Play(key, position, tint, scale, duration, follow, ground); TrackEffect(handle); return handle;
        }
        /// <summary>Hostile impacts sit on the camera side of the body so sparks are not buried in large models.</summary>
        void Impact(string key, BattleDisplayUnit unit, Color tint, bool hostile) =>
            Effect(key, hostile ? HitPoint(unit) : unit.Model.CenterPoint, tint, ImpactScale(unit), 0, null, unit.Home.y);
        Vector3 HitPoint(BattleDisplayUnit unit)
        {
            Vector3 center = unit.Model.CenterPoint;
            return center + (_camera.transform.position - center).normalized * (unit.Model.Radius * .8f + .1f);
        }
        static float ImpactScale(BattleDisplayUnit unit) => Mathf.Clamp(unit.Model.Height / 1.3f, 1f, 2f) * 1.2f;
        void AddTrauma(float shake) => _trauma = Mathf.Clamp01(_trauma + shake * 1.5f);
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
        void PreviewTarget(string id)
        {
            foreach (var unit in _units.Values) unit.Model.SetTint(unit.Id == id ? new Color(1.12f, 1.05f, .8f) : Color.white);
            if (id != null && Find(id, out var target)) ActiveShot(target, null, false);
            else Establishing(false);
        }
        void Establishing(bool instant)
        {
            _cameraPosition = transform.TransformPoint(CameraHome);
            _cameraLook = transform.TransformPoint(CameraAim); _fov = CameraFov;
            if (instant) SetCamera();
        }
        void ActiveShot(BattleDisplayUnit actor, BattleDisplayUnit target, bool ultimate)
        {
            if (Reduced) return;
            Vector3 center = target != null ? (actor.Model.CenterPoint + target.Model.CenterPoint) * .5f : actor.Model.CenterPoint;
            Vector3 local = transform.InverseTransformPoint(center);
            // Keep the four-hero establishing composition; action emphasis is a small dolly, not a cut.
            Vector3 emphasis = new Vector3(Mathf.Clamp(local.x - CameraAim.x, -3f, 3f) * .16f, 0,
                Mathf.Clamp(local.z, -3f, 3f) * .1f);
            _cameraPosition = transform.TransformPoint(CameraHome + emphasis);
            _cameraLook = transform.TransformPoint(CameraAim + emphasis);
            _fov = ultimate ? CameraFov - 5f : CameraFov - 2f;
        }
        void SetCamera()
        {
            _cameraBasePosition = _cameraPosition;
            _cameraBaseRotation = Quaternion.LookRotation(_cameraLook - _cameraPosition);
            _camera.transform.SetPositionAndRotation(_cameraBasePosition, _cameraBaseRotation);
            _camera.fieldOfView = _fovBase = _fov; _fovPunch = 0;
        }
        void LateUpdate()
        {
            if (!_initialized || _restored || _camera == null) return;
            _hud.Paused = _app.Paused;
            foreach (var unit in _units.Values) unit.Model.Anim.SetSpeed(_app.Paused || _hitstop ? 0 : Speed);
            if (_vfx != null) _vfx.TimeScale = _app.Paused ? 0 : Speed;
            if (_app.Paused) return;
            if (!_hitstop && _actionLength > 0) _actionElapsed += Dt;
            if (Reduced)
            {
                if (!_wasReduced) Establishing(true);
                _trauma = 0; _fovPunch = 0; _dimTarget = 0;
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
            _wasReduced = Reduced;
            float blend = 1 - Mathf.Exp(-Time.unscaledDeltaTime * _cameraRate);
            _cameraBasePosition = Vector3.Lerp(_cameraBasePosition, _cameraPosition, blend);
            Quaternion rotation = Quaternion.LookRotation(_cameraLook - _cameraBasePosition);
            _cameraBaseRotation = Quaternion.Slerp(_cameraBaseRotation, rotation, blend);
            Vector3 position = _cameraBasePosition;
            Quaternion view = _cameraBaseRotation;
            if (!Reduced && _trauma > .001f)
            {
                // Camera-relative Perlin trauma; squared so light knocks stay subtle and big ones read.
                float shake = _trauma * _trauma, time = Time.unscaledTime * 24f;
                float x = Mathf.PerlinNoise(time, .5f) * 2 - 1, y = Mathf.PerlinNoise(.5f, time + 37f) * 2 - 1;
                float roll = Mathf.PerlinNoise(time + 71f, 13.5f) * 2 - 1;
                position += view * new Vector3(x, y, 0) * (shake * .22f);
                view *= Quaternion.Euler(0, 0, roll * .6f * shake);
                _trauma = Mathf.MoveTowards(_trauma, 0, Time.unscaledDeltaTime * 1.6f);
            }
            _camera.transform.SetPositionAndRotation(position, view);
            _fovBase = Mathf.Lerp(_fovBase, _fov, blend);
            _fovPunch = Mathf.Lerp(_fovPunch, 0, 1 - Mathf.Exp(-Time.unscaledDeltaTime * 9f));
            _camera.fieldOfView = _fovBase + _fovPunch;
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
            foreach (var unit in _units.Values) unit.Model.Anim.SetSpeed(_app.Paused ? 0 : Speed);
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
        IEnumerator Move(BattleDisplayUnit unit, Vector3 destination, float seconds, float arc = 0)
        {
            if (unit.KnockTime > 0) { unit.KnockTime = 0; unit.Model.transform.position = unit.Home; }
            Vector3 from = unit.Model.transform.position; float elapsed = 0;
            while (elapsed < seconds)
            {
                if (!_app.Paused)
                {
                    elapsed += Dt;
                    float t = Mathf.Clamp01(elapsed / seconds), k = 1 - (1 - t) * (1 - t);
                    unit.Model.transform.position = Vector3.Lerp(from, destination, k) + Vector3.up * (Mathf.Sin(Mathf.PI * t) * arc);
                }
                yield return null;
            }
            unit.Model.transform.position = destination;
        }
        static float MovementTime(float distance) => Mathf.Clamp(distance / 10f, .22f, .36f);
        float HitInterval() => Mathf.Max(.12f, _presentation != null ? _presentation.HitInterval : .18f);
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
            switch (actor.DefId)
            { case "warrior": return "sfx_sword"; case "archer": return "sfx_bow"; case "mage": case "cleric": return "sfx_staff"; default: return "sfx_hit"; }
        }
        static void PlaySound(string id) { if (!string.IsNullOrEmpty(id)) AudioManager.Instance.PlaySfx(id); }
        void Restore()
        {
            if (_restored) return; _restored = true;
            foreach (var effect in _effects) effect.Stop(); _effects.Clear(); _auras.Clear();
            if (_vfx != null) _vfx.TimeScale = 1;
            if (_ui != null) { _ui.Numbers.Clear(); _ui.Dialog.Close(); }
            if (_flash != null) { _flash.gameObject.SetActive(false); Destroy(_flash.gameObject); }
            if (_dim != null) { _dim.gameObject.SetActive(false); Destroy(_dim.gameObject); }
            if (_hud != null) { _hud.Lock(); _hud.enabled = false; }
            if (_camera != null) { _camera.transform.SetPositionAndRotation(_oldPosition, _oldRotation); _camera.fieldOfView = _oldFov; }
            if (_app != null && _oldAtmosphere != null) { _app.Atmosphere.Apply(_oldAtmosphere); _app.Atmosphere.SetupCamera(_camera); }
        }
        void OnDestroy()
        {
            StopAllCoroutines(); Playing = false; _completed = null;
            if (_initialized) Restore();
            _units.Clear();
        }
    }
}
