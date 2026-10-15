// External QA code evaluated by Unity Pipeline (unity command eval_file); never included in the shipped player.
// R5-FIX checks in PLAY MODE: boss battle in manual control (review entry point, L13 party), then the phase / enemy-ultimate call-out is driven
// directly through BattleHUD.CutIn / HideCutIn / SkillBanner while the layout is switched between the full (1280x720) and compact (2400x1080) sizes.
// Output: docs/verification/floor1/r5fix/r5_checks.json, progress_r5.log, *.png. Finished when r5fix/DONE exists.
// Run: unity command editor_play, then `unity command --timeout 120 eval_file --file Tools/R5CheckCallout.eval.cs`.
var BF = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var outDir = System.IO.Path.Combine(System.IO.Directory.GetParent(Application.dataPath).FullName, "docs", "verification", "floor1", "r5fix");
System.IO.Directory.CreateDirectory(outDir);
var clock = System.Diagnostics.Stopwatch.StartNew();
double Now() => clock.Elapsed.TotalSeconds;
System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "progress_r5.log"), "");
void P(string m) { System.IO.File.AppendAllText(System.IO.Path.Combine(outDir, "progress_r5.log"), "[" + Now().ToString("F1") + "s] " + m + "\n"); }
var checks = new List<Dictionary<string, object>>();
var infos = new List<string>();
void Check(string name, bool ok, string detail = "") { checks.Add(new Dictionary<string, object> { ["name"] = name, ["passed"] = ok, ["detail"] = detail }); P((ok ? "PASS " : "FAIL ") + name + " " + detail); }
void Info(string s) { infos.Add(s); P("info " + s); }
async System.Threading.Tasks.Task Frames(int n) { int end = Time.frameCount + n; double dl = Now() + 30; while (Time.frameCount < end) { if (Now() > dl) throw new TimeoutException("frames stopped"); await System.Threading.Tasks.Task.Yield(); } }
async System.Threading.Tasks.Task Wait(double s) { double end = Now() + s; while (Now() < end) await System.Threading.Tasks.Task.Yield(); }
async System.Threading.Tasks.Task Shot(string name) { ScreenCapture.CaptureScreenshot(System.IO.Path.Combine(outDir, name + ".png")); await Frames(5); P("shot " + name + " " + Screen.width + "x" + Screen.height); }
void Resize(int width, int height)
{
    var assembly = typeof(UnityEditor.Editor).Assembly;
    var sizesType = assembly.GetType("UnityEditor.GameViewSizes");
    var singleton = typeof(UnityEditor.ScriptableSingleton<>).MakeGenericType(sizesType);
    var sizes = singleton.GetProperty("instance").GetValue(null);
    var getGroup = sizesType.GetMethod("GetGroup");
    var group = getGroup.Invoke(sizes, new[] { Enum.Parse(getGroup.GetParameters()[0].ParameterType, "Standalone") });
    var sizeType = assembly.GetType("UnityEditor.GameViewSize");
    var kind = assembly.GetType("UnityEditor.GameViewSizeType");
    var ctor = sizeType.GetConstructor(BF, null, new[] { kind, typeof(int), typeof(int), typeof(string) }, null);
    var size = ctor.Invoke(new object[] { Enum.ToObject(kind, 1), width, height, "R5 QA " + width + "x" + height });
    int index = (int)group.GetType().GetMethod("GetTotalCount").Invoke(group, null);
    group.GetType().GetMethod("AddCustomSize").Invoke(group, new[] { size });
    var viewType = assembly.GetType("UnityEditor.GameView");
    // The editor can hold several Game views: set every one, the focused one drives Screen.width / height.
    foreach (var window in Resources.FindObjectsOfTypeAll(viewType)) viewType.GetProperty("selectedSizeIndex", BF).SetValue(window, index);
}
async System.Threading.Tasks.Task SetSize(int w, int h)
{
    Resize(w, h);
    double dl = Now() + 6;
    while ((Screen.width != w || Screen.height != h) && Now() < dl) await System.Threading.Tasks.Task.Yield();
    await Frames(12);
    P("size now " + Screen.width + "x" + Screen.height + " compact=" + Abyss.UI.UIRoot.Compact);
}

