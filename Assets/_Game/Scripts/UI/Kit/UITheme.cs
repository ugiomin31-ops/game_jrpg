using System.Collections.Generic;
using TMPro;
using UnityEngine;

namespace Abyss.UI
{
    /// <summary>Font families shipped in Resources/Fonts (all dynamic Korean SDF).</summary>
    public enum UIFont
    {
        /// <summary>Pretendard Regular — descriptions, long text.</summary>
        Body,
        /// <summary>Pretendard Bold — default UI labels.</summary>
        Bold,
        /// <summary>Pretendard ExtraBold — numbers, emphasis.</summary>
        Heavy,
        /// <summary>Black Han Sans — titles, banners, damage numbers.</summary>
        Title,
    }

    /// <summary>Text treatment presets (shared TMP materials; never per-label instances).</summary>
    public enum UITextFx
    {
        /// <summary>No outline or shadow.</summary>
        Plain,
        /// <summary>Subtle dark drop shadow — default for text on glass panels.</summary>
        Shadow,
        /// <summary>Thin dark outline + soft shadow — text over 3D scenes / bars.</summary>
        Outline,
        /// <summary>Heavy outline + shadow — damage numbers, banners.</summary>
        Heavy,
        /// <summary>Warm outer glow — focused/highlighted titles.</summary>
        Glow,
    }

    /// <summary>
    /// Visual language of the Abyss UI: deep navy glass, thin gold filigree, white text, dawn-orange focus.
    /// All colours / fonts / sizes / sprites used by the kit come from here.
    /// </summary>
    public static class UITheme
    {
        // ---- colours ------------------------------------------------------------------------------
        /// <summary>Primary text (warm white).</summary>
        public static readonly Color Text = Hex("f6f2e9");
        /// <summary>Secondary text (cool lavender grey).</summary>
        public static readonly Color TextDim = Hex("aab3d6");
        /// <summary>Disabled text.</summary>
        public static readonly Color TextDisabled = Hex("6c7290");
        /// <summary>Gold accent (frames, headers, currency).</summary>
        public static readonly Color Gold = Hex("e6c477");
        /// <summary>Bright gold for highlights.</summary>
        public static readonly Color GoldBright = Hex("fbe7b0");
        /// <summary>Muted gold for subtle lines.</summary>
        public static readonly Color GoldDim = Hex("8c7444");
        /// <summary>Dawn orange — keyboard/gamepad focus and selection.</summary>
        public static readonly Color Dawn = Hex("ffad5a");
        /// <summary>Light dawn for focus text.</summary>
        public static readonly Color DawnBright = Hex("ffe0b0");
        /// <summary>Navy used for flat fills / dimmers.</summary>
        public static readonly Color Navy = Hex("0d1430");
        /// <summary>Very dark navy (outline / shadow tint, never pure black).</summary>
        public static readonly Color Ink = Hex("070914");
        /// <summary>Negative / warning (disabled reasons, low HP).</summary>
        public static readonly Color Danger = Hex("ff5a6e");
        /// <summary>Positive value change.</summary>
        public static readonly Color Positive = Hex("7dffa8");
        /// <summary>HP full.</summary>
        public static readonly Color HpHigh = Hex("5fe08a");
        /// <summary>HP mid.</summary>
        public static readonly Color HpMid = Hex("ffd35a");
        /// <summary>HP low.</summary>
        public static readonly Color HpLow = Hex("ff4e5e");
        /// <summary>MP bar.</summary>
        public static readonly Color Mp = Hex("4fa3ff");
        /// <summary>TP (limit) bar.</summary>
        public static readonly Color Tp = Hex("ffc93d");
        /// <summary>Damage trail behind draining bars.</summary>
        public static readonly Color Trail = Hex("ff3b4a");
        /// <summary>Heal preview trail ahead of filling bars.</summary>
        public static readonly Color HealTrail = Hex("c8ffd8");
        /// <summary>Damage number: weak hit.</summary>
        public static readonly Color NumWeak = Hex("ffe14a");
        /// <summary>Damage number: critical.</summary>
        public static readonly Color NumCrit = Hex("ff2a4d");
        /// <summary>Damage number: heal.</summary>
        public static readonly Color NumHeal = Hex("33ff88");
        /// <summary>Damage number: MP restore.</summary>
        public static readonly Color NumMp = Hex("5cb8ff");
        /// <summary>Damage number: resisted.</summary>
        public static readonly Color NumResist = Hex("9aa6c4");
        /// <summary>Damage number outline.</summary>
        public static readonly Color NumOutline = Hex("1a1020");
        /// <summary>Full-screen dimmer behind modals.</summary>
        public static readonly Color Dim = new Color(0.02f, 0.03f, 0.08f, 0.62f);

