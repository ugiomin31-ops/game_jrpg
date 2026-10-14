using System.Collections.Generic;
using UnityEngine;

namespace Abyss.Runtime.World
{
    /// <summary>
    /// Third-person orbit camera for the guild town: a pivot at the leader's chest, a distance (3.5-10 m) that also
    /// drives the pitch (close = low and cinematic, far = higher and tactical), a damped yaw the player can turn,
    /// geometry-aware pull-in (fast in, slow out) and a two-shot blend used while talking to an NPC.
    /// <para>The town's colliders are crude (low boxes under tall shops, thin tree trunks), so the camera also reads the
    /// visible bounds of the guild buildings and of trees, carts and booths: buildings pull the camera in, props only
    /// make it climb above them (higher pitch) or tuck in, so it never sits inside a tree crown or a cart canopy.</para>
    /// </summary>
    public sealed class TownCamera
    {
        public const float DefaultDistance = 6.5f;
        public const float MinDistance = 3.5f;
        public const float MaxDistance = 10f;
        /// <summary>Yaw of the previous fixed offset (6.5, 8, -9.5): the camera looks along +Z rotated toward -X.</summary>
        public const float LegacyYaw = -34.4f;

        const float PivotHeight = 1.3f;
        const float NearPitch = 12f, FarPitch = 35f, MaxPitch = 42f;
        const float OrbitFov = 50f, TalkFov = 40f;
        const float ProbeRadius = 0.3f;
        const float MinReach = 1.5f;
        static readonly float[] ClimbSteps = { 0f, 6f, 12f, 18f };

        readonly Camera camera;
        readonly List<Bounds> walls = new List<Bounds>();
        readonly List<Bounds> covers = new List<Bounds>();
        readonly List<Crown> crowns = new List<Crown>();
        /// <summary>Cells (0.5 m) of horizontal overhead sheets: roofs, awnings, parasols, the entrance canopy.</summary>
        readonly HashSet<long> overhead = new HashSet<long>();
        const float Cell = 0.5f, BandMin = 1.5f, BandMax = 8f;
        static readonly List<Vector3> MeshVertices = new List<Vector3>();
        static readonly List<int> MeshTriangles = new List<int>();
        readonly MaterialPropertyBlock block = new MaterialPropertyBlock();
        static readonly int AlphaId = Shader.PropertyToID("_Alpha");

        /// <summary>A tree: turns see-through while it covers the leader or holds the lens (Fade = eased ramp progress 0..1).</summary>
        sealed class Crown { public Renderer Renderer; public Bounds Bounds; public float Fade; public Material[] Opaque, Clear; }
        readonly RaycastHit[] hits = new RaycastHit[32];
        bool reduced;

        float yaw = LegacyYaw, yawTarget = LegacyYaw, yawVelocity;
        float avoid, avoidTarget, avoidVelocity;
        static readonly float[] AvoidSteps = { 12f, 25f, 40f, 55f, 70f, 90f, 115f, 145f, 180f };
        float distance = DefaultDistance, distanceTarget = DefaultDistance;
        float pitchLift, reach = DefaultDistance;
        Vector3 pivot;
        bool ready;

        bool talking;
        float talkBlend, talkSide = 1f, talkAngle = 36f, talkNpcHeight = 1.7f;
        Vector3 talkNpc;

        public TownCamera(Camera camera) { this.camera = camera; }

        /// <summary>Yaw (degrees) the player asked for.</summary>
        public float Yaw => yaw;
        /// <summary>Yaw the lens really uses (the requested yaw plus the swing that keeps it out of a wall): movement is mapped against this.</summary>
        public float ViewYaw => yaw + avoid;
        /// <summary>0..1 weight of the two-shot (labels hide while it is up).</summary>
        public float TalkWeight => talkBlend;
        public float Distance => distanceTarget;
        public float Pitch { get; private set; }
        public bool Talking => talking;
        public bool Reduced { set { reduced = value; } }

