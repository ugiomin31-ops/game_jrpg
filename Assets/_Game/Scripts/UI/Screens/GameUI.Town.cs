using System;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Game;
using Abyss.Runtime;
using Abyss.Presentation.Audio;
using UnityEngine;

namespace Abyss.UI
{
    public sealed partial class GameUI
    {
        static readonly string[] TownIds = { "innkeeper", "shopkeeper", "smith", "guild_clerk", "bestiary", "party", "elder", "gate" };
        static readonly string[] TownTitles = { "menu_inn", "menu_shop", "menu_smithy", "menu_guild", "menu_bestiary", "menu_party", "npc_elder_name", "menu_depart" };
        string GoldLine => $"{app.State.Gold:N0}만원";
        string DeepestLabel => app.DB.Floors[Mathf.Clamp(app.State.DeepestFloor, 0, app.DB.Floors.Count - 1)].FloorLabel;
        UIButton departButton;
        static Sprite TownArtwork(string id)
        {
            switch (id)
            {
                case "innkeeper": case "shopkeeper": case "smith": case "guild_clerk": case "elder": return UIArtwork.NPC(id);
                case "party": return UIArtwork.Command("party");
                default: return null;
            }
        }
        public void ShowTown()
        {
            Clear(); BuildHud(false); RefreshTown();
            townObjective = UIFactory.Label(townPanel, "", 25, UIFont.Bold, UITheme.Text, name: "Current objective");
            townObjective.Rt().TopStrip(34, 91, 24, 24);
            townReadiness = UIFactory.Label(townPanel, "", 22, UIFont.Bold, UITheme.Positive, name: "Departure readiness");
            townReadiness.Rt().TopStrip(30, 126, 24, 24);
            townIssues = UIFactory.Paragraph(townPanel, "", 19, UITheme.TextDim, "Readiness notes");
            townIssues.lineSpacing = 1f;
            townIssues.Rt().TopStrip(38, 156, 24, 248);
            departButton = UIFactory.Button(townPanel, "게이트 출발", ShowDepart, name: "Primary departure");
            departButton.Rt().Place(UIAnchor.BottomRight, new Vector2(-20, 12), new Vector2(224, 54));

            const float width = 500f;
            float height = 430f;
            var services = UIFactory.Panel(hud, UIPanelStyle.Glass, name: "Guild facilities");
            services.Rect.Place(UIAnchor.TopRight, new Vector2(-20, -24), new Vector2(width, height));
            UIFactory.Label(services.Rect, "길드 시설", 28, UIFont.Bold, UITheme.GoldBright).Rt().TopStrip(40, 16, 20, 20);
            UIFactory.Label(services.Rect, "회복 · 보급 · 성장", 20, color: UITheme.TextDim).Rt().TopStrip(28, 53, 20, 20);
            for (int i = 0; i < TownIds.Length - 1; i++)
            {
                string id = TownIds[i];
                string label = id == "elder" ? "길드장실" : T(TownTitles[i]);
                var button = UIFactory.Button(services.Rect, label,
                    () => { if (!BlocksWorldInput) { UIInput.Consume(); ShowTownService(id); } }, TownArtwork(id));
                float buttonWidth = (width - 52f) * 0.5f;
                button.Rt().Place(UIAnchor.TopLeft, new Vector2(18 + (i % 2) * (buttonWidth + 8f), -92 - (i / 2) * 78), new Vector2(buttonWidth, UIRoot.TouchFirst ? UIRoot.TouchTargetHeight : 70));
                button.Label.textWrappingMode = TMPro.TextWrappingModes.Normal;
                button.Label.fontSizeMax = 25;
            }
            string help = UIRoot.TouchFirst
                ? "이동 · 화면을 누른 채 끌기    대화 · 시설 근처에서 탭    수첩 · 오른쪽 아래 버튼"
                : "이동 · WASD / 방향키 / 왼쪽 스틱    대화 · E / 확인    수첩 · Tab / Start";
            UIFactory.Label(hud, help, 21, color: UITheme.TextDim)
                .Rt().BottomStrip(38, 212, 30, 470);
            RefreshTownReadiness();
        }
        void RefreshTown()
        {
            if (app.Screen != GameScreen.Town || area == null) return;
            area.text = "새벽 길드";
            resources.text = $"{GoldLine}  ·  {T("rank_title", "길드 등급")} {GameFlow.GuildRank(app.State)}  ·  최심부 {DeepestLabel}  ·  {DifficultyName(app.State.Difficulty)}";
            RefreshVitals();
            RefreshTownReadiness();
        }
        void RefreshTownReadiness()
        {
            if (app?.State == null || app.Screen != GameScreen.Town || townObjective == null) return;
            var report = ExpeditionReadiness.Evaluate(app.DB, app.State);
            townObjective.text = report.ObjectiveText;
            townReadiness.text = report.SummaryText + "  ·  출발 제한 없음";
            townReadiness.color = report.HasWarnings ? UITheme.Warning : UITheme.Positive;
            if (report.IssueLines.Count == 0)
                townIssues.text = "출발 전 참고 점검 · 현재 파티 상태";
            else
            {
                int shown = Math.Min(2, report.IssueLines.Count);
                var visible = new List<string>();
                for (int i = 0; i < shown; i++) visible.Add(report.IssueLines[i]);
                if (report.IssueLines.Count > shown) visible.Add($"외 {report.IssueLines.Count - shown}건 · 헌터 관리에서 확인");
                townIssues.text = string.Join("  ·  ", visible);
            }
            if (departButton != null) departButton.Label.color = UITheme.Text;
        }
        void ShowTownDirectory() => Menu(T("town_title"), T("town_subtitle"), m =>
        {
            for (int i = 0; i < TownIds.Length; i++)
            {
                string id = TownIds[i];
                m.Add(T(TownTitles[i]), () => ShowTownService(id), icon: TownArtwork(id));
            }
        });
        public void ShowTownService(string id)
        {
            if (app.State == null || app.Screen != GameScreen.Town) return;
            UIInput.Consume();
            switch (id)
            {
                case "innkeeper": ShowInn(); break;
                case "shopkeeper": ShowShop(); break;
                case "smith": ShowSmithy(); break;
                case "guild_clerk": ShowQuests(true); break;
                case "bestiary": ShowBestiary(); break;
                case "party": ShowParty(); break;
                case "elder": ShowElder(); break;
                case "gate": ShowDepart(); break;
            }
        }
        void ShowInn() => Menu(T("inn_title"), T(GameFlow.GreetingKey(app.DB, app.State, "innkeeper")), m =>
        {
            int cost = TownServices.InnCost(app.State);
            m.Subtitle = T(GameFlow.GreetingKey(app.DB, app.State, "innkeeper")) + "  ·  " + GoldLine;
            m.Add(T("inn_rest"), () => Confirm(T("inn_offer"), $"치료비 {cost:N0}만원을 내고 쉴까요?\n\n{T("inn_note")}", () => Execute(TownServices.RestAtInn(app.DB, app.State), m)), T("inn_note"), $"{cost:N0}만원", app.State.Gold >= cost, T("reason_not_enough_gold"));
            foreach (var hero in app.State.Party)
                m.Add(HeroName(hero.Id), () => ShowHero(hero), HeroSummary(hero), $"HP {hero.Hp}", icon: UIArtwork.Hero(hero.Id));
        });
        void ShowShop() => Menu(T("shop_title"), T(GameFlow.GreetingKey(app.DB, app.State, "shopkeeper")), m =>
        {
            m.Subtitle = T(GameFlow.GreetingKey(app.DB, app.State, "shopkeeper")) + "  ·  " + GoldLine;
            if (m.TabIndex < 2)
            {
                bool equipment = m.TabIndex == 1;
                foreach (var row in TownServices.ShopStock(app.DB, app.State, equipment))
                {
                    var entry = row;
                    int have = equipment ? app.State.BagCount(entry.Id) : app.State.ItemCount(entry.Id);
                    int cap = equipment ? GameState.MaxStack : Math.Min(GameState.MaxStack, Math.Max(1, app.DB.Items[entry.Id].MaxStack));
                    int maximum = Math.Min(cap - have, app.State.Gold / entry.Price);
                    string reason = !entry.Unlocked ? T("reason_tier_locked") : have >= cap ? T("reason_stack_full") : T("reason_not_enough_gold");
                    string description = ContentDescription(entry.Id) + $"\n\n보유 {have}개";
                    if (equipment) description = ShopComparison(app.DB.Equipment[entry.Id]) + "\n\n" + description + $" · 장착 {PartyStats.EquippedCount(app.State, entry.Id)}개";
                    if (!entry.Unlocked) description += $"\n{app.DB.Floors[Math.Min(app.DB.Floors.Count - 1, TownServices.TierUnlockFloor(entry.ShopTier))].FloorLabel} 도달 시 해금";
                    m.Add(entry.DisplayName, () => ShowQuantity(T("buy") + " · " + entry.DisplayName, maximum, entry.Price, n => equipment ? TownServices.BuyEquipment(app.DB, app.State, entry.Id, n) : TownServices.BuyItem(app.DB, app.State, entry.Id, n), m), description, $"{entry.Price:N0}만원", entry.Unlocked && maximum > 0, reason, equipment ? UIArtwork.Gear(entry.Id) : UIArtwork.Item(entry.Id));
                }
            }
            else
            {
                AddSellRows(m, false); AddSellRows(m, true);
            }
        }, new[] { T("tab_items"), T("tab_equipment"), T("tab_sell") });
        void AddSellRows(GameMenuScreen m, bool equipment)
        {
            var inventory = equipment ? app.State.EquipmentBag : app.State.Inventory;
            var ids = new List<string>(inventory.Keys); ids.Sort(StringComparer.Ordinal);
            foreach (string key in ids)
            {
                string id = key;
                if (inventory[id] <= 0) continue;
                int value = equipment ? TownServices.EquipmentSellValue(app.DB, id) : TownServices.ItemSellValue(app.DB, id);
                int count = inventory[id];
                m.Add(ItemName(id), () => ShowQuantity(T("sell") + " · " + ItemName(id), count, value,
                    n => equipment ? TownServices.SellEquipment(app.DB, app.State, id, n) : TownServices.SellItem(app.DB, app.State, id, n), m),
                    ContentDescription(id) + $"\n\n보유 {count}개\n장착 중인 장비는 해제한 뒤 판매할 수 있습니다.", $"{value:N0}만원", value > 0, T("reason_not_sellable"), equipment ? UIArtwork.Gear(id) : UIArtwork.Item(id));
            }
        }
        void ShowQuantity(string title, int maximum, int price, Func<int, ServiceResult> operation, GameMenuScreen owner)
        {
            Menu(title, "수량을 선택한 뒤 합계를 확인하고 거래를 승인하세요.", q =>
            {
                for (int i = 1; i <= maximum; i++)
                {
                    int count = i;
                    q.Add($"{count}개", () => Confirm("거래 확인", $"{title}\n수량 {count}개 · 합계 {price * count:N0}만원\n{GoldLine}\n\n거래를 진행할까요?", () =>
                    {
                        var result = operation(count);
                        if (result.Success) q.Close();
                        Execute(result, owner);
                    }), $"{title}\n수량 {count}개\n합계 {price * count:N0}만원\n\n{GoldLine}", $"{price * count:N0}만원");
                }
            });
        }
        void ShowSmithy() => Menu(T("smithy_title"), T(GameFlow.GreetingKey(app.DB, app.State, "smith")), m =>
        {
            m.Subtitle = T(GameFlow.GreetingKey(app.DB, app.State, "smith")) + "  ·  " + GoldLine;
            if (m.TabIndex == 1) { AddEnhanceRows(m); return; }
            var recipes = TownServices.SmithyRecipes(app.DB, app.State);
            if (recipes.Count == 0) m.Add(T("smithy_empty"), () => UIModal.Alert(root.Modals, T("smithy_title"), T("smithy_empty")), T("smithy_empty"));
            foreach (var row in recipes)
            {
                var recipe = row;
                var lines = new List<string> { EquipmentDescription(recipe.Equipment), "", T("materials") };
                foreach (var material in recipe.Materials) lines.Add($"{ItemName(material.ItemId)} · {material.Have}/{material.Need}");
                lines.Add($"제작비 {recipe.Gold:N0}만원\n보유 {app.State.BagCount(recipe.Equipment.Id)}개");
                bool capacity = app.State.BagCount(recipe.Equipment.Id) < GameState.MaxStack;
                m.Add(recipe.Equipment.DisplayName, () => Confirm(T("craft"), string.Join("\n", lines) + "\n\n이 장비를 제작할까요?", () => Execute(TownServices.Craft(app.DB, app.State, recipe.Equipment.Id), m)),
                    string.Join("\n", lines), $"{recipe.Gold:N0}만원", recipe.CanCraft && capacity, !capacity ? T("reason_stack_full") : app.State.Gold < recipe.Gold ? T("reason_not_enough_gold") : T("reason_missing_materials"), UIArtwork.Gear(recipe.Equipment.Id));
            }
        }, new[] { T("tab_craft"), T("tab_enhance") });
        /// <summary>Smithy 강화 tab: every owned piece with its next step, before → after stats and cost.</summary>
        void AddEnhanceRows(GameMenuScreen m)
        {
            var entries = Enhancement.Candidates(app.DB, app.State);
            if (entries.Count == 0) { m.Add(T("smithy_enhance_empty"), () => UIModal.Alert(root.Modals, T("smithy_title"), T("smithy_enhance_empty")), T("smithy_enhance_empty")); return; }
            foreach (var row in entries)
            {
                var entry = row; var piece = entry.Equipment;
                string name = EquipmentName(piece.Id);
                if (entry.Cost == null)
                {
                    m.Add(name, () => UIModal.Alert(root.Modals, name, EquipmentDescription(piece)), EquipmentDescription(piece) + "\n\n" + T("reason_max_enhance"), "+10 최대", false, T("reason_max_enhance"), UIArtwork.Gear(piece.Id));
                    continue;
                }
                string details = EnhancePreview(entry);
                string reason = entry.StonesOwned < entry.Cost.Stones ? T("reason_missing_stones") : T("reason_not_enough_gold");
                m.Add(name, () => Confirm(T("enhance"), details + "\n\n강화할까요? (실패하지 않습니다)", () => Execute(Enhancement.Enhance(app.DB, app.State, piece.Id), m)),
                    details, $"+{entry.Level} → +{entry.Level + 1}", entry.CanEnhance, reason, UIArtwork.Gear(piece.Id));
            }
        }
        string EnhancePreview(EnhanceEntry entry)
        {
            var piece = entry.Equipment;
            var before = Enhancement.Stats(piece, entry.Level);
            var after = Enhancement.Stats(piece, entry.Level + 1);
            var lines = new List<string> { $"<b>{Enhancement.DisplayName(piece, entry.Level)} → {Enhancement.DisplayName(piece, entry.Level + 1)}</b>", "", "<b>능력치     현재 → 강화 후</b>" };
            void Line(string label, int a, int b) { if (a != 0 || b != 0) ComparisonLine(lines, label, a, b); }
            Line(T("stat_hp"), before.MaxHp, after.MaxHp);
            Line(T("stat_mp"), before.MaxMp, after.MaxMp);
            Line(T("stat_atk"), before.Attack, after.Attack);
            Line(T("stat_mag"), before.Magic, after.Magic);
            Line(T("stat_def"), before.Defense, after.Defense);
            Line(T("stat_res"), before.Resistance, after.Resistance);
            Line(T("stat_spd"), before.Speed, after.Speed);
            lines.Add("");
            lines.Add($"{ItemName(entry.Cost.StoneId)} · {entry.StonesOwned}/{entry.Cost.Stones}");
            lines.Add($"강화비 {entry.Cost.Gold:N0}만원  ·  {GoldLine}");
            lines.Add($"보유 {entry.Owned}개 (같은 장비는 모두 함께 강화됩니다)");
            return string.Join("\n", lines);
        }
        public void ShowQuests(bool guild = false) => Menu(guild ? T("guild_title") : "의뢰 수첩", guild ? T(GameFlow.GreetingKey(app.DB, app.State, "guild_clerk")) : "의뢰의 진행 상황을 확인합니다. 수락과 보상 수령은 길드 접수처에서 할 수 있습니다.", m =>
        {
            QuestLog.Refresh(app.DB, app.State);
            if (guild)
            {
                m.Add(T("hunter_scout", "헌터 스카우트"), ShowScout, "길드에 새 헌터를 영입합니다. 깊은 구역에 도달할수록 실력 있는 헌터가 찾아옵니다.", ScoutBoardValue(), icon: UIArtwork.Command("party"));
                m.Add(T("job_title", "전직"), ShowJobs, T("job_greeting", "전직"), JobBoardValue(), icon: UIArtwork.Command("party"));
            }
            foreach (var row in TownServices.QuestBoard(app.DB, app.State))
            {
                var entry = row; var quest = entry.Quest;
                string status = QuestStatus(entry.State);
                string target = QuestTarget(quest);
                string details = $"{quest.Description}\n\n{T("quest_kind_" + quest.Kind)} · {target} ×{entry.Count}\n진행 {entry.Progress}/{entry.Count}\n{status}\n\n{T("reward")} · {QuestLog.RewardText(app.DB, quest)}";
                if (entry.State == QuestBoardState.Locked) details += $"\n{app.DB.Floors[Mathf.Clamp(quest.UnlockFloor, 0, app.DB.Floors.Count - 1)].FloorLabel} 도달 시 해금";
                m.Add(quest.Title, () =>
                {
                    if (guild && entry.State == QuestBoardState.Available) Confirm("의뢰 수락", details + "\n\n이 의뢰를 수락할까요?", () => Execute(TownServices.AcceptQuest(app.DB, app.State, quest.Id), m));
                    else if (guild && entry.State == QuestBoardState.Complete) Execute(TownServices.ClaimQuest(app.DB, app.State, quest.Id), m);
                    else UIModal.Alert(root.Modals, quest.Title, details);
                }, details, status);
            }
        });
        string ScoutBoardValue()
        {
            int open = 0;
            foreach (var offer in HunterRoster.ScoutOffers(app.DB, app.State)) if (offer.Unlocked) open++;
            return open > 0 ? $"영입 가능 {open}명" : "명단 확인";
        }
        void ShowScout() => Menu(T("hunter_scout", "헌터 스카우트"), "길드에 새 헌터를 영입합니다.", m =>
        {
            m.Subtitle = "계약금을 내면 바로 합류합니다  ·  " + GoldLine;
            var offers = HunterRoster.ScoutOffers(app.DB, app.State);
            if (offers.Count == 0) AddInformation(m, "스카우트 명단이 비었습니다", "스카우트할 수 있는 헌터를 모두 영입했습니다.");
            foreach (var row in offers)
            {
                var offer = row; var def = offer.Hunter;
                string where = offer.Unlocked ? "" : $"\n\n{def.JoinZone}구역에 도달하면 스카우트할 수 있습니다.";
                string details = $"{HunterProfile(def.Id)}\n\nHP {def.MaxHp} · MP {def.MaxMp} · 공격 {def.Attack} · 마력 {def.Magic} · 속도 {def.Speed}\n합류 레벨 · 현재 헌터 평균 레벨{where}";
                m.Add(offer.Unlocked ? def.DisplayName : $"{def.DisplayName} · 미해금", () => Confirm("헌터 스카우트", $"{def.DisplayName}\n{HunterProfile(def.Id)}\n\n계약금 {offer.Price:N0}만원 · {GoldLine}\n\n영입할까요?", () =>
                {
                    var result = HunterRoster.Scout(app.DB, app.State, def.Id);
                    Execute(result, m);
                    if (result.Success) { AudioManager.Instance?.PlayJingle("jingle_level"); app.RefreshRosterVisuals(); }
                }), details, $"{offer.Price:N0}만원", offer.Unlocked && app.State.Gold >= offer.Price,
                    offer.Unlocked ? T("reason_not_enough_gold") : T("scout_locked", "아직 스카우트할 수 없는 헌터입니다."), UIArtwork.Hero(def.Id));
            }
        });
        string QuestStatus(QuestBoardState state)
        {
            switch (state)
            {
                case QuestBoardState.Locked: return "미해금";
                case QuestBoardState.Available: return T("accept");
                case QuestBoardState.Accepted: return T("in_progress");
                case QuestBoardState.Complete: return T("claim");
                default: return T("claimed");
            }
        }
        string QuestTarget(QuestDef quest)
        {
            if (app.DB.Items.TryGetValue(quest.TargetId, out var item)) return item.DisplayName;
            if (app.DB.Enemies.TryGetValue(quest.TargetId, out var enemy)) return enemy.DisplayName;
            foreach (var floor in app.DB.Floors) if (floor.Id == quest.TargetId) return floor.FloorLabel + " · " + floor.AreaName;
            return "게이트 탐사";
        }
        // Tabs 0-5 = zone pairs 1-2 .. 11-12 (bestiary chapters 1-6), tab 6 = the red gate (chapter 7), tab 7 = milestone rewards.
        static readonly string[] BestiaryTabs = { "1·2구역", "3·4구역", "5·6구역", "7·8구역", "9·10구역", "11·12구역", "붉은 게이트", "보상" };
        const int BestiaryRewardTab = 7;
        void ShowBestiary() => Menu(T("bestiary_title"), T("menu_bestiary_sub"), m =>
        {
            var rows = TownServices.BestiaryRows(app.DB, app.State);
            int found = 0, killed = 0, kills = 0;
            foreach (var row in rows) { if (row.Seen) found++; if (row.Kills > 0) killed++; kills += row.Kills; }
            m.Subtitle = $"발견 {found}/{rows.Count} · 토벌 완료 {killed}/{rows.Count} · 누적 토벌 {kills:N0}회";
            if (m.TabIndex == BestiaryRewardTab) { AddBestiaryRewards(m); return; }
            int chapter = m.TabIndex + 1;
            foreach (var row in rows)
            {
                if (row.Chapter != chapter) continue;
                var entry = row; var enemy = entry.Enemy;
                string title = (entry.IsBoss ? "보스 · " : entry.IsElite ? "강적 · " : "") + (entry.Seen ? enemy.DisplayName : T("unknown_name"));
                Color? accent = entry.IsBoss ? UITheme.GoldBright : entry.IsElite ? UITheme.Epic : (Color?)null;
                string description = entry.Seen ? BestiaryDetails(entry) : $"{T("bestiary_unseen")}\n\n수록 · {BestiaryChapterName(entry.Chapter)}";
                m.Add(title, () => UIModal.Alert(root.Modals, title, description), description, entry.Seen ? $"{entry.Kills}회" : "미발견",
                    icon: entry.Seen ? UIArtwork.Enemy(enemy.Id) : null, labelColor: entry.Seen ? accent : null);
            }
        }, BestiaryTabs);
        string BestiaryChapterName(int chapter) => chapter >= 7 ? "붉은 게이트" : $"{2 * chapter - 1}·{2 * chapter}구역";
        string BestiaryDetails(BestiaryRow entry)
        {
            var enemy = entry.Enemy;
            var weak = new List<string>();
            foreach (int element in entry.RevealedWeaknesses) weak.Add(T("element_" + element));
            if (entry.HiddenWeaknesses > 0) weak.Add("?");
            var drops = new List<string>();
            if (entry.DropsRevealed)
                foreach (var drop in enemy.Drops)
                {
                    int rarity = ItemRarity(drop.Id);
                    drops.Add($"{UITheme.Tag(UITheme.RarityColor(rarity))}{UITheme.RarityName(rarity)}</color> {ItemName(drop.Id)} · {drop.Chance:P0}");
                }
            string rank = entry.IsBoss ? "등급 · 보스 · 게이트의 주인" : entry.IsElite ? "등급 · 강적 · 배회 강적" : "등급 · 일반 · 게이트 몬스터";
            string lore = app.DB.Text.TryGetValue("enemy_desc_" + enemy.Id, out var loreText) ? loreText + "\n" : "";
            string habitat = entry.Habitat.Count == 0 ? "알 수 없음" : string.Join(" · ", entry.Habitat);
            return $"{enemy.DisplayName} · Lv.{enemy.Level}\n{rank}\n{lore}HP {enemy.MaxHp} · MP {enemy.MaxMp}\n공격 {enemy.Attack} · 마력 {enemy.Magic}\n방어 {enemy.Defense} · 저항 {enemy.Resistance} · 속도 {enemy.Speed}\n실드 {enemy.BreakShield}\n토벌 {entry.Kills:N0}회\n서식지 · {habitat}\n\n약점 · {(weak.Count == 0 ? T("weak_none") : string.Join(" · ", weak))}\n\n드롭 · {(!entry.DropsRevealed ? T("drops_unknown") : drops.Count == 0 ? T("drops_none") : string.Join("\n", drops))}";
        }
        int ItemRarity(string id) => app.DB.Items.TryGetValue(id, out var item) ? item.Rarity : app.DB.Equipment.TryGetValue(id, out var piece) ? piece.Rarity : 0;
        void AddBestiaryRewards(GameMenuScreen m)
        {
            foreach (var milestone in TownServices.BestiaryMilestones(app.DB, app.State))
            {
                var row = milestone;
                bool claimable = row.Reached && !row.Claimed;
                string status = row.Claimed ? T("claimed") : row.Reached ? "선택하면 보상을 받습니다." : "아직 조건을 달성하지 못했습니다.";
                string details = $"{row.Label}\n진행 {row.Progress}/{row.Goal}\n\n{T("reward")} · {row.RewardText}\n\n{status}";
                m.Add(row.Label, () => Confirm(T("claim"), $"{row.Label} 달성 보상\n\n{row.RewardText}\n\n보상을 받을까요?", () => Execute(TownServices.ClaimBestiaryReward(app.DB, app.State, row.Index), m)),
                    details, row.Claimed ? T("claimed") : row.Reached ? T("claim") : $"{row.Progress}/{row.Goal}", claimable, row.Claimed ? T("claimed") : T("reason_not_reached"),
                    labelColor: claimable ? UITheme.GoldBright : (Color?)null);
            }
        }
        void ShowElder()
        {
            var lines = new List<string>();
            foreach (string key in GameFlow.ElderLineKeys(app.DB, app.State)) lines.Add(T(key));
            root.Screens.Push<GameStoryScreen>(s => { s.Title = T("npc_elder_name"); s.Pages = lines; s.CharactersPerSecond = app.Preferences.TextSpeed; s.ReducedMotion = app.Preferences.ReducedMotion; });
        }
        void ShowDepart() => Menu(T("depart_title"), $"탐험 기록 · 최심부 {DeepestLabel}", m =>
        {
            foreach (int value in TownServices.DepartureFloors(app.DB, app.State))
            {
                int index = value; var floor = app.DB.Floors[index];
                m.Add(floor.FloorLabel + " · " + floor.AreaName, () => Confirm(T("depart"), $"{floor.FloorLabel} · {floor.AreaName}\n\n준비를 마치고 출발할까요?", () => app.Depart(index)),
                    floor.AreaDescription + "\n\n" + T(index == 0 ? "depart_start" : "depart_warp"));
            }
        });
    }
}
