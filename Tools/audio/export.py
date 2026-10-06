"""Production renderer: python Tools/audio/export.py [optional IDs].
Exports every original composition/design, RIFF loops and Unity's runtime catalogue.
The measured levels below are derived during mastering, not fabricated QA results.
"""
import gc
import json
import sys
from pathlib import Path

from abyss_audio import dsp, master
from songs import title, score, jingles
import effects

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "Assets/_Game/Resources/Audio"


def render_all(selected=()):
    DEST.mkdir(parents=True, exist_ok=True)
    catalogue_path=DEST / "catalogue.json"
    old=json.loads(catalogue_path.read_text(encoding="utf-8"))["entries"] if catalogue_path.exists() else []
    entries={e["id"]:e for e in old}
    jobs=[("bgm_title","bgm","title")]
    jobs += [("bgm_"+n,"bgm",n) for n in score.SCORES]
    jobs += [("jingle_"+n,"jingle",n) for n in jingles.JINGLES]
    jobs += [("sfx_"+n,"sfx",n) for n in effects.IDS]
    for index,(ident,kind,name) in enumerate(jobs):
        if selected and ident not in selected: continue
        print("Rendering "+ident,flush=True)
        song=None
        if kind=="bgm":
            song=title.build() if name=="title" else score.build(name)
            x=master.master_music(song.mixdown(),target_lufs=-16,loop=True)
        elif kind=="jingle":
            song=jingles.build(name)
            x=master.trim_silence(master.master_music(song.mixdown(),target_lufs=-15,loop=False))
        else:
            x=master.trim_silence(master.master_sfx(effects.build(name),target_db=-20 if name.startswith("ui_") else -15))
        master.write_wav(str(DEST / kind / (ident+".wav")),x,dither_seed=index+1000,loop=kind=="bgm")
        metrics=master.stats(x)
        entry={"id":ident,"kind":kind,"resourcePath":"Audio/"+kind+"/"+ident,
               "loop":kind=="bgm","loopStartSample":0,"loopEndSample":len(x) if kind=="bgm" else 0,
               "sampleRate":dsp.SR,"channels":2,"bpm":song.bpm if song else 0,
               "bars":32 if kind=="bgm" else 4 if kind=="jingle" else 0,
               "duration":metrics["duration"],"peakDb":metrics["peak_db"],"rmsDb":metrics["rms_db"],
               "lufs":metrics["lufs"],"clippedSamples":metrics["clipped"]}
        entries[ident]=entry
        catalogue_path.write_text(json.dumps({"version":1,"entries":list(entries.values())},indent=2),encoding="utf-8")
        print(f"Exported {ident}: {metrics['duration']:.2f}s, {metrics['lufs']:.2f} LUFS, {metrics['peak_db']:.2f} dBFS",flush=True)
        del x,song
        gc.collect()
    provenance=("ABYSS ORIGINAL PROCEDURAL SCORE AND SOUND DESIGN\n"
        "All 66 stereo 44.1kHz PCM16 WAVs are synthesised from original note arrangements, additive/subtractive/physical-model instruments and seeded noise.\n"
        "No commercial samples, audio recordings or transcribed commercial melodies are included.\n"
        "Source: Tools/audio; production command: python Tools/audio/export.py\n"
        "10 BGM cues use 32-bar A/A'/B/A'' arrangements with contrasting instrumentation and counterpoint.\n"
        "6 non-looping harmonised notification jingles; 50 separately layered interface, foley, spell and combat sound designs.\n"
        "BGM ring-outs and reverb are folded into the loop head; RIFF smpl specifies inclusive last sample. catalogue.json uses an exclusive loop end.\n"
        "Music target -16 LUFS; jingles -15 LUFS; effects peak-window RMS -15 dBFS (UI -20), peak ceiling -1 dBFS.\n"
        "Actual export duration, loudness, peak and clip counts are in catalogue.json.\n"
        "Unity AudioManager loops complete music clips, crossfades on unscaled time, ducks music during jingles, pools effects and persists mixer volumes/mute.\n"
        "Gameplay pause freezes music/non-UI voices and fade timers; UI voices remain audible. Application suspension pauses every voice.\n")
    (DEST / "Provenance.txt").write_text(provenance,encoding="utf-8")


if __name__=="__main__":
    render_all(sys.argv[1:])
