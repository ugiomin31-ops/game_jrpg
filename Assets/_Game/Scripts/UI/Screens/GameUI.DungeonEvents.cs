using System;
using System.Collections.Generic;
using Abyss.Logic;
using Abyss.Logic.Dungeon;

namespace Abyss.UI
{
    /// <summary>Rescue / elite-choice event presentation. All state changes happen in DungeonRun; GameApp saves them.</summary>
    public sealed partial class GameUI
    {
        /// <summary>
        /// Elite nest offer: accept (fight the elite group for the special reward), leave (gone for good) or decide later
        /// (cancel; the nest re-opens on Interact). Each answer is delivered once; the run rejects stale answers anyway.
        /// </summary>
        public void ShowDungeonChoice(DungeonChoice choice, Action<DungeonChoice, int> resolve, Action<DungeonChoice> dismiss)
        {
            if (choice?.Event == null) return;
            var row = choice.Event;
            var lines = new List<string>();
            if (!string.IsNullOrEmpty(row.Text)) lines.Add(row.Text);
            lines.Add("<color=#E8B04A>" + T("event_choice_risk", "") + "</color>");
            string preview = RewardSummary(row.Reward);
            if (preview.Length > 0) lines.Add(app.DB.T("event_choice_reward_preview", preview));
            string accept = string.IsNullOrEmpty(row.AcceptLabel) ? "도전한다" : row.AcceptLabel;
            string leave = string.IsNullOrEmpty(row.LeaveLabel) ? "지나간다" : row.LeaveLabel;
            const int later = 2;
            bool answered = false;
            UIModal.Choice(root.Modals, string.IsNullOrEmpty(row.Title) ? T("lore") : row.Title, string.Join("\n\n", lines),
                new[] { accept, leave, T("event_choice_later", "나중에") }, index =>
                {
                    if (answered) return;
                    answered = true;
                    if (index == DungeonChoice.Accept || index == DungeonChoice.Leave) resolve?.Invoke(choice, index);
                    else dismiss?.Invoke(choice);
                }, cancelIndex: later, defaultIndex: later);
        }

        /// <summary>Event reward reveal (rescue thanks, elite victory bonus) on the shared loot popup.</summary>
        public void ShowEventReward(string title, TreasureContents contents, Action closed = null)
        {
            if (contents == null) { closed?.Invoke(); return; }
            var entries = new List<UILootEntry>();
            foreach (var kv in contents.Equipment)
            {
                app.DB.Equipment.TryGetValue(kv.Key, out var piece);
                entries.Add(new UILootEntry
                {
                    Icon = UIArtwork.Gear(kv.Key), Name = ItemName(kv.Key), Count = kv.Value,
                    Tag = piece == null ? "장비" : UITheme.RarityName(piece.Rarity) + " · " + T("slot_" + piece.Slot, "장비"),
                    Accent = piece == null ? UITheme.Dawn : UITheme.RarityColor(piece.Rarity),
                });
            }
            foreach (var kv in contents.Items)
            {
                app.DB.Items.TryGetValue(kv.Key, out var item);
                entries.Add(new UILootEntry
                {
                    Icon = UIArtwork.Item(kv.Key), Name = ItemName(kv.Key), Count = kv.Value,
                    Tag = UITheme.RarityName(item?.Rarity ?? 0) + " · " + UITheme.ItemCategory(item?.ItemType ?? ItemType.Healing), Accent = UITheme.RarityColor(item?.Rarity ?? 0),
                });
            }
            UILootPopup.Show(root.Modals, title, entries, contents.Gold, closed);
        }

        string RewardSummary(TreasureContents contents)
        {
            if (contents == null) return "";
            var parts = new List<string>();
            if (contents.Gold > 0) parts.Add($"{contents.Gold:N0}만원");
            foreach (var kv in contents.Items) parts.Add($"{ItemName(kv.Key)} ×{kv.Value}");
            foreach (var kv in contents.Equipment) parts.Add($"{ItemName(kv.Key)} ×{kv.Value}");
            return string.Join(" · ", parts);
        }
    }
}
