"""Core DSP primitives: oscillators, envelopes, filters, spatial effects and dynamics.

All signals are float64 numpy arrays at SR. Mono signals are 1-D, stereo signals are (n, 2).
"""
import zlib

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

SR = 44100


# --------------------------------------------------------------------------- helpers

def seeded_rng(*key):
    """Deterministic RNG derived from an arbitrary key (stable across processes)."""
    return np.random.default_rng(zlib.crc32(repr(key).encode("utf-8")))


def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def ns(seconds):
    return max(1, int(round(seconds * SR)))


def tvec(n):
    return np.arange(n) / SR


def db(x):
    return 10.0 ** (x / 20.0)


def fit(x, n):
    """Pad with zeros or truncate along axis 0 to length n."""
    if len(x) >= n:
        return x[:n]
    pad = [(0, n - len(x))] + [(0, 0)] * (x.ndim - 1)
    return np.pad(x, pad)


def mix_into(dst, src, start):
    """Add src into dst at sample offset start (clipped to dst bounds)."""
    if start >= len(dst):
        return
    s0 = 0
    if start < 0:
        s0 = -start
        start = 0
    if s0 >= len(src):
        return
    n = min(len(src) - s0, len(dst) - start)
    dst[start:start + n] += src[s0:s0 + n]


def pan(x, p):
    """Constant-power pan of a mono signal; p in [-1, 1]."""
    a = (p + 1.0) * np.pi / 4.0
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * np.sqrt(2.0)


def stereo(x):
    return x if x.ndim == 2 else np.stack([x, x], axis=1)


def balance(x, p):
    """Pan an already stereo signal (keeps width, shifts balance)."""
    a = (p + 1.0) * np.pi / 4.0
    g = np.array([np.cos(a), np.sin(a)]) * np.sqrt(2.0)
    return x * g


def width(x, w):
    """Mid/side width scaling for stereo signals (w=0 mono, 1 unchanged, >1 wider)."""
    m = (x[:, 0] + x[:, 1]) * 0.5
    s = (x[:, 0] - x[:, 1]) * 0.5 * w
    return np.stack([m + s, m - s], axis=1)


def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    if fin > 0:
        n = min(len(x), ns(fin))
        r = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
        x[:n] *= r if x.ndim == 1 else r[:, None]
    if fout > 0:
        n = min(len(x), ns(fout))
        r = np.cos(np.linspace(0, np.pi / 2, n)) ** 2
        x[-n:] *= r if x.ndim == 1 else r[:, None]
    return x


# --------------------------------------------------------------------------- envelopes

def adsr(gate, a, d, s, r, pad=2.0):
    """ADSR envelope: gate seconds of A/D/S, an exponential release of r seconds (-60 dB), then `pad`
    seconds of silence so callers can slice it to any buffer length up to gate + r + pad."""
    ng = ns(gate)
    nr = ns(r)
    t = tvec(ng)
    a = max(a, 1e-4)
    att = np.sin(np.clip(t / a, 0, 1) * np.pi / 2) ** 1.5
    dec = s + (1.0 - s) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4) * 3.0)
    e = np.where(t < a, att, dec)
    rel = e[-1] * np.exp(-tvec(nr) / r * 6.9)
    out = np.concatenate([e, rel])
    out[-ns(0.003):] *= np.linspace(1, 0, ns(0.003))
    return np.concatenate([out, np.zeros(ns(pad))])


def perc(n, attack, t60):
    """Percussive envelope of n samples: short sine attack, exponential decay reaching -60 dB at t60."""
    t = tvec(n)
    a = max(attack, 1e-4)
    return np.where(t < a, np.sin(np.clip(t / a, 0, 1) * np.pi / 2), np.exp(-(t - a) / t60 * 6.9))


# --------------------------------------------------------------------------- oscillators

def _phase(f, n, phase0=0.0):
    inc = np.full(n, f / SR) if np.isscalar(f) else np.asarray(f, dtype=float) / SR
    ph = (np.cumsum(inc) - inc[0] + phase0) % 1.0
    return ph, inc


def _blep(ph, dt):
    out = np.zeros_like(ph)
    m = ph < dt
    if np.any(m):
        x = ph[m] / (dt[m] if np.ndim(dt) else dt)
        out[m] = x + x - x * x - 1.0
    m = ph > 1.0 - dt
    if np.any(m):
        x = (ph[m] - 1.0) / (dt[m] if np.ndim(dt) else dt)
        out[m] = x * x + x + x + 1.0
    return out


def sine(f, n, phase0=0.0):
    ph, _ = _phase(f, n, phase0)
    return np.sin(2 * np.pi * ph)


def saw(f, n, phase0=0.0):
    """Band-limited (polyBLEP) sawtooth."""
    ph, dt = _phase(f, n, phase0)
    return 2.0 * ph - 1.0 - _blep(ph, dt)


def square(f, n, pw=0.5, phase0=0.0):
    """Band-limited pulse wave with pulse width pw."""
    ph, dt = _phase(f, n, phase0)
    ph2 = (ph + (1.0 - pw)) % 1.0
    a = 2.0 * ph - 1.0 - _blep(ph, dt)
    b = 2.0 * ph2 - 1.0 - _blep(ph2, dt)
    return (a - b) * 0.5


