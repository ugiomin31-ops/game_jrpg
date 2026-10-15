// Parent-only Unity Pipeline probe: PLAY MODE, representative MANUAL battle at a command boundary.
// unity command eval_file --file Tools/TripoHudStateChecks.eval.cs
// Run at normal and compact sizes; the parent separately exercises a real resize across the boundary.
// Synchronously rebuilds cards twice, asserts per-unit flags and refreshed presentation, restores flags.
// No gameplay commands, frames awaited, screenshots, or resolution changes. Does not prove visual layout.
var bf = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var hudType = typeof(Abyss.UI.Battle.BattleHUD);
var outDir = System.IO.Path.Combine(System.IO.Directory.GetParent(UnityEngine.Application.dataPath).FullName,
    ".git", "codex-runs", "20261015-165918-tripo-motion", "fix-hud-state");
System.IO.Directory.CreateDirectory(outDir);
var reportPath = System.IO.Path.Combine(outDir, "checkreport-" + (Abyss.UI.UIRoot.Compact ? "compact" : "normal") + ".json");
var checks = new System.Collections.Generic.List<string>();
var report = new System.Collections.Generic.Dictionary<string, object>();
report["probe"] = "TripoHudStateChecks";
report["utc"] = System.DateTime.UtcNow.ToString("o");
report["width"] = UnityEngine.Screen.width;
report["height"] = UnityEngine.Screen.height;
report["compact"] = Abyss.UI.UIRoot.Compact;
report["coverage"] = "Direct synchronous RebuildCards at current geometry; real compact transition and visual/tween QA remain separate.";
void Check(bool condition, string label)
{
    if (!condition) throw new System.InvalidOperationException(label);
    checks.Add(label);
}
object Field(object target, string name) => target.GetType().GetField(name, bf).GetValue(target);
void SetFlag(object card, string name, bool value) => card.GetType().GetField(name, bf).SetValue(card, value);
bool Flag(object card, string name) => (bool)Field(card, name);
var originals = new System.Collections.Generic.Dictionary<string, (bool Pinned, bool EnemyThreat)>();
Abyss.UI.Battle.BattleHUD hud = null;
System.Collections.IDictionary cards = null;
var root = Abyss.UI.UIRoot.Instance;
var reducedProperty = typeof(Abyss.UI.UIRoot).GetProperty("ReducedMotion", bf);
bool originalReduced = false, restoreNeeded = false;
string failure = null;
try
{
    Check(UnityEngine.Application.isPlaying, "Play Mode required");
    var huds = UnityEngine.Object.FindObjectsByType<Abyss.UI.Battle.BattleHUD>(UnityEngine.FindObjectsSortMode.None);
    foreach (var candidate in huds)
        if (candidate.isActiveAndEnabled)
        {
            Check(hud == null, "Only one active BattleHUD");
            hud = candidate;
        }
    Check(hud != null && root != null, "Active BattleHUD and UIRoot required");
    Check(!(bool)Field(hud, "_auto") && (bool)Field(hud, "_input") && hud.CommandRootOpen,
        "Manual battle at root command boundary required");
    cards = (System.Collections.IDictionary)Field(hud, "_cards");
    int partyCount = 0, enemyCount = 0;
    foreach (System.Collections.DictionaryEntry entry in cards)
    {
        var unit = (Abyss.Runtime.Battle.BattleDisplayUnit)Field(entry.Value, "Unit");
        originals.Add((string)entry.Key, (Flag(entry.Value, "Pinned"), Flag(entry.Value, "EnemyThreat")));
        if (unit.Alive) { if (Flag(entry.Value, "Party")) partyCount++; else enemyCount++; }
    }
    Check(partyCount > 0 && enemyCount > 0, "Living party and enemy required");
    report["livingParty"] = partyCount;
    report["livingEnemies"] = enemyCount;
    Check(reducedProperty != null, "ReducedMotion property available");
    originalReduced = (bool)reducedProperty.GetValue(root);
    restoreNeeded = true;
    // Make positional assertions synchronous without advancing battle replay or changing saved preferences.
    reducedProperty.SetValue(root, true);
    var refresh = hudType.GetMethod("RefreshPlateStates", bf);
    var rebuild = hudType.GetMethod("RebuildCards", bf);
    Check(refresh != null && rebuild != null, "HUD methods available");
    for (int pass = 0; pass < 2; pass++)
    {
        int partyIndex = 0, enemyIndex = 0;
        foreach (System.Collections.DictionaryEntry entry in cards)
        {
            var card = entry.Value;
            var unit = (Abyss.Runtime.Battle.BattleDisplayUnit)Field(card, "Unit");
            bool party = Flag(card, "Party");
            bool chosen = unit.Alive && ((party ? partyIndex++ : enemyIndex++) % 2 == pass);
            SetFlag(card, "Pinned", !party && chosen);
            SetFlag(card, "EnemyThreat", party && chosen);
        }
        refresh.Invoke(hud, null);
        var expected = new System.Collections.Generic.Dictionary<string,
            (object Card, object Unit, bool Pinned, bool EnemyThreat, bool Marked, UnityEngine.Color Edge,
             UnityEngine.Color Fill, UnityEngine.Vector2 Position, bool Chip)>();
        foreach (System.Collections.DictionaryEntry entry in cards)
        {
            var card = entry.Value;
            var plate = (Abyss.UI.UISlantPlate)Field(card, "Plate");
            var chip = (Abyss.UI.UISlantPlate)Field(card, "ThreatChip");
            var rect = (UnityEngine.RectTransform)Field(card, "Root");
            expected.Add((string)entry.Key, (card, Field(card, "Unit"), Flag(card, "Pinned"), Flag(card, "EnemyThreat"),
                Flag(card, "Marked"), plate.Edge.color, plate.Fill.color, rect.anchoredPosition,
                chip != null && chip.gameObject.activeSelf));
        }
        rebuild.Invoke(hud, null);
        Check(cards.Count == expected.Count, "pass " + pass + " card count preserved");
        foreach (var entry in expected)
        {
            string prefix = "pass " + pass + " " + entry.Key + " ";
            Check(cards.Contains(entry.Key), prefix + "unit ID preserved");
            var card = cards[entry.Key];
            var state = entry.Value;
            Check(!object.ReferenceEquals(card, state.Card), prefix + "card recreated");
            Check(object.ReferenceEquals(Field(card, "Unit"), state.Unit), prefix + "display unit preserved");
            Check(Flag(card, "Pinned") == state.Pinned, prefix + "Pinned preserved");
            Check(Flag(card, "EnemyThreat") == state.EnemyThreat, prefix + "EnemyThreat preserved");
            Check(Flag(card, "Marked") == state.Marked, prefix + "marks reapplied");
            Check(Flag(card, "Dirty"), prefix + "tag layout invalidated");
            var plate = (Abyss.UI.UISlantPlate)Field(card, "Plate");
            Check(plate.Edge.color == state.Edge && plate.Fill.color == state.Fill, prefix + "plate colours refreshed");
            if (Flag(card, "Party"))
            {
                var chip = (Abyss.UI.UISlantPlate)Field(card, "ThreatChip");
                Check(chip != null && chip.gameObject.activeSelf == state.Chip, prefix + "threat chip refreshed");
                var rect = (UnityEngine.RectTransform)Field(card, "Root");
                Check((rect.anchoredPosition - state.Position).sqrMagnitude < 0.01f, prefix + "raised position refreshed");
            }
        }
    }
}
catch (System.Exception ex)
{
    failure = ex.ToString();
}
finally
{
    try
    {
        if (restoreNeeded)
        {
            foreach (var entry in originals)
            {
                var card = cards[entry.Key];
                SetFlag(card, "Pinned", entry.Value.Pinned);
                SetFlag(card, "EnemyThreat", entry.Value.EnemyThreat);
                SetFlag(card, "Dirty", true);
            }
            hudType.GetMethod("RefreshPlateStates", bf).Invoke(hud, null);
        }
    }
    catch (System.Exception ex) { failure = (failure ?? "") + "\nRESTORE FAILED: " + ex; }
    finally
    {
        if (restoreNeeded) reducedProperty.SetValue(root, originalReduced);
        report["passed"] = failure == null;
        report["checks"] = checks;
        report["failure"] = failure;
        System.IO.File.WriteAllText(reportPath, Newtonsoft.Json.JsonConvert.SerializeObject(report, Newtonsoft.Json.Formatting.Indented));
    }
}
if (failure != null) throw new System.InvalidOperationException("HUD_STATE_FAIL: " + reportPath + "\n" + failure);
return "HUD_STATE_PASS: " + checks.Count + " assertions; " + reportPath;
