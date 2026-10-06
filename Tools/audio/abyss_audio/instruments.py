"""Synthesised instruments.

Every instrument has the signature ``fn(f, dur, vel, rng, **kw) -> np.ndarray`` where
f is the fundamental in Hz, dur the gate length in seconds, vel 0..1 and rng a numpy Generator.
The returned buffer (mono 1-D or stereo (n,2)) includes the instrument's natural release tail.
"""
import numpy as np

from .dsp import (SR, adsr, additive, biquad, bp, chorus, fit, hp, karplus, lp, noise, ns, pan, peak, perc,
                  resonator, saw, shelf_hi, shelf_lo, sine, soft_clip, square, sweep, triangle, tvec, vibrato)

# --------------------------------------------------------------------------- keyboard / mallets


def piano(f, dur, vel, rng, bright=0.5):
    """Grand-piano style additive voice: inharmonic partials, string-pair beating, hammer, damper."""
    natural = float(np.clip(7.0 * (262.0 / f) ** 0.55, 1.2, 14.0))
    n = ns(min(dur, natural) + 0.35)
    t = tvec(n)
    B = 0.00025 * (f / 262.0) ** 0.6
    nparts = int(min(28, 9000 / f))
    out = np.zeros(n)
    tone = 0.18 + 0.3 * vel + 0.2 * bright
    for k in range(1, nparts + 1):
        fk = k * f * np.sqrt(1 + B * k * k)
        amp = k ** -1.15 * np.exp(-(k - 1) * (0.42 - tone * 0.45))
        t60 = natural / (1 + 0.38 * (k - 1))
        dec = 0.75 * np.exp(-t / (t60 * 0.18) * 6.9) + 0.25 * np.exp(-t / t60 * 6.9)
        ph = rng.uniform(0, 2 * np.pi)
        det = 1 + rng.uniform(0.0002, 0.0009)
        out += amp * dec * (np.sin(2 * np.pi * fk * t + ph) + 0.8 * np.sin(2 * np.pi * fk * det * t + ph * 1.3))
    ham = lp(noise(ns(0.02), rng), 1200 + 2500 * vel) * np.linspace(1, 0, ns(0.02)) ** 2
    out[:len(ham)] += ham * 0.25
    na = ns(0.002)
    out[:na] *= np.linspace(0, 1, na)
    damp_start = ns(min(dur, natural))
    damp = np.ones(n)
    tail = n - damp_start
    if tail > 0:
        damp[damp_start:] = np.exp(-tvec(tail) / 0.25 * 6.9)
    out *= damp
    out = shelf_lo(out, 180, 2.0)
    return out * (0.25 + 0.75 * vel) * 0.32


def bell(f, dur, vel, rng, length=6.0):
    """Tuned bell (clear pitch, warm hum, shimmering upper partials)."""
    n = ns(length * float(np.clip((523.0 / f) ** 0.35, 0.6, 1.8)))
    ratios = [0.5, 1.0, 2.0, 2.39, 3.0, 4.07, 5.43, 6.8, 8.21]
    amps = [0.22, 1.0, 0.5, 0.32, 0.22, 0.18, 0.11, 0.07, 0.04]
    t60s = [9.0, 6.0, 3.6, 2.8, 2.2, 1.6, 1.1, 0.8, 0.55]
    sc = float(np.clip((523.0 / f) ** 0.35, 0.5, 1.8)) * length / 6.0
    freqs, a2, d2 = [], [], []
    for r, a, d in zip(ratios, amps, t60s):
        for det in (1.0, 1.0 + rng.uniform(0.0004, 0.0012)):
            freqs.append(f * r * det)
            a2.append(a * 0.5)
            d2.append(d * sc)
    out = additive(freqs, a2, d2, n, rng, attack=0.001)
    strike = hp(noise(ns(0.012), rng), 3000) * np.linspace(1, 0, ns(0.012)) ** 3
    out[:len(strike)] += strike * 0.15 * vel
    return out * (0.3 + 0.7 * vel) * 0.35


def celesta(f, dur, vel, rng):
    n = ns(2.6 * float(np.clip((800.0 / f) ** 0.4, 0.5, 1.6)) + 0.1)
    s = float(np.clip((800.0 / f) ** 0.4, 0.5, 1.6))
    out = additive([f, 2 * f, 3.01 * f, 4.1 * f, 6.2 * f], [1.0, 0.22, 0.07, 0.1, 0.03],
                   [2.4 * s, 0.7 * s, 0.35, 0.18, 0.08], n, rng, attack=0.0015)
    click = hp(noise(ns(0.004), rng), 5000) * np.linspace(1, 0, ns(0.004))
    out[:len(click)] += click * 0.08
    return out * (0.3 + 0.7 * vel) * 0.42


