// Parent-only SERIALIZED eval_file; fresh Main Play after TownWorld/TownEnrichment compile.
// Focused production-input trail + imported town asset acceptance. No original campaign load/restore.
// BeginReview precedes every mutating GameApp call. Stop Play after evidence collection.
// Narrow rerun for the former-proxy assertion. Set false for the full focused trail/tree/station fixture.
bool TreeProbeOnly = false;
var project = System.IO.Directory.GetParent(Application.dataPath).FullName;
if (!Application.isPlaying || Abyss.Runtime.GameApp.Instance == null
    || !string.Equals(project, @"C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015", System.StringComparison.OrdinalIgnoreCase)
    || UnityEngine.SceneManagement.SceneManager.GetActiveScene().name != "Main")
    throw new System.InvalidOperationException("Fresh Main Play in the assigned checkout is required.");
if (GameObject.Find("AstraTownTrailAcceptance_BUSY") != null || GameObject.Find("AstraWorldAcceptance_BUSY") != null)
    throw new System.InvalidOperationException("Another acceptance fixture is active.");
var app = Abyss.Runtime.GameApp.Instance;
var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic;
var outDir = System.IO.Path.Combine(project, "docs/verification/astra-enrichment-20261015/runtime/" + (TreeProbeOnly ? "town-tree-probe-" : "town-trail-") + System.DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
var qaSave = System.IO.Path.Combine(outDir, "qa-save");
System.IO.Directory.CreateDirectory(outDir);
var checks = new System.Collections.Generic.List<object>();
var issues = new System.Collections.Generic.List<object>();
var images = new System.Collections.Generic.List<object>();
var traces = new System.Collections.Generic.List<object>();
bool failed = false, isolated = false;
string phase = "scheduled";
System.DateTime deadline = System.DateTime.MaxValue;
var preferences = app.Preferences;
float captureDelta = Time.captureDeltaTime;
bool background = Application.runInBackground;
var priorKeyboard = UnityEngine.InputSystem.Keyboard.current;
UnityEngine.InputSystem.Keyboard keyboard = null;
Abyss.Runtime.World.TownWorld town = null;
System.Collections.Generic.List<Abyss.Runtime.Art.CharacterModel> party = null;
Pose[] homePoses = null;
GameObject lease = null, arena = null;
UnityEditor.EditorWindow gameView = null;
System.Reflection.PropertyInfo selectedSize = null;
object sizeGroup = null;
int originalSize = -1;
var sizes = new System.Collections.Generic.List<int>();
object Read(object target, string name) => target.GetType().GetField(name, flags).GetValue(target);
object Prop(object target, string name) => target.GetType().GetProperty(name, flags).GetValue(target);
object Call(object target, string name, params object[] args) => target.GetType().GetMethod(name, flags).Invoke(target, args);
float[] V(Vector3 v) => new[] { v.x, v.y, v.z };
float Flat(Vector3 v) => new Vector2(v.x, v.z).magnitude;
void Check(string name, bool pass, object detail = null) { checks.Add(new { phase, name, passed = pass, detail }); if (!pass) failed = true; }
void Need(bool pass, string name) { Check(name, pass); if (!pass) throw new System.InvalidOperationException(name); }
string Hash(string path) {
    if (!System.IO.File.Exists(path)) return "missing";
    using (var hash = System.Security.Cryptography.SHA256.Create())
        return System.BitConverter.ToString(hash.ComputeHash(System.IO.File.ReadAllBytes(path))).Replace("-", "").ToLowerInvariant();
}
var build = new {
    project, unity = Application.unityVersion, module = typeof(Abyss.Runtime.GameApp).Module.ModuleVersionId.ToString(),
    assembly = Hash(typeof(Abyss.Runtime.GameApp).Assembly.Location),
    town = Hash(System.IO.Path.Combine(project, "Assets/_Game/Scripts/Runtime/World/TownWorld.cs")),
    enrichment = Hash(System.IO.Path.Combine(project, "Assets/_Game/Scripts/Runtime/World/TownEnrichment.cs")),
    station = Hash(System.IO.Path.Combine(project, "Assets/_Game/Resources/Art/Props/GuildFieldStation/guild_field_gear_station.fbx")),
    fixture = Hash(System.IO.Path.Combine(project, "Tools/AstraTownTrailAcceptance.eval.cs"))
};
void Report(string status) => System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "result.json"),
    Newtonsoft.Json.JsonConvert.SerializeObject(new { status, phase, build, isolated, qaSave, checks, issues, images, traces,
        scope = TreeProbeOnly ? "tree-probe-only; trails, station and captures not rerun" : "trail-tree-station", expectedPngs = TreeProbeOnly ? 0 : 4,
        visualAccepted = false, requestedModel = "gpt-6-astra", requestedEffort = "high", requestedTier = "Fast/priority", verifiedRouting = "not exposed",
        limits = new[] { "Constructed static rectangular obstacle; not every authored town route or dynamic obstruction.",
            "Captured deltaTime and sparse scheduling exercise production Update; not an induced CPU stall or physical input test.",
            "Trail bounds are sampled on these routes; full-capacity pressure, roster replacement mid-corner, steps and long sessions are separate acceptance.",
            "Inspect station PNGs for actual visible material, occlusion and ground fit. Frustum checks are not pixel visibility proof." } }, Newtonsoft.Json.Formatting.Indented));
