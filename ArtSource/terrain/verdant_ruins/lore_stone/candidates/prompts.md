# verdant_ruins / lore_stone

Brief: A mossy stone stele with a glowing green rift line.

Images: chatgpt.com (Chrome), GPT-6, reasoning Extra High (4th of 5, verified before the prompt), 2026-10-16. Saved via the page clipboard (ChatGPT downloads are blocked in this Chrome), pixels unchanged, re-encoded PNG.

## Prompt (sent once, verbatim)

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A mossy stone stele with a glowing green rift line. About 2 m tall, the rift line a solid glowing groove (abstract, no runes or letters). Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

## Pick: D

D: clean stele slab on a stepped pedestal with one wide solid glowing S-groove (abstract, no runes). B's glow is a thin branching crack, A a crack in a natural rock, C adds side pillars. Blender: CHECK meshes 1 tris 3554 dims [(0.56, 0.58, 0.98)] images [('verdant_ruins_lore_stone_basecolor', (2048, 2048)), ('verdant_ruins_lore_stone_metallic', (1024, 1024)), ('verdant_ruins_lore_stone_normal', (1024, 1024)), ('verdant_ruins_lore_stone_roughness', (1024, 1024))]

## Tripo Studio

- Task id: `b8550be4-8319-4012-8ddd-da2e2c7d236a`
- Image-to-3D: H3.1 Best Quality, Ultra Mesh Quality ON, Texture ON, Texture Quality 2K, PBR ON (Remove Lighting ON, default) — 45 cr
- Retopology: Triangle, Smart Mesh P1.0 ON, target 3500 → 3554 tris — 35 cr
- Export: FBX, Blender preset, texture 2k (free)
- Credits: 1930 before → 1850 after (80 spent)

## Files

- `tripo/verdant_ruins_lore_stone.zip` (3,178,769 bytes, unchanged Tripo download)
  - `tripo_convert_6453f942-0a3d-45b4-849f-2d7644d69eeb.fbx` (148,572 B)
  - `tripo_convert_6453f942-0a3d-45b4-849f-2d7644d69eeb.fbm/verdant_ruins_lore_stone_rm.PNG` (1,398,841 B)
  - `tripo_convert_6453f942-0a3d-45b4-849f-2d7644d69eeb.fbm/verdant_ruins_lore_stone_roughness.JPEG` (129,476 B)
  - `tripo_convert_6453f942-0a3d-45b4-849f-2d7644d69eeb.fbm/verdant_ruins_lore_stone_basecolor.JPEG` (566,420 B)
  - `tripo_convert_6453f942-0a3d-45b4-849f-2d7644d69eeb.fbm/verdant_ruins_lore_stone_normal.JPEG` (610,226 B)
  - `tripo_convert_6453f942-0a3d-45b4-849f-2d7644d69eeb.fbm/verdant_ruins_lore_stone_metallic.JPEG` (361,456 B)
- `candidates/` candidate_A.png, candidate_B.png, candidate_C.png, candidate_D.png

### Installed 2026-10-16
- lore_stone.fbx: uniform x2.046, 1.15 x 1.19 x 2.00 m, 3554 tris (Tripo 3554), material M_VerdantLoreStone_Tripo
- Installed by `Blender/environment/tripo_props.py` into Assets/_Game/Resources/Art/Environment/verdant_ruins/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (base colour, 1024) written; Unity creates <piece>_mat. Raw Tripo zip and candidate images stay on branch tripo-glb-drop.
- Unity not run here: import/material creation and in-game facing still to be verified.
