# terrain/subway · overlay_1 — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd7017-c664-83ec-a40c-b0d325060ec5
Brief source: ArtSource/_briefs/environment.md, subway table, overlay_1 = "A violet gate crack running up a tiled wall with fallen tile rubble at the base." Overlay rules (environment.md): wall decal that hugs the -Y face of a wall block, flat-backed, up to ~4.4 m tall; the image shows a flat decal panel.
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One flat decal panel for a stylised game set in a modern Seoul subway station, to be stuck flat on a tiled wall face: a violet gate crack running up a white tiled wall in a jagged line from the floor, with a few pieces of fallen cream tile rubble lying at its base. Flat-backed, the decal is a relief panel no deeper than a few centimetres, the crack a matte violet-tinted groove, no glow. Full panel visible with margins, straight-on front view with a slight three-quarter tilt, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no medieval or fantasy ornament, no skulls, no runes, no crowns, no gold filigree. Vary crack width, rubble amount and panel height within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_D.png. Reason: thinnest flat slab decal with a single jagged violet crack from floor to top and cream tile rubble at the base; C has branching crack lines that will be thin in retopo. Alternative: candidate_C.png

## Tripo (B6-TRIPO-2, 2026-10-13, third account, quality-first)
- Picked image: candidate_D.png (pick line above), uploaded exactly.
- Generate: task 2416f6a1-525d-4ffb-8181-29ccb878f723. H3.1 Best Quality, Ultra Mesh on, Texture on, 4K (55), PBR on, Triangle. Cost 55, balance 1300 -> 1245.
- Retopo: Triangle + Smart Mesh on, 6000 (verified by zoom before click), cost 35, balance 1245 -> 1210. Actual faces 5663.
- Export: FBX, Blender preset, texture 2k, static. Local: ArtSource/terrain/subway/overlay_1/tripo/tripo_convert_87246246-a9d3-4bc6-a8cc-1572b980d4d8.fbx (+ .fbm). Zip kept as cracked+wall+3d+model.zip.


### Installed 2026-10-13 (INSTALL-B6-2, Claude Sonnet, headless Blender, no credits)
- Assets/_Game/Resources/Art/Environment/subway/overlay_1.fbx replaced in place (GUID kept; old file+meta in ArtSource/_backup_20261013_b6_2/subway/). Raw Tripo geometry only: 5663 tris = raw 5663, UV multiset 100%, single uniform scale (anisotropy 1.0), rigid rotation/pivot only, one mesh 'overlay_1' (no children needed: the code looks up no anchors for this piece), material M_SubwayCrackOverlay_Tripo.
- Placement: rigid yaw +7.44 deg so the flat back is parallel to the wall (Tripo baked a 3/4 tilt), uniform 4.0285 (fits wall height 3.9686: top at 3.949), centred x, flat back plane at y=-1.98 (2 cm into the wall face), base z=0; front -Y; 1.82 x 0.63 x 3.95 m.
- Texture: raw 2048 basecolor JPEG -> overlay_1_tex/M_SubwayCrackOverlay_Tripo.png pixel-identical; overlay_1.tripo marker written; Unity creates _mat on import.
