// Balance T2: defeat gold loss per difficulty (and its Korean text), the last superboss's EXP, and the zone-1 boss's own
// model. Regular battle length (2-4 rounds per zone) is asserted with the campaign table in CampaignBalanceTests.
using System;
using System.IO;
using Abyss.Logic;
using Abyss.Logic.Game;

namespace Abyss.LogicTests
{
    public static class T2BalanceTests
    {
        [LogicTest]
        public static void DefeatGoldLossIsZeroQuarterHalfByDifficulty()
        {
            var db = TestMain.DB;
            Assert.Equal(0f, TownServices.DefeatGoldLoss(Difficulty.Easy), "easy keeps all gold");
            Assert.Equal(0.25f, TownServices.DefeatGoldLoss(Difficulty.Normal), "normal loses 25 %");
            Assert.Equal(0.5f, TownServices.DefeatGoldLoss(Difficulty.Hard), "hard loses 50 %");
            foreach (var (difficulty, expected) in new[] { (Difficulty.Easy, 0), (Difficulty.Normal, 250), (Difficulty.Hard, 501) })
            {
                var state = GameState.NewGame(db, difficulty);
                state.Gold = 1003;
                // The preview is pure and equals what the recovery then takes (rounded down).
                Assert.Equal(expected, TownServices.DefeatGoldLossAmount(state), difficulty + ": preview");
                Assert.Equal(1003, state.Gold, difficulty + ": preview changes nothing");
                Assert.Equal(0, GameFlow.RecoverFromDefeat(db, state), difficulty + ": no pending defeat, no loss");
                Assert.Equal(1003, state.Gold, difficulty + ": no pending defeat keeps gold");
                state.Flags.Add(GameFlow.FlagDefeatPending);
                Assert.Equal(expected, GameFlow.RecoverFromDefeat(db, state), difficulty + ": gold lost");
                Assert.Equal(1003 - expected, state.Gold, difficulty + ": gold left");
                Assert.True(!state.Flags.Contains(GameFlow.FlagDefeatPending), difficulty + ": defeat cleared");
            }
            var broke = GameState.NewGame(db, Difficulty.Hard);
            broke.Gold = 1;
            Assert.Equal(0, TownServices.DefeatGoldLossAmount(broke), "one coin rounds down to no loss");
        }

        [LogicTest]
        public static void DefeatTextsNameTheLostAmountInKorean()
        {
            var db = TestMain.DB;
            foreach (var key in new[] { "defeat_penalty", "defeat_no_loss", "defeat_easy", "defeat_gold_lost" })
                Assert.True(db.Text.ContainsKey(key), "text_ko has " + key);
            string penalty = db.T("defeat_penalty", 25, "1,250");
            Assert.True(penalty.Contains("25%") && penalty.Contains("1,250만원") && !penalty.Contains("%d") && !penalty.Contains("%s"),
                "defeat menu names percent and amount: " + penalty);
            string lost = db.T("defeat_gold_lost", "1,250");
            Assert.True(lost.Contains("1,250만원") && lost.Contains("잃었다"), "return toast names the lost amount: " + lost);
            Assert.True(!db.T("difficulty_hint").Contains("보통·어려움에서는 패배 시 보유 금액의 절반"), "difficulty hint no longer says normal loses half");
        }

        [LogicTest]
        public static void LastSuperbossPaysOnePointTwoTimesTheAbyssLord()
        {
            var db = TestMain.DB;
            int lord = db.Enemies["abyss_lord"].ExperienceReward, echo = db.Enemies["abyss_lord_ex"].ExperienceReward;
            Assert.Equal(59884, echo, "abyss_lord_ex EXP");
            Assert.Equal((int)Math.Round(lord * 1.2), echo, "abyss_lord_ex EXP is 1.2x abyss_lord (" + lord + ")");
        }

        [LogicTest]
        public static void SubwayBatLordUsesItsOwnUntintedModel()
        {
            var db = TestMain.DB;
            var def = db.Enemies["subway_bat_lord"];
            Assert.Equal("subway_bat_lord", ArtVariants.EnemyModel(def), "own model");
            Assert.True(ArtVariants.EnemyTint(def) == null && def.Tint.Length >= 3 && def.Tint[0] == 1f && def.Tint[1] == 1f && def.Tint[2] == 1f,
                "no tint on the textured model");
            Assert.Equal(1f, def.ScaleMult, "boss scale (the model is built at the elite_bat height it replaces)");
            string resources = Path.GetFullPath(Path.Combine(Environment.GetEnvironmentVariable("ABYSS_DATA_DIR"), ".."));
            Assert.True(File.Exists(Path.Combine(resources, "Art", "Enemies", "subway_bat_lord", "subway_bat_lord.fbx")), "model file exists");
        }
    }
}
