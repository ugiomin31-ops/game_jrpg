using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Abyss.Runtime;
using Abyss.UI;
using Abyss.UI.Battle;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;
using Newtonsoft.Json;

public static class Pr6CompactBoundsEval
{
    static readonly BindingFlags Flags = BindingFlags.Instance | BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
    static readonly List<object> Checks = new List<object>();
    static void Check(string name, bool passed, object detail = null) => Checks.Add(new { name, passed, detail });
    static async Task Frames(int count)
    {
        int end = Time.frameCount + count;
        var deadline = DateTime.UtcNow.AddSeconds(6);
        while (Time.frameCount < end)
        {
            if (DateTime.UtcNow > deadline) throw new TimeoutException("Editor frames stopped during compact bounds evaluation");
            await Task.Yield();
        }
    }
    static void Resize(int width, int height)
    {
        var asm = typeof(Editor).Assembly;
        var sizesType = asm.GetType("UnityEditor.GameViewSizes");
        var singleton = typeof(ScriptableSingleton<>).MakeGenericType(sizesType);
        var sizes = singleton.GetProperty("instance").GetValue(null);
        var getGroup = sizesType.GetMethod("GetGroup");
        var group = getGroup.Invoke(sizes, new[] { Enum.Parse(getGroup.GetParameters()[0].ParameterType, "Standalone") });
        var sizeType = asm.GetType("UnityEditor.GameViewSize");
        var kind = asm.GetType("UnityEditor.GameViewSizeType");
        var ctor = sizeType.GetConstructor(Flags, null, new[] { kind, typeof(int), typeof(int), typeof(string) }, null);
        var size = ctor.Invoke(new object[] { Enum.ToObject(kind, 1), width, height, "PR6 compact bounds" });
        int index = (int)group.GetType().GetMethod("GetTotalCount").Invoke(group, null);
        group.GetType().GetMethod("AddCustomSize").Invoke(group, new[] { size });
        var viewType = asm.GetType("UnityEditor.GameView");
        var view = EditorWindow.GetWindow(viewType);
        viewType.GetProperty("selectedSizeIndex", Flags).SetValue(view, index);
    }
    static Rect ScreenRect(RectTransform rt)
    {
        var corners = new Vector3[4];
        rt.GetWorldCorners(corners);
        var canvas = rt.GetComponentInParent<Canvas>();
        Camera cam = canvas != null && canvas.renderMode != RenderMode.ScreenSpaceOverlay ? canvas.worldCamera : null;
        Vector2 a = RectTransformUtility.WorldToScreenPoint(cam, corners[0]);
        Vector2 b = RectTransformUtility.WorldToScreenPoint(cam, corners[2]);
        return Rect.MinMaxRect(a.x, a.y, b.x, b.y);
    }
    static object RectData(Rect r) => new { left = r.xMin, bottom = r.yMin, right = r.xMax, top = r.yMax, width = r.width, height = r.height };
    static int ButtonCount(BattleHUD hud)
        => ((List<UIButton>)typeof(BattleHUD).GetField("_buttons", Flags).GetValue(hud)).Count;
    static RectTransform Rt(UIButton button) => (RectTransform)button.transform;

