using System.Collections;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Runtime.Art;
using Abyss.Presentation.Audio;
using Abyss.Presentation.Vfx;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Abyss.Runtime.World
{
    public sealed class DungeonWorld : MonoBehaviour
    {
        const float CellSize = 4f;
        static readonly int TintId = Shader.PropertyToID("_Tint");
        static readonly Color FoeThreatColor = new Color(1f, 0.55f, 0.12f);
        static readonly Color FoeChaseColor = new Color(1f, 0.26f, 0.05f);
        static readonly Color FoeAlertColor = new Color(1.6f, 0.75f, 0.25f);
        static readonly Color FoeChaseBodyTint = new Color(1f, 0.82f, 0.7f);
        readonly Dictionary<GridPos, Transform> chests = new Dictionary<GridPos, Transform>();
        readonly Dictionary<GridPos, Transform> doors = new Dictionary<GridPos, Transform>();
        readonly Dictionary<GridPos, GameObject> keys = new Dictionary<GridPos, GameObject>();
        readonly Dictionary<string, CharacterModel> foes = new Dictionary<string, CharacterModel>();
        readonly Dictionary<string, Vector3> foeStarts = new Dictionary<string, Vector3>();
        readonly List<Light> lights = new List<Light>();
        readonly List<FoeMarker> foeMarkers = new List<FoeMarker>();
        Mesh markerQuad;
        Material ringMaterial, beaconMaterial, alertMaterial;
        MaterialPropertyBlock markerBlock;
        GameApp app;
        DungeonRun run;
        string tileset;
        bool busy;
        VfxHandle ambient;
        float nextHeldInput;
        public bool Busy => busy;

        /// <summary>Depth-tested world cue parented to a FOE model: orange ground ring + head beacon; chasing adds an alert glyph.</summary>
        sealed class FoeMarker
        {
            public FoeState Foe;
            public CharacterModel Model;
            public Transform Ring, Beacon, Alert;
            public MeshRenderer RingRenderer, BeaconRenderer, AlertRenderer;
            public float RingSize, HeadHeight, Phase;
            public bool Chasing;
        }
        public static Vector3 Position(GridPos cell) => new Vector3(cell.X * CellSize, 0, -cell.Y * CellSize);

        public void Initialize(GameApp app, DungeonRun run)
        {
            this.app = app;
            this.run = run;
            tileset = run.Grid.Floor.Tileset;
            app.Atmosphere.Apply(AtmospherePreset.ForTileset(tileset));
            app.Atmosphere.SetupCamera(app.MainCamera);
            app.MainCamera.fieldOfView = 65;
            var grid = run.Grid;
            for (int y = 0; y < grid.Height; y++)
            for (int x = 0; x < grid.Width; x++)
            {
                var cell = new GridPos(x, y);
                char marker = grid.Cell(cell);
                int variant = (x * 17 + y * 31) % 3;
                if (marker == '#')
                {
                    Spawn("wall_" + (char)('a' + variant), cell);
                    continue;
                }
                Spawn("floor_" + (char)('a' + variant), cell);
                switch (marker)
                {
                    case 'T':
                        var chest = Spawn("chest", cell);
                        chests[cell] = EnvironmentProcessor.Find(chest.transform, "Lid");
                        break;
                    case 'L':
                        var door = Spawn("door_locked", cell);
                        if (grid.Cell(cell.Step(Facing.North)) == '#' && grid.Cell(cell.Step(Facing.South)) == '#') door.transform.Rotate(0, 90, 0);
                        doors[cell] = EnvironmentProcessor.Find(door.transform, "Door");
                        break;
                    case '>': Spawn("stairs_down", cell); break;
                    case '<': Spawn("stairs_up", cell); break;
                    case 'K':
                        var key = ArtLibrary.SpawnStatic(ArtLibrary.PropPath("Common", "key_item"), transform);
                        key.transform.position = Position(cell) + Vector3.up * 0.8f;
                        keys[cell] = key;
                        break;
                    case 'H': Spawn("spring", cell); break;
                    case 'W': Spawn("warp", cell); break;
                    case 'N': Spawn("lore_stone", cell); break;
                    case 'X': Spawn("trap", cell); break;
                    case 'B': Spawn("boss_gate", cell); break;
                }
                // Sparse side dressing keeps the centre of every walkable cell clear.
                if ((x * 13 + y * 7) % 9 == 0)
                {
                    for (int facing = 0; facing < 4; facing++)
                    {
                        var adjacent = cell.Step((Facing)facing);
                        if (grid.Cell(adjacent) != '#') continue;
                        Vector3 direction = Position(adjacent) - Position(cell);
                        var torch = Spawn("torch", cell);
                        torch.transform.position += direction.normalized * 1.7f;
                        torch.transform.rotation = Quaternion.LookRotation(-direction);
                        break;
                    }
                }
            }
            foreach (var foe in grid.Foes)
            {
                if (!foe.Alive || foe.Group.Count == 0) continue;
                var model = ArtLibrary.SpawnEnemy(foe.Group[0], transform);
                model.transform.position = Position(foe.Position);
                model.Play("Idle");
                foes[foe.Id] = model;
                if (markerQuad == null) CreateMarkerAssets();
                foeMarkers.Add(CreateFoeMarker(foe, model));
            }
            SnapCamera();
            RefreshProgress();
            var vfx = VfxLibrary.Create();
            vfx.Camera = app.MainCamera;
            ambient = vfx.Play("environment_" + tileset, app.MainCamera.transform.position, Color.white, follow: app.MainCamera.transform);
        }

        void CreateMarkerAssets()
        {
            var shader = Shader.Find("Abyss/VfxUnlit");
            if (shader == null) throw new System.InvalidOperationException("Abyss/VfxUnlit shader is missing.");
            ringMaterial = MarkerMaterial(shader, "ring", true);
            beaconMaterial = MarkerMaterial(shader, "glow", false);
            alertMaterial = MarkerMaterial(shader, "anger", false);
            markerBlock = new MaterialPropertyBlock();
            markerQuad = new Mesh { name = "FOE marker quad" };
            markerQuad.vertices = new[] { new Vector3(-.5f, -.5f, 0), new Vector3(.5f, -.5f, 0), new Vector3(.5f, .5f, 0), new Vector3(-.5f, .5f, 0) };
            markerQuad.uv = new[] { new Vector2(0, 0), new Vector2(1, 0), new Vector2(1, 1), new Vector2(0, 1) };
            markerQuad.colors = new[] { Color.white, Color.white, Color.white, Color.white };
            markerQuad.triangles = new[] { 0, 1, 2, 0, 2, 3 };
            markerQuad.RecalculateBounds();
        }
        static Material MarkerMaterial(Shader shader, string texture, bool alpha)
        {
            var resource = Resources.Load<Texture2D>("Vfx/Textures/" + texture);
            if (resource == null) throw new System.InvalidOperationException("Missing VFX texture: " + texture);
            var material = new Material(shader) { name = "FOE marker " + texture, mainTexture = resource };
            // Alpha-blended ring stays legible on bright floors where additive orange washes out.
            material.SetFloat("_DstBlend", (float)(alpha ? UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha : UnityEngine.Rendering.BlendMode.One));
            return material;
        }
        FoeMarker CreateFoeMarker(FoeState foe, CharacterModel model)
        {
            var marker = new FoeMarker
            {
                Foe = foe, Model = model, Phase = foeMarkers.Count * 1.7f,
                RingSize = Mathf.Clamp(model.Radius * 2.6f, 1.6f, 3.4f), HeadHeight = model.Height + 0.45f
            };
            marker.Ring = MarkerPart(model.transform, "FOE threat ring", ringMaterial, out marker.RingRenderer);
            marker.Ring.localPosition = new Vector3(0f, 0.1f, 0f);
            marker.Beacon = MarkerPart(model.transform, "FOE threat beacon", beaconMaterial, out marker.BeaconRenderer);
            marker.Alert = MarkerPart(model.transform, "FOE chase alert", alertMaterial, out marker.AlertRenderer);
            marker.Alert.gameObject.SetActive(false);
            return marker;
        }
        Transform MarkerPart(Transform parent, string name, Material material, out MeshRenderer renderer)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = markerQuad;
            renderer = go.AddComponent<MeshRenderer>();
            renderer.sharedMaterial = material;
            renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            renderer.receiveShadows = false;
            renderer.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
            renderer.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;
            return go.transform;
        }

        GameObject Spawn(string piece, GridPos cell)
        {
            var go = ArtLibrary.SpawnStatic(ArtLibrary.EnvPath(tileset, piece), transform);
            go.transform.position = Position(cell);
            var processed = EnvironmentProcessor.Process(go, app.Atmosphere.Current.TorchColor, 1.5f, 5.5f);
            lights.AddRange(processed.Lights);
            return go;
        }
        public void RefreshProgress()
        {
            var progress = run.Grid.Progress;
            foreach (var pair in chests)
                if (pair.Value != null) pair.Value.localRotation = progress.OpenedChests.Contains(pair.Key) ? Quaternion.Euler(-105, 0, 0) : Quaternion.identity;
            foreach (var pair in doors)
                if (pair.Value != null) pair.Value.localRotation = progress.OpenedDoors.Contains(pair.Key) ? Quaternion.Euler(0, 95, 0) : Quaternion.identity;
            foreach (var pair in keys) pair.Value.SetActive(!progress.TakenKeys.Contains(pair.Key));
            foreach (var foe in run.Grid.Foes)
            {
                if (!foes.TryGetValue(foe.Id, out var model)) continue;
                model.gameObject.SetActive(foe.Alive);
                if (foe.Alive && !busy) model.transform.position = Position(foe.Position);
            }
            RefreshLights();
        }
        void RefreshLights()
        {
            Vector3 eye = app.MainCamera.transform.position;
            foreach (var light in lights) light.enabled = (light.transform.position - eye).sqrMagnitude < 18f * 18f;
        }
        void SnapCamera()
        {
            app.MainCamera.transform.SetPositionAndRotation(Position(run.State.Position) + Vector3.up * 1.35f, Quaternion.Euler(0, (int)run.State.Facing * 90, 0));
        }
        bool CanAct => !busy && !app.Paused && app.Screen == GameScreen.Dungeon && !app.UI.BlocksWorldInput && run.CanAct;
        public void Move(RelativeMove direction) { if (CanAct) StartCoroutine(AnimateStep(run.Move(direction))); }
        public void Turn(int quarterTurns) { if (CanAct) StartCoroutine(AnimateStep(run.Turn(quarterTurns))); }
        public void Interact() { if (CanAct) StartCoroutine(AnimateStep(run.Interact())); }
        public void WaitTurn() { if (CanAct) StartCoroutine(AnimateStep(run.WaitTurn())); }

        IEnumerator AnimateStep(DungeonStepResult result)
        {
            busy = true;
            var camera = app.MainCamera.transform;
            Vector3 start = camera.position;
            Quaternion startRotation = camera.rotation;
            Vector3 destination = Position(run.State.Position) + Vector3.up * 1.35f;
            Quaternion destinationRotation = Quaternion.Euler(0, (int)run.State.Facing * 90, 0);
            if (result.FloorChanged || result.ReturnToTown) destination = start;
            string sound = SoundFor(result.Effect, result.Moved);
            if (sound != null) AudioManager.Instance.PlaySfx(sound);
            float duration = app.Preferences.ReducedMotion ? 0.05f : 0.24f;
            float elapsed = 0;
            foeStarts.Clear();
            foreach (var pair in foes) foeStarts[pair.Key] = pair.Value.transform.position;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float t = Mathf.Clamp01(elapsed / duration);
                float eased = t * t * (3f - 2f * t);
                camera.position = Vector3.Lerp(start, destination, eased);
                if (result.Moved && !app.Preferences.ReducedMotion) camera.position += Vector3.up * Mathf.Sin(t * Mathf.PI) * 0.04f;
                camera.rotation = Quaternion.Slerp(startRotation, destinationRotation, eased);
                if (!result.FloorChanged)
                    foreach (var foe in run.Grid.Foes)
                    {
                        if (!foes.TryGetValue(foe.Id, out var model) || !foeStarts.TryGetValue(foe.Id, out var from)) continue;
                        Vector3 target = Position(foe.Position);
                        Vector3 delta = target - from;
                        model.transform.position = Vector3.Lerp(from, target, eased);
                        if (delta.sqrMagnitude > 0.01f) { model.transform.rotation = Quaternion.LookRotation(delta); model.Play("Run"); }
                    }
                yield return null;
            }
            foreach (var pair in foes) pair.Value.Play("Idle");
            camera.SetPositionAndRotation(destination, destinationRotation);
            busy = false;
            app.HandleDungeonStep(result);
        }
        void Update()
        {
            if (!CanAct) return;
            var keyboard = Keyboard.current;
            var gamepad = Gamepad.current;
            bool forward = (keyboard?.wKey.isPressed ?? false) || (keyboard?.upArrowKey.isPressed ?? false) || (gamepad?.dpad.up.isPressed ?? false);
            bool back = (keyboard?.sKey.isPressed ?? false) || (keyboard?.downArrowKey.isPressed ?? false) || (gamepad?.dpad.down.isPressed ?? false);
            bool left = (keyboard?.aKey.isPressed ?? false) || (keyboard?.leftArrowKey.isPressed ?? false) || (gamepad?.dpad.left.isPressed ?? false);
            bool right = (keyboard?.dKey.isPressed ?? false) || (keyboard?.rightArrowKey.isPressed ?? false) || (gamepad?.dpad.right.isPressed ?? false);
            if (!(forward || back || left || right)) nextHeldInput = 0;
            if (Time.unscaledTime >= nextHeldInput && (forward || back || left || right))
            {
                nextHeldInput = Time.unscaledTime + 0.28f;
                if (forward) Move(RelativeMove.Forward);
                else if (back) Move(RelativeMove.Back);
                else if (left) Turn(-1);
                else Turn(1);
            }
            else if ((keyboard?.qKey.wasPressedThisFrame ?? false) || (gamepad?.leftShoulder.wasPressedThisFrame ?? false)) Move(RelativeMove.Left);
            else if ((keyboard?.rKey.wasPressedThisFrame ?? false) || (gamepad?.rightShoulder.wasPressedThisFrame ?? false)) Move(RelativeMove.Right);
            else if ((keyboard?.eKey.wasPressedThisFrame ?? false) || (keyboard?.spaceKey.wasPressedThisFrame ?? false) || (gamepad?.buttonSouth.wasPressedThisFrame ?? false)) Interact();
            else if ((keyboard?.periodKey.wasPressedThisFrame ?? false) || (gamepad?.buttonWest.wasPressedThisFrame ?? false)) WaitTurn();
        }
        static string SoundFor(DungeonEffect effect, bool moved)
        {
            switch (effect)
            {
                case DungeonEffect.Blocked: case DungeonEffect.DoorLocked: return "sfx_ui_error";
                case DungeonEffect.DoorOpened: return "sfx_door";
                case DungeonEffect.Treasure: return "sfx_chest";
                case DungeonEffect.Key: return "sfx_item";
                case DungeonEffect.Trap: return "sfx_hit";
                case DungeonEffect.Spring: return "sfx_heal";
                case DungeonEffect.Warp: return "sfx_warp";
                case DungeonEffect.Stairs: return "sfx_stairs";
                default: return moved ? "sfx_footstep" : null;
            }
        }
        // Markers are children of FOE models: hidden with the model on defeat, destroyed with it. Scaled time freezes them while paused.
        void LateUpdate()
        {
            if (foeMarkers.Count == 0 || app == null) return;
            bool reduced = app.Preferences.ReducedMotion;
            var view = app.MainCamera.transform;
            Quaternion viewRotation = view.rotation;
            Vector3 eye = view.position;
            float time = Time.time;
            for (int i = 0; i < foeMarkers.Count; i++)
            {
                var marker = foeMarkers[i];
                if (marker.Model == null || !marker.Model.gameObject.activeInHierarchy) continue;
                bool chasing = marker.Foe.Alive && marker.Foe.Chasing;
                if (chasing != marker.Chasing)
                {
                    marker.Chasing = chasing;
                    marker.Alert.gameObject.SetActive(chasing);
                    marker.Model.SetTint(chasing ? FoeChaseBodyTint : Color.white);
                }
                float t = time + marker.Phase;
                float pulse = reduced ? 0f : Mathf.Sin(t * (chasing ? 7f : 2.2f));
                float ring = marker.RingSize * (chasing ? 1.18f : 1f) * (1f + pulse * (chasing ? 0.07f : 0.03f));
                marker.Ring.localScale = new Vector3(ring, ring, 1f);
                marker.Ring.rotation = Quaternion.Euler(90f, 0f, reduced ? 0f : t * (chasing ? 90f : 25f));
                Tint(marker.RingRenderer, chasing ? FoeChaseColor : FoeThreatColor, chasing ? 0.85f + 0.15f * pulse : 0.55f + 0.1f * pulse);
                float bob = reduced ? 0f : Mathf.Sin(t * 2.4f) * 0.08f;
                var head = new Vector3(0f, marker.HeadHeight + bob, 0f);
                marker.Beacon.localPosition = head;
                marker.Beacon.rotation = viewRotation;
                float beacon = (chasing ? 1.1f : 0.6f) * (1f + pulse * 0.08f);
                marker.Beacon.localScale = new Vector3(beacon, beacon, 1f);
                Tint(marker.BeaconRenderer, chasing ? FoeChaseColor : FoeThreatColor, chasing ? 0.45f : 0.8f);
                if (chasing)
                {
                    marker.Alert.localPosition = head;
                    marker.Alert.rotation = viewRotation;
                    float alert = 0.6f * (1f + pulse * 0.1f);
                    marker.Alert.localScale = new Vector3(alert, alert, 1f);
                    Tint(marker.AlertRenderer, FoeAlertColor, 1f);
                    // Presentation only: a chaser turns to face the party between steps.
                    if (!busy && !app.Paused)
                    {
                        var body = marker.Model.transform;
                        Vector3 toward = eye - body.position;
                        toward.y = 0f;
                        if (toward.sqrMagnitude > 0.01f)
                        {
                            var facing = Quaternion.LookRotation(toward);
                            body.rotation = reduced ? facing : Quaternion.RotateTowards(body.rotation, facing, 300f * Time.deltaTime);
                        }
                    }
                }
            }
        }
        void Tint(Renderer renderer, Color color, float alpha)
        {
            color.a = alpha;
            markerBlock.SetColor(TintId, color);
            renderer.SetPropertyBlock(markerBlock);
        }
        void OnDisable() => ambient.Stop();
        void OnDestroy()
        {
            if (markerQuad != null) Destroy(markerQuad);
            if (ringMaterial != null) Destroy(ringMaterial);
            if (beaconMaterial != null) Destroy(beaconMaterial);
            if (alertMaterial != null) Destroy(alertMaterial);
        }
    }
}
