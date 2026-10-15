// Handoff source for the parent's Unity EditMode NUnit test assembly.
// Uses the real ClipAnimator and Unity Playables; it is not a standalone logic harness.
// Not auto-discovered from docs/. Do not include in Tools/logic_test.py (Unity dependencies).
using System.Reflection;
using Abyss.Runtime.Art;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Abyss.Verification
{
    public sealed class BattleAnimationEntryRegressionTests
    {
        GameObject _root;
        ClipAnimator _anim;
        AnimationClip[] _clips;
        const float Phase = .9f, Seam = .3f;

        [SetUp]
        public void SetUp()
        {
            _root = new GameObject("ClipAnimator regression");
            new GameObject("Body").transform.SetParent(_root.transform, false);
            _clips = new[] { Clip("Idle", true), Clip("BattleIdle", true), Clip("Attack", false) };
            _anim = _root.AddComponent<ClipAnimator>();
            _anim.Init(_clips);
            typeof(ClipAnimator).GetField("_phase", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(_anim, Phase);
            _anim.RestClip = "BattleIdle";
            _anim.Play("Attack", 0f);
        }

        static AnimationClip Clip(string name, bool loop)
        {
            var clip = new AnimationClip { name = name, frameRate = 30f };
            clip.SetCurve("Body", typeof(Transform), "localPosition.x", AnimationCurve.Linear(0f, 0f, 1.5f, 1f));
            var settings = AnimationUtility.GetAnimationClipSettings(clip);
            settings.loopTime = loop;
            AnimationUtility.SetAnimationClipSettings(clip, settings);
            return clip;
        }

        [TearDown]
        public void TearDown()
        {
            Object.DestroyImmediate(_root); // ClipAnimator.OnDestroy releases the real playable graph first.
            if (_clips != null) foreach (var clip in _clips) Object.DestroyImmediate(clip);
        }

        [TestCase(1f, 1f, ClipAnimator.ReturnFade)]
        [TestCase(1f, 2f, ClipAnimator.ReturnFade)]
        [TestCase(1f, 0f, ClipAnimator.ReturnFade)]
        [TestCase(1.6f, 1f, ClipAnimator.ReturnFade)]
        [TestCase(1f, 1f, 0f)]
        public void LateRestEntryReservesBothFades(float clipRate, float battleSpeed, float fade)
        {
            _anim.SetLoopBlend("BattleIdle", Seam);
            _anim.SetClipRate("BattleIdle", clipRate);
            _anim.SetSpeed(battleSpeed);
            _anim.Play("Idle", fade);

            float remainingBattleSeconds = (1f - _anim.NormalizedTime) * _anim.Length("BattleIdle") / clipRate;
            Assert.That(_anim.CurrentClip, Is.EqualTo("BattleIdle"));
            Assert.That(remainingBattleSeconds, Is.GreaterThanOrEqualTo(fade + Seam - .00001f),
                "The first seam must leave time for the incoming blend and a full outgoing seam blend.");
            Assert.That(_anim.NormalizedTime, Is.GreaterThan(0f), "Keep unit phase variation instead of synchronizing every rest entry to zero.");
        }

        [Test]
        public void ExplicitStartRemainsAuthoritative()
        {
            _anim.SetLoopBlend("BattleIdle", Seam);
            _anim.PlayFrom("BattleIdle", Phase, ClipAnimator.ReturnFade, null);
            Assert.That(_anim.NormalizedTime, Is.EqualTo(Phase).Within(.00001f));
        }

        [Test]
        public void LoopWithoutSeamCorrectionRetainsItsPhase()
        {
            _anim.Play("Idle", ClipAnimator.ReturnFade);
            Assert.That(_anim.NormalizedTime, Is.EqualTo(Phase).Within(.00001f));
        }

        [Test]
        public void SafeRestEntriesKeepDifferentUnitPhases()
        {
            _anim.SetLoopBlend("BattleIdle", Seam);
            _anim.Play("Idle", ClipAnimator.ReturnFade);
            float laterEntry = _anim.NormalizedTime;
            _anim.Play("Attack", 0f);
            typeof(ClipAnimator).GetField("_phase", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(_anim, .2f);
            _anim.Play("Idle", ClipAnimator.ReturnFade);
            Assert.That(_anim.NormalizedTime, Is.LessThan(laterEntry));
            Assert.That(_anim.NormalizedTime, Is.GreaterThan(0f));
        }
    }
}
