// Unity Pipeline eval_file; parent executes in an idle, focused Play Mode scene with UI initialized.
// unity command eval_file --file Tools/TripoInputChecks.eval.cs
// NOT executed by the implementation worker. Synthetic events do not prove physical touch/raycasting.
// Uses a temporary keyboard and explicit InputSystem.Update; do not run during gameplay/input capture.
if (!UnityEngine.Application.isPlaying || !UnityEngine.Application.isFocused)
    throw new System.InvalidOperationException("Run in focused, idle Play Mode.");
var eventSystem = UnityEngine.EventSystems.EventSystem.current;
if (eventSystem == null) throw new System.InvalidOperationException("An initialized EventSystem is required.");
var instanceFlags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
var staticFlags = System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic;
var inputType = typeof(Abyss.UI.UIInput);
var inputFields = new[] { "_frame", "_consumedFrame", "_pulse" };
var savedInput = new object[inputFields.Length];
for (int i = 0; i < inputFields.Length; i++) savedInput[i] = inputType.GetField(inputFields[i], staticFlags).GetValue(null);
var previousKeyboard = UnityEngine.InputSystem.Keyboard.current;
UnityEngine.InputSystem.Keyboard keyboard = null;
UnityEngine.GameObject host = null;
int checks = 0;
void Check(bool passed, string label)
{
    if (!passed) throw new System.InvalidOperationException("INPUT_CHECK_FAIL: " + label);
    checks++;
}
void ResetDebounce(Abyss.UI.UIButton button)
    => typeof(Abyss.UI.UIButton).GetField("_nextClickAt", instanceFlags).SetValue(button, 0f);
