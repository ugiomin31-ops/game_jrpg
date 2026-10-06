"""Music theory helpers and the Song sequencer/mixer.

Notation
--------
Pitches: ``"C4"``, ``"F#5"``, ``"Bb3"`` (C4 = MIDI 60) or MIDI ints.
Melodies (``seq``): whitespace-separated ``PITCH/BEATS`` tokens; ``r/BEATS`` is a rest,
``-/BEATS`` extends the previous note, ``|`` is ignored (bar marker), a trailing ``!`` accents.
Chords: ``"Am"``, ``"F#m7"``, ``"Bbmaj7"``, ``"Dsus4"``, ``"G7"``, ``"C/E"``, ``"Bdim"``, ``"Eadd9"``, ...
Drum patterns: one char per step, ``X`` accent, ``x`` normal, ``o`` ghost, ``.`` rest.
"""
import re

import numpy as np

from . import dsp
from .dsp import SR
from .instruments import INSTRUMENTS

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note(name):
    """MIDI number of a pitch name (or passthrough for ints)."""
    if isinstance(name, (int, np.integer)):
        return int(name)
    m = re.fullmatch(r"([A-Ga-g])([#b]*)(-?\d)", name.strip())
    if not m:
        raise ValueError(f"bad note {name!r}")
    pc = _PC[m.group(1).upper()] + m.group(2).count("#") - m.group(2).count("b")
    return pc + 12 * (int(m.group(3)) + 1)


_QUALITIES = {
    "": (0, 4, 7), "m": (0, 3, 7), "dim": (0, 3, 6), "aug": (0, 4, 8), "sus4": (0, 5, 7), "sus2": (0, 2, 7),
    "7": (0, 4, 7, 10), "maj7": (0, 4, 7, 11), "m7": (0, 3, 7, 10), "m7b5": (0, 3, 6, 10), "dim7": (0, 3, 6, 9),
    "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9), "add9": (0, 4, 7, 14), "madd9": (0, 3, 7, 14), "9": (0, 4, 7, 10, 14),
    "m9": (0, 3, 7, 10, 14), "maj9": (0, 4, 7, 11, 14), "7sus4": (0, 5, 7, 10), "7b9": (0, 4, 7, 10, 13),
    "5": (0, 7), "mmaj7": (0, 3, 7, 11),
}


def chord(sym):
    """Parse a chord symbol -> (root_pc, intervals, bass_pc)."""
    m = re.fullmatch(r"([A-G][#b]?)([^/]*)(?:/([A-G][#b]?))?", sym.strip())
    if not m:
        raise ValueError(f"bad chord {sym!r}")
    root = note(m.group(1) + "0") % 12
    ivs = _QUALITIES[m.group(2)]
    bass = note(m.group(3) + "0") % 12 if m.group(3) else root
    return root, ivs, bass


def voicing(sym, center=64, size=4, prev=None):
    """Close-position voicing of `size` notes near `center`; with `prev`, picks the inversion with least motion."""
    root, ivs, _ = chord(sym)
    pcs = sorted({(root + i) % 12 for i in ivs})
    best, best_cost = None, 1e9
    for low in range(center - 13, center + 1):
        if low % 12 not in pcs:
            continue
        notes = [low]
        while len(notes) < size:
            m = notes[-1] + 1
            while m % 12 not in pcs:
                m += 1
            notes.append(m)
        cost = abs(np.mean(notes) - center) * 0.6
        if prev is not None:
            cost += sum(min(abs(a - b) for b in prev) for a in notes) * 0.5
        if cost < best_cost:
            best, best_cost = notes, cost
    return best


def bass_note(sym, octave=2):
    _, _, bass = chord(sym)
    return bass + 12 * (octave + 1)


def root_note(sym, octave=2):
    root, _, _ = chord(sym)
    return root + 12 * (octave + 1)


def seq(text, start=0.0):
    """Parse melody text -> list of (beat, dur, midi|None, accent)."""
    out = []
    b = start
    for tok in text.split():
        if tok == "|":
            continue
        acc = tok.endswith("!")
        tok = tok.rstrip("!")
        p, d = tok.split("/")
        d = float(d)
        if p == "-":
            if out:
                bb, dd, pp, aa = out[-1]
                out[-1] = (bb, dd + d, pp, aa)
        elif p == "r":
            pass
        else:
            out.append((b, d, note(p), acc))
        b += d
    return out