    public static async Task<string> Execute()
    {
        Application.runInBackground = true;
        Checks.Clear();
        var app = GameApp.Instance;
        if (app == null || app.UI == null || app.UI.Content == null || app.DB == null)
            throw new InvalidOperationException("Editor play runtime is not initialized: expected GameApp, UI.Content and GameDB");

        var begin = typeof(BattleHUD).GetMethod("BeginChoices", Flags);
        var add = typeof(BattleHUD).GetMethod("Add", Flags);
        var render = typeof(BattleHUD).GetMethod("Render", Flags);
        var page = typeof(BattleHUD).GetMethod("Page", Flags);

        var frames = new[] { new[] { 915, 412 }, new[] { 1280, 720 }, new[] { 1024, 768 }, new[] { 1920, 1080 }, new[] { 1440, 900 } };
        foreach (var size in frames)
        {
            Resize(size[0], size[1]);
            await Frames(2);
            var uiRoot = UIRoot.Instance;
            if (uiRoot == null) throw new InvalidOperationException("UIRoot.Instance unavailable after GameView resize");
            typeof(UIRoot).GetMethod("UpdateSafeArea", Flags).Invoke(uiRoot, null);
            Canvas.ForceUpdateCanvases();
            var host = new GameObject("PR6 compact bounds isolated fixture", typeof(RectTransform), typeof(BattleHUD));
            host.transform.SetParent(app.UI.Content, false);
            var hud = host.GetComponent<BattleHUD>();
            int autoClicks = 0, speedClicks = 0;
            hud.Initialize(app.UI.Content, Camera.main, app.DB, _ => { }, () => { }, _ => { });
            hud.EnableSpeedToggle("속도 1x", () => speedClicks++);
            var auto = (UIButton)typeof(BattleHUD).GetField("_autoButton", Flags).GetValue(hud);
            var speed = (UIButton)typeof(BattleHUD).GetField("_speedButton", Flags).GetValue(hud);
            var menu = (RectTransform)typeof(BattleHUD).GetField("_menu", Flags).GetValue(hud);
            typeof(BattleHUD).GetField("_toggleAuto", Flags).SetValue(hud, (Action)(() => autoClicks++));
            bool compact = (bool)typeof(BattleHUD).GetProperty("Compact", Flags).GetValue(null);
            int perPage = (int)typeof(BattleHUD).GetProperty("PerPage", Flags).GetValue(null);
            begin.Invoke(hud, new object[] { "격리된 compact bounds QA", null });
            for (int i = 0; i < 8; i++) add.Invoke(hud, new object[] { "시험 선택 " + (i + 1), "Bounds fixture", true, null, (Action)(() => { }), null, null });
            render.Invoke(hud, null);
            Canvas.ForceUpdateCanvases();
            var autoRect = ScreenRect(Rt(auto));
            var speedRect = ScreenRect(Rt(speed));
            var menuRect = ScreenRect(menu);
            bool noTopOverlap = !autoRect.Overlaps(speedRect) && !autoRect.Overlaps(menuRect) && !speedRect.Overlaps(menuRect);
            bool minTarget = autoRect.height >= 44f && speedRect.height >= 44f;
            int firstPageButtons = ButtonCount(hud) - 3;
            bool expectedCompact = size[0] == 915 && size[1] == 412;
            Check("actual GameView resolution " + size[0] + "x" + size[1], Screen.width == size[0] && Screen.height == size[1], new { width = Screen.width, height = Screen.height, compact, perPage, touchSupported = UITouch.Supported, mobilePlatform = Application.isMobilePlatform });
            Check("auto, speed and menu bounds do not overlap " + size[0] + "x" + size[1], noTopOverlap, new { auto = RectData(autoRect), speed = RectData(speedRect), menu = RectData(menuRect) });
            Check("auto and speed are at least 44 screen pixels " + size[0] + "x" + size[1], minTarget, new { autoHeightPx = autoRect.height, speedHeightPx = speedRect.height });
            if (expectedCompact)
            {
                Check("915x412 uses compact three-choice page", compact && perPage == 3 && firstPageButtons == 3, new { compact, perPage, firstPageButtons });
                page.Invoke(hud, new object[] { 1 });
                Canvas.ForceUpdateCanvases();
                int secondPageButtons = ButtonCount(hud) - 3;
                Check("compact choices remain reachable on page two", secondPageButtons == 3, new { secondPageChoiceButtons = secondPageButtons, totalChoices = 8, pageSize = perPage });
                var next = ((List<UIButton>)typeof(BattleHUD).GetField("_buttons", Flags).GetValue(hud)).Last();
                Check("compact next-page control is enabled", next.Interactable, next.Label.text);
                page.Invoke(hud, new object[] { 1 });
                int thirdPageButtons = ButtonCount(hud) - 3;
                var finalNext = ((List<UIButton>)typeof(BattleHUD).GetField("_buttons", Flags).GetValue(hud)).Last();
                Check("last compact page exposes remaining choices and disables next", thirdPageButtons == 2 && !finalNext.Interactable, new { thirdPageChoiceButtons = thirdPageButtons, totalChoices = 8, pageSize = perPage });
                page.Invoke(hud, new object[] { -1 });
                page.Invoke(hud, new object[] { -1 });
                auto.Click(); speed.Click();
                Check("auto and speed controls invoke their actions", autoClicks == 1 && speedClicks == 1, new { autoClicks, speedClicks });
                var shot = System.IO.Path.GetFullPath(System.IO.Path.Combine("docs/verification/pr6-improvements", "compact-bounds-915x412.png"));
                ScreenCapture.CaptureScreenshot(shot);
                await Frames(1);
            }
            else Check("noncompact page size remains touch four or desktop six " + size[0] + "x" + size[1], perPage == 4 || perPage == 6, new { compact, perPage });
            UnityEngine.Object.Destroy(host);
            await Frames(1);
        }
        string status = Checks.All(c => (bool)c.GetType().GetProperty("passed").GetValue(c)) ? "passed" : "failed";
        string report = JsonConvert.SerializeObject(new { status, requestedModel = "gpt-6-luna", requestedEffort = "high", fixture = "isolated BattleHUD parented to GameApp.UI.Content with dummy callbacks; no player input", checks = Checks }, Formatting.Indented);
        System.IO.File.WriteAllText("docs/verification/pr6-improvements/compact-bounds-acceptance.json", report);
        return status + ": " + Checks.Count + " checks";
    }
}
