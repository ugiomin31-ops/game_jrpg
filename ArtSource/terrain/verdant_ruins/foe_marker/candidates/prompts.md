# verdant_ruins / foe_marker

Brief: A floor ring of moss with a floating orange gate crystal.

Images: chatgpt.com (Chrome), GPT-6, reasoning Extra High (4th of 5, verified before the prompt), 2026-10-16. Saved via the page clipboard (ChatGPT downloads are blocked in this Chrome), pixels unchanged, re-encoded PNG.

## Prompt (sent once, verbatim)

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A floor ring of moss with a floating orange gate crystal. Ring about 2 m across; the crystal is attached to the ring by a solid glow column (nothing floating free). Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

## Pick: B

B: low ring of mossy stone with the orange crystal held in a stone cradle on a solid glow column (nothing floating). A and C add tall side stones; D's standing arches look like the warp piece. Blender: CHECK meshes 1 tris 3390 dims [(0.98, 0.96, 0.76)] images [('verdant_ruins_foe_marker_basecolor', (2048, 2048)), ('verdant_ruins_foe_marker_metallic', (1024, 1024)), ('verdant_ruins_foe_marker_normal', (1024, 1024)), ('verdant_ruins_foe_marker_roughness', (1024, 1024))]

## Tripo Studio

- Task id: `c1331484-2d7d-49b7-a450-c897ef456e85`
- Image-to-3D: H3.1 Best Quality, Ultra Mesh Quality ON, Texture ON, Texture Quality 2K, PBR ON (Remove Lighting ON, default) — 45 cr
- Retopology: Triangle, Smart Mesh P1.0 ON, target 3500 → 3390 tris — 35 cr
- Export: FBX, Blender preset, texture 2k (free)
- Credits: 1530 before → 1450 after (80 spent)

## Files

- `tripo/verdant_ruins_foe_marker.zip` (2,956,765 bytes, unchanged Tripo download)
  - `tripo_convert_208ccd66-9ae9-49cc-88e0-7dcd844c0ee1.fbx` (141,548 B)
  - `tripo_convert_208ccd66-9ae9-49cc-88e0-7dcd844c0ee1.fbm/verdant_ruins_foe_marker_roughness.JPEG` (97,868 B)
  - `tripo_convert_208ccd66-9ae9-49cc-88e0-7dcd844c0ee1.fbm/verdant_ruins_foe_marker_normal.JPEG` (612,427 B)
  - `tripo_convert_208ccd66-9ae9-49cc-88e0-7dcd844c0ee1.fbm/verdant_ruins_foe_marker_rm.PNG` (1,309,992 B)
  - `tripo_convert_208ccd66-9ae9-49cc-88e0-7dcd844c0ee1.fbm/verdant_ruins_foe_marker_metallic.JPEG` (301,494 B)
  - `tripo_convert_208ccd66-9ae9-49cc-88e0-7dcd844c0ee1.fbm/verdant_ruins_foe_marker_basecolor.JPEG` (534,063 B)
- `candidates/` candidate_A.png, candidate_B.png, candidate_C.png, candidate_D.png

### Installed 2026-10-16
- foe_marker.fbx: uniform x2.044, 2.00 x 1.95 x 1.55 m, 3390 tris (Tripo 3390), material M_VerdantFoeMarker_Tripo; Spot_foe at (0, 0, 0)
- Installed by `Blender/environment/tripo_props.py` into Assets/_Game/Resources/Art/Environment/verdant_ruins/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (base colour, 1024) written; Unity creates <piece>_mat. Raw Tripo zip and candidate images stay on branch tripo-glb-drop.
- Unity not run here: import/material creation and in-game facing still to be verified.
