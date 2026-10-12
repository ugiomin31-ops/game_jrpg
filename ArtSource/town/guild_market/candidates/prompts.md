# guild_market — candidates

Batch: B2 (ArtSource/_briefs/B2_prompts.md). Status: 4 candidates saved. Pick suggested, main session makes final pick.

## Model check (before send, 2026-10-11 23:37)
- Model menu: "GPT-6" aria-checked=true (GPT-5.6 Sol and GPT-5.5 unchecked)
- Reasoning slider: [role=slider] aria-valuenow=3, aria-valuemax=4 (Extra High, 4th of 5 stops)

## Chat
- URL: https://chatgpt.com/c/6acb9e4a-7280-83ec-9f65-aa52bc9c00bf (new chat for this asset)
- Source site: chatgpt.com (web), GPT-6, Extra High
- Images returned in this response: 4 (separate images, md5 distinct)
- Downloads: viewer "이미지 다운로드" per image; images 1-4 mapped to candidate_A..D in order

## Prompt (sent verbatim)
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One closed contemporary hunter-market shop, warm-yellow walls, a red-and-cream striped attached awning, a blank illuminated sign band, an opaque painted shopfront and a closed door. Body about 5.2 m deep, 8.2 m frontage, 5.6 m high. No visible merchandise, crates, fridge or separate street furniture. One complete connected object, chunky modern Seoul toon-3D style, front three-quarter view, plain light-grey background, generous margins, square 1:1. Thick attached construction, opaque painted windows, closed doors; no interiors, people, vehicles, transparent parts, floating effects, lettering, logos, medieval decoration or thin dangling pieces. Vary proportions and colour accents between the four images while keeping the description.

## Candidates
- candidate_A.png (1254x1254): single storey, warm-yellow walls, red-and-cream striped awning, large blank illuminated sign band, opaque grey shopfront, closed door. Fits closely to the 5.6 m single-storey body.
- candidate_B.png (1254x1254): two storeys with a lit sign band between floors, red-and-cream awning, red lower panels, wall lights, closed door. Fits the materials; it reads taller than a single-storey 5.6 m body and adds wall lights.
- candidate_C.png (1254x1254): two storeys, cream and red trim, a lit sign band below the upper windows, striped awning, closed door. Fits the materials; the upper floor and lights are extra.
- candidate_D.png (1254x1254): single storey, cream and yellow walls with red accents, blank sign panel, striped awning, large dark shopfront, closed door. Fits; the red wall accents and cream cornice are extra.

## Suggested pick (main session makes the final pick)
- candidate_A.png: single storey matches the 5.6 m body, the awning and blank sign band are clear, the shopfront is opaque and closed, and the silhouette is clean. Runner-up: candidate_D.png.

## Tripo Studio (web) — B2 run, 2026-10-11/12
- Main final pick: candidate_A.png (main-approved B2 table)
- Source site: studio.tripo3d.ai (web, Tripo subscription credits). Model H3.1 Best Quality, Geometry & Texture.
- Generation task: 0eb69da3-a92e-4238-a48f-6bb84f85af86 (https://studio.tripo3d.ai/workspace/generate/0eb69da3-a92e-4238-a48f-6bb84f85af86). Cost 55, balance 525 -> 470.
- Retopo: Triangle (data-state=on), Smart Mesh on, target 8000 (textbox and slider aria-valuenow both 8000). Cost 35, balance 215 -> 180. Result: 7715 faces / 9069 vertices.
- Rig: none.
- Export: FBX, Texture Resolution 2k (verified: textures 2048x2048), Blender preset (default). Zip extracted to ArtSource/town/guild_market/tripo/ (tripo_convert_7f395177-47fd-4b04-befd-cef362187d0a.fbx + .fbm textures).
- Balance after this asset: 180.

## Installed in town.fbx 2026-10-12 (B2 town install)
Guild_Market (7715 tris, M_GuildMarket_Tripo, 2048) at (15.6, -1.5, 0), rotation 90 (facade -X). Scale 8.37/9.05/8.67: body x 15.6..20.8, y -5.6..2.6, height 5.6 m; awning projects 0.71 m (tip x 14.89, <= 1.8). Replaces build_market's visuals incl. Sign_Market (removed; the sign band is in the texture). Col_Market kept. Spot_shopkeeper unchanged (2.5 m clear). The crates/fridge/menu kit props stay. Installed through Blender/town/guild.py + Blender/town/tripo_pieces.json (backup of the previous build in ArtSource/town/_backup_20261012/). Marker Assets/_Game/Resources/Art/Town/town.tripo. Staged by non-uniform fit (ArtSource/town/guild_market/staging: fbx, tex PNG, placement.json, .tripo). Credits: 0 in this step. Previews: scratchpad s8/town_{old,new}_*.png. No Unity run, no commit; the .mat is created on the next editor load by TexturedMaterials.SyncAll.
