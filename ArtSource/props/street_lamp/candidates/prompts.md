
## B3 candidates (ChatGPT web, GPT-6 Extra High, 2026-10-12, Haiku worker BROWSER-QUEUE 2b)
- Chat URL: https://chatgpt.com/c/6acbc00e-d434-83ee-87e4-0a5e3ebca9d6 (model GPT-6, reasoning slider 3/4 = Extra High, checked before sending)
- Prompt (lead + brief + weapon/object frame, from ArtSource/_briefs/B3_prompts.md): "Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One contemporary Seoul street lamp, sturdy upright steel pole, a compact curved attached arm and a thick sealed lamp head with an opaque warm-light underside, about 3.4 m tall, full object visible; no wires, separate pavement slab or transparent lens. Chunky clean stylized toon 3D game asset for a present-day Seoul Korean hunter RPG, thick attached parts, single solid object, entire object visible with generous margins, plain light grey background, soft studio light, no cast shadow, square 1:1. No hands, text, lettering, logos, numbers, runes, skulls, ornate gold, medieval decoration, floating effects, transparent parts or thin dangling parts. Vary proportions and colour accents between the four images while keeping the description."
- candidate_A.png: pass (preferred). Upright pole with a compact curved arm, round thick head with a warm-lit underside, no wires, no slab, plain background. Teal band accents.
- candidate_B.png: pass with note. Slender pole, longer arm than the brief's compact arm, rectangular head with a warm underside. The head looks slightly translucent at the edges.
- candidate_C.png: pass with note. Dome-shaped head with an opaque warm underside and a thick sealed look. Arm is more straight than curved.
- candidate_D.png: pass with note. Tapered pole, orange accents, rectangular head with warm underside, attached arm. Accent colour only; no wires or slab.
- Suggested pick: candidate_A.png (compact curved arm, thick sealed head). Runner-up: candidate_C.png. Main session makes the final pick. Height is not verified (no scale reference in the image).

## Tripo second account (2026-10-12, Haiku worker B3-TRIPO)
- Main final pick: candidate_A.png (main-approved pick)
- Source: https://studio.tripo3d.ai (Tripo Studio web, HD Model, Geometry & Texture, AI Model H3.1 - Best Quality, expected 55 credits)
- Task: 9739745d-37d1-4fee-9ec1-fb83c8e526d1  URL https://studio.tripo3d.ai/workspace/generate/9739745d-37d1-4fee-9ec1-fb83c8e526d1
- Generate cost: 55 credits; 2765 -> 2710

## Tripo second account (2026-10-12, Haiku worker B3-TRIPO)
- Main final pick: candidate_A.png (main-approved pick)
- Source: https://studio.tripo3d.ai (Tripo Studio web, HD Model, Geometry & Texture, H3.1 - Best Quality)
- Task: 9739745d-37d1-4fee-9ec1-fb83c8e526d1  URL https://studio.tripo3d.ai/workspace/generate/9739745d-37d1-4fee-9ec1-fb83c8e526d1
- Generate: 55 credits (2765 -> 2710)
- Retopo: Triangle, Smart Mesh on, target 3000 -> 2690 faces / 3473 vertices (cost 35; balance 2295 -> 2260). Slightly under the 3000 target, exported anyway per launcher rule.
- Rig: none.
- Export: FBX (Blender preset), texture 1k, no animations. Downloaded street+lamp+3d+model.zip (3.2 MB), extracted to tripo/.
- Export path: ArtSource/props/street_lamp/tripo/ (tripo_convert_*.fbx + .fbm)
- Credits spent on this asset: 90 (55+35).

## Installed 2026-10-12
Staged ArtSource/props/street_lamp/staging (street_lamp.fbx 2690 tris, M_StreetLamp_Tripo 1024 px, placement.json, .tripo): uniform scale 3.486, 3.4 m tall, origin = pole base centre, arm and head toward +X (head centre x 0.59, underside z 3.14, extent x -0.27..1.17, y +-0.34). Credits: 0 in this step. Backups: ArtSource/town/_backup_20261012b/ (town files + torch.fbx/.meta).
1. Town (Blender/town/tripo_pieces.json piece street_lamp, token street_lamp): replaces the three KayKit plaza lamps; instances Street_Lamp_1 (-11, 8.6, rot 0), Street_Lamp_2 (10.5, 8.6, rot 180), Street_Lamp_3 (-18, -9.5, rot 0). LightAnchor_street_01..03 keep name and x/y (the pole), z 4.1 -> 3.1 under the shorter head; they are empties, not baked. The festoon strings and their east pole follow the lower lamps (params festoon_z_end 3.3, festoon_pole_h 3.4, were 4.0 / 4.1). Texture Art/Town/town_tex/M_StreetLamp_Tripo.png; town.tripo updated.
2. Dungeon guild_street: torch is its own FBX (Assets/_Game/Resources/Art/Environment/guild_street/torch.fbx, built by hunter_kits_b/guild_street.py torch()). Replaced in place via Blender/lib/abyss_bpy.export_fbx (path_mode RELATIVE, same axis/scale as the other pieces: object rot 90 X, world z 0..3.4 on re-import), mesh name torch, empty LightAnchor at (0.589, 0, 3.1) under the head (not baked), torch.tripo marker written first, torch_tex/M_StreetLamp_Tripo.png, torch.fbx.meta unchanged. The guild_street.py source still builds the KayKit lamp (a regeneration would overwrite this FBX); the head arm now reaches 1.17 m along the wall and may clip the wall face by about 0.1 m.
Previews: scratchpad s16/ (town_old_/town_new_{lamp1,lamp3,festoon}.png, torch_old_vs_new.png). No Unity run, no commit.
