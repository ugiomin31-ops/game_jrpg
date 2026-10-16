using System.Collections;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Dungeon;
using Abyss.Runtime.Art;
using Abyss.Presentation.Audio;
using Abyss.UI;
using Abyss.Presentation.Vfx;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Abyss.Runtime.World
{
    public sealed class DungeonWorld : MonoBehaviour
    {
        const float CellSize = 4f;
        /// <summary>Run playback rate of a roaming FOE (a cell in 0.24 s is far beyond any Run stride; same cap as battle's enemy run).</summary>
        const float FoeRunRate = 3f;
        // Biome dressing density (percent per wall face beside a walkable cell); see Dress().
        const int OverlayChance = 18, DecorChance = 26;
        static readonly int TintId = Shader.PropertyToID("_Tint");
        static readonly Color FoeThreatColor = new Color(1f, 0.55f, 0.12f);
        static readonly Color FoeChaseColor = new Color(1f, 0.26f, 0.05f);
        static readonly Color FoeAlertColor = new Color(1.6f, 0.75f, 0.25f);
        static readonly Color FoeChaseBodyTint = new Color(1f, 0.82f, 0.7f);
        readonly Dictionary<GridPos, Transform> chests = new Dictionary<GridPos, Transform>();
        // Props standing on a walkable cell (chest, lore stone, spring, key): they shrink away as the camera walks
        // into them instead of filling the screen from the inside.
        readonly List<(Transform Root, Vector3 Scale)> nearProps = new List<(Transform, Vector3)>();
        readonly Dictionary<GridPos, Transform> doors = new Dictionary<GridPos, Transform>();
        /// <summary>
        /// Doors that open by sinking whole into the floor (frame and leaf): restored Tripo doors whose glass is fused to the
        /// frame, so swinging the `Door` leaf would leave shards. Kit doors keep the clean leaf swing. Passability is the
        /// grid's (DungeonGrid.OpenDoor), never this visual.
        /// </summary>
        readonly Dictionary<GridPos, Transform> sinkingDoors = new Dictionary<GridPos, Transform>();
        /// <summary>Boss gates close the corridor until their battle is won (Progress.ClearedBattles), then step aside.</summary>
        readonly Dictionary<GridPos, GameObject> bossGates = new Dictionary<GridPos, GameObject>();
        static readonly HashSet<string> SinkingDoorTilesets = new HashSet<string> { "subway" };
        const float DoorSinkTime = .6f;
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
            app.Atmosphere.Apply(AtmospherePreset.ForFloor(run.Grid.Floor));
            app.Atmosphere.SetupCamera(app.MainCamera, Abyss.Runtime.Art.OutlineContext.Dungeon);
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
                    // Walls buried among walls can never be seen: skip them (about a third of a floor's blocks).
                    if (TouchesOpenCell(grid, cell)) HideBuriedWallFaces(Spawn("wall_" + (char)('a' + variant), cell), grid, cell);
                    continue;
                }
                // stairs_down carries its own opening into the floor; a floor tile would cap it. The tile's ceiling still
                // closes the cell overhead (without it the stairwell looks up into the void).
                var tile = Spawn("floor_" + (char)('a' + variant), cell);
                if (marker == '>') KeepCeilingOnly(tile);
                switch (marker)
                {
                    case 'T':
                        var chest = Spawn("chest", cell);
                        var lidPart = EnvironmentProcessor.Find(chest.transform, "Lid");
                        AgainstWall(chest, grid, cell, ChestWallOffset(chest.transform, lidPart));
                        chests[cell] = lidPart;
                        break;
                    case 'L':
                        var door = Spawn("door_locked", cell);
                        if (grid.Cell(cell.Step(Facing.North)) == '#' && grid.Cell(cell.Step(Facing.South)) == '#') door.transform.Rotate(0, 90, 0);
                        var leaf = EnvironmentProcessor.Find(door.transform, "Door");
                        if (SinkingDoorTilesets.Contains(tileset) || leaf == null) sinkingDoors[cell] = door.transform;
                        else doors[cell] = leaf;
                        break;
                    case '>': Spawn("stairs_down", cell); break;
                    case '<': Spawn("stairs_up", cell); break;
                    case 'K':
                        var key = ArtLibrary.SpawnStatic(ArtLibrary.PropPath("Common", "key_item"), transform);
                        key.transform.position = Position(cell) + Vector3.up * 0.8f;
                        AgainstWall(key, grid, cell, 1.1f);
                        keys[cell] = key;
                        break;
                    case 'H': AgainstWall(Spawn("spring", cell), grid, cell, 1.1f); break;
                    case 'W': Spawn("warp", cell); break;
                    case 'N': AgainstWall(Spawn("lore_stone", cell), grid, cell, 1.35f); break;
                    case 'X': Spawn("trap", cell); break;
                    case 'B':
                        // Like the door, the gate spans its local X: turn it across an east-west corridor so it closes the
                        // passage instead of standing edge-on in the middle of it.
                        var gate = Spawn("boss_gate", cell);
                        if (grid.Cell(cell.Step(Facing.North)) == '#' && grid.Cell(cell.Step(Facing.South)) == '#') gate.transform.Rotate(0, 90, 0);
                        bossGates[cell] = gate;
                        break;
                }
                // Sparse side dressing keeps the centre of every walkable cell clear.
                int torchFacing = -1;
                if ((x * 13 + y * 7) % 9 == 0)
                {
                    for (int facing = 0; facing < 4 && torchFacing < 0; facing++)
                    {
                        var adjacent = cell.Step((Facing)facing);
                        if (grid.Cell(adjacent) != '#') continue;
                        torchFacing = facing;
                        Vector3 direction = Position(adjacent) - Position(cell);
                        var torch = Spawn("torch", cell);
                        torch.transform.position += direction.normalized * 1.7f;
                        torch.transform.rotation = Quaternion.LookRotation(-direction);
                    }
                }
                Dress(grid, cell, marker, torchFacing);
            }
            foreach (var foe in grid.Foes)
            {
                if (!foe.Alive || foe.Group.Count == 0) continue;
                var model = ArtLibrary.SpawnEnemy(app.DB, foe.Group[0], transform);
                model.transform.position = Position(foe.Position);
                // A roaming FOE crosses a whole cell during the 0.24 s step: churn its Run at the fastest rate battle uses.
                if (model.Anim is ClipAnimator clips && clips.HasClip("Run")) clips.SetClipRate("Run", FoeRunRate);
                model.Play("Idle");
                foes[foe.Id] = model;
                if (markerQuad == null) CreateMarkerAssets();
                foeMarkers.Add(CreateFoeMarker(foe, model));
            }
            SnapCamera();
            RefreshProgress();
            var vfx = VfxLibrary.Create();
            vfx.Camera = app.MainCamera;
            // A tileset without its own drifting particles simply has none (an unknown key must not stop the floor from loading).
            if (vfx.Supports("environment_" + tileset))
                ambient = vfx.Play("environment_" + tileset, app.MainCamera.transform.position, AtmospherePreset.ParticleTint(run.Grid.Floor), follow: app.MainCamera.transform);
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

        /// <summary>
        /// Tiled wall models export per-face children (Face_N/E/S/W). A face pressed against a neighbouring wall block can
        /// never be seen, so it is switched off. The side a face covers is read from where its mesh sits in the block, not
        /// from its name: the restored subway kit names its east and west faces mirrored (Face_E sits on the -X side), and
        /// trusting the name hid the face an open cell looks at, leaving a black hole. Walls without those children
        /// (procedural kits) have nothing to find and stay exactly as built.
        /// </summary>
        static void HideBuriedWallFaces(GameObject wall, DungeonGrid grid, GridPos cell)
        {
            var hide = new List<GameObject>();
            foreach (var renderer in wall.GetComponentsInChildren<Renderer>())
            {
                var face = FaceRoot(renderer.transform, wall.transform);
                if (face == null) continue;
                Vector3 offset = renderer.bounds.center - wall.transform.position;
                Facing side = Mathf.Abs(offset.x) >= Mathf.Abs(offset.z)
                    ? (offset.x > 0f ? Facing.East : Facing.West)
                    : (offset.z > 0f ? Facing.North : Facing.South);   // grid north (y - 1) is world +Z
                if (grid.Cell(cell.Step(side)) == '#') hide.Add(face.gameObject);
            }
            foreach (var face in hide) face.SetActive(false);
        }

        /// <summary>The Face_* transform a renderer belongs to (itself or an ancestor below the wall root), or null.</summary>
        static Transform FaceRoot(Transform part, Transform wall)
        {
            for (var t = part; t != null && t != wall; t = t.parent)
                if (t.name.StartsWith("Face_", System.StringComparison.Ordinal)) return t;
            return null;
        }

        /// <summary>
        /// Pulls a wall-side prop back toward its cell centre until its (turned) mesh bounds stop
        /// <see cref="WallClearance"/> short of the wall face: deep props such as the bin with its bag otherwise reach into the tiles.
        /// </summary>
        static void KeepOffWall(GameObject prop, Vector3 cellCentre, Vector3 toWall)
        {
            bool any = false; Bounds bounds = default;
            foreach (var renderer in prop.GetComponentsInChildren<Renderer>())
            {
                if (renderer is ParticleSystemRenderer) continue;
                if (!any) { bounds = renderer.bounds; any = true; } else bounds.Encapsulate(renderer.bounds);
            }
            if (!any) return;
            Vector3 axis = new Vector3(Mathf.Abs(toWall.x), 0f, Mathf.Abs(toWall.z));
            float reach = Vector3.Dot(bounds.center - cellCentre, toWall) + Vector3.Dot(bounds.extents, axis);
            float limit = CellSize * .5f - WallClearance;
            if (reach > limit) prop.transform.position -= toWall * (reach - limit);
        }

        /// <summary>Switches off every part of a floor tile except its ceiling pieces (renderers and their colliders).</summary>
        static void KeepCeilingOnly(GameObject tile)
        {
            foreach (var renderer in tile.GetComponentsInChildren<Renderer>())
            {
                if (renderer.name.StartsWith("Ceiling", System.StringComparison.Ordinal)) continue;
                renderer.enabled = false;
                foreach (var collider in renderer.GetComponents<Collider>()) collider.enabled = false;
            }
        }

        static bool TouchesOpenCell(DungeonGrid grid, GridPos cell)
        {
            for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++)
                if (grid.Cell(new GridPos(cell.X + dx, cell.Y + dy)) != '#') return true;
            return false;
        }

        /// <summary>
        /// Biome dressing, purely visual (no colliders) and deterministic per cell so a floor always looks the same.
        /// For each wall face beside this walkable cell (except the torch's): sometimes an overlay_1/2 hung on that
        /// wall face, and on plain floor cells at most one decor_1..6 standing against the wall, 1.45 m toward it and
        /// 1 m to one side, which keeps both walking lines through the cell centre clear. Door, stair and boss cells
        /// stay bare so their frames never clip.
        /// </summary>
        void Dress(DungeonGrid grid, GridPos cell, char marker, int torchFacing)
        {
            if (marker == 'L' || marker == 'B' || marker == '<' || marker == '>') return;
            bool decorAllowed = marker == '.' || marker == 'S' || marker == 'E';
            for (int facing = 0; facing < 4; facing++)
            {
                var wall = cell.Step((Facing)facing);
                if (facing == torchFacing || grid.Cell(wall) != '#') continue;
                Vector3 toWall = (Position(wall) - Position(cell)) / CellSize;
                int hash = CellHash(cell.X, cell.Y, facing);
                if (hash % 100 < OverlayChance)
                {
                    // Overlays are authored on a wall block's -Y (Unity +Z) face: turn that face toward this cell.
                    var overlay = Spawn(hash % 2 == 0 ? "overlay_1" : "overlay_2", wall);
                    overlay.transform.rotation = Quaternion.LookRotation(-toWall);
                }
                if (decorAllowed && hash / 100 % 100 < DecorChance)
                {
                    var decor = Spawn("decor_" + (1 + hash / 10000 % 6), cell);
                    Vector3 side = Vector3.Cross(Vector3.up, toWall) * (((hash >> 20) & 1) == 0 ? -1f : 1f);
                    decor.transform.position += toWall * 1.45f + side * 1f;
                    decor.transform.rotation = Quaternion.LookRotation(-toWall) * Quaternion.Euler(0f, ((hash >> 21) % 5 - 2) * 12f, 0f);
                    KeepOffWall(decor, Position(cell), toWall);
                    decorAllowed = false;
                }
            }
        }

        // Chest lid: opened angle about the hinge (local X) and the animation's peak overshoot share.
        const float ChestOpenAngle = -92f, ChestOvershoot = .06f, ChestWallOffset0 = 1.3f, WallClearance = .08f;
        /// <summary>
        /// How far a chest may stand toward its wall: the authored 1.3 m, pulled in when the body or the swung-open lid
        /// (at the animation's overshoot, from the lid's own mesh bounds about its hinge) would reach into the wall face.
        /// </summary>
        static float ChestWallOffset(Transform chest, Transform lid)
        {
            float back = 0f;   // furthest reach behind the chest origin (local -Z), body or open lid
            foreach (var filter in chest.GetComponentsInChildren<MeshFilter>())
            {
                if (filter.sharedMesh == null) continue;
                var b = filter.sharedMesh.bounds;
                bool isLid = lid != null && filter.transform == lid;
                Quaternion open = Quaternion.Euler(ChestOpenAngle * (1f + ChestOvershoot), 0, 0);
                for (int k = 0; k < 8; k++)
                {
                    var corner = new Vector3((k & 1) == 0 ? b.min.x : b.max.x, (k & 2) == 0 ? b.min.y : b.max.y, (k & 4) == 0 ? b.min.z : b.max.z);
                    Vector3 p = isLid ? lid.parent.TransformPoint(lid.localPosition + lid.localRotation * (open * Vector3.Scale(corner, lid.localScale)))
                        : filter.transform.TransformPoint(corner);
                    back = Mathf.Max(back, -chest.InverseTransformPoint(p).z);
                }
            }
            return Mathf.Clamp(CellSize * .5f - WallClearance - back, 0f, ChestWallOffset0);
        }
        /// <summary>
        /// Moves a cell prop from the centre (where the camera walks) against one of the cell's walls, facing the
        /// cell, and registers it for the near-camera fade. Open cells without a wall keep the prop centred.
        /// </summary>
        void AgainstWall(GameObject prop, DungeonGrid grid, GridPos cell, float offset)
        {
            int start = CellHash(cell.X, cell.Y, 7) % 4;
            for (int i = 0; i < 4; i++)
            {
                int facing = (start + i) % 4;
                if (grid.Cell(cell.Step((Facing)facing)) != '#') continue;
                Vector3 toWall = (Position(cell.Step((Facing)facing)) - Position(cell)) / CellSize;
                prop.transform.position += toWall * offset;
                prop.transform.rotation = Quaternion.LookRotation(-toWall);
                break;
            }
            nearProps.Add((prop.transform, prop.transform.localScale));
        }

        /// <summary>Shrinks cell props the camera is about to pass through (horizontal distance under ~1.6 m).</summary>
        void FadeNearProps()
        {
            if (nearProps.Count == 0 || app == null) return;
            Vector3 eye = app.MainCamera.transform.position;
            for (int i = 0; i < nearProps.Count; i++)
            {
                var (root, scale) = nearProps[i];
                if (root == null) continue;
                Vector3 d = root.position - eye;
                d.y = 0f;
                float k = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.7f, 1.6f, d.magnitude));
                root.localScale = scale * k; // scale only: activation belongs to progress (taken keys)
            }
        }

        static int CellHash(int x, int y, int salt)
        {
            unchecked
            {
                uint h = (uint)x * 374761393u + (uint)y * 668265263u + (uint)salt * 2246822519u;
                h = (h ^ (h >> 13)) * 1274126177u;
                return (int)((h ^ (h >> 16)) & 0x7fffffff);
            }
        }

        GameObject Spawn(string piece, GridPos cell)
        {
            var go = ArtLibrary.SpawnStatic(ArtLibrary.EnvPath(tileset, piece), transform);
            go.transform.position = Position(cell);
            // Cave / vault ceilings ride on floor pieces; they must not shadow the corridor from the sun.
            foreach (var r in go.GetComponentsInChildren<MeshRenderer>())
                if (r.name.StartsWith("Ceiling")) r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            var processed = EnvironmentProcessor.Process(go, app.Atmosphere.Current.TorchColor, 1.5f, 5.5f);
            lights.AddRange(processed.Lights);
            return go;
        }
        public void RefreshProgress()
        {
            var progress = run.Grid.Progress;
            foreach (var pair in chests)
                if (pair.Value != null) pair.Value.localRotation = progress.OpenedChests.Contains(pair.Key) ? Quaternion.Euler(ChestOpenAngle, 0, 0) : Quaternion.identity;
            foreach (var pair in doors)
                if (pair.Value != null) pair.Value.localRotation = progress.OpenedDoors.Contains(pair.Key) ? Quaternion.Euler(0, 95, 0) : Quaternion.identity;
            foreach (var pair in sinkingDoors)
                if (pair.Value != null && pair.Value.gameObject.activeSelf == progress.OpenedDoors.Contains(pair.Key))
                {
                    pair.Value.position = Position(pair.Key);
                    pair.Value.gameObject.SetActive(!progress.OpenedDoors.Contains(pair.Key));
                }
            foreach (var pair in keys) pair.Value.SetActive(!progress.TakenKeys.Contains(pair.Key));
            foreach (var pair in bossGates) if (pair.Value != null) pair.Value.SetActive(!progress.ClearedBattles.Contains(pair.Key));
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
            if (result.Effect == DungeonEffect.Treasure) yield return OpenChestLid();
            if (result.Effect == DungeonEffect.DoorOpened) yield return SinkDoor();
            busy = false;
            app.HandleDungeonStep(result);
        }

        /// <summary>Swings open the lid of the chest that was just opened (closed lid, opened cell) with a gold burst.</summary>
        IEnumerator OpenChestLid()
        {
            Transform lid = null;
            foreach (var pair in chests)
                if (pair.Value != null && run.Grid.Progress.OpenedChests.Contains(pair.Key) && Quaternion.Angle(pair.Value.localRotation, Quaternion.identity) < 1f)
                    lid = pair.Value;
            if (lid == null) yield break;
            var vfx = VfxLibrary.Create();
            vfx.Camera = app.MainCamera;
            vfx.Play("buff", lid.position + Vector3.up * 0.2f, new Color(1f, 0.82f, 0.35f), 1.2f);
            float duration = app.Preferences.ReducedMotion ? 0.05f : 0.42f;
            for (float t = 0; t < duration; t += Time.deltaTime)
            {
                float k = Mathf.Clamp01(t / duration);
                // Overshoot slightly past fully open, then settle.
                float angle = ChestOpenAngle * (1f + ChestOvershoot * Mathf.Sin(k * Mathf.PI)) * (1f - Mathf.Pow(1f - k, 3f));
                lid.localRotation = Quaternion.Euler(angle, 0, 0);
                yield return null;
            }
            lid.localRotation = Quaternion.Euler(ChestOpenAngle, 0, 0);
            yield return new WaitForSeconds(app.Preferences.ReducedMotion ? 0f : 0.15f);
        }
        /// <summary>
        /// A sinking door that was just opened (opened cell, still standing) drops whole into the floor with an ease-in and
        /// a dust puff, then hides. The door sound already played with the step. Reduced motion hides it at once.
        /// </summary>
        IEnumerator SinkDoor()
        {
            Transform door = null; GridPos at = default;
            foreach (var pair in sinkingDoors)
                if (pair.Value != null && pair.Value.gameObject.activeSelf && run.Grid.Progress.OpenedDoors.Contains(pair.Key)) { door = pair.Value; at = pair.Key; }
            if (door == null) yield break;
            Vector3 home = Position(at);
            if (!app.Preferences.ReducedMotion)
            {
                float depth = 0f;
                foreach (var r in door.GetComponentsInChildren<Renderer>()) depth = Mathf.Max(depth, r.bounds.max.y - home.y);
                depth = Mathf.Max(1f, depth) + .05f;
                var vfx = VfxLibrary.Create();
                vfx.Camera = app.MainCamera;
                vfx.Play("spark", home + Vector3.up * 1.3f, new Color(1f, .85f, .4f), 1.2f);   // the lock giving
                vfx.Play("smoke", home + Vector3.up * .3f, new Color(.78f, .76f, .72f), 1.6f, 0, null, home.y);
                for (float t = 0; t < DoorSinkTime; t += Time.deltaTime)
                {
                    float k = Mathf.Clamp01(t / DoorSinkTime);
                    door.position = home + Vector3.down * (depth * k * k);   // ease-in: starts slow, drops away
                    yield return null;
                }
            }
            door.position = home;
            door.gameObject.SetActive(false);
        }
        void Update()
        {
            // HUD buttons consume input before calling the public actions, so only gate raw polling here.
            if (!CanAct || UIInput.ConsumedThisFrame) return;
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
            else
            {
                // Touch: flick up/down to step forward/back, left/right to turn. No tap-to-interact: an empty
                // interaction spends a turn, so stray taps would let foes advance; the HUD pad's 조사 button does it.
                var swipe = UITouch.Swipe;
                if (swipe.y > 0) Move(RelativeMove.Forward);
                else if (swipe.y < 0) Move(RelativeMove.Back);
                else if (swipe.x != 0) Turn(swipe.x);
            }
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
            FadeNearProps();
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
