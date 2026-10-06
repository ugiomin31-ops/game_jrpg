using System;
using System.Collections.Generic;
using UnityEngine;

namespace Abyss.UI
{
    public sealed partial class GameUI
    {
        public void ShowCredits(Action completed = null)
        {
            var sections = new[]
            {
                (Title: "제작 · 프로젝트", Asset: "overview"),
                (Title: "제작 과정 · 출처", Asset: "provenance"),
                (Title: "Pretendard · 글꼴 라이선스", Asset: "pretendard"),
                (Title: "Black Han Sans · 글꼴 라이선스", Asset: "black_han_sans"),
                (Title: "Liberation Sans · 글꼴 라이선스", Asset: "liberation_sans"),
                (Title: "Newtonsoft.Json · MIT 고지", Asset: "newtonsoft"),
                (Title: "렌더링 · 수학 라이브러리 고지", Asset: "rendering"),
                (Title: "Burst · 라이브러리 고지", Asset: "burst"),
                (Title: "Unity Pipeline · 라이브러리 고지", Asset: "pipeline"),
                (Title: "Unity 패키지 · 저작권 고지", Asset: "unity_packages"),
                (Title: "Unity Companion 라이선스", Asset: "unity_companion"),
                (Title: "Unity 패키지 배포 라이선스", Asset: "unity_distribution"),
                (Title: "고지 범위 · 출처 목록", Asset: "scope")
            };
            var texts = new string[sections.Length];
            // Load every required notice before opening the screen: missing legal content is an error,
            // never a substitute acknowledgment or an empty license page.
            for (int i = 0; i < sections.Length; i++)
            {
                var asset = Resources.Load<TextAsset>("Credits/" + sections[i].Asset);
                if (asset == null) throw new InvalidOperationException("Missing credits notice: Credits/" + sections[i].Asset);
                texts[i] = asset.text;
            }

            bool returned = false;
            root.Screens.Push<GameMenuScreen>(menu =>
            {
                menu.Title = T("credits", "크레딧");
                menu.Subtitle = "항목 선택: 고지 전문 · 좌우: 상세 스크롤 · 돌아가기: 이전 화면";
                menu.FullBackdrop = true;
                menu.Closed = () =>
                {
                    if (returned) return;
                    returned = true;
                    completed?.Invoke();
                };
                menu.RefreshContent = screen =>
                {
                    for (int i = 0; i < sections.Length; i++)
                    {
                        int section = i;
                        screen.Add(sections[i].Title,
                            () => ShowCreditsNotice(sections[section].Title, texts[section]), "<noparse>" + texts[i] + "</noparse>");
                    }
                    screen.Add(completed == null ? "이전 화면으로 돌아가기" : "크레딧 마치기", screen.Close,
                        "고지문은 언제든 크레딧에서 다시 확인할 수 있습니다.\n플레이해 주셔서 감사합니다.");
                };
            });
        }

        void ShowCreditsNotice(string title, string text)
        {
            // Keep all source characters, including copyright lines and license titles. Each page is
            // immediately visible and scrollable; no legal text waits for the story typewriter.
            const int pageLength = 3500;
            var pages = new List<string>();
            for (int start = 0; start < text.Length;)
            {
                int count = Math.Min(pageLength, text.Length - start);
                if (start + count < text.Length)
                {
                    int newline = text.LastIndexOf('\n', start + count - 1, count);
                    if (newline >= start) count = newline - start + 1;
                    else if (char.IsHighSurrogate(text[start + count - 1])) count--;
                }
                pages.Add("<noparse>" + text.Substring(start, count) + "</noparse>");
                start += count;
            }
            root.Screens.Push<GameStoryScreen>(screen =>
            {
                screen.Title = title;
                screen.Pages = pages;
                screen.ReducedMotion = true;
                screen.ReadOnly = true;
            });
        }
    }
}