var ht = typeof(Abyss.UI.Battle.BattleHUD);
Abyss.UI.Battle.BattleHUD hud = null;
T Fld<T>(string name) => (T)ht.GetField(name, BF).GetValue(hud);
void SetFld(string name, object v) => ht.GetField(name, BF).SetValue(hud, v);
System.Collections.IDictionary Cards() => Fld<System.Collections.IDictionary>("_cards");
object CardF(object card, string name) => card.GetType().GetField(name).GetValue(card);
RectTransform RootRt() => Fld<RectTransform>("_root");
Rect CanvasRectOf(RectTransform rt)
{
    var root = RootRt(); var c = new Vector3[4]; rt.GetWorldCorners(c);
    var a = root.InverseTransformPoint(c[0]); var b = root.InverseTransformPoint(c[2]); var mn = root.rect.min;
    return Rect.MinMaxRect(a.x - mn.x, a.y - mn.y, b.x - mn.x, b.y - mn.y);
}
RectTransform CutRt() => Fld<RectTransform>("_cutin");
bool CutVisible() => CutRt().gameObject.activeInHierarchy;

// Verifies the visible call-out against everything it must not cover; returns the number of violations.
int Verify(string label)
{
    var fails = new List<string>();
    var root = RootRt(); float height = root.rect.height, width = root.rect.width;
    var cut = CutRt();
    if (!CutVisible())
    {
        Info(label + ": call-out not visible (suppressed or hidden); size=" + Fld<Vector2>("_coSize") + " blockers=" + string.Join(" ", Fld<List<Rect>>("_coBlockers").Select(b => b.ToString("F0"))));
        return 0;
    }
    Rect co = CanvasRectOf(cut);
    if (co.yMin < height * (2f / 3f) - 0.5f) fails.Add("below the top third " + co);
    if (co.xMin < 0 || co.xMax > width) fails.Add("outside the screen " + co);
    foreach (System.Collections.DictionaryEntry kv in Cards())
    {
        var card = kv.Value; var unit = (Abyss.Runtime.Battle.BattleDisplayUnit)CardF(card, "Unit");
        bool party = (bool)CardF(card, "Party");
        var cardRoot = (RectTransform)CardF(card, "Root");
        if (party)
        {
            if (unit.Alive && hud.TryGetUnitRect(unit.Id, out var body) && body.Overlaps(co)) fails.Add("living hero body " + unit.Id + " " + body);
            if (cardRoot.gameObject.activeInHierarchy && CanvasRectOf(cardRoot).Overlaps(co)) fails.Add("party plate " + unit.Id);
            foreach (var chipName in new[] { "ThreatChip", "Pill" })
            {
                var chip = CardF(card, chipName);
                var rt = chip == null ? null : ((Abyss.UI.UISlantPlate)chip).Rect;
                if (rt != null && rt.gameObject.activeInHierarchy && CanvasRectOf(rt).Overlaps(co)) fails.Add("party " + chipName + " " + unit.Id);
            }
        }
        else
        {
            if (cardRoot.gameObject.activeInHierarchy && CanvasRectOf(cardRoot).Overlaps(co)) fails.Add("enemy tag " + unit.Id + " " + CanvasRectOf(cardRoot));
            var pill = (Abyss.UI.UISlantPlate)CardF(card, "Pill");
            if (pill != null && pill.gameObject.activeInHierarchy && CanvasRectOf(pill.Rect).Overlaps(co)) fails.Add("enemy pill " + unit.Id);
        }
    }
    foreach (var name in new[] { "_top", "_logPanel", "_enemyBanner", "_autoBanner", "_menu", "_banner" })
    {
        var rt = Fld<RectTransform>(name);
        if (rt != null && rt.gameObject.activeInHierarchy && CanvasRectOf(rt).Overlaps(co)) fails.Add("HUD " + name + " " + CanvasRectOf(rt));
    }
    foreach (var name in new[] { "_autoButton", "_speedButton" })
    {
        var b = (Component)ht.GetField(name, BF).GetValue(hud);
        if (b != null && b.gameObject.activeInHierarchy && CanvasRectOf((RectTransform)b.transform).Overlaps(co)) fails.Add("HUD " + name);
    }
    var chain = Fld<Abyss.UI.UISlantPlate>("_chainPlate");
    if (chain != null && chain.gameObject.activeInHierarchy && CanvasRectOf(chain.Rect).Overlaps(co)) fails.Add("chain plate");
    Check(label + " | call-out " + co.ToString("F0") + " clear of bodies/plates/chips/top controls/ribbon/tags/pills", fails.Count == 0, string.Join("; ", fails));
    return fails.Count;
}

