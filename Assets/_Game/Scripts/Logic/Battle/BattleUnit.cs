// One combatant (port of battle_unit.gd). Public members are read-only views for the battle UI;
// the engine mutates state through internal members.
using System;
using System.Collections.Generic;

namespace Abyss.Logic.Battle
{
    /// <summary>Team of a unit.</summary>
    public enum BattleSide { Party = 0, Enemy = 1 }

    /// <summary>Damage channel of a hit (decides crit/miss/FREEZE shatter rules).</summary>
    public enum DamageType { Physical = 0, Magical = 1, Status = 2, Item = 3 }

    /// <summary>A hero or enemy in battle with its live combat state.</summary>
    public sealed class BattleUnit
    {
        /// <summary>Max TP of party members (enemies have none).</summary>
        public const int MaxTpValue = 100;

        /// <summary>Unique unit id, e.g. "party_00_warrior", "enemy_02_slime" (summons continue the enemy index).</summary>
        public string Id { get; private set; }
        /// <summary>Hero id or enemy id (heroes.json / enemies.json).</summary>
        public string DefId { get; private set; }
        /// <summary>Localised display name.</summary>
        public string DisplayName { get; private set; }
        /// <summary>Team.</summary>
        public BattleSide Side { get; private set; }
        /// <summary>Formation index (party order / enemy order; summons get the next free index).</summary>
        public int Slot { get; private set; }
        /// <summary>Row for presentation: hero spec row, or enemy battle_row (0 front, 1 back).</summary>
        public int Row { get; private set; }
        /// <summary>Level.</summary>
        public int Level { get; private set; }
        /// <summary>Source hero spec (party units only).</summary>
        public HeroCombatSpec HeroSpec { get; private set; }
        /// <summary>Source enemy definition (enemy units only).</summary>
        public EnemyDef EnemyDef { get; private set; }

        public int MaxHp { get; internal set; }
        public int Hp { get; internal set; }
        public int MaxMp { get; internal set; }
        public int Mp { get; internal set; }
        public int Tp { get; internal set; }
        public int MaxTp { get; private set; }
        /// <summary>Base stats after difficulty / equipment (statuses not applied).</summary>
        public int Attack { get; private set; }
        public int Defense { get; private set; }
        public int Magic { get; private set; }
        public int Resistance { get; private set; }
        public int Speed { get; private set; }
        public double CritRate { get; private set; }
        public double CritMultiplier { get; private set; }
        public double HitRate { get; private set; }
        public double Evade { get; private set; }
        /// <summary>Element of a plain attack (0 = none).</summary>
        public int AttackElement { get; private set; }
        /// <summary>Gear regeneration at the end of each own turn (party units): ratio of max HP, flat MP.</summary>
        public double HpRegenRatio { get; private set; }
        public int MpRegenPerTurn { get; private set; }

        public int MaxShield { get; private set; }
        public int Shield { get; internal set; }
        public bool Broken { get; internal set; }
        public bool Guarding { get; internal set; }

        public bool IsBoss { get; private set; }
        public int Rank { get; private set; }
        public string AiProfile { get; private set; } = "basic";
        public int ActionsPerTurn { get; internal set; } = 1;
        public bool Summoned { get; internal set; }
        public string SummonerId { get; internal set; } = "";
        public bool Enraged { get; internal set; }
        /// <summary>Ran away (runner AI): out of the fight, but neither defeated nor rewarded.</summary>
        public bool Escaped { get; internal set; }
        public int ExperienceReward { get; private set; }
        public int GoldReward { get; private set; }

        public IReadOnlyList<int> Weaknesses => _weaknesses;
        public IReadOnlyList<int> Resistances => _resistances;
        public IReadOnlyList<string> StatusImmunities => _immunities;
        public IReadOnlyList<string> Gimmicks => _gimmicks;
        /// <summary>Current statuses in application order.</summary>
        public IReadOnlyList<BattleStatus> Statuses => _statuses;
        /// <summary>Usable skills (resolved, in authored order; phases replace them for bosses).</summary>
        public IReadOnlyList<SkillDef> Skills => SkillList;

