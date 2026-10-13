# decor_2 (subway P1) — ChatGPT web candidates, 2026-10-12

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High).
Chat: https://chatgpt.com/c/6acc81af-f6c0-83ee-b1f4-4d4a22baf647
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. A stainless three-seat platform bench with a green back stripe and broad supports. View: front three-quarter. One chunky stylised present-day Seoul subway game asset, restrained cream tile, stainless steel, line-green and navy accents, slightly worn but readable, plain neutral background, whole asset visible, square image. No people, letters, numbers, logos or medieval motifs; screens and windows opaque.

Results (one response, 4 images):
- candidate_A.png: three seats, green back stripe, arm-style side panels with navy inserts; broad supports.
- candidate_B.png: three seats, green back stripe, broad trapezoid supports with navy inserts; clean silhouette.
- candidate_C.png: three seats, green stripe, curved sculpted legs with navy feet; sloped back.
- candidate_D.png: three seats, thin green stripe, slotted seats, cream legs with navy feet.

Suggested pick: candidate_B.png. Reason: three clear seats, green back stripe, broad trapezoid supports and a clean readable silhouette. candidate_A is the alternative.

## Tripo (B5-TRIPO-2, 2026-10-12, third account)
- Image uploaded: candidates/candidate_B.png (the suggested pick above).
- Image-to-3D: studio.tripo3d.ai web, AI Model H3.1 Best Quality, Geometry & Texture: Ultra Mesh Quality on, Texture on, Texture Quality 2K, PBR on. Generate cost 45. Task id: 29cec456-bdf0-4898-bd0b-1fe91cc9496c
- Balance: 3540 -> 3495
- Retopology: Topology Triangle, Smart Mesh on, polygon count 3500 target, result 3424 faces (binary count). Cost 35. Balance: 3495 -> 3460
- Export: FBX, Blender preset, texture 2k. Local file: ArtSource/terrain/subway/decor_2/tripo/tripo_convert_a1ba9426-85d5-4439-aa63-00b54b60d0ea.fbx (+ adjacent .fbm)

### Installed 2026-10-13 (B5-INSTALL-2)
- decor_2.fbx: stainless station bench, uniform x1.737 to 1.7 m wide (1.7 x 0.702 x 0.908 m), base-centre pivot, front (seat side) = Blender -Y = Unity +Z (Dress() turns it toward the cell), 3424 tris (Tripo 3424). Material M_SubwayBench_Tripo.
- Installed 2026-10-13 (B5-INSTALL-2) into Assets/_Game/Resources/Art/Environment/subway/ ; original + .fbx.meta backed up in ArtSource/terrain/subway/_backup_20261012/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (1024 px) written; Unity creates <piece>_mat. Export: Blender/lib/abyss_bpy.export_fbx, path_mode RELATIVE, force=True. Shared single material name, no .001 duplicates. Unity not run by this worker: import/material creation and in-game facing still to be verified.

### RESTORE-SUBWAY (2026-10-13, Claude Sonnet)
Texture-only: installed decor_2_tex/M_SubwayBench_Tripo.png replaced with raw 2048 basecolor pixels. Installed FBX already raw geometry (3424 tris, UV 100%, scale 1.7372 uniform) - untouched.
