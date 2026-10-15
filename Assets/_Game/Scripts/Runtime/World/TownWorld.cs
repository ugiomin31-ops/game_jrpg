using System;
using System.Collections.Generic;
using Abyss.Runtime.Art;
using Abyss.Presentation.Audio;
using Abyss.UI;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;

namespace Abyss.Runtime.World
{
    public sealed class TownWorld : MonoBehaviour
    {
        sealed class ServiceSpot
        {
            public string Id;
            public Transform Marker;
            public CharacterModel Npc;
            public TextMeshPro Label;
        }
        sealed class FollowerMotion
        {
            public CharacterController Body;
            public float VerticalSpeed;
            public Vector3 LastPosition;
            public readonly FollowTrail Trail = new FollowTrail();
        }
        // A follower consumes the actual swept positions of the member ahead, never a chord to its current location.
        sealed class FollowTrail
        {
            public const int Capacity = 256;
            readonly Vector3[] points = new Vector3[Capacity];
            int head;
            public int Count { get; private set; }
            public float Length { get; private set; } // Horizontal length between queued points.
            public bool HasRoom => Count < Capacity;
            public Vector3 First => points[head];
            public Vector3 Last => points[(head + Count - 1) % Capacity];

            public void Reset(Vector3 position)
            {
                head = 0; Count = 1; Length = 0f; points[0] = position;
            }
            public void Append(Vector3 position)
            {
                float distance = Count == 0 ? 0f : FlatDistance(Last, position);
                if (Count > 0 && distance < 0.001f) return;
                if (Count > 1)
                {
                    Vector3 previous = points[(head + Count - 2) % Capacity];
                    Vector3 incoming = Last - previous, outgoing = position - Last;
                    incoming.y = outgoing.y = 0f;
                    // Coalesce only forward collinear motion (not reversals/turns), keeping slow straight walks compact.
                    if (Vector3.Dot(incoming, outgoing) > 0f && Vector3.Cross(incoming.normalized, outgoing.normalized).sqrMagnitude < 0.00000001f)
                    {
                        Length += FlatDistance(previous, position) - incoming.magnitude;
                        points[(head + Count - 1) % Capacity] = position;
                        return;
                    }
                }
                // Callers reserve room before moving the predecessor; never overwrite an unvisited corner.
                if (!HasRoom) return;
                points[(head + Count) % Capacity] = position;
                Count++; Length += distance;
            }
            public void Arrive()
            {
                if (Count <= 1) return; // Keep the tail as the origin of the next recorded segment.
                Length = Mathf.Max(0f, Length - FlatDistance(First, points[(head + 1) % Capacity]));
                head = (head + 1) % Capacity; Count--;
            }
        }
        const float FollowSpacing = 0.95f, FollowArrival = 0.015f, MotionStep = 0.1f, MaxMotionDelta = 0.1f;
        const int MaxFollowSteps = 32;
        readonly List<ServiceSpot> services = new List<ServiceSpot>();
        readonly List<CharacterModel> party = new List<CharacterModel>();
        readonly List<FollowerMotion> followers = new List<FollowerMotion>();
        /// <summary>Resource path each party model was spawned from (job outfit or base hero), parallel to <see cref="party"/>.</summary>
        readonly List<string> partyPaths = new List<string>();
        GameApp app;
        CharacterController controller;
        Transform player;
        Vector3 lastLeaderPosition;
        Vector3 heading = Vector3.forward;
        float verticalSpeed;
        bool title;
        float titleTime;
        Vector3 titlePosition;
        Quaternion titleRotation;
        ServiceSpot nearest;
        static readonly string[] NpcIds = { "innkeeper", "shopkeeper", "smith", "guild_clerk", "elder" };
        static readonly string[] NpcLabels = { "윤 간호사 · 의무실", "박 사장 · 헌터 마켓", "곽 장인 · 장비 공방", "서 주임 · 접수처", "백 길드장 · 길드장실" };
        /// <summary>Benched hunters standing at the lounge spots (villager_1..3).</summary>
        readonly List<CharacterModel> lounge = new List<CharacterModel>();
        EnvironmentProcessor.Result layout;
        TownCamera rig;
        ServiceSpot talkSpot, pendingTalk;
        float pendingTimer;
        int talkFrame;
        float talkIdle, runTimer;
        bool lookDrag;