def music_box(f, dur, vel, rng):
    """Comb-tine music box: bright plucked tine with inharmonic overtones."""
    s = float(np.clip((1000.0 / f) ** 0.5, 0.5, 1.8))
    n = ns(2.4 * s)
    out = additive([f, f * 1.0015, 5.93 * f, 13.4 * f, 2.0 * f], [1.0, 0.5, 0.28, 0.08, 0.06],
                   [2.2 * s, 2.0 * s, 0.35 * s, 0.09, 0.6 * s], n, rng, attack=0.0008)
    click = bp(noise(ns(0.003), rng), 3000, 12000) * np.linspace(1, 0, ns(0.003))
    out[:len(click)] += click * 0.25
    return out * (0.3 + 0.7 * vel) * 0.36


def kalimba(f, dur, vel, rng):
    s = float(np.clip((600.0 / f) ** 0.5, 0.5, 1.8))
    n = ns(1.8 * s)
    out = additive([f, 6.27 * f, 2.0 * f, 17.5 * f], [1.0, 0.18, 0.05, 0.03],
                   [1.6 * s, 0.12, 0.4, 0.04], n, rng, attack=0.001)
    thump = lp(noise(ns(0.01), rng), 900) * np.linspace(1, 0, ns(0.01)) ** 2
    out[:len(thump)] += thump * 0.3
    out = peak(out, f * 1.0, 3.0, 2.0)
    return out * (0.3 + 0.7 * vel) * 0.42


def marimba(f, dur, vel, rng):
    s = float(np.clip((400.0 / f) ** 0.5, 0.4, 2.0))
    n = ns(1.3 * s)
    out = additive([f, 3.93 * f, 9.2 * f, 2.0 * f], [1.0, 0.16 + 0.12 * vel, 0.04, 0.03],
                   [1.0 * s, 0.18 * s, 0.05, 0.3], n, rng, attack=0.0015)
    mallet = lp(noise(ns(0.008), rng), 2000) * np.linspace(1, 0, ns(0.008)) ** 2
    out[:len(mallet)] += mallet * 0.2
    return out * (0.3 + 0.7 * vel) * 0.45


def glock(f, dur, vel, rng):
    n = ns(2.5)
    out = additive([f, 2.76 * f, 5.40 * f, 8.93 * f], [1.0, 0.25, 0.12, 0.05],
                   [2.4, 0.9, 0.35, 0.15], n, rng, attack=0.0008)
    return out * (0.3 + 0.7 * vel) * 0.3


def glass_harmonica(f, dur, vel, rng):
    """Bowed glass: pure, slightly beating tone with slow swell (eerie / crystalline)."""
    n = ns(dur + 1.2)
    t = tvec(n)
    env = adsr(dur, 0.35, 0.4, 0.85, 1.2)[:n]
    fr = vibrato(f, n, 4.2, 6, 0.0, 0.5, rng)
    out = sine(fr, n) + 0.22 * sine(fr * 2.0, n) + 0.05 * sine(fr * 3.0, n)
    out += 0.7 * sine(fr * 1.0025, n, rng.uniform())
    out *= 1.0 + 0.12 * np.sin(2 * np.pi * 5.2 * t)
    return out * env * (0.3 + 0.7 * vel) * 0.22


# --------------------------------------------------------------------------- plucked strings


def _pluck(f, dur, vel, rng, bright, t60, pick, damp_t, body=(), lp_hz=8000.0, mute=True):
    nat = min(dur + damp_t, t60 * 1.1) if mute else t60 * 1.1
    n = ns(nat + 0.05)
    g = 10 ** (-3.0 / (t60 * f))
    y = karplus(f, n, rng, bright=bright * (0.55 + 0.45 * vel), decay=float(np.clip(g, 0.9, 0.99995)), pick=pick)
    for fc, gain, q in body:
        y = peak(y, fc, gain, q)
    y = lp(y, lp_hz, 2)
    if mute and dur + damp_t < t60 * 1.1:
        k = ns(dur)
        if k < n:
            y[k:] *= np.exp(-tvec(n - k) / damp_t * 6.9)
    y = y / (np.max(np.abs(y[:ns(0.05)])) + 1e-9)
    return y * (0.3 + 0.7 * vel)


def guitar(f, dur, vel, rng):
    """Nylon-string guitar."""
    return _pluck(f, dur, vel, rng, 0.35, 3.2 * (196 / f) ** 0.3, 0.27, 0.18,
                  body=((105, 4.0, 1.5), (230, 3.0, 2.0), (2800, -3.0, 1.0)), lp_hz=6000) * 0.42


def harp(f, dur, vel, rng):
    return _pluck(f, dur, vel, rng, 0.5, 4.5 * (262 / f) ** 0.4, 0.45, 1.5,
                  body=((180, 2.0, 1.0),), lp_hz=9000, mute=False) * 0.38


def oud(f, dur, vel, rng):
    """Fretless lute: bright plectrum attack, quick decay, a little buzz."""
    y = _pluck(f, dur, vel, rng, 0.85, 1.4 * (147 / f) ** 0.3, 0.18, 0.12,
               body=((140, 4.0, 1.2), (1100, 3.0, 1.5), (3000, 2.0, 2.0)), lp_hz=7000)
    y = soft_clip(y * 1.6, 1.2)
    pickn = hp(noise(ns(0.006), rng), 2500) * np.linspace(1, 0, ns(0.006))
    y[:len(pickn)] += pickn * 0.35 * vel
    return y * 0.38


