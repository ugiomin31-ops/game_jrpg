# cargo (town P1) — ChatGPT web candidates, 2026-10-12

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High).
Chat: https://chatgpt.com/c/6acc8bb0-0bc8-83ee-925e-a5b2ca8203b5
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. Stacked shipping boxes beside a low steel workbench; no labels. View: front three-quarter. One chunky polished Seoul hunter-guild street asset, modern Korean urban design, broad readable forms, clean restrained material colours, plain neutral background, complete object, square image. No people or readable signage.

Results (one response, 4 images):
- candidate_A.png: stacked cardboard and olive cases beside a steel workbench with lower shelf; the workbench is low.
- candidate_B.png: tall stacks of cardboard and cases beside a steel workbench with a back rail; workbench is taller.
- candidate_C.png: stacked cardboard and cases beside a steel workbench; workbench is low with a lower shelf.
- candidate_D.png: stacked cardboard and olive cases beside a steel workbench with a rear rail; the rail adds height.

Suggested pick: candidate_C.png. Reason: stacked boxes beside a low steel workbench with a lower shelf, no labels, clean silhouette. candidate_A is the alternative.

## Tripo (B5-TRIPO-2, 2026-10-12, third account)
- Image uploaded: candidates/candidate_C.png (the suggested pick above).
- Image-to-3D: studio.tripo3d.ai web, AI Model H3.1 Best Quality, Geometry & Texture: Ultra Mesh Quality on, Texture on, Texture Quality 2K, PBR on. Generate cost 45. Task id: 99bf94c1-d6cb-4eb2-b5ce-345bbe43eefb
- Balance: 2980 -> 2935
- Retopology: Topology Triangle, Smart Mesh on, polygon count 4000 target, result 4506 faces (binary count). Cost 35. Balance: 2935 -> 2900
- Export: FBX, Blender preset, texture 2k. Local file: ArtSource/town/cargo/tripo/tripo_convert_7113615c-9247-4c85-982f-660bc3153d5b.fbx (+ adjacent .fbm)

### Installed 2026-10-13 (B5-INSTALL-2, Blender/town/tripo_pieces.json + Blender/town/guild.py)
- Staging: ArtSource/town/cargo/staging/ (cargo.fbx 4506 tris = Tripo 4506, M_Cargo_Tripo 1024 px, placement.json, cargo.tripo). Uniform/stage scale [2.452, 2.452, 2.452], base-centre pivot at ground, bounds [-1.2, -0.589, 0.0]..[1.2, 0.589, 1.348] m.
- Replaces the KayKit cargo_A/cargo_B boxes + table_low in front of the workshop (build_storefront_kits(), token `cargo`): one instance Workshop_Cargo at (14.6, 5.2), rot -90 (front toward -X), 2.4 x 1.179 x 1.348 m (uniform x2.452). Collider Col_Workshop_Cargo 2.4 x 1.18 x 1.2 m (new).
- Town rebuilt with `blender -b --factory-startup --python-exit-code 1 -P Blender/town/guild.py -- --no-preview`; texture copied to Assets/_Game/Resources/Art/Town/town_tex/M_Cargo_Tripo.png (town.fbx.meta untouched). Backup of the previous town.fbx/.meta/.tripo, town_tex PNGs, guild.py, markers.json, guild_atmosphere.json, tripo_pieces.json and town_guild.blend: ArtSource/town/_backup_20261012c/. Unity not run by this worker: import, material creation and in-game look still to be verified.
