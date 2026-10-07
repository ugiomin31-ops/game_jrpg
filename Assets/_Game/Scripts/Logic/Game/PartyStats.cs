// Hero stat building, levelling and post-battle processing (port of party_stats.gd and the
// reward/snapshot half of game_state.gd). CONTENT_DESIGN §1.1, §2.
using System;
using System.Collections.Generic;
using System.Globalization;

namespace Abyss.Logic.Game
{
    /// <summary>The seven integer combat stats.</summary>
    public struct StatBlock
    {
        public int MaxHp, MaxMp, Attack, Magic, Defense, Resistance, Speed;

        public static StatBlock operator +(StatBlock a, StatBlock b) => new StatBlock
        {
            MaxHp = a.MaxHp + b.MaxHp, MaxMp = a.MaxMp + b.MaxMp, Attack = a.Attack + b.Attack, Magic = a.Magic + b.Magic,
            Defense = a.Defense + b.Defense, Resistance = a.Resistance + b.Resistance, Speed = a.Speed + b.Speed,
        };

        public static StatBlock operator -(StatBlock a, StatBlock b) => new StatBlock
        {
            MaxHp = a.MaxHp - b.MaxHp, MaxMp = a.MaxMp - b.MaxMp, Attack = a.Attack - b.Attack, Magic = a.Magic - b.Magic,
            Defense = a.Defense - b.Defense, Resistance = a.Resistance - b.Resistance, Speed = a.Speed - b.Speed,
        };
    }

    /// <summary>Effective stats of a hero (level growth + equipment), as shown in menus and used in battle.</summary>
    public sealed class HeroStats
    {
        public StatBlock Stats;
        public float Hit, Evade, Crit;
        public List<int> ElementResists = new List<int>();
        public List<string> StatusImmunities = new List<string>();
        public int MaxHp => Stats.MaxHp;
        public int MaxMp => Stats.MaxMp;
    }

    /// <summary>One hero's level-up after a battle.</summary>
    public sealed class LevelUpReport
    {
        public string HeroId;
        public int OldLevel, NewLevel;
        /// <summary>Effective stat gain (new - old).</summary>
        public StatBlock StatDeltas;
        /// <summary>Skill ids learned by this level-up, in learn order.</summary>
        public List<string> NewSkills = new List<string>();
    }

    /// <summary>Change of one accepted quest's progress.</summary>
    public sealed class QuestUpdate
    {
        public string QuestId;
        public int OldProgress, NewProgress;
        /// <summary>True when this update turned the quest complete (claimable at the Guild).</summary>
        public bool Completed;
    }

    /// <summary>Everything <see cref="PartyStats.ApplyBattleOutcome"/> changed, for the result screen.</summary>
    public sealed class BattleReport
    {
        public BattleResult Result;
        public int Experience, Gold;
        public Dictionary<string, int> Drops = new Dictionary<string, int>();
        public List<LevelUpReport> LevelUps = new List<LevelUpReport>();
        public List<QuestUpdate> QuestUpdates = new List<QuestUpdate>();
        /// <summary>Enemy ids seen for the first time.</summary>
        public List<string> NewBestiaryEntries = new List<string>();
        /// <summary>"enemyId:element" weaknesses recorded for the first time.</summary>
        public List<string> NewWeaknesses = new List<string>();
    }

    /// <summary>Environmental trap changes, for field damage and poison presentation.</summary>
    public sealed class TrapReport
    {
        public Dictionary<string, int> Damage = new Dictionary<string, int>();
        public List<string> Poisoned = new List<string>();
    }

    /// <summary>Hero stats, skills, equipment and battle bookkeeping.</summary>
    public static class PartyStats
    {
        /// <summary>XP needed to go from <paramref name="level"/> to the next: round(30 × L^1.75) + 25 (§1.1).</summary>
        public static int XpToNext(int level) => RoundI(30.0 * Math.Pow(Math.Max(1, level), 1.75)) + 25;

        /// <summary>Total XP needed to reach <paramref name="level"/> from Lv1.</summary>
        public static int CumulativeXp(int level)
        {
            int total = 0;
            for (int l = 1; l < Math.Min(level, GameState.LevelCap); l++) total += XpToNext(l);
            return total;
        }

        /// <summary>Equipment class restriction: empty Classes = every hero.</summary>
        public static bool AllowsClass(EquipmentDef piece, string heroId) => piece.Classes == null || piece.Classes.Count == 0 || piece.Classes.Contains(heroId);