        public bool IsAlive => Hp > 0;

        internal List<SkillDef> SkillList = new List<SkillDef>();
        internal List<int> SkillWeights = new List<int>();
        internal List<BossPhase> Phases = new List<BossPhase>();
        internal List<int> PhasesDone = new List<int>();
        internal List<string> Summons = new List<string>();
        internal int SummonLimit;
        internal List<DropEntry> Drops = new List<DropEntry>();
        internal readonly List<BattleStatus> _statuses = new List<BattleStatus>();
        readonly List<int> _weaknesses = new List<int>();
        readonly List<int> _resistances = new List<int>();
        readonly List<string> _immunities = new List<string>();
        readonly List<string> _gimmicks = new List<string>();

        BattleUnit() { }

        internal static BattleUnit FromHero(GameDB db, HeroCombatSpec spec, int index)
        {
            var u = new BattleUnit
            {
                HeroSpec = spec,
                Side = BattleSide.Party,
                Slot = index,
                DefId = string.IsNullOrEmpty(spec.HeroId) ? "unit_" + index : spec.HeroId,
                Row = spec.Row,
            };
            u.Id = MakeId(BattleSide.Party, index, u.DefId);
            u.DisplayName = !string.IsNullOrEmpty(spec.DisplayName) ? spec.DisplayName
                : (db.Heroes.TryGetValue(u.DefId, out var hd) ? hd.DisplayName : u.DefId);
            u.Level = Math.Max(1, spec.Level);
            u.MaxHp = Math.Max(1, spec.MaxHp);
            u.Hp = spec.Hp < 0 ? u.MaxHp : Gd.Clamp(spec.Hp, 0, u.MaxHp);
            u.MaxMp = Math.Max(0, spec.MaxMp);
            u.Mp = spec.Mp < 0 ? u.MaxMp : Gd.Clamp(spec.Mp, 0, u.MaxMp);
            u.Attack = Math.Max(1, spec.Attack);
            u.Defense = Math.Max(0, spec.Defense);
            u.Magic = Math.Max(0, spec.Magic);
            u.Resistance = spec.Resistance < 0 ? u.Defense : spec.Resistance;
            u.Speed = Math.Max(1, spec.Speed);
            u.CritRate = Gd.Clamp(Gd.D(spec.Crit), 0.0, 1.0);
            u.CritMultiplier = 1.5;
            u.HitRate = Gd.Clamp(Gd.D(spec.Hit), 0.0, 2.0);
            u.Evade = Gd.Clamp(Gd.D(spec.Evade), 0.0, 0.95);
            foreach (var id in spec.Skills)
                if (id != null && db.Skills.TryGetValue(id, out var sk)) u.SkillList.Add(sk);
            foreach (int e in spec.ElementResists) u._resistances.Add(e);
            foreach (var s in spec.StatusImmunities) u._immunities.Add(s);
            u.MaxTp = MaxTpValue;
            u.AttackElement = Math.Max(0, spec.AttackElement);
            u.HpRegenRatio = Gd.Clamp(Gd.D(spec.HpRegen), 0.0, 1.0);
            u.MpRegenPerTurn = Math.Max(0, spec.MpRegen);
            if (u.Hp > 0) u.Tp = Gd.Clamp(spec.TpStart, 0, u.MaxTp);
            return u;
        }

