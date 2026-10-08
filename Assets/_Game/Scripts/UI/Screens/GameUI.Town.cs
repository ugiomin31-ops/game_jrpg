using System;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Game;
using Abyss.Runtime;
using UnityEngine;

namespace Abyss.UI
{
    public sealed partial class GameUI
    {
        static readonly string[] TownIds = { "innkeeper", "shopkeeper", "smith", "guild_clerk", "bestiary", "party", "elder", "gate" };
        static readonly string[] TownTitles = { "menu_inn", "menu_shop", "menu_smithy", "menu_guild", "menu_bestiary", "menu_party", "npc_elder_name", "menu_depart" };
        string GoldLine => $"{app.State.Gold:N0} G";
        string DeepestLabel => app.DB.Floors[Mathf.Clamp(app.State.DeepestFloor, 0, app.DB.Floors.Count - 1)].FloorLabel;
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
            var services = UIFactory.Panel(hud, UIPanelStyle.Ornate, name: "Town service cards");
            bool compact = UIRoot.Compact;
            const float width = 440f;
            services.Rect.Place(UIAnchor.TopRight, new Vector2(-24, compact ? -126 : -156), new Vector2(width, 548));
            UIFactory.Label(services.Rect, "마을에서 준비하기", 32, UIFont.Title, UITheme.GoldBright, TMPro.TextAlignmentOptions.Center, UITextFx.Outline).Rt().TopStrip(44, 18, 24, 24);
            UIFactory.Separator(services.Rect, width - 80f).rectTransform.Place(UIAnchor.Top, new Vector2(0, -66), new Vector2(width - 80f, 18));
            UIFactory.Label(services.Rect, "회복 · 보급 · 성장", 21, color: UITheme.TextDim, align: TMPro.TextAlignmentOptions.Center).Rt().TopStrip(28, 80, 24, 24);
            var hints = new[] { "파티 회복", "소모품 · 장비", "장비 제작", "의뢰 · 전직", "약점 · 전리품", "장비 · 기술", "이야기", "미궁 탐험 시작" };
            for (int i = 0; i < TownIds.Length; i++)
            {
                string id = TownIds[i];
                var button = UIFactory.Button(services.Rect, (id == "elder" ? "촌장" : T(TownTitles[i])) + "\n<size=20>" + hints[i] + "</size>",
                    () => { if (!BlocksWorldInput) { UIInput.Consume(); ShowTownService(id); } }, TownArtwork(id));
                button.Rt().Place(UIAnchor.TopLeft, new Vector2(20 + (i % 2) * 204, -124 - (i / 2) * 102), new Vector2(196, UIRoot.TouchFirst ? UIRoot.TouchTargetHeight : 92));
                button.Label.textWrappingMode = TMPro.TextWrappingModes.Normal;
                button.Label.fontSizeMax = 25;
                if (id == "gate") button.Label.color = UITheme.DawnBright;
            }
            string help = UIRoot.TouchFirst
                ? "이동 · 화면을 누른 채 끌기    대화 · 시설 근처에서 탭    수첩 · 오른쪽 아래 버튼"
                : "이동 · WASD / 방향키 / 왼쪽 스틱    대화 · E / 확인    수첩 · Tab / Start";
            UIFactory.Label(hud, help, 21, color: UITheme.TextDim)
                .Rt().BottomStrip(38, 212, 30, 470);
        }
        void RefreshTown()
        {
            if (app.Screen != GameScreen.Town || area == null) return;
            area.text = T("town_title");
            resources.text = $"{GoldLine}  ·  최심부 {DeepestLabel}  ·  {DifficultyName(app.State.Difficulty)}";
            RefreshVitals();
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
            m.Add(T("inn_rest"), () => Confirm(T("inn_offer"), $"숙박비 {cost:N0} G를 지불하고 쉴까요?\n\n{T("inn_note")}", () => Execute(TownServices.RestAtInn(app.DB, app.State), m)), T("inn_note"), $"{cost:N0} G", app.State.Gold >= cost, T("reason_not_enough_gold"));
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
                    if (!entry.Unlocked) description += $"\n{app.DB.Floors[Math.Min(app.DB.Floors.Count - 1, (entry.ShopTier - 1) * GameFlow.FloorsPerChapter)].FloorLabel} 도달 시 해금";
                    m.Add(entry.DisplayName, () => ShowQuantity(T("buy") + " · " + entry.DisplayName, maximum, entry.Price, n => equipment ? TownServices.BuyEquipment(app.DB, app.State, entry.Id, n) : TownServices.BuyItem(app.DB, app.State, entry.Id, n), m), description, $"{entry.Price:N0} G", entry.Unlocked && maximum > 0, reason, equipment ? UIArtwork.Gear(entry.Id) : UIArtwork.Item(entry.Id));
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
                    ContentDescription(id) + $"\n\n보유 {count}개\n장착 중인 장비는 해제한 뒤 판매할 수 있습니다.", $"{value:N0} G", value > 0, T("reason_not_sellable"), equipment ? UIArtwork.Gear(id) : UIArtwork.Item(id));
            }
        }
        void ShowQuantity(string title, int maximum, int price, Func<int, ServiceResult> operation, GameMenuScreen owner)
        {
            Menu(title, "수량을 선택한 뒤 합계를 확인하고 거래를 승인하세요.", q =>
            {
                for (int i = 1; i <= maximum; i++)
                {
                    int count = i;
                    q.Add($"{count}개", () => Confirm("거래 확인", $"{title}\n수량 {count}개 · 합계 {price * count:N0} G\n{GoldLine}\n\n거래를 진행할까요?", () =>
                    {
                        var result = operation(count);
                        if (result.Success) q.Close();
                        Execute(result, owner);
                    }), $"{title}\n수량 {count}개\n합계 {price * count:N0} G\n\n{GoldLine}", $"{price * count:N0} G");
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
                lines.Add($"제작비 {recipe.Gold:N0} G\n보유 {app.State.BagCount(recipe.Equipment.Id)}개");
                bool capacity = app.State.BagCount(recipe.Equipment.Id) < GameState.MaxStack;
                m.Add(recipe.Equipment.DisplayName, () => Confirm(T("craft"), string.Join("\n", lines) + "\n\n이 장비를 제작할까요?", () => Execute(TownServices.Craft(app.DB, app.State, recipe.Equipment.Id), m)),
                    string.Join("\n", lines), $"{recipe.Gold:N0} G", recipe.CanCraft && capacity, !capacity ? T("reason_stack_full") : app.State.Gold < recipe.Gold ? T("reason_not_enough_gold") : T("reason_missing_materials"), UIArtwork.Gear(recipe.Equipment.Id));
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
            lines.Add($"강화비 {entry.Cost.Gold:N0} G  ·  {GoldLine}");
            lines.Add($"보유 {entry.Owned}개 (같은 장비는 모두 함께 강화됩니다)");
            return string.Join("\n", lines);
        }
        public void ShowQuests(bool guild = false) => Menu(guild ? T("guild_title") : "의뢰 수첩", guild ? T(GameFlow.GreetingKey(app.DB, app.State, "guild_clerk")) : "의뢰의 진행 상황을 확인합니다. 수락과 보상 수령은 마을 길드에서 할 수 있습니다.", m =>
        {
            QuestLog.Refresh(app.DB, app.State);
            if (guild) m.Add(T("job_title", "전직"), ShowJobs, T("job_greeting", "전직"), JobBoardValue(), icon: UIArtwork.Command("party"));
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
            return "미궁 탐험";
        }
        void ShowBestiary() => Menu(T("bestiary_title"), T("menu_bestiary_sub"), m =>
        {
            var rows = TownServices.BestiaryRows(app.DB, app.State);
            int found = 0, kills = 0;
            foreach (var row in rows) { if (row.Seen) found++; kills += row.Kills; }
            m.Subtitle = $"발견한 마물 {found}/{rows.Count} · 누적 토벌 {kills:N0}회";
            foreach (var row in rows)
            {
                var entry = row; var enemy = entry.Enemy;
                string title = entry.Seen ? enemy.DisplayName : T("unknown_name");
                string details = T("bestiary_unseen");
                if (entry.Seen)
                {
                    var weak = new List<string>();
                    foreach (int element in entry.RevealedWeaknesses) weak.Add(T("element_" + element));
                    if (entry.HiddenWeaknesses > 0) weak.Add("?");
                    var drops = new List<string>();
                    if (entry.DropsRevealed) foreach (var drop in enemy.Drops) drops.Add($"{ItemName(drop.Id)} · {drop.Chance:P0}");
                    string lore = app.DB.Text.TryGetValue("enemy_desc_" + enemy.Id, out var loreText) ? loreText + "\n" : "";
                    details = $"{enemy.DisplayName} · Lv.{enemy.Level}\n{(entry.IsBoss ? "봉인의 수호자" : entry.IsElite ? "배회 강적" : "미궁의 마물")}\n{lore}HP {enemy.MaxHp} · MP {enemy.MaxMp}\n공격 {enemy.Attack} · 마력 {enemy.Magic}\n방어 {enemy.Defense} · 저항 {enemy.Resistance} · 속도 {enemy.Speed}\n실드 {enemy.BreakShield}\n토벌 {entry.Kills:N0}회\n\n약점 · {(weak.Count == 0 ? T("weak_none") : string.Join(" · ", weak))}\n\n드롭 · {(!entry.DropsRevealed ? T("drops_unknown") : drops.Count == 0 ? T("drops_none") : string.Join("\n", drops))}";
                }
                string description = details;
                m.Add(title, () => UIModal.Alert(root.Modals, title, description), description, entry.Seen ? $"{entry.Kills}회" : "미발견", icon: entry.Seen ? UIArtwork.Enemy(enemy.Id) : null);
            }
        });
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