        public void Initialize(GameApp app, bool title)
        {
            this.app = app;
            this.title = title;
            app.Atmosphere.Apply(AtmospherePreset.ForTileset(title ? "town_night" : "town_dawn"));
            app.Atmosphere.SetupCamera(app.MainCamera, Abyss.Runtime.Art.OutlineContext.Town);
            var town = ArtLibrary.SpawnStatic(ArtLibrary.TownPath, transform);
            TownEnrichment.Apply(town);
            layout = EnvironmentProcessor.Process(town, app.Atmosphere.Current.TorchColor, 2f, 7f);
            for (int i = 0; i < NpcIds.Length; i++)
            {
                var marker = RequireSpot(layout, NpcIds[i]);
                var npc = ArtLibrary.SpawnNpc(NpcIds[i], transform);
                npc.transform.SetPositionAndRotation(marker.position, marker.rotation);
                npc.Play("Idle");
                var spot = new ServiceSpot { Id = NpcIds[i], Marker = marker, Npc = npc };
                if (!title) spot.Label = CreateLabel(NpcLabel(i), marker.position + Vector3.up * (npc.Height + 0.3f));
                services.Add(spot);
            }
            SpawnLounge();
            var gate = RequireSpot(layout, "gate");
            services.Add(new ServiceSpot { Id = "gate", Marker = gate, Label = title ? null : CreateLabel("게이트 이동 · 출발", gate.position + Vector3.up * 2.4f) });
            if (title)
            {
                var cameraMarker = RequireSpot(layout, "camera_title");
                titlePosition = cameraMarker.position;
                titleRotation = Quaternion.LookRotation((RequireSpot(layout, "innkeeper").position + RequireSpot(layout, "smith").position + RequireSpot(layout, "elder").position) / 3f + Vector3.up * 1.5f - titlePosition);
                app.MainCamera.transform.SetPositionAndRotation(titlePosition, titleRotation);
                return;
            }
            var spawn = RequireSpot(layout, "spawn");
            SpawnParty(spawn.position, spawn.rotation);
            rig = new TownCamera(app.MainCamera) { Reduced = app.Preferences.ReducedMotion };
            rig.Collect(town.transform);
            FollowCamera(true);
        }

        string NpcLabel(int i)
        {
            string key = "npc_" + NpcIds[i] + "_name";
            string text = app.DB.T(key);
            return text == key ? NpcLabels[i] : text;
        }

        /// <summary>
        /// A hunter in town: rests in the authored relaxed loop (weight shift, a breath, a look around) instead of the
        /// library's near-static attention Idle, unless its class / own layer ships an Idle of its own.
        /// </summary>
        CharacterModel SpawnHunter(string heroId, Transform parent, string jobId)
        {
            var model = ArtLibrary.SpawnHero(heroId, parent, jobId);
            if (model.Anim is ClipAnimator clips && clips.HasClip("RelaxLoop") && !model.HasClassClip("Idle")) clips.RestClip = "RelaxLoop";
            return model;
        }

        void SpawnParty(Vector3 position, Quaternion rotation, List<Pose> poses = null)
        {
            var forward = rotation * Vector3.forward;
            foreach (var hero in app.State.Party)
            {
                var model = SpawnHunter(hero.Id, transform, hero.Job);
                int index = party.Count;
                if (poses != null && index < poses.Count)
                    model.transform.SetPositionAndRotation(poses[index].position, poses[index].rotation);
                else if (poses != null && index > 0)
                    model.transform.SetPositionAndRotation(party[index - 1].transform.position, party[index - 1].transform.rotation);
                else model.transform.SetPositionAndRotation(position - forward * index * 0.9f, rotation);
                model.Play("Idle");
                party.Add(model);
                partyPaths.Add(ArtLibrary.HeroModelPath(hero.Id, hero.Job));
            }
            int followerCount = Mathf.Max(0, party.Count - 1);
            if (followers.Count > followerCount) followers.RemoveRange(followerCount, followers.Count - followerCount);
            RefreshEquipment();
            AttachController();
            for (int i = 1; i < party.Count; i++) AttachFollowerController(i);
            heading = player.forward;
            lastLeaderPosition = player.position;
        }