        /// <summary>
        /// Equipment job restriction: empty Jobs = any job; otherwise the hero's current job or a job it was promoted
        /// from must be listed (a knight's sword stays usable as a paladin; a paladin's sword is not usable as a knight).
        /// </summary>
        public static bool AllowsJob(GameDB db, EquipmentDef piece, HeroState hero)
        {
            if (piece.Jobs == null || piece.Jobs.Count == 0) return true;
            foreach (string job in JobPath(db, hero)) if (piece.Jobs.Contains(job)) return true;
            return false;
        }

        /// <summary>Class and job restriction together.</summary>
        public static bool AllowsHero(GameDB db, EquipmentDef piece, HeroState hero) => AllowsClass(piece, hero.Id) && AllowsJob(db, piece, hero);

        /// <summary>The hero's current job row, or null when jobs.json has no row for it (stats then use the plain hero).</summary>
        public static JobDef JobOf(GameDB db, HeroState hero)
        {
            string id = string.IsNullOrEmpty(hero.Job) ? hero.Id : hero.Job;
            return db.Jobs.TryGetValue(id, out var job) && job.Hero == hero.Id ? job : null;
        }

        /// <summary>Job ids from the base job down to <paramref name="jobId"/> (e.g. cleric, priest, saint).</summary>
        public static List<string> JobPath(GameDB db, string heroId, string jobId)
        {
            var path = new List<string>();
            string id = string.IsNullOrEmpty(jobId) ? heroId : jobId;
            while (!string.IsNullOrEmpty(id) && db.Jobs.TryGetValue(id, out var job) && job.Hero == heroId && !path.Contains(id))
            {
                path.Insert(0, id);
                id = job.Parent;
            }
            if (path.Count == 0 || path[0] != heroId) path.Insert(0, heroId);
            return path;
        }

        /// <summary>Job path of the hero's current job.</summary>
        public static List<string> JobPath(GameDB db, HeroState hero) => JobPath(db, hero.Id, hero.Job);

        /// <summary>Display name of the hero's current job (the hero's own name for a missing job row).</summary>
        public static string JobName(GameDB db, HeroState hero) => JobOf(db, hero)?.DisplayName ?? (db.Heroes.TryGetValue(hero.Id, out var def) ? def.DisplayName : hero.Id);

        /// <summary>True once the hero has left the base job.</summary>
        public static bool IsPromoted(HeroState hero) => !string.IsNullOrEmpty(hero.Job) && hero.Job != hero.Id;

        /// <summary>Level stats with the job multipliers applied (no equipment).</summary>
        public static StatBlock JobLevelStats(HeroDef hero, JobDef job, int level)
        {
            var stats = LevelStats(hero, level);
            if (job == null) return stats;
            return new StatBlock
            {
                MaxHp = Math.Max(1, RoundI(stats.MaxHp * D(job.HpMult))),
                MaxMp = Math.Max(0, RoundI(stats.MaxMp * D(job.MpMult))),
                Attack = Math.Max(1, RoundI(stats.Attack * D(job.AtkMult))),
                Magic = Math.Max(0, RoundI(stats.Magic * D(job.MagMult))),
                Defense = Math.Max(0, RoundI(stats.Defense * D(job.DefMult))),
                Resistance = Math.Max(0, RoundI(stats.Resistance * D(job.ResMult))),
                Speed = Math.Max(1, RoundI(stats.Speed * D(job.SpdMult))),
            };
        }

        /// <summary>Level stats of the hero in its current job (no equipment); the party menu's "기본" column.</summary>
        public static StatBlock BaseStats(GameDB db, HeroState hero) => JobLevelStats(db.Heroes[hero.Id], JobOf(db, hero), hero.Level);

        /// <summary>Level stats without equipment: round(base + growth × (L − 1)) (§1.1).</summary>
        public static StatBlock LevelStats(HeroDef hero, int level)
        {
            int steps = Math.Max(0, Math.Min(GameState.LevelCap, Math.Max(1, level)) - 1);
            return new StatBlock
            {
                MaxHp = Math.Max(1, RoundI(hero.MaxHp + D(hero.HpGrowth) * steps)),
                MaxMp = Math.Max(0, RoundI(hero.MaxMp + D(hero.MpGrowth) * steps)),
                Attack = Math.Max(1, RoundI(hero.Attack + D(hero.AtkGrowth) * steps)),
                Magic = Math.Max(0, RoundI(hero.Magic + D(hero.MagGrowth) * steps)),
                Defense = Math.Max(0, RoundI(hero.Defense + D(hero.DefGrowth) * steps)),
                Resistance = Math.Max(0, RoundI(hero.Resistance + D(hero.ResGrowth) * steps)),
                Speed = Math.Max(1, RoundI(hero.Speed + D(hero.SpdGrowth) * steps)),
            };
        }

