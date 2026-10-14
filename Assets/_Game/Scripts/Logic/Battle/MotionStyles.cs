using System;
using System.Collections.Generic;

namespace Abyss.Logic.Battle
{
    /// <summary>How a monster closes in for a melee strike (staged by BattleView; the battle rules never read it).</summary>
    public enum EnemyMove
    {
        /// <summary>The plain run / pounce-arc dash to the strike mark.</summary>
        Dash,
        /// <summary>Crouch, then a high leap that lands on the target with the strike.</summary>
        Pounce,
        /// <summary>Head-down rush that overshoots the mark and skids back.</summary>
        Charge,
        /// <summary>Jumps high over the target and body-slams down (ground shock).</summary>
        Slam,
        /// <summary>Flyers: climb, then dive along a curve onto the target.</summary>
        Swoop,
        /// <summary>Spirits: fade out, reappear beside the target, strike, fade back home.</summary>
        Blink,
        /// <summary>Sinks into the floor, travels unseen and erupts under the target.</summary>
        Burrow,
        /// <summary>Blobs / small plants: a series of shrinking hops ending on the target.</summary>
        Bounce,
        /// <summary>Insects / small beasts: a fast side-to-side skitter.</summary>
        Zigzag,
        /// <summary>Dashes in and spins through a full turn as it strikes.</summary>
        Spin,
    }

    /// <summary>Body motion a monster adds to a stationary cast (breath, roar, spell).</summary>
    public enum CastFlourish { None, Rear, Hover, Stomp }

    /// <summary>Movement family of a monster model, from which its default moves come.</summary>
    public enum BodyFamily { Brute, Beast, Heavy, Serpent, Flyer, Blob, Plant, Spirit, Insect }

    /// <summary>Extra body motion BattleView adds around a hero take.</summary>
    public enum HeroFlourish { None, Leap, Spin, Backstep, Levitate, Dash }

    /// <summary>The takes and flourish a hero action is staged with. <see cref="Combo"/> lists the takes of later strike waves.</summary>
    public sealed class HeroMotionPlan
    {
        public string Take = "Attack";
        public HeroFlourish Flourish;
        public IReadOnlyList<string> Combo = Array.Empty<string>();
    }

    /// <summary>
    /// Presentation-only choice of motion styles, so the same monster or hunter does not repeat one swing all battle. Pure and
    /// deterministic (ids, data fields and a per-unit use counter in, a style out); BattleView stages the result and falls back
    /// to the plain take when a model lacks one.
    /// </summary>
    public static class MotionStyles
    {
        static readonly Dictionary<string, BodyFamily> Families = new Dictionary<string, BodyFamily>(StringComparer.Ordinal)
        {
            // Four-legged hunters and other pouncers.
            { "ice_wolf", BodyFamily.Beast }, { "hellhound", BodyFamily.Beast }, { "horned_rabbit", BodyFamily.Beast },
            { "sewer_rat", BodyFamily.Beast }, { "shadow_beast", BodyFamily.Beast }, { "nightmare", BodyFamily.Beast },
            { "cave_mole", BodyFamily.Beast }, { "fire_drake", BodyFamily.Beast }, { "flame_sphinx", BodyFamily.Beast },
            { "mimic", BodyFamily.Beast }, { "lizardman", BodyFamily.Beast },
            // Heavy bodies: golems, shells, constructs, titans.
            { "ice_golem", BodyFamily.Heavy }, { "sand_golem", BodyFamily.Heavy }, { "scrap_bot", BodyFamily.Heavy },
            { "rhino_beetle", BodyFamily.Heavy }, { "crystal_horror", BodyFamily.Heavy }, { "turtle_titan", BodyFamily.Heavy },
            { "giant_clam", BodyFamily.Heavy }, { "coral_crab", BodyFamily.Heavy }, { "scrap_colossus", BodyFamily.Heavy },
            { "yeti", BodyFamily.Heavy }, { "temple_guardian", BodyFamily.Heavy }, { "forest_guardian", BodyFamily.Heavy },
            // Serpents and worms.
            { "sea_serpent", BodyFamily.Serpent }, { "abyss_worm", BodyFamily.Serpent }, { "leviathan", BodyFamily.Serpent },
            { "naga_priestess", BodyFamily.Serpent }, { "frost_kraken", BodyFamily.Serpent },
            // Small plants that hop.
            { "mushroom", BodyFamily.Plant }, { "sprout", BodyFamily.Plant }, { "mandragora", BodyFamily.Plant },
            // Spirits and casters that drift rather than walk.
            { "ghost", BodyFamily.Spirit }, { "wisp", BodyFamily.Spirit }, { "lich", BodyFamily.Spirit },
            { "void_eye", BodyFamily.Spirit }, { "plague_lich", BodyFamily.Spirit }, { "abyss_herald", BodyFamily.Spirit },
            { "void_reaper", BodyFamily.Spirit }, { "mummy_pup", BodyFamily.Spirit }, { "jellyfish", BodyFamily.Spirit },
            { "doppelganger", BodyFamily.Spirit }, { "boss", BodyFamily.Spirit }, { "abyss_lord", BodyFamily.Spirit },
            // Insects and arachnids.
            { "frost_spider", BodyFamily.Insect }, { "sand_scorpion", BodyFamily.Insect }, { "killer_bee", BodyFamily.Insect },
        };

