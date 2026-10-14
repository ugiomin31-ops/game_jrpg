# guild_hq candidates (batch B1, 2026-10-11)

Prompt (exact, sent once; the brief's "front three-quarter view, whole structure visible" line is from the header of B1_prompts.md, placed before the frame):
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One closed four-storey Seoul guild headquarters, pale stone, blue accents, opaque painted glass, an attached sunrise relief and a blank sign. Wide low block about 27 m wide, 11.5 m deep, 15.4 m tall; entrance on the long front side. A thick attached blue-and-cream canopy over the entrance. No visible interiors, no separate kiosk, no people or vehicles. Front three-quarter view, whole structure visible. Chunky clean stylized toon 3D game asset for a present-day Seoul Korean hunter RPG, thick attached parts, single solid object, entire object visible with generous margins, plain light grey background, soft studio light, no cast shadow, square 1:1. No hands, text, lettering, logos, numbers, runes, skulls, ornate gold, medieval decoration, floating effects, transparent parts or thin dangling parts. Vary proportions and colour accents between the four images while keeping the description.

Model: GPT-6, reasoning Extra High (slider 3 of 4) verified before sending.
Chat: https://chatgpt.com/c/6acb7f42-b1c4-83e8-a6e1-d1aec7afd04c
Images: 4 separate images, 1254x1254 PNG (square), no follow-up needed.

Per image:
- candidate_A.png: four storeys, cream and blue, arched sunrise relief above the entrance, blue-and-cream canopy with a blank sign panel, opaque blue glass. Wide front reads well.
- candidate_B.png: tall four-storey block, sunrise relief in a blue panel, blue sign band, canopy less distinct, teal accents. Looks taller than wide.
- candidate_C.png: wide low block, appears three storeys, arched sunrise relief, curved blue canopy, no clear blank sign panel. Storey count does not match the brief.
- candidate_D.png: four-storey block with a tall arched window and sunrise relief above the entrance, blue canopy and sign, warm light in the entrance. Strong, but its proportions look more square.

Suggested pick (main decides): candidate_A.png. Reason: four storeys with a wide low proportion close to the brief, blue-and-cream canopy and blank sign panel present, sunrise relief attached, no people or vehicles, entrance on the long front side.

Method note: copy via a real click on the image's copy button (bottom-left of the response, "이미지 복사") after a real click on the thumbnail. JS-only clicks on the copy button left the clipboard unchanged. Clipboard checked per file; all four files differ.

## B1-TRIPO (2026-10-11 21:53)
Main final pick: candidate_A.png (main-approved).
Source: studio.tripo3d.ai, H3.1 - Best Quality, same settings. Generate cost 55.
Tripo task: https://studio.tripo3d.ai/workspace/generate/325a89b0-a414-44a8-81a7-20c0a33634fe
Status: generation submitted once. Retopo and export NOT yet done.

## B1-FINISH (2026-10-11, Haiku worker)
Retopo: Tripo Retopology (Triangle, Smart Mesh on), target 12000, verified slider 12000 and textbox 12000. Cost 35 credits. Balance before 740, after 705. Result faces 13544 (vertices 19618). Target was 12000, result is about 13% above target. Per task rule, not retopoed again; exported as is and reported.
Rig: none (building).
Export: FBX, texture 2k (set and verified), no skeleton toggle for non-rigged model, format preset Blender (default). No export cost shown.
Files: ArtSource/town/guild_hq/tripo/tripo_convert_3c337d11-27e4-4957-b476-ffd444932826.fbx (+ .fbm, 5 maps). Source zip modern+office+building+3d+model.zip, traversal check clean.
Tripo tab closed after download.

## Staged 2026-10-11 (B1-TOWN-INSTALL, NOT installed)
The town is ONE combined FBX (Assets/_Game/Resources/Art/Town/town.fbx, loaded as a single prefab by ArtLibrary.TownPath / TownWorld.Initialize; Blender/town/guild.py bakes every building into it via MB().build()). There is no separate per-piece FBX or .meta to replace, so the combined file was left untouched. Cleaned piece staged in ArtSource/town/guild_hq/staging/: guild_hq.fbx, guild_hq.tripo (marker), guild_hq_tex/M_GuildHq_Tripo.png (2048x2048 base colour), placement.json.
Staged mesh: 13544 triangles (source 13544, geometry unchanged), single material M_GuildHq_Tripo, uniform scale 25.2528 (rotated 180 deg about Z), origin = front-face centre of the body at ground level (plaza side = +Y). Bounds metres (Blender, Z up): min [-12.334, -18.441, 0.0] max [12.334, 3.717, 15.4], size 24.67 x 22.16 x 15.40.
Intended placement (Blender metres): [[0.0, -17.5, 0.0]].
Fit: height 15.4 m exactly; the Tripo proportions give 24.7 m wide x 18.4 m deep body + 3.7 m canopy (brief said 27 x 11.5), so the building is about 7 m deeper than the old block (extends to y -35.9; skyline colliders start at y -41.4, plaza boundary wall at -24.5 is behind the front face, so walkability is unchanged). Front face (y=0 local) lands on y -17.5 facing +Y (plaza). Needed guild.py change: drop build_hq's Guild_HQ mesh, Sign_DawnGuild, the canopy, plinth, steps, kiosk and quest-board-on-HQ visuals; import the staged FBX at (0, -17.5, 0); replace Col_HQ_Body/Col_HQ_Plinth_W/E with the proposed boxes in placement.json (Col_HQ_Body x -12.33..12.33, y -35.94..-17.5, h 15.4; canopy posts/steps rails need small boxes, listed there, adjust after eyeballing). The Tripo entrance has no 0.9 m plinth (steps top about 0.3 m), the kiosk is absent, and a stair rail/post sits near x -3.6..-3.2 and 3.5..4.9 at the canopy front: Spot_elder (-3.6,-16.4,0.9) and Spot_guild_clerk (6.2,-16.4,0.9) must be moved (z to 0.3) and Col_Reception_Kiosk removed or replaced by a small counter prop. LightAnchor_hq_05 (0,-15,3.6) stays under the 4.1 m canopy slab.
Renders: scratchpad s6/town_old_*.png vs town_new_*.png (preview only). Tripo credits for this step: 0 (cleanup in Blender only). No Unity run, no commit.

## Installed in town.fbx 2026-10-11 (S7-TOWN-REBUILD)
Installed through Blender/town/guild.py + Blender/town/tripo_pieces.json (data-driven table; a missing file falls back to the procedural build). Old town.fbx, .meta, guild.py, markers.json and town_guild.blend backed up in ArtSource/town/_backup_20261011/. Marker Assets/_Game/Resources/Art/Town/town.tripo. Guild_HQ (13544 tris, 1 draw material M_GuildHq_Tripo) at (0, -17.5, 0), rot 0. Replaces the whole procedural build_hq body: Guild_HQ block, canopy, plinth, steps, glass lobby, windows, crest and Sign_DawnGuild (removed). Kept procedural: Reception_Kiosk as its own object (x 5.3..7.3, y -15.9..-14.6, standing on the paving, Col_Reception_Kiosk 1.1 m high, Spot_guild_clerk (6.2,-16.4) now z 0.0 behind it) and the quest board (own object Quest_Board, unchanged). Colliders: Col_HQ_Body x -12.33..12.33, y -35.94..-17.5, h 15.4; Col_HQ_Column_W/E (canopy columns, footprints checked against the mesh: y -17.4..-15.9, h 3.96, the staging proposal's y 3.09 included the canopy lip so it was shortened); Col_HQ_Stoop (x -3.1..3.1, y -17.5..-17.0, h 0.29 = the doorway landing); Col_HQ_Plinth_W/E removed. Spot_elder moved to the doorway (-1.5, -17.1, 0.29), facing kept. Paving strips beside the HQ and Col_Barricade_Corner / barricade line were adjusted to the narrower body (x +-12.33 instead of +-13.5). Texture: Assets/_Game/Resources/Art/Town/town_tex/M_GuildHq_Tripo.png (2048). Credits: 0.
Previews: scratchpad s7/town_old_*.png vs town_new_*.png (hq_front, hq_entrance, gate, fountain). No Unity run, no commit; materials get their .mat on the next editor load via TexturedMaterials.SyncAll.

Stoop fix 2026-10-11: Col_HQ_Stoop top lowered 0.29 -> 0.20 m (CharacterController stepOffset 0.24 m) via tripo_pieces.json; visual landing and Spot_elder z 0.29 unchanged.