def triangle(f, n, phase0=0.0):
    ph, _ = _phase(f, n, phase0)
    return 2.0 * np.abs(2.0 * ph - 1.0) - 1.0


def vibrato(f, n, rate=5.0, depth_cents=12.0, delay=0.25, ramp=0.4, rng=None):
    """Frequency curve with delayed vibrato (and slight random drift)."""
    t = tvec(n)
    amt = np.clip((t - delay) / max(ramp, 1e-3), 0, 1)
    ph0 = rng.uniform(0, 2 * np.pi) if rng is not None else 0.0
    cents = depth_cents * amt * np.sin(2 * np.pi * rate * t + ph0)
    return f * 2.0 ** (cents / 1200.0)


def noise(n, rng):
    return rng.standard_normal(n)


def additive(freqs, amps, decays, n, rng=None, attack=0.002):
    """Sum of decaying sine partials. decays are t60 seconds per partial."""
    t = tvec(n)
    out = np.zeros(n)
    for f, a, d in zip(freqs, amps, decays):
        if f >= SR * 0.45 or a == 0:
            continue
        ph = rng.uniform(0, 2 * np.pi) if rng is not None else 0.0
        out += a * np.sin(2 * np.pi * f * t + ph) * np.exp(-t / d * 6.9)
    na = ns(attack)
    if na > 1:
        out[:na] *= np.linspace(0, 1, na)
    return out


# --------------------------------------------------------------------------- filters

def _sos(kind, fc, order=2, q=None):
    fc = np.clip(fc, 10.0, SR * 0.49)
    return signal.butter(order, fc, btype=kind, fs=SR, output="sos")


def lp(x, fc, order=2):
    return signal.sosfilt(_sos("lowpass", fc, order), x, axis=0)


def hp(x, fc, order=2):
    return signal.sosfilt(_sos("highpass", fc, order), x, axis=0)


def bp(x, lo, hi, order=2):
    lo = max(lo, 10.0)
    hi = min(hi, SR * 0.49)
    sos = signal.butter(order, [lo, hi], btype="bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def _rbj(kind, f0, q, gain_db=0.0):
    f0 = float(np.clip(f0, 10.0, SR * 0.49))
    w0 = 2 * np.pi * f0 / SR
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2 * q)
    A = 10 ** (gain_db / 40)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "bp":
        b = [alpha, 0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "peak":
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind == "lowshelf":
        sq = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) - (A - 1) * cw + sq), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sq)]
        a = [(A + 1) + (A - 1) * cw + sq, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sq]
    elif kind == "highshelf":
        sq = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) + (A - 1) * cw + sq), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sq)]
        a = [(A + 1) - (A - 1) * cw + sq, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sq]
    else:
        raise ValueError(kind)
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return b, a


def biquad(x, kind, f0, q=0.707, gain_db=0.0):
    b, a = _rbj(kind, f0, q, gain_db)
    return signal.lfilter(b, a, x, axis=0)


def peak(x, f0, gain_db, q=1.0):
    return biquad(x, "peak", f0, q, gain_db)


def shelf_lo(x, f0, gain_db):
    return biquad(x, "lowshelf", f0, 0.707, gain_db)


def shelf_hi(x, f0, gain_db):
    return biquad(x, "highshelf", f0, 0.707, gain_db)


def resonator(x, f0, q):
    """Band-pass resonance normalised to unity peak gain."""
    return biquad(x, "bp", f0, q)