def qanun(f, dur, vel, rng):
    return _pluck(f, dur, vel, rng, 0.75, 2.4 * (262 / f) ** 0.35, 0.12, 0.6,
                  body=((900, 2.0, 1.0), (4000, 2.0, 1.5)), lp_hz=10000, mute=False) * 0.32


def pizz(f, dur, vel, rng):
    return _pluck(f, min(dur, 0.25), vel, rng, 0.28, 0.6 * (196 / f) ** 0.2, 0.4, 0.1,
                  body=((280, 4.0, 1.2), (1200, 2.0, 1.0)), lp_hz=4000) * 0.45


def upright_bass(f, dur, vel, rng):
    y = _pluck(f, dur, vel, rng, 0.22, 2.2, 0.35, 0.12, body=((90, 3.0, 1.0), (700, 2.0, 1.5)), lp_hz=1800)
    n = len(y)
    sub = sine(f, n) * np.exp(-tvec(n) / 1.6 * 6.9) * 0.35
    k = ns(dur)
    if k < n:
        sub[k:] *= np.exp(-tvec(n - k) / 0.12 * 6.9)
    return (y + sub) * 0.55


# --------------------------------------------------------------------------- bowed / sustained


def _saw_stack(f, n, rng, voices, spread_cents, vib_rate=5.0, vib_cents=8.0, vib_delay=0.3):
    outL = np.zeros(n)
    outR = np.zeros(n)
    for i in range(voices):
        c = (i / max(voices - 1, 1) - 0.5) * 2 * spread_cents if voices > 1 else 0.0
        c += rng.uniform(-1.5, 1.5)
        fr = vibrato(f * 2 ** (c / 1200), n, vib_rate * rng.uniform(0.9, 1.1), vib_cents, vib_delay, 0.5, rng)
        v = saw(fr, n, rng.uniform())
        p = (i / max(voices - 1, 1) - 0.5) * 1.4 if voices > 1 else 0.0
        a = (p + 1) * np.pi / 4
        outL += v * np.cos(a)
        outR += v * np.sin(a)
    return np.stack([outL, outR], axis=1) / np.sqrt(voices)


def string_pad(f, dur, vel, rng, attack=0.45, release=1.0, cutoff=None):
    """Lush string ensemble pad (stereo)."""
    n = ns(dur + release)
    x = _saw_stack(f, n, rng, 6, 14, 5.2, 6, 0.4)
    fc = cutoff or (900 + 2600 * vel) * min(1.0, (f / 300) ** 0.25)
    x = lp(x, fc, 2)
    x = hp(x, 90, 1)
    x = peak(x, 2400, 2.0, 1.0)
    env = adsr(dur, attack, 0.5, 0.9, release)[:n]
    return x * env[:, None] * (0.35 + 0.65 * vel) * 0.32


def strings_legato(f, dur, vel, rng, attack=0.12):
    """Violin section for melodies (stereo)."""
    n = ns(dur + 0.45)
    x = _saw_stack(f, n, rng, 4, 7, 5.6, 14, 0.18)
    x = peak(x, 480, 3.0, 1.2)
    x = peak(x, 2600, 4.0, 1.4)
    x = peak(x, 1200, -2.0, 1.0)
    x = lp(x, 5500 + 2000 * vel, 2)
    x = hp(x, 160, 1)
    env = adsr(dur, attack, 0.3, 0.92, 0.4)[:n]
    return x * env[:, None] * (0.35 + 0.65 * vel) * 0.33


def strings_stacc(f, dur, vel, rng):
    """Spiccato string ensemble (stereo) for ostinatos."""
    gate = min(dur, 0.16)
    n = ns(gate + 0.14)
    x = _saw_stack(f, n, rng, 3, 9, 5.0, 0.0, 1.0)
    x = lp(x, 2600 + 3000 * vel, 2)
    x = peak(x, 500, 3.0, 1.0)
    x = hp(x, 120, 1)
    env = adsr(gate, 0.006, 0.07, 0.35, 0.12)[:n]
    bow = bp(noise(n, rng), 2000, 7000) * np.exp(-tvec(n) / 0.03)
    x = x + (bow * 0.15)[:, None]
    return x * env[:, None] * (0.35 + 0.65 * vel) * 0.42


def tremolo_strings(f, dur, vel, rng, rate=11.0):
    x = string_pad(f, dur, vel, rng, attack=0.2, release=0.6)
    t = tvec(len(x))
    am = 0.55 + 0.45 * np.abs(np.sin(np.pi * rate * t + rng.uniform(0, 3)))
    return x * am[:, None] * 1.2


