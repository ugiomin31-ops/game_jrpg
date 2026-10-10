using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Battle;
using Abyss.Runtime.Art;
using UnityEngine;

namespace Abyss.Runtime.Battle
{
    /// <summary>Presentation-owned state. Only chronological event values may change these gauges.</summary>
    public sealed class BattleDisplayUnit
    {
        public string Id, DefId, Name;
        /// <summary>Data name without the display letter, and the letter itself ("" when the name is unique).</summary>
        public string BaseName, Suffix = "";
        public BattleSide Side;
        public int Slot, Row, Hp, MaxHp, Mp, MaxMp, Tp, MaxTp, Shield, MaxShield;
        public int ArenaLane;
        public bool Alive, Broken, Guarding, Boss;
        public CharacterModel Model;
        public Vector3 Home;
        public Quaternion Facing;
        /// <summary>Hit recoil: seconds left and peak push (metres) away from the opponents' side.</summary>
        public float KnockTime, KnockAmount;
        public readonly Dictionary<string, DisplayStatus> Statuses = new Dictionary<string, DisplayStatus>();
        public readonly List<int> Weaknesses = new List<int>();
        // These values deliberately do NOT come from UnitSnapshot / Engine. Apply() at TurnEnd must not
        // erase a charge that survived a skipped turn or replace intents with a future round's plans.
        public readonly SortedDictionary<int, EnemyIntent> Intents = new SortedDictionary<int, EnemyIntent>();
        public PendingCharge DisplayCharge;

        public void Plan(EnemyIntent intent) => Intents[intent.Slot] = intent;
        public void ClearIntent(int slot) => Intents.Remove(slot);
        public void StartCharge(string skillId, string targetId, int round, Scope scope)
            => DisplayCharge = new PendingCharge(skillId, targetId, round, scope);
        public void ClearCharge() => DisplayCharge = null;
        public void ClearWarnings() { Intents.Clear(); ClearCharge(); }
        public void CancelCharge()
        {
            ClearCharge();
            // The following IntentCleared is idempotent. Do not keep showing a cancelled release during
            // the interruption call-out's wait, or remove the enemy's unrelated remaining slots.
            var releases = new List<int>();
            foreach (var pair in Intents) if (pair.Value.IsChargeRelease) releases.Add(pair.Key);
            foreach (int slot in releases) Intents.Remove(slot);
        }

        /// <summary>Pending/charge warnings take precedence; otherwise the next unconsumed slot.</summary>
        public EnemyIntent LeadingIntent
        {
            get
            {
                EnemyIntent next = null;
                foreach (var intent in Intents.Values)
                {
                    if (next == null) next = intent;
                    if (intent.IsChargeAnnounce || intent.IsChargeRelease) return intent;
                }
                return next;
            }
        }

        public void Apply(UnitSnapshot s)
        {
            Id = s.Id; DefId = s.DefId; Name = s.DisplayName; BaseName = s.BaseName ?? s.DisplayName; Suffix = s.LabelSuffix ?? ""; Side = s.Side; Slot = s.Slot; Row = s.Row;
            Hp = s.Hp; MaxHp = s.MaxHp; Mp = s.Mp; MaxMp = s.MaxMp; Tp = s.Tp; MaxTp = s.MaxTp;
            Shield = s.Shield; MaxShield = s.MaxShield; Alive = s.IsAlive; Broken = s.Broken;
            Guarding = s.Guarding; Boss = s.IsBoss;
            Statuses.Clear();
            if (s.Statuses != null) foreach (var status in s.Statuses)
                Statuses.Add(status.Id, new DisplayStatus { Id = status.Id, Name = status.DisplayName,
                    Turns = status.Turns, Beneficial = status.Beneficial, Type = status.EffectType });
            Weaknesses.Clear();
            if (s.KnownWeaknesses != null) Weaknesses.AddRange(s.KnownWeaknesses);
        }
    }

    public sealed class DisplayStatus
    {
        public string Id, Name;
        public int Turns;
        public bool Beneficial;
        public StatusEffectType Type;
    }
}
