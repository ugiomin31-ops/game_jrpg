# guild_workshop — candidates

Batch: B2 (ArtSource/_briefs/B2_prompts.md). Status: 4 candidates saved. Pick suggested, main session makes final pick.

## Model check (before send, 2026-10-11 23:41)
- Model menu: "GPT-6" aria-checked=true (GPT-5.6 Sol and GPT-5.5 unchecked)
- Reasoning slider: [role=slider] aria-valuenow=3, aria-valuemax=4 (Extra High, 4th of 5 stops)

## Chat
- URL: https://chatgpt.com/c/6acb9f18-717c-83ee-aeb4-ecfec75198a1 (new chat for this asset)
- Source site: chatgpt.com (web), GPT-6, Extra High
- Images returned in this response: 4 (separate images, md5 distinct)
- Downloads: viewer "이미지 다운로드" per image; images 1-4 mapped to candidate_A..D in order

## Prompt (sent verbatim)
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One closed modern equipment-repair workshop, steel-blue walls, a dark flat roof, a broad closed charcoal roller shutter and a blank amber sign band. Body about 5.2 m deep, 6.8 m frontage, 6 m high. No open garage, furnace interior, cargo or workbench. One complete connected object, chunky modern Seoul toon-3D style, front three-quarter view, plain light-grey background, generous margins, square 1:1. Thick attached construction, opaque painted windows, closed doors; no interiors, people, vehicles, transparent parts, floating effects, lettering, logos, medieval decoration or thin dangling pieces. Vary proportions and colour accents between the four images while keeping the description.

## Candidates
- candidate_A.png (1254x1254): steel-blue walls, dark flat roof, broad charcoal roller shutter, blank amber sign band, small closed door, opaque windows. Fits closely; few extras.
- candidate_B.png (1254x1254): steel-blue walls, dark roof, large roller shutter, amber sign band with three attached lamps above, yellow bollard stripes at the shutter edges. Fits; the lamps and bollards are extra.
- candidate_C.png (1254x1254): dark roof, roller shutter on the left face, amber sign band, teal accent bands, steel-blue side wall. Fits; the shutter sits on the front-left face and the teal accents are extra.
- candidate_D.png (1254x1254): steel-blue walls, dark roof, broad roller shutter, amber sign band, wall lamps and tan plinths. Fits; the tan plinths and lamps are extra.

## Suggested pick (main session makes the final pick)
- candidate_A.png: the broadest closed shutter, a clean blank amber sign band, steel-blue walls and a dark flat roof with the fewest extra parts. Runner-up: candidate_D.png.

## Tripo Studio (web) — B2 run, 2026-10-12
- Main final pick: candidate_A.png (main-approved B2 table)
- Source site: studio.tripo3d.ai (web, Tripo subscription credits). Model H3.1 Best Quality, Geometry & Texture.
- Generation task: cfb6d55d-6751-4615-ba90-c32181fdc7b1 (https://studio.tripo3d.ai/workspace/generate/cfb6d55d-6751-4615-ba90-c32181fdc7b1). Cost 55, balance 470 -> 415.
- Retopo: Triangle (data-state=on), Smart Mesh on, target 6000 (textbox and slider aria-valuenow both 6000). Cost 35, balance 180 -> 145. Result: 5789 faces / 6471 vertices.
- Rig: none.
- Export: FBX, Texture Resolution 2k, Blender preset (default). Zip extracted to ArtSource/town/guild_workshop/tripo/.
- Balance after this asset: 145.

## Installed in town.fbx 2026-10-12 (B2 town install)
Guild_Workshop (5789 tris, M_GuildWorkshop_Tripo, 2048) at (15.6, 10.6, 0), rotation 90 (facade -X). Scale 6.95/6.98/8.65: body x 15.6..20.8, y 7.2..14.0, height 6.0 m (roof <= 6.3); the door hood projects 0.16 m. Replaces build_workshop's visuals incl. Sign_Workshop (removed). Col_Workshop kept. Spot_smith unchanged (2.8 m clear). The anvil, barrel and cargo kit props stay. Installed through Blender/town/guild.py + Blender/town/tripo_pieces.json (backup of the previous build in ArtSource/town/_backup_20261012/). Marker Assets/_Game/Resources/Art/Town/town.tripo. Staged by non-uniform fit (ArtSource/town/guild_workshop/staging: fbx, tex PNG, placement.json, .tripo). Credits: 0 in this step. Previews: scratchpad s8/town_{old,new}_*.png. No Unity run, no commit; the .mat is created on the next editor load by TexturedMaterials.SyncAll.