        /// <summary>Card fills for result / facility tiles: the same midnight glass family as the kit sprites.</summary>
        public static readonly Color Surface = Hex("111a40");
        public static readonly Color SurfaceRaised = Hex("1d2858");
        public static readonly Color SurfaceSelected = Hex("33407e");
        public static readonly Color Border = Hex("8c7444");
        /// <summary>Rarity accents: common (dim) · rare (azure) · epic (violet) · legendary (gold).</summary>
        public static readonly Color Rare = Hex("7fb6ff");
        public static readonly Color Epic = Hex("cf9dff");

        public static Color RarityColor(int rarity) => rarity >= 3 ? GoldBright : rarity == 2 ? Epic : rarity == 1 ? Rare : TextDim;
        public static string RarityName(int rarity) => rarity >= 3 ? "전설" : rarity == 2 ? "영웅" : rarity == 1 ? "희귀" : "일반";

        // ---- sizes (reference resolution 1920×1080) -------------------------------------------------
        /// <summary>Small captions, tags, key hints.</summary>
        public const float SizeCaption = 20f;
        /// <summary>Descriptions.</summary>
        public const float SizeBody = 25f;
        /// <summary>List rows, buttons.</summary>
        public const float SizeLabel = 28f;
        /// <summary>Panel headers.</summary>
        public const float SizeHeader = 34f;
        /// <summary>Screen titles.</summary>
        public const float SizeTitle = 50f;
        /// <summary>Banners.</summary>
        public const float SizeBanner = 64f;
        /// <summary>Default list row height.</summary>
        public const float RowHeight = 56f;
        /// <summary>Default panel padding.</summary>
        public const float Padding = 24f;

        /// <summary>Reference resolution used by <see cref="UIRoot"/>.</summary>
        public static readonly Vector2 ReferenceResolution = new Vector2(1920f, 1080f);

        // ---- fonts ----------------------------------------------------------------------------------
        static readonly TMP_FontAsset[] Fonts = new TMP_FontAsset[4];
        static readonly string[] FontPaths = { "Fonts/Body SDF", "Fonts/Bold SDF", "Fonts/Heavy SDF", "Fonts/Title SDF" };
        static readonly Dictionary<(UIFont, UITextFx), Material> Materials = new Dictionary<(UIFont, UITextFx), Material>();

        /// <summary>Returns the TMP font asset for a family (loaded once from Resources).</summary>
        public static TMP_FontAsset Font(UIFont font)
        {
            int i = (int)font;
            if (Fonts[i] == null) Fonts[i] = Resources.Load<TMP_FontAsset>(FontPaths[i]);
            return Fonts[i];
        }

        /// <summary>
        /// Shared TMP material for a font + effect preset (created once per combination at runtime).
        /// Returns the font's default material for <see cref="UITextFx.Plain"/>.
        /// </summary>
        public static Material TextMaterial(UIFont font, UITextFx fx)
        {
            var fa = Font(font);
            if (fa == null) return null;
            if (fx == UITextFx.Plain) return fa.material;
            if (Materials.TryGetValue((font, fx), out var m) && m != null) return m;
            m = new Material(fa.material) { name = $"{fa.name} [{fx}]" };
            switch (fx)
            {
                case UITextFx.Shadow:
                    SetUnderlay(m, new Color(0.01f, 0.01f, 0.05f, 0.85f), 0.9f, -1.0f, 0.35f, 0.05f);
                    break;
                case UITextFx.Outline:
                    SetOutline(m, Ink, 0.16f);
                    SetUnderlay(m, new Color(0f, 0f, 0.03f, 0.7f), 0.8f, -1.0f, 0.4f, 0.12f);
                    break;
                case UITextFx.Heavy:
                    SetOutline(m, NumOutline, 0.28f);
                    SetUnderlay(m, new Color(0f, 0f, 0f, 0.75f), 1.0f, -1.2f, 0.25f, 0.3f);
                    break;
                case UITextFx.Glow:
                    SetOutline(m, new Color(0.18f, 0.08f, 0.02f, 1f), 0.10f);
                    SetUnderlay(m, new Color(1f, 0.55f, 0.15f, 0.55f), 0f, 0f, 0.8f, 0.45f);
                    break;
            }
            Materials[(font, fx)] = m;
            return m;
        }

