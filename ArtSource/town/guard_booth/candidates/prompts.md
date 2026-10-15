# guard_booth candidates (batch B1, 2026-10-11)

Prompt (exact, sent once; the brief's "front three-quarter view, whole structure visible" line is from the header of B1_prompts.md, placed before the frame; the multiplication sign in "1.6 × 1.6 m" is kept as written in the brief):
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One closed white-and-navy security booth, about 1.6 × 1.6 m and 2 m tall with a slightly wider flat roof, opaque painted windows and a thick attached roof light. No interior. Front three-quarter view, whole structure visible. Chunky clean stylized toon 3D game asset for a present-day Seoul Korean hunter RPG, thick attached parts, single solid object, entire object visible with generous margins, plain light grey background, soft studio light, no cast shadow, square 1:1. No hands, text, lettering, logos, numbers, runes, skulls, ornate gold, medieval decoration, floating effects, transparent parts or thin dangling parts. Vary proportions and colour accents between the four images while keeping the description.

Model: GPT-6, reasoning Extra High (slider 3 of 4) verified before sending.
Chat: https://chatgpt.com/c/6acb816f-a7f8-83ee-9048-34b65ea6bb67
Images: 4 separate images, 1254x1254 PNG (square), no follow-up needed.

Per image:
- candidate_A.png: white walls with navy frames, navy roof band with white edge, thick roof light attached under the roof, opaque navy windows, closed door. Roof only slightly wider than walls.
- candidate_B.png: navy roof with a wide overhang, white walls, navy base, roof light attached. Overhang is wider than "slightly".
- candidate_C.png: white walls, navy base and roof, teal-grey window strips, roof light attached, opaque windows. Clean.
- candidate_D.png: white upper walls, navy lower panels with teal trim, navy roof, roof light attached. Lower panels add extra detail.

Suggested pick (main decides): candidate_A.png. Reason: closest to "slightly wider flat roof" with a thick attached roof light, opaque painted windows and a closed door, plain white-and-navy colour split, clean silhouette.

Method note: copy via real click on the thumbnail, then real click on the image copy button (bottom-left of the response). Clipboard checked per file; all four files differ.

## B1-TRIPO (2026-10-11 21:53)
Main final pick: candidate_A.png (main-approved).
Source: studio.tripo3d.ai, H3.1 - Best Quality, same settings. Generate cost 55.
Tripo task: https://studio.tripo3d.ai/workspace/generate/0bd1c210-b6ff-4d49-8cdd-ecb914d413c1
Status: generation submitted once. Retopo and export NOT yet done.

## B1-FINISH (2026-10-11, Haiku worker)
Retopo: Tripo Retopology (Triangle, Smart Mesh on), target 3000, verified textbox 3000 (slider reads 3000 after set). Triangle set via DOM click after coordinate clicks did not register. Retopo button first coordinate click did not register (balance unchanged at 670, verified), second coordinate click registered once (balance 670 -> 635). Cost 35 credits total. Balance before 670, after 635. Result faces 2888 (vertices 3637). Within about 4% of target 3000.
Rig: none (booth).
Export: FBX, texture 1k (set and verified), no skeleton toggle for non-rigged model, format preset Blender (default). No export cost shown.
Files: ArtSource/town/guard_booth/tripo/tripo_convert_7146a206-0d20-4691-a484-53a107a86278.fbx (+ .fbm, 5 maps). Source zip security+booth+3d+model.zip, traversal check clean.
Tripo tab closed after download.

## Staged 2026-10-11 (B1-TOWN-INSTALL, NOT installed)
The town is ONE combined FBX (Assets/_Game/Resources/Art/Town/town.fbx, loaded as a single prefab by ArtLibrary.TownPath / TownWorld.Initialize; Blender/town/guild.py bakes every building into it via MB().build()). There is no separate per-piece FBX or .meta to replace, so the combined file was left untouched. Cleaned piece staged in ArtSource/town/guard_booth/staging/: guard_booth.fbx, guard_booth.tripo (marker), guard_booth_tex/M_GuardBooth_Tripo.png (1024x1024 base colour), placement.json.
Staged mesh: 2888 triangles (source 2888, geometry unchanged), single material M_GuardBooth_Tripo, uniform scale 2.2492 (rotated 0 deg about Z), origin = footprint bbox centre at ground level. Bounds metres (Blender, Z up): min [-0.919, -0.893, 0.0] max [0.919, 0.893, 2.2], size 1.84 x 1.79 x 2.20.
Intended placement (Blender metres): [[-19.8, -14.3, 0.0], [-13.8, -14.3, 0.0]].
Fit: height 2.2 m exactly; roof 1.84 x 1.79 m, body about 1.64 x 1.54 m. Two instances (west and east) at (-19.8,-14.3,0) and (-13.8,-14.3,0), door/window face on -Y (toward the barricade) like the old windows. Replaces the two navy boxes in build_gate; the existing Col_Booth_W / Col_Booth_E (1.2 m high boxes, x -20.7..-18.9 and -14.6..-13.0, y -15.1..-13.5) can stay as they are; new footprints (x -20.72..-18.88 and -14.72..-12.88, y -15.2..-13.4) stay clear of Col_Barricade_* (y -16.5..-16.0) and Spot_gate (-16.5,-15).
Renders: scratchpad s6/town_old_*.png vs town_new_*.png (preview only). Tripo credits for this step: 0 (cleanup in Blender only). No Unity run, no commit.

## Installed in town.fbx 2026-10-11 (S7-TOWN-REBUILD)
Installed through Blender/town/guild.py + Blender/town/tripo_pieces.json (data-driven table; a missing file falls back to the procedural build). Old town.fbx, .meta, guild.py, markers.json and town_guild.blend backed up in ArtSource/town/_backup_20261011/. Marker Assets/_Game/Resources/Art/Town/town.tripo. Guard_Booth_W and Guard_Booth_E (2888 tris each, M_GuardBooth_Tripo) at (-19.8, -14.3, 0) and (-13.8, -14.3, 0), rot 0, each its own mesh copy. Replace the two navy boxes baked into Dungeon_Gate. Col_Booth_W (x -20.7..-18.9) / Col_Booth_E (x -14.6..-13.0), y -15.1..-13.5, h 1.2 kept unchanged: both lie inside the new footprints (x -20.72..-18.88 / -14.72..-12.88, y -15.19..-13.41). Texture: Art/Town/town_tex/M_GuardBooth_Tripo.png (1024). Credits: 0.
Previews: scratchpad s7/town_old_*.png vs town_new_*.png (hq_front, hq_entrance, gate, fountain). No Unity run, no commit; materials get their .mat on the next editor load via TexturedMaterials.SyncAll.