def violin(f, dur, vel, rng):
    """Expressive solo violin-like lead."""
    n = ns(dur + 0.35)
    fr = vibrato(f, n, 6.0, 22, 0.15, 0.35, rng)
    x = saw(fr, n, rng.uniform()) * 0.85 + square(fr, n, 0.3) * 0.15
    x = peak(x, 300, 4.0, 1.5)
    x = peak(x, 1000, 3.0, 2.0)
    x = peak(x, 2800, 5.0, 2.0)
    x = peak(x, 4500, 3.0, 2.0)
    x = lp(x, 7000, 2)
    x = hp(x, 180, 1)
    x += bp(noise(n, rng), 2500, 8000) * 0.04
    env = adsr(dur, 0.05, 0.2, 0.9, 0.3)[:n]
    return x * env * (0.35 + 0.65 * vel) * 0.3


def cello(f, dur, vel, rng):
    n = ns(dur + 0.5)
    x = _saw_stack(f, n, rng, 3, 6, 5.0, 10, 0.25)
    x = peak(x, 250, 3.0, 1.0)
    x = peak(x, 1500, 2.0, 1.5)
    x = lp(x, 2200 + 1500 * vel, 2)
    env = adsr(dur, 0.14, 0.3, 0.9, 0.45)[:n]
    return x * env[:, None] * (0.35 + 0.65 * vel) * 0.38


def brass(f, dur, vel, rng, soft=0.0):
    """Brass section voice with filter-envelope 'blat' and pitch scoop. soft 0..1 -> horn-like."""
    n = ns(dur + 0.3)
    t = tvec(n)
    scoop = 2 ** (-45 * np.exp(-t / 0.03) / 1200)
    fr = vibrato(f, n, 5.2, 9, 0.35, 0.4, rng) * scoop
    x = saw(fr, n, rng.uniform()) + saw(fr * 1.003, n, rng.uniform()) * 0.8 + square(fr * 0.998, n, 0.45) * 0.25
    fe = adsr(dur, 0.05 + 0.04 * soft, 0.35, 0.55, 0.25)[:n]
    fc = f * (1.2 + (2.0 + 5.0 * vel) * (1 - 0.6 * soft) * fe) + 200
    x = sweep(x, "lp", np.clip(fc, 80, 16000), 0.9)
    x = soft_clip(x * 0.8, 1.5)
    x = peak(x, 1200, 2.0 - 4 * soft, 1.0)
    env = adsr(dur, 0.035 + 0.05 * soft, 0.25, 0.8, 0.2)[:n]
    return x * env * (0.35 + 0.65 * vel) * 0.36


def horn(f, dur, vel, rng):
    return brass(f, dur, vel, rng, soft=0.85)


def choir(f, dur, vel, rng, vowel="ah", attack=0.35, release=0.9, voices=5):
    """Formant-filtered vocal ensemble (stereo)."""
    formants = {
        "ah": ((750, 1.0, 90), (1150, 0.55, 110), (2600, 0.3, 160), (3400, 0.15, 220)),
        "oo": ((330, 1.0, 70), (700, 0.35, 90), (2400, 0.1, 160), (3200, 0.05, 200)),
        "oh": ((480, 1.0, 80), (850, 0.5, 100), (2600, 0.18, 160), (3300, 0.08, 200)),
        "eh": ((550, 1.0, 80), (1750, 0.45, 120), (2600, 0.25, 160), (3500, 0.12, 220)),
        "mm": ((260, 1.0, 60), (1900, 0.04, 200), (2700, 0.02, 200), (3500, 0.01, 200)),
    }[vowel]
    n = ns(dur + release)
    src = _saw_stack(f, n, rng, voices, 16, 5.0, 16, 0.2)
    src += (bp(noise(n, rng), 600, 6000) * 0.05)[:, None]
    y = np.zeros_like(src)
    for fc, a, bw in formants:
        y += resonator(src, fc, fc / bw) * a
    y = lp(y, 6000, 2)
    env = adsr(dur, attack, 0.4, 0.9, release)[:n]
    return y * env[:, None] * (0.35 + 0.65 * vel) * 0.9


def choir_stab(f, dur, vel, rng, vowel="ah"):
    return choir(f, min(dur, 0.4), vel, rng, vowel=vowel, attack=0.02, release=0.5)


def organ(f, dur, vel, rng, pipe=True):
    """Pipe organ (flue + mixture ranks) with chiff and subtle tremulant (stereo)."""
    n = ns(dur + 0.6)
    t = tvec(n)
    ranks = ((0.5, 0.55), (1, 1.0), (2, 0.55), (3, 0.28), (4, 0.25), (6, 0.1), (8, 0.08)) if pipe else \
        ((0.5, 0.6), (1, 1.0), (1.5, 0.5), (2, 0.6), (3, 0.3), (4, 0.3))
    L = np.zeros(n)
    R = np.zeros(n)
    for i, (r, a) in enumerate(ranks):
        if f * r > 12000:
            continue
        v = sine(f * r * (1 + rng.uniform(-0.0006, 0.0006)), n, rng.uniform()) * a
        if i % 2:
            L += v * 1.1
            R += v * 0.8
        else:
            L += v * 0.8
            R += v * 1.1
    trem = 1 + 0.06 * np.sin(2 * np.pi * 5.5 * t)
    chiff = bp(noise(ns(0.06), rng), f * 2, min(f * 8, 15000)) * np.exp(-tvec(ns(0.06)) / 0.015)
    L[:len(chiff)] += chiff * 0.25
    R[:len(chiff)] += chiff * 0.25
    env = adsr(dur, 0.06, 0.2, 0.95, 0.5)[:n]
    x = np.stack([L * trem, R * (2 - trem)], axis=1) * env[:, None]
    return x * (0.35 + 0.65 * vel) * 0.2


