# Elite mushroom: standalone Cast verification — 2026-10-15

**Verdict: usable complete one-shot `Cast` source, with foot-contact quality limitations.** This export contains an actual `cast_a_spell` motion through its entire 5.375 seconds. Windup, hand thrust, held casting pose, and return to the starting pose are visible in the rendered evidence. It is not the static tail from the previous concatenated export. Parent owns visual acceptance, event timing, retargeting and Unity import.

Requested execution: `gpt-6-astra`, reasoning `high`, priority/Fast where supported. Served model, effort and service tier are not independently observable from this worker's tool results; no configuration was changed. No children were used.

## Source and preservation

Parent-reported Studio provenance: exactly one selected `주문_걸기`, UI duration 5.37s, FBX/Mixamo, skeleton on, current-frame off, in-place on, 1k export setting, 0 credits spent, balance 3260. These UI facts were provided by the parent; this worker did not open Studio.

- Raw FBX: `raw/tripo_convert_5a303303-ca4a-4913-b018-a1250767306b.fbx`; 12,679,024 bytes; SHA-256 `628fcf6d8c54dc59c8835ca1be1e206c0c67d90a29ff0f3a91e70f3009a0063b`.
- Archive: `elite_mushroom_cast_only.zip`; 22,247,391 bytes; SHA-256 `825ce2f26a6495b9e97e2d2c006cb653e57d53cff7808c2ac27d68f3e744ca0c`.
- All six ZIP members match the loose raw FBX and five textures. The ZIP plus all six raw files are retained unchanged, checked before/after. Blender imported only the byte-identical copy in `processed/source-input`, so embedded-texture extraction could not write to `raw`.
- Actual mesh: 5,836 vertices, 11,662 triangles, 65 bones; material `tripo_mat_5a303303`. Basecolor, normal, metallic and roughness are 1024×1024. The supplied packed `_rm.PNG` is **2048×2048**, despite the parent-reported 1k setting; it was preserved, not resized.

## Skin and full motion

Installed Blender **5.2.1 LTS**, headless, 4 threads; analysis, rig verification and both final render commands exited 0. `Tools/verify_tripo_rig.py` reports **PASS**: 5,836/5,836 weighted vertices, zero unweighted vertices, zero invalid weights, weight sums 1.0–1.000000052. Independent 23°/17°/11° rotation probes on 12 major limb bones all produce actual evaluated mesh deformation. No posed probe was saved or exported.

There is one action, `Armature|cast_a_spell|Base Layer`, from native take **`cast_a_spell`**. 650 imported F-curves; 377 nonconstant native curves. Every one of the 129 sampled frame transitions changes pose, including **76/76 transitions from Blender 53 to 129**. No static tail was detected at the documented thresholds (0.01° local bone rotation or 0.000001 world-unit bone-head displacement). Evaluated skin and bounds were measured at all 130 frames.

The armature object's matrix is constant. Hips horizontal spans are approximately 0.000004092 × 0.000009290 world units; vertical range is 0.150476–0.194719, with zero endpoint displacement. This supports the in-place export setting. Start/end maximum bone-head difference is 0.000000582; maximum evaluated surface difference is 0.000000579; maximum local bone-angle difference is 0.000262°. Use as a one-shot; matching endpoint poses alone do not establish loop velocity continuity.

Full animated bounds in Blender world **X/Y/Z, Z-up**: minimum `(-0.442638, -0.573437, -0.079764)`, maximum `(0.365139, 0.315702, 0.963070)`. First-frame mesh height is 0.983199 world units. No normalization, root adjustment, geometry changes, new clips or re-export was performed.

## Exact clip mapping

Use the **whole named take `cast_a_spell`**, game label `Cast`, 24fps, loop off.

| Coordinate system | First | Last | Duration |
|---|---:|---:|---:|
| Native FBX frames | -1 | 128 | 129 intervals |
| Native FBX absolute seconds | -0.041666667 | 5.333333333 | 5.375s |
| Blender imported frames | 0 | 129 | 130 endpoint-inclusive samples |
| Time relative to take start | 0s | 5.375s | 5.375s |

`Blender frame B = native frame F + 1`; `elapsed seconds = B/24 = (F+1)/24`; `normalized time = B/129`. Native AnimationStack `LocalStart/LocalStop` and take `LocalTime/ReferenceTime` agree: `-1924423250..246326176000` ticks, at 46,186,158,000 ticks/second. The unrelated global FBX `TimeSpanStart/Stop` is 0..1 second and **must not be used to truncate the take**. Blender represents the first frame as `1.1102230246251565e-16`; analysis/render boundary checks treat this floating-point epsilon as frame 0.

Unity was not run. Its importer frame origin has not been independently observed. Parent should select the full named take and inspect its actual importer range; do not blindly paste Blender 0..129 into a different coordinate system. Machine-readable mapping is in `processed/cast-mapping.json`.

## Windup, release and recovery

These are interpretations of sampled poses and renders, **not authored event markers or new subclips**. Adjacent rows partition the sampled integer frames, while the source animation remains continuous.

| Observed phase | Blender frames | Native frames | Take-relative sample times |
|---|---:|---:|---:|
| Ready pose, slight motion | 0–9 | -1–8 | 0–0.375s |
| Body/arm preparation and hand gathering | 10–56 | 9–55 | 0.416667–2.333333s |
| Right-hand thrust / release | 57–64 | 56–63 | 2.375–2.666667s |
| Extended casting pose with residual motion | 65–88 | 64–87 | 2.708333–3.666667s |
| Recovery, return and settling | 89–129 | 88–128 | 3.708333–5.375s |

