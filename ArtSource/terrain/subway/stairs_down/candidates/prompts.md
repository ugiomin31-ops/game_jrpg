# terrain/subway · stairs_down — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd7292-b604-83ee-894e-c66d5b1e201f
Brief source: ArtSource/_briefs/environment_tiling.md §3 (stairs: straight side or three-quarter orthographic view of the stair run) and §2/§3 geometry (stairs_down = half floor at y 0..2 plus 5 steps descending to z -2.5 over y -2..0). NO subway row exists for stairs in environment_tiling.md §6 or environment.md, so the look is INFERRED from the existing subway set (cream tiles, green line-2 stripe, steel), and this is stated here as the inference.
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky toon staircase going down for a stylised game set in a modern Seoul subway station: a stair opening of five cream tiled steps descending into the ground, each step nosing edged with a green line stripe, with steel handrails on both sides. Straight side three-quarter orthographic view of the stair run, the whole stair visible with margins, the top landing flat and level with the floor, a clean readable silhouette, no perspective exaggeration. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, even flat lighting, no shadow, plain light-grey background, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no medieval or fantasy ornament, no skulls, no runes, no crowns, no gold filigree. Vary step height, handrail thickness and stripe width within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_D.png. Reason: five cream steps with green nosings and steel rails on both sides, symmetric compact silhouette with a flat top landing. Alternative: candidate_C.png

## Tripo (B6-TRIPO-2, 2026-10-13, third account, quality-first)
- Picked image: candidate_D.png (pick line above), uploaded exactly.
- Generate: task bbe23630-7972-4a97-b28a-18d8115ea83a. H3.1 Best Quality, Ultra Mesh on, Texture on, 4K (55), PBR on, Triangle. Cost 55, balance 1480 -> 1425.
- Retopo: Triangle + Smart Mesh on, polygon count set to 6000 with form_input, cost 35, balance 1425 -> 1390. Actual faces 5617.
- Export: FBX, Blender preset, texture 2k, static. Local: ArtSource/terrain/subway/stairs_down/tripo/tripo_convert_2903b0ab-a950-4574-8c05-f577b3463ac3.fbx (+ .fbm). Zip kept as stairs+3d+model.zip.


### Installed 2026-10-13 (INSTALL-B6-2, Claude Sonnet, headless Blender, no credits)
- Assets/_Game/Resources/Art/Environment/subway/stairs_down.fbx replaced in place (GUID kept; old file+meta in ArtSource/_backup_20261013_b6_2/subway/). Raw Tripo geometry only: 5617 tris = raw 5617, UV multiset 100%, single uniform scale (anisotropy 1.0), rigid rotation/pivot only, one mesh 'stairs_down' (no children needed: the code looks up no anchors for this piece), material M_SubwayStairsDown_Tripo.
- Placement: uniform 4.0924 (4.0 m on the larger footprint axis like stairs_up, no rotation: raw rises toward +Y = south landing, steps descend toward north); landing top (raw z 0.3099) at z=0; x/y centred; bbox x +-1.64, y +-2.0, z -1.268..+0.728 m.
- Texture: raw 2048 basecolor JPEG -> stairs_down_tex/M_SubwayStairsDown_Tripo.png pixel-identical; stairs_down.tripo marker written; Unity creates _mat on import.