        /// <summary>Effective stats of a hero state (unknown equipment ids are ignored).</summary>
        public static HeroStats EffectiveStats(GameDB db, HeroState hero)
        {
            var def = db.Heroes[hero.Id];
            var job = JobOf(db, hero);
            var stats = JobLevelStats(def, job, hero.Level);
            double hit = D(def.Hit), evade = D(def.Evade), crit = D(def.Crit);
            if (job != null) { hit += D(job.Hit); evade += D(job.Evade); crit += D(job.Crit); }
            var output = new HeroStats();
            foreach (string slot in GameState.EquipSlots)
            {
                if (!db.Equipment.TryGetValue(hero.Equipped(slot), out var piece)) continue;
                stats += new StatBlock { MaxHp = piece.Hp, MaxMp = piece.Mp, Attack = piece.Atk, Magic = piece.Mag, Defense = piece.Def, Resistance = piece.Res, Speed = piece.Spd };
                hit += D(piece.Hit);
                evade += D(piece.Evade);
                crit += D(piece.Crit);
                foreach (int element in piece.ElementResists) if (!output.ElementResists.Contains(element)) output.ElementResists.Add(element);
                foreach (string status in piece.StatusImmunities) if (!output.StatusImmunities.Contains(status)) output.StatusImmunities.Add(status);
            }
            stats.MaxHp = Math.Max(1, stats.MaxHp);
            stats.MaxMp = Math.Max(0, stats.MaxMp);
            stats.Attack = Math.Max(1, stats.Attack);
            stats.Speed = Math.Max(1, stats.Speed);
            stats.Magic = Math.Max(0, stats.Magic);
            stats.Defense = Math.Max(0, stats.Defense);
            stats.Resistance = Math.Max(0, stats.Resistance);
            output.Stats = stats;
            output.Hit = (float)Clamp(hit, 0, 1);
            output.Evade = (float)Clamp(evade, 0, 0.95);
            output.Crit = (float)Clamp(crit, 0, 1);
            return output;
        }

        /// <summary>Pure equip/unequip preview. Uses the same clamps, resistances and immunities as battle stats.</summary>
        public static HeroStats PreviewEquipment(GameDB db, HeroState hero, string slot, string equipmentId)
        {
            if (Array.IndexOf(GameState.EquipSlots, slot) < 0) throw new ArgumentException("Unknown equipment slot", nameof(slot));
            if (!string.IsNullOrEmpty(equipmentId) && (!db.Equipment.TryGetValue(equipmentId, out var piece)
                || piece.Slot != slot || !AllowsHero(db, piece, hero))) throw new ArgumentException("Incompatible equipment", nameof(equipmentId));
            var preview = new HeroState { Id = hero.Id, Job = hero.Job, Level = hero.Level, Equipment = new Dictionary<string, string>(hero.Equipment) };
            preview.Equipment[slot] = equipmentId ?? "";
            return EffectiveStats(db, preview);
        }

        /// <summary>Effective stats by hero id.</summary>
        public static HeroStats EffectiveStats(GameDB db, GameState state, string heroId) => EffectiveStats(db, state.Hero(heroId));

        /// <summary>Lv1 skills (incl. basic_attack) followed by learnset skills with level ≤ <paramref name="level"/>, unique, in learn order.</summary>
        public static List<string> SkillsForLevel(HeroDef hero, int level)
        {
            var output = new List<string>();
            foreach (string s in hero.Skills) if (!output.Contains(s)) output.Add(s);
            var rows = new List<LearnEntry>(hero.Learnset);
            rows.Sort((a, b) => a.Level.CompareTo(b.Level)); // List.Sort is unstable; learnsets have one skill per level row anyway
            foreach (var row in rows) if (row.Level <= level && !string.IsNullOrEmpty(row.Skill) && !output.Contains(row.Skill)) output.Add(row.Skill);
            return output;
        }

