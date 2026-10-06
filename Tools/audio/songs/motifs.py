"""Shared themes. The 'dawn bell' motif ties the title, area jingle and ending together."""

# Dawn bell motif in D major: rising fifth, stepwise fall, resolving to the tonic (2 bars of 4/4).
DAWN = "D5/1 A5/1 G5/1 F#5/1 | E5/1.5 F#5/.5 D5/2"
DAWN_ANSWER = "D5/1 A5/1 B5/1 F#5/1 | E5/4"
DAWN_LIFT = "D5/1 A5/1 G5/1 F#5/1 | E5/1.5 G5/.5 A5/2"

# Title main theme (8 bars, D major) over THEME_CHORDS.
THEME_CHORDS = "D A/C# Bm G D/F# G Em7 A"
THEME = ("A4/1 D5/1 F#5/1.5 E5/.5 | E5/1 A5/1 G5/1 F#5/1 | F#5/1.5 E5/.5 D5/1 B4/1 | D5/3 E5/1 | "
         "F#5/1 A5/1 D6/1.5 C#6/.5 | B5/1 A5/1 G5/1 B5/1 | A5/1.5 G5/.5 F#5/1 E5/1 | E5/3 r/1")
THEME_TO_B = ("A4/1 D5/1 F#5/1.5 E5/.5 | E5/1 A5/1 G5/1 F#5/1 | F#5/1.5 E5/.5 D5/1 B4/1 | D5/3 E5/1 | "
              "F#5/1 A5/1 D6/1.5 C#6/.5 | B5/1 A5/1 G5/1 B5/1 | A5/1.5 G5/.5 F#5/1 E5/1 | E5/2 F#5/1 G5/1")
THEME_COUNTER = "F#4/2 A4/2 | E4/2 C#4/2 | D4/2 F#4/2 | G4/2 B4/1 A4/1 | A4/4 | B4/2 D5/2 | B4/2 G4/2 | A4/2 C#5/2"

# Bridge (8 bars) over BRIDGE_CHORDS.
BRIDGE_CHORDS = "G A F#m Bm G A Bm Asus4:2 A:2"
BRIDGE = ("B5/1.5 A5/.5 G5/1 D5/1 | C#5/1 E5/1 A5/2 | A5/1 C#6/1 B5/1 A5/1 | F#5/3 D5/1 | "
          "G5/1.5 F#5/.5 E5/1 D5/1 | E5/1 F#5/1 G5/1 A5/1 | B5/1.5 A5/.5 F#5/2 | E5/4")
BRIDGE_COUNTER = "D4/4 | E4/4 | F#4/2 A4/2 | B4/2 F#4/2 | G4/2 B4/2 | C#5/2 A4/2 | D5/2 B4/2 | A4/2 C#5/2"