Abyss.Runtime.GameApp app = null;
// QA isolation: park the party behind the camera (their projected bounds vanish) so the seat search is tested without hero bodies in the way.
var savedPos = new Dictionary<Abyss.Runtime.Battle.BattleDisplayUnit, Vector3>();
List<Abyss.Runtime.Battle.BattleDisplayUnit> Heroes()
{
    var list = new List<Abyss.Runtime.Battle.BattleDisplayUnit>();
    foreach (System.Collections.DictionaryEntry kv in Cards())
    {
        var u = (Abyss.Runtime.Battle.BattleDisplayUnit)CardF(kv.Value, "Unit");
        if ((bool)CardF(kv.Value, "Party") && u.Alive && u.Model != null) list.Add(u);
    }
    return list;
}
// Moves a model onto the floor under the given screen fraction (0 bottom .. 1 top) of the camera view; returns false when that ray misses the floor.
bool PutAt(Abyss.Runtime.Battle.BattleDisplayUnit unit, float fracX, float fracY)
{
    var cam = Fld<Camera>("_camera"); var pr = cam.pixelRect;
    var ray = cam.ScreenPointToRay(new Vector3(pr.xMin + pr.width * fracX, pr.yMin + pr.height * fracY, 0f));
    if (!new Plane(Vector3.up, unit.Model.transform.position).Raycast(ray, out float dist)) return false;
    unit.Model.transform.position = ray.GetPoint(dist);
    return true;
}
async System.Threading.Tasks.Task HeroesAway(Abyss.Runtime.Battle.BattleDisplayUnit except = null)
{
    var cam = Fld<Camera>("_camera");
    foreach (var u in Heroes())
    {
        if (u == except) continue;
        if (!savedPos.ContainsKey(u)) savedPos[u] = u.Model.transform.position;
        u.Model.transform.position = cam.transform.position - cam.transform.forward * 60f;
    }
    await Frames(4);
}
async System.Threading.Tasks.Task HeroesBack()
{
    foreach (var kv in savedPos) if (kv.Key.Model != null) kv.Key.Model.transform.position = kv.Value;
    savedPos.Clear();
    await Frames(4);
}
Rect CoRect() => Fld<Rect>("_coRect");
bool CoShown() => Fld<bool>("_coShown");
bool CoRequested() => Fld<bool>("_coRequested");

string shortSub = "시스템 점검 중 — 모두 주의하라!";
string twoLineSub = "어둠 속에서 수천 마리의 박쥐가 깨어난다. 지하철 선로 전체가 군주의 날갯짓으로 흔들리고, 천장에서는 낡은 조명이 하나둘 꺼지기 시작한다.";
string longSub = twoLineSub + " 이제 도망칠 곳은 어디에도 없다. 승객들의 비명이 터널을 가득 채우고 마지막 열차의 불빛이 사라진다.";
var variants = new (string name, string text)[] { ("empty", ""), ("short", shortSub), ("two-line", twoLineSub), ("overlong", longSub) };
string bossTitle = "지하철 박쥐 군주 · PHASE 2";

