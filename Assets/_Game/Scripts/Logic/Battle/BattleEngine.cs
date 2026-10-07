// Turn-based combat engine (port of battle_state_machine.gd). Deterministic, seedable and
// presentation-agnostic: it never blocks; Start/Advance/Submit run the battle until a hero needs a
// command or the battle ends and return the events produced, in exact chronological order.
using System;
using System.Collections.Generic;

namespace Abyss.Logic.Battle
{
    /// <summary>Externally visible engine state.</summary>
    public enum BattleEngineState { NotStarted = 0, AwaitingCommand = 1, Ended = 2 }

    /// <summary>
    /// Runs one battle. Usage: <c>var e = new BattleEngine(db, setup); var evs = e.Start();</c> then, while
    /// <see cref="State"/> is AwaitingCommand, <c>evs = e.Submit(cmd)</c> for <see cref="ActiveHero"/>.
    /// </summary>
    public sealed partial class BattleEngine
    {
        public const int MaxLivingEnemies = 5;
        public const int TpOnDeal = 8;
        public const int TpOnTake = 12;
        public const int TpOnAllyFall = 20;
        public const int TpOnBreak = 10;
        public const double EnrageBelow = 0.3;

        readonly GameDB _db;
        readonly BattleSetup _setup;
        readonly GodotRng _rng;
        readonly double _enemyPower;
        readonly List<BattleUnit> _party = new List<BattleUnit>();
        readonly List<BattleUnit> _enemies = new List<BattleUnit>();
        readonly List<BattleUnit> _units = new List<BattleUnit>();
        readonly Dictionary<string, BattleUnit> _byId = new Dictionary<string, BattleUnit>();
        readonly Dictionary<string, int> _inventory = new Dictionary<string, int>();
        readonly Dictionary<string, int> _itemsUsed = new Dictionary<string, int>();
        readonly HashSet<string> _known;
        readonly HashSet<string> _discovered = new HashSet<string>();
        readonly Dictionary<string, int> _drops = new Dictionary<string, int>();
        readonly List<BattleUnit> _queue = new List<BattleUnit>();

        int _turnIndex;
        readonly HashSet<string> _resistSeen = new HashSet<string>(); // "enemyId:element" resisted this battle (AUTO)
        BattleUnit _current;
        bool _active;
        bool _awaiting;
        BattleOutcome _outcome;
        BattleEngineState _state = BattleEngineState.NotStarted;
        int _seq;
        List<BattleEvent> _out = new List<BattleEvent>();

        // Per-action bookkeeping (TP gains and once-per-target effectiveness popups).
        bool _actionDealtDamage;
        int _actionHpDealt; // HP damage dealt to opponents by the current action (skill drain)
        readonly List<BattleUnit> _actionDamaged = new List<BattleUnit>();
        readonly HashSet<string> _actionEffectShown = new HashSet<string>();
        readonly Dictionary<string, int> _actionHitIndex = new Dictionary<string, int>();

        /// <summary>Builds every unit (difficulty / FOE power applied once). Does not roll anything yet.</summary>
        public BattleEngine(GameDB db, BattleSetup setup)
        {
            _db = db ?? throw new ArgumentNullException(nameof(db));
            _setup = setup ?? throw new ArgumentNullException(nameof(setup));
            _rng = new GodotRng(unchecked((ulong)(long)setup.Seed));
            _enemyPower = EnemyStats.EncounterPower(setup);
            _known = setup.KnownWeaknesses != null ? new HashSet<string>(setup.KnownWeaknesses) : new HashSet<string>();
            if (setup.Inventory != null)
                foreach (var kv in setup.Inventory) _inventory[kv.Key] = kv.Value;
            for (int i = 0; i < setup.Party.Count; i++)
            {
                var unit = BattleUnit.FromHero(db, setup.Party[i], i);
                _party.Add(unit);
                Register(unit, setup.Party[i].Statuses);
            }
            for (int i = 0; i < setup.EnemyGroup.Count; i++)
            {
                if (!db.Enemies.TryGetValue(setup.EnemyGroup[i], out var def))
                    throw new ArgumentException("Unknown enemy id: " + setup.EnemyGroup[i]);
                var unit = BattleUnit.FromEnemy(db, def, EnemyStats.Build(def, setup.Difficulty, _enemyPower), i);
                _enemies.Add(unit);
                Register(unit, null);
            }
        }

        // --- Public state --------------------------------------------------------------------------

        public BattleEngineState State => _state;
        public BattleSetup Setup => _setup;
        /// <summary>Hero waiting for a command (null unless AwaitingCommand).</summary>
        public BattleUnit ActiveHero => _state == BattleEngineState.AwaitingCommand ? _current : null;
        /// <summary>Unit whose turn it is (or was last).</summary>
        public BattleUnit CurrentActor => _current;
        /// <summary>Party then enemies (summons appended in arrival order).</summary>
        public IReadOnlyList<BattleUnit> Units => _units;
        public IReadOnlyList<BattleUnit> Party => _party;
        public IReadOnlyList<BattleUnit> Enemies => _enemies;
        public int Round { get; private set; }
        /// <summary>Action order of the current round (units that were alive at round start).</summary>
        public IReadOnlyList<BattleUnit> TurnOrder => _queue;
        /// <summary>Index into <see cref="TurnOrder"/> of the current actor.</summary>
        public int TurnIndex => _turnIndex;
        /// <summary>Filled when the battle has ended.</summary>
        public BattleOutcome Outcome => _outcome;
        /// <summary>Consumables left (item id -> count).</summary>
        public IReadOnlyDictionary<string, int> Inventory => _inventory;
        /// <summary>The seeded battle RNG (tests / simulators).</summary>
        public GodotRng Rng => _rng;

        public BattleUnit UnitById(string id) => id != null && _byId.TryGetValue(id, out var u) ? u : null;
        public int InventoryCount(string itemId) => itemId != null && _inventory.TryGetValue(itemId, out var n) ? n : 0;

        /// <summary>Living units that still act this round, current actor first.</summary>
        public IReadOnlyList<BattleUnit> RemainingTurnOrder
        {
            get
            {
                var r = new List<BattleUnit>();
                for (int i = _turnIndex; i < _queue.Count; i++) if (_queue[i].IsAlive) r.Add(_queue[i]);
                return r;
            }
        }

        /// <summary>Weakness elements of this enemy the player knows (from earlier battles or hit this battle).</summary>
        public IReadOnlyList<int> KnownWeaknessesOf(BattleUnit unit)
        {
            if (unit == null || unit.Side != BattleSide.Enemy) return Array.Empty<int>();
            var result = new List<int>();
            for (int e = 1; e <= (int)Element.Holy; e++)
            {
                string key = WeaknessKey(unit.DefId, e);
                if (_known.Contains(key) || _discovered.Contains(key)) result.Add(e);
            }
            return result;
        }

