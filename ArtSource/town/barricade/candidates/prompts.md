# barricade (town P1) — ChatGPT web candidates, 2026-10-12

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High).
Chat: https://chatgpt.com/c/6acc8ce1-3a94-83e8-8681-9bbc9687297e
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. A yellow-and-black water-filled road barrier with broad feet and moulded handle openings. View: front three-quarter. One chunky polished Seoul hunter-guild street asset, modern Korean urban design, broad readable forms, clean restrained material colours, plain neutral background, complete object, square image. No people or readable signage.

Results (one response, 4 images):
- candidate_A.png: yellow body with black top band and black feet, handle openings on top; no diagonal striping.
- candidate_B.png: yellow body with black-and-yellow diagonal stripes on lower band, handle openings on top, broad black feet.
- candidate_C.png: yellow body with black diagonal stripes, two moulded handle openings on top, broad black feet; clearest read.
- candidate_D.png: yellow body with black top stripes, handle openings, broad black feet; stripe pattern only on the top band.

Suggested pick: candidate_C.png. Reason: yellow-and-black diagonal striping, moulded handle openings and broad feet, all as briefed, with a clean silhouette. candidate_B is the alternative.

## Tripo (B5-TRIPO-2, 2026-10-12, third account)
- Image uploaded: candidates/candidate_C.png (the suggested pick above).
- Image-to-3D: studio.tripo3d.ai web, AI Model H3.1 Best Quality, Geometry & Texture: Ultra Mesh Quality on, Texture on, Texture Quality 2K, PBR on. Generate cost 45. Task id: 10efe42b-5976-4371-a0b2-021527934ec4
- Balance: 2900 -> 2855
- Retopology: Topology Triangle, Smart Mesh on, polygon count 3000 target, result 2991 faces (binary count). Cost 35. Balance: 2855 -> 2820
- Export: FBX, Blender preset, texture 2k. Local file: ArtSource/town/barricade/tripo/tripo_convert_b65ad7dc-38f2-4b3b-980c-91ff012bca24.fbx (+ adjacent .fbm)

### Installed 2026-10-13 (B5-INSTALL-2, Blender/town/tripo_pieces.json + Blender/town/guild.py)
- Staging: ArtSource/town/barricade/staging/ (barricade.fbx 2991 tris = Tripo 2991, M_Barricade_Tripo 1024 px, placement.json, barricade.tripo). Uniform/stage scale [2.5048, 2.1541, 2.1541], base-centre pivot at ground, bounds [-1.225, -0.468, 0.0]..[1.225, 0.468, 1.282] m.
- Replaces the five KayKit dungeon barriers of the gate cordon (build_kit_gate(), token `barricade`) and the procedural warning tape: Barricade_Tripo_1..3 at x -19.75/-17.25/-14.75, y -16.2, 2.45 m long; _4 the short corner piece (-13.6, -16.85, rot 90, x scale 0.53); _5 the filler to the Tripo HQ wall (-12.915, -16.2, x scale 0.478). Staged non-uniformly (x2.505, y/z 2.154) to 2.45 x 0.936 x 1.282 m. The Col_Barricade_* colliders and Col_Barricade_Corner stay in guild.py.
- Town rebuilt with `blender -b --factory-startup --python-exit-code 1 -P Blender/town/guild.py -- --no-preview`; texture copied to Assets/_Game/Resources/Art/Town/town_tex/M_Barricade_Tripo.png (town.fbx.meta untouched). Backup of the previous town.fbx/.meta/.tripo, town_tex PNGs, guild.py, markers.json, guild_atmosphere.json, tripo_pieces.json and town_guild.blend: ArtSource/town/_backup_20261012c/. Unity not run by this worker: import, material creation and in-game look still to be verified.

### RESTORE-TOWN-CHARS (2026-10-13, Claude Sonnet)
- Re-staged with ONE uniform scale 2.1541 (was 2.5048/2.1541/2.1541); 2.107 x 0.936 x 1.282 m. Basecolor now the raw 2048 px (was downscaled to 1024). Instances _4/_5 no longer use an x squeeze: _1.._4 are four equal segments along y=-16.2 from x=-21 to the HQ west wall (-12.33), _5 is a return piece at (-12.9,-16.9) rot 90 (uniform). guild.py now rejects anisotropic instance scale.