        /// <summary>
        /// Usable skills of a hero in a job: the hero's own skills by level (<see cref="SkillsForLevel"/>), then the
        /// learnset of every job on the path base -> <paramref name="jobId"/> with level ≤ <paramref name="level"/>.
        /// Learn rule: job learnsets use hero levels and are learned while the hero is that job or any job promoted
        /// from it. Promotion only moves down the tree, so a class change never removes a skill; promoting late
        /// grants every job skill up to the current level at once.
        /// </summary>
        public static List<string> SkillsFor(GameDB db, string heroId, string jobId, int level)
        {
            var output = SkillsForLevel(db.Heroes[heroId], level);
            foreach (string id in JobPath(db, heroId, jobId))
            {
                if (id == heroId || !db.Jobs.TryGetValue(id, out var job)) continue;
                var rows = new List<LearnEntry>(job.Learnset);
                rows.Sort((a, b) => a.Level.CompareTo(b.Level));
                foreach (var row in rows) if (row.Level <= level && !string.IsNullOrEmpty(row.Skill) && !output.Contains(row.Skill)) output.Add(row.Skill);
            }
            return output;
        }

        /// <summary>Usable skills of a hero state (current job and level).</summary>
        public static List<string> SkillsFor(GameDB db, HeroState hero) => SkillsFor(db, hero.Id, hero.Job, hero.Level);

        /// <summary>Learnset entries (hero and current job path) with a level above the hero's current level (party menu "upcoming skills").</summary>
        public static List<LearnEntry> UpcomingSkills(GameDB db, HeroState hero)
        {
            var output = new List<LearnEntry>();
            foreach (var row in db.Heroes[hero.Id].Learnset) if (row.Level > hero.Level) output.Add(row);
            foreach (string id in JobPath(db, hero))
                if (id != hero.Id && db.Jobs.TryGetValue(id, out var job))
                    foreach (var row in job.Learnset) if (row.Level > hero.Level) output.Add(row);
            output.Sort((a, b) => a.Level.CompareTo(b.Level));
            return output;
        }

        /// <summary>Makes <see cref="HeroState.LearnedSkills"/> exactly the skills of the hero's job path and level. Returns ids newly added.</summary>
        public static List<string> SyncLearnedSkills(GameDB db, HeroState hero)
        {
            var target = SkillsFor(db, hero);
            var added = new List<string>();
            foreach (string s in target) if (!hero.LearnedSkills.Contains(s)) added.Add(s);
            hero.LearnedSkills = target;
            return added;
        }

        /// <summary>Battle-ready spec for one hero: effective stats, current vitals, learned skills (incl. ultimates), carried statuses.</summary>
        public static HeroCombatSpec BuildCombatSpec(GameDB db, GameState state, string heroId)
        {
            var hero = state.Hero(heroId) ?? throw new ArgumentException("Unknown hero " + heroId, nameof(heroId));
            var def = db.Heroes[heroId];
            var stats = EffectiveStats(db, hero);
            var spec = new HeroCombatSpec
            {
                HeroId = heroId,
                DisplayName = IsPromoted(hero) ? JobName(db, hero) : def.DisplayName,
                Level = hero.Level,
                MaxHp = stats.MaxHp,
                MaxMp = stats.MaxMp,
                Hp = Math.Max(0, Math.Min(stats.MaxHp, hero.Hp)),
                Mp = Math.Max(0, Math.Min(stats.MaxMp, hero.Mp)),
                Attack = stats.Stats.Attack,
                Magic = stats.Stats.Magic,
                Defense = stats.Stats.Defense,
                Resistance = stats.Stats.Resistance,
                Speed = stats.Stats.Speed,
                Hit = stats.Hit,
                Evade = stats.Evade,
                Crit = stats.Crit,
                Skills = SkillsFor(db, hero),
                ElementResists = new List<int>(stats.ElementResists),
                StatusImmunities = new List<string>(stats.StatusImmunities),
                WeaponId = hero.Equipped("weapon"),
                ArmorId = hero.Equipped("armor"),
                AccessoryId = hero.Equipped("accessory"),
                Row = db.HeroOrder.IndexOf(heroId) == 0 ? 0 : 1,
            };
            if (hero.Hp > 0)
                foreach (var kv in hero.Statuses) if (kv.Value > 0) spec.Statuses[kv.Key] = kv.Value;
            return spec;
        }