        public bool IsWeaknessKnown(BattleUnit unit, int element)
        {
            string key = WeaknessKey(unit.DefId, element);
            return _known.Contains(key) || _discovered.Contains(key);
        }

        static string WeaknessKey(string enemyId, int element) => enemyId + ":" + element;

        /// <summary>True when the flee command (or a smoke bomb, <paramref name="smoke"/>) may be used.</summary>
        public bool FleeAllowed(bool smoke = false)
        {
            var kind = _setup.Kind;
            if (kind == BattleKind.Boss || kind == BattleKind.Event || (kind == BattleKind.Foe && !smoke)) return false;
            foreach (var e in _enemies)
            {
                if (e.Summoned) continue;
                if (e.IsBoss) return false;
            }
            return true;
        }

        // --- Flow ------------------------------------------------------------------------------------

        /// <summary>Starts the battle (phase checks, first round) and runs until the first hero command or the end.</summary>
        public IReadOnlyList<BattleEvent> Start()
        {
            if (_state != BattleEngineState.NotStarted) throw new InvalidOperationException("Battle already started.");
            if (_party.Count == 0 || _enemies.Count == 0) throw new InvalidOperationException("Battle requires at least one hero and one enemy.");
            BeginBatch();
            _active = true;
            var snaps = new List<UnitSnapshot>();
            foreach (var u in _units) snaps.Add(u.Snapshot(KnownWeaknessesOf(u)));
            Emit(new BattleStartEvent { Units = snaps });
            CheckPhases();
            StartRound();
            Run();
            return EndBatch();
        }

        /// <summary>Continues until a hero needs a command or the battle ends (no-op when already waiting / ended).</summary>
        public IReadOnlyList<BattleEvent> Advance()
        {
            if (_state == BattleEngineState.NotStarted) return Start();
            BeginBatch();
            Run();
            return EndBatch();
        }

        /// <summary>
        /// Resolves the active hero's command and continues to the next hero command or the end. A refused
        /// command returns a single <see cref="CommandRejectedEvent"/> and changes nothing.
        /// </summary>
        public IReadOnlyList<BattleEvent> Submit(BattleCommand cmd)
        {
            BeginBatch();
            if (_state != BattleEngineState.AwaitingCommand || cmd == null)
            {
                Reject("input_locked");
                return EndBatch();
            }
            var actor = _current;
            if (actor == null || actor.Side != BattleSide.Party || !actor.IsAlive)
            {
                Reject("no_actor");
                return EndBatch();
            }
            var action = ToAction(actor, cmd);
            string rejection = Prepare(action, actor);
            if (rejection != null)
            {
                Reject(rejection);
                return EndBatch();
            }
            _awaiting = false;
            Execute(action);
            if (!CheckOutcome()) FinishTurn(actor, false);
            Run();
            return EndBatch();
        }

        void BeginBatch() => _out = new List<BattleEvent>();

        IReadOnlyList<BattleEvent> EndBatch()
        {
            _state = !_active && _outcome != null ? BattleEngineState.Ended
                : (_awaiting ? BattleEngineState.AwaitingCommand : _state);
            return _out;
        }

        void Emit(BattleEvent e)
        {
            e.Seq = _seq++;
            _out.Add(e);
        }

        void Msg(string key, params string[] args)
            => Emit(new MessageEvent { Key = key, Args = args, Text = _db.T(key, args) });

        void Reject(string key) => Emit(new CommandRejectedEvent { Key = key, Text = _db.T(key) });

        void Run()
        {
            while (_active && !_awaiting) BeginNextActor();
        }

        void StartRound()
        {
            if (!_active) return;
            Round++;
            _queue.Clear();
            foreach (var u in _units) if (u.IsAlive) _queue.Add(u);
            _queue.Sort(CompareTurns);
            _turnIndex = 0;
            var ids = new List<string>(_queue.Count);
            foreach (var u in _queue) ids.Add(u.Id);
            Emit(new RoundStartEvent { Round = Round, TurnOrder = ids });
        }

        static int CompareTurns(BattleUnit a, BattleUnit b)
        {
            if (ReferenceEquals(a, b)) return 0;
            int sa = a.EffectiveSpeed, sb = b.EffectiveSpeed;
            if (sa != sb) return sb.CompareTo(sa);
            if (a.Side != b.Side) return a.Side == BattleSide.Party ? -1 : 1;
            return a.Slot.CompareTo(b.Slot);
        }

        void BeginNextActor()
        {
            if (CheckOutcome()) return;
            while (_turnIndex < _queue.Count)
            {
                var actor = _queue[_turnIndex];
                if (actor.IsAlive)
                {
                    _current = actor;
                    actor.Guarding = false;
                    Emit(new TurnStartEvent { UnitId = actor.Id, Round = Round });
                    if (actor.Broken)
                    {
                        // BREAK: the whole next turn (all actions) is lost, then it recovers.
                        Emit(new TurnSkippedEvent { UnitId = actor.Id, Broken = true });
                        Msg("broken_skip", actor.DisplayName);
                        FinishTurn(actor, true);
                        return;
                    }
                    if (!actor.CanAct)
                    {
                        Emit(new TurnSkippedEvent { UnitId = actor.Id, Broken = false });
                        Msg("cannot_move", actor.DisplayName);
                        FinishTurn(actor, false);
                        return;
                    }
                    if (actor.Side == BattleSide.Party)
                    {
                        _awaiting = true;
                        Emit(new CommandRequestedEvent { UnitId = actor.Id });
                    }
                    else EnemyTurn(actor);
                    return;
                }
                _turnIndex++;
            }
            StartRound();
        }

        void EnemyTurn(BattleUnit actor)
        {
            CheckPhases();
            int count = Math.Max(1, actor.ActionsPerTurn);
            for (int i = 0; i < count; i++)
            {
                if (!_active || !actor.IsAlive || !actor.CanAct || !EnemyAI.AnyLiving(_party)) break;
                var action = EnemyAI.Choose(actor, _party, _enemies, _rng, _setup.Difficulty, SummonSlots(actor));
                if (Prepare(action, actor) != null)
                {
                    action = BattleAction.Make(ActionKind.Attack, actor.Id);
                    if (Prepare(action, actor) != null)
                    {
                        action = BattleAction.Make(ActionKind.Guard, actor.Id);
                        Prepare(action, actor); // executed regardless, as in the original
                    }
                }
                Execute(action);
                if (CheckOutcome()) return;
            }
            FinishTurn(actor, false);
        }

        int SummonSlots(BattleUnit actor)
        {
            int summonedAlive = 0, living = 0;
            foreach (var e in _enemies)
            {
                if (!e.IsAlive) continue;
                living++;
                if (e.SummonerId == actor.Id) summonedAlive++;
            }
            int limit = actor.Summons.Count > 0 ? actor.SummonLimit : 0;
            return Math.Max(0, Math.Min(limit - summonedAlive, MaxLivingEnemies - living));
        }