def seq_len(text):
    return sum(float(t.rstrip("!").split("/")[1]) for t in text.split() if t != "|")


def prog(text, beats_per_chord):
    """'Am F C G' -> [(beat, dur, sym)]. Tokens may carry ':beats' to override duration."""
    out = []
    b = 0.0
    for tok in text.split():
        if tok == "|":
            continue
        if ":" in tok:
            s, d = tok.split(":")
            d = float(d)
        else:
            s, d = tok, beats_per_chord
        out.append((b, d, s))
        b += d
    return out


# --------------------------------------------------------------------------- sequencer


class Track:
    """A mixer channel: renders notes of one or more instruments into a stereo buffer."""

    def __init__(self, song, name, gain=1.0, pan=0.0, reverb=0.2, delay=0.0, hp=0.0, lp=0.0, width=1.0,
                 humanize=0.006, vel_jitter=0.05, chorus=0.0):
        self.song = song
        self.name = name
        self.gain = gain
        self.pan = pan
        self.reverb = reverb
        self.delay = delay
        self.hp = hp
        self.lp = lp
        self.width = width
        self.humanize = humanize
        self.vel_jitter = vel_jitter
        self.chorus = chorus
        self.buf = np.zeros((song.n, 2))

    def note(self, inst, beat, dur, pitch, vel=0.8, pan=None, **kw):
        """Render one note. `pitch` may be MIDI/name; beats/dur in song beats."""
        s = self.song
        midi = note(pitch) if isinstance(pitch, str) else pitch
        f = float(dsp.mtof(midi))
        v = float(np.clip(vel + s.rng.uniform(-self.vel_jitter, self.vel_jitter), 0.05, 1.0))
        v = round(v * 20) / 20
        secs = dur * s.spb
        audio = s.render(inst, f, round(secs, 3), v, **kw)
        jitter = s.rng.normal(0, self.humanize) if self.humanize else 0.0
        start = int(round((beat * s.spb + jitter) * SR))
        p = self.pan if pan is None else pan
        if audio.ndim == 1:
            audio = dsp.pan(audio, p)
        elif p:
            audio = dsp.balance(audio, p)
        dsp.mix_into(self.buf, audio, max(start, 0))

    def play(self, inst, events, offset=0.0, vel=0.8, transpose=0, legato=1.0, accent=0.15, **kw):
        """Render a parsed `seq` event list starting at beat `offset`."""
        for b, d, m, acc in events:
            self.note(inst, offset + b, d * legato, m + transpose, min(1.0, vel + (accent if acc else 0.0)), **kw)

    def melody(self, inst, text, offset=0.0, **kw):
        self.play(inst, seq(text), offset, **kw)

    def chords(self, inst, progression, offset=0.0, center=62, size=4, vel=0.6, legato=1.0, rhythm=None, **kw):
        """Sustain (or rhythmically re-strike) voiced chords. rhythm = list of (beat_in_chord, dur)."""
        prev = None
        for b, d, sym in progression:
            v = voicing(sym, center, size, prev)
            prev = v
            hits = rhythm if rhythm is not None else [(0.0, d)]
            for hb, hd in hits:
                if hb >= d:
                    continue
                for m in v:
                    self.note(inst, offset + b + hb, min(hd, d - hb) * legato, m, vel, **kw)

    def arp(self, inst, progression, pattern, step=0.5, offset=0.0, center=64, size=4, vel=0.6, gate=0.9,
            accents=None, **kw):
        """Arpeggiate chords; pattern indexes the voicing (wrapping by octave)."""
        prev = None
        for b, d, sym in progression:
            v = voicing(sym, center, size, prev)
            prev = v
            steps = int(round(d / step))
            for i in range(steps):
                idx = pattern[i % len(pattern)]
                if idx is None:
                    continue
                o, k = divmod(idx, len(v))
                m = v[k] + 12 * o
                a = accents[i % len(accents)] if accents else 1.0
                self.note(inst, offset + b + i * step, step * gate, m, vel * a, **kw)

    def bass(self, inst, progression, pattern, offset=0.0, octave=2, vel=0.8, **kw):
        """Bass line from chord bass notes. pattern: list of (beat, dur, interval_semitones, vel_mult)."""
        for b, d, sym in progression:
            base = bass_note(sym, octave)
            root = root_note(sym, octave)
            for pb, pd, iv, vm in pattern:
                if pb >= d:
                    continue
                m = (base if iv == 0 else root + iv)
                self.note(inst, offset + b + pb, min(pd, d - pb), m, vel * vm, **kw)

    def drums(self, kit, patterns, offset=0.0, bars=1, step=0.25, vel=0.8, beats_per_bar=None):
        """kit: {key: (inst, pitch)}; patterns: {key: 'x..x....'} (one char per step, repeated per bar)."""
        bpb = beats_per_bar or self.song.meter
        levels = {"X": 1.0, "x": 0.78, "o": 0.42}
        for bar in range(bars):
            for key, pat in patterns.items():
                inst, pitch = kit[key]
                for i, ch in enumerate(pat.replace(" ", "")):
                    if ch in levels:
                        beat = offset + bar * bpb + i * step
                        self.note(inst, beat, step, pitch, vel * levels[ch])