void Pulse(Abyss.UI.UIButtonGroup group, int x, int y, bool confirm)
{
    UnityEngine.InputSystem.InputSystem.QueueStateEvent(keyboard, confirm
        ? new UnityEngine.InputSystem.LowLevel.KeyboardState(UnityEngine.InputSystem.Key.Enter)
        : new UnityEngine.InputSystem.LowLevel.KeyboardState());
    UnityEngine.InputSystem.InputSystem.Update();
    inputType.GetField("_frame", staticFlags).SetValue(null, UnityEngine.Time.frameCount);
    inputType.GetField("_consumedFrame", staticFlags).SetValue(null, -1);
    inputType.GetField("_pulse", staticFlags).SetValue(null, new UnityEngine.Vector2Int(x, y));
    typeof(Abyss.UI.UIButtonGroup).GetMethod("Update", instanceFlags).Invoke(group, null);
}
try
{
    host = new UnityEngine.GameObject("Tripo isolated input checks", typeof(UnityEngine.RectTransform));
    Abyss.UI.UIInput.PushLayer(host.transform);
    keyboard = UnityEngine.InputSystem.InputSystem.AddDevice<UnityEngine.InputSystem.Keyboard>();
    var group = host.AddComponent<Abyss.UI.UIButtonGroup>();
    var buttons = new Abyss.UI.UIButton[4];
    var counts = new int[4];
    for (int i = 0; i < buttons.Length; i++)
    {
        int slot = i;
        buttons[i] = Abyss.UI.UIFactory.Button(host.transform, "Input check " + i, () => counts[slot]++);
        buttons[i].Quiet = true;
        group.Add(buttons[i]);
    }
    var first = buttons[0];
    // Reject direct Click and real group Confirm; rejected clicks must not start the debounce timer.
    for (int mode = 0; mode < 3; mode++)
    {
        group.SetFocus(0, true);
        ResetDebounce(first);
        int before = counts[0];
        if (mode == 0) first.enabled = false;
        else if (mode == 1) first.gameObject.SetActive(false);
        else host.SetActive(false);
        Check(!first.isActiveAndEnabled, "inactive state " + mode);
        first.Click();
        Check(counts[0] == before, "inactive direct callback " + mode);
        Check((float)typeof(Abyss.UI.UIButton).GetField("_nextClickAt", instanceFlags).GetValue(first) == 0f,
            "inactive direct click leaves debounce untouched " + mode);
        // A hidden parent disables the group too, so Unity would not call Update in that case.
        if (mode != 2)
        {
            Pulse(group, 0, 0, true);
            Check(counts[0] == before, "inactive confirm callback " + mode);
            Check((int)inputType.GetField("_consumedFrame", staticFlags).GetValue(null) == -1, "inactive confirm not consumed " + mode);
            Pulse(group, 0, 0, false);
        }
        first.enabled = true;
        first.gameObject.SetActive(true);
        host.SetActive(true);
        Check(first.isActiveAndEnabled, "reenabled state " + mode);
        Pulse(group, 0, 0, true);
        Check(counts[0] == before + 1, "reenabled confirm exactly once " + mode);
        first.Click();
        Check(counts[0] == before + 1, "immediate duplicate still debounced " + mode);
        Pulse(group, 0, 0, false);
    }

    group.SetFocus(0, true);
    buttons[1].enabled = false;
    buttons[3].gameObject.SetActive(false);
    typeof(Abyss.UI.UIButtonGroup).GetField("_horizontal", instanceFlags).SetValue(group, true);
    Pulse(group, 1, 0, false); Check(group.FocusIndex == 2, "forward skips disabled component");
    Pulse(group, 1, 0, false); Check(group.FocusIndex == 0, "forward wraps past hidden object");
    Pulse(group, -1, 0, false); Check(group.FocusIndex == 2, "backward wraps past hidden object");
    Pulse(group, -1, 0, false); Check(group.FocusIndex == 0, "backward skips disabled component");
    group.SetFocus(1, true); Check(group.FocusIndex == 0, "explicit focus rejects disabled component");
    group.SetFocus(3, true); Check(group.FocusIndex == 0, "explicit focus rejects hidden object");
    typeof(Abyss.UI.UIButtonGroup).GetField("_horizontal", instanceFlags).SetValue(group, false);
    Pulse(group, 0, -1, false); Check(group.FocusIndex == 2, "vertical forward skip");
    Pulse(group, 0, 1, false); Check(group.FocusIndex == 0, "vertical backward skip");
    buttons[2].Interactable = false;
    Pulse(group, 0, -1, false); Check(group.FocusIndex == 2, "noninteractable reason remains focusable");
    Pulse(group, 0, 0, true); Check(counts[2] == 0, "noninteractable confirm has no callback");
    Pulse(group, 0, 0, false);
    buttons[2].Interactable = true;
    ResetDebounce(buttons[2]);
    Pulse(group, 0, 0, true); Check(counts[2] == 1, "interactable confirm restored");
    Pulse(group, 0, 0, false);
    foreach (var button in buttons) button.gameObject.SetActive(false);
    int selected = group.FocusIndex;
    int total = counts[0] + counts[1] + counts[2] + counts[3];
    Pulse(group, 0, -1, true);
    Check(group.FocusIndex == selected, "all inactive navigation terminates without moving");
    Check(counts[0] + counts[1] + counts[2] + counts[3] == total, "all inactive confirm has no callback");

    var tap = host.AddComponent<Abyss.UI.UITapArea>();
    int taps = 0;
    tap.Tapped += () => taps++;
    var pointerButtons = new[] { UnityEngine.EventSystems.PointerEventData.InputButton.Left,
        UnityEngine.EventSystems.PointerEventData.InputButton.Right, UnityEngine.EventSystems.PointerEventData.InputButton.Middle };
    foreach (var pointerButton in pointerButtons)
    {
        foreach (bool dragging in new[] { false, true })
        {
            int before = taps;
            var evt = new UnityEngine.EventSystems.PointerEventData(eventSystem) { button = pointerButton, dragging = dragging, pointerId = -1 - (int)pointerButton };
            UnityEngine.EventSystems.ExecuteEvents.Execute(host, evt, UnityEngine.EventSystems.ExecuteEvents.pointerClickHandler);
            int expected = pointerButton == UnityEngine.EventSystems.PointerEventData.InputButton.Left && !dragging ? 1 : 0;
            Check(taps == before + expected, "pointer " + pointerButton + " drag=" + dragging);
        }
    }
    int beforeTouch = taps;
    // Touch uses Left. Positive pointer ID checks the handler path, not a physical touchscreen.
    var touch = new UnityEngine.EventSystems.PointerEventData(eventSystem) { button = UnityEngine.EventSystems.PointerEventData.InputButton.Left, pointerId = 1 };
    UnityEngine.EventSystems.ExecuteEvents.Execute(host, touch, UnityEngine.EventSystems.ExecuteEvents.pointerClickHandler);
    Check(taps == beforeTouch + 1, "touch-equivalent left event exactly once");
    touch.dragging = true;
    UnityEngine.EventSystems.ExecuteEvents.Execute(host, touch, UnityEngine.EventSystems.ExecuteEvents.pointerClickHandler);
    Check(taps == beforeTouch + 1, "touch drag ignored");
}
finally
{
    if (host != null)
    {
        Abyss.UI.UIInput.PopLayer(host.transform);
        host.SetActive(false);
        UnityEngine.Object.Destroy(host);
    }
    if (keyboard != null) UnityEngine.InputSystem.InputSystem.RemoveDevice(keyboard);
    if (previousKeyboard != null && previousKeyboard.added) previousKeyboard.MakeCurrent();
    for (int i = 0; i < inputFields.Length; i++) inputType.GetField(inputFields[i], staticFlags).SetValue(null, savedInput[i]);
}
return "INPUT_CHECK_PASS: " + checks + " assertions; synthetic input only, physical touch/raycasting needs separate verification.";