        /// <summary>Benched hunters wait at the lounge spots (villager_1..3).</summary>
        void SpawnLounge()
        {
            foreach (var m in lounge) if (m != null) Destroy(m.gameObject);
            lounge.Clear();
            var bench = title || app.State == null ? new List<Abyss.Logic.Game.HeroState>() : app.State.Reserve;
            for (int i = 0; i < 3; i++)
            {
                if (!layout.Spots.TryGetValue("villager_" + (i + 1), out var marker)) continue;
                if (i >= bench.Count) break;
                var npc = SpawnHunter(bench[i].Id, transform, bench[i].Job);
                npc.transform.SetPositionAndRotation(marker.position, marker.rotation);
                npc.Play("Idle");
                lounge.Add(npc);
            }
        }

        /// <summary>After a roster change: respawns the party where the leader stands and the benched hunters in the lounge.</summary>
        public void RefreshRoster()
        {
            if (title || player == null) return;
            CheckFollowerTrails();
            Vector3 position = player.position;
            Quaternion rotation = player.rotation;
            var poses = new List<Pose>();
            foreach (var member in party) poses.Add(new Pose(member.transform.position, member.transform.rotation));
            foreach (var m in party) { m.gameObject.SetActive(false); Destroy(m.gameObject); }
            party.Clear();
            partyPaths.Clear();
            // Paths belong to spatial slots, so a replacement hunter keeps that slot's position and unvisited corners.
            SpawnParty(position, rotation, poses);
            SpawnLounge();
        }

        void AttachController()
        {
            player = party[0].transform;
            player.gameObject.layer = 8;
            controller = player.gameObject.AddComponent<CharacterController>();
            controller.height = 1.35f;
            controller.radius = 0.28f;
            controller.center = Vector3.up * 0.7f;
            controller.stepOffset = 0.24f;
            controller.slopeLimit = 45;
            // Outfit swaps replace the leader's controller; keep the party from blocking itself.
            foreach (var follower in followers)
                if (follower.Body != null && follower.Body.gameObject.activeInHierarchy) Physics.IgnoreCollision(controller, follower.Body);
        }

        void AttachFollowerController(int index)
        {
            var member = party[index];
            member.gameObject.layer = 8; // Like the leader, excluded from camera obstacle probes.
            var body = member.gameObject.AddComponent<CharacterController>();
            body.height = controller.height;
            body.radius = controller.radius;
            body.center = controller.center;
            body.stepOffset = controller.stepOffset;
            body.slopeLimit = controller.slopeLimit;
            body.skinWidth = controller.skinWidth;
            Physics.IgnoreCollision(body, controller);
            for (int i = 0; i < followers.Count; i++)
                if (i != index - 1 && followers[i].Body != null && followers[i].Body.gameObject.activeInHierarchy)
                    Physics.IgnoreCollision(body, followers[i].Body);
            bool added = followers.Count < index;
            var motion = added ? new FollowerMotion() : followers[index - 1];
            motion.Body = body; motion.VerticalSpeed = 0f; motion.LastPosition = member.transform.position;
            if (added)
            {
                motion.Trail.Reset(party[index - 1].transform.position);
                followers.Add(motion);
            }
        }

        /// <summary>After a class change: swaps each hero whose job outfit differs from the spawned model, in place.</summary>
        public void RefreshJobModels()
        {
            if (title) return;
            CheckFollowerTrails();
            bool changed = false;
            for (int i = 0; i < party.Count; i++)
            {
                var old = party[i];
                var hero = app.State.Hero(old.ModelId);
                if (hero == null) continue;
                string path = ArtLibrary.HeroModelPath(old.ModelId, hero.Job);
                if (path == partyPaths[i]) continue;
                var model = SpawnHunter(old.ModelId, transform, hero.Job);
                model.transform.SetPositionAndRotation(old.transform.position, old.transform.rotation);
                model.Play("Idle");
                party[i] = model;
                partyPaths[i] = path;
                old.gameObject.SetActive(false);
                Destroy(old.gameObject);
                if (i == 0) AttachController();
                else AttachFollowerController(i);
                changed = true;
            }
            if (changed) RefreshEquipment();
            RefreshLoungeJobs();
        }

        /// <summary>
        /// Benched hunters in the lounge are dressed once at spawn (outfit + promotion rim for the job they had then)
        /// and never pass through <see cref="RefreshEquipment"/>, so a job change respawns that hunter in place with
        /// the new job's outfit and branch-colour rim.
        /// </summary>
        void RefreshLoungeJobs()
        {
            for (int i = 0; i < lounge.Count; i++)
            {
                var old = lounge[i];
                if (old == null) continue;
                var hero = app.State.Hero(old.ModelId);
                if (hero == null || (hero.Job ?? "") == (old.PromotionJob ?? "")) continue;
                var model = SpawnHunter(old.ModelId, transform, hero.Job);
                model.transform.SetPositionAndRotation(old.transform.position, old.transform.rotation);
                model.Play("Idle");
                lounge[i] = model;
                old.gameObject.SetActive(false);
                Destroy(old.gameObject);
            }
        }

