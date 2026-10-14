using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Reflection;
using System.Threading.Tasks;
using UnityEngine;
using UnityEditor;
using Abyss.Runtime;
using Abyss.Runtime.Persistence;
using Abyss.Logic;
using Abyss.Logic.Game;
using Abyss.Logic.Battle;
using Abyss.Logic.Dungeon;
using Newtonsoft.Json;
public static class Pr6Review {
 const string Out = "docs/verification/pr6-improvements";
 static readonly BindingFlags Flags = BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;
 public static object BeginBaseline() { _ = Baseline(); return "started"; }
 static async Task Frames(int n) { int f=Time.frameCount+n; while(Time.frameCount<f) await Task.Yield(); }
 static async Task Snap(string name,int w,int h) { PhoneView(w,h); await Frames(15); ScreenCapture.CaptureScreenshot(Out+"/baseline-"+name+"-"+w+"x"+h+".png"); await Frames(5); }
 public static object Isolate() { var a=GameApp.Instance; string p=Path.GetFullPath(Out+"/qa-save"); typeof(GameApp).GetField("saveDirectory",Flags).SetValue(a,p); typeof(GameApp).GetField("<Saves>k__BackingField",Flags).SetValue(a,new SaveRepository(p,a.DB)); a.Preferences.AutoBattle=false; Application.runInBackground=true; return p; }
 static async Task Baseline() { Directory.CreateDirectory(Out); try { Isolate(); var a=GameApp.Instance;
 foreach(var sz in new[]{new[]{1280,720},new[]{1920,1080},new[]{1024,768},new[]{1440,900},new[]{915,412}}) {
 a.ShowTitle(); await Snap("title",sz[0],sz[1]);
 a.NewGame(Difficulty.Normal); GameFlow.CompletePrologue(a.State); a.State.Flags.Add(GameFlow.TipFlag("first_town")); a.State.Flags.Add(GameFlow.TipFlag("first_battle")); a.State.Flags.Add("biome_0_seen"); a.EnterTown(); await Snap("guild",sz[0],sz[1]);
 a.UI.ShowParty(); await Snap("roster",sz[0],sz[1]);
 a.Depart(0); await Frames(20);
 var request=(DungeonBattleRequest)typeof(DungeonRun).GetMethod("StartBattle",Flags).Invoke(a.Dungeon,new object[]{BattleKind.Random,new List<string>{"slime","slime"},a.State.Position,a.State.Position,"",1f});
 a.BeginBattle(request.Setup); await Frames(120); await Snap("battle",sz[0],sz[1]);
 }
 File.WriteAllText(Out+"/baseline-captures.json",JsonConvert.SerializeObject(new{status="complete",screens=20}));
 } catch(Exception e) { File.WriteAllText(Out+"/baseline-captures.json",JsonConvert.SerializeObject(new{status="failed",error=e.ToString()})); } }
    public static object PhoneView(int width, int height)
    {
        // Unity has no public Editor API for a fixed Game view resolution.
        // Keep the reflection in this external review tool, away from shipped code.
        var assembly = typeof(Editor).Assembly;
        var sizesType = assembly.GetType("UnityEditor.GameViewSizes");
        var singleton = typeof(ScriptableSingleton<>).MakeGenericType(sizesType);
        var sizes = singleton.GetProperty("instance").GetValue(null);
        var getGroup = sizesType.GetMethod("GetGroup");
        var group = getGroup.Invoke(sizes, new[] { Enum.Parse(getGroup.GetParameters()[0].ParameterType, "Standalone") });
        var sizeType = assembly.GetType("UnityEditor.GameViewSize");
        var kind = assembly.GetType("UnityEditor.GameViewSizeType");
        var ctor = sizeType.GetConstructor(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance, null, new[] { kind, typeof(int), typeof(int), typeof(string) }, null);
        var size = ctor.Invoke(new object[] { Enum.ToObject(kind, 1), width, height, "Codex mobile review" });
        int index = (int)group.GetType().GetMethod("GetTotalCount").Invoke(group, null);
        group.GetType().GetMethod("AddCustomSize").Invoke(group, new[] { size });
        var viewType = assembly.GetType("UnityEditor.GameView");
        var window = EditorWindow.GetWindow(viewType);
        viewType.GetProperty("selectedSizeIndex", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic).SetValue(window, index);
        return new { width, height };
    }
}
