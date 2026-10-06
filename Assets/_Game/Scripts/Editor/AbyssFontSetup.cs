using System.IO;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.TextCore.LowLevel;

namespace Abyss.EditorTools
{
    /// <summary>Creates dynamic TMP SDF font assets (Korean) under Resources/Fonts and sets the TMP default font.</summary>
    public static class AbyssFontSetup
    {
        const string SrcDir = "Assets/_Game/Fonts";
        const string OutDir = "Assets/_Game/Resources/Fonts";

        [MenuItem("Abyss/Setup Fonts")]
        public static void Setup()
        {
            Directory.CreateDirectory(OutDir);
            var body = Make("Pretendard-Regular.otf", "Body SDF");
            var bold = Make("Pretendard-Bold.otf", "Bold SDF");
            var heavy = Make("Pretendard-ExtraBold.otf", "Heavy SDF");
            var title = Make("BlackHanSans-Regular.ttf", "Title SDF");
            // Title font lacks some symbols; fall back to Bold, then Body.
            title.fallbackFontAssetTable = new System.Collections.Generic.List<TMP_FontAsset> { bold, body };
            bold.fallbackFontAssetTable = new System.Collections.Generic.List<TMP_FontAsset> { body };
            heavy.fallbackFontAssetTable = new System.Collections.Generic.List<TMP_FontAsset> { body };
            EditorUtility.SetDirty(title); EditorUtility.SetDirty(bold); EditorUtility.SetDirty(heavy);

            var settings = TMP_Settings.instance;
            if (settings != null)
            {
                var so = new SerializedObject(settings);
                so.FindProperty("m_defaultFontAsset").objectReferenceValue = bold;
                so.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(settings);
            }
            AssetDatabase.SaveAssets();
            Debug.Log("[Abyss] fonts ready");
        }

        static TMP_FontAsset Make(string src, string name)
        {
            string path = $"{OutDir}/{name}.asset";
            var existing = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(path);
            if (existing != null) return existing;
            var font = AssetDatabase.LoadAssetAtPath<Font>($"{SrcDir}/{src}");
            var fa = TMP_FontAsset.CreateFontAsset(font, 72, 9, GlyphRenderMode.SDFAA, 2048, 2048, AtlasPopulationMode.Dynamic, true);
            fa.name = name;
            AssetDatabase.CreateAsset(fa, path);
            // Persist atlas texture + material as sub-assets so the asset survives reloads/builds.
            foreach (var tex in fa.atlasTextures)
            {
                if (tex == null) continue;
                tex.name = name + " Atlas";
                AssetDatabase.AddObjectToAsset(tex, fa);
            }
            fa.material.name = name + " Material";
            AssetDatabase.AddObjectToAsset(fa.material, fa);
            EditorUtility.SetDirty(fa);
            return fa;
        }
    }
}