        static void SetOutline(Material m, Color color, float width)
        {
            m.EnableKeyword(ShaderUtilities.Keyword_Outline);
            m.SetColor(ShaderUtilities.ID_OutlineColor, color);
            m.SetFloat(ShaderUtilities.ID_OutlineWidth, width);
            m.SetFloat(ShaderUtilities.ID_FaceDilate, width * 0.35f);
        }

        static void SetUnderlay(Material m, Color color, float offsetX, float offsetY, float softness, float dilate)
        {
            m.EnableKeyword(ShaderUtilities.Keyword_Underlay);
            m.SetColor(ShaderUtilities.ID_UnderlayColor, color);
            m.SetFloat(ShaderUtilities.ID_UnderlayOffsetX, offsetX);
            m.SetFloat(ShaderUtilities.ID_UnderlayOffsetY, offsetY);
            m.SetFloat(ShaderUtilities.ID_UnderlaySoftness, softness);
            m.SetFloat(ShaderUtilities.ID_UnderlayDilate, dilate);
        }

        // ---- helpers --------------------------------------------------------------------------------

        /// <summary>HP fill colour for a 0..1 ratio (red → yellow → green).</summary>
        public static Color HpColor(float ratio)
        {
            ratio = Mathf.Clamp01(ratio);
            return ratio < 0.5f
                ? Color.Lerp(HpLow, HpMid, Mathf.InverseLerp(0.15f, 0.5f, ratio))
                : Color.Lerp(HpMid, HpHigh, Mathf.InverseLerp(0.5f, 0.8f, ratio));
        }

        /// <summary>Same colour with a different alpha.</summary>
        public static Color WithAlpha(this Color c, float a) { c.a = a; return c; }

        /// <summary>Parses "rrggbb" / "rrggbbaa" (no '#').</summary>
        public static Color Hex(string hex)
        {
            ColorUtility.TryParseHtmlString("#" + hex, out var c);
            return c;
        }

        /// <summary>Rich-text colour tag for a colour, e.g. <c>$"{UITheme.Tag(UITheme.Gold)}120</color>"</c>.</summary>
        public static string Tag(Color c) => "<color=#" + ColorUtility.ToHtmlStringRGBA(c) + ">";
    }

    /// <summary>Sprite ids of the generated kit art in Resources/UI (see Tools/ui/gen_ui_sprites.py).</summary>
    public static class UISprites
    {
        static readonly Dictionary<string, Sprite> Cache = new Dictionary<string, Sprite>();

        /// <summary>Loads (cached) Resources/UI/<paramref name="name"/>.</summary>
        public static Sprite Get(string name)
        {
            if (Cache.TryGetValue(name, out var s) && s != null) return s;
            s = Resources.Load<Sprite>("UI/" + name);
            if (s == null) Debug.LogWarning($"[UI] missing sprite Resources/UI/{name}");
            Cache[name] = s;
            return s;
        }

