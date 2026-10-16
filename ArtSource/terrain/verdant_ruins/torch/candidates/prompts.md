# verdant_ruins / torch

Brief: A stone post brazier with a warm flame.

Images: chatgpt.com (Chrome), GPT-6, reasoning Extra High (4th of 5, verified before the prompt), 2026-10-16. Saved via the page clipboard (ChatGPT downloads are blocked in this Chrome), pixels unchanged, re-encoded PNG.

## Prompt (sent once, verbatim)

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A stone post brazier with a warm flame. About 1.8 m tall, the flame a chunky solid stylised shape attached to the bowl. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

## Pick: A

A: sturdy square post on a wide stepped base with a chunky solid flame filling the bowl; most stable silhouette. D has loose sparks and thin prongs, B a slender column with hanging vines, C thin prongs round the bowl. Blender: CHECK meshes 1 tris 3394 dims [(0.45, 0.5, 0.98)] images [('verdant_ruins_torch_basecolor', (2048, 2048)), ('verdant_ruins_torch_metallic', (1024, 1024)), ('verdant_ruins_torch_normal', (1024, 1024)), ('verdant_ruins_torch_roughness', (1024, 1024))]

## Tripo Studio

- Task id: `104cb8ff-cf02-43b7-b3e3-1ae61ffd5752`
- Image-to-3D: H3.1 Best Quality, Ultra Mesh Quality ON, Texture ON, Texture Quality 2K, PBR ON (Remove Lighting ON, default) — 45 cr
- Retopology: Triangle, Smart Mesh P1.0 ON, target 3500 → 3394 tris — 35 cr
- Export: FBX, Blender preset, texture 2k (free)
- Credits: 1770 before → 1690 after (80 spent)

## Files

- `tripo/verdant_ruins_torch.zip` (3,063,030 bytes, unchanged Tripo download)
  - `tripo_convert_50a1cdf2-1db7-4572-b368-70d4e817833f.fbx` (140,988 B)
  - `tripo_convert_50a1cdf2-1db7-4572-b368-70d4e817833f.fbm/verdant_ruins_torch_metallic.JPEG` (311,515 B)
  - `tripo_convert_50a1cdf2-1db7-4572-b368-70d4e817833f.fbm/verdant_ruins_torch_rm.PNG` (1,373,581 B)
  - `tripo_convert_50a1cdf2-1db7-4572-b368-70d4e817833f.fbm/verdant_ruins_torch_normal.JPEG` (582,272 B)
  - `tripo_convert_50a1cdf2-1db7-4572-b368-70d4e817833f.fbm/verdant_ruins_torch_basecolor.JPEG` (578,081 B)
  - `tripo_convert_50a1cdf2-1db7-4572-b368-70d4e817833f.fbm/verdant_ruins_torch_roughness.JPEG` (116,459 B)
- `candidates/` candidate_A.png, candidate_B.png, candidate_C.png, candidate_D.png

### Installed 2026-10-16
- torch.fbx: uniform x1.842, 0.83 x 0.92 x 1.80 m, 3394 tris (Tripo 3394), material M_VerdantTorch_Tripo; LightAnchor at (-0.01, -0.18, 1.6)
- Installed by `Blender/environment/verdant_ruins/install_tripo.py` into Assets/_Game/Resources/Art/Environment/verdant_ruins/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (base colour, 1024) written; Unity creates <piece>_mat. Raw Tripo zip and candidate images stay on branch tripo-glb-drop.
- Unity not run here: import/material creation and in-game facing still to be verified.