        void FinishTurn(BattleUnit actor, bool recoverBreak)
        {
            ApplyTurnEndEffects(actor);
            if (actor.IsAlive)
                foreach (var id in actor.RemoveExpiredStatuses())
                    Emit(new StatusRemovedEvent { UnitId = actor.Id, StatusId = id, Reason = StatusRemoveReason.Expired });
            if (recoverBreak && actor.Broken)
            {
                actor.Broken = false;
                actor.Shield = actor.MaxShield;
                Emit(new RecoverEvent { UnitId = actor.Id, Shield = actor.Shield, MaxShield = actor.MaxShield });
                Emit(new ShieldChangeEvent { UnitId = actor.Id, Shield = actor.Shield, MaxShield = actor.MaxShield });
                if (actor.IsAlive) Msg("break_recovered", actor.DisplayName);
            }
            Emit(new TurnEndEvent { Unit = actor.Snapshot(KnownWeaknessesOf(actor)) });
            if (CheckOutcome()) return;
            _turnIndex++;
        }

        void ApplyTurnEndEffects(BattleUnit actor)
        {
            if (!actor.IsAlive) return;
            var ticks = new List<(int damage, int heal, BattleStatus status)>();
            bool dotResist = actor.HasGimmick("dot_resist");
            foreach (var s in actor.Statuses)
            {
                int damage = s.DamagePerTurn;
                if (s.MaxHpDamageRatio > 0.0)
                    damage = Math.Max(damage, Math.Max(1, Gd.RoundI(actor.MaxHp * s.MaxHpDamageRatio)));
                if (dotResist && (s.EffectType == StatusEffectType.Poison || s.EffectType == StatusEffectType.Burn))
                    damage = Math.Max(1, Gd.RoundI(damage * 0.25));
                int heal = s.HealPerTurn;
                if (s.HealRatioPerTurn > 0.0)
                    heal = Math.Max(heal, Math.Max(1, Gd.RoundI(actor.MaxHp * s.HealRatioPerTurn)));
                ticks.Add((damage, heal, s));
            }
            foreach (var tick in ticks)
            {
                if (!actor.IsAlive) return;
                if (tick.damage > 0)
                {
                    StatusDamage(actor, tick.damage, tick.status);
                    if (!actor.IsAlive) return;
                }
                if (tick.heal > 0)
                {
                    int healed = actor.Heal(Gd.RoundI(tick.heal * actor.HealingReceivedScale));
                    if (healed > 0)
                        Emit(new HealEvent { TargetId = actor.Id, SourceId = tick.status.SourceId, Amount = healed, StatusId = tick.status.Id, HpAfter = actor.Hp, MaxHp = actor.MaxHp });
                }
            }
        }

        /// <summary>DoT / bleed damage (no TP, no break, no phase check).</summary>
        void StatusDamage(BattleUnit unit, int amount, BattleStatus status)
        {
            int mpBefore = unit.Mp;
            var r = unit.ReceiveDamage(amount, DamageType.Status);
            Emit(new DamageEvent
            {
                TargetId = unit.Id, SourceId = status.SourceId, Amount = r.Hp, Absorbed = r.Absorbed, Type = DamageType.Status,
                Effectiveness = Effectiveness.Normal, StatusId = status.Id, HpAfter = unit.Hp, MaxHp = unit.MaxHp, Killed = !unit.IsAlive,
            });
            if (r.Mp > 0) Emit(new MpChangeEvent { UnitId = unit.Id, Mp = unit.Mp, MaxMp = unit.MaxMp, Delta = unit.Mp - mpBefore });
            foreach (var id in r.Removed) Emit(new StatusRemovedEvent { UnitId = unit.Id, StatusId = id, Reason = StatusRemoveReason.Damage });
            if (!unit.IsAlive) OnUnitDown(unit);
        }

        // --- Validation --------------------------------------------------------------------------------

        BattleAction ToAction(BattleUnit actor, BattleCommand cmd)
        {
            var targets = cmd.TargetId != null ? new[] { cmd.TargetId } : null;
            switch (cmd.Kind)
            {
                case CommandKind.Skill: return BattleAction.Make(ActionKind.Skill, actor.Id, targets, cmd.SkillId ?? "");
                case CommandKind.Item: return BattleAction.Make(ActionKind.Item, actor.Id, targets, cmd.ItemId ?? "");
                case CommandKind.Guard: return BattleAction.Make(ActionKind.Guard, actor.Id, targets);
                case CommandKind.Flee: return BattleAction.Make(ActionKind.Flee, actor.Id, targets);
                case CommandKind.Attack: return BattleAction.Make(ActionKind.Attack, actor.Id, targets);
                default: return BattleAction.Make((ActionKind)(-1), actor.Id, targets);
            }
        }

        /// <summary>
        /// Validates the action and resolves its targets WITHOUT consuming anything (RANDOM picks roll here,
        /// as in the original). Returns the rejection text key, or null when the action is valid.
        /// </summary>
        string Prepare(BattleAction action, BattleUnit actor)
        {
            if (actor == null || !actor.IsAlive || action.ActorId != actor.Id || !actor.CanAct || actor.Broken)
                return "invalid_action";
            switch (action.Kind)
            {
                case ActionKind.Attack:
                    action.Skill = null;
                    break;
                case ActionKind.Skill:
                    action.Skill = FindActorSkill(actor, action.PayloadId);
                    if (action.Skill == null) return "skill_unavailable";
                    int mp = Math.Max(0, action.Skill.MpCost), tp = Math.Max(0, action.Skill.TpCost);
                    if (mp > 0 && actor.IsSilenced) return "silenced";
                    if (actor.Mp < mp) return "mp_short";
                    if (actor.Tp < tp) return "tp_short";
                    break;
                case ActionKind.Item:
                    action.Item = _db.Items.TryGetValue(action.PayloadId, out var item) ? item : null;
                    if (action.Item == null || InventoryCount(action.PayloadId) <= 0) return "item_unavailable";
                    var itemEffect = EffectOf(action);
                    if (itemEffect == ActionEffect.Unusable) return "item_unavailable";
                    if (itemEffect == ActionEffect.Flee && !FleeAllowed(true)) return "flee_forbidden";
                    break;
                case ActionKind.Flee:
                    if (!FleeAllowed()) return "flee_forbidden";
                    action.TargetIds.Clear();
                    return null;
                case ActionKind.Guard:
                    action.TargetIds.Clear();
                    action.TargetIds.Add(actor.Id);
                    return null;
                case ActionKind.Summon:
                    if (actor.Side != BattleSide.Enemy || !actor.Summons.Contains(action.PayloadId) || SummonSlots(actor) <= 0)
                        return "invalid_action";
                    if (!_db.Enemies.ContainsKey(action.PayloadId)) return "invalid_action";
                    action.TargetIds.Clear();
                    return null;
                default:
                    return "invalid_action";
            }
            return ResolveTargets(action, actor);
        }

        SkillDef FindActorSkill(BattleUnit actor, string id)
        {
            foreach (var s in actor.SkillList) if (s.Id == id) return s;
            return null;
        }

