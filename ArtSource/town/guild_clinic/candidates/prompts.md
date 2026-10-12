# guild_clinic — candidates

Batch: B2 (ArtSource/_briefs/B2_prompts.md). Status: 4 candidates saved. Pick suggested, main session makes final pick.

## Model check (before send, 2026-10-11 23:30)
- Model menu: "GPT-6" aria-checked=true (GPT-5.6 Sol and GPT-5.5 unchecked)
- Reasoning slider: [role=slider] aria-valuenow=3, aria-valuemax=4 (Extra High, 4th of 5 stops)

## Chat
- URL: https://chatgpt.com/c/6acb9d85-7784-83ec-89dd-b51b8dcf6811 (new chat for this asset)
- Source site: chatgpt.com (web), GPT-6, Extra High
- Images returned in this response: 4 (separate images, md5 distinct)
- Downloads: viewer "이미지 다운로드" per image; images 1-4 mapped to candidate_A..D in order

## Prompt (sent verbatim)
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One closed two-storey guild infirmary, white and mint walls, a dark-teal flat roof, opaque blue painted windows and a closed entrance on the long façade. A blank mint sign panel with a simple abstract colour band, no cross. Body about 5.2 m deep, 10.2 m frontage, 6.8 m high; a thick attached teal-and-white canopy. No separate flagpole. One complete connected object, chunky modern Seoul toon-3D style, front three-quarter view, plain light-grey background, generous margins, square 1:1. Thick attached construction, opaque painted windows, closed doors; no interiors, people, vehicles, transparent parts, floating effects, lettering, logos, medieval decoration or thin dangling pieces. Vary proportions and colour accents between the four images while keeping the description.

## Candidates
- candidate_A.png (1254x1254): two storeys, dark-teal flat roof, white and mint walls, wave-banded teal canopy over the entrance, blue painted windows, closed double doors. Fits; the sign is the canopy band, with no separate blank sign panel.
- candidate_B.png (1254x1254): two storeys, flat dark-teal roof, a blank mint sign panel with a wave band above a teal-and-white canopy, blue windows, closed doors. Fits closely to the sign and canopy brief.
- candidate_C.png (1254x1254): two storeys, teal roof, mint sign panel with a wave band over the entrance, a canopy with a small blue arc accent, closed doors. Fits; the blue arc is an extra accent.
- candidate_D.png (1254x1254): two storeys, teal roof, large mint sign panel with a wave band, teal-and-white entrance pillars, grey plinths, closed doors. Fits; the grey plinths are extra.

## Suggested pick (main session makes the final pick)
- candidate_B.png: the blank mint sign panel with a simple wave band, the attached teal-and-white canopy, closed entrance and opaque blue windows all match the brief, with a clean silhouette. Runner-up: candidate_D.png.

## Notes
- The brief asks for a square 1:1 image; the saved PNGs are 1254x1254.

## Tripo Studio (web) — B2 run, 2026-10-11
- Main final pick: candidate_D.png (main-approved B2 table; Haiku note above was only a suggestion)
- Source site: studio.tripo3d.ai (web, Tripo subscription credits). Model H3.1 Best Quality, Geometry & Texture.
- Generation task: 1d85429d-8e96-4c3c-b120-62f1123865f9 (https://studio.tripo3d.ai/workspace/generate/1d85429d-8e96-4c3c-b120-62f1123865f9). Cost 55, balance 580 -> 525.
- Retopo: Triangle (data-state=on), Smart Mesh on, target 10000 (textbox and slider aria-valuenow both 10000). Cost 35 (button showed 40 under Quad), balance 250 -> 215. Result: 10166 faces / 10691 vertices.
- Rig: none.
- Export: FBX, Texture Resolution 2k, Blender preset (default highlighted). Downloaded zip, extracted to ArtSource/town/guild_clinic/tripo/ (tripo_convert_4815b307-0429-4836-a3e9-fde54aa9c7db.fbx + .fbm textures).
- Balance after this asset: 215.

## Installed in town.fbx 2026-10-12 (B2 town install)
Guild_Clinic (10166 tris, M_GuildClinic_Tripo, 2048) at (-15.6, 1.5, 0), rotation -90 (facade +X). Fit scale x/y/z 11.30/6.56/10.07 so the body keeps the procedural footprint x -20.8..-15.6, y -3.6..6.6, height 6.8 m (roof <= 7.1); canopy and entrance steps project 0.85 m (canopy tip x -14.46, <= 1.8). Replaces build_clinic's visuals (token clinic); Col_Clinic kept; new Col_Clinic_Steps (x -15.6..-14.65, y -2.8..5.6, h 0.8) for the porch steps; the two clinic planters moved out to y -3.7 / 6.5 (colliders follow, tags kept) because the steps overlapped them. Spot_innkeeper unchanged (1.6 m clear). The flagpole, sandwich board and menu kit stay procedural. Installed through Blender/town/guild.py + Blender/town/tripo_pieces.json (backup of the previous build in ArtSource/town/_backup_20261012/). Marker Assets/_Game/Resources/Art/Town/town.tripo. Staged by non-uniform fit (ArtSource/town/guild_clinic/staging: fbx, tex PNG, placement.json, .tripo). Credits: 0 in this step. Previews: scratchpad s8/town_{old,new}_*.png. No Unity run, no commit; the .mat is created on the next editor load by TexturedMaterials.SyncAll.