        /// <summary>
        /// Complete battle request: party specs, difficulty, consumables in the bag, known weaknesses.
        /// <paramref name="foePower"/> only matters for <see cref="BattleKind.Foe"/>.
        /// </summary>
        public static BattleSetup BuildBattleSetup(GameDB db, GameState state, BattleKind kind, IEnumerable<string> enemyGroup, float foePower, string floorId, int seed)
        {
            var setup = new BattleSetup
            {
                Kind = kind,
                Difficulty = state.Difficulty,
                EnemyGroup = new List<string>(enemyGroup),
                FoePower = kind == BattleKind.Foe ? foePower : 1f,
                FloorId = floorId,
                Seed = seed,
                KnownWeaknesses = state.KnownWeaknessKeys(),
            };
            foreach (var hero in state.Party) setup.Party.Add(BuildCombatSpec(db, state, hero.Id));
            foreach (var kv in state.Inventory)
                if (kv.Value > 0 && db.Items.TryGetValue(kv.Key, out var item) && item.ItemType != ItemType.Material)
                    setup.Inventory[kv.Key] = kv.Value;
            return setup;
        }

        /// <summary>Full HP/MP, revives KO'd heroes, clears statuses (inn, spring, defeat recovery).</summary>
        public static void RestoreParty(GameDB db, GameState state)
        {
            foreach (var hero in state.Party)
            {
                var stats = EffectiveStats(db, hero);
                hero.Hp = stats.MaxHp;
                hero.Mp = stats.MaxMp;
                hero.Statuses.Clear();
            }
        }

        /// <summary>Traps cannot KO; each standing hero rolls poison, respecting equipment immunity.</summary>
        public static TrapReport ApplyTrap(GameDB db, GameState state, Func<float> randomRoll, float damageRatio = 0.08f, float poisonChance = 0.30f)
        {
            if (randomRoll == null) throw new ArgumentNullException(nameof(randomRoll));
            var report = new TrapReport();
            StatusDef poison = null;
            foreach (var status in db.Statuses.Values)
                if (status.EffectType == StatusEffectType.Poison && (poison == null || string.CompareOrdinal(status.Id, poison.Id) < 0)) poison = status;
            string poisonId = poison == null || string.IsNullOrEmpty(poison.Id) ? "poison" : poison.Id;
            int turns = poison == null ? 3 : Math.Max(1, poison.DurationTurns);
            foreach (var hero in state.Party)
            {
                if (hero.Hp <= 0) continue;
                var stats = EffectiveStats(db, hero);
                int before = Math.Min(hero.Hp, stats.MaxHp);
                int damage = Math.Max(1, RoundI(stats.MaxHp * D(Math.Max(0f, damageRatio))));
                hero.Hp = Math.Max(1, before - damage);
                report.Damage[hero.Id] = before - hero.Hp;
                if (randomRoll() < poisonChance && !stats.StatusImmunities.Contains(poisonId))
                {
                    SetStatus(hero, poisonId, turns);
                    report.Poisoned.Add(hero.Id);
                }
            }
            return report;
        }

        /// <summary>
        /// Adds XP to one hero (no-op at the level cap). On level up, current HP/MP rise by the gained maximum
        /// (KO'd heroes stay at 0 HP) and new skills are learned. Returns null when the level did not change.
        /// </summary>
        public static LevelUpReport AwardXp(GameDB db, HeroState hero, int xp)
        {
            int from = Math.Max(1, Math.Min(GameState.LevelCap, hero.Level));
            if (from >= GameState.LevelCap) { hero.Xp = 0; return null; }
            int level = from;
            int current = Math.Max(0, hero.Xp) + Math.Max(0, xp);
            while (level < GameState.LevelCap && current >= XpToNext(level))
            {
                current -= XpToNext(level);
                level++;
            }
            if (level >= GameState.LevelCap) current = 0;
            var before = EffectiveStats(db, hero);
            hero.Level = level;
            hero.Xp = current;
            if (level == from) return null;
            var after = EffectiveStats(db, hero);
            if (hero.Hp > 0) hero.Hp = Math.Min(after.MaxHp, hero.Hp + Math.Max(0, after.MaxHp - before.MaxHp));
            hero.Mp = Math.Min(after.MaxMp, hero.Mp + Math.Max(0, after.MaxMp - before.MaxMp));
            return new LevelUpReport
            {
                HeroId = hero.Id,
                OldLevel = from,
                NewLevel = level,
                StatDeltas = after.Stats - before.Stats,
                NewSkills = SyncLearnedSkills(db, hero),
            };
        }

