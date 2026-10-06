"""Mastering, file output and QA measurements."""
import os
import struct

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

from . import dsp
from .dsp import SR

_METER = pyln.Meter(SR)


def lufs(x):
    if len(x) < SR // 2:
        x = np.concatenate([x, np.zeros((SR // 2 - len(x) + 1, x.shape[1]))])
    return float(_METER.integrated_loudness(x))


def master_music(x, target_lufs=-14.0, ceiling_db=-1.0, loop=True, glue_ratio=1.8):
    """Glue-compress, loudness-normalise and brickwall-limit a music buffer (loop-aware)."""
    x = dsp.stereo(x)
    rms_db = 10 * np.log10(np.mean(x ** 2) + 1e-12)
    x = dsp.compress(x, thresh_db=rms_db + 3.0, ratio=glue_ratio, wrap=loop)
    for _ in range(4):
        x = x * dsp.db(target_lufs - lufs(x))
        x = dsp.limit(x, ceiling_db, wrap=loop)
    return x


def master_sfx(x, target_db=-12.0, ceiling_db=-1.0):
    """Normalise an SFX so its loudest 50 ms window sits at target_db RMS, then peak-limit."""
    x = dsp.stereo(x)
    w = max(1, dsp.ns(0.05))
    p = np.convolve(np.mean(x ** 2, axis=1), np.ones(w) / w, mode="same")
    peak_rms = 10 * np.log10(np.max(p) + 1e-12)
    x = x * dsp.db(target_db - peak_rms)
    x = dsp.limit(x, ceiling_db, hold=0.004, wrap=False)
    return x


def trim_silence(x, thresh_db=-70.0, keep=0.02):
    a = np.max(np.abs(dsp.stereo(x)), axis=1)
    idx = np.nonzero(a > dsp.db(thresh_db))[0]
    if len(idx) == 0:
        return x
    end = min(len(x), idx[-1] + dsp.ns(keep))
    return dsp.fade(x[:end], 0.0, min(0.02, end / SR / 4))


def write_wav(path, x, dither_seed=0, loop=False):
    """Write dithered 16-bit stereo PCM; loops carry a standard RIFF smpl chunk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = dsp.stereo(x)
    rng = np.random.default_rng(dither_seed)
    d = (rng.uniform(-0.5, 0.5, x.shape) + rng.uniform(-0.5, 0.5, x.shape)) / 32768.0
    sf.write(path, np.clip(x + d, -1.0, 32767 / 32768), SR, subtype="PCM_16")
    if loop:
        # MIDI unity note C4, nanoseconds/sample, one forward loop, inclusive end.
        header = struct.pack("<9I", 0, 0, round(1e9 / SR), 60, 0, 0, 0, 1, 0)
        region = struct.pack("<6I", 0, 0, 0, len(x) - 1, 0, 0)
        chunk = b"smpl" + struct.pack("<I", len(header) + len(region)) + header + region
        with open(path, "r+b") as f:
            f.seek(0, os.SEEK_END)
            f.write(chunk)
            size = f.tell() - 8
            f.seek(4)
            f.write(struct.pack("<I", size))


def stats(x):
    """Duration, peak dBFS, RMS dBFS and integrated LUFS."""
    x = dsp.stereo(x)
    peak = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x ** 2)))
    return {
        "duration": len(x) / SR,
        "peak_db": 20 * np.log10(peak + 1e-12),
        "rms_db": 20 * np.log10(rms + 1e-12),
        "lufs": lufs(x),
        "clipped": int(np.sum(np.abs(x) >= 0.9999)),
    }


def seam_check(x):
    """Loop seam continuity.

    Returns the seam's first-difference jump relative to the file's 99.9th percentile step, and the
    seam's second-difference (click) energy relative to the 95th percentile of the same metric over the
    file. A seamless loop has both ratios <= 1.
    """
    x = dsp.stereo(x)
    wrapped = np.concatenate([x[-256:], x[:256]])
    step = np.abs(np.diff(x, axis=0))
    p999 = np.percentile(step, 99.9, axis=0)
    seam_step = np.abs(x[0] - x[-1])
    ratio_step = float(np.max(seam_step / (p999 + 1e-12)))
    d2 = np.diff(wrapped, n=2, axis=0)
    w = 88
    seam_e = float(np.mean(d2[256 - 2 - w // 2:256 - 2 + w // 2] ** 2))
    d2_all = np.diff(x, n=2, axis=0)
    hop = 2048
    frames = [np.mean(d2_all[i:i + w] ** 2) for i in range(0, len(d2_all) - w, hop)]
    ratio_click = seam_e / (float(np.percentile(frames, 95)) + 1e-18)
    return {"seam_step_ratio": ratio_step, "seam_click_ratio": ratio_click}