        /// <summary>Navy glass panel with thin gold line (9-slice).</summary>
        public static Sprite PanelGlass => Get("panel_glass");
        /// <summary>Navy glass panel with ornate gold corner filigree and gems (9-slice).</summary>
        public static Sprite PanelOrnate => Get("panel_ornate");
        /// <summary>White rounded rect for tinted flat panels (9-slice).</summary>
        public static Sprite PanelWhite => Get("panel_white");
        /// <summary>White rounded outline (9-slice).</summary>
        public static Sprite PanelOutline => Get("panel_outline");
        /// <summary>Small white rounded rect (9-slice).</summary>
        public static Sprite PanelSmall => Get("panel_small");
        /// <summary>Soft drop shadow (9-slice, extend 28px past the panel).</summary>
        public static Sprite PanelShadow => Get("panel_shadow");
        /// <summary>Tooltip background (9-slice).</summary>
        public static Sprite Tooltip => Get("tooltip");
        /// <summary>Recessed icon slot (9-slice).</summary>
        public static Sprite Slot => Get("slot");
        /// <summary>Button states (9-slice).</summary>
        public static Sprite ButtonNormal => Get("btn_normal");
        /// <summary>Hovered / focused button.</summary>
        public static Sprite ButtonHover => Get("btn_hover");
        /// <summary>Pressed button.</summary>
        public static Sprite ButtonPressed => Get("btn_pressed");
        /// <summary>Disabled button.</summary>
        public static Sprite ButtonDisabled => Get("btn_disabled");
        /// <summary>Dawn glow ring (9-slice, ring sits 22px inside the sprite edge).</summary>
        public static Sprite FocusGlow => Get("focus_glow");
        /// <summary>Tab sprites (9-slice).</summary>
        public static Sprite TabActive => Get("tab_active");
        /// <summary>Inactive tab.</summary>
        public static Sprite TabInactive => Get("tab_inactive");
        /// <summary>Gauge frame / trough (9-slice).</summary>
        public static Sprite BarFrame => Get("bar_frame");
        /// <summary>White shaded gauge fill, tint it (9-slice).</summary>
        public static Sprite BarFill => Get("bar_fill");
        /// <summary>White flat gauge fill (9-slice).</summary>
        public static Sprite BarFlat => Get("bar_flat");
        /// <summary>Shield / break pip (filled).</summary>
        public static Sprite PipOn => Get("pip_on");
        /// <summary>Shield / break pip (empty).</summary>
        public static Sprite PipOff => Get("pip_off");
        /// <summary>Gold circular portrait ring with jewels.</summary>
        public static Sprite PortraitFrame => Get("portrait_frame");
        /// <summary>Circle mask matching the portrait ring's opening.</summary>
        public static Sprite PortraitMask => Get("portrait_mask");
        /// <summary>Navy radial backdrop for portraits.</summary>
        public static Sprite PortraitBg => Get("portrait_bg");
        /// <summary>Gold separator flourish.</summary>
        public static Sprite Separator => Get("separator");
        /// <summary>Soft horizontal glow line.</summary>
        public static Sprite GlowLine => Get("glow_line");
        /// <summary>Selection cursor arrow (points right).</summary>
        public static Sprite Cursor => Get("cursor_arrow");
        /// <summary>Small down arrow (advance prompt / scroll hint).</summary>
        public static Sprite ArrowDown => Get("arrow_down");
        /// <summary>Banner ribbon (9-slice horizontally).</summary>
        public static Sprite Ribbon => Get("banner_ribbon");
        /// <summary>Full-screen vignette.</summary>
        public static Sprite Vignette => Get("vignette");
        /// <summary>Soft radial glow.</summary>
        public static Sprite SoftRadial => Get("soft_radial");
        /// <summary>Vertical fade sheen.</summary>
        public static Sprite Sheen => Get("sheen");
        /// <summary>Horizontal 0→1 alpha ramp.</summary>
        public static Sprite GradientH => Get("gradient_h");
        /// <summary>Vertical 1→0 alpha ramp.</summary>
        public static Sprite GradientV => Get("gradient_v");
        /// <summary>Selected list row highlight (dawn gradient, 9-slice left edge).</summary>
        public static Sprite RowHighlight => Get("row_highlight");
        /// <summary>Flat white.</summary>
        public static Sprite White => Get("white");
        /// <summary>White circle.</summary>
        public static Sprite Circle => Get("circle");
        /// <summary>Small gold diamond bullet.</summary>
        public static Sprite Diamond => Get("diamond");
        /// <summary>Speaker name plate (9-slice).</summary>
        public static Sprite NamePlate => Get("nameplate");
        /// <summary>Key cap for input hints (9-slice).</summary>
        public static Sprite KeyCap => Get("keycap");
    }
}
