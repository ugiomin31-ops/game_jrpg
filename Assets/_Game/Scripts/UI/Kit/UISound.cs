using System;

namespace Abyss.UI
{
    /// <summary>Semantic UI sound cues emitted by kit widgets.</summary>
    public enum UISoundId
    {
        /// <summary>Cursor moved / hover changed.</summary>
        Move,
        /// <summary>Selection confirmed / button clicked.</summary>
        Confirm,
        /// <summary>Back / cancel.</summary>
        Cancel,
        /// <summary>Tried to pick something disabled.</summary>
        Buzzer,
        /// <summary>Tab switched.</summary>
        Tab,
        /// <summary>Window / screen opened.</summary>
        Open,
        /// <summary>Window / screen closed.</summary>
        Close,
        /// <summary>Toast / banner shown.</summary>
        Notify,
        /// <summary>Typewriter character tick.</summary>
        Type,
    }

    /// <summary>Audio backend for UI cues (implemented by the audio system; the kit never loads clips itself).</summary>
    public interface IUISound
    {
        /// <summary>Plays the cue.</summary>
        void Play(UISoundId id);
    }

    /// <summary>Static dispatch point for UI sounds: widgets call <see cref="Play"/>; audio code sets <see cref="Provider"/> or listens to <see cref="Played"/>.</summary>
    public static class UISound
    {
        /// <summary>Backend that actually plays cues (may be null).</summary>
        public static IUISound Provider { get; set; }

        /// <summary>Raised for every cue (after the provider).</summary>
        public static event Action<UISoundId> Played;

        /// <summary>Emits a cue.</summary>
        public static void Play(UISoundId id)
        {
            Provider?.Play(id);
            Played?.Invoke(id);
        }
    }
}