# --------------------------------------------------------------------------- winds


def flute(f, dur, vel, rng, breath=0.09, vib=10.0, bend=0.0):
    n = ns(dur + 0.25)
    t = tvec(n)
    fr = vibrato(f, n, 5.0, vib, 0.25, 0.4, rng)
    if bend:
        fr = fr * 2 ** (bend * np.exp(-t / 0.05) / 1200)
    x = sine(fr, n) + 0.22 * sine(fr * 2, n, 0.25) + 0.07 * sine(fr * 3, n, 0.5) + 0.02 * sine(fr * 4, n)
    br = bp(noise(n, rng), f * 0.9, min(f * 5, 16000)) * breath * 4
    chiff = bp(noise(ns(0.05), rng), f * 2, min(f * 8, 16000)) * np.exp(-tvec(ns(0.05)) / 0.012) * 0.6
    x += br
    x[:len(chiff)] += chiff
    env = adsr(dur, 0.06, 0.15, 0.85, 0.18)[:n]
    am = 1 + 0.05 * np.sin(2 * np.pi * 5.0 * t)
    return x * env * am * (0.35 + 0.65 * vel) * 0.3


def ney(f, dur, vel, rng):
    """Breathy end-blown reed flute with scooped attack."""
    return flute(f, dur, vel, rng, breath=0.22, vib=18.0, bend=-70.0) * 0.95


def ocarina(f, dur, vel, rng):
    n = ns(dur + 0.2)
    fr = vibrato(f, n, 4.6, 9, 0.3, 0.4, rng)
    x = sine(fr, n) + 0.06 * sine(fr * 3, n) + 0.03 * sine(fr * 2, n)
    x += bp(noise(n, rng), f, f * 3) * 0.12
    env = adsr(dur, 0.05, 0.2, 0.85, 0.15)[:n]
    return x * env * (0.35 + 0.65 * vel) * 0.32


def clarinet(f, dur, vel, rng):
    n = ns(dur + 0.2)
    fr = vibrato(f, n, 4.8, 6, 0.35, 0.5, rng)
    x = square(fr, n, 0.5) * 0.8 + sine(fr, n) * 0.4
    x = lp(x, 1400 + 2200 * vel, 2)
    x = peak(x, 1500, 2.5, 1.5)
    x += bp(noise(n, rng), 1000, 4000) * 0.02
    env = adsr(dur, 0.04, 0.2, 0.88, 0.15)[:n]
    return x * env * (0.35 + 0.65 * vel) * 0.3


# --------------------------------------------------------------------------- synths


def synth_lead(f, dur, vel, rng):
    n = ns(dur + 0.2)
    fr = vibrato(f, n, 6.0, 16, 0.2, 0.3, rng)
    x = saw(fr, n, rng.uniform()) * 0.6 + saw(fr * 1.005, n, rng.uniform()) * 0.5 + square(fr * 0.5, n, 0.35) * 0.25
    fe = adsr(dur, 0.01, 0.25, 0.6, 0.15)[:n]
    x = sweep(x, "lp", np.clip(f * 2 + 4500 * fe * (0.5 + 0.5 * vel), 200, 16000), 1.1)
    env = adsr(dur, 0.008, 0.2, 0.85, 0.12)[:n]
    return x * env * (0.35 + 0.65 * vel) * 0.3


def pulse_arp(f, dur, vel, rng):
    gate = min(dur, 0.18)
    n = ns(gate + 0.12)
    x = square(f, n, 0.28) + saw(f * 1.004, n) * 0.4
    fe = np.exp(-tvec(n) / 0.09)
    x = sweep(x, "lp", np.clip(400 + 5500 * fe * vel, 100, 16000), 1.4)
    env = adsr(gate, 0.002, 0.1, 0.4, 0.08)[:n]
    return x * env * (0.35 + 0.65 * vel) * 0.3


def synth_bass(f, dur, vel, rng, drive=1.6):
    n = ns(dur + 0.08)
    x = saw(f, n, rng.uniform()) * 0.8 + square(f * 1.003, n, 0.5) * 0.35 + sine(f * 0.5, n) * 0.0
    fe = np.exp(-tvec(n) / 0.12)
    x = sweep(x, "lp", np.clip(f * 1.5 + 2800 * fe * (0.4 + 0.6 * vel), 60, 12000), 1.2)
    x = soft_clip(x, drive)
    x += sine(f, n) * 0.55
    env = adsr(dur, 0.003, 0.2, 0.75, 0.06)[:n]
    return x * env * (0.35 + 0.65 * vel) * 0.42


