# verdant_ruins / decor_1

Brief: A clump of ferns, ginkgo saplings and a few small green crystals.

Images: chatgpt.com (Chrome), GPT-6, reasoning Extra High (4th of 5, verified before the prompt), 2026-10-16. Saved via the page clipboard (ChatGPT downloads are blocked in this Chrome), pixels unchanged, re-encoded PNG.

## Prompt (sent once, verbatim)

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A clump of ferns, ginkgo saplings and a few small green crystals. Freestanding, footprint under 1.5 m, plants as chunky solid leaf clusters (no thin strands). Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

## Pick: A

A: low wide clump with a solid rock base, short ginkgo saplings and crystals tucked in at the base; most compact, chunky silhouette. B/C/D have taller thin sapling trunks or a tall slab that would thin out in retopo. Blender check: 1 mesh, 3073 tris, 0.98 x 0.89 x 0.61, basecolor 2048 + metallic/normal/roughness 1024.

## Tripo Studio

- Task id: `4c4fb0a5-ab48-4e58-b33e-b9e2a58ded16`
- Image-to-3D: H3.1 Best Quality, Ultra Mesh Quality ON, Texture ON, Texture Quality 2K, PBR ON (Remove Lighting ON, default) — 45 cr
- Retopology: Triangle, Smart Mesh P1.0 ON, target 3500 → 3073 tris — 35 cr
- Export: FBX, Blender preset, texture 2k (free)
- Credits: 2490 before → 2410 after (80 spent)

## Files

- `tripo/verdant_ruins_decor_1.zip` (3,159,062 bytes, unchanged Tripo download)
  - `tripo_convert_4cf0d701-050b-4547-a205-2551038a1dd8.fbx` (135,820 B)
  - `tripo_convert_4cf0d701-050b-4547-a205-2551038a1dd8.fbm/verdant_ruins_decor_1_basecolor.JPEG` (441,795 B)
  - `tripo_convert_4cf0d701-050b-4547-a205-2551038a1dd8.fbm/verdant_ruins_decor_1_metallic.JPEG` (360,427 B)
  - `tripo_convert_4cf0d701-050b-4547-a205-2551038a1dd8.fbm/verdant_ruins_decor_1_roughness.JPEG` (143,893 B)
  - `tripo_convert_4cf0d701-050b-4547-a205-2551038a1dd8.fbm/verdant_ruins_decor_1_rm.PNG` (1,456,300 B)
  - `tripo_convert_4cf0d701-050b-4547-a205-2551038a1dd8.fbm/verdant_ruins_decor_1_normal.JPEG` (663,142 B)
- `candidates/` candidate_A.png, candidate_B.png, candidate_C.png, candidate_D.png

### Installed 2026-10-16
- decor_1.fbx: uniform x1.430, 1.40 x 1.27 x 0.87 m, 3073 tris (Tripo 3073), material M_VerdantDecor1_Tripo
- Installed by `Blender/environment/tripo_props.py` into Assets/_Game/Resources/Art/Environment/verdant_ruins/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (base colour, 1024) written; Unity creates <piece>_mat. Raw Tripo zip and candidate images stay on branch tripo-glb-drop.
- Unity not run here: import/material creation and in-game facing still to be verified.
