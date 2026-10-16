# verdant_ruins / overlay_1

Brief: Ivy and flowering vines hanging from the wall top.

Images: chatgpt.com (Chrome), GPT-6, reasoning Extra High (4th of 5, verified before the prompt), 2026-10-16. Saved via the page clipboard (ChatGPT downloads are blocked in this Chrome), pixels unchanged, re-encoded PNG.

## Prompt (sent once, verbatim)

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One wall decal panel for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): Ivy and flowering vines hanging from the wall top. One flat decal panel to be stuck on a 4 m wide stone wall face: vines hang from the top edge down about two thirds. Flat-backed, relief no deeper than a few centimetres. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

## Pick: A (top-left variant)

ChatGPT ignored 'separate images' and returned four 2x2 contact sheets (16 variants, candidate_A..D are the sheets). Picked the top-left variant of sheet A, cropped to 627px (candidate_A_topleft_pick.png, sent to Tripo): flat wall face with ivy and white-flowered vines hanging about two thirds down from the top edge. Note: the result includes the stone wall slab itself, not vines alone; trim the back in Blender if a vine-only decal is needed. Blender: CHECK meshes 1 tris 3753 dims [(0.98, 0.17, 0.66)] images [('verdant_ruins_overlay_1_basecolor', (2048, 2048)), ('verdant_ruins_overlay_1_metallic', (1024, 1024)), ('verdant_ruins_overlay_1_normal', (1024, 1024)), ('verdant_ruins_overlay_1_roughness', (1024, 1024))]

## Tripo Studio

- Task id: `b277d098-282c-44b1-b83b-49ef5d27ca7e`
- Image-to-3D: H3.1 Best Quality, Ultra Mesh Quality ON, Texture ON, Texture Quality 2K, PBR ON (Remove Lighting ON, default) — 45 cr
- Retopology: Triangle, Smart Mesh P1.0 ON, target 3500 → 3753 tris — 35 cr
- Export: FBX, Blender preset, texture 2k (free)
- Credits: 1450 before → 1370 after (80 spent)

## Files

- `tripo/verdant_ruins_overlay_1.zip` (3,075,551 bytes, unchanged Tripo download)
  - `tripo_convert_5234248a-ac10-4cd9-9b4b-f029e890b8af.fbx` (172,236 B)
  - `tripo_convert_5234248a-ac10-4cd9-9b4b-f029e890b8af.fbm/verdant_ruins_overlay_1_roughness.JPEG` (86,834 B)
  - `tripo_convert_5234248a-ac10-4cd9-9b4b-f029e890b8af.fbm/verdant_ruins_overlay_1_basecolor.JPEG` (516,675 B)
  - `tripo_convert_5234248a-ac10-4cd9-9b4b-f029e890b8af.fbm/verdant_ruins_overlay_1_rm.PNG` (1,326,077 B)
  - `tripo_convert_5234248a-ac10-4cd9-9b4b-f029e890b8af.fbm/verdant_ruins_overlay_1_normal.JPEG` (696,430 B)
  - `tripo_convert_5234248a-ac10-4cd9-9b4b-f029e890b8af.fbm/verdant_ruins_overlay_1_metallic.JPEG` (322,503 B)
- `candidates/` candidate_A.png, candidate_A_topleft_pick.png, candidate_B.png, candidate_C.png, candidate_D.png

### Installed 2026-10-16
- overlay_1.fbx: uniform x3.985, 3.90 x 0.30 x 2.65 m, 3753 tris (Tripo 3753), material M_VerdantOverlay1_Tripo; relief squashed x0.45; wall decal, back on y -2.0, anchored at the floor
- Tripo modelled the whole mossy wall panel (pillars, stone face, ivy) rather than vines alone, so it is installed as a floor-standing facade 3.9 m wide on the wall block's -Y face (y -2.0 … -2.3), not hung from the wall top.
- Installed by `Blender/environment/tripo_props.py` into Assets/_Game/Resources/Art/Environment/verdant_ruins/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (base colour, 1024) written; Unity creates <piece>_mat. Raw Tripo zip and candidate images stay on branch tripo-glb-drop.
- Unity not run here: import/material creation and in-game facing still to be verified.