        public void RefreshEquipment()
        {
            foreach (var model in party)
            {
                string id = model.ModelId;
                var hero = app.State.Hero(id);
                string weapon = hero.Equipped("weapon");
                GearDisplay.DressBody(model, GearDisplay.Rank(app.DB, hero.Equipped("armor")), GearDisplay.Rank(app.DB, hero.Equipped("accessory")));
                GearDisplay.AttachWeapon(app.DB, model, app.DB.ClassOf(id) == "archer" ? "weapon.L" : "weapon.R", weapon);
            }
        }

        static Transform RequireSpot(EnvironmentProcessor.Result layout, string name)
        {
            if (!layout.Spots.TryGetValue(name, out var spot)) throw new InvalidOperationException("Town art missing Spot_" + name);
            return spot;
        }
        TextMeshPro CreateLabel(string text, Vector3 position)
        {
            var label = new GameObject("Town Label").AddComponent<TextMeshPro>();
            label.transform.SetParent(transform, false);
            label.transform.position = position;
            label.font = Resources.Load<TMP_FontAsset>("Fonts/Bold SDF");
            label.text = text;
            label.fontSize = 3.2f;
            label.alignment = TextAlignmentOptions.Center;
            label.color = new Color(1f, 0.9f, 0.62f);
            label.rectTransform.sizeDelta = new Vector2(5f, 0.7f);
            label.outlineWidth = 0.16f;
            label.outlineColor = new Color(0.04f, 0.05f, 0.10f);
            return label;
        }
        void Update()
        {
            if (title)
            {
                if (!app.Preferences.ReducedMotion)
                {
                    titleTime += Time.unscaledDeltaTime;
                    app.MainCamera.transform.position = titlePosition + new Vector3(Mathf.Sin(titleTime * 0.12f) * 0.7f, Mathf.Sin(titleTime * 0.18f) * 0.2f, 0);
                    app.MainCamera.transform.rotation = titleRotation;
                }
                return;
            }
            bool labelsVisible = rig == null || rig.TalkWeight < 0.02f;
            foreach (var service in services)
                if (service.Label != null)
                {
                    service.Label.transform.rotation = app.MainCamera.transform.rotation;
                    // Constant on-screen size: the orbit camera sits much closer than the old fixed one.
                    float labelDistance = Vector3.Distance(app.MainCamera.transform.position, service.Label.transform.position);
                    service.Label.transform.localScale = Vector3.one * Mathf.Clamp(labelDistance / 13f, 0.3f, 1f);
                    if (service.Label.enabled != labelsVisible) service.Label.enabled = labelsVisible;
                }
            if (app.Screen != GameScreen.Town || app.Paused || app.UI.BlocksWorldInput || UIInput.ConsumedThisFrame) { IdleParty(); return; }
            UIRoot.Instance?.RequestTouchStick();
            if (pendingTalk != null)
            {
                // Let the two-shot settle (and the person answer) before the facility screen covers the street.
                IdleParty();
                pendingTimer -= Time.unscaledDeltaTime;
                if (pendingTimer <= 0f) { var spot = pendingTalk; pendingTalk = null; app.OpenTownService(spot.Id); }
                return;
            }
            CheckFollowerTrails();
            Vector2 input = ReadMove();
            ReadCamera(input);
            // Movement is relative to the orbit yaw the lens really uses (not the blended pose), so it stays stable through talk blends.
            var yawRotation = Quaternion.Euler(0f, rig.ViewYaw, 0f);
            var forward = yawRotation * Vector3.forward;
            var right = yawRotation * Vector3.right;
            Vector3 motion = Vector3.ClampMagnitude(forward * input.y + right * input.x, 1f);
            // A fully deflected touch stick runs, like holding Shift.
            bool running = (Keyboard.current?.leftShiftKey.isPressed ?? false) || UITouch.Stick.sqrMagnitude > 0.8f;
            float speed = running ? 5.5f : 3.5f;
            Vector3 moved = MoveLeader(motion, speed, Time.deltaTime);
            if (moved.sqrMagnitude > 0.000001f)
            {
                heading = moved.normalized;
                player.rotation = Quaternion.Slerp(player.rotation, Quaternion.LookRotation(heading), Time.deltaTime * 12f);
                party[0].Play(running ? "Run" : "Walk");
            }
            else party[0].Play("Idle");
            UpdateFollowers(speed, running, Time.deltaTime);
            runTimer = moved.sqrMagnitude > 0.000001f ? runTimer + Time.unscaledDeltaTime : 0f;
            UpdateNearest();
            bool confirm = (Keyboard.current?.eKey.wasPressedThisFrame ?? false) || (Keyboard.current?.spaceKey.wasPressedThisFrame ?? false) || (Gamepad.current?.buttonSouth.wasPressedThisFrame ?? false);
            bool click = ((Mouse.current?.leftButton.wasPressedThisFrame ?? false) && !(EventSystem.current?.IsPointerOverGameObject() ?? false)) || UITouch.Tapped;
            if (nearest != null && (confirm || click)) Interact(nearest);
        }

