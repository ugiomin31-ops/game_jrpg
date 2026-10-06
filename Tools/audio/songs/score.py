"""Original 32-bar through-arranged area and combat cues. No sampled audio."""
from abyss_audio.music import Song, prog
from . import motifs as M

# Each theme is an independently written eight-bar phrase; B is a contrasting development.
SCORES = {
    "town": (106, "D G A D Bm Em7 G A", "G D/F# Em7 A Bm G E7 A",
        "F#5/1 A5/.5 F#5/.5 E5/1 D5/1 | B4/1 D5/1 G5/2 | E5/.5 F#5/.5 E5/1 C#5/1 A4/1 | D5/3 r/1 | F#5/1 B5/1 A5/1 F#5/1 | G5/1 E5/1 D5/1 B4/1 | D5/.5 E5/.5 G5/1 F#5/1 E5/1 | C#5/2 A4/2",
        "B5/1 A5/1 G5/2 | F#5/1 E5/1 D5/2 | E5/.5 F#5/.5 G5/1 B5/2 | A5/3 r/1 | F#5/1 B5/1 C#6/1 D6/1 | B5/1 G5/1 D5/2 | E5/1 G#5/1 B5/1 E6/1 | C#6/2 A5/2", "clarinet", "pizz", "guitar", "string_pad", "upright_bass"),
    "forest": (92, "Em7 Cmaj7 G D Em7 Am7 C B7", "Am7 D G C F#dim B7 Em B7",
        "E5/1 B5/.5 A5/.5 G5/2 | E5/1 G5/1 B5/2 | D6/1 B5/1 G5/1 A5/1 | F#5/3 r/1 | E5/1 G5/.5 F#5/.5 E5/2 | C5/1 E5/1 A5/2 | G5/1 E5/1 D5/1 C5/1 | D#5/2 F#5/2",
        "A5/1 C6/1 B5/1 A5/1 | F#5/1 A5/1 D6/2 | B5/1 D6/1 G6/2 | E6/1 D6/1 C6/2 | A5/1 F#5/1 C6/2 | B5/1 A5/1 F#5/1 D#5/1 | E5/1 G5/1 B5/1 E6/1 | F#5/3 r/1", "flute", "kalimba", "harp", "air_pad", "upright_bass"),
    "desert": (112, "Dm Bb A7 Dm Gm Dm Bb A7", "Gm C F Bb Gm Edim A7 A7",
        "D5/.5 Eb5/.5 F#5/1 A5/1 G5/1 | F5/1 D5/1 Bb4/2 | C#5/.5 D5/.5 E5/1 G5/1 A5/1 | F5/2 D5/2 | G5/1 A5/.5 Bb5/.5 D6/2 | A5/1 F5/1 E5/1 D5/1 | F5/.5 G5/.5 Bb5/1 A5/1 G5/1 | E5/1 C#5/1 A4/2",
        "Bb5/1 A5/1 G5/1 D5/1 | E5/.5 F5/.5 G5/1 C6/2 | A5/1 C6/1 F6/2 | D6/1 C6/1 Bb5/2 | G5/.5 A5/.5 Bb5/1 D6/1 Bb5/1 | G5/1 E5/1 Bb5/2 | A5/1 G5/1 E5/1 C#5/1 | E5/1 G5/1 A5/2", "ney", "oud", "qanun", "warm_pad", "orch_bass"),
    "frost": (76, "Bm Gmaj7 D A Bm Em7 G F#7", "Em7 A D G C#dim F#7 Bm F#7",
        "B5/2 F#5/1 A5/1 | G5/3 F#5/1 | E5/1 F#5/1 A5/2 | E5/3 r/1 | D5/1 F#5/1 B5/2 | G5/2 E5/2 | D5/1 B4/1 G4/2 | A#4/1 C#5/1 F#5/2",
        "G5/2 B5/2 | C#6/1 B5/1 A5/2 | F#5/1 A5/1 D6/2 | B5/2 G5/2 | E5/1 G5/1 C#6/2 | A#5/1 G#5/1 F#5/2 | D6/1 B5/1 F#5/2 | C#5/1 F#5/1 A#5/2", "glass_harmonica", "celesta", "harp", "glass_pad", "cello"),
    "abyss": (68, "Cm Abmaj7 Fm G7b9 Cm Db Ab G7", "Fm Db Cm G7 Ab Fm Ddim G7b9",
        "C5/2 G4/1 Db5/1 | C5/1 Eb5/1 G5/2 | Ab5/2 F5/2 | D5/1 Eb5/1 B4/2 | C5/1 G5/1 Eb5/2 | F5/1 Ab5/1 Db6/2 | C6/2 Ab5/2 | G5/1 F5/1 D5/1 B4/1",
        "F5/1 C6/1 Ab5/2 | Db6/1 C6/1 Ab5/2 | G5/1 Eb5/1 C5/2 | B4/2 D5/2 | Eb5/1 Ab5/1 C6/2 | C6/1 Ab5/1 F5/2 | Ab5/1 F5/1 D5/2 | B4/1 D5/1 G5/2", "choir", "piano", "bell", "dark_drone", "sub_drone"),
    "battle": (152, "Em C G D Em C Am B7", "Am D G C F#dim B7 Em B7",
        "E5/.5 G5/.5 B5/1 A5/.5 G5/.5 E5/1 | G5/.5 E5/.5 C5/1 E5/1 G5/1 | B5/1 D6/.5 B5/.5 A5/1 G5/1 | F#5/.5 A5/.5 D6/1 C6/1 A5/1 | B5/.5 E6/.5 D6/1 B5/1 G5/1 | E5/1 G5/.5 A5/.5 C6/2 | B5/1 A5/1 G5/1 E5/1 | F#5/.5 D#5/.5 B4/1 F#5/2",
        "A5/1 C6/1 E6/1 C6/1 | F#5/.5 A5/.5 D6/1 E6/1 F#6/1 | G6/1 D6/1 B5/2 | E6/1 D6/1 C6/2 | A5/.5 F#5/.5 C6/1 A5/1 F#5/1 | D#5/1 F#5/1 A5/1 B5/1 | G5/1 B5/1 E6/2 | D#6/.5 C6/.5 B5/1 F#5/2", "brass", "strings_stacc", "pulse_arp", "string_pad", "synth_bass"),
    "boss": (138, "Dm Bb Gm A7 Dm C Bb A7", "Gm Eb Bb F Gm Edim A7 A7",
        "D5/.5 A5/.5 D6/1 C6/1 A5/1 | Bb5/1 F5/1 D5/1 F5/1 | G5/.5 A5/.5 Bb5/1 D6/2 | C#6/1 A5/1 G5/1 E5/1 | F5/1 A5/1 D6/2 | E6/.5 D6/.5 C6/1 G5/2 | F5/1 Bb5/1 A5/1 G5/1 | E5/.5 C#5/.5 A4/1 A5/2",
        "Bb5/1 D6/1 G6/2 | Eb6/1 D6/1 Bb5/2 | F5/1 Bb5/1 D6/2 | C6/.5 A5/.5 F5/1 A5/2 | G5/1 Bb5/1 D6/1 G6/1 | E6/1 Bb5/1 G5/2 | C#6/1 E6/1 G6/2 | E6/.5 C#6/.5 A5/1 G5/1 E5/1", "strings_legato", "strings_stacc", "organ", "choir", "orch_bass"),
    "finalboss": (158, "Cm Ab Fm G7 Cm Bb Ab G7", "Fm Db Ab Eb Ddim G7 Cm G7b9",
        "C5/.5 G5/.5 C6/1 B5/.5 Ab5/.5 G5/1 | Eb5/1 Ab5/1 C6/2 | Ab5/.5 G5/.5 F5/1 C6/2 | B5/1 D6/1 G6/2 | Eb6/1 D6/1 C6/1 G5/1 | F5/1 Bb5/1 D6/2 | C6/.5 Ab5/.5 Eb5/1 C6/1 Ab5/1 | G5/1 F5/1 D5/1 B4/1",
        "F5/1 Ab5/1 C6/1 F6/1 | Db6/1 C6/1 Ab5/2 | C6/1 Eb6/1 Ab6/2 | G6/1 F6/1 Eb6/2 | D6/1 Ab5/1 F5/1 D5/1 | B5/.5 D6/.5 F6/1 G6/2 | Eb6/1 C6/1 G5/2 | B5/1 D6/1 G6/1 Ab6/1", "brass", "tremolo_strings", "organ", "choir", "synth_bass"),
    "ending": (88, M.THEME_CHORDS, M.BRIDGE_CHORDS, M.THEME_TO_B, M.BRIDGE,
        "strings_legato", "piano", "harp", "string_pad", "cello"),
}


