# bow_hunter candidates (batch B1, 2026-10-11)

Prompt (exact, sent once):
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One compact modern hunting compound bow, olive-drab riser, black limbs, thick attached cam discs at both tips and visibly thick connected strings/cables. Side three-quarter view shows the complete bow; no arrows, quiver, tiny open mechanisms or detached parts. Chunky clean stylized toon 3D game asset for a present-day Seoul Korean hunter RPG, thick attached parts, single solid object, entire object visible with generous margins, plain light grey background, soft studio light, no cast shadow, square 1:1. No hands, text, lettering, logos, numbers, runes, skulls, ornate gold, medieval decoration, floating effects, transparent parts or thin dangling parts. Vary proportions and colour accents between the four images while keeping the description.

Model: GPT-6, reasoning Extra High (slider 3 of 4) verified before sending.
Chat: https://chatgpt.com/c/6acb7c44-a8f8-83ee-9c11-2ffb162d1b9c
Images: 4 separate images, 1254x1254 PNG (square), no follow-up needed.

Per image:
- candidate_A.png: olive riser with cyan accent, black limbs, two thick cam discs, cables connected, bow reads well in three-quarter view.
- candidate_B.png: olive riser, orange accent bands on limb tips and cable collars, black limbs and cams.
- candidate_C.png: olive riser with navy accents, large cam discs, cables and cable guard blocks, clear silhouette.
- candidate_D.png: olive riser with red accent strips, cams and cables, slightly thinner riser.

Suggested pick (main decides): candidate_A.png. Reason: olive-drab riser dominates as the brief asks, black limbs and both thick cam discs read clearly, cables connected, cyan accent is the least busy.

Method note: copy-image via real thumbnail click then copy button; clipboard verified by sentinel and per-file checksum; all four files differ.

## B1-TRIPO (2026-10-11 21:53)
Main final pick: candidate_A.png (main-approved).
Source: studio.tripo3d.ai, H3.1 - Best Quality, same settings. Generate cost 55.
Tripo task: https://studio.tripo3d.ai/workspace/generate/75bbbc92-f657-45d2-9fa9-d62e7cf219f3
Status: generation submitted once. Retopo and export NOT yet done.

## B1-FINISH (2026-10-11, Haiku worker)
Retopo: Tripo Retopology (Triangle, Smart Mesh on), target 4500, verified slider 4500 and textbox 4500. First Triangle click after navigation did not register; re-clicked and verified data-state=on. Cost 35 credits. Balance before 845, after 810. Result faces 5433 (vertices 8486). Within small prop range (3k-6k).
Rig: none (weapon).
Export: FBX, texture 1k (dropdown set and verified), no skeleton toggle shown for non-rigged model, format preset Blender (default). No export cost shown.
Files: ArtSource/weapons/bow_hunter/tripo/tripo_convert_58954c68-2c4f-47a0-be3a-a28083d70015.fbx (+ .fbm, 5 maps). Source zip compound+bow+3d+model.zip, traversal check clean.
Tripo tab kept for next asset (closed after the next download).

Correction (B1-FINISH): the Tripo tab was closed right after the bow download, as required.

## Installed 2026-10-11
Installed by a Sonnet 5.5 worker with headless Blender 5.2 (build script in the session scratchpad s5/build.py). Source FBX: ArtSource/weapons/bow_hunter/tripo/tripo_convert_*.fbx (Tripo Studio H3.1 export, retopo 4500 target, 1k texture). Export settings = Blender/lib/abyss_bpy.py export_fbx (axis -Z/Y, FBX_SCALE_ALL, bake_space_transform, path_mode STRIP, MESH only). Meta kept untouched (GUID preserved: e1cc30d376396194a9b4cedf50639e92). Single material M_BowHunter_Tripo, base colour 1024 PNG at Assets/_Game/Resources/Art/Weapons/bow_hunter_tex/M_BowHunter_Tripo.png. Marker bow_hunter.tripo written first. Original FBX + meta in ArtSource/weapons/bow_hunter/backup_20261011/. No Tripo credits spent in this step.
- Result: 5433 tris (no decimation, under 6000; UVs untouched), bounds X -0.0508..0.0508, Y -0.2883..0.1734, Z -0.4895..0.4895 (old: X -0.033..0.0386, Y -0.0559..0.1579, Z -0.4895..0.4895). Uniform scale 1.0015 (Tripo 0.9775 m -> 0.979 m, same total length as the old bow).
- Axis layout copied from the old bow: limbs along Z, grip at origin (centre of the riser grip, x -0.0574 / z 0.4888 in the source), string on the -Y side, limb tips and riser toward +Y, thickness along X. Source draw plane was XZ with the string toward +X; measured yaw between grip and string was 0.0 deg, so the transform is a pure Rz(-90 deg). No lean to correct.
- Compound bow: cam discs and cables are in the mesh, so the new bow is deeper than the old recurve (Y span 0.46 m vs 0.21 m) because the length was matched; the string line sits at about Y -0.19 from the grip.