        /// <summary>Movement family of a model id; unlisted models follow their archetype (flyer, blob) or walk as brutes.</summary>
        public static BodyFamily FamilyOf(string modelId, string archetype)
        {
            if (modelId != null && Families.TryGetValue(modelId, out var family)) return family;
            switch (archetype)
            {
                case "flyer": return BodyFamily.Flyer;
                case "blob": return BodyFamily.Blob;
                default: return BodyFamily.Brute;
            }
        }

        static bool Has(string id, params string[] words)
        {
            if (string.IsNullOrEmpty(id)) return false;
            foreach (string word in words) if (id.IndexOf(word, StringComparison.Ordinal) >= 0) return true;
            return false;
        }

        static readonly EnemyMove[] BeastMoves = { EnemyMove.Pounce, EnemyMove.Dash, EnemyMove.Zigzag };
        static readonly EnemyMove[] BruteMoves = { EnemyMove.Dash, EnemyMove.Charge, EnemyMove.Dash, EnemyMove.Spin };
        static readonly EnemyMove[] HeavyMoves = { EnemyMove.Charge, EnemyMove.Slam };
        static readonly EnemyMove[] SerpentMoves = { EnemyMove.Burrow, EnemyMove.Dash };
        static readonly EnemyMove[] FlyerMoves = { EnemyMove.Swoop, EnemyMove.Dash };
        static readonly EnemyMove[] BlobMoves = { EnemyMove.Bounce };
        static readonly EnemyMove[] PlantMoves = { EnemyMove.Bounce, EnemyMove.Dash };
        static readonly EnemyMove[] SpiritMoves = { EnemyMove.Blink, EnemyMove.Swoop };
        static readonly EnemyMove[] InsectMoves = { EnemyMove.Zigzag, EnemyMove.Pounce };

        static EnemyMove[] Rotation(BodyFamily family)
        {
            switch (family)
            {
                case BodyFamily.Beast: return BeastMoves;
                case BodyFamily.Heavy: return HeavyMoves;
                case BodyFamily.Serpent: return SerpentMoves;
                case BodyFamily.Flyer: return FlyerMoves;
                case BodyFamily.Blob: return BlobMoves;
                case BodyFamily.Plant: return PlantMoves;
                case BodyFamily.Spirit: return SpiritMoves;
                case BodyFamily.Insect: return InsectMoves;
                default: return BruteMoves;
            }
        }

