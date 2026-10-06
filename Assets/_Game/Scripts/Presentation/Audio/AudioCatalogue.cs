using System;
using System.Collections.Generic;
using UnityEngine;

namespace Abyss.Presentation.Audio
{
    [Serializable]
    public sealed class AudioEntry
    {
        public string id;
        public string kind;
        public string resourcePath;
        public bool loop;
        public int loopStartSample;
        public int loopEndSample;
        public int sampleRate;
        public int channels;
        public float bpm;
        public int bars;
        public float duration;
        public float peakDb;
        public float rmsDb;
        public float lufs;
        public int clippedSamples;
    }

    [Serializable]
    public sealed class AudioCatalogue
    {
        public int version;
        public AudioEntry[] entries;
        readonly Dictionary<string, AudioEntry> byId = new Dictionary<string, AudioEntry>(StringComparer.Ordinal);
        readonly Dictionary<string, AudioClip> clips = new Dictionary<string, AudioClip>(StringComparer.Ordinal);

        public static AudioCatalogue Load()
        {
            var asset = Resources.Load<TextAsset>("Audio/catalogue");
            if (asset == null) throw new InvalidOperationException("Missing Audio/catalogue. Run Tools/audio/export.py.");
            var catalogue = JsonUtility.FromJson<AudioCatalogue>(asset.text);
            if (catalogue == null || catalogue.version != 1 || catalogue.entries == null)
                throw new InvalidOperationException("Invalid original audio catalogue.");
            foreach (var entry in catalogue.entries)
                catalogue.byId.Add(entry.id, entry);
            return catalogue;
        }

        public AudioEntry Find(string id)
        {
            if (id == null || !byId.TryGetValue(id, out var entry))
                throw new ArgumentException("Unknown audio id: " + id, nameof(id));
            return entry;
        }

        public AudioClip Clip(string id, string expectedKind)
        {
            var entry = Find(id);
            if (entry.kind != expectedKind)
                throw new ArgumentException(id + " is not a " + expectedKind + " cue.", nameof(id));
            if (clips.TryGetValue(id, out var clip)) return clip;
            clip = Resources.Load<AudioClip>(entry.resourcePath);
            if (clip == null) throw new InvalidOperationException("Missing audio export: " + entry.resourcePath);
            clips.Add(id, clip);
            return clip;
        }
    }
}