**Event candidate for parent review: B60 / native F59 / elapsed 2.500s / normalized 0.465116.** The right shoulder-to-hand distance rises from 0.126024 at B56 to 0.213003 at B60 and 0.214029 at B61; the B60 render shows the thrust, with the extended pose settling by B64. This is a suggested synchronization point, not a claimed embedded animation event. No VFX or event was added.

## Contact and sliding limitation

Ground is estimated from the lowest foot surface at B0: Z = **-0.045747932**. There are no authored contact flags. Fixed sole markers are the lowest 20% of foot-weighted vertices at B0 (43 per foot); they are tracked through the evaluated skin. Near-floor means within 0.019664 world units above this reference; low speed means at most 0.049160 world units/second. The render plane is 0.002 below the same numerical reference, not a per-frame floor adjustment.

- Left foot: near-floor at all 130 frames, maximum penetration below the reference 0.034016 at B91. Near-floor peak sole speed 0.419971 units/s at B92→93. During recovery B89–113, near-floor sole-centroid net XY travel is **0.196216** units (about 20% of body height), with path length 0.197254. This is material contact drift, not a locked planted foot.
- Right foot: near-floor at 117/130 frames, maximum penetration 0.021329 at B42, maximum lift above reference 0.046787. Near-floor peak sole speed 0.644991 units/s at B101→102. Intentional foot lifting/pivoting is visible in the contact sheets.
- Only 47/129 transitions per foot satisfy both near-floor and low-speed criteria. Rotations, foot shape and skin deformation contribute to centroid travel, so these figures are not all pure translational sliding. Nevertheless, this source does **not** pass a strict no-slide/no-penetration contact gate. Parent may accept it for the stylized Cast or require later contact polish; no corrective motion was synthesized here.

## Comparison with previous concatenation

The existing `../../processed/motion-evidence.json` records old action `walk_hit_to_body_01_idle_cheer_cast_a_spell_defeat_03_box_01`, Blender range 0..368, movement ending at B53 and a static B53..368 tail. That old report is the comparison baseline, not a new claim of re-running it. The new standalone native action is explicitly `cast_a_spell`, spans B0..129, has 374 native curves changing after native F52, and has all 76 B53..129 transitions moving. Therefore the previous static tail must not be used for Cast; this standalone file supplies the missing motion.

## Evidence and reproduction

Both contact sheets were opened and visually inspected by this worker:

- `processed/contact-sheet-overview-front.png`: 18 original-action poses, 1920×960; fixed **+Y** inspection camera. The inherited filename label `front` is not a verified character-forward or Unity-forward contract; this view mostly shows the back/side.
- `processed/contact-sheet-phase-detail-opposite-quarter.png`: 12 poses, 1920×640; fixed **+X/-Y** camera revealing the face and casting hand. Key sampled frames are 0,24,40,52,56,60,64,80,92,102,112,129.
- Original per-frame PNGs and indices are retained under `processed/renders` and `processed/render-index-*.json`. Cycles CPU, 4 threads, 12 samples, 320×320 tiles. Inspection material uses the unchanged source basecolor with temporary roughness 0.72. The camera, lights, labels and floor exist only for evidence; none are exported.
- `processed/rig-verification.json`, `motion-analysis.json`, `frame-metrics.json`, `motion-samples.npz`, `raw-animation-curves.json`, `pose-landmarks.json`, `contact-detail.json`, `archive-verification.json`, and `raw-hashes-*.json` contain the numerical evidence.

Commands were run from the checkout with `C:\Users\User\Tools\Blender\blender.exe --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1` followed by:

```text
--python Tools/inspect_elite_cast.py -- analyze
--python Tools/verify_tripo_rig.py -- <cast>/processed/source-input/tripo_convert_5a303303-ca4a-4913-b018-a1250767306b.fbx <cast>/processed/rig-verification.json
--python Tools/inspect_elite_cast.py -- render --frames 0,8,16,24,32,40,48,56,64,72,80,88,96,104,112,120,124,129 --view front --tag overview
--python Tools/inspect_elite_cast.py -- render --frames 0,24,40,52,56,60,64,80,92,102,112,129 --view opposite-quarter --tag phase-detail
```

`<cast>` means `ArtSource/enemies/elite_mushroom/enrichment_20261015/individual-motion-exports/cast`. Logs are retained. The first overview attempt stopped at the overly strict floating-point boundary check before any rendering; `render-overview.log` preserves that failure. The boundary check was corrected to match verified integer FBX boundaries, and `render-overview-retry.log` records the successful complete render. No Unity import, source compiler, tests, browser, network, model generation, source-motion edits or application configuration changes were performed.

Owned writes: this `verification.md`, `cast/processed/**`, and `Tools/inspect_elite_cast.py` only. Existing shared inspection scripts were imported/read, not edited.

## Parent disposition — 2026-10-15

After viewing **both Cast contact sheets**, the parent **rejected Unity integration** because the approximately 19.6 cm recovery contact drift fails the user's requested naturalness. The technical finding that this is a complete, deforming Cast remains historical evidence, not approval for game use. Preserve the raw source, reports and rendered evidence; do not import or substitute this motion, regress the current asset, or continue cleanup. Parent's existing `.gitignore` excludes `processed/source-input/` staging while retaining the original `raw/` files. Final acceptance disposition: **archived evidence only; not approved for Unity integration**.
