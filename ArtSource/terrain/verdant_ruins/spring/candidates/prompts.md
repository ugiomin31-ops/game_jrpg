# verdant_ruins / spring

Brief: A clear spring pool with a cyan glowing ring.

Images: chatgpt.com (Chrome), GPT-6, reasoning Extra High (4th of 5, verified before the prompt), 2026-10-16. Saved via the page clipboard (ChatGPT downloads are blocked in this Chrome), pixels unchanged, re-encoded PNG.

## Prompt (sent once, verbatim)

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A clear spring pool with a cyan glowing ring. About 2.5 m across, low stone rim, water as a solid glossy surface, the ring a solid glowing band. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

## Pick: D

D: the cyan ring is a clear solid glowing band in a flat water surface inside a low stone rim; reads clearly as a heal spring and differs from decor_3's lily pool. A looks too much like decor_3, B and C have tall back stones. Blender: CHECK meshes 1 tris 3212 dims [(0.98, 0.96, 0.3)] images [('verdant_ruins_spring_basecolor', (2048, 2048)), ('verdant_ruins_spring_metallic', (1024, 1024)), ('verdant_ruins_spring_normal', (1024, 1024)), ('verdant_ruins_spring_roughness', (1024, 1024))]

## Tripo Studio

- Task id: `12089441-43a7-446a-92a4-32c75f99bed1`
- Image-to-3D: H3.1 Best Quality, Ultra Mesh Quality ON, Texture ON, Texture Quality 2K, PBR ON (Remove Lighting ON, default) — 45 cr
- Retopology: Triangle, Smart Mesh P1.0 ON, target 3500 → 3212 tris — 35 cr
- Export: FBX, Blender preset, texture 2k (free)
- Credits: 1850 before → 1770 after (80 spent)

## Files

- `tripo/verdant_ruins_spring.zip` (3,108,029 bytes, unchanged Tripo download)
  - `tripo_convert_56a33417-17be-4c35-ae07-3defded028f9.fbx` (133,100 B)
  - `tripo_convert_56a33417-17be-4c35-ae07-3defded028f9.fbm/verdant_ruins_spring_roughness.JPEG` (181,634 B)
  - `tripo_convert_56a33417-17be-4c35-ae07-3defded028f9.fbm/verdant_ruins_spring_normal.JPEG` (531,884 B)
  - `tripo_convert_56a33417-17be-4c35-ae07-3defded028f9.fbm/verdant_ruins_spring_basecolor.JPEG` (471,760 B)
  - `tripo_convert_56a33417-17be-4c35-ae07-3defded028f9.fbm/verdant_ruins_spring_metallic.JPEG` (322,334 B)
  - `tripo_convert_56a33417-17be-4c35-ae07-3defded028f9.fbm/verdant_ruins_spring_rm.PNG` (1,509,605 B)
- `candidates/` candidate_A.png, candidate_B.png, candidate_C.png, candidate_D.png

### Installed 2026-10-16
- spring.fbx: uniform x2.241, 2.20 x 2.15 x 0.67 m, 3212 tris (Tripo 3212), material M_VerdantSpring_Tripo; LightAnchor_spring at (0, 0, 1.2)
- Installed by `Blender/environment/tripo_props.py` into Assets/_Game/Resources/Art/Environment/verdant_ruins/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (base colour, 1024) written; Unity creates <piece>_mat. Raw Tripo zip and candidate images stay on branch tripo-glb-drop.
- Unity not run here: import/material creation and in-game facing still to be verified.
