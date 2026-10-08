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
        readonly List<ServiceSpot> services = new List<ServiceSpot>();
        readonly List<CharacterModel> party = new List<CharacterModel>();
        /// <summary>Resource path each party model was spawned from (job outfit or base hero), parallel to <see cref="party"/>.</summary>
        readonly List<string> partyPaths = new List<string>();
        GameApp app;
        CharacterController controller;
        Transform player;
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

        public void Initialize(GameApp app, bool title)
        {
            this.app = app;
            this.title = title;
            app.Atmosphere.Apply(AtmospherePreset.ForTileset(title ? "town_night" : "town_dawn"));
            app.Atmosphere.SetupCamera(app.MainCamera);
            var town = ArtLibrary.SpawnStatic(ArtLibrary.TownPath, transform);
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
            FollowCamera(true);
        }

        string NpcLabel(int i)
        {
            string key = "npc_" + NpcIds[i] + "_name";
            string text = app.DB.T(key);
            return text == key ? NpcLabels[i] : text;
        }

        void SpawnParty(Vector3 position, Quaternion rotation)
        {
            var forward = rotation * Vector3.forward;
            foreach (var hero in app.State.Party)
            {
                var model = ArtLibrary.SpawnHero(hero.Id, transform, hero.Job);
                model.transform.SetPositionAndRotation(position - forward * party.Count * 0.9f, rotation);
                model.Play("Idle");
                party.Add(model);
                partyPaths.Add(ArtLibrary.HeroModelPath(hero.Id, hero.Job));
            }
            RefreshEquipment();
            AttachController();
            heading = player.forward;
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
                var npc = ArtLibrary.SpawnHero(bench[i].Id, transform, bench[i].Job);
                npc.transform.SetPositionAndRotation(marker.position, marker.rotation);
                npc.Play("Idle");
                lounge.Add(npc);
            }
        }

        /// <summary>After a roster change: respawns the party where the leader stands and the benched hunters in the lounge.</summary>
        public void RefreshRoster()
        {
            if (title || player == null) return;
            Vector3 position = player.position;
            Quaternion rotation = player.rotation;
            foreach (var m in party) { m.gameObject.SetActive(false); Destroy(m.gameObject); }
            party.Clear();
            partyPaths.Clear();
            SpawnParty(position, rotation);
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
        }

        /// <summary>After a class change: swaps each hero whose job outfit differs from the spawned model, in place.</summary>
        public void RefreshJobModels()
        {
            if (title) return;
            bool changed = false;
            for (int i = 0; i < party.Count; i++)
            {
                var old = party[i];
                var hero = app.State.Hero(old.ModelId);
                if (hero == null) continue;
                string path = ArtLibrary.HeroModelPath(old.ModelId, hero.Job);
                if (path == partyPaths[i]) continue;
                var model = ArtLibrary.SpawnHero(old.ModelId, transform, hero.Job);
                model.transform.SetPositionAndRotation(old.transform.position, old.transform.rotation);
                model.Play("Idle");
                party[i] = model;
                partyPaths[i] = path;
                old.gameObject.SetActive(false);
                Destroy(old.gameObject);
                if (i == 0) AttachController();
                changed = true;
            }
            if (changed) RefreshEquipment();
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
            foreach (var service in services)
                if (service.Label != null) service.Label.transform.rotation = app.MainCamera.transform.rotation;
            if (app.Screen != GameScreen.Town || app.Paused || app.UI.BlocksWorldInput) { party[0].Play("Idle"); return; }
            UIRoot.Instance?.RequestTouchStick();
            Vector2 input = ReadMove();
            var forward = app.MainCamera.transform.forward; forward.y = 0; forward.Normalize();
            var right = app.MainCamera.transform.right; right.y = 0; right.Normalize();
            Vector3 motion = Vector3.ClampMagnitude(forward * input.y + right * input.x, 1f);
            // A fully deflected touch stick runs, like holding Shift.
            bool running = (Keyboard.current?.leftShiftKey.isPressed ?? false) || UITouch.Stick.sqrMagnitude > 0.8f;
            float speed = running ? 5.5f : 3.5f;
            if (controller.isGrounded && verticalSpeed < 0) verticalSpeed = -2f;
            else verticalSpeed -= 20f * Time.deltaTime;
            controller.Move((motion * speed + Vector3.up * verticalSpeed) * Time.deltaTime);
            if (motion.sqrMagnitude > 0.01f)
            {
                heading = motion.normalized;
                player.rotation = Quaternion.Slerp(player.rotation, Quaternion.LookRotation(heading), Time.deltaTime * 12f);
                party[0].Play(running ? "Run" : "Walk");
            }
            else party[0].Play("Idle");
            for (int i = 1; i < party.Count; i++)
            {
                var follower = party[i];
                Vector3 target = party[i - 1].transform.position - heading * 0.95f;
                Vector3 delta = target - follower.transform.position;
                delta.y = 0;
                if (delta.sqrMagnitude > 0.2f)
                {
                    follower.transform.position = Vector3.MoveTowards(follower.transform.position, target, speed * Time.deltaTime);
                    follower.transform.rotation = Quaternion.Slerp(follower.transform.rotation, Quaternion.LookRotation(delta), Time.deltaTime * 9f);
                    follower.Play(running ? "Run" : "Walk");
                }
                else follower.Play("Idle");
            }
            UpdateNearest();
            bool confirm = (Keyboard.current?.eKey.wasPressedThisFrame ?? false) || (Keyboard.current?.spaceKey.wasPressedThisFrame ?? false) || (Gamepad.current?.buttonSouth.wasPressedThisFrame ?? false);
            bool click = ((Mouse.current?.leftButton.wasPressedThisFrame ?? false) && !(EventSystem.current?.IsPointerOverGameObject() ?? false)) || UITouch.Tapped;
            if (nearest != null && (confirm || click))
            {
                nearest.Npc?.PlayOnce("Talk");
                AudioManager.Instance.PlaySfx("sfx_ui_confirm", ui: true);
                app.OpenTownService(nearest.Id);
            }
        }
        void LateUpdate() { if (!title && player != null && app.Screen == GameScreen.Town) FollowCamera(false); }
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
            Vector3 target = player.position + Vector3.up * 0.8f;
            Vector3 offset = new Vector3(10f, 12f, -14f);
            var camera = app.MainCamera;
            Vector3 desired = target + offset;
            if (Physics.SphereCast(target, 0.35f, offset.normalized, out var hit, offset.magnitude, ~(1 << 8), QueryTriggerInteraction.Ignore))
                desired = target + offset.normalized * Mathf.Max(2f, hit.distance - 0.45f);
            camera.transform.position = snap ? desired : Vector3.Lerp(camera.transform.position, desired, 1f - Mathf.Exp(-5f * Time.unscaledDeltaTime));
            camera.transform.LookAt(target);
            camera.fieldOfView = 45;
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