        string ResolveTargets(BattleAction action, BattleUnit actor)
        {
            var effect = EffectOf(action);
            if (effect == ActionEffect.Flee)
            {
                action.TargetIds.Clear();
                return null;
            }
            var rule = RuleOf(action);
            var allies = actor.Side == BattleSide.Party ? _party : _enemies;
            var opponents = actor.Side == BattleSide.Party ? _enemies : _party;
            bool reviving = effect == ActionEffect.Revive;
            var allyPool = reviving ? EnemyAI.Fallen(allies) : EnemyAI.Living(allies);
            var opponentPool = EnemyAI.Living(opponents);
            var ids = new List<string>();
            action.Scope = 0;
            switch (rule)
            {
                case TargetRule.Self:
                    if (reviving || (action.TargetIds.Count > 0 && action.TargetIds[0] != actor.Id)) return "invalid_target";
                    ids.Add(actor.Id);
                    break;
                case TargetRule.None:
                    break;
                case TargetRule.AllAllies:
                    action.Scope = 1;
                    foreach (var u in allyPool) ids.Add(u.Id);
                    break;
                case TargetRule.AllEnemies:
                    action.Scope = 1;
                    foreach (var u in opponentPool) ids.Add(u.Id);
                    break;
                case TargetRule.All:
                    action.Scope = 1;
                    foreach (var u in EnemyAI.Living(allies)) ids.Add(u.Id);
                    foreach (var u in opponentPool) ids.Add(u.Id);
                    break;
                case TargetRule.RandomEnemies:
                case TargetRule.RandomAllies:
                {
                    action.Scope = 2;
                    var pool = rule == TargetRule.RandomAllies ? allyPool : opponentPool;
                    if (pool.Count > 0)
                    {
                        int picks = Math.Max(1, HitCountOf(action));
                        for (int i = 0; i < picks; i++) ids.Add(pool[_rng.RandiRange(0, pool.Count - 1)].Id);
                    }
                    break;
                }
                default:
                {
                    bool pickAllies = rule == TargetRule.SingleAlly;
                    var pool = pickAllies ? allyPool : opponentPool;
                    var team = pickAllies ? allies : opponents;
                    if (action.TargetIds.Count > 0)
                    {
                        var chosen = UnitById(action.TargetIds[0]);
                        if (chosen == null || !team.Contains(chosen) || !pool.Contains(chosen)) return "invalid_target";
                        ids.Add(chosen.Id);
                    }
                    else if (pool.Count > 0) ids.Add(pool[0].Id);
                    if (!pickAllies && IsOffensive(effect))
                    {
                        var forced = ProvokeTarget(actor, opponentPool);
                        if (forced != null) { ids.Clear(); ids.Add(forced.Id); }
                    }
                    break;
                }
            }
            if (ids.Count == 0 && rule != TargetRule.None) return "no_target";
            action.TargetIds.Clear();
            action.TargetIds.AddRange(ids);
            return null;
        }

        static bool IsOffensive(ActionEffect e)
            => e == ActionEffect.Damage || e == ActionEffect.DamageFixed || e == ActionEffect.Debuff || e == ActionEffect.Status;

        BattleUnit ProvokeTarget(BattleUnit actor, List<BattleUnit> livingOpponents)
        {
            string provoker = actor.ProvokedBy();
            if (provoker != "")
            {
                var u = UnitById(provoker);
                if (u != null && livingOpponents.Contains(u)) return u;
            }
            foreach (var u in livingOpponents) if (u.IsTaunting) return u;
            return null;
        }

        static int HitCountOf(BattleAction action) => action.Skill != null ? action.Skill.HitCount : 1;

        /// <summary>Effect family of an action (damage, heal, buff, ...).</summary>
        static ActionEffect EffectOf(BattleAction action)
        {
            switch (action.Kind)
            {
                case ActionKind.Attack: return ActionEffect.Damage;
                case ActionKind.Item: return action.Item == null ? ActionEffect.Unusable : ItemEffect(action.Item);
                case ActionKind.Skill: return action.Skill == null ? ActionEffect.Damage : SkillEffect(action.Skill);
                default: return ActionEffect.Damage;
            }
        }

        /// <summary>Effect family of a skill.</summary>
        public static ActionEffect SkillEffect(SkillDef skill)
        {
            switch (skill.Kind)
            {
                case SkillKind.Heal: return ActionEffect.Heal;
                case SkillKind.Buff: return ActionEffect.Buff;
                case SkillKind.Debuff: return ActionEffect.Debuff;
                case SkillKind.Revive: return ActionEffect.Revive;
                case SkillKind.Cleanse: return ActionEffect.Cleanse;
                default: return ActionEffect.Damage;
            }
        }

        /// <summary>Effect family of an item in battle (ESCAPE_DUNGEON and MATERIAL are unusable).</summary>
        public static ActionEffect ItemEffect(ItemDef item)
        {
            switch (item.ItemType)
            {
                case ItemType.Healing: return ActionEffect.Heal;
                case ItemType.MpRestore: return ActionEffect.RestoreMp;
                case ItemType.Cure: return ActionEffect.Cleanse;
                case ItemType.Revive: return ActionEffect.Revive;
                case ItemType.FleeBattle: return ActionEffect.Flee;
                case ItemType.Damage: return ActionEffect.DamageFixed;
                case ItemType.Buff: return ActionEffect.Buff;
                default: return ActionEffect.Unusable;
            }
        }

        static TargetRule RuleOf(BattleAction action)
        {
            switch (action.Kind)
            {
                case ActionKind.Guard: return TargetRule.Self;
                case ActionKind.Attack: return TargetRule.SingleEnemy;
                case ActionKind.Item: return action.Item == null ? TargetRule.SingleEnemy : ItemRule(action.Item);
                case ActionKind.Skill: return action.Skill == null ? TargetRule.SingleEnemy : SkillRule(action.Skill);
                default: return TargetRule.None;
            }
        }

        /// <summary>Target rule of a skill (target_type x scope).</summary>
        public static TargetRule SkillRule(SkillDef skill)
        {
            int scope = Gd.Clamp((int)skill.Scope, 0, 2);
            switch (skill.TargetType)
            {
                case TargetType.Ally: return scope == 0 ? TargetRule.SingleAlly : (scope == 1 ? TargetRule.AllAllies : TargetRule.RandomAllies);
                case TargetType.Self: return TargetRule.Self;
                default: return scope == 0 ? TargetRule.SingleEnemy : (scope == 1 ? TargetRule.AllEnemies : TargetRule.RandomEnemies);
            }
        }