        /// <summary>
        /// Applies a finished battle to the campaign (any result): vitals/statuses, consumed items, bestiary
        /// (seen, kills, weaknesses). On victory also: win count, gold, drops, XP to every hero still standing
        /// (KO'd heroes get none; <see cref="BattleOutcome.Experience"/> is already difficulty/FOE scaled), and
        /// kill/foe/boss quest progress. Map consequences (FOE removal, cleared cells, boss flags) are
        /// <see cref="Dungeon.DungeonRun.ResolveBattle"/>'s job.
        /// </summary>
        public static BattleReport ApplyBattleOutcome(GameDB db, GameState state, BattleOutcome outcome)
        {
            var report = new BattleReport { Result = outcome.Result };
            foreach (var hero in state.Party)
            {
                var stats = EffectiveStats(db, hero);
                if (outcome.FinalHp.TryGetValue(hero.Id, out int hp)) hero.Hp = Math.Max(0, Math.Min(stats.MaxHp, hp));
                if (outcome.FinalMp.TryGetValue(hero.Id, out int mp)) hero.Mp = Math.Max(0, Math.Min(stats.MaxMp, mp));
                hero.Statuses.Clear();
                if (hero.Hp > 0 && outcome.FinalStatuses != null && outcome.FinalStatuses.TryGetValue(hero.Id, out var statuses))
                    foreach (var kv in statuses) if (kv.Value > 0 && !string.IsNullOrEmpty(kv.Key)) hero.Statuses[kv.Key] = kv.Value;
            }
            foreach (var kv in outcome.ItemsUsed) if (kv.Value > 0) state.RemoveItem(kv.Key, kv.Value);

            var seen = new List<string>();
            if (outcome.SeenEnemies != null) seen.AddRange(outcome.SeenEnemies);
            seen.AddRange(outcome.DefeatedEnemies);
            foreach (string enemyId in seen)
            {
                if (string.IsNullOrEmpty(enemyId)) continue;
                var entry = state.BestiaryOf(enemyId);
                if (!entry.Seen) { entry.Seen = true; report.NewBestiaryEntries.Add(enemyId); }
            }
            foreach (string enemyId in outcome.DefeatedEnemies) state.BestiaryOf(enemyId).Kills++;
            var weakSorted = new List<string>(outcome.DiscoveredWeaknesses);
            weakSorted.Sort(string.CompareOrdinal);
            foreach (string key in weakSorted)
            {
                int colon = key.LastIndexOf(':');
                if (colon <= 0 || !int.TryParse(key.Substring(colon + 1), NumberStyles.Integer, CultureInfo.InvariantCulture, out int element)) continue;
                var entry = state.BestiaryOf(key.Substring(0, colon));
                if (entry.WeakKnown.Contains(element)) continue;
                entry.WeakKnown.Add(element);
                entry.WeakKnown.Sort();
                report.NewWeaknesses.Add(key);
            }

            if (outcome.Result == BattleResult.Victory)
            {
                state.TotalWins++;
                report.Experience = Math.Max(0, outcome.Experience);
                report.Gold = Math.Max(0, outcome.Gold);
                state.Gold += report.Gold;
                foreach (var hero in state.Party)
                {
                    if (hero.Hp <= 0) continue;
                    var levelUp = AwardXp(db, hero, report.Experience);
                    if (levelUp != null) report.LevelUps.Add(levelUp);
                }
                foreach (var kv in outcome.Drops)
                {
                    if (kv.Value <= 0) continue;
                    state.AddContent(db, kv.Key, kv.Value);
                    report.Drops[kv.Key] = kv.Value;
                }
                foreach (string enemyId in outcome.DefeatedEnemies)
                {
                    QuestLog.Advance(db, state, QuestLog.KindKill, enemyId, 1, report.QuestUpdates);
                    if (!db.Enemies.TryGetValue(enemyId, out var enemy)) continue;
                    if (enemy.IsBoss) QuestLog.Advance(db, state, QuestLog.KindBoss, enemyId, 1, report.QuestUpdates);
                    if (enemy.Rank == 1) QuestLog.Advance(db, state, QuestLog.KindFoe, enemyId, 1, report.QuestUpdates);
                }
            }
            QuestLog.Refresh(db, state, report.QuestUpdates);
            return report;
        }