        internal static BattleUnit FromEnemy(GameDB db, EnemyDef def, EnemyBuild build, int index)
        {
            var u = new BattleUnit
            {
                EnemyDef = def,
                Side = BattleSide.Enemy,
                Slot = index,
                DefId = def.Id,
                Row = def.BattleRow,
            };
            u.Id = MakeId(BattleSide.Enemy, index, def.Id);
            u.DisplayName = string.IsNullOrEmpty(def.DisplayName) ? def.Id : def.DisplayName;
            u.Level = Math.Max(1, def.Level);
            u.MaxHp = Math.Max(1, build.MaxHp);
            u.Hp = u.MaxHp;
            u.MaxMp = Math.Max(0, def.MaxMp);
            u.Mp = u.MaxMp;
            u.Attack = Math.Max(1, build.Attack);
            u.Defense = Math.Max(0, def.Defense);
            u.Magic = Math.Max(0, build.Magic);
            u.Resistance = Math.Max(0, def.Resistance >= 0 ? def.Resistance : def.Defense);
            u.Speed = Math.Max(1, def.Speed);
            u.CritRate = EnemyStats.DefaultCrit;
            u.CritMultiplier = EnemyStats.DefaultCritMultiplier;
            u.HitRate = Gd.Clamp(Gd.D(def.Hit), 0.0, 1.0);
            u.Evade = Gd.Clamp(Gd.D(def.Evade), 0.0, 0.95);
            var seen = new HashSet<string>();
            foreach (var id in def.Skills)
                if (id != null && seen.Add(id) && db.Skills.TryGetValue(id, out var sk)) u.SkillList.Add(sk);
            u._weaknesses.AddRange(def.Weaknesses);
            u._resistances.AddRange(def.Resistances);
            u.MaxTp = 0;
            u.MaxShield = Math.Max(0, def.BreakShield);
            u.Shield = u.MaxShield;
            u.ExperienceReward = Math.Max(0, build.ExperienceReward);
            u.GoldReward = Math.Max(0, build.GoldReward);
            foreach (var d in def.Drops)
                if (d != null && !string.IsNullOrEmpty(d.Id)) u.Drops.Add(d);
            u.Rank = def.Rank;
            u.IsBoss = def.IsBoss || def.Rank == 2;
            u.AiProfile = string.IsNullOrEmpty(def.AiProfile) ? "basic" : def.AiProfile.ToLowerInvariant();
            u.ActionsPerTurn = Gd.Clamp(def.ActionsPerTurn, 1, 6);
            u.SkillWeights.AddRange(def.SkillWeights);
            u.Phases.AddRange(def.Phases);
            u.Summons.AddRange(def.Summons);
            u.SummonLimit = Math.Max(0, def.SummonLimit);
            if (def.Gimmicks != null) u._gimmicks.AddRange(def.Gimmicks);
            return u;
        }

        static string MakeId(BattleSide side, int index, string defId)
            => (side == BattleSide.Party ? "party" : "enemy") + "_" + index.ToString("00") + "_" + defId;

        // --- Derived stats -------------------------------------------------------------------

        public int EffectiveAttack => Math.Max(1, Gd.RoundI(Attack * Scale(s => s.AttackScale)));
        public int EffectiveDefense => Math.Max(0, Gd.RoundI(Defense * Scale(s => s.DefenseScale)));
        public int EffectiveMagic => Math.Max(1, Gd.RoundI(Magic * Scale(s => s.MagicScale)));
        public int EffectiveResistance => Math.Max(0, Gd.RoundI(Resistance * Scale(s => s.ResistanceScale)));
        public int EffectiveSpeed => Math.Max(1, Gd.RoundI(Speed * Scale(s => s.SpeedScale)));
        internal double AccuracyScale => Scale(s => s.AccuracyScale);
        internal double PhysicalDamageTakenScale => Scale(s => s.PhysicalDamageTakenScale);
        internal double HealingReceivedScale => Scale(s => s.HealingReceivedScale);

        double Scale(Func<BattleStatus, double> pick)
        {
            double scale = 1.0;
            foreach (var s in _statuses) scale *= pick(s);
            return scale;
        }

        /// <summary>False while stunned / frozen / asleep (or dead).</summary>
        public bool CanAct
        {
            get
            {
                foreach (var s in _statuses) if (!s.CanAct) return false;
                return IsAlive;
            }
        }

        /// <summary>SILENCE: skills with an MP cost are blocked (ultimates and items are not).</summary>
        public bool IsSilenced
        {
            get
            {
                foreach (var s in _statuses) if (s.BlocksMpSkills) return true;
                return false;
            }
        }

