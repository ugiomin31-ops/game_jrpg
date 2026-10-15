using System;
using System.Collections.Generic;
using Abyss.Runtime.Art;
using Abyss.Presentation.Audio;
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
        static readonly string[] NpcLabels = { "마사 · 여관", "피핀 · 상점", "브론 · 대장간", "리나 · 길드", "에드윈 · 장로" };

        public void Initialize(GameApp app, bool title)
        {
            this.app = app;
            this.title = title;
            app.Atmosphere.Apply(AtmospherePreset.ForTileset(title ? "town_night" : "town_dawn"));
            app.Atmosphere.SetupCamera(app.MainCamera);
            var town = ArtLibrary.SpawnStatic(ArtLibrary.TownPath, transform);
            var layout = EnvironmentProcessor.Process(town, app.Atmosphere.Current.TorchColor, 2f, 7f);
            for (int i = 0; i < NpcIds.Length; i++)
            {
                var marker = RequireSpot(layout, NpcIds[i]);
                var npc = ArtLibrary.SpawnNpc(NpcIds[i], transform);
                npc.transform.SetPositionAndRotation(marker.position, marker.rotation);
                npc.Play("Idle");
                var spot = new ServiceSpot { Id = NpcIds[i], Marker = marker, Npc = npc };
                if (!title) spot.Label = CreateLabel(NpcLabels[i], marker.position + Vector3.up * (npc.Height + 0.3f));
                services.Add(spot);
            }
            for (int i = 0; i < 3; i++)
            {
                if (!layout.Spots.TryGetValue("villager_" + (i + 1), out var marker)) continue;
                var npc = ArtLibrary.SpawnNpc("villager_" + (char)('a' + i), transform);
                npc.transform.SetPositionAndRotation(marker.position, marker.rotation);
                npc.Play("Idle");
            }
            var gate = RequireSpot(layout, "gate");
            services.Add(new ServiceSpot { Id = "gate", Marker = gate, Label = title ? null : CreateLabel("심연의 미궁 · 출발", gate.position + Vector3.up * 2.4f) });
            if (title)
            {
                var cameraMarker = RequireSpot(layout, "camera_title");
                titlePosition = cameraMarker.position;
                titleRotation = Quaternion.LookRotation((RequireSpot(layout, "innkeeper").position + RequireSpot(layout, "smith").position + RequireSpot(layout, "elder").position) / 3f + Vector3.up * 1.5f - titlePosition);
                app.MainCamera.transform.SetPositionAndRotation(titlePosition, titleRotation);
                return;
            }
            var spawn = RequireSpot(layout, "spawn");
            foreach (string id in app.DB.HeroOrder)
            {
                var model = ArtLibrary.SpawnHero(id, transform);
                model.transform.SetPositionAndRotation(spawn.position - spawn.forward * party.Count * 0.9f, spawn.rotation);
                model.Play("Idle");
                party.Add(model);
            }
            RefreshEquipment();
            player = party[0].transform;
            player.gameObject.layer = 8;
            controller = player.gameObject.AddComponent<CharacterController>();
            controller.height = 1.35f;
            controller.radius = 0.28f;
            controller.center = Vector3.up * 0.7f;
            controller.stepOffset = 0.24f;
            controller.slopeLimit = 45;
            heading = player.forward;
            FollowCamera(true);
        }

        public void RefreshEquipment()
        {
            foreach (var model in party)
            {
                string id = model.ModelId;
                string weapon = app.State.Hero(id).Equipped("weapon");
                GameObject prefab = null;
                if (!string.IsNullOrEmpty(weapon))
                {
                    prefab = ArtLibrary.LoadPrefab(ArtLibrary.WeaponPath(weapon));
                    if (prefab == null) throw new InvalidOperationException("Missing equipped weapon: " + weapon);
                }
                model.Attach(id == "archer" ? "weapon.L" : "weapon.R", prefab);
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
            Vector2 input = ReadMove();
            var forward = app.MainCamera.transform.forward; forward.y = 0; forward.Normalize();
            var right = app.MainCamera.transform.right; right.y = 0; right.Normalize();
            Vector3 motion = Vector3.ClampMagnitude(forward * input.y + right * input.x, 1f);
            bool running = Keyboard.current?.leftShiftKey.isPressed ?? false;
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
            bool click = (Mouse.current?.leftButton.wasPressedThisFrame ?? false) && !(EventSystem.current?.IsPointerOverGameObject() ?? false);
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
                if (nearest != null) app.Notify("E / 확인: " + (nearest.Label != null ? nearest.Label.text : nearest.Id));
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
            Vector2 move = Gamepad.current?.leftStick.ReadValue() ?? Vector2.zero;
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
