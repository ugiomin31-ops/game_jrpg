# banner — candidates

Batch: B2 (ArtSource/_briefs/B2_prompts.md). Status: 4 candidates saved. Pick suggested, main session makes final pick.

## Model check (before send, 2026-10-11 23:49)
- Model menu: "GPT-6" aria-checked=true (GPT-5.6 Sol and GPT-5.5 unchecked)
- Reasoning slider: [role=slider] aria-valuenow=3, aria-valuemax=4 (Extra High, 4th of 5 stops)

## Chat
- URL: https://chatgpt.com/c/6acba0c3-9a80-83e8-aa1a-9c2753ab8229 (new chat for this asset)
- Source site: chatgpt.com (web), GPT-6, Extra High
- Images returned in this response: 4 (separate images, md5 distinct)
- Downloads: viewer "이미지 다운로드" per image; images 1-4 mapped to candidate_A..D in order

## Prompt (sent verbatim)
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One rigid contemporary guild pennant assembly: a sturdy steel pole with an attached solid blue rectangular banner slab, a restrained abstract sunrise relief and a plain warm-metal lower band, about 0.9 m wide, 0.16 m deep, 4.8 m high; banner 2.2 m tall. No fabric flutter, thin cords, text or heraldic ornament. One complete connected object, chunky modern Seoul toon-3D style, front three-quarter view, plain light-grey background, generous margins, square 1:1. Thick attached construction, opaque painted windows, closed doors; no interiors, people, vehicles, transparent parts, floating effects, lettering, logos, medieval decoration or thin dangling pieces. Vary proportions and colour accents between the four images while keeping the description.

## Candidates
- candidate_A.png: steel pole with a spiked finial, solid blue slab with a large gold sunrise relief, gold lower band, rigid bracket arms, grey-bronze base. Fits; the sunrise is large and the pole base is detailed.
- candidate_B.png: steel pole with a gold finial, solid blue slab with a gold sunrise relief and a plain gold lower band, a rigid top rail, grey base. Fits closely; the sunrise and band are restrained.
- candidate_C.png: dark navy slab (less blue than the brief), copper sunrise relief and copper lower band, steel pole with copper rings. Fits the parts; the colour is darker and the copper is warmer than the brief.
- candidate_D.png: blue slab with a gold sunrise relief and a plain gold lower band, a horizontal steel arm at the top, ornate bronze pole and base. Fits; the top arm and the base ornament are extra.

## Suggested pick (main session makes the final pick)
- candidate_B.png: solid blue slab that matches the brief, restrained sunrise relief, a plain warm-metal lower band, and a sturdy pole with a rigid top rail. Runner-up: candidate_A.png.

## Tripo Studio (web) — B2 run, 2026-10-12
- Main final pick: candidate_B.png (main-approved B2 table)
- Source site: studio.tripo3d.ai (web, Tripo subscription credits). Model H3.1 Best Quality, Geometry & Texture.
- Generation task: c9de11a4-0f3c-46dd-8c6c-562aa4698bfd (https://studio.tripo3d.ai/workspace/generate/c9de11a4-0f3c-46dd-8c6c-562aa4698bfd). Cost 55, balance 305 -> 250 (banner was the 5th generation of this batch).
- Retopo: Triangle (data-state=on), Smart Mesh on, target 3000 (textbox and slider aria-valuenow both 3000). Cost 35, balance 110 -> 75. Result: 2928 faces / 3862 vertices.
- Rig: none.
- Export: FBX, Texture Resolution 1k. Zip extracted to ArtSource/town/banner/tripo/.
- Balance after this asset: 75.

## Installed in town.fbx 2026-10-12 (B2 town install)
Banner_north_a (-2.6, 13.1), Banner_north_b (-17.0, 13.2) and Banner_south_west (-20.0, -19.8) (2928 tris each, M_Banner_Tripo, 1024), origin = pole base, rotation 0/0/180 (south_west turned so the slab hangs toward the plaza). Uniform scale 4.89: 4.8 m high; the slab is 1.74 m wide and the whole piece 2.1 x 1.1 m (the brief's 0.9 m width is not what the mesh has). Replaces all three procedural pennants (token banner); they were blue, red and teal, now all blue. No colliders (as before). Installed through Blender/town/guild.py + Blender/town/tripo_pieces.json (backup of the previous build in ArtSource/town/_backup_20261012/). Marker Assets/_Game/Resources/Art/Town/town.tripo. Staged by non-uniform fit (ArtSource/town/banner/staging: fbx, tex PNG, placement.json, .tripo). Credits: 0 in this step. Previews: scratchpad s8/town_{old,new}_*.png. No Unity run, no commit; the .mat is created on the next editor load by TexturedMaterials.SyncAll.
