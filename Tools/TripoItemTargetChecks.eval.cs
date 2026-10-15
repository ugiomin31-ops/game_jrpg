// Parent executes with Unity Pipeline eval_file in Play Mode, idle town, all menus/modals closed.
// unity command eval_file --file Tools/TripoItemTargetChecks.eval.cs
// Temporary in-memory state only; no GameApp.NewGame/EnterTown/autosave calls and no files written.
// Checks real menu/list states and disabled submission. Screenshots/layout require separate review.
if (!UnityEngine.Application.isPlaying) throw new System.InvalidOperationException("Run in Play Mode.");
var app = Abyss.Runtime.GameApp.Instance;
if (app == null || app.State == null || app.UI == null || app.Screen != Abyss.Runtime.GameScreen.Town || app.State.PendingBattle != null)
    throw new System.InvalidOperationException("Requires initialized idle town.");
var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public;
var root = (Abyss.UI.UIRoot)typeof(Abyss.UI.GameUI).GetField("root", flags).GetValue(app.UI);
if (root.Screens.Count != 0 || root.Modals.Count != 0)
    throw new System.InvalidOperationException("Close all screens and modals first.");
Abyss.Logic.ItemDef revive = null;
foreach (var item in app.DB.Items.Values)
    if (item.ItemType == Abyss.Logic.ItemType.Revive && item.Target != "all_allies" && item.Power > 0f) { revive = item; break; }
if (revive == null) throw new System.InvalidOperationException("No positive-power single-target revive item.");
var original = app.State;
string originalJson = Abyss.Logic.Game.SaveCodec.Serialize(original);
var fixture = Abyss.Logic.Game.GameState.NewGame(app.DB, Abyss.Logic.Difficulty.Normal);
if (fixture.Party.Count < 2) throw new System.InvalidOperationException("Requires two starter hunters.");
fixture.Inventory[revive.Id] = 2;
fixture.Party[0].Hp = 1;
fixture.Party[1].Hp = 0;
var stateProperty = typeof(Abyss.Runtime.GameApp).GetProperty("State", flags);
var showTargets = typeof(Abyss.UI.GameUI).GetMethod("ShowItemTargets", flags);
int checks = 0;
void Check(bool ok, string label)
{
    if (!ok) throw new System.InvalidOperationException("ITEM_TARGET_FAIL: " + label);
    checks++;
}
try
{
    stateProperty.SetValue(app, fixture);
    string before = Abyss.Logic.Game.SaveCodec.Serialize(fixture);
    showTargets.Invoke(app.UI, new object[] { revive.Id, null });
    var menu = root.Screens.Top as Abyss.UI.GameMenuScreen;
    Check(menu != null, "target menu opened");
    var list = (Abyss.UI.UIList)typeof(Abyss.UI.GameMenuScreen).GetField("list", flags).GetValue(menu);
    Check(list.Items.Count == fixture.Party.Count, "one row per party member");
    Check(!list.Items[0].Enabled, "alive target disabled");
    Check(list.Items[0].DisabledReason == "쓰러진 헌터에게만 사용할 수 있습니다.", "alive target reason");
    Check(list.Items[1].Enabled, "dead target enabled");
    Check(before == Abyss.Logic.Game.SaveCodec.Serialize(fixture), "opening targets is pure");
    list.SelectedIndex = 0;
    list.Submit();
    Check(root.Modals.Count == 0, "disabled submit cannot open confirmation");
    Check(before == Abyss.Logic.Game.SaveCodec.Serialize(fixture), "disabled submit is pure");
    list.SelectedIndex = 1;
    list.Submit();
    Check(root.Modals.Count == 1, "enabled target opens confirmation");
    root.Modals.Pop(); // Cancel without executing the use callback.
    Check(before == Abyss.Logic.Game.SaveCodec.Serialize(fixture), "cancel preserves all fixture state");
    var used = Abyss.Logic.Game.GameFlow.UseFieldItem(app.DB, fixture, revive.Id, fixture.Party[1].Id, false);
    Check(used.Success && fixture.Party[1].Hp > 0, "GameFlow revives dead target");
    Check(fixture.ItemCount(revive.Id) == 1, "exactly one item consumed");
    menu.Refresh();
    Check(!list.Items[1].Enabled, "revived target disabled after refresh with stock remaining");
    var repeated = Abyss.Logic.Game.GameFlow.UseFieldItem(app.DB, fixture, revive.Id, fixture.Party[1].Id, false);
    Check(!repeated.Success && repeated.TextKey == "no_effect" && fixture.ItemCount(revive.Id) == 1, "repeat cannot consume");
    fixture.Party[1].Hp = 0;
    fixture.Inventory[revive.Id] = 0;
    menu.Refresh();
    foreach (var row in list.Items)
    {
        Check(!row.Enabled, "zero stock disables every target");
        Check(row.DisabledReason == app.DB.Text["item_missing"], "missing quantity reason takes precedence");
    }
    fixture.Inventory[revive.Id] = 1;
    menu.Refresh();
    Check(!list.Items[0].Enabled && list.Items[1].Enabled, "restock recomputes alive/dead availability");
}
finally
{
    try
    {
        while (root.Modals.Count > 0) root.Modals.Pop();
        while (root.Screens.Count > 0) root.Screens.Pop();
    }
    finally { stateProperty.SetValue(app, original); }
}
Check(object.ReferenceEquals(app.State, original), "original state reference restored");
Check(Abyss.Logic.Game.SaveCodec.Serialize(original) == originalJson, "original state unchanged");
return "ITEM_TARGET_PASS: " + checks + " assertions; real rows/submission checked, no screenshot/layout acceptance implied.";