def sweep(x, kind, fc_curve, q=0.707, block=64):
    """Time-varying RBJ biquad (lp/hp/bp) with cutoff curve fc_curve (same length as x, mono)."""
    n = len(x)
    out = np.empty(n)
    zi = np.zeros(2)
    for i in range(0, n, block):
        b, a = _rbj(kind, fc_curve[min(i + block // 2, n - 1)], q)
        out[i:i + block], zi = signal.lfilter(b, a, x[i:i + block], zi=zi)
    return out


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    return signal.lfilter([1 - a], [1, -a], x, axis=0)


# --------------------------------------------------------------------------- plucked strings

def karplus(f, n, rng, bright=0.5, decay=0.996, pick=0.5, excite=None):
    """Karplus-Strong plucked string with exact tuning (rendered at a nearby rate, then resampled).

    bright: excitation brightness 0..1. decay: per-period loop gain. pick: pick position comb 0..1.
    """
    period = SR / f
    N = int(np.floor(period - 0.5))
    N = max(N, 2)
    f_ks = SR / (N + 0.5)
    ratio = f / f_ks
    m = int(n * ratio) + 4
    if excite is None:
        ex = rng.uniform(-1, 1, N)
        ex = onepole_lp(ex, 600 + bright * 9000)
        if 0 < pick < 1:
            k = max(1, int(N * pick * 0.5))
            ex = ex - np.concatenate([np.zeros(k), ex[:-k]])
    else:
        ex = fit(excite, N)
    ex = ex - ex.mean()
    x = np.zeros(m)
    x[:N] = ex
    g = decay * 0.5
    a = np.zeros(N + 2)
    a[0] = 1.0
    a[N] -= g
    a[N + 1] -= g
    y = signal.lfilter([1.0], a, x)
    # resample to exact pitch
    src_t = np.arange(n) * ratio
    return np.interp(src_t, np.arange(m), y)


# --------------------------------------------------------------------------- modulation / space

def chorus(x, rate=0.8, depth_ms=2.5, base_ms=12.0, mix=0.5, rng=None):
    """Stereo chorus (input mono or stereo, output stereo)."""
    x = stereo(x)
    n = len(x)
    t = tvec(n)
    out = x.copy() * (1 - mix * 0.5)
    for ch, ph in ((0, 0.0), (1, np.pi / 2)):
        d = (base_ms + depth_ms * np.sin(2 * np.pi * rate * t + ph)) * SR / 1000.0
        idx = np.arange(n) - d
        out[:, ch] += np.interp(idx, np.arange(n), x[:, ch], left=0.0) * mix
    return out


def make_ir(t60=2.2, predelay=0.02, bright=0.5, early=True, seed=7, length=None):
    """Synthetic stereo reverb impulse response (decorrelated channels, frequency-dependent decay)."""
    rng = seeded_rng("ir", t60, predelay, bright, seed)
    L = length if length is not None else t60 * 1.25
    n = ns(L)
    t = tvec(n)
    chans = []
    for ch in range(2):
        w = rng.standard_normal(n)
        lo = lp(w, 350, 2)
        hi = hp(w, 3500, 2)
        mid = w - lo - hi
        t_lo, t_mid, t_hi = t60 * 1.15, t60, t60 * (0.25 + 0.5 * bright)
        ir = lo * np.exp(-t / t_lo * 6.9) + mid * np.exp(-t / t_mid * 6.9) + hi * np.exp(-t / t_hi * 6.9)
        ir *= 1.0 - np.exp(-t / 0.012)
        if early:
            for _ in range(10):
                k = int(rng.uniform(0.004, 0.07) * SR)
                ir[k] += rng.uniform(-1, 1) * 6.0 * np.exp(-k / SR / 0.08)
        ir = np.concatenate([np.zeros(ns(predelay)), ir])
        chans.append(ir / np.sqrt(np.sum(ir ** 2)))
    return np.stack(chans, axis=1)


def convolve(x, ir, n_out=None):
    """Convolve (mono or stereo) x with stereo IR -> stereo of length n_out (default len(x))."""
    n_out = n_out or len(x)
    x = stereo(x)
    out = np.zeros((n_out, 2))
    for ch in range(2):
        y = signal.fftconvolve(x[:, ch], ir[:, ch], mode="full")
        out[:, ch] = fit(y, n_out)
    return out


def echo(x, time_s, feedback=0.4, repeats=8, pingpong=True, lp_hz=4000.0, hp_hz=200.0):
    """Feedback delay (stereo out). Each repeat is darker; ping-pong alternates sides."""
    x = stereo(x)
    n = len(x)
    d = ns(time_s)
    out = np.zeros_like(x)
    cur = hp(x, hp_hz)
    g = 1.0
    for k in range(1, repeats + 1):
        cur = lp(cur, lp_hz, 1)
        g *= feedback if k > 1 else 1.0
        shifted = np.zeros_like(x)
        off = d * k
        if off >= n:
            break
        src = cur[:n - off]
        if pingpong:
            src = src[:, ::-1] if k % 2 == 1 else src
        shifted[off:] = src * g
        out += shifted
    return out


# --------------------------------------------------------------------------- dynamics

def _filt_mode(wrap):
    return "wrap" if wrap else "nearest"


def compress(x, thresh_db=-18.0, ratio=2.0, window=0.04, smooth=0.12, wrap=True):
    """RMS bus compressor (zero-latency, symmetric smoothing). wrap=True treats x as a loop."""
    mode = _filt_mode(wrap)
    p = uniform_filter1d(np.mean(x ** 2, axis=1), size=ns(window), mode=mode)
    lvl = 10 * np.log10(p + 1e-12)
    gr = -np.maximum(lvl - thresh_db, 0.0) * (1.0 - 1.0 / ratio)
    gr = uniform_filter1d(gr, size=ns(smooth), mode=mode)
    return x * db(gr)[:, None]


def limit(x, ceiling_db=-1.0, hold=0.02, wrap=True):
    """Look-ahead brickwall limiter (gain never exceeds what the peak requires). wrap for loops."""
    mode = _filt_mode(wrap)
    c = db(ceiling_db)
    a = np.max(np.abs(x), axis=1)
    g = np.minimum(1.0, c / np.maximum(a, 1e-9))
    w = 2 * ns(hold) + 1
    g = minimum_filter1d(g, size=w, mode=mode)
    g = uniform_filter1d(g, size=w, mode=mode)
    y = x * g[:, None]
    return np.clip(y, -c, c)


def soft_clip(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive)