        /// <summary>
        /// How a monster closes in for a melee action. Skill names pick a fitting move (a burrow strike burrows, a crash
        /// slams, a sweep spins); everything else cycles through the family's moves with <paramref name="useIndex"/>
        /// (the unit's count of melee actions so far), so consecutive basic attacks differ.
        /// </summary>
        public static EnemyMove EnemyApproach(string modelId, string archetype, bool boss, string skillId, int useIndex)
        {
            var family = FamilyOf(modelId, archetype);
            bool flying = family == BodyFamily.Flyer || family == BodyFamily.Spirit;
            if (Has(skillId, "burrow")) return EnemyMove.Burrow;
            if (Has(skillId, "dive", "black_wings", "feather")) return flying ? EnemyMove.Swoop : EnemyMove.Pounce;
            if (Has(skillId, "trample", "charge", "rush", "anchor")) return EnemyMove.Charge;
            if (Has(skillId, "titan_crash", "crash", "slam", "quake", "smash", "stunning"))
                return flying ? EnemyMove.Swoop : boss ? EnemyMove.Charge : EnemyMove.Slam;
            if (Has(skillId, "sweep", "cleave", "reap", "scythe", "flail", "whirl", "tail")) return EnemyMove.Spin;
            if (Has(skillId, "mirror", "death_mark", "shadow_bite", "void_blade", "fallen_blade"))
                return flying || family == BodyFamily.Spirit ? EnemyMove.Blink : EnemyMove.Zigzag;
            if (Has(skillId, "pounce")) return flying ? EnemyMove.Swoop : boss ? EnemyMove.Charge : EnemyMove.Pounce;
            if (Has(skillId, "bite", "fang", "devour", "clamp", "maul", "constrict"))
                return family == BodyFamily.Blob ? EnemyMove.Bounce : family == BodyFamily.Serpent ? EnemyMove.Dash
                    : flying ? EnemyMove.Swoop : EnemyMove.Pounce;
            if (Has(skillId, "bleed_edge", "venom")) return family == BodyFamily.Beast || family == BodyFamily.Insect ? EnemyMove.Zigzag : EnemyMove.Dash;
            if (Has(skillId, "strong_attack")) return family == BodyFamily.Beast ? EnemyMove.Pounce : flying ? EnemyMove.Swoop
                : family == BodyFamily.Blob || family == BodyFamily.Plant ? EnemyMove.Bounce : EnemyMove.Slam;
            var moves = Rotation(family);
            // Big bosses keep their footing: no hopping or skittering across the arena.
            var move = moves[Math.Abs(useIndex) % moves.Length];
            if (boss && (move == EnemyMove.Bounce || move == EnemyMove.Zigzag || move == EnemyMove.Pounce)) return EnemyMove.Charge;
            return move;
        }

        /// <summary>Body motion over a monster's stationary cast: rear back for breaths and roars, stamp for quakes, hover for spirits.</summary>
        public static CastFlourish EnemyCast(string modelId, string archetype, string skillId)
        {
            var family = FamilyOf(modelId, archetype);
            if (Has(skillId, "quake", "sandstorm", "shell", "stone", "harden", "crystal", "iron_wall", "titan")) return CastFlourish.Stomp;
            if (Has(skillId, "breath", "roar", "screech", "howl", "war_cry", "spit", "jet", "tide", "wave", "lure", "spike", "inferno", "flare"))
                return family == BodyFamily.Flyer || family == BodyFamily.Spirit ? CastFlourish.Hover : CastFlourish.Rear;
            switch (family)
            {
                case BodyFamily.Flyer: case BodyFamily.Spirit: return CastFlourish.Hover;
                case BodyFamily.Blob: case BodyFamily.Heavy: return CastFlourish.Stomp;
                default: return CastFlourish.Rear;
            }
        }

        static readonly string[] MeleeBasic = { "Attack", "Slash", "Attack", "Thrust" };
        static readonly string[] ComboAfterSlash = { "Thrust", "Attack", "Slash" };
        static readonly string[] ComboAfterThrust = { "Slash", "Attack", "Thrust" };
        static readonly string[] ComboAfterAttack = { "Slash", "Thrust", "Attack" };
        static readonly string[] ComboAfterSmash = { "Slash", "Smash" };

