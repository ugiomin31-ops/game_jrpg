# terrain/subway · lore_stone — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd6ee6-7754-83ee-8eff-234603e653db
Brief source: ArtSource/_briefs/environment.md, subway table, lore_stone = "A station information kiosk with a glowing blue touch screen (abstract map shapes)." Prop frame: README.md §Prompt frame (prop). Note: the brief row says "white kiosk + blue screen"; the steel base and grey keypad are an inferred detail from the subway set (steel).
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky toon environment prop for a stylised game set in a modern Seoul subway station: a station information kiosk in white with a glowing blue touch screen showing abstract map shapes (no letters), a steel base and a small grey keypad. Single object centered, three-quarter view from slightly above, the whole object visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI labels, no medieval or fantasy ornament, no skulls, no runes, no crowns, no gold filigree. Vary kiosk height, screen angle and base width within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_C.png. Reason: compact chunky kiosk with a large glowing blue map screen, steel base and keypad; B is tall and thin, D adds a thin side light strip. Alternative: candidate_A.png

## Tripo (B6-TRIPO-2, 2026-10-13, third account, quality-first)
- Picked image: candidate_C.png (pick line above), uploaded exactly.
- Generate: task 1e87567b-6159-4ec3-8f7b-fd271e64abfe. H3.1 Best Quality, Ultra Mesh on, Texture on, 4K (55), PBR on, Triangle. Cost 55, balance 1570 -> 1515.
- Retopo: Triangle + Smart Mesh on, polygon count shown 6000, cost 35, balance 1515 -> 1480. Actual faces 10641 (over target; the value did not reach the job, see ledger process note). Not re-paid; flagged.
- Export: FBX, Blender preset, texture 2k, static. Local: ArtSource/terrain/subway/lore_stone/tripo/tripo_convert_b7b9af4b-dae4-430d-8976-b00bda236f66.fbx (+ .fbm). Zip kept as futuristic+control+console+3d+model.zip.


### Installed 2026-10-13 (INSTALL-B6-2, Claude Sonnet, headless Blender, no credits)
- Assets/_Game/Resources/Art/Environment/subway/lore_stone.fbx replaced in place (GUID kept; old file+meta in ArtSource/_backup_20261013_b6_2/subway/). Raw Tripo geometry only: 10641 tris = raw 10641, UV multiset 100%, single uniform scale (anisotropy 1.0), rigid rotation/pivot only, one mesh 'lore_stone' (no children needed: the code looks up no anchors for this piece), material M_SubwayKiosk_Tripo.
- Placement: uniform 1.35; centred xy (half depth 0.51 < 0.65 left by AgainstWall 1.35), base z=0; screen faces -Y; 1.32 x 1.02 x 1.29 m.
- Texture: raw 2048 basecolor JPEG -> lore_stone_tex/M_SubwayKiosk_Tripo.png pixel-identical; lore_stone.tripo marker written; Unity creates _mat on import.