        /// <summary>Whether <paramref name="heroId"/> may wear <paramref name="equipmentId"/> (known piece, valid slot, class allowed).</summary>
        public static bool CanEquip(GameDB db, string heroId, string equipmentId) =>
            db.Equipment.TryGetValue(equipmentId, out var piece) && db.Heroes.ContainsKey(heroId)
            && Array.IndexOf(GameState.EquipSlots, piece.Slot) >= 0 && AllowsClass(piece, heroId);

        /// <summary>Whether this hero, in its current job, may wear <paramref name="equipmentId"/> (class and job restriction).</summary>
        public static bool CanEquip(GameDB db, HeroState hero, string equipmentId) =>
            CanEquip(db, hero.Id, equipmentId) && AllowsJob(db, db.Equipment[equipmentId], hero);

        /// <summary>Equips one piece from the bag; the previous piece in that slot returns to the bag. Vitals are clamped.</summary>
        public static ServiceResult Equip(GameDB db, GameState state, string heroId, string equipmentId)
        {
            var hero = state.Hero(heroId);
            if (hero == null) return ServiceResult.Fail("unknown_member");
            if (!db.Equipment.TryGetValue(equipmentId, out var piece)) return ServiceResult.Fail("unknown_equipment");
            if (Array.IndexOf(GameState.EquipSlots, piece.Slot) < 0) return ServiceResult.Fail("invalid_slot");
            if (!AllowsClass(piece, heroId)) return ServiceResult.Fail("class_mismatch");
            if (!AllowsJob(db, piece, hero)) return ServiceResult.Fail("job_mismatch");
            if (state.BagCount(equipmentId) < 1) return ServiceResult.Fail("not_owned");
            string previous = hero.Equipped(piece.Slot);
            state.RemoveEquipment(equipmentId, 1);
            if (previous != "") state.AddEquipment(previous, 1);
            hero.Equipment[piece.Slot] = equipmentId;
            ClampVitals(db, hero);
            return ServiceResult.Ok("equipped_msg", piece.DisplayName);
        }

        /// <summary>Moves the piece in <paramref name="slot"/> back to the bag.</summary>
        public static ServiceResult Unequip(GameDB db, GameState state, string heroId, string slot)
        {
            var hero = state.Hero(heroId);
            if (hero == null) return ServiceResult.Fail("unknown_member");
            if (Array.IndexOf(GameState.EquipSlots, slot) < 0) return ServiceResult.Fail("invalid_slot");
            string previous = hero.Equipped(slot);
            if (previous == "") return ServiceResult.Fail("slot_empty");
            state.AddEquipment(previous, 1);
            hero.Equipment[slot] = "";
            ClampVitals(db, hero);
            return ServiceResult.Ok("unequipped_msg", db.Equipment.TryGetValue(previous, out var p) ? p.DisplayName : previous);
        }

        /// <summary>Total pieces of <paramref name="equipmentId"/> currently worn by the party.</summary>
        public static int EquippedCount(GameState state, string equipmentId)
        {
            int n = 0;
            foreach (var hero in state.Party) foreach (string slot in GameState.EquipSlots) if (hero.Equipped(slot) == equipmentId) n++;
            return n;
        }

        /// <summary>Caps current HP/MP at the effective maxima (after gear changes).</summary>
        public static void ClampVitals(GameDB db, HeroState hero)
        {
            var stats = EffectiveStats(db, hero);
            hero.Hp = Math.Max(0, Math.Min(hero.Hp, stats.MaxHp));
            hero.Mp = Math.Max(0, Math.Min(hero.Mp, stats.MaxMp));
        }

        /// <summary>Sets a carried status, keeping the longer duration when already present.</summary>
        public static void SetStatus(HeroState hero, string statusId, int turns)
        {
            hero.Statuses[statusId] = hero.Statuses.TryGetValue(statusId, out int have) ? Math.Max(have, turns) : turns;
        }

        internal static int RoundI(double x) => (int)Math.Round(x, MidpointRounding.AwayFromZero);

        /// <summary>JSON floats -> the authored decimal as Godot held it (shortest round-trip text).</summary>
        internal static double D(float f) => double.Parse(f.ToString("R", CultureInfo.InvariantCulture), CultureInfo.InvariantCulture);

        static double Clamp(double v, double lo, double hi) => v < lo ? lo : (v > hi ? hi : v);
    }
}