        /// <summary>
        /// Takes and flourish of a hero action. <paramref name="actorAction"/> / <paramref name="approach"/> come from the
        /// action's presentation (null for a basic attack); <paramref name="melee"/> is true when the hero closes in.
        /// Take names are the shared authored ones (Slash, Thrust, Smash, Spin, Spell, Channel, Rally, Kneel, Throw);
        /// BattleView keeps a class / hero take of the original name where the model ships one.
        /// </summary>
        public static HeroMotionPlan Hero(string classId, ActionKind kind, string skillId, string actorAction, bool melee,
            bool targetsAllies, int hitCount, int tier, int useIndex)
        {
            var plan = new HeroMotionPlan();
            if (kind == ActionKind.Item) { plan.Take = "Throw"; return plan; }
            if (kind == ActionKind.Attack)
            {
                plan.Take = melee ? MeleeBasic[Math.Abs(useIndex) % MeleeBasic.Length] : "Attack";
                // A mace or staff does not stab: clerics alternate their swing with the sweep.
                if (classId == "cleric" && plan.Take == "Thrust") plan.Take = "Slash";
                return plan;
            }
            if (kind != ActionKind.Skill) return plan;
            if (!melee)
            {
                if (targetsAllies || actorAction == "cast" && Has(skillId, "cry", "rally", "banner", "provoke", "overlord", "berserk",
                        "frenzy", "blood_thirst", "reckless", "war", "vow", "fortress", "iron_wall", "aegis", "conquer"))
                {
                    plan.Take = Has(skillId, "revive", "resurrection", "rebirth", "miracle", "full_heal") ? "Kneel"
                        : Has(skillId, "cry", "rally", "banner", "provoke", "overlord", "berserk", "frenzy", "blood_thirst", "reckless",
                            "war", "vow", "fortress", "iron_wall", "aegis", "conquer") ? "Rally" : "Channel";
                    return plan;
                }
                if (actorAction == "shoot" || classId == "archer")
                {
                    plan.Take = "Attack";
                    if (Has(skillId, "quick_draw", "wind_step", "gale", "snare", "flash", "disarm", "suppress", "step", "raid"))
                        plan.Flourish = HeroFlourish.Backstep;
                    return plan;
                }
                plan.Take = "Spell";
                if (classId == "mage" && tier >= 3) plan.Flourish = HeroFlourish.Levitate;
                return plan;
            }
            if (Has(skillId, "whirl", "cyclone", "rampage", "tornado", "spin", "round", "gale_dance", "storm"))
            { plan.Take = "Spin"; plan.Flourish = HeroFlourish.Spin; plan.Combo = ComboAfterSlash; }
            else if (Has(skillId, "crash", "smash", "slam", "quake", "earth", "titan", "giga", "cataclysm", "skull", "split", "judgment",
                         "ragnarok", "rend", "meteor", "grand_cross", "holy_smite", "shield_bash", "rampart", "power_break", "crush", "execution", "hammer"))
            { plan.Take = "Smash"; plan.Flourish = HeroFlourish.Leap; plan.Combo = ComboAfterSmash; }
            else if (Has(skillId, "thrust", "lance", "pierce", "stab", "assassinate", "fang", "raid", "lunge", "spear", "armor_break"))
            { plan.Take = "Thrust"; plan.Flourish = HeroFlourish.Dash; plan.Combo = ComboAfterThrust; }
            else if (Has(skillId, "twin", "double", "crimson", "fury", "combo", "flurry", "dance", "bleed"))
            { plan.Take = "Slash"; plan.Combo = ComboAfterSlash; }
            else if (Has(skillId, "slash", "cleave", "blade", "edge", "cut", "strike"))
            { plan.Take = "Slash"; plan.Combo = ComboAfterSlash; }
            else
            {
                plan.Take = Math.Abs(useIndex) % 2 == 0 ? "Slash" : "Thrust";
                plan.Combo = plan.Take == "Slash" ? ComboAfterSlash : ComboAfterThrust;
            }
            if (hitCount <= 1) plan.Combo = Array.Empty<string>();
            return plan;
        }

        /// <summary>Take of the <paramref name="wave"/>-th strike (1-based) of a hero action: the plan's take, then its combo in turn.</summary>
        public static string WaveTake(HeroMotionPlan plan, int wave)
        {
            if (plan == null) return "Attack";
            if (wave <= 1 || plan.Combo.Count == 0) return plan.Take;
            return plan.Combo[(wave - 2) % plan.Combo.Count];
        }
    }
}
