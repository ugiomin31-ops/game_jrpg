// Port of scripts/core/enemy_stats.gd: difficulty (CONTENT_DESIGN §1.5) and FOE power scaling,
// applied exactly once when an enemy unit is built.
using System;

namespace Abyss.Logic.Battle
{
    /// <summary>Per-difficulty multipliers.</summary>
    public readonly struct DifficultyScale
    {
        public readonly double Hp, Attack, Magic, Xp, Gold;
        public DifficultyScale(double hp, double attack, double magic, double xp, double gold)
        { Hp = hp; Attack = attack; Magic = magic; Xp = xp; Gold = gold; }
    }

    /// <summary>Scaled numbers of one enemy for a battle.</summary>
    public readonly struct EnemyBuild
    {
        public readonly int MaxHp, Attack, Magic, ExperienceReward, GoldReward;
        public EnemyBuild(int maxHp, int attack, int magic, int xp, int gold)
        { MaxHp = maxHp; Attack = attack; Magic = magic; ExperienceReward = xp; GoldReward = gold; }
    }

    /// <summary>Enemy difficulty / FOE scaling.</summary>
    public static class EnemyStats
    {
        public const double DefaultCrit = 0.05;
        public const double DefaultCritMultiplier = 1.5;

        /// <summary>Multipliers for a difficulty; hard bosses use the per-kind override (HP 1.2, ATK/MAG 1.1).</summary>
        public static DifficultyScale ScalesFor(Difficulty difficulty, bool isBoss)
        {
            switch (difficulty)
            {
                case Difficulty.Easy: return new DifficultyScale(0.75, 0.8, 0.8, 1.2, 1.0);
                case Difficulty.Hard:
                    return isBoss ? new DifficultyScale(1.2, 1.1, 1.1, 1.1, 1.2) : new DifficultyScale(1.35, 1.2, 1.2, 1.1, 1.2);
                default: return new DifficultyScale(1.0, 1.0, 1.0, 1.0, 1.0);
            }
        }

        /// <summary>Non-positive / NaN power counts as 1.</summary>
        public static double SanitizePower(double power) => power > 0.0 && !double.IsNaN(power) && !double.IsInfinity(power) ? power : 1.0;

        /// <summary>FOE threat multiplier of a battle: the setup's FoePower for FOE battles, else 1.</summary>
        public static double EncounterPower(BattleSetup setup)
            => setup.Kind == BattleKind.Foe ? SanitizePower(Gd.D(setup.FoePower)) : 1.0;

        /// <summary>
        /// Scaled stats: max HP / ATK / MAG x difficulty x power, XP / gold x difficulty x (1 + power) / 2.
        /// </summary>
        public static EnemyBuild Build(EnemyDef def, Difficulty difficulty, double power = 1.0)
        {
            var scale = ScalesFor(difficulty, def.IsBoss || def.Rank == 2);
            power = SanitizePower(power);
            double rewardScale = (1.0 + power) / 2.0;
            int maxHp = Math.Max(1, Gd.RoundI(def.MaxHp * scale.Hp * power));
            int attack = Math.Max(1, Gd.RoundI(def.Attack * scale.Attack * power));
            int magic = Math.Max(0, Gd.RoundI(def.Magic * scale.Magic * power));
            int xp = Math.Max(0, Gd.RoundI(def.ExperienceReward * scale.Xp * rewardScale));
            int gold = Math.Max(0, Gd.RoundI(def.GoldReward * scale.Gold * rewardScale));
            return new EnemyBuild(maxHp, attack, magic, xp, gold);
        }
    }
}