        /// <summary>Indexes the buildings and props the camera must keep out of (once, after the town is processed).</summary>
        public void Collect(Transform townRoot)
        {
            Release();
            walls.Clear(); covers.Clear(); crowns.Clear(); overhead.Clear();
            var raw = new HashSet<long>();
            foreach (var r in townRoot.GetComponentsInChildren<Renderer>())
            {
                if (r is ParticleSystemRenderer || r is TrailRenderer || r is LineRenderer) continue;
                Bounds b = r.bounds;
                string n = r.transform.name;
                Vector3 s = b.size;
                if (n.StartsWith("Tree"))
                {
                    var crown = new Bounds(b.center, new Vector3(s.x * 0.75f, s.y, s.z * 0.75f));
                    crown.SetMinMax(new Vector3(crown.min.x, Mathf.Max(crown.min.y, 1.3f), crown.min.z), crown.max);
                    crowns.Add(new Crown { Renderer = r, Bounds = crown });
                    continue;
                }
                if (n.StartsWith("Guild_Clinic") || n.StartsWith("Guild_Market") || n.StartsWith("Guild_Workshop") || n.StartsWith("Gate_Portal")) walls.Add(b);
                else if (n.StartsWith("Guild_HQ"))
                    // The HQ body has a collider; its entrance canopy (roof underside at 3.9 m, measured from the mesh) does not.
                    walls.Add(new Bounds(new Vector3(b.center.x - 0.25f, 3f, b.min.z + 1.95f), new Vector3(10.9f, 6f, 4.1f)));
                if (n.StartsWith("Kit_") || n.StartsWith("City_") || n == "Plaza") continue;
                if (!Voxelize(r, raw) && !n.StartsWith("Guild_") && Mathf.Max(s.x, s.z) < 8f && Mathf.Min(s.x, s.z) >= 1.6f && s.y >= 1.8f)
                    covers.Add(b);   // unreadable mesh: its box is the best we have
            }
            // Only broad horizontal sheets count (roofs, awnings, parasols, at least 1.5 m across): posts, cables and thin ribbons never fill their 3x3 block.
            foreach (long key in raw)
            {
                Unpack(key, out int x, out int y, out int z);
                int sides = 0;
                for (int dx = -1; dx <= 1; dx++)
                    for (int dz = -1; dz <= 1; dz++)
                        if ((dx != 0 || dz != 0) && raw.Contains(Key(x + dx, y, z + dz))) sides++;
                if (sides >= 7) overhead.Add(key);
            }
        }

        static long Key(int x, int y, int z) => ((long)(x & 0x1FFFFF) << 42) | ((long)(y & 0x1FFFFF) << 21) | (long)(z & 0x1FFFFF);
        static int Signed(long v) { int i = (int)(v & 0x1FFFFF); return i >= 0x100000 ? i - 0x200000 : i; }
        static void Unpack(long key, out int x, out int y, out int z) { x = Signed(key >> 42); y = Signed(key >> 21); z = Signed(key); }

        /// <summary>Rasterises the part of a readable mesh between 1.5 and 8 m into 0.5 m cells.</summary>
        static bool Voxelize(Renderer r, HashSet<long> cells)
        {
            var filter = r.GetComponent<MeshFilter>();
            Mesh mesh = filter != null ? filter.sharedMesh : null;
            if (mesh == null || !mesh.isReadable) return false;
            mesh.GetVertices(MeshVertices);
            Matrix4x4 toWorld = r.transform.localToWorldMatrix;
            for (int i = 0; i < MeshVertices.Count; i++) MeshVertices[i] = toWorld.MultiplyPoint3x4(MeshVertices[i]);
            for (int sub = 0; sub < mesh.subMeshCount; sub++)
            {
                mesh.GetTriangles(MeshTriangles, sub);
                for (int t = 0; t + 2 < MeshTriangles.Count; t += 3)
                {
                    Vector3 a = MeshVertices[MeshTriangles[t]], b = MeshVertices[MeshTriangles[t + 1]], c = MeshVertices[MeshTriangles[t + 2]];
                    if (Mathf.Max(a.y, Mathf.Max(b.y, c.y)) < BandMin || Mathf.Min(a.y, Mathf.Min(b.y, c.y)) > BandMax) continue;
                    float edge = Mathf.Max((a - b).magnitude, Mathf.Max((b - c).magnitude, (c - a).magnitude));
                    int n = Mathf.Clamp(Mathf.CeilToInt(edge / (Cell * 0.5f)), 1, 48);
                    for (int u = 0; u <= n; u++)
                        for (int v = 0; v <= n - u; v++)
                        {
                            Vector3 p = a + (b - a) * (u / (float)n) + (c - a) * (v / (float)n);
                            if (p.y < BandMin || p.y > BandMax) continue;
                            cells.Add(Key(Mathf.FloorToInt(p.x / Cell), Mathf.FloorToInt(p.y / Cell), Mathf.FloorToInt(p.z / Cell)));
                        }
                }
            }
            return true;
        }

