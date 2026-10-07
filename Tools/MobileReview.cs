// Editor-only review runner, compiled ephemerally with Pipeline run_script.
// Input is queued through Touchscreen and routed by the real InputSystemUIInputModule.
// These checks emulate touch; they do not certify a physical Android/iOS device.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Abyss.Logic.Battle;
using Abyss.Logic.Dungeon;
using System.Threading.Tasks;
using Abyss.Logic;
using Abyss.Logic.Game;
using Abyss.Runtime;
using Abyss.UI;
using Newtonsoft.Json;
using UnityEditor;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.EnhancedTouch;
using UnityEngine.InputSystem.LowLevel;

public static class MobileReview
{
    static readonly List<object> Checks = new List<object>();
    static readonly List<string> Failures = new List<string>();
    static Touchscreen touch;
    static int finger;

    public static object Begin()
    {
        if (!Application.isPlaying) throw new InvalidOperationException("Enter Play mode first.");
        Directory.CreateDirectory("Review");
        File.WriteAllText("Review/mobile-review.json", "{\"status\":\"running\"}");
        _ = Run();
        return new { status = "running", output = "Review/mobile-review.json" };
    }

    static async Task Run()
    {
        Checks.Clear(); Failures.Clear();
        try
        {
            Application.runInBackground = true;
            InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
            touch = Touchscreen.current ?? InputSystem.AddDevice<Touchscreen>();
            EnhancedTouchSupport.Enable();
            int frame = Time.frameCount;
            await Frames(8);
            Check("Player loop advances", Time.frameCount > frame);
            var app = GameApp.Instance;
            app.Preferences.AutoBattle = false;
            app.NewGame(Difficulty.Normal);
            GameFlow.CompletePrologue(app.State);
            app.State.Flags.Add(GameFlow.TipFlag("first_town"));
            app.State.Flags.Add("biome_0_seen");
            app.EnterTown();
            await Frames(24);
            Check("Phone layout and touch device", UIRoot.Compact == ((float)Screen.width / Screen.height >= 1.85f) && UITouch.Supported);
            Capture("town");
            await Frames(4);
            var player = app.WorldRoot.GetComponentsInChildren<Abyss.Runtime.Art.CharacterModel>().First(x => x.ModelId == "warrior").transform;
            var origin = player.position;
            Vector2 start = new Vector2(Screen.width * .2f, Screen.height * .48f);
            BeginTouch(start);
            await Frames(3);
            MoveTouch(start + Vector2.right * 100);
            await Frames(24);
            Check("Touch stick moves town party", Vector3.Distance(origin, player.position) > .15f);
            EndTouch(start + Vector2.right * 100);
            await Frames(4);
            var stopped = player.position;
            await Frames(10);
            Check("Stick stops on release", Vector3.Distance(stopped, player.position) < .1f);

            await Tap(Find(app.DB.T("menu_inn")));
            await Frames(12);
            Check("Facility opens through touch", UIRoot.Instance.Screens.Count == 1);
            await Tap(Find(app.DB.T("inn_rest")));
            await Frames(12);
            Check("Purchase/rest asks for confirmation", UIRoot.Instance.Modals.Count == 1);
            Capture("confirmation"); await Frames(4);
            int gold = app.State.Gold;
            await Tap(Find("취소"));
            await Frames(16);
            Check("Cancel preserves gold", app.State.Gold == gold && UIRoot.Instance.Modals.Count == 0);
            UIRoot.Instance.Screens.Clear();
            await Frames(8);

            int accepted = 0;
            var modal = UIModal.Confirm(UIRoot.Instance.Modals, "입력 검증", "동일 입력으로 실행이 중복되지 않아야 합니다.", yes => { if (yes) accepted++; });
            var execute = Find("실행").GetComponent<UIButton>();
            execute.Click(); execute.Click();
            Check("Immediate duplicate submit rejected", accepted == 0);
            await Seconds(.5f);
            await Tap(Find("실행"));
            await Frames(16);
            Check("Confirmed action executes once", accepted == 1);

            app.Depart(0);
            await Frames(30);
            Check("Dungeon route opens", app.Screen == GameScreen.Dungeon);
            var facing = app.State.Facing;
            await Tap(Find("회전 ↻")); await Frames(20);
            Check("Dungeon turn button routes touch", app.State.Facing == GridPos.Rotate(facing, 1));
            await Tap(Find("지도")); await Frames(10);
            Check("Map opens by touch", UIRoot.Instance.Screens.Count == 1);
            UIRoot.Instance.Screens.Clear(); await Frames(6);
            Capture("dungeon");
            await Frames(4);
            foreach (int floor in new[] { 3, 6, 9 })
            {
                app.ReturnToTown();
                app.State.SetDeepestFloor(app.DB, floor);
                app.State.WarpsUnlocked.Add(floor);
                app.State.Flags.Add("biome_" + floor / 3 + "_seen");
                app.Depart(floor); await Frames(24);
                Check("Biome loads: " + app.DB.Floors[floor].Tileset, app.Screen == GameScreen.Dungeon);
                Capture(app.DB.Floors[floor].Tileset); await Frames(4);
            }
            app.ReturnToTown(); app.Depart(0); await Frames(24);
            var request = (DungeonBattleRequest)typeof(DungeonRun).GetMethod("StartBattle", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(app.Dungeon,
                new object[] { BattleKind.Random, new List<string> { "slime", "slime" }, app.State.Position, app.State.Position, "", 1f });
            app.State.Flags.Add(GameFlow.TipFlag("first_battle"));
            var setup = request.Setup;
            app.BeginBattle(setup);
            await Frames(90);
            Capture("battle");
            var auto = Find("자동전투 OFF");
            Check("AUTO target is at least 44 pixels tall", auto.rect.height * UIRoot.Instance.Canvas.scaleFactor >= 43.9f);
            await Tap(auto);
            await Frames(8);
            Check("AUTO touch persists preference", app.Battle.Auto && app.Preferences.AutoBattle);
            var battle = app.Battle;
            app.Preferences.BattleSpeed = 2f;
            int deadline = Time.frameCount + 2400;
            while (GameObject.Find("Battle result") == null && Time.frameCount < deadline) await Frames(12);
            Check("AUTO reaches battle result", GameObject.Find("Battle result") != null);
            Capture("battle-result");
            await Frames(4);
            Check("AUTO remains enabled after combat", app.Preferences.AutoBattle);
            await Seconds(.5f);
            await Tap(Find("모험 계속"));
            await Frames(30);
            Check("Result acknowledgement returns to dungeon", app.Screen == GameScreen.Dungeon);
            request = (DungeonBattleRequest)typeof(DungeonRun).GetMethod("StartBattle", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(app.Dungeon,
                new object[] { BattleKind.Random, new List<string> { "slime" }, app.State.Position, app.State.Position, "", 1f });
            app.BeginBattle(request.Setup);
            await Frames(20);
            Check("Next encounter inherits AUTO", app.Battle.Auto);

        }
        catch (Exception error) { Failures.Add(error.ToString()); }
        finally
        {
            if (touch != null) EndTouch(Vector2.zero);
            string report = JsonConvert.SerializeObject(new { status = "complete", unity = Application.unityVersion, width = Screen.width, height = Screen.height, frame = Time.frameCount, checks = Checks, failures = Failures }, Formatting.Indented);
            File.WriteAllText("Review/mobile-review.json", report);
            File.WriteAllText($"Review/mobile-review-{Screen.width}x{Screen.height}.json", report);
        }
    }

    static void Check(string name, bool passed)
    {
        Checks.Add(new { name, passed });
        if (!passed) Failures.Add(name);
    }
    static RectTransform Find(string text)
    {
        var button = UnityEngine.Object.FindObjectsByType<UIButton>(FindObjectsSortMode.None)
            .FirstOrDefault(b => b.gameObject.activeInHierarchy && b.Label != null && (b.Label.text == text || b.Label.text.StartsWith(text + "\n")));
        if (button != null) return (RectTransform)button.transform;
        return UnityEngine.Object.FindObjectsByType<TMPro.TextMeshProUGUI>(FindObjectsSortMode.None)
            .First(t => t.gameObject.activeInHierarchy && t.text == text && t.GetComponentInParent<UIList>() != null).rectTransform;
    }
    static async Task Tap(RectTransform rect)
    {
        Vector2 point = RectTransformUtility.WorldToScreenPoint(null, rect.TransformPoint(rect.rect.center));
        BeginTouch(point); await Frames(3); EndTouch(point); await Frames(3);
    }
    static void BeginTouch(Vector2 point)
    {
        finger++;
        InputSystem.QueueStateEvent(touch, new TouchState { touchId = finger, phase = UnityEngine.InputSystem.TouchPhase.Began, position = point });
    }
    static void MoveTouch(Vector2 point) => InputSystem.QueueStateEvent(touch, new TouchState { touchId = finger, phase = UnityEngine.InputSystem.TouchPhase.Moved, position = point });
    static void EndTouch(Vector2 point) => InputSystem.QueueStateEvent(touch, new TouchState { touchId = finger, phase = UnityEngine.InputSystem.TouchPhase.Ended, position = point });
    static void Capture(string name) => ScreenCapture.CaptureScreenshot($"Review/{name}-{Screen.width}x{Screen.height}.png");
    static async Task Seconds(float seconds)
    {
        float until = Time.unscaledTime + seconds;
        while (Time.unscaledTime < until) await Frames(1);
    }
    static Task Frames(int count)
    {
        var task = new TaskCompletionSource<bool>();
        int target = Time.frameCount + count;
        double deadline = EditorApplication.timeSinceStartup + 30;
        EditorApplication.CallbackFunction tick = null;
        tick = () =>
        {
            if (Time.frameCount < target && Application.isPlaying && EditorApplication.timeSinceStartup < deadline) return;
            EditorApplication.update -= tick;
            if (Time.frameCount < target) task.TrySetException(new TimeoutException("Player loop did not advance."));
            else task.TrySetResult(true);
        };
        EditorApplication.update += tick;
        return task.Task;
    }
}
