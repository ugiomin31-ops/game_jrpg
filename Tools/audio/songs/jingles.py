"""Six original, harmonised cadential fanfares (not looping)."""
from abyss_audio.music import Song, prog

JINGLES = {
    "victory": (148, "D G A D", "A4/.5 D5/.5 F#5/.5 A5/.5 D6/1 r/1 | B5/.5 A5/.5 G5/1 D5/2 | E5/.5 F#5/.5 G5/.5 A5/.5 C#6/1 E6/1 | D6/4", "brass"),
    "defeat": (64, "Bm G Em F#7:2 Bm:2", "F#5/2 E5/1 D5/1 | B4/2 A4/2 | G4/1 F#4/1 E4/2 | A#4/2 B4/2", "cello"),
    "level": (144, "D A Bm G:2 D:2", "D5/.5 F#5/.5 A5/.5 D6/.5 F#6/2 | E6/1 C#6/1 A5/2 | B5/.5 D6/.5 F#6/1 A6/2 | G6/1 E6/1 D6/2", "glock"),
    "quest": (120, "G D/F# Em7 A:2 D:2", "G5/1 B5/.5 D6/.5 B5/2 | A5/1 F#5/1 D5/2 | E5/1 G5/1 B5/2 | A5/1 C#6/1 D6/2", "flute"),
    "treasure": (138, "Bm G A D", "B5/.25 D6/.25 F#6/.5 B6/1 F#6/2 | G6/.5 D6/.5 B5/1 D6/2 | E6/.5 C#6/.5 A5/1 C#6/2 | D6/4", "celesta"),
    "rest": (80, "Dmaj7 Gmaj7 Em7 A:2 Dmaj7:2", "F#5/2 E5/2 | D5/1 B4/1 G4/2 | B4/2 G4/2 | A4/2 D5/2", "music_box"),
}


def build(name):
    bpm, harmony, melody, inst = JINGLES[name]
    s = Song("jingle_"+name, bpm, 4, seed=301+list(JINGLES).index(name), loop=False, tail=4,
             reverb=(1.5,.02,.55))
    lead = s.track("lead", gain=.9, reverb=.3)
    strings = s.track("harmony", gain=.55, reverb=.35)
    bass = s.track("bass", gain=.7, reverb=.15)
    arp = s.track("sparkle", gain=.5, pan=.15, reverb=.3)
    p = prog(harmony,4)
    lead.melody(inst, melody, vel=.72)
    strings.chords("string_pad",p,center=62,size=3,vel=.5)
    bass.bass("orch_bass",p,[(0,3,0,1)],octave=2,vel=.55)
    arp.arp("harp" if name in ("rest","defeat") else "piano",p,[0,1,2,3,4,3,2,1],.5,center=65,size=3,vel=.45)
    if name == "victory":
        percussion = s.track("fanfare",gain=.55,reverb=.25)
        percussion.note("crash",0,1,"C4",.55)
        for i in range(8):
            percussion.note("snare",6+i*.25,.25,"D3",.35+i*.03)
        percussion.note("timpani",12,1,"D2",.65)
    return s