        public void AddYaw(float degrees) { yawTarget += degrees; }
        public void AddZoom(float meters) { distanceTarget = Mathf.Clamp(distanceTarget + meters, MinDistance, MaxDistance); }
        public void ResetYaw(float degrees) { yaw = yawTarget = degrees; yawVelocity = 0f; }

        public void BeginTalk(Vector3 playerPosition, Vector3 npcPosition, float npcHeight)
        {
            talking = true;
            talkNpc = npcPosition; talkNpcHeight = npcHeight;
            Vector3 d = npcPosition - playerPosition; d.y = 0f;
            if (d.sqrMagnitude < 0.01f) d = Quaternion.Euler(0f, ViewYaw, 0f) * Vector3.forward;
            d.Normalize();
            Vector3 right = Vector3.Cross(Vector3.up, d);
            float preferred = Vector3.Dot(camera.transform.position - playerPosition, right) >= 0f ? 1f : -1f;
            // Keep the side the lens is already on unless a wall or prop is in the way there; then try the other side and a wider angle.
            float bestScore = float.MinValue;
            foreach (float angle in new[] { 36f, 58f, 18f })
                for (int k = 0; k < 2; k++)
                {
                    float side = k == 0 ? preferred : -preferred;
                    TalkOffset(playerPosition, side, angle, out Vector3 look, out Vector3 dir, out float length);
                    float r = ClearReach(look, dir, length) / length;
                    float score = r - (k == 0 ? 0f : 0.04f) - (angle == 36f ? 0f : 0.03f);
                    if (score > bestScore) { bestScore = score; talkSide = side; talkAngle = angle; }
                    if (r >= 0.92f && k == 0 && angle == 36f) { bestScore = float.MaxValue; break; }
                }
        }

        public void EndTalk() { talking = false; }

        public void Snap(Vector3 playerPosition) { ready = false; Update(playerPosition, 0.016f, true); }

        public void Update(Vector3 playerPosition, float dt, bool snap)
        {
            dt = Mathf.Clamp(dt, 0.0001f, 0.1f);
            Vector3 want = playerPosition + Vector3.up * PivotHeight;
            if (snap || !ready) pivot = want;
            else
            {
                float kh = 1f - Mathf.Exp(-(reduced ? 24f : 11f) * dt), kv = 1f - Mathf.Exp(-8f * dt);
                pivot.x += (want.x - pivot.x) * kh;
                pivot.z += (want.z - pivot.z) * kh;
                pivot.y += (want.y - pivot.y) * kv;
            }

            yawTarget = yaw + Mathf.DeltaAngle(yaw, yawTarget);
            yaw = snap || !ready ? yawTarget : Mathf.SmoothDampAngle(yaw, yawTarget, ref yawVelocity, reduced ? 0.05f : 0.14f, float.MaxValue, dt);
            distance = snap || !ready ? distanceTarget : Mathf.Lerp(distance, distanceTarget, 1f - Mathf.Exp(-(reduced ? 24f : 9f) * dt));

            // Close = low and filmic, far = high enough to read the street.
            float t = Mathf.InverseLerp(MinDistance, MaxDistance, distance);
            float basePitch = Mathf.Lerp(NearPitch, FarPitch, Mathf.Pow(t, 1.15f));
            avoidTarget = SolveAvoid(basePitch);
            avoid = snap || !ready ? avoidTarget : Mathf.SmoothDampAngle(avoid, avoidTarget, ref avoidVelocity, reduced ? 0.12f : 0.4f, float.MaxValue, dt);
            Solve(basePitch, out float targetLift, out float targetReach);
            if (snap || !ready) { pitchLift = targetLift; reach = targetReach; }
            else
            {
                pitchLift = Mathf.Lerp(pitchLift, targetLift, 1f - Mathf.Exp(-(targetLift > pitchLift ? 5f : 2.5f) * dt * (reduced ? 3f : 1f)));
                float rate = targetReach < reach ? (reduced ? 30f : 16f) : (reduced ? 6f : 2.2f);
                reach = Mathf.Lerp(reach, targetReach, 1f - Mathf.Exp(-rate * dt));
            }
            Pitch = Mathf.Min(basePitch + pitchLift, MaxPitch);
            Quaternion orbitRotation = Quaternion.Euler(Pitch, ViewYaw, 0f);
            Vector3 back = orbitRotation * Vector3.back;
            reach = Mathf.Min(reach, ClearReach(pivot, back, reach));      // hard guarantee: never inside geometry
            Vector3 orbitPosition = pivot + back * reach;

            UpdateCrowns(orbitPosition, playerPosition, snap ? 10f : dt);

            // Two-shot blend.
            float blendTime = reduced ? 0.25f : 0.5f;
            talkBlend = Mathf.MoveTowards(talkBlend, talking ? 1f : 0f, (snap ? 1f : dt / blendTime));
            if (!ready || talkBlend <= 0f)
            {
                camera.transform.SetPositionAndRotation(orbitPosition, orbitRotation);
                camera.fieldOfView = OrbitFov;
            }
            else
            {
                ComputeTalkPose(playerPosition, out Vector3 talkPosition, out Quaternion talkRotation);
                float e = Mathf.SmoothStep(0f, 1f, talkBlend);
                camera.transform.SetPositionAndRotation(Vector3.Lerp(orbitPosition, talkPosition, e), Quaternion.Slerp(orbitRotation, talkRotation, e));
                camera.fieldOfView = Mathf.Lerp(OrbitFov, TalkFov, e);
            }
            ready = true;
        }