        static float FlatDistance(Vector3 a, Vector3 b)
        {
            Vector3 delta = b - a; delta.y = 0f;
            return delta.magnitude;
        }

        bool CanRecordMove(int index) => index >= followers.Count || followers[index].Trail.HasRoom;

        bool MoveMember(int index, CharacterController body, Vector3 step)
        {
            if (!CanRecordMove(index)) return false;
            body.Move(step);
            Vector3 position = body.transform.position;
            if (index < followers.Count) followers[index].Trail.Append(position);
            if (index == 0) lastLeaderPosition = position;
            else followers[index - 1].LastPosition = position;
            return true;
        }

        Vector3 MoveLeader(Vector3 motion, float speed, float dt)
        {
            dt = Mathf.Clamp(dt, 0f, MaxMotionDelta); // A frame hitch cannot turn into a long corner-cutting jump.
            Vector3 before = player.position;
            if (CanRecordMove(0))
            {
                if (controller.isGrounded && verticalSpeed < 0f) verticalSpeed = -2f;
                else verticalSpeed -= 20f * dt;
                int steps = Mathf.Clamp(Mathf.CeilToInt(motion.magnitude * speed * dt / MotionStep), 1, MaxFollowSteps);
                Vector3 step = (motion * speed + Vector3.up * verticalSpeed) * (dt / steps);
                for (int i = 0; i < steps; i++)
                    if (!MoveMember(0, controller, step)) break;
            }
            Vector3 moved = player.position - before; moved.y = 0f;
            return moved;
        }

        void UpdateFollowers(float speed, bool running, float dt)
        {
            dt = Mathf.Clamp(dt, 0f, MaxMotionDelta);
            for (int i = 1; i < party.Count; i++)
            {
                var follower = party[i];
                var follow = followers[i - 1];
                Vector3 before = follower.transform.position;
                if (CanRecordMove(i))
                {
                    if (follow.Body.isGrounded && follow.VerticalSpeed < 0f) follow.VerticalSpeed = -2f;
                    else follow.VerticalSpeed -= 20f * dt;
                    Vector3 gravity = Vector3.up * follow.VerticalSpeed * dt;
                    float budget = speed * dt;
                    var trail = follow.Trail;
                    // Under buffer pressure close the gap gradually, so very slow/high-refresh movement cannot deadlock a full trail.
                    float gap = FollowSpacing * Mathf.Clamp01((FollowTrail.Capacity - 1 - trail.Count) / 32f);
                    for (int n = 0; n < MaxFollowSteps && budget > 0f && CanRecordMove(i); n++)
                    {
                        Vector3 delta = trail.First - follower.transform.position; delta.y = 0f;
                        float distance = delta.magnitude;
                        if (distance <= FollowArrival)
                        {
                            if (trail.Count <= 1) break;
                            trail.Arrive(); continue;
                        }
                        float travel = Mathf.Min(MotionStep, Mathf.Min(distance, Mathf.Min(budget, Mathf.Max(0f, trail.Length + distance - gap))));
                        if (travel <= 0.0001f) break;
                        Vector3 stepStart = follower.transform.position;
                        MoveMember(i, follow.Body, delta * (travel / distance));
                        budget -= travel;
                        if (FlatDistance(stepStart, follower.transform.position) < 0.0001f) break;
                    }
                    // Apply gravity last, also at rest, so isGrounded reflects the downward sweep rather than a horizontal-only move.
                    if (gravity != Vector3.zero) MoveMember(i, follow.Body, gravity);
                }
                Vector3 moved = follower.transform.position - before; moved.y = 0f;
                if (moved.sqrMagnitude > 0.000001f)
                {
                    follower.transform.rotation = Quaternion.Slerp(follower.transform.rotation, Quaternion.LookRotation(moved), dt * 9f);
                    follower.Play(running ? "Run" : "Walk");
                }
                else follower.Play("Idle");
            }
        }

