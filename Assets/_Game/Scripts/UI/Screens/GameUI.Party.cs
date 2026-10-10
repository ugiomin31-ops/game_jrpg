using System;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Game;
using Abyss.Runtime;
using Abyss.Logic.Battle;

namespace Abyss.UI
{
    public sealed partial class GameUI
    {
        // Tab 0 = the active party (equipment, skills, formation), tab 1 = reserve hunters. Formation changes only at the guild.
        public void ShowParty() => Menu(T("menu_party", "헌터 관리"), "헌터를 선택해 장비, 기술과 능력치를 확인하고 파티를 편성하세요.", m =>
        {
            bool mutable = app.Screen != GameScreen.Battle && app.State.PendingBattle == null;
            bool formation = mutable && app.Screen == GameScreen.Town;
            m.Subtitle = $"파티 {app.State.Party.Count}/{GameState.PartySize} · 대기 {app.State.Reserve.Count}명 · {T("rank_title", "길드 등급")} {GameFlow.GuildRank(app.State)}";
            if (m.TabIndex == 0)
            {
                m.Add("파티 전체 최강 장비", () => ConfirmPartyAutoEquip(m), "파티 헌터 모두에게 보유 장비 중 가장 강한 장비를 한 번에 장착합니다.", enabled: mutable, reason: T("battle_unavailable"));
                for (int i = 0; i < app.State.Party.Count; i++)
                {
                    var hero = app.State.Party[i]; int slot = i;
                    m.Add($"{slot + 1}. {HeroLabel(hero)}", () => ShowPartyMember(hero, m), HeroSummary(hero), $"{JobName(hero)} · Lv.{hero.Level}", icon: UIArtwork.Hero(hero.Id));
                }
            }
            else
            {
                if (app.State.Reserve.Count == 0)
                    AddInformation(m, "대기 중인 헌터가 없습니다", "구역 보스를 쓰러뜨리면 새 헌터가 합류하고, 접수처에서 헌터를 스카우트할 수 있습니다.");
                foreach (var member in app.State.Reserve)
                {
                    var hero = member;
                    m.Add(HeroLabel(hero), () => ShowReserveMember(hero, m), HeroSummary(hero) + "\n\n대기 헌터도 전투 EXP의 절반을 받습니다.", formation ? "파티에 넣기" : $"Lv.{hero.Level}", icon: UIArtwork.Hero(hero.Id));
                }
            }
        }, new[] { T("hunter_party", "파티 편성"), "대기 헌터" });
        bool FormationOpen => app.Screen == GameScreen.Town && app.State.PendingBattle == null;
        void ShowPartyMember(HeroState hero, GameMenuScreen owner) => Menu(HeroLabel(hero), HunterProfile(hero.Id), m =>
        {
            int slot = app.State.Party.IndexOf(hero);
            m.Add("장비 · 기술 · 능력치", () => ShowHero(hero), HeroSummary(hero), icon: UIArtwork.Hero(hero.Id));
            m.Add("대기로 보내기", () => ExecuteRoster(HunterRoster.Bench(app.State, hero.Id), owner, true), "파티에서 빼고 대기 헌터로 둡니다.", enabled: FormationOpen && app.State.Party.Count > 1,
                reason: !FormationOpen ? T("roster_town_only", "파티 편성은 길드에서만 바꿀 수 있습니다.") : T("roster_last_member", "파티에는 최소 한 명이 있어야 합니다."));
            if (slot > 0) m.Add("앞 순서로", () => { HunterRoster.SwapSlots(app.State, slot, slot - 1); ExecuteRoster(ServiceResult.Ok("roster_changed_msg"), owner, true); }, "전열에 가까운 자리로 옮깁니다.", enabled: FormationOpen, reason: T("roster_town_only", "파티 편성은 길드에서만 바꿀 수 있습니다."));
            if (slot >= 0 && slot < app.State.Party.Count - 1) m.Add("뒤 순서로", () => { HunterRoster.SwapSlots(app.State, slot, slot + 1); ExecuteRoster(ServiceResult.Ok("roster_changed_msg"), owner, true); }, "뒤쪽 자리로 옮깁니다.", enabled: FormationOpen, reason: T("roster_town_only", "파티 편성은 길드에서만 바꿀 수 있습니다."));
        });
        void ShowReserveMember(HeroState hero, GameMenuScreen owner) => Menu(HeroLabel(hero), HunterProfile(hero.Id), m =>
        {
            m.Add("장비 · 기술 · 능력치", () => ShowHero(hero), HeroSummary(hero), icon: UIArtwork.Hero(hero.Id));
            string townOnly = T("roster_town_only", "파티 편성은 길드에서만 바꿀 수 있습니다.");
            if (app.State.Party.Count < GameState.PartySize)
                m.Add("파티에 넣기", () => ExecuteRoster(HunterRoster.PutInParty(app.State, hero.Id, GameState.PartySize), owner, true), $"빈 자리({app.State.Party.Count + 1}번)에 넣습니다.", enabled: FormationOpen, reason: townOnly);
            for (int i = 0; i < app.State.Party.Count; i++)
            {
                var member = app.State.Party[i]; int slot = i;
                m.Add($"{HeroName(member.Id)} 대신 넣기", () => ExecuteRoster(HunterRoster.PutInParty(app.State, hero.Id, slot), owner, true),
                    RosterSwapComparison(member, hero, slot), $"{slot + 1}번", FormationOpen, townOnly, UIArtwork.Hero(member.Id));
            }
        });
        string RosterSwapComparison(HeroState outgoing, HeroState incoming, int slot)
        {
            var before = PartyStats.EffectiveStats(app.DB, outgoing);
            var after = PartyStats.EffectiveStats(app.DB, incoming);
            string GearLine(HeroState hero)
            {
                var gear = new List<string>();
                foreach (string equipSlot in GameState.EquipSlots)
                    gear.Add(T("slot_" + equipSlot) + " " + EquipmentName(hero.Equipped(equipSlot)));
                return string.Join(" · ", gear);
            }
            return $"{slot + 1}번 자리 교체 · 나가는 헌터는 대기 명단으로 이동합니다.\n\n" +
                $"내보냄  {HeroLabel(outgoing)} · Lv.{outgoing.Level}\n유효 HP {outgoing.Hp}/{before.MaxHp} · MP {outgoing.Mp}/{before.MaxMp}\n장비 {GearLine(outgoing)}\n\n" +
                $"영입  {HeroLabel(incoming)} · Lv.{incoming.Level}\n유효 HP {incoming.Hp}/{after.MaxHp} · MP {incoming.Mp}/{after.MaxMp}\n장비 {GearLine(incoming)}";
        }
        void ExecuteRoster(ServiceResult result, GameMenuScreen owner, bool close)
        {
            Execute(result, owner);
            if (!result.Success) return;
            app.RefreshRosterVisuals();
            if (close) root.Screens.Pop();
        }
        /// <summary>"C급 궁수 헌터" profile line plus the hunter's quote.</summary>
        string HunterProfile(string heroId)
        {
            if (!app.DB.Heroes.TryGetValue(heroId ?? "", out var def)) return "";
            string cls = app.DB.Jobs.TryGetValue(app.DB.ClassOf(heroId), out var job) ? job.DisplayName : "";
            string head = string.IsNullOrEmpty(def.Rank) ? $"{cls} 헌터" : $"{def.Rank}급 {cls} 헌터";
            return string.IsNullOrEmpty(def.Line) ? head : $"{head}\n\"{def.Line}\"";
        }
        void ShowHero(HeroState hero) => Menu(HeroLabel(hero), HeroSummary(hero), m =>
        {
            var stats = PartyStats.EffectiveStats(app.DB, hero);
            m.Subtitle = $"{JobName(hero)} · Lv.{hero.Level} · {HeroVitals(hero)}";
            if (m.TabIndex == 0)
            {
                bool mutable = app.Screen != GameScreen.Battle && app.State.PendingBattle == null;
                m.Add("최강 장비", () => ConfirmAutoEquip(hero, m), "보유한 장비 중 이 헌터에게 가장 강한 조합을 한 번에 장착합니다.", enabled: mutable, reason: T("battle_unavailable"));
                foreach (string value in GameState.EquipSlots)
                {
                    string slot = value;
                    string current = hero.Equipped(slot);
                    string description = app.DB.Equipment.TryGetValue(current, out var piece) ? EquipmentDescription(piece) : T("slot_empty");
                    m.Add(T("slot_" + slot) + " · " + EquipmentName(current), () => ShowGear(hero, slot), description, T("change"), icon: piece == null ? null : UIArtwork.Gear(current));
                }
            }
            else if (m.TabIndex == 1)
            {
                foreach (string id in PartyStats.SkillsFor(app.DB, hero))
                    if (app.DB.Skills.TryGetValue(id, out var skill)) AddSkill(m, skill, 0);
                foreach (var learn in PartyStats.UpcomingSkills(app.DB, hero))
                    if (app.DB.Skills.TryGetValue(learn.Skill, out var skill)) AddSkill(m, skill, learn.Level);
            }
            else
            {
                var baseline = PartyStats.BaseStats(app.DB, hero);
                AddStat(m, T("stat_hp"), stats.MaxHp, baseline.MaxHp);
                AddStat(m, T("stat_mp"), stats.MaxMp, baseline.MaxMp);
                AddStat(m, T("stat_atk"), stats.Stats.Attack, baseline.Attack);
                AddStat(m, T("stat_mag"), stats.Stats.Magic, baseline.Magic);
                AddStat(m, T("stat_def"), stats.Stats.Defense, baseline.Defense);
                AddStat(m, T("stat_res"), stats.Stats.Resistance, baseline.Resistance);
                AddStat(m, T("stat_spd"), stats.Stats.Speed, baseline.Speed);
                AddInformation(m, T("stat_hit"), $"{stats.Hit:P0}");
                AddInformation(m, T("stat_evade"), $"{stats.Evade:P0}");
                AddInformation(m, T("stat_crit"), $"{stats.Crit:P0}");
                AddInformation(m, T("resist_label"), Elements(stats.ElementResists));
                AddInformation(m, T("immune_label"), StatusNames(stats.StatusImmunities));
                AddInformation(m, "성장", hero.Level >= GameState.LevelCap ? "최대 레벨에 도달했습니다." : $"EXP {hero.Xp}/{PartyStats.XpToNext(hero.Level)}\n다음 레벨까지 EXP {Math.Max(0, PartyStats.XpToNext(hero.Level) - hero.Xp)}");
                AddInformation(m, "현재 상태", HeroStatuses(hero));
            }
        }, new[] { T("tab_equip"), T("tab_skills"), T("tab_stats") });
        void AddStat(GameMenuScreen menu, string name, int effective, int basic) =>
            AddInformation(menu, name, $"기본 {basic}\n장비 보정 {effective - basic:+0;-0;0}\n합계 {effective}", effective.ToString());
        void AddInformation(GameMenuScreen menu, string title, string description, string value = null) =>
            menu.Add(title, () => UIModal.Alert(root.Modals, title, description), description, value);
        void AddSkill(GameMenuScreen menu, SkillDef skill, int learnLevel)
        {
            string target = skill.TargetType == TargetType.Self ? T("target_self") : skill.TargetType == TargetType.Ally ? T(skill.Scope == Scope.All ? "target_allies" : "target_ally") : T(skill.Scope == Scope.All ? "target_enemies" : "target_enemy");
            if (skill.Scope == Scope.Random) target = $"무작위 {skill.HitCount}회";
            string description = $"{skill.Description}\n\n{T("element_" + (int)skill.Element)} · {T("scope_" + (int)skill.Scope)}\n대상 · {target}\nMP {skill.MpCost} · TP {skill.TpCost}";
            if (learnLevel > 0) description += $"\nLv.{learnLevel} 습득 예정";
            string cost = learnLevel > 0 ? $"Lv.{learnLevel} 습득" : skill.TpCost > 0 ? $"TP {skill.TpCost}" : skill.MpCost > 0 ? $"MP {skill.MpCost}" : T("basic");
            menu.Add(skill.DisplayName, () => UIModal.Alert(root.Modals, skill.DisplayName, description), description, cost, icon: UIArtwork.Element(skill.Element));
        }
        void ShowGear(HeroState hero, string slot) => Menu(HeroName(hero.Id) + " · " + T("slot_" + slot), T("candidates"), m =>
        {
            bool mutable = app.Screen != GameScreen.Battle && app.State.PendingBattle == null;
            string currentId = hero.Equipped(slot);
            app.DB.Equipment.TryGetValue(currentId, out var current);
            m.Subtitle = T("equipped_now") + " · " + EquipmentName(currentId) + (mutable ? "" : " · 전투 중 변경 불가");
            m.Add(T("remove"), () => Confirm("장비 해제", GearComparison(hero, slot, null) + "\n\n해제할까요?", () => ExecuteEquipment(PartyStats.Unequip(app.DB, app.State, hero.Id, slot), m)), current == null ? T("slot_empty") : GearComparison(hero, slot, null), enabled: mutable && current != null, reason: !mutable ? T("battle_unavailable") : T("reason_slot_empty"));
            var ids = new List<string>(app.State.EquipmentBag.Keys); ids.Sort(StringComparer.Ordinal);
            int candidates = 0;
            foreach (string id in ids)
            {
                if (app.State.BagCount(id) <= 0 || !app.DB.Equipment.TryGetValue(id, out var piece) || piece.Slot != slot) continue;
                candidates++;
                var equipment = piece;
                bool allowed = PartyStats.CanEquip(app.DB, hero, id);
                string refusal = PartyStats.CanEquip(app.DB, hero.Id, id) ? T("cannot_equip_job", "다른 직업 전용 장비") : T("cannot_equip_class");
                string details = (allowed ? GearComparison(hero, slot, piece) + "\n\n" : "") + EquipmentDescription(piece);
                m.Add(EquipmentName(id), () => Confirm("장비 변경", details + "\n\n이 장비를 장착할까요?", () => ExecuteEquipment(PartyStats.Equip(app.DB, app.State, hero.Id, equipment.Id), m)), details, allowed ? GearVerdict(hero, slot, piece) : "직업 제한", mutable && allowed, !mutable ? T("battle_unavailable") : refusal, UIArtwork.Gear(id));
            }
            if (candidates == 0) AddInformation(m, T("no_candidates"), T("no_candidates"));
        });
        void ExecuteEquipment(ServiceResult result, GameMenuScreen screen)
        {
            Execute(result, screen);
            if (result.Success) app.RefreshEquipmentVisuals();
        }
        void ConfirmAutoEquip(HeroState hero, GameMenuScreen screen)
        {
            var plan = AutoEquip.Plan(app.DB, app.State, hero.Id);
            if (!plan.Changed) { UIModal.Alert(root.Modals, "최강 장비", "이미 가장 좋은 장비를 장착하고 있습니다."); return; }
            Confirm("최강 장비", AutoEquipSummary(plan) + "\n\n장착할까요?", () => ExecuteAutoEquip(new[] { AutoEquip.Apply(app.DB, app.State, hero.Id) }, "최강 장비", screen));
        }
        void ConfirmPartyAutoEquip(GameMenuScreen screen)
        {
            var sections = new List<string>();
            foreach (var plan in AutoEquip.PlanParty(app.DB, app.State))
                if (plan.Changed) sections.Add($"<b>{HeroName(plan.HeroId)}</b>\n{AutoEquipSummary(plan)}");
            if (sections.Count == 0) { UIModal.Alert(root.Modals, "파티 전체 최강 장비", "이미 가장 좋은 장비를 장착하고 있습니다."); return; }
            Confirm("파티 전체 최강 장비", string.Join("\n\n", sections) + "\n\n장착할까요?", () => ExecuteAutoEquip(AutoEquip.ApplyParty(app.DB, app.State), "파티 전체 최강 장비", screen));
        }
        void ExecuteAutoEquip(IEnumerable<AutoEquipResult> results, string label, GameMenuScreen screen)
        {
            AutoEquipResult failed = null;
            foreach (var result in results) if (!result.Success) { failed = result; break; }
            ExecuteEquipment(failed == null ? ServiceResult.Ok("equipped_msg", label) : ServiceResult.Fail(failed.Reason), screen);
        }
        /// <summary>One line per changed slot ("무기: 철검 → 미스릴 검") and the loadout's main stat change ("공격 +12 · 방어 -3").</summary>
        string AutoEquipSummary(AutoEquipPlan plan)
        {
            var lines = new List<string>();
            foreach (var slot in plan.Slots) if (slot.Changed) lines.Add($"{T("slot_" + slot.Slot)}: {EquipmentName(slot.CurrentId)} → {EquipmentName(slot.RecommendedId)}");
            var stats = new List<string>();
            AddDelta(stats, T("stat_hp"), plan.StatDelta.MaxHp);
            AddDelta(stats, T("stat_mp"), plan.StatDelta.MaxMp);
            AddDelta(stats, T("stat_atk"), plan.StatDelta.Attack);
            AddDelta(stats, T("stat_mag"), plan.StatDelta.Magic);
            AddDelta(stats, T("stat_def"), plan.StatDelta.Defense);
            AddDelta(stats, T("stat_res"), plan.StatDelta.Resistance);
            AddDelta(stats, T("stat_spd"), plan.StatDelta.Speed);
            lines.Add("능력 변화 · " + (stats.Count == 0 ? T("no_change") : string.Join(" · ", stats)));
            return string.Join("\n", lines);
        }
        BattleUnit LiveHero(HeroState hero)
        {
            if (app.Screen == GameScreen.Battle && app.Battle?.Engine != null)
                foreach (var unit in app.Battle.Engine.Party) if (unit.DefId == hero.Id) return unit;
            return null;
        }
        string HeroVitals(HeroState hero)
        {
            var live = LiveHero(hero);
            if (live != null) return $"HP {live.Hp}/{live.MaxHp} · MP {live.Mp}/{live.MaxMp} · TP {live.Tp}";
            var stats = PartyStats.EffectiveStats(app.DB, hero);
            return $"HP {hero.Hp}/{stats.MaxHp} · MP {hero.Mp}/{stats.MaxMp}";
        }
        string HeroSummary(HeroState hero)
        {
            var lines = new List<string> { $"{HeroName(hero.Id)} · Lv.{hero.Level}", $"{T("job_label", "직업")} · {JobName(hero)}", HunterProfile(hero.Id), HeroVitals(hero), "상태 · " + HeroStatuses(hero) };
            foreach (string slot in GameState.EquipSlots) lines.Add(T("slot_" + slot) + " · " + EquipmentName(hero.Equipped(slot)));
            lines.Add(hero.Level >= GameState.LevelCap ? "최대 레벨" : $"다음 레벨까지 EXP {Math.Max(0, PartyStats.XpToNext(hero.Level) - hero.Xp)}");
            return string.Join("\n", lines);
        }
        string HeroStatuses(HeroState hero)
        {
            var names = new List<string>();
            var live = LiveHero(hero);
            if ((live?.Hp ?? hero.Hp) <= 0) names.Add(T("knocked_out"));
            if (live != null)
            {
                foreach (var status in live.Statuses) names.Add($"{status.DisplayName} · {status.TurnsRemaining}턴");
            }
            else foreach (var status in hero.Statuses)
                if (app.DB.Statuses.TryGetValue(status.Key, out var def)) names.Add($"{def.DisplayName} · {status.Value}턴");
            return names.Count == 0 ? "정상" : string.Join(" · ", names);
        }
        string Elements(IEnumerable<int> elements)
        {
            var names = new List<string>(); foreach (int e in elements) names.Add(T("element_" + e));
            return names.Count == 0 ? T("none") : string.Join(" · ", names);
        }
        string StatusNames(IEnumerable<string> statuses)
        {
            var names = new List<string>();
            foreach (string id in statuses) if (app.DB.Statuses.TryGetValue(id, out var status)) names.Add(status.DisplayName);
            return names.Count == 0 ? T("none") : string.Join(" · ", names);
        }
        string ContentDescription(string id) => app.DB.Items.TryGetValue(id, out var item) ? item.Description : app.DB.Equipment.TryGetValue(id, out var equipment) ? EquipmentDescription(equipment) : "물품 정보를 확인할 수 없습니다.";
        string EquipmentDescription(EquipmentDef piece)
        {
            var names = new List<string>(); foreach (string id in piece.Classes) names.Add(HeroName(id));
            var jobs = new List<string>();
            if (piece.Jobs != null) foreach (string id in piece.Jobs) jobs.Add(app.DB.Jobs.TryGetValue(id, out var job) ? job.DisplayName : id);
            string jobLine = jobs.Count == 0 ? "" : $"\n전용 직업 · {string.Join(" · ", jobs)}";
            int level = Enhancement.LevelOf(app.State, piece.Id);
            string tier = piece.Tier > 0 ? $" · T{piece.Tier}" : "";
            string enhance = level > 0 ? $"\n강화 +{level} (기본 능력치 +{level * 10}%)" : "";
            return $"{UITheme.Tag(UITheme.RarityColor(piece.Rarity))}{UITheme.RarityName(piece.Rarity)}</color>{tier} · {piece.Description}\n\n{T("slot_" + piece.Slot)} · {(names.Count == 0 ? "모든 직업" : string.Join(" · ", names))}{jobLine}{enhance}\n" + EquipmentDelta(piece, level)
                + GearEffects(piece)
                + $"\n\n{T("resist_label")} · {Elements(piece.ElementResists)}\n{T("immune_label")} · {StatusNames(piece.StatusImmunities)}";
        }
        /// <summary>Special gear effects (attack element, regeneration, starting TP, EXP / gold bonus) as extra lines.</summary>
        string GearEffects(EquipmentDef piece)
        {
            var lines = new List<string>();
            if (piece.Element != Element.None) lines.Add($"평타 속성 · {T("element_" + (int)piece.Element)}");
            if (piece.HpRegen > 0f) lines.Add($"매 턴 HP {piece.HpRegen * 100:0.#}% 회복");
            if (piece.MpRegen > 0) lines.Add($"매 턴 MP {piece.MpRegen} 회복");
            if (piece.TpStart > 0) lines.Add($"전투 시작 시 TP {piece.TpStart}");
            if (piece.ExpBonus > 0f) lines.Add($"획득 경험치 +{piece.ExpBonus * 100:0}%");
            if (piece.GoldBonus > 0f) lines.Add($"획득 보상금 +{piece.GoldBonus * 100:0}% (파티 합산 최대 +100%)");
            return lines.Count == 0 ? "" : "\n" + string.Join("\n", lines);
        }
        string GearVerdict(HeroState hero, string slot, EquipmentDef piece)
        {
            var before = PartyStats.EffectiveStats(app.DB, hero);
            var after = PartyStats.PreviewEquipment(app.DB, hero, slot, piece?.Id);
            var a = before.Stats; var z = after.Stats;
            var deltas = new[] { z.MaxHp-a.MaxHp, z.MaxMp-a.MaxMp, z.Attack-a.Attack, z.Magic-a.Magic,
                z.Defense-a.Defense, z.Resistance-a.Resistance, z.Speed-a.Speed, after.Hit-before.Hit, after.Evade-before.Evade, after.Crit-before.Crit };
            bool up = false, down = false;
            foreach (var d in deltas) { up |= d > 0.0001f; down |= d < -0.0001f; }
            foreach (var e in after.ElementResists) up |= !before.ElementResists.Contains(e);
            foreach (var e in before.ElementResists) down |= !after.ElementResists.Contains(e);
            foreach (var s in after.StatusImmunities) up |= !before.StatusImmunities.Contains(s);
            foreach (var s in before.StatusImmunities) down |= !after.StatusImmunities.Contains(s);
            return up && down ? "장단점 교환" : up ? "능력 상승 ↑" : down ? "능력 하락 ↓" : "동일 능력";
        }
        string GearComparison(HeroState hero, string slot, EquipmentDef piece)
        {
            var before = PartyStats.EffectiveStats(app.DB, hero);
            var after = PartyStats.PreviewEquipment(app.DB, hero, slot, piece?.Id);
            var a = before.Stats; var z = after.Stats;
            var lines = new List<string> { $"<b>{HeroName(hero.Id)} · {GearVerdict(hero, slot, piece)}</b>",
                "현재 · " + EquipmentName(hero.Equipped(slot)), "선택 · " + (piece == null ? T("slot_none") : EquipmentName(piece.Id)), "", "<b>능력치     현재 → 변경 (차이)</b>" };
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
            lines.Add($"\n속성 저항 · {Elements(before.ElementResists)} → {Elements(after.ElementResists)}");
            lines.Add($"상태 면역 · {StatusNames(before.StatusImmunities)} → {StatusNames(after.StatusImmunities)}");
            return string.Join("\n", lines);
        }
        static void ComparisonLine(List<string> lines, string name, float before, float after, bool percent = false)
        {
            float delta = after - before;
            string unit = percent ? "%" : "";
            string difference = Math.Abs(delta) < 0.0001f ? "변화 없음" : $"{delta:+0.#;-0.#;0}{(percent ? "%p" : "")}";
            var color = delta > 0.0001f ? UITheme.Positive : delta < -0.0001f ? UITheme.Danger : UITheme.TextDim;
            lines.Add($"{name}   {before:0.#}{unit} → {after:0.#}{unit}   {UITheme.Tag(color)}({difference})</color>");
        }
        string ShopComparison(EquipmentDef piece)
        {
            var lines = new List<string>();
            foreach (var hero in app.State.Party)
                if (PartyStats.AllowsHero(app.DB, piece, hero)) lines.Add(GearComparison(hero, piece.Slot, piece));
            return string.Join("\n\n", lines);
        }

