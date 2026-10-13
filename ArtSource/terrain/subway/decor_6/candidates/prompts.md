# terrain/subway · decor_6 — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd6e60-115c-83e8-9d30-71ea09579c9c
Brief source: ArtSource/_briefs/environment.md, subway table, decor_6 = "A white tiled column with two line-colour bands and a round navy station-number sign on top (number shape, no letters)." Prop frame: README.md §Prompt frame (prop).
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky toon environment prop for a stylised game set in a modern Seoul subway station: a tall white tiled column with two green and blue line-colour bands and a round navy station-number sign on top showing only an abstract number shape (no letters). Single object centered, three-quarter view from slightly above, the whole object visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no medieval or fantasy ornament, no skulls, no runes, no crowns, no gold filigree. Vary column width, band positions and sign size within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_C.png. Reason: round tiled column with blue and green bands and an abstract, non-numeral navy sign; A, B and D show a readable '3'. Alternative: candidate_A.png

## Tripo (B6-TRIPO-2, 2026-10-13, third account, quality-first)
- Picked image: candidate_C.png (pick line above). Uploaded exactly this PNG.
- Generate: studio.tripo3d.ai/workspace/generate, task 7a26eda6-48c1-40cf-963a-19bc89c0c05b. H3.1 Best Quality, Geometry & Texture panel: Ultra Mesh Quality on, Texture on, Texture Quality 4K (button 55), PBR on, Topology Triangle. Cost 55, balance 1660 -> 1605.
- Retopo: Triangle + Smart Mesh on, polygon count 6000 entered, cost 35, balance 1605 -> 1570. Actual faces 9025 (over the 3k-6k small-prop target; not re-retopologized to avoid a second paid step).
- Export: FBX, Blender preset, texture 2k, static, no rig. Settled 2026-10-13 13:26.
- Local files: ArtSource/terrain/subway/decor_6/tripo/tripo_convert_d79f52be-bdb6-4deb-b0d9-6f3869a291b9.fbx (+ .fbm with five maps). Source zip kept as gas+cylinder+3d+model.zip.


### Installed 2026-10-13 (INSTALL-B6-2, Claude Sonnet, headless Blender, no credits)
- Assets/_Game/Resources/Art/Environment/subway/decor_6.fbx replaced in place (GUID kept; old file+meta in ArtSource/_backup_20261013_b6_2/subway/). Raw Tripo geometry only: 9025 tris = raw 9025, UV multiset 100%, single uniform scale (anisotropy 1.0), rigid rotation/pivot only, one mesh 'decor_6' (no children needed: the code looks up no anchors for this piece), material M_SubwayPillar_Tripo.
- Placement: uniform 2.46; centred xy, base z=0; 0.61 x 0.61 x 2.40 m (old pillar 0.6 x 2.16).
- Texture: raw 2048 basecolor JPEG -> decor_6_tex/M_SubwayPillar_Tripo.png pixel-identical; decor_6.tripo marker written; Unity creates _mat on import.