void Budget() {
    if (!Application.isPlaying) throw new System.InvalidOperationException("Play stopped during " + phase);
    if (System.DateTime.UtcNow > deadline) throw new System.TimeoutException("25-second step deadline: " + phase);
}
async System.Threading.Tasks.Task Until(System.Func<bool> condition, string label) {
    var end = System.DateTime.UtcNow.AddSeconds(25);
    while (!condition()) { Budget(); if (System.DateTime.UtcNow > end) throw new System.TimeoutException(label); await System.Threading.Tasks.Task.Yield(); }
}
async System.Threading.Tasks.Task Frames(int count) { int end = Time.frameCount + count; await Until(() => Time.frameCount >= end, "frame advance"); }
async System.Threading.Tasks.Task Step(string name, System.Func<System.Threading.Tasks.Task> body) {
    phase = name; deadline = System.DateTime.UtcNow.AddSeconds(25); Report("running");
    try { await body(); Budget(); } catch (System.Exception e) { failed = true; issues.Add(new { phase, error = e.ToString() }); }
    finally {
        if (arena != null) { UnityEngine.Object.Destroy(arena); arena = null; }
        deadline = System.DateTime.MaxValue;
    }
    Report("running");
}
void Focus() {
    if (gameView == null) {
        var type = typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.GameView");
        gameView = UnityEditor.EditorWindow.GetWindow(type);
        selectedSize = type.GetProperty("selectedSizeIndex", flags); originalSize = (int)selectedSize.GetValue(gameView);
    }
    gameView.Focus();
}
async System.Threading.Tasks.Task Resize(int w, int h) {
    Focus(); var a = typeof(UnityEditor.Editor).Assembly;
    var type = a.GetType("UnityEditor.GameViewSizes");
    var instance = typeof(UnityEditor.ScriptableSingleton<>).MakeGenericType(type).GetProperty("instance").GetValue(null);
    var get = type.GetMethod("GetGroup"); sizeGroup = get.Invoke(instance, new[] { System.Enum.Parse(get.GetParameters()[0].ParameterType, "Standalone") });
    var kind = a.GetType("UnityEditor.GameViewSizeType");
    var ctor = a.GetType("UnityEditor.GameViewSize").GetConstructor(flags, null, new[] { kind, typeof(int), typeof(int), typeof(string) }, null);
    int index = (int)Call(sizeGroup, "GetTotalCount");
    Call(sizeGroup, "AddCustomSize", ctor.Invoke(new object[] { System.Enum.ToObject(kind, 1), w, h, "Astra trail temporary" }));
    sizes.Add(index); selectedSize.SetValue(gameView, index);
    await Until(() => Screen.width == w && Screen.height == h, "GameView size"); await Frames(4);
}
async System.Threading.Tasks.Task Snap(string label, int w, int h) {
    Canvas.ForceUpdateCanvases(); string path = System.IO.Path.Combine(outDir, label + "-" + w + "x" + h + ".png");
    ScreenCapture.CaptureScreenshot(path); await Frames(3);
    await Until(() => System.IO.File.Exists(path) && new System.IO.FileInfo(path).Length > 32, "PNG written");
    var bytes = System.IO.File.ReadAllBytes(path);
    int pw = (bytes[16] << 24) | (bytes[17] << 16) | (bytes[18] << 8) | bytes[19];
    int ph = (bytes[20] << 24) | (bytes[21] << 16) | (bytes[22] << 8) | bytes[23];
    Check("PNG actual dimensions " + label, pw == w && ph == h && Screen.width == w && Screen.height == h);
    images.Add(new { label, path, width = pw, height = ph, sha256 = Hash(path), frame = Time.frameCount,
        cameraPosition = V(app.MainCamera.transform.position), cameraRotation = V(app.MainCamera.transform.eulerAngles), app.MainCamera.fieldOfView });
}
void Key(UnityEngine.InputSystem.Key key = UnityEngine.InputSystem.Key.None) {
    UnityEngine.InputSystem.InputSystem.QueueStateEvent(keyboard, key == UnityEngine.InputSystem.Key.None
        ? new UnityEngine.InputSystem.LowLevel.KeyboardState() : new UnityEngine.InputSystem.LowLevel.KeyboardState(key));
    UnityEngine.InputSystem.InputSystem.Update();
}
void Place(Pose[] poses) {
    for (int i = 0; i < party.Count; i++) {
        var body = party[i].GetComponent<CharacterController>(); body.enabled = false;
        party[i].transform.SetPositionAndRotation(poses[i].position, poses[i].rotation); body.enabled = true;
    }
    Physics.SyncTransforms(); // Production Update detects relocation and resets its own trail; no trail writes here.
}
void Capsule(CharacterController body, Vector3 position, out Vector3 bottom, out Vector3 top, out float radius) {
    var scale = body.transform.lossyScale;
    radius = Mathf.Max(.01f, body.radius * Mathf.Max(Mathf.Abs(scale.x), Mathf.Abs(scale.z)) - body.skinWidth - .01f);
    Vector3 center = position + body.transform.TransformVector(body.center);
    float half = Mathf.Max(0f, body.height * Mathf.Abs(scale.y) * .5f - body.radius * Mathf.Max(Mathf.Abs(scale.x), Mathf.Abs(scale.z)));
    bottom = center - Vector3.up * half; top = center + Vector3.up * half;
}
Collider[] Blockers(CharacterController body, Vector3 position) {
    Capsule(body, position, out var b, out var t, out float r);
    return Physics.OverlapCapsule(b, t, r, ~(1 << 8), QueryTriggerInteraction.Ignore);
}
async System.Threading.Tasks.Task Route(float dt, int stride, bool mirror) {
    var rig = (Abyss.Runtime.World.TownCamera)Read(town, "rig");
    var rotation = Quaternion.Euler(0f, rig.ViewYaw, 0f);
    arena = new GameObject("Astra temporary rectangular trail arena"); arena.transform.SetPositionAndRotation(new Vector3(1000f, 0f, 1000f), rotation);
    var ground = new GameObject("QA ground"); ground.transform.SetParent(arena.transform, false);
    var floor = ground.AddComponent<BoxCollider>(); floor.center = new Vector3(0f, -.5f, 0f); floor.size = new Vector3(34f, 1f, 34f);
    var solid = new GameObject("QA 3.4m square obstacle"); solid.transform.SetParent(arena.transform, false);
    var obstacle = solid.AddComponent<BoxCollider>(); obstacle.center = Vector3.up; obstacle.size = new Vector3(3.4f, 2f, 3.4f);
    float sign = mirror ? -1f : 1f;
    var formation = Enumerable.Range(0, 4).Select(i => new Pose(arena.transform.TransformPoint(new Vector3(-2.15f * sign, .04f, -2.15f - i * .95f)), rotation)).ToArray();
    var followers = ((System.Collections.IList)Read(town, "followers")).Cast<object>().ToArray();
    var trails = followers.Select(f => Read(f, "Trail")).ToArray();
    var arrays = trails.Select(t => (System.Array)Read(t, "points")).ToArray();
    int capacity = (int)trails[0].GetType().GetField("Capacity", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static).GetRawConstantValue();
    Need(capacity == 256 && arrays.All(a => a.Length == capacity), "production fixed 256-point trail buffers");
    var samples = new System.Collections.Generic.List<object>();
    var crossedCorner = new bool[4]; int[] peak = new int[3]; float peakLength = 0f, peakStep = 0f, minDt = float.MaxValue, maxDt = 0f;
    int ticks = 0, intersections = 0, sweptIntersections = 0, locked = 0, longestLock = 0;
    try {
        Time.captureDeltaTime = dt; Place(formation); Key(); await Frames(3); Call(town, "Update");
        async System.Threading.Tasks.Task Tick(UnityEngine.InputSystem.Key key) {
            Budget(); await Frames(stride); Key(key);
            if (!Application.isFocused || app.UI.BlocksWorldInput || Abyss.UI.UIInput.ConsumedThisFrame)
                throw new System.InvalidOperationException("Movement input became blocked; no route pass can be claimed.");
            if (Mathf.Abs(Mathf.DeltaAngle(rotation.eulerAngles.y, rig.ViewYaw)) > .05f)
                throw new System.InvalidOperationException("Camera yaw changed during the input-aligned route.");
            var before = party.Select(p => p.transform.position).ToArray();
            Call(town, "Update"); ticks++; minDt = Mathf.Min(minDt, Time.deltaTime); maxDt = Mathf.Max(maxDt, Time.deltaTime);
            int[] counts = trails.Select(t => (int)Prop(t, "Count")).ToArray();
            float[] lengths = trails.Select(t => (float)Prop(t, "Length")).ToArray();
            for (int i = 0; i < 3; i++) {
                if (counts[i] < 1 || counts[i] > capacity || !object.ReferenceEquals(arrays[i], Read(trails[i], "points"))
                    || float.IsNaN(lengths[i]) || float.IsInfinity(lengths[i]) || lengths[i] < -.001f)
                    throw new System.InvalidOperationException("Invalid or growing production trail buffer at tick " + ticks);
                peak[i] = Mathf.Max(peak[i], counts[i]); peakLength = Mathf.Max(peakLength, lengths[i]);
            }
            for (int i = 0; i < 4; i++) {
                var body = party[i].GetComponent<CharacterController>(); var now = party[i].transform.position;
                float travel = Flat(now - before[i]); peakStep = Mathf.Max(peakStep, travel);
                if (Blockers(body, now).Contains(obstacle)) intersections++;
                Capsule(body, before[i], out var b, out var t, out float r);
                Vector3 delta = now - before[i];
                if (delta.magnitude > .0001f && Physics.CapsuleCastAll(b, t, r, delta.normalized, delta.magnitude, ~(1 << 8), QueryTriggerInteraction.Ignore).Any(h => h.collider == obstacle)) sweptIntersections++;
                Vector3 local = arena.transform.InverseTransformPoint(now);
                if (local.z > 1.85f && local.x * sign < -1.85f) crossedCorner[i] = true;
            }
            locked = key != UnityEngine.InputSystem.Key.None && Flat(party[0].transform.position - before[0]) < .001f ? locked + 1 : 0;
            longestLock = Mathf.Max(longestLock, locked);
            samples.Add(new { tick = ticks, frame = Time.frameCount, deltaTime = Time.deltaTime, key = key.ToString(), positions = party.Select(p => V(arena.transform.InverseTransformPoint(p.transform.position))).ToArray(), counts, lengths, intersections, sweptIntersections, peakStep });
            if (locked >= 12) throw new System.InvalidOperationException("Leader blocked for 12 commanded updates on a clear corridor.");
            if (intersections > 0 || sweptIntersections > 0 || peakStep > .38f)
                throw new System.InvalidOperationException("Obstacle intersection or unbounded walking displacement at tick " + ticks);
        }
        while (arena.transform.InverseTransformPoint(party[0].transform.position).z < 2.15f) await Tick(UnityEngine.InputSystem.Key.W);
        while (arena.transform.InverseTransformPoint(party[0].transform.position).x * sign < 6.5f)
            await Tick(mirror ? UnityEngine.InputSystem.Key.A : UnityEngine.InputSystem.Key.D);
        int settled = 0;
        while (settled < 6) {
            var before = party.Select(p => p.transform.position).ToArray(); await Tick(UnityEngine.InputSystem.Key.None);
            settled = party.Select((p, i) => Flat(p.transform.position - before[i]) < .001f).All(v => v) ? settled + 1 : 0;
        }
        var end = party.Select(p => arena.transform.InverseTransformPoint(p.transform.position)).ToArray();
        Check("all four traverse the L corner and finish beyond the obstacle", crossedCorner.All(v => v) && end.All(p => p.x * sign > 2.05f && p.z > 2f), end.Select(V).ToArray());
        Check("all three settle at retained route spacing", Enumerable.Range(1, 3).All(i => Flat(end[i] - end[i - 1]) <= 1.12f));
        Check("no endpoint or swept capsule intersection (skin allowance)", intersections == 0 && sweptIntersections == 0, new { intersections, sweptIntersections });
        Check("bounded trails and no persistent leader lock", peak.All(n => n <= capacity) && longestLock < 12 && peakStep <= .38f, new { peak, peakLength, longestLock, peakStep });
        Check("production Update observed requested deltaTime", Mathf.Abs(minDt - dt) < .004f && Mathf.Abs(maxDt - dt) < .004f, new { requested = dt, minDt, maxDt, stride, ticks });
    } finally {
        traces.Add(new { profile = phase, requestedDelta = dt, frameStride = stride, mirror, samples });
        Key(); Time.captureDeltaTime = captureDelta; Place(homePoses);
        UnityEngine.Object.Destroy(arena); arena = null;
    }
}
async System.Threading.Tasks.Task Run() {
    await System.Threading.Tasks.Task.Yield();
    Application.LogCallback log = (message, stack, type) => { if (type == LogType.Error || type == LogType.Exception || type == LogType.Assert) { failed = true; issues.Add(new { phase, message, stack, type = type.ToString() }); } };
    Application.logMessageReceived += log;
    try {
        phase = "focus-and-QA-isolation"; deadline = System.DateTime.UtcNow.AddSeconds(25);
        Focus(); await Until(() => Application.isFocused && UnityEditor.EditorWindow.focusedWindow == gameView, "actual GameView focus");
        var state = Abyss.Logic.Game.GameState.NewGame(app.DB, Abyss.Logic.Difficulty.Normal);
        Abyss.Logic.Game.GameFlow.CompletePrologue(state);
        foreach (string tip in new[] { "first_town", "first_battle", "first_foe", "first_trap", "first_tp_full" }) state.Flags.Add(Abyss.Logic.Game.GameFlow.TipFlag(tip));
        state.Flags.Add("biome_0_seen"); state.Repair(app.DB); Abyss.Logic.Game.GameFlow.EnterTown(app.DB, state);
        state.FloorIndex = 0; state.Location = Abyss.Logic.Game.GameLocation.Dungeon;
        state.Position = Abyss.Logic.Dungeon.DungeonGrid.Parse(app.DB.Floors[0], state.Floor(app.DB.Floors[0].Id)).Start;
        app.BeginReview(state, 0); // FIRST mutating GameApp call switches away from the normal campaign.
        typeof(Abyss.Runtime.GameApp).GetField("saveDirectory", flags).SetValue(app, qaSave);
        typeof(Abyss.Runtime.GameApp).GetField("<Saves>k__BackingField", flags).SetValue(app, new Abyss.Runtime.Persistence.SaveRepository(qaSave, app.DB));
        isolated = (string)Read(app, "saveDirectory") == qaSave; Need(isolated, "dedicated QA persistence after BeginReview");
        lease = new GameObject("AstraTownTrailAcceptance_BUSY");
        typeof(Abyss.Runtime.GameApp).GetField("<Preferences>k__BackingField", flags).SetValue(app,
            Newtonsoft.Json.JsonConvert.DeserializeObject<Abyss.Runtime.Persistence.GamePreferences>(Newtonsoft.Json.JsonConvert.SerializeObject(preferences)));
        app.Preferences.ReducedMotion = true; Application.runInBackground = true;
        app.EnterTown(); await Until(() => app.Screen == Abyss.Runtime.GameScreen.Town && !app.UI.BlocksWorldInput, "town ready"); await Frames(5);
        town = (Abyss.Runtime.World.TownWorld)Read(app, "townWorld"); town.enabled = false;
        party = (System.Collections.Generic.List<Abyss.Runtime.Art.CharacterModel>)Read(town, "party");
        Need(party.Count == 4 && party.All(p => p.GetComponent<CharacterController>() != null), "four real town party controllers");
        homePoses = party.Select(p => new Pose(p.transform.position, p.transform.rotation)).ToArray();
        keyboard = UnityEngine.InputSystem.InputSystem.AddDevice<UnityEngine.InputSystem.Keyboard>(); keyboard.MakeCurrent(); Key();
        Need((UnityEngine.InputSystem.Gamepad.current?.leftStick.ReadValue() ?? Vector2.zero).sqrMagnitude < .0001f
            && Abyss.UI.UITouch.Stick.sqrMagnitude < .0001f, "no competing gamepad or touch movement input");
        deadline = System.DateTime.MaxValue;
        if (!TreeProbeOnly) {
            await Step("L-route-60Hz", () => Route(1f / 60f, 1, false));
            await Step("L-route-hitch-250ms-mirrored", () => Route(.25f, 1, true));
            await Step("L-route-sparse-100ms-every-third-frame", () => Route(.1f, 3, false));
        }
        await Step("actual-tree-proxy-and-former-location", async () => {
            var tree = Abyss.Runtime.World.EnvironmentProcessor.Find(town.transform, "Tree_plaza_5");
            var proxy = Abyss.Runtime.World.EnvironmentProcessor.Find(town.transform, "Col_Tree_plaza_-140_10");
            Need(tree != null && proxy != null, "actual tree and proxy exist");
            var box = proxy.GetComponent<BoxCollider>(); Need(box != null && box.enabled && !box.isTrigger, "actual trunk has solid primitive collider");
            var raw = Resources.Load<GameObject>(Abyss.Runtime.Art.ArtLibrary.TownPath);
            Need(raw != null, "unmodified imported town prefab is available");
            var original = Abyss.Runtime.World.EnvironmentProcessor.Find(raw.transform, proxy.name);
            var liveRoot = Abyss.Runtime.World.EnvironmentProcessor.Find(town.transform, "Guild_Field_Gear_Station").parent;
            var oldPosition = liveRoot.TransformPoint(raw.transform.InverseTransformPoint(original.position));
            var originalBox = original.GetComponent<BoxCollider>();
            Need(originalBox != null, "original tree proxy collider is present in imported prefab");
            Check("proxy XZ aligned with the rendered tree", Flat(proxy.position - tree.position) < .002f, new { tree = V(tree.position), proxy = V(proxy.position), oldPosition = V(oldPosition) });
            Check("old position is distinct and proxy shape/Y/rotation preserved", Flat(oldPosition - proxy.position) > 1f && Mathf.Abs(oldPosition.y - proxy.position.y) < .002f
                && box.size == originalBox.size && box.center == originalBox.center
                && Quaternion.Angle(proxy.rotation, liveRoot.rotation * Quaternion.Inverse(raw.transform.rotation) * original.rotation) < .01f);
            var body = party[0].GetComponent<CharacterController>();
            object[] SweptGeometry(Vector3 origin, Vector3 direction, float distance) {
                Capsule(body, origin, out var bottom, out var top, out float radius);
                radius += body.skinWidth + .01f; // Diagnostics use the full physical radius, without the overlap-test skin allowance.
                return Physics.CapsuleCastAll(bottom, top, radius, direction, distance, ~(1 << 8), QueryTriggerInteraction.Ignore)
                    .OrderBy(h => h.distance).Select(h => (object)new { collider = h.collider.name, kind = h.collider.GetType().Name,
                        h.distance, point = V(h.point), minimum = V(h.collider.bounds.min), maximum = V(h.collider.bounds.max) }).ToArray();
            }
            // Prior run crossed the old center at x=14, then stopped at x=14.3719 toward Clinic_Steps (front ~14.65).
            // Preserve the original X-corridor geometry as diagnostics; test the old trunk volume parallel to the facade on Z.
            float oldReach = box.bounds.extents.x + body.radius + .4f;
            var oldStart = new Vector3(oldPosition.x - oldReach, box.bounds.min.y + .04f, oldPosition.z);
            traces.Add(new { profile = phase, probe = "original-X-corridor-diagnostics", start = V(oldStart), direction = V(Vector3.right),
                desired = oldReach * 2f, candidates = SweptGeometry(oldStart, Vector3.right, oldReach * 2f) });
            void Sweep(Vector3 center, bool blocked) {
                var poses = party.Select(p => new Pose(p.transform.position, p.transform.rotation)).ToArray();
                Vector3 direction = blocked ? Vector3.right : Vector3.forward;
                float reach = (blocked ? box.bounds.extents.x : box.bounds.extents.z) + body.radius + .4f;
                var start = new Vector3(center.x, box.bounds.min.y + .04f, center.z) - direction * reach;
                try {
                    body.enabled = false; body.transform.position = start; body.enabled = true; Physics.SyncTransforms();
                    Need(Blockers(body, start).Length == 0, "sweep starts clear at " + (blocked ? "current tree" : "former proxy"));
                    var candidates = SweptGeometry(start, direction, reach * 2f);
                    var hits = body.Move(direction * (reach * 2f));
                    float moved = Vector3.Dot(body.transform.position - start, direction);
                    if (!blocked) Check("former trunk center has no residual solid collider", Blockers(body, new Vector3(center.x, start.y, center.z)).Length == 0);
                    Check(blocked ? "current tree blocks actual controller" : "former proxy location is traversable",
                        blocked ? (hits & CollisionFlags.Sides) != 0 && moved < reach : (hits & CollisionFlags.Sides) == 0 && moved >= reach * 2f - .08f,
                        new { start = V(start), end = V(body.transform.position), direction = V(direction), moved, desired = reach * 2f, hits = hits.ToString(), candidates });
                } finally { Place(poses); }
            }
            Sweep(oldPosition, false); Sweep(box.bounds.center, true); await Frames(2);
        });
        if (!TreeProbeOnly) await Step("station-import-and-world-fit", async () => {
            var station = Abyss.Runtime.World.EnvironmentProcessor.Find(town.transform, "Guild_Field_Gear_Station");
            Need(station != null, "required station loaded by production town initialization");
            var renderers = station.GetComponentsInChildren<MeshRenderer>();
            var filters = station.GetComponentsInChildren<MeshFilter>();
            Need(renderers.Length > 0 && renderers.All(r => r.enabled && r.gameObject.activeInHierarchy) && filters.All(f => f.sharedMesh != null), "live station renderers and meshes survive environment processing");
            long triangles = 0; var local = new Bounds(); bool first = true;
            foreach (var filter in filters) {
                var mesh = filter.sharedMesh;
                for (int s = 0; s < mesh.subMeshCount; s++) if (mesh.GetTopology(s) == MeshTopology.Triangles) triangles += mesh.GetIndexCount(s) / 3;
                var b = mesh.bounds;
                for (int i = 0; i < 8; i++) {
                    var corner = b.center + Vector3.Scale(b.extents, new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1));
                    var p = station.InverseTransformPoint(filter.transform.TransformPoint(corner));
                    if (first) { local = new Bounds(p, Vector3.zero); first = false; } else local.Encapsulate(p);
                }
            }
            Check("imported station is exactly 5990 triangles", triangles == 5990, triangles);
            var mats = renderers.SelectMany(r => r.sharedMaterials).ToArray();
            var expectedMaterial = Resources.Load<Material>("Art/Props/GuildFieldStation/guild_field_gear_station_mat/tripo_mat_3551cec0");
            var expectedTexture = Resources.Load<Texture2D>("Art/Props/GuildFieldStation/guild_field_gear_station_tex/tripo_mat_3551cec0");
            bool valid = mats.Length > 0 && mats.All(m => m != null && m.shader != null && m.shader.isSupported && m.shader.name != "Hidden/InternalErrorShader"
                && m.GetTexturePropertyNames().Any(n => m.GetTexture(n) != null && m.GetTexture(n).width > 0));
            Check("station has loaded supported textured materials", valid, mats.Select(m => m == null ? null : new { m.name, shader = m.shader == null ? null : m.shader.name,
                textures = m.GetTexturePropertyNames().Where(n => m.GetTexture(n) != null).Select(n => new { property = n, path = UnityEditor.AssetDatabase.GetAssetPath(m.GetTexture(n)), width = m.GetTexture(n).width, height = m.GetTexture(n).height }).ToArray() }).ToArray());
            Check("actual station uses its imported material and base texture", expectedMaterial != null && expectedTexture != null
                && mats.Contains(expectedMaterial) && expectedMaterial.HasProperty("_BaseMap") && expectedMaterial.GetTexture("_BaseMap") == expectedTexture);
            Check("station local dimensions and scale match approved 1.4 x 1.05 x 0.665m", (local.size - new Vector3(1.4f, 1.05f, .665f)).magnitude < .04f
                && (station.lossyScale - Vector3.one).sqrMagnitude < .0001f, new { size = V(local.size), minimum = V(local.min), scale = V(station.lossyScale) });
            var colliders = station.GetComponentsInChildren<Collider>(); var box = colliders.Length == 1 ? colliders[0] as BoxCollider : null;
            Check("one separate solid simple station collider; renderer is retained", box != null && box.enabled && !box.isTrigger
                && box.name == "Col_Guild_Field_Gear_Station" && box.GetComponent<Renderer>() == null
                && (box.size - new Vector3(1.4f, 1.05f, .665f)).sqrMagnitude < .00001f && (box.center - new Vector3(0f, .525f, 0f)).sqrMagnitude < .00001f);
            Check("station authored placement", (station.localPosition - new Vector3(17.3f, .03f, -4.9f)).sqrMagnitude < .00001f
                && Quaternion.Angle(station.localRotation, Quaternion.Euler(0f, -90f, 0f)) < .01f);
            var world = renderers[0].bounds; foreach (var r in renderers.Skip(1)) world.Encapsulate(r.bounds);
            var floors = Physics.RaycastAll(new Vector3(world.center.x, world.min.y + .2f, world.center.z), Vector3.down, 2f, ~(1 << 8), QueryTriggerInteraction.Ignore)
                .Where(h => !h.collider.transform.IsChildOf(station) && h.normal.y > .75f).OrderBy(h => h.distance).ToArray();
            Need(floors.Length > 0, "real ground exists beneath station");
            float gap = world.min.y - floors[0].point.y;
            Check("station grounded without visible sink or float", gap >= -.02f && gap <= .08f, new { gap, ground = floors[0].collider.name, size = V(world.size) });
            await Frames(2);
        });
        if (!TreeProbeOnly) foreach (var size in new[] { new[] { 1280, 720 }, new[] { 915, 412 } }) await Step("station-camera-" + size[0], async () => {
            await Resize(size[0], size[1]); app.UI.ShowTown(); await Frames(3);
            var station = Abyss.Runtime.World.EnvironmentProcessor.Find(town.transform, "Guild_Field_Gear_Station");
            Need(station != null, "station present for game integration capture");
            var bounds = station.GetComponentsInChildren<Renderer>()[0].bounds;
            foreach (var r in station.GetComponentsInChildren<Renderer>().Skip(1)) bounds.Encapsulate(r.bounds);
            var offset = new Vector3(-3.8f, 0f, -2.8f); var facing = Quaternion.LookRotation(-offset);
            var formation = Enumerable.Range(0, 4).Select(i => new Pose(new Vector3(station.position.x + offset.x, homePoses[i].position.y, station.position.z + offset.z)
                - facing * Vector3.forward * (i * .95f), facing)).ToArray();
            Need(Enumerable.Range(0, 4).All(i => Blockers(party[i].GetComponent<CharacterController>(), formation[i].position).Length == 0
                && Physics.RaycastAll(formation[i].position + Vector3.up * .4f, Vector3.down, .8f, ~(1 << 8), QueryTriggerInteraction.Ignore).Any(h => h.normal.y > .75f)),
                "normal-camera QA party formation is on clear ground");
            Place(formation); Key(); await Frames(2); Call(town, "Update");
            var rig = (Abyss.Runtime.World.TownCamera)Read(town, "rig"); rig.ResetYaw(facing.eulerAngles.y);
            Call(town, "FollowCamera", true); await Frames(5);
            Check("normal production orbit uses default distance", Mathf.Abs(rig.Distance - Abyss.Runtime.World.TownCamera.DefaultDistance) < .01f);
            Check("station bounds in normal camera frustum", GeometryUtility.TestPlanesAABB(GeometryUtility.CalculateFrustumPlanes(app.MainCamera), bounds));
            await Snap("station-normal-game-camera", size[0], size[1]);
            var camera = app.MainCamera; var pose = new Pose(camera.transform.position, camera.transform.rotation); float fov = camera.fieldOfView;
            try {
                camera.transform.position = bounds.center + new Vector3(-2.1f, 1.3f, -1.7f); camera.transform.LookAt(bounds.center); camera.fieldOfView = 45f;
                await Frames(4); await Snap("station-closeup-in-town", size[0], size[1]);
            } finally { camera.transform.SetPositionAndRotation(pose.position, pose.rotation); camera.fieldOfView = fov; Place(homePoses); }
        });
    } catch (System.Exception e) { failed = true; issues.Add(new { phase, error = e.ToString() }); }
    finally {
        deadline = System.DateTime.MaxValue;
        try {
            if (keyboard != null) { Key(); UnityEngine.InputSystem.InputSystem.RemoveDevice(keyboard); priorKeyboard?.MakeCurrent(); }
            Time.captureDeltaTime = captureDelta; Application.runInBackground = background;
            if (arena != null) UnityEngine.Object.Destroy(arena);
            if (town != null) { if (homePoses != null) Place(homePoses); town.enabled = true; }
            if (isolated) typeof(Abyss.Runtime.GameApp).GetField("<Preferences>k__BackingField", flags).SetValue(app, preferences);
            if (gameView != null && selectedSize != null) selectedSize.SetValue(gameView, originalSize);
            if (sizeGroup != null) for (int i = sizes.Count - 1; i >= 0; i--) Call(sizeGroup, "RemoveCustomSize", sizes[i]);
            if (lease != null) UnityEngine.Object.Destroy(lease);
        } catch (System.Exception e) { failed = true; issues.Add(new { phase = "cleanup", error = e.ToString() }); }
        Application.logMessageReceived -= log; phase = "finished";
        Report(failed ? "failed" : "automated-checks-passed-visual-review-required");
        System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "DONE"), failed ? "failed" : "visual-review-required");
    }
}
// Keep the eval wrapper's appended fallback reachable.
if (Application.isPlaying) { Report("scheduled"); _ = Run(); return "Town trail acceptance scheduled: " + outDir + "; poll DONE, inspect result.json and PNGs, then stop Play."; }