        /// <summary>The piece's stats at an enhancement level as "+N" lines.</summary>
        string EquipmentDelta(EquipmentDef piece, int level)
        {
            var lines = new List<string>();
            var stats = Enhancement.Stats(piece, level);
            AddDelta(lines, T("stat_hp"), stats.MaxHp);
            AddDelta(lines, T("stat_mp"), stats.MaxMp);
            AddDelta(lines, T("stat_atk"), stats.Attack);
            AddDelta(lines, T("stat_mag"), stats.Magic);
            AddDelta(lines, T("stat_def"), stats.Defense);
            AddDelta(lines, T("stat_res"), stats.Resistance);
            AddDelta(lines, T("stat_spd"), stats.Speed);
            AddPercentDelta(lines, T("stat_hit"), piece.Hit);
            AddPercentDelta(lines, T("stat_evade"), piece.Evade);
            AddPercentDelta(lines, T("stat_crit"), piece.Crit);
            return lines.Count == 0 ? T("no_change") : string.Join("\n", lines);
        }
        static void AddDelta(List<string> lines, string name, int delta) { if (delta != 0) lines.Add($"{name} {delta:+0;-0;0}"); }
        static void AddPercentDelta(List<string> lines, string name, float delta) { if (Math.Abs(delta) > 0.0001f) lines.Add($"{name} {delta * 100:+0.#;-0.#;0}%"); }
        public void ShowFieldItems() => Menu(T("cmd_item"), T("camp_hint"), m =>
        {
            var ids = new List<string>(app.State.Inventory.Keys); ids.Sort(StringComparer.Ordinal);
            foreach (string key in ids)
            {
                string id = key;
                if (app.State.ItemCount(id) <= 0 || !app.DB.Items.TryGetValue(id, out var item)) continue;
                bool usable = item.ItemType == ItemType.Healing || item.ItemType == ItemType.MpRestore || item.ItemType == ItemType.Revive || item.ItemType == ItemType.Cure || item.ItemType == ItemType.Seed || (item.ItemType == ItemType.EscapeDungeon && app.Screen == GameScreen.Dungeon);
                string usage = item.ItemType == ItemType.Material ? T("materials") : item.ItemType == ItemType.Key ? "중요 물품 · 전직할 때 사용합니다." : item.Target == "all_allies" ? T("target_allies") : T("target_ally");
                bool mutable = app.Screen != GameScreen.Battle && app.State.PendingBattle == null;
                m.Add(item.DisplayName, () =>
                {
                    if (item.ItemType == ItemType.EscapeDungeon) Confirm(T("return_stone"), "게이트 탈출 비콘을 사용하고 길드로 돌아갈까요?", () => UseFieldItem(id, null, m));
                    else if (item.Target == "all_allies") Confirm("아이템 사용", $"{item.DisplayName} 1개를 파티 전체에게 사용할까요?\n{item.Description}", () => UseFieldItem(id, null, m));
                    else ShowItemTargets(id, m);
                }, item.Description + "\n\n" + usage, $"×{app.State.ItemCount(id)}", usable && mutable, !mutable ? T("battle_unavailable") : T("item_unavailable"), UIArtwork.Item(id));
            }
        });
        void ShowItemTargets(string itemId, GameMenuScreen inventory) => Menu(ItemName(itemId), "아이템을 사용할 헌터를 선택하세요.", m =>
        {
            foreach (var member in app.State.Party)
            {
                var hero = member;
                m.Add(HeroName(hero.Id), () => Confirm("아이템 사용", $"{ItemName(itemId)} 1개 → {HeroName(hero.Id)}\n\n{ContentDescription(itemId)}\n\n사용할까요?", () => UseFieldItem(itemId, hero.Id, inventory, m)), HeroSummary(hero), $"HP {hero.Hp}", app.State.ItemCount(itemId) > 0, T("item_missing"), UIArtwork.Hero(hero.Id));
            }
        });
        void UseFieldItem(string itemId, string heroId, GameMenuScreen inventory, GameMenuScreen targets = null)
        {
            var result = GameFlow.UseFieldItem(app.DB, app.State, itemId, heroId, app.Screen == GameScreen.Dungeon);
            if (!result.Success) { UIModal.Alert(root.Modals, ItemName(itemId), T(result.TextKey)); return; }
            bool seed = app.DB.Items.TryGetValue(itemId, out var used) && used.ItemType == ItemType.Seed && heroId != null;
            Notify(seed ? app.DB.T("seed_used", HeroName(heroId)) : app.DB.T(result.TextKey, ItemName(itemId)));
            if (result.ReturnToTown) { app.ReturnToTown(); return; }
            targets?.Close(); inventory.Refresh(); RefreshVitals();
        }
    }
}