        public bool HasStatus(string key)
        {
            foreach (var s in _statuses) if (s.Matches(key)) return true;
            return false;
        }

        public bool HasGimmick(string gimmick) => _gimmicks.Contains(gimmick);
        public bool IsWeakTo(int element) => element > 0 && _weaknesses.Contains(element);
        public bool Resists(int element) => element > 0 && _resistances.Contains(element);

        internal bool IsImmuneTo(BattleStatus effect)
        {
            foreach (var key in _immunities) if (effect.Matches(key)) return true;
            return HasGimmick("cc_immune") && IsCrowdControl(effect.EffectType);
        }

        internal static bool IsCrowdControl(StatusEffectType t)
            => t == StatusEffectType.Stun || t == StatusEffectType.Sleep || t == StatusEffectType.Freeze;

        /// <summary>Unit id this unit is forced to target (PROVOKE applied by someone else), or "".</summary>
        internal string ProvokedBy()
        {
            foreach (var s in _statuses)
                if (s.Provoke && s.SourceId != "" && s.SourceId != Id) return s.SourceId;
            return "";
        }

        /// <summary>True when this unit taunts (PROVOKE it applied to itself).</summary>
        public bool IsTaunting
        {
            get
            {
                foreach (var s in _statuses)
                    if (s.Provoke && (s.SourceId == Id || s.SourceId == "")) return true;
                return false;
            }
        }

        // --- Mutation --------------------------------------------------------------------------

        internal struct DamageReceipt
        {
            public int Hp;
            public int Mp;
            public int Absorbed;
            public List<string> Removed;
        }

        int TakeDamage(int amount)
        {
            int applied = Math.Min(Math.Max(amount, 0), Hp);
            Hp -= applied;
            return applied;
        }

        /// <summary>Damage after INVINCIBLE / BARRIER / MANA_SHIELD; wakes SLEEP, shatters FREEZE (physical).</summary>
        internal DamageReceipt ReceiveDamage(int amount, DamageType type)
        {
            int remaining = Math.Max(amount, 0);
            int absorbed = 0, mpLoss = 0;
            var removed = new List<string>();
            foreach (var s in _statuses)
            {
                if (s.Invincible) { absorbed += remaining; remaining = 0; break; }
            }
            if (remaining > 0)
            {
                foreach (var s in _statuses)
                {
                    if (s.EffectType != StatusEffectType.Barrier) continue;
                    if (s.BarrierFullHit)
                    {
                        absorbed += remaining;
                        remaining = 0;
                        s.BarrierFullHit = false;
                        s.TurnsRemaining = 0;
                    }
                    else
                    {
                        int used = Math.Min(s.BarrierRemaining, remaining);
                        s.BarrierRemaining -= used;
                        remaining -= used;
                        absorbed += used;
                        if (s.BarrierRemaining <= 0) s.TurnsRemaining = 0;
                    }
                    if (remaining <= 0) break;
                }
            }
            if (remaining > 0)
            {
                foreach (var s in _statuses)
                {
                    if (s.ManaShieldRatio > 0.0 && Mp > 0)
                    {
                        int toMp = Math.Min(Mp, Gd.RoundI(remaining * s.ManaShieldRatio));
                        Mp -= toMp;
                        mpLoss += toMp;
                        remaining -= toMp;
                        break;
                    }
                }
            }
            int applied = TakeDamage(remaining);
            foreach (var s in _statuses)
            {
                if ((s.WakesOnDamage && (applied > 0 || mpLoss > 0)) || (s.BreaksOnPhysical && type == DamageType.Physical && amount > 0))
                    s.TurnsRemaining = 0;
            }
            for (int i = _statuses.Count - 1; i >= 0; i--)
            {
                if (_statuses[i].TurnsRemaining <= 0)
                {
                    removed.Add(_statuses[i].Id);
                    _statuses.RemoveAt(i);
                }
            }
            return new DamageReceipt { Hp = applied, Mp = mpLoss, Absorbed = absorbed, Removed = removed };
        }

