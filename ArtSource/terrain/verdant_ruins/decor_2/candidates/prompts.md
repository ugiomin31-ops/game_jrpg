# verdant_ruins / decor_2

Brief: A broken mossy stone column with a fallen fluted drum beside it.

Images: chatgpt.com (Chrome), GPT-6, reasoning Extra High (4th of 5, verified before the prompt), 2026-10-16. Saved via the page clipboard (ChatGPT downloads are blocked in this Chrome), pixels unchanged, re-encoded PNG.

## Prompt (sent once, verbatim)

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A broken mossy stone column with a fallen fluted drum beside it. Freestanding, column about 2 m tall, footprint under 2 m. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

## Pick: A

A: chunky fluted column on a stepped block base with the fallen drum leaning against it; ivy hugs the stone, few dangling strands. B and C have long hanging vines, D a tall thin broken top. Blender check: 1 mesh, 3497 tris, 0.98 x 0.88 x 0.95, basecolor 2048 + metallic/normal/roughness 1024.

## Tripo Studio

- Task id: `25701ba6-0f08-4e08-af32-1b873f91e5b4`
- Image-to-3D: H3.1 Best Quality, Ultra Mesh Quality ON, Texture ON, Texture Quality 2K, PBR ON (Remove Lighting ON, default) — 45 cr
- Retopology: Triangle, Smart Mesh P1.0 ON, target 3500 → 3497 tris — 35 cr
- Export: FBX, Blender preset, texture 2k (free)
- Credits: 2410 before → 2330 after (80 spent)

## Files

- `tripo/verdant_ruins_decor_2.zip` (3,096,503 bytes, unchanged Tripo download)
  - `tripo_convert_857428a7-bcdc-4abd-be3c-41eafc6315df.fbx` (148,316 B)
  - `tripo_convert_857428a7-bcdc-4abd-be3c-41eafc6315df.fbm/verdant_ruins_decor_2_rm.PNG` (1,428,208 B)
  - `tripo_convert_857428a7-bcdc-4abd-be3c-41eafc6315df.fbm/verdant_ruins_decor_2_metallic.JPEG` (307,438 B)
  - `tripo_convert_857428a7-bcdc-4abd-be3c-41eafc6315df.fbm/verdant_ruins_decor_2_roughness.JPEG` (150,308 B)
  - `tripo_convert_857428a7-bcdc-4abd-be3c-41eafc6315df.fbm/verdant_ruins_decor_2_basecolor.JPEG` (511,900 B)
  - `tripo_convert_857428a7-bcdc-4abd-be3c-41eafc6315df.fbm/verdant_ruins_decor_2_normal.JPEG` (592,060 B)
- `candidates/` candidate_A.png, candidate_B.png, candidate_C.png, candidate_D.png

### Installed 2026-10-16
- decor_2.fbx: uniform x1.639, 1.60 x 1.44 x 1.56 m, 3497 tris (Tripo 3497), material M_VerdantDecor2_Tripo
- Installed by `Blender/environment/tripo_props.py` into Assets/_Game/Resources/Art/Environment/verdant_ruins/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (base colour, 1024) written; Unity creates <piece>_mat. Raw Tripo zip and candidate images stay on branch tripo-glb-drop.
- Unity not run here: import/material creation and in-game facing still to be verified.