def orch_bass(f, dur, vel, rng):
    """Celli + basses section for low lines (stereo)."""
    n = ns(dur + 0.4)
    x = _saw_stack(f, n, rng, 3, 5, 5.0, 6, 0.3)
    x = lp(x, 700 + 900 * vel, 2)
    x += (sine(f, n) * 0.35)[:, None]
    env = adsr(dur, 0.04, 0.3, 0.85, 0.3)[:n]
    return x * env[:, None] * (0.35 + 0.65 * vel) * 0.5


def sub_drone(f, dur, vel, rng):
    n = ns(dur + 1.5)
    t = tvec(n)
    x = sine(f, n) + 0.3 * sine(f * 2.001, n) + 0.12 * sine(f * 3.002, n)
    x *= 1 + 0.1 * np.sin(2 * np.pi * 0.17 * t)
    env = adsr(dur, 1.2, 1.0, 1.0, 1.5)[:n]
    return x * env * vel * 0.4


def dark_drone(f, dur, vel, rng):
    n = ns(dur + 2.0)
    x = _saw_stack(f, n, rng, 4, 9, 0.2, 0.0, 9.0)
    x = lp(x, 380, 2)
    env = adsr(dur, 2.0, 1.0, 1.0, 2.0)[:n]
    return x * env[:, None] * vel * 0.55


def warm_pad(f, dur, vel, rng):
    n = ns(dur + 1.0)
    x = _saw_stack(f, n, rng, 4, 10, 4.0, 4, 0.5) * 0.6
    tri = triangle(f, n)
    x += (tri * 0.5)[:, None]
    x = lp(x, 900 + 700 * vel, 2)
    env = adsr(dur, 0.6, 0.6, 0.9, 1.0)[:n]
    return x * env[:, None] * (0.35 + 0.65 * vel) * 0.38


def air_pad(f, dur, vel, rng):
    """Breathy pad: soft saws with band-limited noise tuned around the pitch (stereo)."""
    n = ns(dur + 1.4)
    x = _saw_stack(f, n, rng, 4, 12, 0.3, 0.0, 9.0) * 0.5
    x = lp(x, 1300, 2)
    for ch in range(2):
        nz = noise(n, rng)
        x[:, ch] += (resonator(nz, f * 2, 30) + resonator(nz, f * 3, 30) * 0.6) * 0.5
    env = adsr(dur, 1.0, 0.8, 0.9, 1.4)[:n]
    return x * env[:, None] * (0.35 + 0.65 * vel) * 0.4


def glass_pad(f, dur, vel, rng):
    """Crystalline FM pad with shimmer (stereo)."""
    n = ns(dur + 1.6)
    t = tvec(n)
    chans = []
    for side in (0, 1):
        det = 1 + (side - 0.5) * 0.004
        idx = 1.2 * np.exp(-t / 2.5) + 0.35
        mod = np.sin(2 * np.pi * f * 3.0 * det * t + rng.uniform(0, 6)) * idx
        c = np.sin(2 * np.pi * f * det * t + mod)
        c += 0.25 * np.sin(2 * np.pi * f * 4.0 * det * t + rng.uniform(0, 6)) * (1 + 0.5 * np.sin(2 * np.pi * 0.3 * t))
        chans.append(c)
    x = np.stack(chans, axis=1)
    x *= (1 + 0.08 * np.sin(2 * np.pi * 4.3 * t))[:, None]
    env = adsr(dur, 0.7, 0.6, 0.85, 1.6)[:n]
    return x * env[:, None] * (0.35 + 0.65 * vel) * 0.18


# --------------------------------------------------------------------------- percussion


def kick(f, dur, vel, rng, punch=1.0):
    n = ns(0.55)
    t = tvec(n)
    fr = 48 + 110 * np.exp(-t / 0.035) * punch
    x = sine(fr, n) * np.exp(-t / 0.42 * 6.9)
    click = hp(noise(ns(0.004), rng), 2500) * np.linspace(1, 0, ns(0.004))
    x[:len(click)] += click * 0.35
    x = soft_clip(x * 1.4, 1.2)
    return x * (0.3 + 0.7 * vel) * 0.8


def snare(f, dur, vel, rng, tail=0.22):
    n = ns(tail + 0.1)
    t = tvec(n)
    body = (sine(185 * (1 + 0.3 * np.exp(-t / 0.01)), n) + 0.6 * sine(330, n)) * np.exp(-t / 0.12 * 6.9)
    nz = bp(noise(n, rng), 1500, 10000) * np.exp(-t / tail * 6.9)
    x = body * 0.5 + nz * 0.7
    return x * (0.25 + 0.75 * vel) * 0.55


def rim(f, dur, vel, rng):
    n = ns(0.08)
    t = tvec(n)
    x = (sine(1700, n) * 0.5 + bp(noise(n, rng), 2000, 6000)) * np.exp(-t / 0.03 * 6.9)
    return x * (0.3 + 0.7 * vel) * 0.4


