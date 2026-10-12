namespace Abyss.Runtime.Art
{
    /// <summary>
    /// Animation backend of a <see cref="CharacterModel"/>: the authored-take <see cref="ClipAnimator"/> or the
    /// code-driven <see cref="RiglessBlobAnimator"/> for the few rigless blob creatures. Battle code talks to this
    /// shape only. Time advances at <see cref="SetSpeed"/> x Time.deltaTime; speed 0 freezes the pose.
    /// </summary>
    public interface IModelAnimator
    {
        /// <summary>Name of the take being played (the one a blend is heading to).</summary>
        string CurrentClip { get; }
        /// <summary>Playback position of the current take in take lengths (a looping take keeps counting past 1).</summary>
        float NormalizedTime { get; }
        bool HasClip(string clip);
        /// <summary>Take length in seconds at speed 1 (0 when unknown).</summary>
        float Length(string clip);
        /// <summary>Blend to a take. restart=false ignores a repeat of the current take. then (optional) plays when a one-shot ends.</summary>
        void Play(string clip, float fade = 0.15f, bool restart = true, string then = null);
        /// <summary>Restart a take part-way through (0..1), e.g. a follow-up strike that skips the wind-up.</summary>
        void PlayFrom(string clip, float normalizedStart, float fade = 0.05f, string then = "Idle");
        /// <summary>Play one cycle (including a looping take), then continue with <paramref name="then"/>.</summary>
        void PlayOnce(string clip, string then = "Idle", float fade = 0.1f);
        void SetSpeed(float speed);
    }
}
