# door_locked (subway P1) — ChatGPT web candidates, 2026-10-12

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High).
Chat: https://chatgpt.com/c/6acc878e-efc4-83ee-a2ad-9099871e2520
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. A white station frame around a closed steel-framed screen door with a compact access lock. View: straight front. One chunky stylised present-day Seoul subway game asset, restrained cream tile, stainless steel, line-green and navy accents, slightly worn but readable, plain neutral background, whole asset visible, square image. No people, letters, numbers, logos or medieval motifs; screens and windows opaque.

Note: this was generated before wall_base, floor_base and stairs_up (the brief lists them earlier). Order differs from the brief, the set is complete for this entry.

Results (one response, 4 images, all straight front):
- candidate_A.png: wide cream frame with green/navy bands; steel double doors with opaque dark-blue-grey panels and green band; compact lock on the right. Frame is wider than tall.
- candidate_B.png: taller cream tile frame with green band top and navy base; steel double doors, dark panels with a green band; compact lock right. Proportion closest to the 4 x 4.5 m frame.
- candidate_C.png: cream frame with green top band; steel doors with frosted-grey panels, green and navy bands; lock right.
- candidate_D.png: cream frame with green/navy bands on a dark grey backdrop; steel doors with frosted-grey panels, green and navy bands; lock right.

Suggested pick: candidate_B.png. Reason: tall cream station frame with steel double doors and a compact lock; proportion matches the briefed 4 x 4.5 m frame. candidate_A is the alternative.

## Tripo (B5-TRIPO-2, 2026-10-12, third account)
- Image uploaded: candidates/candidate_B.png (the suggested pick above).
- Image-to-3D: studio.tripo3d.ai web, AI Model H3.1 Best Quality, Geometry & Texture: Ultra Mesh Quality on, Texture on, Texture Quality 2K, PBR on. Generate cost 45. Task id: ee7779e3-4a9c-48a5-8c28-75df49ff8c2b
- Balance: 3380 -> 3335
- Retopology: Topology Triangle, Smart Mesh on, polygon count 3000 target, result 2625 faces (binary count). Cost 35. Balance: 3335 -> 3300
- Export: FBX, Blender preset, texture 2k. Local file: ArtSource/terrain/subway/door_locked/tripo/tripo_convert_534bb8c6-d5f6-421f-8f1a-9c5d1cf68af0.fbx (+ adjacent .fbm)

### Installed 2026-10-13 (B5-INSTALL-2)
- door_locked.fbx: tiled frame + steel double door. Frame = Tripo mesh scaled x5.923 / y5.2 / z4.603 to x [-2, 2], y [-0.632, 0.632], z [0, 4.5] (the frame must fill the cell width, otherwise the corridor is visible beside it). The opening was cut out of the Tripo mesh (bisected at x = +-0.238, z = 0.7235 in source units, recessed door slab and everything behind it deleted, flat lining quads added for both jambs and the lintel with the plain frame colour UV), so the passage is open. Opening x [-1.41, 1.41], height 3.33 m.
- Child object `Door` (the only name DungeonWorld.Initialize looks up, via EnvironmentProcessor.Find(door.transform, "Door")): the recessed door-front faces (175 tris, glass panels + frame bars) duplicated 0.10 m behind and flipped (two-sided thin leaf, 422 tris), object origin = hinge at the -X jamb (x -1.41, z 0), it opens with localRotation Euler(0, 95, 0) as before. Frame object name `door_locked`. 3404 tris in total (frame 2982 + leaf 422; budget 4000).
- NOT recreated: the old child `Lock` (emissive green/red indicator quads parented to the leaf); no code looks it up (grep "Lock" in Assets/_Game/Scripts: only DoorLocked effect enum). The Tripo keypad box is part of the frame.
- Material M_SubwayDoor_Tripo (1024 px).
- Installed 2026-10-13 (B5-INSTALL-2) into Assets/_Game/Resources/Art/Environment/subway/ ; original + .fbx.meta backed up in ArtSource/terrain/subway/_backup_20261012/ ; .fbx.meta (GUID) untouched ; <piece>.tripo marker + <piece>_tex/<material>.png (1024 px) written; Unity creates <piece>_mat. Export: Blender/lib/abyss_bpy.export_fbx, path_mode RELATIVE, force=True. Shared single material name, no .001 duplicates. Unity not run by this worker: import/material creation and in-game facing still to be verified.

### RESTORE-SUBWAY (2026-10-13, Claude Sonnet)
STAGED, NOT INSTALLED. Staged stage/subway/door_locked.fbx = raw geometry, uniform scale 4.602965, Door (404 tris: existing front-leaf faces + rear skin faces) + frame 2221 = 2625 = raw, UV 100%, raw 2048 texture. Fidelity PASS, functional FAIL: raw geometry fuses the glass panes into the frame, so rotating Door about the hinge (Blender (-1.202,-0.0385,0) -> Unity (-1.202,0,+0.0385)) leaves jagged shards in the opening (renders/door4_sheet.png). Not shipped; current installed door kept. 0 credits.