def clap(f, dur, vel, rng):
    n = ns(0.3)
    t = tvec(n)
    env = np.zeros(n)
    for k in range(3):
        o = ns(0.009 * k)
        env[o:] += np.exp(-tvec(n - o) / 0.006)
    env += 0.5 * np.exp(-t / 0.18 * 6.9)
    x = bp(noise(n, rng), 900, 3500) * env
    return x * (0.3 + 0.7 * vel) * 0.5


_METAL = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)


def _metal(n, rng, scale=1.0):
    return sum(square(fr * scale * 1.7, n, 0.5, rng.uniform()) for fr in _METAL)


def hat(f, dur, vel, rng, open_=False):
    t60 = 0.45 if open_ else 0.07
    n = ns(t60 + 0.02)
    t = tvec(n)
    x = bp(_metal(n, rng) * 0.15 + noise(n, rng), 7000, 15000) * np.exp(-t / t60 * 6.9)
    return x * (0.25 + 0.75 * vel) * 0.32


def hat_open(f, dur, vel, rng):
    return hat(f, dur, vel, rng, open_=True)


def cymbal(f, dur, vel, rng, t60=2.6, swell=False):
    n = ns(t60 + 0.1)
    t = tvec(n)
    x = hp(_metal(n, rng, 1.3) * 0.12 + noise(n, rng), 3500, 2)
    x = shelf_hi(x, 9000, -3)
    if swell:
        e = (t / t[-1]) ** 3
        e[-ns(0.02):] *= np.linspace(1, 0, ns(0.02))
    else:
        e = np.exp(-t / t60 * 6.9) * (1 - np.exp(-t / 0.002))
    return x * e * (0.25 + 0.75 * vel) * 0.3


def crash(f, dur, vel, rng):
    return cymbal(f, dur, vel, rng)


def swell_cymbal(f, dur, vel, rng):
    """Reverse-cymbal swell lasting dur seconds (peaks at the end)."""
    return cymbal(f, dur, vel, rng, t60=dur, swell=True)


def ride(f, dur, vel, rng):
    n = ns(1.4)
    t = tvec(n)
    x = hp(_metal(n, rng, 2.1) * 0.2 + noise(n, rng) * 0.6, 5000) * np.exp(-t / 1.2 * 6.9)
    x += additive([3100, 4720, 6230], [0.5, 0.3, 0.2], [0.9, 0.6, 0.4], n, rng) * 0.4
    return x * (0.25 + 0.75 * vel) * 0.18


def tom(f, dur, vel, rng):
    n = ns(0.7)
    t = tvec(n)
    x = sine(f * (1 + 0.6 * np.exp(-t / 0.03)), n) * np.exp(-t / 0.55 * 6.9)
    x += lp(noise(n, rng), 3000) * np.exp(-t / 0.05 * 6.9) * 0.3
    return x * (0.3 + 0.7 * vel) * 0.6


def taiko(f, dur, vel, rng):
    n = ns(1.4)
    t = tvec(n)
    fr = f * (1 + 0.9 * np.exp(-t / 0.025))
    x = sine(fr, n) * np.exp(-t / 1.1 * 6.9) + 0.35 * sine(fr * 1.58, n) * np.exp(-t / 0.4 * 6.9)
    x += lp(noise(n, rng), 700) * np.exp(-t / 0.25 * 6.9) * 0.6
    x += bp(noise(n, rng), 1000, 5000) * np.exp(-t / 0.02 * 6.9) * 0.3
    x = soft_clip(x * 1.2, 1.3)
    return x * (0.3 + 0.7 * vel) * 0.75


def timpani(f, dur, vel, rng):
    n = ns(2.4)
    t = tvec(n)
    bend = 1 + 0.025 * np.exp(-t / 0.06)
    x = np.zeros(n)
    for r, a, d in ((1, 1.0, 1.9), (1.5, 0.45, 1.3), (1.98, 0.3, 1.0), (2.44, 0.18, 0.7), (2.94, 0.1, 0.5)):
        x += a * sine(f * r * bend, n, rng.uniform()) * np.exp(-t / d * 6.9)
    x += lp(noise(n, rng), 800) * np.exp(-t / 0.05 * 6.9) * 0.5
    x = lp(x, 3000, 2)
    return x * (0.25 + 0.75 * vel) * 0.55


def frame_drum(f, dur, vel, rng):
    n = ns(0.8)
    t = tvec(n)
    x = sine(f * (1 + 0.25 * np.exp(-t / 0.02)), n) * np.exp(-t / 0.45 * 6.9)
    x += 0.3 * sine(f * 2.3, n) * np.exp(-t / 0.15 * 6.9)
    x += bp(noise(n, rng), 300, 3000) * np.exp(-t / 0.05 * 6.9) * 0.4
    return x * (0.3 + 0.7 * vel) * 0.6