        /// <summary>Target rule of an item (its authored `target`).</summary>
        public static TargetRule ItemRule(ItemDef item)
        {
            switch ((item.Target ?? "").ToLowerInvariant())
            {
                case "single_ally": case "ally": return TargetRule.SingleAlly;
                case "all_allies": case "party": return TargetRule.AllAllies;
                case "all_enemies": case "enemies": return TargetRule.AllEnemies;
                case "random_enemies": return TargetRule.RandomEnemies;
                case "random_allies": return TargetRule.RandomAllies;
                case "all": return TargetRule.All;
                case "self": return TargetRule.Self;
                case "none": return TargetRule.None;
                default: return TargetRule.SingleEnemy;
            }
        }

        // --- Resolution -----------------------------------------------------------------------------

        void Execute(BattleAction action)
        {
            if (!_active) return;
            var actor = UnitById(action.ActorId);
            if (actor == null || !actor.IsAlive) return;
            _actionDealtDamage = false;
            _actionHpDealt = 0;
            _actionDamaged.Clear();
            _actionEffectShown.Clear();
            _actionHitIndex.Clear();
            ApplyActionBleed(actor);
            if (!actor.IsAlive) return;
            EmitActionStart(actor, action);

            switch (action.Kind)
            {
                case ActionKind.Attack:
                    ResolveDamage(actor, action, null);
                    break;
                case ActionKind.Skill:
                {
                    int mp = Math.Max(0, action.Skill.MpCost), tp = Math.Max(0, action.Skill.TpCost);
                    if (actor.SpendMp(mp))
                    {
                        if (mp > 0) Emit(new MpChangeEvent { UnitId = actor.Id, Mp = actor.Mp, MaxMp = actor.MaxMp, Delta = -mp });
                        if (tp > 0)
                        {
                            int before = actor.Tp;
                            actor.Tp = Math.Max(0, actor.Tp - tp);
                            Emit(new TpChangeEvent { UnitId = actor.Id, Tp = actor.Tp, MaxTp = actor.MaxTp, Delta = actor.Tp - before });
                        }
                        ResolvePayload(actor, action);
                    }
                    break;
                }
                case ActionKind.Item:
                    ConsumeItem(action.PayloadId);
                    if (EffectOf(action) == ActionEffect.Flee)
                    {
                        Msg("smoke_bomb");
                        Emit(new FleeEvent { Success = true, SmokeBomb = true });
                        Emit(new ActionEndEvent { ActorId = actor.Id, Kind = action.Kind });
                        EndBattle(BattleResult.Fled);
                        return;
                    }
                    ResolvePayload(actor, action);
                    break;
                case ActionKind.Guard:
                    actor.Guarding = true;
                    Msg("guard", actor.DisplayName);
                    break;
                case ActionKind.Flee:
                    if (AttemptFlee())
                    {
                        Emit(new FleeEvent { Success = true });
                        Emit(new ActionEndEvent { ActorId = actor.Id, Kind = action.Kind });
                        EndBattle(BattleResult.Fled);
                        return;
                    }
                    Emit(new FleeEvent { Success = false });
                    Msg("flee_failed");
                    break;
                case ActionKind.Summon:
                    Msg("summon", actor.DisplayName);
                    Summon(actor, new[] { action.PayloadId });
                    break;
            }

            if (_actionDealtDamage) GainTp(actor, TpOnDeal);
            foreach (var t in _actionDamaged) GainTp(t, TpOnTake);
            CheckPhases();
            Emit(new ActionEndEvent { ActorId = actor.Id, Kind = action.Kind });
        }

        void EmitActionStart(BattleUnit actor, BattleAction action)
        {
            var ev = new ActionStartEvent
            {
                ActorId = actor.Id, Kind = action.Kind, TargetIds = new List<string>(action.TargetIds),
                Scope = (Scope)action.Scope, HitCount = 1,
            };
            switch (action.Kind)
            {
                case ActionKind.Attack:
                    ev.Element = actor.AttackElement;
                    ev.PresentationId = AttackPresentation(actor);
                    break;
                case ActionKind.Skill:
                    ev.SkillId = action.Skill.Id;
                    ev.DisplayName = action.Skill.DisplayName;
                    ev.PresentationId = action.Skill.Presentation;
                    ev.Element = DamageFormula.ElementOf(actor, action.Skill);
                    ev.HitCount = Math.Max(1, action.Skill.HitCount);
                    ev.IsUltimate = action.Skill.TpCost > 0;
                    break;
                case ActionKind.Item:
                    ev.ItemId = action.Item.Id;
                    ev.DisplayName = action.Item.DisplayName;
                    ev.Element = (int)action.Item.Element;
                    break;
                case ActionKind.Summon:
                    ev.SkillId = action.PayloadId;
                    break;
            }
            Emit(ev);
        }

        /// <summary>Per-hero basic attack staging (attack_warrior, attack_archer, ...), attack_enemy for monsters.</summary>
        string AttackPresentation(BattleUnit actor)
        {
            string id = actor.Side == BattleSide.Enemy ? "attack_enemy" : "attack_" + actor.DefId;
            if (_db.Presentations.ContainsKey(id)) return id;
            return actor.Side == BattleSide.Party && _db.Presentations.ContainsKey("attack_party") ? "attack_party" : null;
        }

        void ApplyActionBleed(BattleUnit actor)
        {
            foreach (var s in new List<BattleStatus>(actor.Statuses))
            {
                if (s.BleedRatio <= 0.0 || !actor.IsAlive) continue;
                double ratio = s.BleedRatio * (actor.HasGimmick("dot_resist") ? 0.25 : 1.0);
                StatusDamage(actor, Math.Max(1, Gd.RoundI(actor.MaxHp * ratio)), s);
            }
        }

        void ResolvePayload(BattleUnit actor, BattleAction action)
        {
            switch (EffectOf(action))
            {
                case ActionEffect.Heal: ResolveHeal(actor, action); break;
                case ActionEffect.Status:
                case ActionEffect.Buff:
                case ActionEffect.Debuff:
                    ApplyPayloadStatuses(actor, TargetsOf(action), action.Skill, true);
                    ApplyItemStatus(actor, TargetsOf(action), action.Item);
                    break;
                case ActionEffect.RestoreMp: ResolveMpRestore(action); break;
                case ActionEffect.Revive: ResolveRevive(actor, action); break;
                case ActionEffect.Cleanse: ResolveCleanse(actor, action); break;
                case ActionEffect.DamageFixed: ResolveFixedDamage(actor, action); break;
                default: ResolveDamage(actor, action, action.Skill); break;
            }
        }

        List<BattleUnit> TargetsOf(BattleAction action)
        {
            var r = new List<BattleUnit>();
            foreach (var id in action.TargetIds)
            {
                var u = UnitById(id);
                if (u != null && !r.Contains(u)) r.Add(u);
            }
            return r;
        }