        /// <summary>
        /// See-through trees: while a crown actually covers the leader's capsule from this lens (sight lines to the feet,
        /// chest and head) or holds the lens, the whole tree eases to a translucent fade and back. The fade swaps in a
        /// runtime clone of the tree's own material set to alpha blending (transparent queue, depth kept so the crown
        /// stays one clean layer, shadow kept); the Tripo mesh, texture and shared material are never changed.
        /// </summary>
        void UpdateCrowns(Vector3 lens, Vector3 leader, float dt)
        {
            for (int i = 0; i < crowns.Count; i++)
            {
                var crown = crowns[i];
                Bounds near = crown.Bounds; near.Expand(1.0f);
                bool cover = near.Contains(lens);
                for (int k = 0; k < CapsuleHeights.Length && !cover; k++)
                {
                    Vector3 target = leader + Vector3.up * CapsuleHeights[k], to = target - lens;
                    float length = to.magnitude;
                    if (length < 0.01f) continue;
                    cover = crown.Bounds.IntersectRay(new Ray(lens, to / length), out float d) && d < length - 0.35f;
                }
                float goal = cover ? 1f : 0f;
                if (Mathf.Approximately(crown.Fade, goal)) continue;
                crown.Fade = Mathf.MoveTowards(crown.Fade, goal, dt / (reduced ? CrownFadeTime * .35f : CrownFadeTime));
                if (crown.Renderer == null) continue;
                bool faded = crown.Fade > 0.001f;
                if (faded && crown.Opaque == null)
                {
                    crown.Opaque = crown.Renderer.sharedMaterials;
                    crown.Clear = new Material[crown.Opaque.Length];
                    for (int m = 0; m < crown.Opaque.Length; m++) crown.Clear[m] = SeeThrough(crown.Opaque[m]);
                }
                if (crown.Opaque != null) crown.Renderer.sharedMaterials = faded ? crown.Clear : crown.Opaque;
                crown.Renderer.GetPropertyBlock(block);
                block.SetFloat(AlphaId, faded ? 1f - CrownSeeThrough * Mathf.SmoothStep(0f, 1f, crown.Fade) : 1f);
                crown.Renderer.SetPropertyBlock(block);
            }
        }
        /// <summary>Alpha-blended clone of a tree material (runtime only; destroyed with the town in <see cref="Release"/>).</summary>
        static Material SeeThrough(Material source)
        {
            if (source == null) return null;
            var clone = new Material(source) { name = source.name + " (see-through)", renderQueue = 3000 };
            clone.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
            clone.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            clone.SetFloat("_ZWrite", 1f);
            clone.SetFloat("_ShadowKeep", 1f);
            clone.SetOverrideTag("RenderType", "Transparent");
            return clone;
        }
        /// <summary>Restores the trees' own materials and destroys the see-through clones (town teardown).</summary>
        public void Release()
        {
            foreach (var crown in crowns)
            {
                if (crown.Renderer != null && crown.Opaque != null) { crown.Renderer.sharedMaterials = crown.Opaque; crown.Renderer.SetPropertyBlock(null); }
                if (crown.Clear != null) foreach (var m in crown.Clear) if (m != null) UnityEngine.Object.Destroy(m);
                crown.Opaque = crown.Clear = null; crown.Fade = 0f;
            }
        }
        /// <summary>Leader capsule sample heights (m), how much of a covering crown fades away, and the ramp time (s).</summary>
        static readonly float[] CapsuleHeights = { 0.25f, 1.0f, 1.65f };
        const float CrownSeeThrough = .68f, CrownFadeTime = .35f;