        internal int Heal(int amount)
        {
            int before = Hp;
            Hp = Math.Min(MaxHp, Hp + Math.Max(amount, 0));
            return Hp - before;
        }

        internal bool SpendMp(int amount)
        {
            int cost = Math.Max(0, amount);
            if (Mp < cost) return false;
            Mp -= cost;
            return true;
        }

        internal int GainTp(int amount)
        {
            if (MaxTp <= 0 || !IsAlive) return 0;
            int before = Tp;
            Tp = Gd.Clamp(Tp + amount, 0, MaxTp);
            return Tp - before;
        }

        /// <summary>Adds or refreshes (same id) a status. Returns true when an existing one was refreshed.</summary>
        internal bool ApplyStatus(BattleStatus effect)
        {
            effect.BindTo(MaxHp);
            foreach (var cur in _statuses)
            {
                if (cur.Id == effect.Id)
                {
                    cur.RefreshFrom(effect);
                    return true;
                }
            }
            _statuses.Add(effect);
            return false;
        }

        internal string RemoveStatusAt(int index)
        {
            string id = _statuses[index].Id;
            _statuses.RemoveAt(index);
            return id;
        }

        internal List<string> ClearStatuses()
        {
            var removed = new List<string>();
            foreach (var s in _statuses) removed.Add(s.Id);
            _statuses.Clear();
            return removed;
        }

        internal List<string> RemoveExpiredStatuses()
        {
            var expired = new List<string>();
            for (int i = _statuses.Count - 1; i >= 0; i--)
            {
                if (_statuses[i].Tick())
                {
                    expired.Add(_statuses[i].Id);
                    _statuses.RemoveAt(i);
                }
            }
            return expired;
        }

        /// <summary>Immutable copy of the unit's displayable state.</summary>
        public UnitSnapshot Snapshot(IReadOnlyList<int> knownWeaknesses = null)
        {
            var statuses = new List<StatusSnapshot>(_statuses.Count);
            foreach (var s in _statuses) statuses.Add(new StatusSnapshot(s));
            return new UnitSnapshot
            {
                Id = Id, DefId = DefId, DisplayName = DisplayName, Side = Side, Slot = Slot, Row = Row, Level = Level,
                Hp = Hp, MaxHp = MaxHp, Mp = Mp, MaxMp = MaxMp, Tp = Tp, MaxTp = MaxTp,
                Shield = Shield, MaxShield = MaxShield, Broken = Broken, Guarding = Guarding,
                IsAlive = IsAlive, IsBoss = IsBoss, Summoned = Summoned, Statuses = statuses,
                KnownWeaknesses = knownWeaknesses ?? Array.Empty<int>(),
            };
        }

        public override string ToString() => Id;
    }

    /// <summary>Copy of one status at a point in time.</summary>
    public sealed class StatusSnapshot
    {
        public readonly string Id, DisplayName;
        public readonly StatusEffectType EffectType;
        public readonly int Turns;
        public readonly bool Beneficial;
        public readonly float[] Tint;

        public StatusSnapshot(BattleStatus s)
        {
            Id = s.Id; DisplayName = s.DisplayName; EffectType = s.EffectType; Turns = s.TurnsRemaining;
            Beneficial = s.IsBeneficial; Tint = s.Def?.Tint;
        }
    }

    /// <summary>Copy of a unit's displayable state at a point in time (events never reference live state).</summary>
    public sealed class UnitSnapshot
    {
        public string Id, DefId, DisplayName;
        public BattleSide Side;
        public int Slot, Row, Level, Hp, MaxHp, Mp, MaxMp, Tp, MaxTp, Shield, MaxShield;
        public bool Broken, Guarding, IsAlive, IsBoss, Summoned;
        public IReadOnlyList<StatusSnapshot> Statuses;
        /// <summary>Weakness elements the player knows (enemies only).</summary>
        public IReadOnlyList<int> KnownWeaknesses;
    }
}