        void ResolveDamage(BattleUnit actor, BattleAction action, SkillDef skill)
        {
            int hitCount = Math.Max(1, skill != null ? skill.HitCount : 1);
            int hitsPerTarget = action.Scope == 2 ? 1 : hitCount;
            var statusTargets = new List<BattleUnit>();
            for (int pick = 0; pick < action.TargetIds.Count; pick++)
            {
                var target = UnitById(action.TargetIds[pick]);
                if (action.Scope == 2 && (target == null || !target.IsAlive))
                {
                    var randomPool = EnemyAI.Living(actor.Side == BattleSide.Party ? _enemies : _party);
                    if (randomPool.Count > 0)
                    {
                        target = randomPool[_rng.RandiRange(0, randomPool.Count - 1)];
                        action.TargetIds[pick] = target.Id;
                    }
                }
                if (target == null || !target.IsAlive) continue;
                bool landed = false;
                for (int h = 0; h < hitsPerTarget; h++)
                {
                    if (!target.IsAlive) break;
                    var roll = DamageFormula.Damage(actor, target, skill, _rng);
                    if (roll.Missed)
                    {
                        Emit(new MissEvent { TargetId = target.Id, SourceId = actor.Id, HitIndex = NextHitIndex(target) });
                        continue;
                    }
                    landed = true;
                    DealHit(actor, target, roll.Amount, roll.Critical, roll.Type, roll.Element, roll.ElementMultiplier);
                }
                if (landed && target.IsAlive && !statusTargets.Contains(target)) statusTargets.Add(target);
            }
            ApplyDrain(actor, skill);
            ApplyPayloadStatuses(actor, statusTargets, skill, false);
        }

        /// <summary>Drain skills return a share of the HP damage dealt to the actor (no RNG; burn halves it).</summary>
        void ApplyDrain(BattleUnit actor, SkillDef skill)
        {
            if (skill == null || skill.Drain <= 0f || _actionHpDealt <= 0 || !actor.IsAlive) return;
            double ratio = Gd.Clamp(Gd.D(skill.Drain), 0.0, 1.0);
            int applied = actor.Heal(Gd.RoundI(_actionHpDealt * ratio * actor.HealingReceivedScale));
            if (applied > 0)
                Emit(new HealEvent { TargetId = actor.Id, SourceId = actor.Id, Amount = applied, HpAfter = actor.Hp, MaxHp = actor.MaxHp });
        }

        int NextHitIndex(BattleUnit target)
        {
            _actionHitIndex.TryGetValue(target.Id, out int i);
            _actionHitIndex[target.Id] = i + 1;
            return i;
        }

        /// <summary>DAMAGE items: fixed value (or power x 100) x element multiplier; never misses.</summary>
        void ResolveFixedDamage(BattleUnit actor, BattleAction action)
        {
            var item = action.Item;
            int baseAmount = item.Value;
            if (baseAmount <= 0) baseAmount = Gd.RoundI(Math.Max(0.0, Gd.D(item.Power)) * 100.0);
            int element = (int)item.Element;
            foreach (var target in TargetsOf(action))
            {
                if (!target.IsAlive) continue;
                double multiplier = DamageFormula.ElementMultiplier(target, element);
                double amount = baseAmount * multiplier;
                if (target.Broken) amount *= DamageFormula.BrokenMultiplier;
                DealHit(actor, target, Math.Max(1, Gd.RoundI(amount)), false, DamageType.Item, element, multiplier);
            }
        }

        void DealHit(BattleUnit actor, BattleUnit target, int amount, bool critical, DamageType type, int element, double multiplier)
        {
            bool show = multiplier != 1.0 && _actionEffectShown.Add(target.Id);
            int mpBefore = target.Mp;
            int hitIndex = NextHitIndex(target);
            var r = target.ReceiveDamage(amount, type);
            Emit(new DamageEvent
            {
                TargetId = target.Id, SourceId = actor.Id, Amount = r.Hp, Absorbed = r.Absorbed, Critical = critical, Type = type,
                Element = element, Effectiveness = multiplier > 1.0 ? Effectiveness.Weak : (multiplier < 1.0 ? Effectiveness.Resist : Effectiveness.Normal),
                ShowEffectiveness = show, HitIndex = hitIndex, HpAfter = target.Hp, MaxHp = target.MaxHp, Killed = !target.IsAlive,
            });
            if (r.Mp > 0) Emit(new MpChangeEvent { UnitId = target.Id, Mp = target.Mp, MaxMp = target.MaxMp, Delta = target.Mp - mpBefore });
            foreach (var id in r.Removed) Emit(new StatusRemovedEvent { UnitId = target.Id, StatusId = id, Reason = StatusRemoveReason.Damage });
            if (r.Hp > 0)
            {
                if (actor.Side != target.Side) { _actionDealtDamage = true; _actionHpDealt += r.Hp; }
                if (!_actionDamaged.Contains(target)) _actionDamaged.Add(target);
            }
            if (multiplier < 1.0 && target.Side == BattleSide.Enemy) _resistSeen.Add(WeaknessKey(target.DefId, element));
            if (multiplier > 1.0)
            {
                if (target.Side == BattleSide.Enemy) DiscoverWeakness(target, element);
                if (target.IsAlive && target.MaxShield > 0 && !target.Broken)
                {
                    target.Shield = Math.Max(0, target.Shield - 1);
                    Emit(new ShieldChangeEvent { UnitId = target.Id, Shield = target.Shield, MaxShield = target.MaxShield });
                    if (target.Shield == 0)
                    {
                        target.Broken = true;
                        Emit(new BreakEvent { UnitId = target.Id });
                        foreach (var ally in _party) GainTp(ally, TpOnBreak);
                        Msg("break", target.DisplayName);
                    }
                }
            }
            if (!target.IsAlive) OnUnitDown(target);
            CheckPhases();
        }

        void DiscoverWeakness(BattleUnit unit, int element)
        {
            string key = WeaknessKey(unit.DefId, element);
            bool wasKnown = _known.Contains(key) || _discovered.Contains(key);
            _discovered.Add(key);
            if (!wasKnown) Emit(new WeaknessDiscoveredEvent { UnitId = unit.Id, EnemyId = unit.DefId, Element = element });
        }

        void OnUnitDown(BattleUnit unit)
        {
            Emit(new UnitDownEvent { UnitId = unit.Id });
            unit.Guarding = false;
            foreach (var id in unit.ClearStatuses())
                Emit(new StatusRemovedEvent { UnitId = unit.Id, StatusId = id, Reason = StatusRemoveReason.Down });
            if (unit.Tp != 0)
            {
                int before = unit.Tp;
                unit.Tp = 0;
                Emit(new TpChangeEvent { UnitId = unit.Id, Tp = 0, MaxTp = unit.MaxTp, Delta = -before });
            }
            if (unit.Side == BattleSide.Party)
                foreach (var ally in _party)
                    if (ally != unit && ally.IsAlive) GainTp(ally, TpOnAllyFall);
        }

        void GainTp(BattleUnit unit, int amount)
        {
            int delta = unit.GainTp(amount);
            if (delta != 0) Emit(new TpChangeEvent { UnitId = unit.Id, Tp = unit.Tp, MaxTp = unit.MaxTp, Delta = delta });
        }