class Song:
    """Multi-track arrangement rendered to a stereo buffer; loops are wrapped seamlessly.

    The arrangement is rendered `tail` seconds past the loop end; every sample past the loop
    end (ringing notes, reverb/echo tails) is folded back onto the head, so the loop seam is
    exactly continuous.
    """

    def __init__(self, name, bpm, bars, meter=4, seed=1, tail=10.0, loop=True,
                 reverb=(2.2, 0.02, 0.5), echo=None, length_beats=None):
        self.name = name
        self.bpm = bpm
        self.meter = meter
        self.spb = 60.0 / bpm
        self.loop = loop
        beats = length_beats if length_beats is not None else bars * meter
        self.beats = beats
        self.loop_len = int(round(beats * self.spb * SR))
        self.n = self.loop_len + dsp.ns(tail)
        self.rng = np.random.default_rng(seed)
        self.tracks = {}
        self.reverb_cfg = reverb
        self.echo_cfg = echo  # (beats, feedback)
        self._cache = {}

    def bar(self, i):
        """Beat at which (0-based) bar i starts."""
        return i * self.meter

    def track(self, name, **kw):
        t = Track(self, name, **kw)
        self.tracks[name] = t
        return t

    def render(self, inst, f, secs, vel, **kw):
        """Render (cached) one instrument note; up to three round-robin variants per identical note."""
        variant = int(self.rng.integers(0, 3))
        key = (inst, round(f, 3), secs, vel, variant, tuple(sorted(kw.items())))
        a = self._cache.get(key)
        if a is None:
            fn = INSTRUMENTS[inst]
            a = fn(f, secs, vel, dsp.seeded_rng(self.name, *key[:5]), **kw)
            self._cache[key] = a
        return a

    def mixdown(self):
        """Sum tracks through sends/returns -> stereo float buffer (loop length if looping)."""
        dry = np.zeros((self.n, 2))
        rev_send = np.zeros((self.n, 2))
        echo_send = np.zeros((self.n, 2))
        for t in self.tracks.values():
            x = t.buf
            if t.hp:
                x = dsp.hp(x, t.hp, 2)
            if t.lp:
                x = dsp.lp(x, t.lp, 2)
            if t.chorus:
                x = dsp.chorus(x, mix=t.chorus)
            if t.width != 1.0:
                x = dsp.width(x, t.width)
            x = x * t.gain
            dry += x
            if t.reverb:
                rev_send += x * t.reverb
            if t.delay:
                echo_send += x * t.delay
        out = dry
        if self.echo_cfg and np.any(echo_send):
            beats, fb = self.echo_cfg
            e = dsp.echo(echo_send, beats * self.spb, fb)
            out = out + e
            rev_send += e * 0.3
        if np.any(rev_send):
            t60, pre, bright = self.reverb_cfg
            ir = dsp.make_ir(t60, pre, bright)
            rev = dsp.convolve(dsp.hp(rev_send, 180, 2), ir, self.n)
            out = out + rev
        out = dsp.hp(out, 28, 2)
        if self.loop:
            body = out[:self.loop_len].copy()
            tail = out[self.loop_len:]
            k = min(len(tail), self.loop_len)
            body[:k] += tail[:k]
            return body
        return out