def doum(f, dur, vel, rng):
    """Goblet drum low centre stroke."""
    n = ns(0.6)
    t = tvec(n)
    fr = f * (1 + 0.35 * np.exp(-t / 0.015))
    x = sine(fr, n) * np.exp(-t / 0.38 * 6.9) + 0.4 * sine(fr * 1.62, n) * np.exp(-t / 0.18 * 6.9)
    x += 0.15 * sine(fr * 2.31, n) * np.exp(-t / 0.1 * 6.9)
    x += lp(noise(n, rng), 1500) * np.exp(-t / 0.015 * 6.9) * 0.4
    return x * (0.3 + 0.7 * vel) * 0.65


def tek(f, dur, vel, rng, soft=False):
    """Goblet drum rim stroke (tek / ka)."""
    n = ns(0.18)
    t = tvec(n)
    x = bp(noise(n, rng), 1800, 9000) * np.exp(-t / (0.05 if not soft else 0.035) * 6.9)
    x += sine(780, n) * np.exp(-t / 0.06 * 6.9) * 0.5 + sine(1430, n) * np.exp(-t / 0.04 * 6.9) * 0.3
    return x * (0.3 + 0.7 * vel) * (0.32 if soft else 0.45)


def ka(f, dur, vel, rng):
    return tek(f, dur, vel, rng, soft=True)


def riq(f, dur, vel, rng):
    """Frame drum jingles (zills)."""
    n = ns(0.3)
    t = tvec(n)
    x = np.zeros(n)
    for k in range(4):
        o = int(rng.uniform(0, 0.012) * SR)
        burst = additive([rng.uniform(5800, 7200), rng.uniform(8200, 9800), rng.uniform(11000, 12500)],
                         [1, 0.7, 0.4], [0.18, 0.14, 0.1], n - o, rng)
        x[o:] += burst * rng.uniform(0.5, 1.0)
    x += hp(noise(n, rng), 6000) * np.exp(-t / 0.12 * 6.9) * 0.6
    return x * (0.3 + 0.7 * vel) * 0.16


def shaker(f, dur, vel, rng):
    n = ns(0.12)
    t = tvec(n)
    env = (1 - np.exp(-t / 0.012)) * np.exp(-t / 0.09 * 6.9)
    x = bp(noise(n, rng), 4500, 12000) * env
    return x * (0.3 + 0.7 * vel) * 0.35


def finger_cymbal(f, dur, vel, rng):
    n = ns(2.0)
    x = additive([2900, 2911, 4180, 6790, 8420], [1, 0.8, 0.55, 0.35, 0.2], [1.8, 1.8, 1.2, 0.8, 0.5], n, rng, 0.0005)
    return x * (0.3 + 0.7 * vel) * 0.12


def sleigh(f, dur, vel, rng):
    """Small ice-bells shake (frost)."""
    n = ns(0.6)
    x = np.zeros(n)
    for k in range(6):
        o = int(rng.uniform(0, 0.05) * SR)
        x[o:] += additive([rng.uniform(4800, 6500), rng.uniform(7600, 9500)], [1, 0.6], [0.25, 0.18], n - o, rng) \
            * rng.uniform(0.4, 1)
    return x * (0.3 + 0.7 * vel) * 0.07


def heartbeat(f, dur, vel, rng):
    n = ns(0.7)
    t = tvec(n)
    x = sine(f * (1 + 0.5 * np.exp(-t / 0.02)), n) * np.exp(-t / 0.3 * 6.9)
    x = lp(x, 400, 2)
    return x * (0.3 + 0.7 * vel) * 0.8


# --------------------------------------------------------------------------- textures


def wind(f, dur, vel, rng):
    """Slowly moving filtered-noise wind (stereo). f is the centre of the howl band."""
    n = ns(dur + 1.0)
    t = tvec(n)
    chans = []
    for side in range(2):
        nz = noise(n, rng)
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.07 + 0.03 * side) * t + rng.uniform(0, 6))
        lfo2 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.23 * t + rng.uniform(0, 6))
        fc = f * (0.6 + 0.9 * lfo + 0.2 * lfo2)
        y = sweep(nz, "bp", fc, 3.0, block=256)
        chans.append(y * (0.4 + 0.6 * lfo))
    x = np.stack(chans, axis=1)
    env = adsr(dur, 1.5, 1.0, 1.0, 1.0)[:n]
    return x * env[:, None] * vel * 0.25


def riser(f, dur, vel, rng):
    """Noise riser sweeping up over dur seconds (stereo)."""
    n = ns(dur)
    t = tvec(n)
    p = t / t[-1]
    chans = []
    for side in range(2):
        nz = noise(n, rng)
        y = sweep(nz, "bp", 300 * (40 ** p), 2.0, block=128)
        chans.append(y)
    x = np.stack(chans, axis=1) * (p ** 2)[:, None]
    x[-ns(0.01):] *= np.linspace(1, 0, ns(0.01))[:, None]
    return x * vel * 0.35


INSTRUMENTS = {k: v for k, v in globals().items() if callable(v) and not k.startswith("_") and v.__module__ == __name__}
