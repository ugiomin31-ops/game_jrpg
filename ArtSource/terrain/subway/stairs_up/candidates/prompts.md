# stairs_up (subway P1) — ChatGPT web candidates, 2026-10-12

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High).
Chat: https://chatgpt.com/c/6acc8943-1054-83ec-a389-abe4b3c252f2
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. Broad cream-tiled station stairs with yellow step noses and a green landing stripe; no ornate rails. View: side-biased orthographic three-quarter. One chunky stylised present-day Seoul subway game asset, restrained cream tile, stainless steel, line-green and navy accents, slightly worn but readable, plain neutral background, whole asset visible, square image. No people, letters, numbers, logos or medieval motifs; screens and windows opaque.

Results (one response, 4 images):
- candidate_A.png: wide stairs, cream tile walls with steel caps and a green wall band, yellow step noses, green landing stripe; plain steel handrails; tall, long footprint.
- candidate_B.png: narrow stairs with thin pipe handrails, yellow noses, green landing stripe; less broad than the brief.
- candidate_C.png: broad stairs with a square footprint, cream tile walls with green wall bands, yellow noses, green landing stripe, short plain rails; closest to "broad" and the 4 x 4 m footprint.
- candidate_D.png: broad stairs with steel caps, navy wall base, green wall band and landing stripe, yellow noses; more ornate capping.

Suggested pick: candidate_C.png. Reason: broad, near-square footprint with cream tile, yellow noses, green landing stripe and plain rails; matches the briefed footprint. candidate_A is the alternative.

## Tripo (B5-TRIPO-2, 2026-10-12, third account)
- Image uploaded: candidates/candidate_C.png (the suggested pick above).
- Image-to-3D: studio.tripo3d.ai web, AI Model H3.1 Best Quality, Geometry & Texture: Ultra Mesh Quality on, Texture on, Texture Quality 2K, PBR on. Generate cost 45. Task id: dc2dde96-9314-4f65-9c9b-bd7262f0a9b5
- Balance: 3300 -> 3255
- Retopology: Topology Triangle, Smart Mesh on, polygon count 3000 target, result 2774 faces (binary count). Cost 35. Balance: 3255 -> 3220
- Export: FBX, Blender preset, texture 2k. Local file: ArtSource/terrain/subway/stairs_up/tripo/tripo_convert_adfa439c-c33a-4656-b6d9-02e06ae09aa6.fbx (+ adjacent .fbm)

### Installed 2026-10-13 (B5-INSTALL-2)
- stairs_up.fbx: Tripo subway staircase rotated 180 deg about Z (Tripo rises toward +Y, the cell contract rises toward north = Blender -Y) and fitted to x, y [-2, 2] with z top 2.5 (non-uniform bbox fit: sx 4.554, sy 4.091, sz 7.062). Footprint 4 x 4 x 2.5 m like the old piece (bbox [-2,-2,0]..[2,2,2.5]); the side walls/handrail reach 2.5 m, the central landing is about 1.46 m high (the Tripo landing is lower than its walls; old landing was a 2.5 m solid), steps start at the +Y (south) edge. 2774 tris (Tripo 2774). Material M_SubwayStairs_Tripo.
- Unity must check: from the east neighbour cell the stair now shows its tiled side wall (green stripe) instead of the flat lavender 2.5 m slab; whether the 1.46 m landing is acceptable when the camera stands in the stair cell.
- Installed 2026-10-13 (B5-INSTALL-2) into Assets/_Game/Resources/Art/Environment/subway/ ; original + .fbx.meta backed up in ArtSource/terrain/subway/_backup_20261012/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (1024 px) written; Unity creates <piece>_mat. Export: Blender/lib/abyss_bpy.export_fbx, path_mode RELATIVE, force=True. Shared single material name, no .001 duplicates. Unity not run by this worker: import/material creation and in-game facing still to be verified.
