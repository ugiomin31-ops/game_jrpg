using System;
using UnityEngine;
using UnityEngine.Audio;

namespace Abyss.Presentation.Audio
{
    /// <summary>Persistent two-deck music player, pooled effects, ducked jingles and saved mixer settings.</summary>
    [DefaultExecutionOrder(-200)]
    public sealed class AudioManager : MonoBehaviour
    {
        const int EffectVoices = 24;
        const int UiVoices = 8;
        const float MusicDuck = 0.32f;
        static AudioManager instance;

        public static AudioManager Instance
        {
            get
            {
                if (instance == null)
                {
                    instance = FindFirstObjectByType<AudioManager>();
                    if (instance == null) new GameObject("Abyss Audio").AddComponent<AudioManager>();
                }
                return instance;
            }
        }

        public string CurrentBgm { get; private set; }
        public bool IsPaused => gamePaused;
        public bool Muted { get; private set; }
        public float MasterVolume { get; private set; }
        public float MusicVolume { get; private set; }
        public float EffectsVolume { get; private set; }
        public AudioCatalogue Catalogue { get; private set; }

        AudioMixer mixer;
        AudioSource[] music;
        AudioSource[] effects;
        AudioSource[] ui;
        AudioSource jingle;
        readonly float[] deckGain = new float[2];
        readonly float[] fadeStart = new float[2];
        readonly float[] fadeTarget = new float[2];
        int currentDeck;
        int effectCursor;
        int uiCursor;
        float fadeDuration;
        float fadeElapsed;
        float duck = 1f;
        float jingleRemaining;
        bool duckJingle;
        bool fading;
        bool gamePaused;
        bool applicationPaused;
        bool sourcesPaused;
        bool uiPaused;
        bool initialized;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetStatics() => instance = null;

