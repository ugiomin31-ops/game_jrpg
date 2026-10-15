// R5-FIX natural run: AUTO boss battle at 2x; records every real phase / ultimate call-out (seated or suppressed) and verifies it against living hero bodies.
var BF = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var outDir = System.IO.Path.Combine(System.IO.Directory.GetParent(Application.dataPath).FullName, "docs", "verification", "floor1", "r5fix");
var clock = System.Diagnostics.Stopwatch.StartNew(); double Now() => clock.Elapsed.TotalSeconds;
var sb = new System.Text.StringBuilder();
void P(string m) { sb.AppendLine("[" + Now().ToString("F1") + "s] " + m); System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "natural.txt"), sb.ToString()); }
var ht = typeof(Abyss.UI.Battle.BattleHUD);
async System.Threading.Tasks.Task Run()
{
    try
    {
        Application.runInBackground = true;
        var app = Abyss.Runtime.GameApp.Instance; var db = app.DB;
        var state = Abyss.Logic.Game.GameState.NewGame(db, Abyss.Logic.Difficulty.Normal);
        state.Flags.Remove(Abyss.Logic.Game.GameFlow.FlagProloguePending);
        foreach (string tip in new[] { "first_battle", "first_foe", "first_tp_full", "first_trap", "first_town" }) state.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag(tip));
        foreach (var h in state.Party) { h.Level = 8; h.Xp = 0; h.Hp = -1; h.Mp = -1; }
        state.FloorIndex = 2; state.Location = Abyss.Logic.Game.GameLocation.Dungeon; state.DeepestFloor = 2;
        state.Repair(db);
        app.BeginReview(state, 2);
        await System.Threading.Tasks.Task.Delay(3000);
        var start = typeof(Abyss.Logic.Dungeon.DungeonRun).GetMethod("StartBattle", BF);
        var req = (Abyss.Logic.Dungeon.DungeonBattleRequest)start.Invoke(app.Dungeon, new object[] { Abyss.Logic.BattleKind.Boss, new List<string> { "subway_bat_lord" }, state.Position, state.Position, "", 1f });
        app.Preferences.AutoBattle = true; app.Preferences.BattleSpeed = 2f;
        app.BeginBattle(req.Setup);
        bool was = false; int shots = 0; double t0 = Now(); int violations = 0, seen = 0;
        while (Now() - t0 < 170 && app.Screen == Abyss.Runtime.GameScreen.Battle)
        {
            var hud = UnityEngine.Object.FindFirstObjectByType<Abyss.UI.Battle.BattleHUD>();
            if (hud != null)
            {
                bool req2 = (bool)ht.GetField("_coRequested", BF).GetValue(hud), shown = (bool)ht.GetField("_coShown", BF).GetValue(hud);
                var cut = (RectTransform)ht.GetField("_cutin", BF).GetValue(hud);
                if (req2 && !was) { seen++; P("call-out requested: '" + ((TMPro.TMP_Text)cut.GetChild(0).GetComponent<TMPro.TMP_Text>())?.text + "'"); }
                if (req2 && cut.gameObject.activeInHierarchy)
                {
                    var root = (RectTransform)ht.GetField("_root", BF).GetValue(hud);
                    var c = new Vector3[4]; cut.GetWorldCorners(c);
                    var a = root.InverseTransformPoint(c[0]); var b = root.InverseTransformPoint(c[2]); var mn = root.rect.min;
                    var co = Rect.MinMaxRect(a.x - mn.x, a.y - mn.y, b.x - mn.x, b.y - mn.y);
                    foreach (System.Collections.DictionaryEntry kv in (System.Collections.IDictionary)ht.GetField("_cards", BF).GetValue(hud))
                    {
                        var u = (Abyss.Runtime.Battle.BattleDisplayUnit)kv.Value.GetType().GetField("Unit").GetValue(kv.Value);
                        if (u.Side == Abyss.Logic.Battle.BattleSide.Party && u.Alive && hud.TryGetUnitRect(u.Id, out var body) && body.Overlaps(co)) { violations++; P("VIOLATION body " + u.Id + " " + body + " vs " + co); }
                    }
                    if (shots < 3 && Now() - t0 > 0) { ScreenCapture.CaptureScreenshot(System.IO.Path.Combine(outDir, "natural_callout_" + (shots++) + ".png")); P("captured seat=" + co + " screen=" + Screen.width + "x" + Screen.height); }
                }
                else if (req2) P("suppressed while requested (frame " + Time.frameCount + ")");
                was = req2;
            }
            await System.Threading.Tasks.Task.Yield();
        }
        P("done: callouts seen=" + seen + " violations=" + violations + " screen=" + app.Screen);
    }
    catch (Exception e) { P("FAILED " + e); }
    System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "natural.done"), "done");
}
if (System.IO.File.Exists(System.IO.Path.Combine(outDir, "natural.done"))) System.IO.File.Delete(System.IO.Path.Combine(outDir, "natural.done"));
_ = Run();
return "natural started";