        /// <summary>Where the two-shot lens sits relative to the point it looks at, for one side and angle off the player-NPC line.</summary>
        void TalkOffset(Vector3 playerPosition, float side, float angleDegrees, out Vector3 look, out Vector3 dir, out float length)
        {
            Vector3 p = playerPosition + Vector3.up * 1.35f;
            Vector3 n = talkNpc + Vector3.up * Mathf.Max(1.2f, talkNpcHeight * 0.85f);
            Vector3 flat = n - p; flat.y = 0f;
            float separation = flat.magnitude;
            Vector3 d = separation > 0.01f ? flat / separation : Quaternion.Euler(0f, ViewYaw, 0f) * Vector3.forward;
            look = Vector3.Lerp(p, n, 0.56f);
            look.y -= 0.05f;
            Vector3 right = Vector3.Cross(Vector3.up, d);
            float radius = 2.35f + separation * 0.5f;
            float angle = angleDegrees * Mathf.Deg2Rad;
            Vector3 offset = (-d * Mathf.Cos(angle) + right * side * Mathf.Sin(angle)) * radius + Vector3.up * 0.45f;
            length = offset.magnitude;
            dir = offset / length;
        }

        /// <summary>Over-the-shoulder two-shot: the lens sits behind the leader, offset to the side picked in <see cref="BeginTalk"/>.</summary>
        void ComputeTalkPose(Vector3 playerPosition, out Vector3 position, out Quaternion rotation)
        {
            TalkOffset(playerPosition, talkSide, talkAngle, out Vector3 look, out Vector3 dir, out float length);
            position = look + dir * Mathf.Min(length, ClearReach(look, dir, length));
            rotation = Quaternion.LookRotation(look - position, Vector3.up);
        }

        /// <summary>
        /// Picks the pitch lift and reach for the wanted distance: the first candidate whose camera point is clear of
        /// props (and not squeezed by a wall) wins; otherwise the least bad one.
        /// </summary>
        void Solve(float basePitch, out float bestLift, out float bestReach)
        {
            bestLift = 0f; bestReach = distance;
            float bestScore = float.MinValue;
            for (int i = 0; i < 7; i++)
            {
                float lift, scale;
                if (i < ClimbSteps.Length) { lift = ClimbSteps[i]; scale = 1f; }
                else if (i == 4) { lift = 18f; scale = 0.75f; }
                else if (i == 5) { lift = 0f; scale = 0.7f; }
                else { lift = 10f; scale = 0.6f; }
                lift = Mathf.Min(lift, Mathf.Max(0f, MaxPitch - basePitch));
                float wanted = distance * scale;
                Vector3 back = Quaternion.Euler(basePitch + lift, ViewYaw, 0f) * Vector3.back;
                float r = Mathf.Min(wanted, ClearReach(pivot, back, wanted));
                bool covered = InCover(pivot + back * r);
                float score = r / wanted - (covered ? 0.6f : 0f) - lift * 0.004f - (1f - scale) * 0.05f;
                if (!covered && r >= wanted * 0.85f) { bestLift = lift; bestReach = r; return; }
                if (score > bestScore) { bestScore = score; bestLift = lift; bestReach = r; }
            }
        }

