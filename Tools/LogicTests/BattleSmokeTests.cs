// Full simulated battles (AUTO heroes vs enemy AI) over every floor's encounter groups, party at the floor's
// main-path level with chapter gear (CampaignSim).
using System;
using System.Collections.Generic;
using System.Linq;
using Abyss.Logic;
using Abyss.Logic.Battle;

namespace Abyss.LogicTests
{
    public static class BattleSimTests
    {
        [LogicTest]
        public static void EveryEncounterGroupCompletes()
        {
            var db = TestMain.DB;
            int battles = 0, victories = 0;
            var summary = new List<string>();
            foreach (var floor in db.Floors)
            {
                int level = CampaignSim.FloorLevel(floor.Index);
                var party = CampaignSim.Party(db, level, CampaignSim.Chapter(floor.Index));
                int floorWins = 0, floorBattles = 0;
                var groups = new List<List<string>>(floor.EncounterGroups);
                if (floor.ShowcaseGroup.Count > 0) groups.Add(floor.ShowcaseGroup);
                foreach (var group in groups)
                {
                    for (int seed = 1; seed <= 3; seed++)
                    {
                        var engine = new BattleEngine(db, Abyss.Logic.Game.PartyStats.BuildBattleSetup(db, party, BattleKind.Random, group, 1f, floor.Id, seed * 7919 + battles));
                        BattleTestUtil.RunAuto(engine);
                        Assert.True(engine.State == BattleEngineState.Ended, $"{floor.FloorLabel} {string.Join(",", group)} ended");
                        battles++; floorBattles++;
                        if (engine.Outcome.Result == BattleResult.Victory) { victories++; floorWins++; }
                    }
                }
                summary.Add($"{floor.FloorLabel}:{floorWins}/{floorBattles}");
            }
            Console.WriteLine("  encounter wins " + string.Join(" ", summary));
            Assert.True(battles > 50, "ran battles");
            Assert.True(victories * 10 >= battles * 6, $"AUTO party wins most normal encounters ({victories}/{battles})");
        }
    }
}