        void CheckFollowerTrails()
        {
            if ((player.position - lastLeaderPosition).sqrMagnitude > 0.01f) { ResetFollowerTrails(); return; }
            for (int i = 0; i < followers.Count; i++)
                if ((party[i + 1].transform.position - followers[i].LastPosition).sqrMagnitude > 0.01f)
                { ResetFollowerTrails(); return; }
        }

        void ResetFollowerTrails()
        {
            // External relocation invalidates the old route. Do not invent a long trail or warp any member to catch up.
            lastLeaderPosition = player.position; verticalSpeed = 0f;
            for (int i = 0; i < followers.Count; i++)
            {
                followers[i].Trail.Reset(party[i].transform.position);
                followers[i].LastPosition = party[i + 1].transform.position;
                followers[i].VerticalSpeed = 0f;
            }
        }

        void IdleParty()
        {
            foreach (var member in party) member.Play("Idle");
        }

        /// <summary>Talks to a facility: a person in reach gets the two-shot first (the screen opens once it has settled).</summary>
        void Interact(ServiceSpot spot)
        {
            spot.Npc?.PlayOnce("Talk");
            AudioManager.Instance.PlaySfx("sfx_ui_confirm", ui: true);
            if (spot.Npc != null && BeginTalk(spot.Id))
            {
                pendingTalk = spot;
                pendingTimer = app.Preferences.ReducedMotion ? 0.12f : 0.8f;
            }
            else app.OpenTownService(spot.Id);
        }
        void LateUpdate() { if (!title && player != null && app.Screen == GameScreen.Town) FollowCamera(false); }
        /// <summary>Destroys the see-through tree material clones the camera made (the trees' own materials are untouched).</summary>
        void OnDestroy() => rig?.Release();

        /// <summary>
        /// Camera controls: right-mouse drag, Q / E (E is the talk key near a facility, so it only turns the view in the
        /// open), right stick and one-finger drag on the right half rotate; wheel, triggers and pinch zoom.
        /// After a few seconds of walking the view eases toward the direction of travel (never while standing, never with
        /// reduced motion, never right after a manual turn).
        /// </summary>
        void ReadCamera(Vector2 move)
        {
            UITouch.RequestCameraZone();
            float dt = Time.unscaledDeltaTime;
            float yaw = 0f, zoom = 0f;
            var keyboard = Keyboard.current;
            if (keyboard != null)
            {
                if (keyboard.qKey.isPressed) yaw -= 110f * dt;
                if (keyboard.eKey.isPressed && nearest == null) yaw += 110f * dt;
            }
            var mouse = Mouse.current;
            if (mouse != null)
            {
                if (mouse.rightButton.wasPressedThisFrame) lookDrag = !(EventSystem.current?.IsPointerOverGameObject() ?? false);
                if (!mouse.rightButton.isPressed) lookDrag = false;
                if (lookDrag) yaw += mouse.delta.ReadValue().x * 0.2f;
                float wheel = mouse.scroll.ReadValue().y;
                if (Mathf.Abs(wheel) > 0.01f && !(EventSystem.current?.IsPointerOverGameObject() ?? false))
                    zoom -= Mathf.Sign(wheel) * (Mathf.Abs(wheel) > 10f ? Mathf.Clamp(Mathf.Abs(wheel) / 120f, 1f, 4f) : 1f) * 0.8f;
            }
            var pad = Gamepad.current;
            if (pad != null)
            {
                yaw += pad.rightStick.ReadValue().x * 130f * dt;
                zoom += (pad.rightTrigger.ReadValue() - pad.leftTrigger.ReadValue()) * 4.5f * dt;
            }
            if (UITouch.Supported)
            {
                // Dragging the pad "grabs" the street: the view follows the finger.
                yaw -= UITouch.LookDelta.x / Mathf.Max(1f, Screen.width) * 200f;
                zoom -= UITouch.Pinch / Mathf.Max(1f, Screen.width) * 9f;
            }
            bool manual = Mathf.Abs(yaw) > 0.001f || Mathf.Abs(zoom) > 0.001f;
            if (manual) runTimer = 0f;
            if (Mathf.Abs(yaw) > 0.001f) rig.AddYaw(yaw);
            if (Mathf.Abs(zoom) > 0.001f) rig.AddZoom(zoom);
            if (!app.Preferences.ReducedMotion && runTimer > 3f && move.y > 0.2f)
            {
                // Gentle: only a real turn (12-80 degrees off the view) nudges the camera, at most 10 degrees a second.
                float turn = Mathf.Atan2(move.x, move.y) * Mathf.Rad2Deg;
                if (Mathf.Abs(turn) > 12f && Mathf.Abs(turn) < 80f) rig.AddYaw(Mathf.Clamp(turn * 0.2f, -10f, 10f) * dt);
            }
        }

