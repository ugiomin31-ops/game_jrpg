# terrain/subway · overlay_2 — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd70be-bba4-83e8-acff-d467bec85faf
Brief source: ArtSource/_briefs/environment.md, subway table, overlay_2 = "A red fire-hose cabinet with two conduits rising to the ceiling and a small grey fuse box." Overlay rules: wall decal, flat-backed (environment.md, special handling for overlay_1/2).
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One flat decal panel for a stylised game set in a modern Seoul subway station, to be stuck flat on a tiled wall face: a grey steel electrical fuse box and a red fire-hose cabinet with its hose reel and two thick black conduits rising up from it toward the ceiling, with a small grey fuse box at the bottom. Flat-backed, the decal is a relief panel no deeper than a few centimetres. Full panel visible with margins, straight-on front view with a slight three-quarter tilt, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no warning symbols, no UI, no medieval or fantasy ornament, no skulls, no runes, no crowns, no gold filigree. Vary cabinet size, conduit thickness and fuse box position within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_D.png. Reason: centred red hose cabinet with two thick conduits rising to the top and a small grey fuse box below; clean composition, A has the same parts but is busier. Alternative: candidate_A.png

## Tripo (B6-TRIPO-2, 2026-10-13, third account, quality-first)
- Picked image: candidate_D.png (pick line above), uploaded exactly.
- Generate: task f756f01a-8436-403d-a8b2-25fcb833d14d. H3.1 Best Quality, Ultra Mesh on, Texture on, 4K (55), PBR on, Triangle. Cost 55, balance 1210 -> 1155.
- Retopo: Triangle + Smart Mesh on, 6000 (verified by zoom before click), cost 35, balance 1155 -> 1120. Actual faces 6036.
- Export: FBX, Blender preset, texture 2k, static. Local: ArtSource/terrain/subway/overlay_2/tripo/tripo_convert_cc7d5a97-6128-49c2-a05e-14b6cdde39e4.fbx (+ .fbm). Zip kept as industrial+machine+3d+model.zip.


### Installed 2026-10-13 (INSTALL-B6-2, Claude Sonnet, headless Blender, no credits)
- Assets/_Game/Resources/Art/Environment/subway/overlay_2.fbx replaced in place (GUID kept; old file+meta in ArtSource/_backup_20261013_b6_2/subway/). Raw Tripo geometry only: 6036 tris = raw 6036, UV multiset 100%, single uniform scale (anisotropy 1.0), rigid rotation/pivot only, one mesh 'overlay_2' (no children needed: the code looks up no anchors for this piece), material M_SubwayHoseOverlay_Tripo.
- Placement: rigid yaw -0.63 deg (back parallel to wall), uniform 4.0399 (top 3.949 under the 3.9686 ceiling), centred x, red cabinet back plane (raw y 0.072) at y=-1.98, base z=0; 2.90 x 0.74 x 3.95 m.
- Texture: raw 2048 basecolor JPEG -> overlay_2_tex/M_SubwayHoseOverlay_Tripo.png pixel-identical; overlay_2.tripo marker written; Unity creates _mat on import.
