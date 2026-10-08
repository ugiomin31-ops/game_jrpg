using System;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Game;
using Abyss.Presentation.Audio;

namespace Abyss.UI
{
    /// <summary>Class change (전직) screens, reached from the Guild board.</summary>
    public sealed partial class GameUI
    {
        /// <summary>Name shown for a party member: the job name once promoted, the hero's own name before.</summary>
        string HeroLabel(HeroState hero) => PartyStats.IsPromoted(app.DB, hero) ? PartyStats.JobName(app.DB, hero) : HeroName(hero.Id);

        string JobName(HeroState hero) => PartyStats.JobName(app.DB, hero);

        /// <summary>Guild board row value: how many heroes can change job right now.</summary>
        string JobBoardValue()
        {
            int ready = 0;
            foreach (var hero in app.State.Party)
                foreach (var option in JobService.Options(app.DB, app.State, hero)) if (option.Available) { ready++; break; }
            return ready > 0 ? $"전직 가능 {ready}명" : "직업 확인";
        }

        void ShowJobs() => Menu(T("job_title"), T("job_greeting"), m =>
        {
            foreach (var member in app.State.Party)
            {
                var hero = member;
                var options = JobService.Options(app.DB, app.State, hero);
                bool ready = false;
                var lines = new List<string> { $"{HeroName(hero.Id)} · Lv.{hero.Level}", $"현재 직업 · {JobName(hero)}", "" };
                if (options.Count == 0) lines.Add("최종 직업에 도달했습니다.");
                foreach (var option in options)
                {
                    ready |= option.Available;
                    lines.Add($"<b>{option.Job.DisplayName}</b> · " + (option.Available ? $"{UITheme.Tag(UITheme.Positive)}전직 가능</color>" : $"{UITheme.Tag(UITheme.Danger)}{T("reason_" + option.Reason)}</color>"));
                }
                string value = options.Count == 0 ? "최종 직업" : ready ? "전직 가능" : "조건 미달";
                m.Add($"{HeroName(hero.Id)} · {JobName(hero)}", () => ShowJobChoices(hero, m), string.Join("\n", lines), value, icon: UIArtwork.Hero(hero.Id));
            }
        });

        void ShowJobChoices(HeroState hero, GameMenuScreen owner) => Menu($"{HeroName(hero.Id)} · {T("job_title")}", $"현재 직업 · {JobName(hero)} · Lv.{hero.Level}", m =>
        {
            m.Subtitle = $"현재 직업 · {JobName(hero)} · Lv.{hero.Level}";
            var options = JobService.Options(app.DB, app.State, hero);
            if (options.Count == 0) AddInformation(m, "최종 직업", $"{JobName(hero)}은(는) 이 길의 마지막 직업입니다. 더 이상 전직할 수 없습니다.");
            foreach (var row in options)
            {
                var option = row;
                string details = JobDetails(hero, option);
                m.Add(option.Job.DisplayName,
                    () => Confirm("전직 확인", details + $"\n\n{HeroName(hero.Id)}을(를) {option.Job.DisplayName}(으)로 전직할까요?\n배운 기술은 그대로 남지만 이전 직업으로는 돌아갈 수 없습니다.", () => ExecuteJobChange(hero, option.Job, m, owner)),
                    details, option.Available ? "전직 가능" : "조건 미달", option.Available, option.Available ? null : T("reason_" + option.Reason), UIArtwork.Job(option.Job.Id, hero.Id));
            }
        });

        string JobDetails(HeroState hero, JobOption option)
        {
            var job = option.Job;
            var lines = new List<string> { $"<b>{job.DisplayName}</b> · {(job.Tier >= 3 ? "2차 전직" : "1차 전직")}", job.Description, "", "<b>전직 조건</b>" };
            foreach (var requirement in option.Requirements)
                lines.Add($"{UITheme.Tag(requirement.Met ? UITheme.Positive : UITheme.Danger)}{(requirement.Met ? "충족" : "미충족")}</color> · {requirement.Text}");

            var before = PartyStats.EffectiveStats(app.DB, hero);
            var after = JobService.PreviewStats(app.DB, hero, job.Id);
            var a = before.Stats; var z = after.Stats;
            lines.Add("");
            lines.Add("<b>능력치     현재 → 전직 후 (차이)</b>");
            ComparisonLine(lines, T("stat_hp"), a.MaxHp, z.MaxHp);
            ComparisonLine(lines, T("stat_mp"), a.MaxMp, z.MaxMp);
            ComparisonLine(lines, T("stat_atk"), a.Attack, z.Attack);
            ComparisonLine(lines, T("stat_mag"), a.Magic, z.Magic);
            ComparisonLine(lines, T("stat_def"), a.Defense, z.Defense);
            ComparisonLine(lines, T("stat_res"), a.Resistance, z.Resistance);
            ComparisonLine(lines, T("stat_spd"), a.Speed, z.Speed);
            ComparisonLine(lines, T("stat_hit"), before.Hit * 100, after.Hit * 100, true);
            ComparisonLine(lines, T("stat_evade"), before.Evade * 100, after.Evade * 100, true);
            ComparisonLine(lines, T("stat_crit"), before.Crit * 100, after.Crit * 100, true);

            var now = JobService.PreviewNewSkills(app.DB, hero, job.Id);
            lines.Add("");
            lines.Add("<b>직업 기술</b>");
            var learnset = new List<LearnEntry>(job.Learnset);
            learnset.Sort((x, y) => x.Level.CompareTo(y.Level));
            foreach (var learn in learnset)
            {
                if (!app.DB.Skills.TryGetValue(learn.Skill, out var skill)) continue;
                string when = now.Contains(learn.Skill) ? $"{UITheme.Tag(UITheme.Positive)}즉시 습득</color>" : $"Lv.{learn.Level}";
                lines.Add($"{when} · {skill.DisplayName}");
            }
            if (!string.IsNullOrEmpty(job.SignatureWeapon) && app.DB.Equipment.TryGetValue(job.SignatureWeapon, out var weapon))
                lines.Add($"\n전용 무기 · {weapon.DisplayName}");
            return string.Join("\n", lines);
        }

        void ExecuteJobChange(HeroState hero, JobDef job, GameMenuScreen choices, GameMenuScreen owner)
        {
            string before = JobName(hero);
            var result = JobService.ChangeJob(app.DB, app.State, hero.Id, job.Id);
            if (!result.Success) { UIModal.Alert(root.Modals, "전직할 수 없습니다", LocalResult(result)); return; }
            AudioManager.Instance?.PlayJingle("jingle_level");
            root.Toast.Banner($"{job.DisplayName} 전직!", $"{HeroName(hero.Id)} · {before} → {job.DisplayName}");
            root.Toast.Show(LocalResult(result), UIToastKind.Good, 3.6f, UIArtwork.Job(job.Id, hero.Id));
            app.RefreshJobVisuals();
            app.RefreshEquipmentVisuals();
            app.Save();
            choices.Refresh(); owner.Refresh(); RefreshVitals(); RefreshTown();
        }
    }
}
