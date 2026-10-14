// External QA code evaluated by Unity Pipeline; never included in the shipped player.
var outDir = System.IO.Path.GetFullPath("docs/verification/pr6-improvements");
var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var checks = new System.Collections.Generic.List<object>();
void Check(string name, bool passed, object detail = null) { checks.Add(new { name, passed, detail }); }
async System.Threading.Tasks.Task Frames(int count) {
    int end = Time.frameCount + count;
    var deadline = System.DateTime.UtcNow.AddSeconds(35);
    while (Time.frameCount < end) { if (System.DateTime.UtcNow > deadline) throw new System.TimeoutException("Game frames stopped advancing"); await System.Threading.Tasks.Task.Yield(); }
}
void Resize(int width, int height) {
    var assembly = typeof(UnityEditor.Editor).Assembly;
    var sizesType = assembly.GetType("UnityEditor.GameViewSizes");
    var singleton = typeof(UnityEditor.ScriptableSingleton<>).MakeGenericType(sizesType);
    var sizes = singleton.GetProperty("instance").GetValue(null);
    var getGroup = sizesType.GetMethod("GetGroup");
    var group = getGroup.Invoke(sizes, new[] { System.Enum.Parse(getGroup.GetParameters()[0].ParameterType, "Standalone") });
    var sizeType = assembly.GetType("UnityEditor.GameViewSize");
    var kind = assembly.GetType("UnityEditor.GameViewSizeType");
    var ctor = sizeType.GetConstructor(flags, null, new[] { kind, typeof(int), typeof(int), typeof(string) }, null);
    var size = ctor.Invoke(new object[] { System.Enum.ToObject(kind, 1), width, height, "PR6 acceptance" });
    int index = (int)group.GetType().GetMethod("GetTotalCount").Invoke(group, null);
    group.GetType().GetMethod("AddCustomSize").Invoke(group, new[] { size });
    var viewType = assembly.GetType("UnityEditor.GameView");
    var window = UnityEditor.EditorWindow.GetWindow(viewType);
    viewType.GetProperty("selectedSizeIndex", flags).SetValue(window, index);
}
async System.Threading.Tasks.Task Snap(string name, int w, int h) {
    Resize(w, h); await Frames(15);
    Check("resolution " + name + " " + w + "x" + h, Screen.width == w && Screen.height == h, new { actualWidth = Screen.width, actualHeight = Screen.height });
    ScreenCapture.CaptureScreenshot(System.IO.Path.Combine(outDir, "after-" + name + "-" + w + "x" + h + ".png"));
    await Frames(5);
}
async System.Threading.Tasks.Task Run() {
    try {
        Application.runInBackground = true;
        var app = Abyss.Runtime.GameApp.Instance;
        if (app == null) throw new System.Exception("Play mode game missing");
        var savePath = System.IO.Path.Combine(outDir, "qa-save-final");
        typeof(Abyss.Runtime.GameApp).GetField("saveDirectory", flags).SetValue(app, savePath);
        typeof(Abyss.Runtime.GameApp).GetField("<Saves>k__BackingField", flags).SetValue(app, new Abyss.Runtime.Persistence.SaveRepository(savePath, app.DB));
        app.Preferences.AutoBattle = false;
        foreach (var size in new[] { new[] {1280,720}, new[] {1920,1080}, new[] {1024,768}, new[] {1440,900}, new[] {915,412} }) {
            app.ShowTitle(); await Snap("title", size[0], size[1]);
            app.NewGame(Abyss.Logic.Difficulty.Normal);
            Abyss.Logic.Game.GameFlow.CompletePrologue(app.State);
            app.State.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag("first_town"));
            app.State.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag("first_battle"));
            app.State.Flags.Add("biome_0_seen");
            app.EnterTown(); await Snap("guild", size[0], size[1]);
            app.UI.ShowParty(); await Snap("roster", size[0], size[1]);
            app.Depart(0); await Frames(20);
            var request = (Abyss.Logic.Dungeon.DungeonBattleRequest)typeof(Abyss.Logic.Dungeon.DungeonRun).GetMethod("StartBattle", flags).Invoke(app.Dungeon,
                new object[] { Abyss.Logic.BattleKind.Random, new System.Collections.Generic.List<string> {"slime","slime"}, app.State.Position, app.State.Position, "", 1f });
            app.BeginBattle(request.Setup); await Frames(150);
            await Snap("battle", size[0], size[1]);
        }
        var battle = app.Battle;
        await Frames(60);
        Check("battle awaiting manual input", !battle.Playing && battle.Engine.ActiveHero != null);
        var hud = (Abyss.UI.Battle.BattleHUD)typeof(Abyss.Runtime.Battle.BattleView).GetField("_hud", flags).GetValue(battle);
        var hudType = hud.GetType();
        var actor = battle.Engine.ActiveHero;
        if (actor == null) throw new System.Exception("No active hero for target checks");
        var skill = battle.Engine.GetCommandOptions(actor).Skills.FirstOrDefault(s => s.Usable && !s.IsUltimate && s.MpCost > 0 && s.Target == Abyss.Logic.Battle.TargetRule.SingleEnemy);
        var command = skill == null ? Abyss.Logic.Battle.BattleCommand.Attack(null) : Abyss.Logic.Battle.BattleCommand.Skill(skill.Id);
        string label = skill == null ? "공격" : skill.DisplayName + " MP " + skill.MpCost;
        string description = skill == null ? "장비 무기" : skill.Skill.Description + " " + skill.Skill.Element;
        var submitField = hudType.GetField("_submit", flags);
        var originalSubmit = (System.Action<Abyss.Logic.Battle.BattleCommand>)submitField.GetValue(hud);
        int submits = 0;
        submitField.SetValue(hud, new System.Action<Abyss.Logic.Battle.BattleCommand>(c => { submits++; originalSubmit(c); }));
        void OpenTargets() { hudType.GetMethod("Targets", flags).Invoke(hud, new object[] { command, null, label, description }); }
        string StateSnapshot() => Newtonsoft.Json.JsonConvert.SerializeObject(battle.Engine.Units.Select(u => new {u.Id,u.Hp,u.Mp,u.Tp,u.Shield}).ToArray());
        OpenTargets(); await Frames(2);
        string before = StateSnapshot();
        var rows = (System.Collections.Generic.List<Abyss.UI.UIButton>)hudType.GetField("_buttons", flags).GetValue(hud);
        rows[0].Click(); await Frames(20);
        Check("first pointer click previews without submission", submits == 0 && before == StateSnapshot());
        var detail = (TMPro.TMP_Text)hudType.GetField("_description", flags).GetValue(hud);
        Check("targeting keeps action and cost", detail.text.Contains(label), detail.text);
        Check("unknown weakness remains undiscovered", battle.Engine.Enemies.All(u => battle.Engine.KnownWeaknessesOf(u).Count == 0));
        await Snap("target-preview",1280,720);
        hudType.GetMethod("Back", flags).Invoke(hud, null); await Frames(2);
        Check("cancel consumes no resource", submits == 0 && before == StateSnapshot());
        OpenTargets(); await Frames(2);
        rows = (System.Collections.Generic.List<Abyss.UI.UIButton>)hudType.GetField("_buttons", flags).GetValue(hud);
        rows[0].Click(); await Frames(20);
        int mp = actor.Mp;
        rows[0].Click(); await Frames(2);
        Check("second pointer click commits exactly once", submits == 1);
        Check("spell consumes MP once", skill != null && actor.Mp == mp - skill.MpCost, new { testedSkill = skill == null ? "none" : skill.Id, beforeMp = mp, afterMp = actor.Mp });
        rows[0].Click();
        Check("duplicate click cannot submit again", submits == 1);
        await Frames(180);
        Check("battle continues after input", battle.Engine.Round > 0 && Time.frameCount > 300);
        app.EnterTown(); await Frames(20);
        var stateBeforeQuery = Abyss.Logic.Game.SaveCodec.Serialize(app.State);
        var report = Abyss.Logic.Game.ExpeditionReadiness.Evaluate(app.DB, app.State);
        Check("readiness query is pure", stateBeforeQuery == Abyss.Logic.Game.SaveCodec.Serialize(app.State), report.SummaryText);
        app.Saves.Write(0, app.State);
        var loaded = app.Saves.Read(0);
        Check("save reload preserves party and progress", loaded.Party.Select(h => h.Id).SequenceEqual(app.State.Party.Select(h => h.Id)) && loaded.Gold == app.State.Gold && loaded.DeepestFloor == app.State.DeepestFloor);
        var hunterId = app.DB.RosterOrder.First(id => !Abyss.Logic.Game.HunterRoster.IsRecruited(app.State, id));
        Abyss.Logic.Game.HunterRoster.Recruit(app.DB, app.State, hunterId);
        app.UI.ShowParty(); await Snap("recruited-roster", 1280,720);
        app.State.Party[0].Hp = 0; app.State.Party[1].Hp = 1; app.State.Party[1].Mp = 0;
        app.EnterTown(); await Snap("readiness-warning",1280,720);
        Check("readiness warning accessible text", Abyss.Logic.Game.ExpeditionReadiness.Evaluate(app.DB,app.State).HasWarnings);
        System.IO.File.WriteAllText(System.IO.Path.Combine(outDir,"runtime-acceptance.json"), Newtonsoft.Json.JsonConvert.SerializeObject(new { status="complete", fixture="seeded editor runtime; isolated saves", checks },Newtonsoft.Json.Formatting.Indented));
    } catch (System.Exception e) {
        System.IO.File.WriteAllText(System.IO.Path.Combine(outDir,"runtime-acceptance.json"), Newtonsoft.Json.JsonConvert.SerializeObject(new { status="failed", error=e.ToString(), checks },Newtonsoft.Json.Formatting.Indented));
    }
}
_ = Run();
return "acceptance started; inspect runtime-acceptance.json";