        /// <summary>Called when a facility screen opens: eases to an over-the-shoulder two-shot when the person is close.</summary>
        public bool BeginTalk(string id)
        {
            // Explicit facility entry supersedes any delayed world interaction, including facilities without an NPC.
            pendingTalk = null;
            pendingTimer = 0f;
            if (title || player == null || rig == null) return false;
            foreach (var service in services)
            {
                if (service.Id != id || service.Npc == null) continue;
                if (talkSpot == service) { talkFrame = Time.frameCount; return true; }
                Vector3 delta = service.Marker.position - player.position; delta.y = 0;
                if (delta.sqrMagnitude > 7.5f * 7.5f) return false;
                talkSpot = service;
                talkFrame = Time.frameCount;
                talkIdle = 0f;
                rig.BeginTalk(player.position, service.Npc.transform.position, service.Npc.Height);
                return true;
            }
            return false;
        }
        void UpdateTalk(float dt)
        {
            if (talkSpot == null) return;
            // The facility screen keeps world input blocked; a short grace avoids flicker between chained screens.
            bool open = pendingTalk != null || app.UI.BlocksWorldInput || Time.frameCount <= talkFrame + 3;
            talkIdle = open ? 0f : talkIdle + dt;
            if (talkIdle > 0.25f) { talkSpot = null; rig.EndTalk(); return; }
            Vector3 toNpc = talkSpot.Npc.transform.position - player.position; toNpc.y = 0;
            if (toNpc.sqrMagnitude > 0.04f)
                player.rotation = Quaternion.Slerp(player.rotation, Quaternion.LookRotation(toNpc), 1f - Mathf.Exp(-9f * dt));
        }
        void UpdateNearest()
        {
            ServiceSpot candidate = null;
            float best = 3.2f * 3.2f;
            foreach (var service in services)
            {
                Vector3 delta = service.Marker.position - player.position;
                delta.y = 0;
                float distance = delta.sqrMagnitude;
                if (distance < best) { best = distance; candidate = service; }
                if (service.Label != null) service.Label.color = distance < 3.2f * 3.2f ? Color.white : new Color(1f, 0.9f, 0.62f);
            }
            if (nearest != candidate)
            {
                nearest = candidate;
                if (nearest != null) app.Notify((UIInput.Device == UIInputDevice.Touch ? "탭하여 대화: " : "E / 확인: ") + (nearest.Label != null ? nearest.Label.text : nearest.Id));
            }
        }
        void FollowCamera(bool snap)
        {
            if (rig == null) return;
            float dt = Time.unscaledDeltaTime;
            rig.Reduced = app.Preferences.ReducedMotion;
            if (!snap) UpdateTalk(dt);
            rig.Update(player.position, dt, snap);
        }
        static Vector2 ReadMove()
        {
            Vector2 move = (Gamepad.current?.leftStick.ReadValue() ?? Vector2.zero) + UITouch.Stick;
            var keyboard = Keyboard.current;
            if (keyboard != null)
            {
                if (keyboard.wKey.isPressed || keyboard.upArrowKey.isPressed) move.y += 1;
                if (keyboard.sKey.isPressed || keyboard.downArrowKey.isPressed) move.y -= 1;
                if (keyboard.dKey.isPressed || keyboard.rightArrowKey.isPressed) move.x += 1;
                if (keyboard.aKey.isPressed || keyboard.leftArrowKey.isPressed) move.x -= 1;
            }
            return Vector2.ClampMagnitude(move, 1f);
        }
    }
}