async System.Threading.Tasks.Task Run()
{
    string failure = null;
    try
    {
        Application.runInBackground = true;
        app = Abyss.Runtime.GameApp.Instance;
        if (app == null) throw new Exception("Play mode game missing");
        var db = app.DB;
        var state = Abyss.Logic.Game.GameState.NewGame(db, Abyss.Logic.Difficulty.Normal);
        state.Flags.Remove(Abyss.Logic.Game.GameFlow.FlagProloguePending);
        foreach (string tip in new[] { "first_battle", "first_foe", "first_tp_full", "first_trap", "first_town" }) state.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag(tip));
        foreach (var h in state.Party) { h.Level = 13; h.Xp = 0; h.Hp = -1; h.Mp = -1; }
        state.FloorIndex = 2; state.Location = Abyss.Logic.Game.GameLocation.Dungeon; state.DeepestFloor = 2;
        state.Repair(db);
        app.BeginReview(state, 2);
        await SetSize(1280, 720);
        await Wait(3);
        var start = typeof(Abyss.Logic.Dungeon.DungeonRun).GetMethod("StartBattle", BF);
        var req = (Abyss.Logic.Dungeon.DungeonBattleRequest)start.Invoke(app.Dungeon, new object[] { Abyss.Logic.BattleKind.Boss, new List<string> { "subway_bat_lord" }, state.Position, state.Position, "", 1f });
        app.Preferences.AutoBattle = false; app.Preferences.BattleSpeed = 1f;
        app.BeginBattle(req.Setup);
        double t0 = Now();
        // ---- boss tag at battle start -----------------------------------------------------------------
        foreach (var at in new[] { 0.5, 1.6, 3.2 })
        {
            while (Now() - t0 < at) await System.Threading.Tasks.Task.Yield();
            hud = UnityEngine.Object.FindFirstObjectByType<Abyss.UI.Battle.BattleHUD>();
            await Shot("boss_tag_1280x720_" + at.ToString("0.0") + "s");
            if (hud == null) { Check("hud exists at " + at, false); continue; }
            foreach (System.Collections.DictionaryEntry kv in Cards())
            {
                var card = kv.Value; var unit = (Abyss.Runtime.Battle.BattleDisplayUnit)CardF(card, "Unit");
                if (!unit.Boss) continue;
                var lvl = CardF(card, "Level").ToString();
                var nm = (TMPro.TMP_Text)CardF(card, "Name"); var ic = (TMPro.TMP_Text)CardF(card, "IconLabel");
                var tag = ((RectTransform)CardF(card, "Root"));
                bool named = lvl == "Icon" ? ic.gameObject.activeInHierarchy && ic.textInfo.characterCount > 0 && ic.text == unit.Name
                    : (lvl == "Compact" || lvl == "Full") ? nm.gameObject.activeInHierarchy && nm.textInfo.characterCount > 0 && nm.text == unit.Name : true;
                Check("boss tag shows its full name at " + at + "s", named && tag.gameObject.activeInHierarchy, "level=" + lvl + " name='" + unit.Name + "' nameChars=" + nm.textInfo.characterCount + " iconChars=" + ic.textInfo.characterCount);
            }
        }
        hud = UnityEngine.Object.FindFirstObjectByType<Abyss.UI.Battle.BattleHUD>();
        await Wait(0.8);
        // ---- forced icon / edge tag labels (the regression: TMP dropped the whole line when it was taller than the rect) --------------
        {
            var tagLevel = ht.GetNestedType("TagLevel", BF);
            var setLevel = ht.GetMethod("SetLevel", BF);
            foreach (System.Collections.DictionaryEntry kv in Cards())
            {
                var card = kv.Value; var unit = (Abyss.Runtime.Battle.BattleDisplayUnit)CardF(card, "Unit");
                if (!unit.Boss) continue;
                var ic = (TMPro.TMP_Text)CardF(card, "IconLabel");
                foreach (var (lv, nameOf) in new[] { (2, "icon"), (3, "edge") })
                {
                    setLevel.Invoke(hud, new object[] { card, Enum.ToObject(tagLevel, lv), new Vector2(lv == 2 ? 206f : 112f, 48f), new Rect(100, 700, 206, 48), 100 });
                    Canvas.ForceUpdateCanvases(); ic.ForceMeshUpdate();
                    Check("boss " + nameOf + "-level label renders glyphs", ic.gameObject.activeInHierarchy && ic.textInfo.characterCount > 0 && ic.textInfo.meshInfo[0].vertexCount > 0,
                        "text='" + ic.text + "' chars=" + ic.textInfo.characterCount + " rectH=" + ic.rectTransform.rect.height + " prefH=" + ic.preferredHeight + " fs=" + ic.fontSize);
                }
            }
            await Frames(4);
        }
        // ---- call-out sweeps ----------------------------------------------------------------------------
        foreach (bool isolated in new[] { true, false })
        foreach (var (layoutName, w, h) in new[] { ("full", 1280, 720), ("compact", 2400, 1080) })
        {
            await SetSize(w, h);
            hud = UnityEngine.Object.FindFirstObjectByType<Abyss.UI.Battle.BattleHUD>();
            Check(layoutName + " layout reached", Abyss.UI.UIRoot.Compact == (layoutName == "compact"), "compact=" + Abyss.UI.UIRoot.Compact + " root=" + RootRt().rect.size);
            if (isolated) await HeroesAway(); else await HeroesBack();
            foreach (bool ribbon in new[] { false, true })
                foreach (var (vname, text) in variants)
                {
                    string label = (isolated ? "isolated " : "natural ") + layoutName + " / sub=" + vname + " / ribbon=" + (ribbon ? "on" : "off");
                    if (ribbon) hud.SkillBanner("불꽃 난무", new Color(1f, 0.55f, 0.2f)); else hud.HideSkillBanner();
                    hud.CutIn(bossTitle, text);
                    await Wait(0.6);
                    int nv = Verify(label);
                    var co = CutRt();
                    bool sized = !CoShown() || (Mathf.Abs(co.sizeDelta.x - Fld<Vector2>("_coSize").x) < 0.01f && Mathf.Abs(co.sizeDelta.y - Fld<Vector2>("_coSize").y) < 0.01f);
                    Check(label + " | plate size follows its content", sized, co.sizeDelta.ToString() + " seat=" + CoRect());
                    if (!ribbon && isolated) Check(label + " | seated without a ribbon", CoShown() && CutVisible(), "shown=" + CoShown());
                    else Info(label + ": shown=" + CoShown() + " rect=" + (CoShown() ? CoRect().ToString("F0") : "-"));
                    bool shot = isolated && ((vname == "two-line" && !ribbon) || (vname == "empty" && ribbon) || (vname == "short" && !ribbon));
                    if (shot) await Shot("callout_" + layoutName + "_" + vname + (ribbon ? "_ribbon" : ""));
                    hud.HideCutIn();
                    await Frames(3);
                    Check(label + " | HideCutIn hides it", !CutVisible() && !CoShown() && !CoRequested());
                }
            hud.HideSkillBanner();
            await HeroesBack();
        }
        // ---- pills: mark the boss while the call-out is up -------------------------------------------------
        {
            await SetSize(1280, 720);
            await HeroesAway();
            var tm = ht.GetNestedType("TargetMark", BF);
            var mark = Activator.CreateInstance(tm);
            foreach (System.Collections.DictionaryEntry kv in Cards())
            {
                var unit = (Abyss.Runtime.Battle.BattleDisplayUnit)CardF(kv.Value, "Unit");
                if (unit.Boss) { tm.GetField("Id").SetValue(mark, unit.Id); tm.GetField("Pill").SetValue(mark, "예상 12,345"); }
            }
            var list = Activator.CreateInstance(typeof(List<>).MakeGenericType(tm));
            list.GetType().GetMethod("Add").Invoke(list, new[] { mark });
            ht.GetMethod("SetMarks", BF).Invoke(hud, new[] { list });
            string PillState()
            {
                var sbp = new System.Text.StringBuilder();
                foreach (System.Collections.DictionaryEntry kv in Cards())
                {
                    if ((bool)CardF(kv.Value, "Party")) continue;
                    var p = (Abyss.UI.UISlantPlate)CardF(kv.Value, "Pill");
                    sbp.Append(((Abyss.Runtime.Battle.BattleDisplayUnit)CardF(kv.Value, "Unit")).Id + " marked=" + CardF(kv.Value, "Marked") + " pillOn=" + CardF(kv.Value, "PillOn") + " hasRect=" + CardF(kv.Value, "HasRect") + " onScreen=" + CardF(kv.Value, "OnScreen") + " level=" + CardF(kv.Value, "Level") + " pillActive=" + p.gameObject.activeInHierarchy + "; ");
                }
                return sbp.ToString();
            }
            Abyss.Runtime.Battle.BattleDisplayUnit bossUnit = null;
            foreach (System.Collections.DictionaryEntry kv in Cards()) { var u = (Abyss.Runtime.Battle.BattleDisplayUnit)CardF(kv.Value, "Unit"); if (u.Boss) bossUnit = u; }
            var bossOld = bossUnit.Model.transform.position;
            // The boss stands under the call-out's seat (its head is where the pill wants to go); keep the first spot where the baseline shows a pill.
            foreach (float fy in new[] { 0.72f, 0.68f, 0.64f, 0.6f, 0.56f })
            {
                bool bossPut = PutAt(bossUnit, 0.5f, fy);
                await Wait(0.35);
                Info("boss at y=" + fy + " put=" + bossPut + " pill baseline (no call-out): " + PillState());
                if (PillState().Contains("pillActive=True")) break;
            }
            Check("pill test setup: marked boss shows a pill before the call-out", PillState().Contains("pillActive=True"), PillState());
            hud.CutIn(bossTitle, twoLineSub);
            await Wait(0.6);
            bool pillOn = PillState().Contains("pillActive=True");
            Check("marked boss shows its estimate pill with the call-out up", pillOn && CutVisible(), PillState());
            Verify("full / marked boss + pill");
            await Shot("callout_full_pill");
            bossUnit.Model.transform.position = bossOld;
            hud.HideCutIn();
            ht.GetMethod("ClearMarks", BF).Invoke(hud, null);
            await HeroesBack();
        }
        // ---- resize while visible --------------------------------------------------------------------------
        {
            await SetSize(1280, 720);
            await HeroesAway();
            hud.CutIn(bossTitle, twoLineSub);
            await Wait(0.5);
            Verify("resize: full before");
            await SetSize(2400, 1080);
            await Wait(0.3);
            var co = CutRt();
            Check("resize full->compact: call-out re-sized and re-seated", CoShown() && Mathf.Abs(co.sizeDelta.x - Fld<Vector2>("_coSize").x) < 0.01f && Fld<Vector2>("_coSize").x <= 760.01f, "size=" + co.sizeDelta + " seat=" + CoRect());
            Verify("resize: compact after");
            await SetSize(1280, 720);
            await Wait(0.3);
            Check("resize compact->full: call-out re-sized and re-seated", CoShown() && Fld<Vector2>("_coSize").x > 760.01f, "size=" + CutRt().sizeDelta);
            Verify("resize: full again");
            // ribbon toggled while the call-out is up
            hud.SkillBanner("불꽃 난무", new Color(1f, 0.55f, 0.2f));
            await Wait(0.5);
            Verify("ribbon appears while call-out up");
            var withRibbon = CoShown() ? CoRect() : default;
            hud.HideSkillBanner();
            await Wait(0.3);
            Verify("ribbon disappears while call-out up");
            Info("ribbon on seat=" + (CoShown() ? withRibbon.ToString("F0") : "suppressed") + " ; ribbon off seat=" + (CoShown() ? CoRect().ToString("F0") : "suppressed"));
            hud.HideCutIn();
            await HeroesBack();
        }
        // ---- a hero walks into the call-out's seat (full: nowhere to go -> suppressed; compact: it moves aside) --------------------
        foreach (var (layoutName, w, h) in new[] { ("full", 1280, 720), ("compact", 2400, 1080) })
        {
            Abyss.Runtime.Battle.BattleDisplayUnit hero = Heroes()[0];
            await HeroesAway(hero);
            await SetSize(w, h);
            hud.CutIn(bossTitle, twoLineSub);
            await Wait(0.5);
            var before = CoShown() ? CoRect() : default;
            Check("hero test (" + layoutName + ") pre-condition: seated", CoShown() && CutVisible(), "seat=" + before);
            var oldPos = hero.Model.transform.position;
            bool put = PutAt(hero, 0.5f, 0.6f);
            await Frames(6);
            hud.TryGetUnitRect(hero.Id, out var body);
            Check("hero test (" + layoutName + ") setup: hero stands in the middle of the view with a projected body", put && body.width > 1f, "put=" + put + " body=" + body);
            Info("hero moved to body " + body.ToString("F0") + " ; seat before " + before.ToString("F0") + " after " + (CoShown() ? CoRect().ToString("F0") : "suppressed"));
            Check("hero test (" + layoutName + "): body reaching the old seat evicts the call-out from it", body.Overlaps(before) && (!CoShown() || !CoRect().Overlaps(body)), "body=" + body + " oldSeat=" + before + " newSeat=" + (CoShown() ? CoRect().ToString() : "suppressed"));
            if (layoutName == "compact") Check("hero test (compact): the call-out relocated sideways instead of vanishing", CoShown() && !Mathf.Approximately(CoRect().x, before.x), "newSeat=" + (CoShown() ? CoRect().ToString() : "suppressed"));
            Verify("hero in the top third (" + layoutName + ")");
            if (layoutName == "compact") await Shot("callout_compact_hero_in_the_way");
            hero.Model.transform.position = oldPos;
            await Frames(6);
            hud.HideCutIn();
            await HeroesBack();
        }
        // ---- no safe slot -> suppressed, retried, never resurrected -------------------------------------------
        {
            float topH = Fld<float>("_topH");
            await SetSize(1280, 720);
            await HeroesAway();
            hud.CutIn(bossTitle, twoLineSub);
            await Wait(0.4);
            Check("pre-condition: seated", CoShown() && CutVisible());
            SetFld("_topH", RootRt().rect.height * 0.9f);        // QA: the top band swallows the whole top third -> no safe seat
            await Frames(6);
            Check("no safe seat: plate suppressed, still requested", !CutVisible() && !CoShown() && CoRequested());
            SetFld("_topH", topH);
            await Wait(0.5);
            Check("suppressed call-out retries while requested and reappears", CoShown() && CutVisible());
            Verify("after retry");
            SetFld("_topH", RootRt().rect.height * 0.9f);
            await Frames(6);
            Check("suppressed again", !CutVisible() && CoRequested());
            hud.HideCutIn();
            SetFld("_topH", topH);
            await Wait(0.6);
            Check("HideCutIn while suppressed: nothing resurrects it", !CutVisible() && !CoShown() && !CoRequested());
            // Lock() while suppressed
            hud.CutIn(bossTitle, shortSub);
            await Wait(0.4);
            SetFld("_topH", RootRt().rect.height * 0.9f);
            await Frames(6);
            hud.Lock();
            SetFld("_topH", topH);
            await Wait(0.6);
            Check("Lock while suppressed: nothing resurrects it", !CutVisible() && !CoShown() && !CoRequested());
            await Shot("after_lock_1280x720");
            await HeroesBack();
        }
    }
    catch (Exception e) { failure = e.GetType().Name + ": " + e.Message; P("FAILED " + e); }
    int failed = checks.Count(c => !(bool)c["passed"]);
    System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "r5_checks.json"), Newtonsoft.Json.JsonConvert.SerializeObject(new { status = failure == null && failed == 0 ? "pass" : "fail", failure, total = checks.Count, failed, checks, infos }, Newtonsoft.Json.Formatting.Indented));
    System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "DONE"), failure == null && failed == 0 ? "pass" : "fail");
}
if (System.IO.File.Exists(System.IO.Path.Combine(outDir, "DONE"))) System.IO.File.Delete(System.IO.Path.Combine(outDir, "DONE"));
_ = Run();
return "r5 checks started; finished when docs/verification/floor1/r5fix/DONE exists";