        void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }
            instance = this;
            transform.SetParent(null);
            DontDestroyOnLoad(gameObject);
            Catalogue = AudioCatalogue.Load();
            mixer = Resources.Load<AudioMixer>("Audio/AbyssMixer");
            if (mixer == null) throw new InvalidOperationException("Missing Audio/AbyssMixer.");
            var musicGroup = Group("Music");
            var effectsGroup = Group("Effects");
            music = MakePool("Music", 2, musicGroup, false);
            effects = MakePool("Effect", EffectVoices, effectsGroup, false);
            ui = MakePool("UI", UiVoices, effectsGroup, true);
            jingle = MakeSource("Jingle", effectsGroup, false);
            music[0].loop = music[1].loop = true;
            music[0].priority = music[1].priority = 0;
            jingle.priority = 8;
            foreach (var source in ui) source.priority = 16;
            MasterVolume = Mathf.Clamp01(PlayerPrefs.GetFloat("audio.master", 0.85f));
            MusicVolume = Mathf.Clamp01(PlayerPrefs.GetFloat("audio.music", 0.8f));
            EffectsVolume = Mathf.Clamp01(PlayerPrefs.GetFloat("audio.effects", 0.85f));
            Muted = PlayerPrefs.GetInt("audio.muted", 0) != 0;
            initialized = true;
            ApplyVolumes();
        }

        void Start()
        {
            // Exposed mixer parameters are applied after the audio graph's initialization.
            if (instance == this) ApplyVolumes();
        }

        AudioMixerGroup Group(string name)
        {
            foreach (var group in mixer.FindMatchingGroups(name))
                if (group.name == name) return group;
            throw new InvalidOperationException("Missing audio mixer group: " + name);
        }

        AudioSource MakeSource(string name, AudioMixerGroup group, bool isUi)
        {
            var child = new GameObject(name);
            child.transform.SetParent(transform, false);
            var source = child.AddComponent<AudioSource>();
            source.playOnAwake = false;
            source.spatialBlend = 0f;
            source.dopplerLevel = 0f;
            source.outputAudioMixerGroup = group;
            source.ignoreListenerPause = isUi;
            source.priority = 64;
            return source;
        }

        AudioSource[] MakePool(string name, int count, AudioMixerGroup group, bool isUi)
        {
            var result = new AudioSource[count];
            for (int i = 0; i < count; i++) result[i] = MakeSource(name + " " + i, group, isUi);
            return result;
        }

        public void PlayBgm(string id, float crossfadeSeconds = 1.2f)
        {
            if (CurrentBgm == id) return;
            var clip = Catalogue.Clip(id, "bgm");
            // Retain the louder deck when another route interrupts an existing fade.
            int next = music[0].isPlaying || music[1].isPlaying || CurrentBgm != null
                ? (deckGain[0] <= deckGain[1] ? 0 : 1) : 0;
            music[next].Stop();
            music[next].clip = clip;
            music[next].volume = 0f;
            music[next].timeSamples = Catalogue.Find(id).loopStartSample;
            music[next].Play();
            if (sourcesPaused) music[next].Pause();
            deckGain[next] = 0f;
            currentDeck = next;
            CurrentBgm = id;
            BeginFade(next, crossfadeSeconds);
        }

        public void StopBgm(float fadeSeconds = 1f)
        {
            CurrentBgm = null;
            BeginFade(-1, fadeSeconds);
        }

        void BeginFade(int target, float seconds)
        {
            for (int i = 0; i < 2; i++)
            {
                fadeStart[i] = deckGain[i];
                fadeTarget[i] = i == target ? 1f : 0f;
            }
            fadeElapsed = 0f;
            fadeDuration = Mathf.Max(0f, seconds);
            fading = true;
            if (fadeDuration == 0f) AdvanceFade(0f);
        }

        void AdvanceFade(float elapsed)
        {
            fadeElapsed += elapsed;
            float t = fadeDuration > 0f ? Mathf.Clamp01(fadeElapsed / fadeDuration) : 1f;
            for (int i = 0; i < 2; i++)
            {
                // Equal-power interpolation avoids a dip when two unrelated cues overlap.
                deckGain[i] = Mathf.Sqrt(Mathf.Lerp(fadeStart[i] * fadeStart[i], fadeTarget[i] * fadeTarget[i], t));
                music[i].volume = deckGain[i] * duck;
                if (t >= 1f && fadeTarget[i] == 0f) music[i].Stop();
            }
            if (t >= 1f) fading = false;
        }

        public void PlaySfx(string id, float volume = 1f, float pitch = 1f, bool ui = false)
        {
            var clip = Catalogue.Clip(id, "sfx");
            // UI IDs route automatically, allowing existing generic callers to remain pause-safe.
            bool isUi = ui || id.StartsWith("sfx_ui_", StringComparison.Ordinal);
            if (applicationPaused || (gamePaused && !isUi)) return;
            var pool = isUi ? this.ui : effects;
            int cursor = isUi ? uiCursor : effectCursor;
            int chosen = cursor;
            for (int i = 0; i < pool.Length; i++)
            {
                int candidate = (cursor + i) % pool.Length;
                if (!pool[candidate].isPlaying) { chosen = candidate; break; }
            }
            var source = pool[chosen];
            source.Stop();
            source.clip = clip;
            source.volume = Mathf.Clamp01(volume);
            source.pitch = Mathf.Clamp(pitch, 0.5f, 2f);
            source.Play();
            if (isUi) uiCursor = (chosen + 1) % pool.Length;
            else effectCursor = (chosen + 1) % pool.Length;
        }

        public void PlayJingle(string id, bool duckMusic = true)
        {
            var clip = Catalogue.Clip(id, "jingle");
            jingle.Stop();
            jingle.clip = clip;
            jingle.volume = 1f;
            jingle.pitch = 1f;
            jingle.Play();
            if (sourcesPaused) jingle.Pause();
            jingleRemaining = clip.length;
            duckJingle = duckMusic;
        }

        public void SetPaused(bool paused)
        {
            gamePaused = paused;
            RefreshPause();
        }

        void OnApplicationPause(bool paused)
        {
            applicationPaused = paused;
            if (initialized) RefreshPause();
        }

        void RefreshPause()
        {
            bool pause = gamePaused || applicationPaused;
            if (sourcesPaused != pause)
            {
                sourcesPaused = pause;
                PausePool(music, pause);
                PausePool(effects, pause);
                if (pause) jingle.Pause(); else jingle.UnPause();
            }
            if (uiPaused != applicationPaused)
            {
                uiPaused = applicationPaused;
                PausePool(ui, uiPaused);
            }
        }

        static void PausePool(AudioSource[] sources, bool pause)
        {
            foreach (var source in sources)
                if (pause) source.Pause(); else source.UnPause();
        }

        public void SetVolumes(float master, float music, float effects)
        {
            MasterVolume = Mathf.Clamp01(master);
            MusicVolume = Mathf.Clamp01(music);
            EffectsVolume = Mathf.Clamp01(effects);
            ApplyVolumes();
            PlayerPrefs.SetFloat("audio.master", MasterVolume);
            PlayerPrefs.SetFloat("audio.music", MusicVolume);
            PlayerPrefs.SetFloat("audio.effects", EffectsVolume);
            PlayerPrefs.Save();
        }

        public void SetMuted(bool muted)
        {
            Muted = muted;
            ApplyVolumes();
            PlayerPrefs.SetInt("audio.muted", Muted ? 1 : 0);
            PlayerPrefs.Save();
        }

        void ApplyVolumes()
        {
            mixer.SetFloat("MasterVolume", ToDb(Muted ? 0f : MasterVolume));
            mixer.SetFloat("MusicVolume", ToDb(MusicVolume));
            mixer.SetFloat("EffectsVolume", ToDb(EffectsVolume));
        }

        static float ToDb(float value) => value <= 0.0001f ? -80f : 20f * Mathf.Log10(value);

        void Update()
        {
            if (!initialized || sourcesPaused) return;
            float delta = Time.unscaledDeltaTime;
            if (jingleRemaining > 0f) jingleRemaining = Mathf.Max(0f, jingleRemaining - delta);
            float targetDuck = duckJingle && jingleRemaining > 0f ? MusicDuck : 1f;
            duck = Mathf.MoveTowards(duck, targetDuck, delta / (targetDuck < duck ? 0.1f : 0.6f));
            if (fading) AdvanceFade(delta);
            else for (int i = 0; i < 2; i++) music[i].volume = deckGain[i] * duck;
        }

        void OnDestroy()
        {
            if (instance == this) instance = null;
        }
    }
}
