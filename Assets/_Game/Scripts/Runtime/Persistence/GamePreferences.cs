using System;
using System.IO;
using Newtonsoft.Json;
using UnityEngine;
using Abyss.Presentation.Audio;

namespace Abyss.Runtime.Persistence
{
    [Serializable]
    public sealed class GamePreferences
    {
        public float Master = 0.8f;
        public float Music = 0.75f;
        public float Effects = 0.85f;
        public bool Muted;
        public bool Fullscreen = true;
        public int ResolutionIndex = 2;
        public float TextSpeed = 42f;
        public bool ReducedMotion;
        /// <summary>User intent persists until explicitly toggled off, including between encounters.</summary>
        public bool AutoBattle;
        /// <summary>Mobile only: caps the frame rate at 30 to save battery and heat.</summary>
        public bool BatterySaver;
        /// <summary>Battle pacing multiplier: 1, 1.5 or 2.</summary>
        public float BattleSpeed = 1f;
        public static readonly float[] BattleSpeeds = { 1f, 1.5f, 2f };
        public static readonly Vector2Int[] Resolutions =
        {
            new Vector2Int(1280, 720), new Vector2Int(1600, 900),
            new Vector2Int(1920, 1080), new Vector2Int(2560, 1440)
        };
        public static GamePreferences Read(string directory)
        {
            string path = Path.Combine(directory, "preferences.json");
            if (!File.Exists(path)) return new GamePreferences();
            try
            {
                var settings = JsonConvert.DeserializeObject<GamePreferences>(File.ReadAllText(path));
                if (settings == null) throw new JsonSerializationException("Empty preferences");
                settings.Normalize();
                return settings;
            }
            catch (Exception e) when (e is IOException || e is JsonException)
            {
                Debug.LogWarning("설정을 읽지 못해 기본값을 사용합니다: " + e.Message);
                return new GamePreferences();
            }
        }
        public void Normalize()
        {
            Master = FiniteClamp(Master, 0f, 1f, 0.8f);
            Music = FiniteClamp(Music, 0f, 1f, 0.75f);
            Effects = FiniteClamp(Effects, 0f, 1f, 0.85f);
            TextSpeed = FiniteClamp(TextSpeed, 8f, 160f, 42f);
            BattleSpeed = FiniteClamp(BattleSpeed, 1f, 2f, 1f);
            ResolutionIndex = Mathf.Clamp(ResolutionIndex, 0, Resolutions.Length - 1);
        }
        static float FiniteClamp(float value, float min, float max, float fallback) =>
            float.IsNaN(value) || float.IsInfinity(value) ? fallback : Mathf.Clamp(value, min, max);
        public void Apply()
        {
            Normalize();
            AudioManager.Instance.SetVolumes(Master, Music, Effects);
            AudioManager.Instance.SetMuted(Muted);
            if (Application.isMobilePlatform)
            {
                // Mobile ignores vSyncCount; the frame cap is the only pacing control, and the screen must not dim mid-battle.
                QualitySettings.vSyncCount = 0;
                Application.targetFrameRate = BatterySaver ? 30 : 60;
                Screen.sleepTimeout = SleepTimeout.NeverSleep;
                return;
            }
            QualitySettings.vSyncCount = 1;
            Application.targetFrameRate = 60;
            if (!Application.isEditor && Application.platform != RuntimePlatform.WebGLPlayer)
            {
                var resolution = Resolutions[ResolutionIndex];
                Screen.SetResolution(resolution.x, resolution.y, Fullscreen ? FullScreenMode.FullScreenWindow : FullScreenMode.Windowed);
            }
        }
        public void Save(string directory)
        {
            Normalize();
            Directory.CreateDirectory(directory);
            SaveRepository.AtomicWrite(Path.Combine(directory, "preferences.json"), JsonConvert.SerializeObject(this, Formatting.Indented));
        }
    }
}