        void ResolveHeal(BattleUnit actor, BattleAction action)
        {
            var targets = TargetsOf(action);
            foreach (var target in targets)
            {
                if (!target.IsAlive) continue;
                int amount = action.Item != null ? Math.Max(0, action.Item.HealAmount) : DamageFormula.Healing(actor, action.Skill, _rng);
                amount = Gd.RoundI(amount * target.HealingReceivedScale);
                int applied = target.Heal(amount);
                if (applied > 0)
                    Emit(new HealEvent { TargetId = target.Id, SourceId = actor.Id, Amount = applied, HpAfter = target.Hp, MaxHp = target.MaxHp });
            }
            ApplyPayloadStatuses(actor, targets, action.Skill, true);
        }

        void ResolveMpRestore(BattleAction action)
        {
            var item = action.Item;
            foreach (var target in TargetsOf(action))
            {
                if (!target.IsAlive) continue;
                int amount = item != null ? item.Value : 0;
                if (amount <= 0)
                {
                    double power = item != null ? Gd.D(item.Power) : 0.0;
                    amount = power <= 1.0 ? Gd.RoundI(target.MaxMp * power) : Gd.RoundI(power);
                }
                int before = target.Mp;
                target.Mp = Math.Min(target.MaxMp, target.Mp + Math.Max(0, amount));
                Emit(new MpChangeEvent { UnitId = target.Id, Mp = target.Mp, MaxMp = target.MaxMp, Delta = target.Mp - before });
            }
        }

        /// <summary>REVIVE: KO'd allies return with max(1, power x max HP).</summary>
        void ResolveRevive(BattleUnit actor, BattleAction action)
        {
            double power = action.Item != null ? Gd.D(action.Item.Power) : (action.Skill != null ? Gd.D(action.Skill.Power) : 0.5);
            double ratio = Gd.Clamp(power, 0.0, 1.0);
            foreach (var target in TargetsOf(action))
            {
                if (target.IsAlive) continue;
                target.Hp = Gd.Clamp(Gd.RoundI(target.MaxHp * ratio), 1, target.MaxHp);
                target.Broken = false;
                target.Tp = 0;
                Emit(new ReviveEvent { UnitId = target.Id, Hp = target.Hp, MaxHp = target.MaxHp });
                Emit(new HealEvent { TargetId = target.Id, SourceId = actor.Id, Amount = target.Hp, HpAfter = target.Hp, MaxHp = target.MaxHp });
                Msg("revived", target.DisplayName);
            }
        }

        /// <summary>CLEANSE: removes the item's status_id, or every harmful status.</summary>
        void ResolveCleanse(BattleUnit actor, BattleAction action)
        {
            string only = action.Item != null ? (action.Item.StatusId ?? "") : "";
            var targets = TargetsOf(action);
            foreach (var target in targets)
            {
                if (!target.IsAlive) continue;
                bool removedAny = false;
                for (int i = target.Statuses.Count - 1; i >= 0; i--)
                {
                    var s = target.Statuses[i];
                    bool hit = only != "" ? s.Matches(only) : !s.IsBeneficial;
                    if (hit)
                    {
                        Emit(new StatusRemovedEvent { UnitId = target.Id, StatusId = target.RemoveStatusAt(i), Reason = StatusRemoveReason.Cleansed });
                        removedAny = true;
                    }
                }
                if (removedAny) Msg("cleansed", target.DisplayName);
            }
            ApplyPayloadStatuses(actor, targets, action.Skill, true);
        }

        void ApplyItemStatus(BattleUnit actor, List<BattleUnit> targets, ItemDef item)
        {
            if (item == null || string.IsNullOrEmpty(item.StatusId)) return;
            if (!_db.Statuses.TryGetValue(item.StatusId, out var def)) return;
            foreach (var t in targets) ApplyStatusTo(actor, t, def);
        }

        /// <summary>
        /// status_effect + extra_statuses of a skill: one roll per target for all entries. Status-only
        /// kinds treat status_chance 0 as "always"; cc_resist halves STUN/SLEEP/FREEZE chances.
        /// </summary>
        void ApplyPayloadStatuses(BattleUnit actor, List<BattleUnit> targets, SkillDef skill, bool statusKind)
        {
            if (skill == null) return;
            var entries = new List<string>();
            if (!string.IsNullOrEmpty(skill.StatusEffect)) entries.Add(skill.StatusEffect);
            if (skill.ExtraStatuses != null) entries.AddRange(skill.ExtraStatuses);
            if (entries.Count == 0) return;
            double chance = Gd.Clamp(Gd.D(skill.StatusChance), 0.0, 1.0);
            if (statusKind && chance <= 0.0) chance = 1.0;
            foreach (var target in targets)
            {
                if (!target.IsAlive) continue;
                double roll = _rng.Randf();
                foreach (var entry in entries)
                {
                    if (entry == null || !_db.Statuses.TryGetValue(entry, out var def)) continue;
                    double landing = chance;
                    if (target.HasGimmick("cc_resist") && BattleUnit.IsCrowdControl(def.EffectType)) landing *= 0.5;
                    if (roll < landing) ApplyStatusTo(actor, target, def);
                }
            }
        }

        void ApplyStatusTo(BattleUnit actor, BattleUnit target, StatusDef def)
        {
            if (!target.IsAlive) return;
            var effect = BattleStatus.FromDef(def, actor != null ? actor.Id : "");
            if (target.IsImmuneTo(effect))
            {
                Emit(new StatusImmuneEvent { UnitId = target.Id, StatusId = effect.Id });
                Msg("immune", target.DisplayName, effect.DisplayName);
                return;
            }
            bool refreshed = target.ApplyStatus(effect);
            BattleStatus current = effect;
            foreach (var s in target.Statuses) if (s.Id == effect.Id) { current = s; break; }
            Emit(new StatusAppliedEvent
            {
                UnitId = target.Id, StatusId = current.Id, DisplayName = current.DisplayName, EffectType = current.EffectType,
                Turns = current.TurnsRemaining, Beneficial = current.IsBeneficial, Refreshed = refreshed, SourceId = current.SourceId,
            });
        }

        // --- Phases, enrage, summons --------------------------------------------------------------

        /// <summary>Boss phases (one-shot each, in order) and berserker enrage; runs after every hit/action.</summary>
        void CheckPhases()
        {
            // Summons append to this list; only units present at entry participate in this check.
            int enemyCount = _enemies.Count;
            for (int enemyIndex = 0; enemyIndex < enemyCount; enemyIndex++)
            {
                var enemy = _enemies[enemyIndex];
                if (!enemy.IsAlive) continue;
                double ratio = (double)enemy.Hp / enemy.MaxHp;
                for (int i = 0; i < enemy.Phases.Count; i++)
                {
                    if (enemy.PhasesDone.Contains(i) || enemy.Phases[i] == null) continue;
                    var row = enemy.Phases[i];
                    if (ratio > Gd.D(row.HpBelow)) continue;
                    enemy.PhasesDone.Add(i);
                    ActivatePhase(enemy, i, row);
                }
                if (enemy.AiProfile == "berserker" && !enemy.Enraged && ratio < EnrageBelow)
                {
                    enemy.Enraged = true;
                    Emit(new EnrageEvent { UnitId = enemy.Id });
                    if (!_db.Statuses.TryGetValue("attack_up_berserk", out var def))
                        def = new StatusDef { Id = "attack_up_berserk", DisplayName = _db.T("enrage_name"), EffectType = StatusEffectType.AttackUp, DurationTurns = 5, Magnitude = 0.5f };
                    ApplyStatusTo(enemy, enemy, def);
                    Msg("enrage", enemy.DisplayName);
                }
            }
        }

