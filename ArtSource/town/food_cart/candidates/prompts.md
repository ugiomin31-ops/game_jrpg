# food_cart (town P1) — ChatGPT web candidates, 2026-10-12

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High).
Chat: https://chatgpt.com/c/6acc89de-1d4c-83ee-aee1-6163af60d252
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. A thick, broad-canopied street cart with a striped awning on four sturdy posts and broad pans. View: front three-quarter. One chunky polished Seoul hunter-guild street asset, modern Korean urban design, broad readable forms, clean restrained material colours, plain neutral background, complete object, square image. No people or readable signage.

Results (one response, 4 images):
- candidate_A.png: red-and-cream striped awning on four sturdy steel-and-wood posts, broad steel pans with tteokbokki and odeng skewers; matches the brief.
- candidate_B.png: gabled striped awning, four posts, pans of tteokbokki and skewers; lower canopy.
- candidate_C.png: red-and-cream awning, red cabinet body, spoked wheels; three visible posts; pans are small.
- candidate_D.png: striped awning on three visible posts, wooden counter, broad pans; one post hidden.

Suggested pick: candidate_A.png. Reason: four visible sturdy posts, striped awning, broad steel pans with tteokbokki and odeng, clean material colours. candidate_B is the alternative.

## Tripo (B5-TRIPO-2, 2026-10-12, third account)
- Image uploaded: candidates/candidate_A.png (the suggested pick above).
- Image-to-3D: studio.tripo3d.ai web, AI Model H3.1 Best Quality, Geometry & Texture: Ultra Mesh Quality on, Texture on, Texture Quality 2K, PBR on. Generate cost 45. Task id: 690af115-9476-4964-a761-2ebea9905bd8
- Balance: 3220 -> 3175
- Retopology: Topology Triangle, Smart Mesh on, polygon count 5000 target, result 5614 faces (binary count). Cost 35. Balance: 3175 -> 3140
- Export: FBX, Blender preset, texture 2k. Local file: ArtSource/town/food_cart/tripo/tripo_convert_1b53cf30-f8d9-40fe-b355-b57893ce5b94.fbx (+ adjacent .fbm)

### Installed 2026-10-13 (B5-INSTALL-2, Blender/town/tripo_pieces.json + Blender/town/guild.py)
- Staging: ArtSource/town/food_cart/staging/ (food_cart.fbx 5614 tris = Tripo 5614, M_FoodCart_Tripo 1024 px, placement.json, food_cart.tripo). Uniform/stage scale [2.4598, 2.4598, 2.4598], base-centre pivot at ground, bounds [-1.2, -0.843, 0.0]..[1.2, 0.843, 2.09] m.
- Replaces the two procedural street food stalls (food_cart() in Blender/town/guild.py, token `food_cart`): instances FoodCart_west (-16.6, -6.6) and FoodCart_east (10.6, -11.4), rot 0, serving side toward -Y as before. Uniform x2.46 -> 2.4 x 1.686 x 2.09 m (old 2.2 x 1.1 x 2.9). Colliders keep the names FoodCart_west/east (guild.py, now 2.4 x 1.6 x 1.2 m so they cover the Tripo footprint).
- Town rebuilt with `blender -b --factory-startup --python-exit-code 1 -P Blender/town/guild.py -- --no-preview`; texture copied to Assets/_Game/Resources/Art/Town/town_tex/M_FoodCart_Tripo.png (town.fbx.meta untouched). Backup of the previous town.fbx/.meta/.tripo, town_tex PNGs, guild.py, markers.json, guild_atmosphere.json, tripo_pieces.json and town_guild.blend: ArtSource/town/_backup_20261012c/. Unity not run by this worker: import, material creation and in-game look still to be verified.

### RESTORE-TOWN-CHARS (2026-10-13, Claude Sonnet)
- Basecolor replaced by the raw 2048 px (was downscaled to 1024); geometry unchanged (uniform 2.4598).