        /// <summary>
        /// Swings the lens around the leader when a building is right behind them (hugging a wall, a narrow lane): the
        /// smallest turn that gives the wanted distance wins, preferring the side already in use so it never flips.
        /// </summary>
        float SolveAvoid(float basePitch)
        {
            float wanted = distance;
            float pitch = basePitch;
            if (Fits(Quaternion.Euler(pitch, yaw, 0f) * Vector3.back, wanted)) return 0f;
            float side = avoidTarget < 0f ? -1f : 1f;
            float best = 0f, bestReach = -1f;
            for (int i = 0; i < AvoidSteps.Length; i++)
                for (int k = 0; k < 2; k++)
                {
                    float offset = AvoidSteps[i] * (k == 0 ? side : -side);
                    Vector3 back = Quaternion.Euler(pitch, yaw + offset, 0f) * Vector3.back;
                    float r = ClearReach(pivot, back, wanted);
                    if (r >= wanted * 0.8f && !InCover(pivot + back * r)) return offset;   // a swing must also land clear of roofs and props
                    if (r > bestReach + 0.05f) { bestReach = r; best = offset; }
                }
            return best;
        }

        /// <summary>The camera must not sit inside a collider (a column, a kiosk) even when pulling in ignores it.</summary>
        static bool InSolid(Vector3 point) => Physics.CheckSphere(point, 0.3f, ~(1 << 8), QueryTriggerInteraction.Ignore);

        bool Fits(Vector3 back, float wanted)
        {
            float r = ClearReach(pivot, back, wanted);
            return r >= wanted * 0.8f && !InSolid(pivot + back * r);
        }

        bool InCover(Vector3 point)
        {
            if (InSolid(point)) return true;
            if (overhead.Count > 0)
            {
                int cx = Mathf.FloorToInt(point.x / Cell), cy = Mathf.FloorToInt(point.y / Cell), cz = Mathf.FloorToInt(point.z / Cell);
                for (int dx = -1; dx <= 1; dx++)
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dz = -1; dz <= 1; dz++)
                            if (overhead.Contains(Key(cx + dx, cy + dy, cz + dz))) return true;
            }
            for (int i = 0; i < covers.Count; i++)
            {
                Bounds b = covers[i];
                b.Expand(0.5f);
                if (b.Contains(point)) return true;
            }
            for (int i = 0; i < crowns.Count; i++)
            {
                Bounds b = crowns[i].Bounds;
                b.Expand(0.5f);
                if (b.Contains(point)) return true;
            }
            return false;
        }

        /// <summary>Longest safe distance from <paramref name="from"/> along <paramref name="dir"/> before the lens meets a building.</summary>
        float ClearReach(Vector3 from, Vector3 dir, float max)
        {
            float best = max;
            int count = Physics.SphereCastNonAlloc(from, ProbeRadius, dir, hits, max, ~(1 << 8), QueryTriggerInteraction.Ignore);
            for (int i = 0; i < count; i++)
            {
                var hit = hits[i];
                if (hit.distance <= 0.001f || Ignorable(hit.collider)) continue;
                best = Mathf.Min(best, hit.distance - 0.05f);
            }
            var ray = new Ray(from, dir);
            for (int i = 0; i < walls.Count; i++)
            {
                Bounds raw = walls[i];
                if (raw.Contains(from)) continue;                       // standing on its steps / porch
                Bounds wide = raw;
                wide.Expand(ProbeRadius * 2f);
                float d;
                if (!wide.Contains(from)) { if (wide.IntersectRay(ray, out d)) best = Mathf.Min(best, d - 0.05f); }
                else if (raw.IntersectRay(ray, out d)) best = Mathf.Min(best, d - 0.1f);   // hugging the wall: only the wall itself counts
            }
            return Mathf.Max(best, MinReach * 0.6f);
        }

        /// <summary>Ground, low walls and props (carts, benches, trunks, lamps) never pull the camera in.</summary>
        static bool Ignorable(Collider c)
        {
            Bounds b = c.bounds;
            return b.max.y < 1.45f || (b.size.x < 2.7f && b.size.z < 2.7f);
        }
    }
}
