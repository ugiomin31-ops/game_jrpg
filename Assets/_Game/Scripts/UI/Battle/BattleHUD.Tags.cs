using System;
using System.Collections.Generic;
using Abyss.Logic.Battle;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI.Battle
{
    public sealed partial class BattleHUD
    {
        const float TagGap = 8f, TagMargin = 8f, UnitPad = 6f, ChipBand = 44f;

        readonly List<Card> _tagOrder = new List<Card>();
        readonly List<Rect> _blockers = new List<Rect>();
        readonly List<Rect> _placed = new List<Rect>();
        readonly Vector3[] _corners = new Vector3[4];
        float _px0, _py0, _kx, _ky;
        Rect _canvasRect;
        int _hiddenTags, _edgeTags, _iconTags;

        /// <summary>Living enemy tags that found no free slot at any size this frame (always 0 when the packer succeeds).</summary>
        public int UnplacedTagCount => _hiddenTags;
        /// <summary>Tags currently shown as off-screen / no-room edge markers.</summary>
        public int EdgeTagCount => _edgeTags;
        /// <summary>Tags currently shown in the icon fallback size.</summary>
        public int IconTagCount => _iconTags;

        /// <summary>Canvas-space (origin bottom left, canvas units) rectangle of the unit's projected renderer bounds; false when it has none.</summary>
        public bool TryGetUnitRect(string unitId, out Rect rect)
        {
            rect = default;
            if (!_cards.TryGetValue(unitId, out var card) || !card.HasRect) return false;
            rect = card.UnitRect;
            return true;
        }

        bool BuildScreenMap()
        {
            _world.GetWorldCorners(_corners);
            float w = _corners[2].x - _corners[0].x, h = _corners[2].y - _corners[0].y;
            if (w < 1f || h < 1f) return false;
            var r = _world.rect;
            _px0 = _corners[0].x; _py0 = _corners[0].y; _kx = r.width / w; _ky = r.height / h;
            _canvasRect = new Rect(0f, 0f, r.width, r.height);
            return true;
        }

        void ScanRenderers(Card card)
        {
            card.RendererScan = Time.frameCount;
            if (card.Renderers == null) card.Renderers = new List<Renderer>(16);
            card.Renderers.Clear();
            card.Bones.Clear();
            var found = card.Unit.Model.GetComponentsInChildren<Renderer>(false);
            for (int i = 0; i < found.Length; i++)
            {
                if (found[i] is SkinnedMeshRenderer smr)
                {
                    // The skeleton follows the animated pose; SkinnedMeshRenderer.bounds is the padded union of every pose.
                    foreach (var bone in smr.bones)
                        if (bone != null && !card.Bones.Contains(bone)) card.Bones.Add(bone);
                }
                else if (found[i] is MeshRenderer) card.Renderers.Add(found[i]);
            }
        }

        /// <summary>
        /// Projected screen rectangle of a unit: the padded bounds of its animated skeleton (skinned meshes report the padded
        /// union of every animation pose as their bounds, several times the figure) plus the exact bounds of rigid meshes
        /// (weapons, flyers, blobs). False while any corner is behind the camera.
        /// </summary>
        bool TryUnitRect(Card card, out Rect rect)
        {
            rect = default;
            var model = card.Unit.Model;
            if (model == null || !card.Unit.Alive) return false;
            if (card.Renderers == null || Time.frameCount - card.RendererScan > 40) ScanRenderers(card);
            float x0 = float.MaxValue, y0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue;
            bool any = false;
            var bones = card.Bones;
            if (bones.Count > 0)
            {
                Vector3 lo = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue), hi = -lo;
                for (int i = 0; i < bones.Count; i++)
                {
                    var t = bones[i];
                    if (t == null) continue;
                    Vector3 p = t.position;
                    lo = Vector3.Min(lo, p); hi = Vector3.Max(hi, p);
                }
                if (lo.x <= hi.x)
                {
                    float h = Mathf.Max(0.5f, model.Height);
                    lo -= new Vector3(h * 0.14f, h * 0.08f, h * 0.14f); hi += new Vector3(h * 0.14f, h * 0.2f, h * 0.14f);
                    if (!Accumulate(lo, hi, ref x0, ref y0, ref x1, ref y1)) return false;
                    any = true;
                }
            }
            var list = card.Renderers;
            for (int i = 0; i < list.Count; i++)
            {
                var r = list[i];
                if (r == null || !r.enabled || !r.gameObject.activeInHierarchy) continue;
                Bounds b = r.bounds;
                if (!Accumulate(b.min, b.max, ref x0, ref y0, ref x1, ref y1)) return false;
                any = true;
            }
            if (!any) return false;
            rect = Rect.MinMaxRect(x0, y0, x1, y1);
            return true;
        }

        /// <summary>Projects the eight corners of a world box into canvas units and grows the running rectangle.</summary>
        bool Accumulate(Vector3 lo, Vector3 hi, ref float x0, ref float y0, ref float x1, ref float y1)
        {
            for (int k = 0; k < 8; k++)
            {
                var p = new Vector3((k & 1) == 0 ? lo.x : hi.x, (k & 2) == 0 ? lo.y : hi.y, (k & 4) == 0 ? lo.z : hi.z);
                Vector3 s = _camera.WorldToScreenPoint(p);
                if (s.z <= 0.01f) return false;
                float x = (s.x - _px0) * _kx, y = (s.y - _py0) * _ky;
                if (x < x0) x0 = x; if (x > x1) x1 = x;
                if (y < y0) y0 = y; if (y > y1) y1 = y;
            }
            return true;
        }

        static Rect Inflate(Rect r, float by) => new Rect(r.xMin - by, r.yMin - by, r.width + by * 2f, r.height + by * 2f);

        static Rect Clip(Rect r, Rect to)
        {
            float x0 = Mathf.Max(r.xMin, to.xMin), y0 = Mathf.Max(r.yMin, to.yMin), x1 = Mathf.Min(r.xMax, to.xMax), y1 = Mathf.Min(r.yMax, to.yMax);
            return x1 <= x0 || y1 <= y0 ? new Rect(Mathf.Clamp(r.center.x, to.xMin, to.xMax), Mathf.Clamp(r.center.y, to.yMin, to.yMax), 0f, 0f) : Rect.MinMaxRect(x0, y0, x1, y1);
        }

        int CompareTags(Card a, Card b)
        {
            // Targeted/pinned first, then the boss, then arena lane, then id: the same frame state always packs the same way.
            int byFocus = (b.Marked || b.Pinned).CompareTo(a.Marked || a.Pinned);
            if (byFocus != 0) return byFocus;
            int byBoss = b.Unit.Boss.CompareTo(a.Unit.Boss);
            if (byBoss != 0) return byBoss;
            int byLane = a.Unit.ArenaLane.CompareTo(b.Unit.ArenaLane);
            return byLane != 0 ? byLane : string.CompareOrdinal(a.Unit.Id, b.Unit.Id);
        }

        /// <summary>HUD rectangles tags must stay out of (canvas units): top band, party band, command fan, auto notice.</summary>
        void AddHudBlockers(float width, float height)
        {
            _blockers.Add(new Rect(0f, height - _topH, width, _topH));
            _blockers.Add(new Rect(0f, 0f, width, _partyBand + (AnyBottomChip() ? ChipBand : 0f)));
            if (_menu != null && _menu.gameObject.activeSelf) _blockers.Add(CanvasRect(_menu, width));
            if (_autoBanner != null && _autoBanner.gameObject.activeSelf) _blockers.Add(CanvasRect(_autoBanner, width));
            // The skill ribbon (top-centre, just under the top band) covers whatever sits behind it: tags keep out of its resting
            // rectangle, not the slide-in position, so they do not shuffle while it animates. Tags still never feed the camera.
            if (_banner != null && _banner.gameObject.activeSelf)
            {
                Vector2 size = _banner.sizeDelta;
                float top = height - (_topH + 14f);
                _blockers.Add(Inflate(new Rect((width - size.x) * 0.5f, top - size.y, size.x, size.y), TagGap * 0.5f));
            }
        }

        /// <summary>Rect of a bottom-right anchored HUD element in the same 0-based canvas units as the tag packer.</summary>
        static Rect CanvasRect(RectTransform rt, float width)
        {
            Vector2 size = rt.sizeDelta, pos = rt.anchoredPosition;
            return new Rect(width + pos.x - size.x, pos.y, size.x, size.y);
        }

        bool AnyBottomChip()
        {
            foreach (var card in _cards.Values)
                if (card.Party && (card.EnemyThreat || card.Marked) && card.Unit.Alive) return true;
            return _chainPlate != null && _chainPlate.gameObject.activeSelf;
        }

        void UpdateTags()
        {
            if (_camera == null || _world == null || !BuildScreenMap()) return;
            float width = _canvasRect.width, height = _canvasRect.height;
            foreach (var card in _cards.Values)
            {
                card.HasRect = TryUnitRect(card, out card.UnitRect);
                Vector2 c = card.UnitRect.center;
                card.OnScreen = card.HasRect && c.x > 0f && c.x < width && c.y > 0f && c.y < height;
            }
            _blockers.Clear();
            foreach (var card in _cards.Values)
                if (card.HasRect) _blockers.Add(Inflate(card.UnitRect, UnitPad + Mathf.Min(card.UnitRect.width, card.UnitRect.height) * 0.12f));
            AddHudBlockers(width, height);
            _tagOrder.Clear();
            foreach (var card in _cards.Values)
                if (!card.Party)
                {
                    if (card.Unit.Alive && card.Unit.Model != null) _tagOrder.Add(card);
                    else if (card.Root.gameObject.activeSelf) card.Root.gameObject.SetActive(false);
                }
            _tagOrder.Sort(CompareTags);
            _placed.Clear();
            _hiddenTags = _edgeTags = _iconTags = 0;
            foreach (var card in _tagOrder) PlaceTag(card, width, height);
            foreach (var card in _tagOrder) PlacePill(card, width, height);
            foreach (var card in _cards.Values)
                if (!card.Party && (card.Unit.Model == null || !card.Unit.Alive) && card.Pill != null && card.Pill.gameObject.activeSelf) card.Pill.gameObject.SetActive(false);
            PlaceReticles(width, height);
        }

        void PlaceTag(Card card, float width, float height)
        {
            if (!card.HasRect) { SetLevel(card, TagLevel.Hidden, default, Rect.zero, -1); return; }
            Rect unit = Clip(card.UnitRect, _canvasRect);
            bool wantFull = card.Marked || card.Pinned;
            if (card.OnScreen)
            {
                for (int pass = wantFull ? 0 : 1; pass < 3; pass++)
                {
                    TagLevel level = pass == 0 ? TagLevel.Full : pass == 1 ? TagLevel.Compact : TagLevel.Icon;
                    Vector2 size = TagSize(card, level);
                    if (FindSlot(unit, size, card.LastKey, width, height, out var slot, out int key))
                    {
                        if (level == TagLevel.Icon) _iconTags++;
                        SetLevel(card, level, size, slot, key);
                        return;
                    }
                }
            }
            Vector2 edgeSize = TagSize(card, TagLevel.Edge);
            if (FindEdge(card.UnitRect, edgeSize, width, height, out var edge))
            {
                _edgeTags++;
                SetLevel(card, TagLevel.Edge, edgeSize, edge, -2);
                return;
            }
            _hiddenTags++;
            SetLevel(card, TagLevel.Hidden, default, Rect.zero, -1);
        }

        /// <summary>Seats the predicted-damage pill of the targeted enemy next to the unit, clear of every unit, HUD band and tag.</summary>
        void PlacePill(Card card, float width, float height)
        {
            bool want = card.Marked && card.PillOn && card.HasRect && card.OnScreen && card.Unit.Alive;
            if (!want) { if (card.Pill.gameObject.activeSelf) card.Pill.gameObject.SetActive(false); return; }
            Vector2 size = new Vector2(Mathf.Clamp(card.PillText.GetPreferredValues().x + 40f, 190f, 330f), 50f);
            Rect unit = Clip(card.UnitRect, _canvasRect);
            if (!FindSlot(unit, size, -1, width, height, out var slot, out _)) { card.Pill.gameObject.SetActive(false); return; }
            card.Pill.gameObject.SetActive(true);
            card.Pill.Rect.sizeDelta = size; card.Pill.Rect.anchoredPosition = slot.position;
            card.Pill.Rect.SetAsLastSibling();
            _placed.Add(Inflate(slot, 3f));
        }

        Vector2 TagSize(Card card, TagLevel level)
        {
            float w = card.Unit.Boss ? 320f : 264f;
            float h = card.ExtraRow ? 88f : 62f;
            switch (level)
            {
                case TagLevel.Full:
                    w = Mathf.Max(w, 304f); h += 34f;
                    if (card.HasIntent) h += 34f;
                    return new Vector2(w, h);
                case TagLevel.Icon: return new Vector2(92f, 48f);
                case TagLevel.Edge: return new Vector2(112f, 48f);
                default: return new Vector2(w, h);
            }
        }

        static int Shift(int i) => ((i + 1) / 2) * ((i & 1) == 1 ? -1 : 1);

        bool Valid(Rect r, float width, float height)
        {
            if (r.xMin < TagMargin || r.xMax > width - TagMargin || r.yMin < 0f || r.yMax > height) return false;
            for (int i = 0; i < _blockers.Count; i++) if (r.Overlaps(_blockers[i])) return false;
            for (int i = 0; i < _placed.Count; i++) if (r.Overlaps(_placed[i])) return false;
            return true;
        }

        void Try(Rect r, int key, float bias, Rect unit, float wantY, int prev, float width, float height, ref float bestCost, ref Rect best, ref int bestKey)
        {
            if (!Valid(r, width, height)) return;
            float cost = Mathf.Abs(r.center.x - unit.center.x) + Mathf.Abs(r.y - wantY) * 0.6f + bias - (key == prev ? 20f : 0f);
            if (cost < bestCost - 0.001f) { bestCost = cost; best = r; bestKey = key; }
        }

        /// <summary>
        /// Deterministic slot search around one unit: above (two rows), below, then right and left, scored by distance from
        /// the "centred just above the head" ideal. A slot must stay clear of every unit's bounds, the HUD bands and the
        /// tags placed before it.
        /// </summary>
        bool FindSlot(Rect unit, Vector2 size, int prev, float width, float height, out Rect best, out int bestKey)
        {
            best = default; bestKey = -1;
            float bestCost = float.MaxValue, wantY = unit.yMax + TagGap;
            for (int row = 0; row < 2; row++)
                for (int i = 0; i < 15; i++)
                {
                    float x = unit.center.x - size.x * 0.5f + Shift(i) * 44f, y = wantY + row * (size.y + TagGap);
                    Try(new Rect(x, y, size.x, size.y), 100 + row * 20 + i, row * 30f, unit, wantY, prev, width, height, ref bestCost, ref best, ref bestKey);
                }
            for (int i = 0; i < 15; i++)
            {
                float x = unit.center.x - size.x * 0.5f + Shift(i) * 44f, y = unit.yMin - TagGap - size.y;
                Try(new Rect(x, y, size.x, size.y), 200 + i, 70f, unit, wantY, prev, width, height, ref bestCost, ref best, ref bestKey);
            }
            for (int j = -3; j <= 3; j++)
            {
                float y = unit.yMax - size.y + j * 36f;
                Try(new Rect(unit.xMax + TagGap, y, size.x, size.y), 300 + j + 3, 40f, unit, wantY, prev, width, height, ref bestCost, ref best, ref bestKey);
                Try(new Rect(unit.xMin - TagGap - size.x, y, size.x, size.y), 320 + j + 3, 40f, unit, wantY, prev, width, height, ref bestCost, ref best, ref bestKey);
            }
            return bestKey >= 0;
        }

        /// <summary>Edge marker: the nearest free spot along the screen borders (outside the HUD bands), for off-screen units.</summary>
        bool FindEdge(Rect unit, Vector2 size, float width, float height, out Rect best)
        {
            best = default;
            float bestCost = float.MaxValue;
            bool found = false;
            float yLow = _partyBand + 30f, yHigh = height - _topH - size.y - 4f;
            float xHigh = width - TagMargin - size.x;
            if (_menu != null && _menu.gameObject.activeSelf) xHigh = Mathf.Min(xHigh, width + _menu.anchoredPosition.x - _menu.sizeDelta.x - size.x - TagGap);
            Vector2 center = unit.center;
            for (int i = 0; i < 40; i++)
            {
                float t = i / 39f;
                Vector2[] spots =
                {
                    new Vector2(TagMargin, Mathf.Lerp(yLow, yHigh, t)),
                    new Vector2(xHigh, Mathf.Lerp(yLow, yHigh, t)),
                    new Vector2(Mathf.Lerp(TagMargin, xHigh, t), yHigh),
                    new Vector2(Mathf.Lerp(TagMargin, xHigh, t), yLow),
                };
                for (int s = 0; s < spots.Length; s++)
                {
                    var r = new Rect(spots[s], size);
                    if (!Valid(r, width, height)) continue;
                    float cost = (r.center - center).sqrMagnitude;
                    if (cost < bestCost - 0.001f) { bestCost = cost; best = r; found = true; }
                }
            }
            return found;
        }

        void SetLevel(Card card, TagLevel level, Vector2 size, Rect slot, int key)
        {
            var root = card.Root;
            if (level == TagLevel.Hidden)
            {
                if (root.gameObject.activeSelf) root.gameObject.SetActive(false);
                card.Level = level; card.LastKey = -1; card.TagRect = Rect.zero;
                return;
            }
            if (!root.gameObject.activeSelf) root.gameObject.SetActive(true);
            card.Level = level; card.LastKey = key; card.TagRect = slot;
            _placed.Add(Inflate(slot, 3f));
            if (card.Dirty || card.LaidLevel != level || card.LaidSize != size || card.LaidExtra != card.ExtraRow || level == TagLevel.Edge)
            {
                LayoutTag(card, level, size, slot);
                card.Dirty = false; card.LaidLevel = level; card.LaidSize = size; card.LaidExtra = card.ExtraRow;
            }
            root.anchoredPosition = slot.position;
            if (level == TagLevel.Full && root.GetSiblingIndex() != root.parent.childCount - 1) root.SetAsLastSibling();
        }

        void LayoutTag(Card c, TagLevel level, Vector2 size, Rect slot)
        {
            var root = c.Root;
            root.sizeDelta = size;
            bool rich = level == TagLevel.Compact || level == TagLevel.Full;
            float w = size.x, pad = 14f;
            c.Name.gameObject.SetActive(rich);
            foreach (var icon in c.WeakIcons) icon.gameObject.SetActive(rich);
            foreach (var icon in c.StatusIcons) icon.gameObject.SetActive(rich);
            c.Shield.gameObject.SetActive(rich && c.Unit.MaxShield > 0);
            c.IntentIcon.gameObject.SetActive(rich); c.IntentDot.gameObject.SetActive(rich);
            c.HpLine.gameObject.SetActive(level == TagLevel.Full);
            c.IntentLine.gameObject.SetActive(level == TagLevel.Full && c.HasIntent);
            c.IconLabel.gameObject.SetActive(!rich);
            var hp = c.Hp.GetComponent<RectTransform>();
            if (!rich)
            {
                string letter = string.IsNullOrEmpty(c.Unit.Suffix) ? FirstGlyph(c.Unit.Name) : c.Unit.Suffix;
                string label = letter;
                if (level == TagLevel.Edge)
                {
                    Vector2 d = c.UnitRect.center - slot.center;
                    string arrow = Mathf.Abs(d.x) >= Mathf.Abs(d.y) ? (d.x < 0f ? "◀" : "▶") : (d.y < 0f ? "▼" : "▲");
                    label = c.Unit.Boss ? arrow + " 보스" : arrow + " " + letter;
                }
                c.IconLabel.text = label;
                c.IconLabel.rectTransform.Stretch(4f, 2f, 4f, 16f);
                hp.Place(UIAnchor.BottomLeft, new Vector2(12f, 9f), new Vector2(w - 24f, 8f));
                return;
            }
            float intentW = c.HasIntent ? 36f : 0f;
            c.Name.rectTransform.Place(UIAnchor.TopLeft, new Vector2(pad, -3f), new Vector2(w - pad * 2f - intentW, 30f));
            c.IntentIcon.rectTransform.Place(UIAnchor.TopLeft, new Vector2(w - pad - 28f, -4f), new Vector2(28f, 28f));
            c.IntentDot.rectTransform.Place(UIAnchor.TopLeft, new Vector2(w - pad - 8f, 0f), new Vector2(12f, 12f));
            int n = c.WeakCount;
            float weakW = n > 0 ? n * 26f + 6f : 0f;
            for (int i = 0; i < c.WeakIcons.Length; i++)
                c.WeakIcons[i].rectTransform.Place(UIAnchor.TopLeft, new Vector2(w - pad - n * 26f + 2f + i * 26f, -33f), new Vector2(24f, 24f));
            hp.Place(UIAnchor.TopLeft, new Vector2(pad, -41f), new Vector2(w - pad * 2f - weakW, 10f));
            float baseH = c.ExtraRow ? 88f : 62f;
            for (int i = 0; i < c.StatusIcons.Length; i++)
                c.StatusIcons[i].rectTransform.Place(UIAnchor.TopLeft, new Vector2(pad + i * 25f, -64f), new Vector2(22f, 22f));
            c.Shield.Rt().Place(UIAnchor.TopRight, new Vector2(-pad, -66f), new Vector2(Mathf.Max(20f, c.Unit.MaxShield * 12f + 8f), 16f));
            if (level == TagLevel.Full)
            {
                c.HpLine.rectTransform.Place(UIAnchor.TopLeft, new Vector2(pad, -baseH - 2f), new Vector2(w - pad * 2f, 34f));
                c.IntentLine.rectTransform.Place(UIAnchor.TopLeft, new Vector2(pad, -baseH - 32f), new Vector2(w - pad * 2f, 34f));
            }
        }

        void PlaceReticles(float width, float height)
        {
            foreach (var card in _cards.Values)
            {
                if (card.Reticle == null) continue;
                bool show = card.Marked && card.HasRect && card.Unit.Alive;
                if (card.Reticle.gameObject.activeSelf != show) card.Reticle.gameObject.SetActive(show);
                if (!show) continue;
                float breathe = UIRoot.Instance != null && UIRoot.Instance.ReducedMotion ? 0f : Mathf.Sin(Time.unscaledTime * 5f) * 3f;
                Rect r = Inflate(card.UnitRect, 8f + breathe);
                card.Reticle.anchoredPosition = r.position;
                card.Reticle.sizeDelta = r.size;
                card.Reticle.SetAsLastSibling();
            }
        }

        void PulseRings()
        {
            float pulse = 0.5f + 0.5f * Mathf.Sin(Time.unscaledTime * 5f);
            foreach (var card in _cards.Values)
            {
                if (!card.Party || card.Ring == null) continue;
                bool full = card.Unit.MaxTp > 0 && card.Unit.Tp >= card.Unit.MaxTp;
                card.Ring.color = full ? Color.Lerp(UITheme.Tp, Color.white, UIRoot.Instance != null && UIRoot.Instance.ReducedMotion ? 0.3f : pulse * 0.6f) : UITheme.Tp;
            }
        }
    }
}