        void ActivatePhase(BattleUnit enemy, int index, BossPhase row)
        {
            if (row.Skills != null)
            {
                var resolved = new List<SkillDef>();
                foreach (var id in row.Skills)
                {
                    var skill = FindActorSkill(enemy, id);
                    if (skill == null && id != null) _db.Skills.TryGetValue(id, out skill);
                    if (skill != null) resolved.Add(skill);
                }
                if (resolved.Count > 0)
                {
                    enemy.SkillList = resolved;
                    enemy.SkillWeights = new List<int>(row.Weights ?? new List<int>());
                }
            }
            enemy.ActionsPerTurn = Gd.Clamp(row.ActionsPerTurn, 1, 6);
            Emit(new BossPhaseEvent { UnitId = enemy.Id, PhaseIndex = index, Line = row.Line ?? "", ActionsPerTurn = enemy.ActionsPerTurn });
            if (row.Summon != null && row.Summon.Count > 0) Summon(enemy, row.Summon);
        }

        /// <summary>Adds enemies (capped at <see cref="MaxLivingEnemies"/> living). Summons give no rewards.</summary>
        void Summon(BattleUnit summoner, IEnumerable<string> ids)
        {
            foreach (var id in ids)
            {
                if (EnemyAI.CountLiving(_enemies) >= MaxLivingEnemies) break;
                if (id == null || !_db.Enemies.TryGetValue(id, out var def)) continue;
                var unit = BattleUnit.FromEnemy(_db, def, EnemyStats.Build(def, _setup.Difficulty, _enemyPower), _enemies.Count);
                unit.Summoned = true;
                unit.SummonerId = summoner.Id;
                _enemies.Add(unit);
                Register(unit, null);
                Emit(new SummonEvent { SummonerId = summoner.Id, Unit = unit.Snapshot(KnownWeaknessesOf(unit)) });
            }
        }

        void Register(BattleUnit unit, Dictionary<string, int> initialStatuses)
        {
            _byId[unit.Id] = unit;
            _units.Add(unit);
            if (initialStatuses == null) return;
            foreach (var kv in initialStatuses)
            {
                if (string.IsNullOrEmpty(kv.Key) || !_db.Statuses.TryGetValue(kv.Key, out var def)) continue;
                var effect = BattleStatus.FromDef(def, "");
                if (kv.Value > 0) effect.TurnsRemaining = kv.Value;
                if (!unit.IsImmuneTo(effect)) unit.ApplyStatus(effect);
            }
        }

        // --- Flee / outcome / rewards -----------------------------------------------------------------

        bool AttemptFlee()
        {
            if (!FleeAllowed()) return false;
            double partySpeed = AverageSpeed(EnemyAI.Living(_party));
            double enemySpeed = AverageSpeed(EnemyAI.Living(_enemies));
            double chance = Gd.Clamp(0.55 + (partySpeed - enemySpeed) * 0.02, 0.15, 0.90);
            return _rng.Randf() <= chance;
        }

        static double AverageSpeed(List<BattleUnit> units)
        {
            if (units.Count == 0) return 0.0;
            double total = 0.0;
            foreach (var u in units) total += u.EffectiveSpeed;
            return total / units.Count;
        }

        void ConsumeItem(string itemId)
        {
            _inventory[itemId] = Math.Max(0, InventoryCount(itemId) - 1);
            _itemsUsed.TryGetValue(itemId, out int used);
            _itemsUsed[itemId] = used + 1;
        }

        bool CheckOutcome()
        {
            if (!_active) return true;
            if (!EnemyAI.AnyLiving(_enemies)) { EndBattle(BattleResult.Victory); return true; }
            if (!EnemyAI.AnyLiving(_party)) { EndBattle(BattleResult.Defeat); return true; }
            return false;
        }

        void EndBattle(BattleResult result)
        {
            if (!_active) return;
            _active = false;
            _awaiting = false;
            if (result == BattleResult.Victory) RollRewards();
            foreach (var m in _party)
            {
                if (m.Tp == 0) continue;
                int before = m.Tp;
                m.Tp = 0;
                Emit(new TpChangeEvent { UnitId = m.Id, Tp = 0, MaxTp = m.MaxTp, Delta = -before });
            }
            _outcome = BuildOutcome(result);
            Emit(new BattleEndEvent { Result = result, Outcome = _outcome });
        }

        /// <summary>Drops roll exactly once, in enemy order (summons excluded), with the battle RNG.</summary>
        void RollRewards()
        {
            _drops.Clear();
            foreach (var e in _enemies)
            {
                if (e.Summoned) continue;
                foreach (var row in e.Drops)
                {
                    if (_rng.Randf() < Gd.Clamp(Gd.D(row.Chance), 0.0, 1.0))
                    {
                        _drops.TryGetValue(row.Id, out int n);
                        _drops[row.Id] = n + 1;
                    }
                }
            }
        }

        BattleOutcome BuildOutcome(BattleResult result)
        {
            var o = new BattleOutcome { Result = result };
            if (result == BattleResult.Victory)
            {
                foreach (var e in _enemies)
                {
                    if (e.Summoned) continue;
                    o.Experience += Math.Max(0, e.ExperienceReward);
                    o.Gold += Math.Max(0, e.GoldReward);
                }
                foreach (var kv in _drops) o.Drops[kv.Key] = kv.Value;
            }
            foreach (var kv in _itemsUsed) o.ItemsUsed[kv.Key] = kv.Value;
            foreach (var e in _enemies)
            {
                if (!o.SeenEnemies.Contains(e.DefId)) o.SeenEnemies.Add(e.DefId);
                if (!e.Summoned && !e.IsAlive) o.DefeatedEnemies.Add(e.DefId);
            }
            foreach (var h in _party)
            {
                o.FinalHp[h.DefId] = h.Hp;
                o.FinalMp[h.DefId] = h.Mp;
                var st = new Dictionary<string, int>();
                if (h.IsAlive)
                    foreach (var s in h.Statuses) if (s.TurnsRemaining > 0) st[s.Id] = s.TurnsRemaining;
                o.FinalStatuses[h.DefId] = st;
            }
            foreach (var k in _discovered) o.DiscoveredWeaknesses.Add(k);
            return o;
        }
    }
}