def build(name):
    bpm, changes_a, changes_b, theme, bridge, lead_inst, rhythm_inst, color_inst, pad_inst, bass_inst = SCORES[name]
    combat = name in ("battle", "boss", "finalboss")
    s = Song("bgm_" + name, bpm, 32, seed=100 + list(SCORES).index(name),
             reverb=(3.2 if name in ("frost", "abyss") else 2.0, .025, .48), echo=(.75, .22))
    pad = s.track("harmony", gain=.55, reverb=.45, hp=100)
    rhythm = s.track("rhythm", gain=.6 if combat else .72, pan=-.25, reverb=.2)
    color = s.track("color", gain=.48, pan=.32, reverb=.35, delay=.12)
    bass = s.track("bass", gain=.85, reverb=.12)
    lead = s.track("lead", gain=.85, pan=.08, reverb=.28, delay=.06)
    counter = s.track("counter", gain=.4, pan=-.2, reverb=.3)
    perc = s.track("percussion", gain=.8 if combat else .4, reverb=.2, humanize=.002)
    for section, (changes, strength) in enumerate(((changes_a,.62),(changes_a,.75),(changes_b,.85),(changes_a,.7))):
        offset = s.bar(section * 8)
        p = prog(changes, 4)
        pad.chords(pad_inst, p, offset, center=57 if name == "abyss" else 62, size=3, vel=strength*.7)
        rhythm.arp(rhythm_inst, p, [0,2,1,3,2,1,3,1] if combat else [0,1,2,3,2,1,0,2],
                   .25 if combat else .5, offset, center=60, size=3, vel=strength*.7, gate=.65 if combat else 1.1)
        bass.bass(bass_inst, p, [(0,1.5,0,1),(2,.75,7,.7),(3,1,0,.8)] if combat else [(0,2,0,1),(2,2,7,.65)],
                  offset, octave=2, vel=strength*.8)
        lead.melody(lead_inst, bridge if section == 2 else theme, offset, vel=strength)
        if section in (1,2):
            color.arp(color_inst, p, [3,4,5,4,3,2,1,2], .5, offset, center=66, size=3, vel=.4, gate=.85)
            counter.chords("horn" if combat else "cello", p, offset, center=53, size=2, vel=.38,
                           rhythm=[(1,1),(3,1)] if combat else [(0,4)])
        if combat:
            perc.drums({"k":("kick","C2"),"s":("snare","D3"),"h":("hat","C5"),"t":("taiko","D2")},
                       {"k":"X.....x.X.x.....", "s":"....X.......X...", "h":"x.x.x.x.x.x.x.x.",
                        "t":"X.......x......."}, offset, bars=8, vel=.75)
            perc.note("crash", offset, 1, "C4", .45)
            for i in range(8):
                perc.note("tom", offset + 30 + i*.25, .25, 50-i*2, .4+i*.035)
        elif name == "desert":
            perc.drums({"d":("doum","D3"),"t":("tek","D4"),"r":("riq","C5")},
                       {"d":"X.....x.........","t":"....x....xx.x...","r":"x...x...x...x..."}, offset, bars=8, vel=.62)
        elif name in ("town","forest"):
            perc.drums({"f":("frame_drum","D3"),"s":("shaker","C5")},
                       {"f":"X.......x.......", "s":"x.x.x.x.x.x.x.x."}, offset, bars=8, vel=.48)
        elif name == "frost":
            for b in range(8):
                perc.note("sleigh", offset+b*4+3, .5, "C5", .25)
        elif name == "abyss":
            for b in range(8):
                perc.note("heartbeat", offset+b*4, 1, "C2", .42)
        else:
            perc.note("swell_cymbal", offset+28, 4, "C4", .35)
            perc.note("timpani", offset, 2, "D2", .4)
    if name == "ending":
        color.melody("bell", M.DAWN, s.bar(28), vel=.65)
        lead.melody("flute", M.THEME_COUNTER, s.bar(16), vel=.4, transpose=12)
    return s
