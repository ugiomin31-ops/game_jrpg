using System;
using Abyss.Runtime.Persistence;
using UnityEngine;

namespace Abyss.UI
{
    public sealed partial class GameUI
    {
        /// <summary>Settings changes apply immediately and persist through GameApp.ApplyPreferences.</summary>
        public void ShowSettings() => Menu(T("settings"), "변경한 설정은 즉시 적용되고 저장됩니다.", m =>
        {
            var p = app.Preferences;
            m.Add("전체 음량", () => ShowVolume("전체 음량", p.Master, value => p.Master = value, m), "음악과 효과음을 함께 조정합니다.", $"{p.Master:P0}");
            m.Add(T("bgm_volume"), () => ShowVolume(T("bgm_volume"), p.Music, value => p.Music = value, m), "배경 음악의 크기를 조정합니다.", $"{p.Music:P0}");
            m.Add(T("sfx_volume"), () => ShowVolume(T("sfx_volume"), p.Effects, value => p.Effects = value, m), "전투, 환경과 UI 효과음의 크기를 조정합니다.", $"{p.Effects:P0}");
            m.Add(T("muted"), () => { p.Muted = !p.Muted; ApplySetting(m); }, "음량 설정은 유지한 채 모든 소리를 켜거나 끕니다.", p.Muted ? "켜짐" : "꺼짐");
            // Phones always run full screen at the device's own resolution.
            if (!Application.isMobilePlatform)
            {
                m.Add("전체 화면", () => { p.Fullscreen = !p.Fullscreen; ApplySetting(m); }, "전체 화면과 창 모드를 전환합니다. 에디터 밖에서 화면에 적용됩니다.", p.Fullscreen ? "전체 화면" : "창 모드");
                var resolution = GamePreferences.Resolutions[p.ResolutionIndex];
                m.Add("화면 해상도", () => ShowResolutions(m), "창 또는 전체 화면의 표시 해상도입니다. UI는 화면에 맞춰 조절됩니다.", $"{resolution.x}×{resolution.y}");
            }
            else m.Add("배터리 절약", () => { p.BatterySaver = !p.BatterySaver; ApplySetting(m); }, "화면 갱신을 초당 30회로 낮춰 발열과 배터리 소모를 줄입니다.", p.BatterySaver ? "켜짐 · 30fps" : "꺼짐 · 60fps");
            m.Add("전투 속도", () => { p.BattleSpeed = NextBattleSpeed(p.BattleSpeed); ApplySetting(m); }, "전투 연출과 대기 시간의 빠르기입니다. 자동 전투와 함께 쓰면 반복 전투가 빨라집니다.", $"{p.BattleSpeed:0.#}배속");
            m.Add(T("text_speed"), () => ShowTextSpeed(m), "대사의 초당 표시 글자 수를 조정합니다. 대사 진행 버튼을 누르면 현재 문장이 즉시 표시됩니다.", $"{p.TextSpeed:0}자/초");
            m.Add("연출 움직임 줄이기", () => { p.ReducedMotion = !p.ReducedMotion; ApplySetting(m); }, "전투의 카메라 흔들림과 섬광을 줄이고 대사를 즉시 표시합니다. 메뉴 이동, 버튼 확대와 선택 커서의 움직임도 생략합니다.", p.ReducedMotion ? "켜짐" : "꺼짐");
        });
        static float NextBattleSpeed(float current)
        {
            var speeds = GamePreferences.BattleSpeeds;
            for (int i = 0; i < speeds.Length; i++) if (current < speeds[i] - 0.01f) return speeds[i];
            return speeds[0];
        }
        void ApplySetting(GameMenuScreen menu) { root.ReducedMotion = app.Preferences.ReducedMotion; app.ApplyPreferences(); menu.Refresh(); }
        void ShowVolume(string title, float current, Action<float> change, GameMenuScreen owner) => Menu(title, "0%는 무음, 100%는 최대 음량입니다.", m =>
        {
            for (int i = 0; i <= 20; i++)
            {
                float value = i / 20f;
                m.Add($"{value:P0}", () => { change(value); app.ApplyPreferences(); m.Close(); owner.Refresh(); }, $"{title} · {value:P0}", Math.Abs(value - current) < 0.01f ? "현재" : null);
            }
        });
        void ShowResolutions(GameMenuScreen owner) => Menu("화면 해상도", "해상도를 선택하세요.", m =>
        {
            for (int i = 0; i < GamePreferences.Resolutions.Length; i++)
            {
                int index = i; var resolution = GamePreferences.Resolutions[i];
                m.Add($"{resolution.x} × {resolution.y}", () => { app.Preferences.ResolutionIndex = index; app.ApplyPreferences(); m.Close(); owner.Refresh(); }, "에디터 밖에서 적용됩니다.", i == app.Preferences.ResolutionIndex ? "현재" : null);
            }
        });
        void ShowTextSpeed(GameMenuScreen owner) => Menu(T("text_speed"), "대사 속도를 선택하세요.", m =>
        {
            foreach (int speed in new[] { 8, 20, 32, 42, 60, 90, 120, 160 })
            {
                int value = speed;
                m.Add($"초당 {speed}자", () => { app.Preferences.TextSpeed = value; app.ApplyPreferences(); m.Close(); owner.Refresh(); }, "움직임 줄이기를 켜면 대사를 즉시 표시합니다.", Math.Abs(app.Preferences.TextSpeed - speed) < 0.1f ? "현재" : null);
            }
        });
    }
}
