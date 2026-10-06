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

        public void Apply(UnitSnapshot s)
        {
            Id = s.Id; DefId = s.DefId; Name = s.DisplayName; Side = s.Side; Slot = s.Slot; Row = s.Row;
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
