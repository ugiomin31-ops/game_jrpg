"""bgm_title — hopeful dawn: bell motif, piano arpeggios, flute theme, strings swell (D major, 84 bpm)."""
from abyss_audio.music import Song, prog

from . import motifs as M

ID = "bgm_title"
KIND = "bgm"


def build():
    s = Song(ID, bpm=84, bars=32, seed=11, reverb=(2.8, 0.03, 0.55), echo=(0.75, 0.3))
    bells = s.track("bells", gain=0.9, pan=0.15, reverb=0.5, delay=0.12, humanize=0.0)
    piano = s.track("piano", gain=0.9, pan=-0.1, reverb=0.32)
    pad = s.track("pad", gain=0.75, reverb=0.4)
    flute = s.track("flute", gain=0.95, pan=0.08, reverb=0.32, delay=0.1)
    vln = s.track("violins", gain=0.8, pan=-0.2, reverb=0.38)
    cello = s.track("cello", gain=0.75, pan=0.25, reverb=0.3)
    horn = s.track("horn", gain=0.7, pan=0.3, reverb=0.45)
    harp = s.track("harp", gain=0.7, pan=-0.35, reverb=0.4, humanize=0.0)
    bass = s.track("bass", gain=0.8, reverb=0.15)
    glock = s.track("glock", gain=0.45, pan=0.4, reverb=0.45, delay=0.15)
    perc = s.track("perc", gain=0.8, reverb=0.3, humanize=0.002)

    intro = prog("D Gmaj7 Bm7 Asus4:2 A:2", 4)
    theme = prog(M.THEME_CHORDS, 4)
    bridge = prog(M.BRIDGE_CHORDS, 4)
    outro = prog("G A G/B A7sus4:2 A7:2", 4)
    sections = [(0, intro, 0.35), (4, theme, 0.5), (12, theme, 0.62), (20, bridge, 0.8), (28, outro, 0.45)]

    arp = [0, 1, 2, 3, 4, 3, 2, 1]
    for bar, p, v in sections:
        o = s.bar(bar)
        pad.chords("string_pad", p, o, center=60, size=4, vel=v)
        if bar > 0:
            piano.arp("piano", p, arp, 0.5, o, center=62, size=4, vel=0.42 + v * 0.25, gate=1.6)
            piano.bass("piano", p, [(0, 2, 0, 1.0), (2, 2, 7, 0.7)], o, octave=2, vel=0.5)
        if bar >= 12:
            bass.bass("orch_bass", p, [(0, 4, 0, 1.0)], o, octave=2, vel=0.45 + v * 0.3)

    # Intro & outro: the dawn bells.
    bells.melody("bell", M.DAWN + " | " + M.DAWN_ANSWER, s.bar(0), vel=0.62)
    bells.melody("bell", M.DAWN + " | " + M.DAWN_LIFT, s.bar(28), vel=0.7)
    flute.melody("flute", "r/2 A5/1 B5/1 | A5/4", s.bar(30), vel=0.42)

    harp.arp("harp", prog("A:3", 3), list(range(12)), 0.25, s.bar(11) + 1, center=55, size=4, vel=0.55)
    flute.melody("flute", M.THEME, s.bar(4), vel=0.65)
    cello.melody("cello", M.THEME_COUNTER, s.bar(4), vel=0.38, transpose=-12)
    vln.melody("strings_legato", M.THEME_TO_B, s.bar(12), vel=0.62)
    flute.melody("flute", M.THEME_TO_B, s.bar(12), vel=0.5, transpose=12)
    cello.melody("cello", M.THEME_COUNTER, s.bar(12), vel=0.58, transpose=-12)
    harp.arp("harp", prog("A:4", 4), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], 0.25, s.bar(11),
             center=62, size=4, vel=0.55)

    harp.arp("harp", prog("A:3", 3), list(range(12)), 0.25, s.bar(19) + 1, center=57, size=4, vel=0.5)
    vln.melody("strings_legato", M.BRIDGE, s.bar(20), vel=0.8)
    flute.melody("flute", M.BRIDGE, s.bar(20), vel=0.55)
    glock.melody("glock", M.BRIDGE, s.bar(20), vel=0.5, transpose=12, legato=0.5)
    horn.melody("horn", M.BRIDGE_COUNTER, s.bar(20), vel=0.66)
    cello.melody("cello", M.BRIDGE_COUNTER, s.bar(20), vel=0.6, transpose=-12)
    harp.arp("harp", prog("G:4", 4), list(range(16)), 0.25, s.bar(19) + 0, center=60, size=4, vel=0.5)
    for i in range(16):
        perc.note("timpani", s.bar(19) + i * 0.25, 0.25, "A2", 0.25 + i * 0.035)
    perc.note("crash", s.bar(20), 1, "C4", 0.55)
    perc.note("swell_cymbal", s.bar(19) + 1.0, 3.0, "C4", 0.5)
    for bar in range(20, 28):
        root = {20: "G2", 21: "A2", 22: "F#2", 23: "B2", 24: "G2", 25: "A2", 26: "B2", 27: "A2"}[bar]
        perc.note("timpani", s.bar(bar), 1, root, 0.55)
        perc.note("timpani", s.bar(bar) + 2.5, 0.5, root, 0.35)
        perc.note("taiko", s.bar(bar), 1, "D2", 0.3)
    for i in range(8):
        perc.note("timpani", s.bar(27) + 2 + i * 0.25, 0.25, "A2", 0.3 + i * 0.05)
    perc.note("crash", s.bar(28), 1, "C4", 0.4)
    perc.note("swell_cymbal", s.bar(31), 4.0, "C4", 0.35)
    return s
