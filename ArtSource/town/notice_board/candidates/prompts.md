# notice_board — candidates

Batch: B2 (ArtSource/_briefs/B2_prompts.md). Status: 4 candidates saved. Pick suggested, main session makes final pick.

## Model check (before send, 2026-10-11 23:44)
- Model menu: "GPT-6" aria-checked=true (GPT-5.6 Sol and GPT-5.5 unchecked)
- Reasoning slider: [role=slider] aria-valuenow=3, aria-valuemax=4 (Extra High, 4th of 5 stops)

## Chat
- URL: https://chatgpt.com/c/6acb9fe2-6d94-83e8-83ad-4e9400e6bc1b (new chat for this asset)
- Source site: chatgpt.com (web), GPT-6, Extra High
- Images returned in this response: 4 (separate images, md5 distinct)
- Downloads: viewer "이미지 다운로드" per image; images 1-4 mapped to candidate_A..D in order

## Prompt (sent verbatim)
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One freestanding guild notice board: a thick cork-coloured rectangular panel in a sturdy contemporary frame, two robust attached posts and a compact top cap, about 1.98 m wide, 0.12 m deep, 2.18 m high. Several blank pastel rectangular notices sit flush against the panel; no writing, pins or loose paper. One complete connected object, chunky modern Seoul toon-3D style, front three-quarter view, plain light-grey background, generous margins, square 1:1. Thick attached construction, opaque painted windows, closed doors; no interiors, people, vehicles, transparent parts, floating effects, lettering, logos, medieval decoration or thin dangling pieces. Vary proportions and colour accents between the four images while keeping the description.

## Candidates
- candidate_A.png (1254x1254): wide landscape board, dark-grey frame with teal accents, cork panel, six blank pastel notices, two posts with a cap. Fits the parts; the board is wider than tall, which is against the 1.98 m wide by 2.18 m high proportion.
- candidate_B.png (1254x1254): taller than wide, grey posts with navy frame and cap, cork panel, five blank pastel notices, robust posts. Fits the 1.98 x 2.18 m proportion most closely.
- candidate_C.png (1254x1254): landscape board, slate frame with olive-green accents and bolts, six pastel notices, posts and cap. Fits; the olive hardware and bolts are extra details.
- candidate_D.png (1254x1254): landscape board, navy frame with copper bands, six pastel notices, two posts with a cap. Fits; the copper bands are extra and the board is wider than tall.

## Suggested pick (main session makes the final pick)
- candidate_B.png: the proportion is closest to 1.98 m wide by 2.18 m high, the frame and posts are sturdy with a compact cap, the notices are flush and blank, and the accents are restrained. Runner-up: candidate_A.png.

## Tripo Studio (web) — B2 run, 2026-10-12
- Main final pick: candidate_B.png (main-approved B2 table)
- Source site: studio.tripo3d.ai (web, Tripo subscription credits). Model H3.1 Best Quality, Geometry & Texture.
- Generation task: a65ebfe5-f399-48ee-bba0-5b664af909ce (https://studio.tripo3d.ai/workspace/generate/a65ebfe5-f399-48ee-bba0-5b664af909ce). Cost 55, balance 415 -> 360.
- Retopo: Triangle (data-state=on), Smart Mesh on, target 3000 (textbox and slider aria-valuenow both 3000). Cost 35, balance 145 -> 110. Result: 2972 faces / 3658 vertices.
- Rig: none.
- Export: FBX, Texture Resolution 1k. Zip extracted to ArtSource/town/notice_board/tripo/.
- Balance after this asset: 110.

## Installed in town.fbx 2026-10-12 (B2 town install)
Notice_Board (2972 tris, M_NoticeBoard_Tripo, 1024) at (-9.6, -1.5, 0), rotation 0 (front -Y). Scale 2.57/2.23/2.23: 1.98 m wide, 2.18 m high, 0.36 m deep (the brief's 0.12 m depth is not what the mesh has). CHOICE: it replaces the plaza notice_board(-9.6,-1.5,'plaza') (same 1.98 x 2.18 size), not the HQ Quest_Board, which stays procedural (3.1 x 3.45 m). The post colliders Col_Notice_plaza_L/R now follow the feet: x -10.59..-10.23 and -8.97..-8.61, y -1.68..-1.32, h 1.2. Installed through Blender/town/guild.py + Blender/town/tripo_pieces.json (backup of the previous build in ArtSource/town/_backup_20261012/). Marker Assets/_Game/Resources/Art/Town/town.tripo. Staged by non-uniform fit (ArtSource/town/notice_board/staging: fbx, tex PNG, placement.json, .tripo). Credits: 0 in this step. Previews: scratchpad s8/town_{old,new}_*.png. No Unity run, no commit; the .mat is created on the next editor load by TexturedMaterials.SyncAll.
