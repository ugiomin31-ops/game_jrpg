// External editor QA only. Does not enter the shipped player.
var outDir = System.IO.Path.GetFullPath("docs/verification/pr6-improvements");
var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var checks = new System.Collections.Generic.List<object>();
void Check(string name, bool passed, object detail = null) { checks.Add(new { name, passed, detail }); }
async System.Threading.Tasks.Task Frames(int count) {
    int end = Time.frameCount + count;
    var deadline = System.DateTime.UtcNow.AddSeconds(25);
    while (Time.frameCount < end) { if (System.DateTime.UtcNow > deadline) throw new System.TimeoutException("Game frames stopped"); await System.Threading.Tasks.Task.Yield(); }
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
    var size = ctor.Invoke(new object[] { System.Enum.ToObject(kind, 1), width, height, "PR6 final delta" });
    int index = (int)group.GetType().GetMethod("GetTotalCount").Invoke(group, null);
    group.GetType().GetMethod("AddCustomSize").Invoke(group, new[] { size });
    var viewType = assembly.GetType("UnityEditor.GameView");
    var window = UnityEditor.EditorWindow.GetWindow(viewType);
    viewType.GetProperty("selectedSizeIndex", flags).SetValue(window, index);
}
async System.Threading.Tasks.Task Snap(string name, int w, int h) {
    Resize(w,h); await Frames(20);
    Check("resolution " + name, Screen.width == w && Screen.height == h, new { width=Screen.width, height=Screen.height });
    ScreenCapture.CaptureScreenshot(System.IO.Path.Combine(outDir,"final-"+name+"-"+w+"x"+h+".png")); await Frames(8);
}
async System.Threading.Tasks.Task Run() {
 try {
 var app=Abyss.Runtime.GameApp.Instance;
 app.NewGame(Abyss.Logic.Difficulty.Normal);
 Abyss.Logic.Game.GameFlow.CompletePrologue(app.State);
 app.State.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag("first_town"));
 app.State.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag("first_battle"));
 app.State.Flags.Add("biome_0_seen"); app.EnterTown(); await Frames(10);
 var recruit=app.DB.RosterOrder.First(id=>!Abyss.Logic.Game.HunterRoster.IsRecruited(app.State,id));
 Abyss.Logic.Game.HunterRoster.Recruit(app.DB,app.State,recruit);
 app.UI.ShowParty(); await Frames(5);
 var owner=GameObject.FindFirstObjectByType<Abyss.UI.GameMenuScreen>();
 app.UI.GetType().GetMethod("ShowReserveMember",flags).Invoke(app.UI,new object[]{app.State.Reserve.First(),owner}); await Frames(5);
 var menu=GameObject.FindObjectsByType<Abyss.UI.GameMenuScreen>(FindObjectsInactive.Exclude,FindObjectsSortMode.None).First(m=>m.gameObject.activeInHierarchy);
 var list=(Abyss.UI.UIList)typeof(Abyss.UI.GameMenuScreen).GetField("list",flags).GetValue(menu); list.SelectedIndex=1;
 typeof(Abyss.UI.GameMenuScreen).GetMethod("SetDetails",flags).Invoke(menu,new object[]{list.Selected});
 await Snap("roster-comparison",915,412);
 app.EnterTown(); await Frames(10); app.Depart(0); await Frames(20);
 var request=(Abyss.Logic.Dungeon.DungeonBattleRequest)typeof(Abyss.Logic.Dungeon.DungeonRun).GetMethod("StartBattle",flags).Invoke(app.Dungeon,new object[]{Abyss.Logic.BattleKind.Random,Enumerable.Repeat("slime",5).ToList(),app.State.Position,app.State.Position,"",1f});
 app.BeginBattle(request.Setup); await Frames(180);
 var wait=System.DateTime.UtcNow.AddSeconds(25);
 while(app.Battle.Playing) {if(System.DateTime.UtcNow>wait) throw new System.Exception("Manual input did not become available"); await Frames(10);}
    var battle=app.Battle;
    var hud=(Abyss.UI.Battle.BattleHUD)typeof(Abyss.Runtime.Battle.BattleView).GetField("_hud",flags).GetValue(battle);
    var type=hud.GetType(); var actor=battle.Engine.ActiveHero;
    if(actor==null || battle.Playing) throw new System.Exception("Wait for a real manual turn before running targeting fixture");
    Check("manual turn available",actor!=null && !battle.Playing);
    var skill=battle.Engine.GetCommandOptions(actor).Skills.FirstOrDefault(s=>s.Usable && !s.IsUltimate && s.MpCost>0 && s.Target==Abyss.Logic.Battle.TargetRule.SingleEnemy);
    var command=skill==null?Abyss.Logic.Battle.BattleCommand.Attack(null):Abyss.Logic.Battle.BattleCommand.Skill(skill.Id);
    string label=skill==null?"공격":skill.DisplayName+" MP "+skill.MpCost;
    var submit=type.GetField("_submit",flags); var original=(System.Action<Abyss.Logic.Battle.BattleCommand>)submit.GetValue(hud); int submits=0;
    submit.SetValue(hud,new System.Action<Abyss.Logic.Battle.BattleCommand>(c=>{submits++; original(c);}));
    void Targets(){type.GetMethod("Targets",flags).Invoke(hud,new object[]{command,null,label,skill==null?"무기":skill.Skill.Description});}
    void Pointer(int i){type.GetMethod("PointerSelect",flags).Invoke(hud,new object[]{i});}
    void Focus(int i){type.GetMethod("Focus",flags).Invoke(hud,new object[]{i});}
    void Page(int d){type.GetMethod("Page",flags).Invoke(hud,new object[]{d});}
    string Snapshot()=>Newtonsoft.Json.JsonConvert.SerializeObject(battle.Engine.Units.Select(u=>new{u.Id,u.Hp,u.Mp,u.Tp,u.Shield}).ToArray());
    Targets(); await Frames(3); string initial=Snapshot();
    Pointer(0); await Frames(3); Check("first pointer preview",submits==0 && initial==Snapshot());
    Focus(1); Pointer(0); await Frames(3); Check("pointer after different keyboard focus previews again",submits==0 && initial==Snapshot());
    Check("targets span two pages",(int)type.GetProperty("PerPage",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic).GetValue(null)<5);
    Page(1); Page(-1); Pointer(0); await Frames(3); Check("pointer after page return previews again",submits==0 && initial==Snapshot());
    Check("unknown weaknesses remain unknown",battle.Engine.Enemies.All(e=>battle.Engine.KnownWeaknessesOf(e).Count==0));
    await Snap("target-preview",915,412);
    var heading=(TMPro.TMP_Text)type.GetField("_title",flags).GetValue(hud); heading.ForceMeshUpdate();
    Check("target heading is bounded",!heading.isTextTruncated && heading.textInfo.lineCount<=2,new {heading.text,lines=heading.textInfo.lineCount,heading.isTextTruncated});
    await Snap("target-preview",1280,720);
    await Snap("target-preview",1024,768);
    await Snap("target-preview",1920,1080);
    await Snap("target-preview",1440,900);
    type.GetMethod("Back",flags).Invoke(hud,null); await Frames(3); Check("cancel remains pure",submits==0 && initial==Snapshot());
    Targets(); await Frames(3); Pointer(0); await Frames(3); int mp=actor.Mp; Pointer(0); await Frames(2);
    Check("second pointer commits once",submits==1);
    Check("MP charged once",skill!=null && actor.Mp==mp-skill.MpCost,new{beforeMp=mp,afterMp=actor.Mp,skill=skill==null?null:skill.Id});
    Pointer(0); Check("duplicate commit rejected",submits==1);
    await Frames(180);
    app.EnterTown(); await Frames(20); app.State.Gold=99999999;
    app.State.Flags.Add(Abyss.Logic.Game.GameFlow.FlagCleared);
    app.State.Flags.Add(Abyss.Logic.Game.GameFlow.BossFlag(Abyss.Logic.Game.GameFlow.MainChapters+1));
    app.EnterTown(); await Snap("completed-objective-stress",1280,720);
    Check("completed objective",Abyss.Logic.Game.ExpeditionReadiness.Evaluate(app.DB,app.State).ObjectiveText.Contains("완료"));
    System.IO.File.WriteAllText(System.IO.Path.Combine(outDir,"resume-targeting-acceptance.json"),Newtonsoft.Json.JsonConvert.SerializeObject(new{status=checks.Count>0?"complete":"failed",fixture="seeded editor runtime; isolated saves; supported five-enemy pagination stress",checks},Newtonsoft.Json.Formatting.Indented));
 } catch(System.Exception e) {System.IO.File.WriteAllText(System.IO.Path.Combine(outDir,"resume-targeting-acceptance.json"),Newtonsoft.Json.JsonConvert.SerializeObject(new{status="failed",error=e.ToString(),checks},Newtonsoft.Json.Formatting.Indented));}
}
_ = Run(); return "delta acceptance started";
