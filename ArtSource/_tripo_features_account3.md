# Tripo Studio: account features and costs (recon, account 3)

Date of recon: 2026-10-14. Task: TRIPO-RECON (no paid steps). No generation, retopo, rig, animate, texture or other spend button was clicked. All costs below are the labels shown on the buttons or read from the DOM without confirming.

Browser: user's Chrome via claude-in-chrome. Tab closed at the end. Each Tripo workspace page with a 3D canvas was rendered inert (WEBGL_lose_context) after load. One renderer freeze occurred after a Multi-stage Motion modal opened a new canvas; it recovered after the context-loss JS ran again.

## 0. Account status

- Logged in. Header on https://studio.tripo3d.ai/workspace/generate shows credit balance **590** (the number next to the Upgrade button). Notifications badge shows 99+.
- Current plan not confirmed (the page offers an "Upgrade" button). The Pricing modal (opened via Upgrade, closed without action) lists Free / Pro / Max, see section 7.
- Setting note: the Geometry & Texture panel says "We'll automatically save your settings for next time". Settings changed during this recon were restored to the values found at start (see section 8).

## 1. Image-to-3D page: https://studio.tripo3d.ai/workspace/generate

Mode switch (top of Generate Model panel): **HD Model** (default, selected) and **Smart Mesh** (crown icon, premium tag).

### 1a. AI Model dropdown (HD Model mode)

| Option | Label | Generate cost (defaults) |
|---|---|---|
| H3.1 | "H3.1 – Best Quality" (default; "Expect longer wait times") | **55** |
| H3.0 | "H3.0 – Fast & Balanced" | **40** |
| H2.5 | "H2.5 – Legacy" | **40** |

### 1b. Geometry & Texture panel (HD mode, H3.1 default state)

Defaults at start: Ultra Mesh Quality ON, AI Complete OFF, Texture ON, Texture Quality 4K, Remove Lighting OFF (tag "New"), PBR ON, Topology Triangle, Polycount slider 500 to 2000000 (value 2000000). Quad / Triangle buttons. "8K" texture quality shows "Trial x1".

Costs measured by flipping one setting at a time from default (55):

| Setting changed | Generate button after change |
|---|---|
| (default) | 55 |
| Ultra Mesh Quality OFF | 40 (-15) |
| AI Complete ON | 55 (no change) |
| Texture OFF | 30 (-25) |
| Texture Quality 2K | 45 (-10) |
| Texture Quality 8K (with 8K Texture switch ON in main panel) | 65 (+10), coin shows "0" next to it (Trial x1) |
| Topology Quad | 60 (+5) |
| PBR OFF | 50 (-5) |
| Remove Lighting ON | 55 (no change) |
| Polycount 500000 | 55 (no change) |

Main panel switches (below General Settings):

- **Generate in Parts**: Trial x1. One reading showed 60 when ON (+5 vs 55). Not fully verified (a later reading was affected by a texture-quality reset, see section 8).
- **8K Texture**: Trial x1. ON adds +10 (65 with defaults, coin shows "0").
- Privacy: "Sharing Only" (dropdown).

### 1c. Smart Mesh mode

- AI Model: **P2.0**, tag "Trial x2". It is the only model listed.
- Number of Generation: 1 / 2 / 4 (default 4, tag "New"). The Generate cost read **100** (coin "0") for 1, 2 and 4. No change observed.
- Sections: Topology (collapsed), Privacy, Customize Poly Counts (collapsed, not expanded).
- Tagline on the panel: "Generate Topo-Ready Mesh in Seconds!".

### 1d. Input options

- Upload image: JPG, PNG, WEBP, size up to 20MB. Button "Generate Image for 3D".
- Upload 3D model (Assets panel on the left): OBJ, FBX, STL, GLB, up to 150MB. See section 5.

## 2. Credit summary for the image-to-3D page (verified readings)

- HD H3.1, Ultra ON, 4K, Triangle, PBR ON, no 8K, no Generate in Parts: **55**
- HD H3.0 or H2.5 (same defaults): **40**
- Smart Mesh P2.0 (any of 1 / 2 / 4): **100**

## 3. Post-generation tools (left nav on every workspace tool page)

Model used: forest_guardian task 880cb170-60bc-46e0-88af-5a126cae1ed9. Model stats: Triangle topology, 19270 faces, 27352 vertices (as shown on the tool pages).

| Tool | URL pattern | Controls | Cost label |
|---|---|---|---|
| Retopo | /workspace/retopology/<id> | Topology Quad / Triangle; "Smart Mesh" toggle (default ON, "P1.0"); Polygon Count input (default 10000, slider range 500 to 10000) | **Retopology 40** (Quad + Smart Mesh, default). Triangle + Smart: 35. Quad without Smart: 10. Triangle without Smart: 5. Polygon count 500 vs 10000: no change (10 at Quad without Smart) |
| Segment | /workspace/segmentation/<id> | Detail Level: Simple (3-6 parts), Balanced (6-15 parts), Detailed (15+ parts). "New Function Trial x1" | **Start Segmenting 40** (coin "0"). Same for all three detail levels |
| Fill Parts | /workspace/fill-parts/<id> | "Automatically complete your segmented model." Button "Recraft" | Not captured. On the first load the header showed "Sign up/Log in" and "View Plans" (transient, the second load showed the logged-in header). Requires a segmented model first |
| Smart UV | /workspace/smart-uv/<id> | "Unwrap UV" | **Unwrap UV 20** (Trial x2, coin "0") |
| Texture | /workspace/texture/<id> | Texture Resolution: 2K / 4K / 8K (8K "Trial x1"); "Create Your Own Texture Style"; style "None"; "Remove Lighting" (New) | **Generate Texture**: 2K **10**, 4K **20**, 8K **30** (Trial x1, coin "0") |
| Texture Edit (Magic Brush) | /workspace/texture-edit/<id> | Gen Mode / Paint Mode; Creativity Strength; counter "81/1000" | **Generate Preview 5** |
| Upscale | /workspace/texture-upscale/<id> | 4K (4096x4096), 8K (8192x8192) | **Enhance Now 10** (shown for default; per-resolution not captured) |
| PBR | /workspace/texture-pbr/<id> | "Generate realistic materials from your model" | **Generate PBR 5** |
| Rig | /workspace/rigging/<id> | Rigging Type: Humanoid / Other; Skeleton Preset: Mixamo; Skeleton; hint "Use a T- or A-pose for best results" | **Retry 20** (both Humanoid and Other show 20) |
| Animate | /workspace/animate/<id> | Preset tab (97 presets), Multi-stage Motion, AI Animation text-to-motion | See section 4 |

Notes:
- Rig page offers "Upload 3D Model" (Assets panel): "Select a model from Assets on the right or upload your own for Rigging and Animation" (quoted from the page). So uploading an FBX/GLB for rigging is supported on this account.
- Export, 3D Print, Share buttons appear on the tool pages (not used).

## 4. Animate page: https://studio.tripo3d.ai/workspace/animate/<id>

### 4a. Preset animations (free, no cost label on any tile)

No cost badge appears on preset tiles in the DOM or screenshot. A Search box filters the list. The list was read fully from the page DOM (97 items, in this order):

cheer, chop, fall, hit_to_body_01, idle, walk, afraid, agree, angry_01, angry_02, angry_03, basketball_shot, bow, box_01, box_02, box_03, cast_a_spell, clap, climb, complain_01, complain_02, crossover_dribble, cry, dance_01, dance_02, dance_03, dance_04, dance_05, dance_06, defeat, defeat_02, depressed, dig, dive, dribble, fire, flee_01, flee_02, flip, fold_arms, football_catch, football_save, football_pass, freaky, frightened, front_kick_01, front_kick_02, frustrated_01, frustrated_02, greet_01, greet_02, greet_03, greet_04, heart_pose, hit_to_body_02, hit_to_head, hit_to_side, hit_to_stomach, hug, jump_down, jump, jump_rope_01, jump_rope_02, laugh_01, laugh_02, lift_heavy, look_around, make_a_call_01, make_a_call_02, pitch_baseball, play_mobile_game, play_video_game, press-up, run_upstairs, run, scared_01, scared_02, stretch, shoot, shovel, sing_01, sing_02, sing_03, sing_04, sit, slash, sob, standing_relax, surf, swagger, swim, turn, volleyball, wait, warm_up, wave_goodbye_01, wave_goodbye_02

Grouping: the page shows one flat group labelled "AI Animation" under the "Preset" tab. No category sub-groups were seen.

Whether a preset requires the model to be rigged first was not tested. The forest_guardian model was not rigged in this recon.

### 4b. Text-to-motion (AI Animation, "Create Your Own Animation")

- Prompt textarea: placeholder "Describe a motion… e.g. "Make the character walk"".
- Duration slider: 1 to 10 seconds, step 1, default 5. Duration does not change the cost (10 s also showed Generate 20).
- Cost: **Generate 20** per clip.

### 4c. Multi-stage Motion (keyframe motion)

- Opens a modal with a 3D preview (this created a new WebGL canvas; the renderer froze until the context was lost again).
- Keyframes: "Start", "Point A", then "+ Add Keyframe" (3 keyframes was reached: Start, Point A, Point B). Each keyframe has a "Describe the motion" text box and a duration slider (default 2 s). Position fields show Z and X values (e.g. "Z: 0.5 X: 0.5").
- Cost label: **Generate 20**, shown greyed out until descriptions are filled. The label stayed at 20 with 3 keyframes. Per-keyframe cost not seen.

### 4d. Other motion features

- Video-to-motion, motion edit, blending: not found on this page.
- Upload in Animate: the Assets panel "Upload 3D Model" (accepts .fbx, .obj, .stl, .glb). Upload cost not shown.

## 5. Upload of an existing FBX/GLB

- Yes. "Upload 3D Model" is in the Assets panel on the Rig, Retopo, Animate and Generate pages. Accepts OBJ, FBX, STL, GLB up to 150MB. The Rig page explicitly says you can upload your own model for rigging and animation.
- Upload itself shows no credit cost. Rigging an uploaded model costs the Rig price (Retry 20). Retopo (if needed) costs 40 by default, or 10 without Smart Mesh.

## 6. Free retries, free credits, trials, perks

- Trial labels seen (first use free of the stated tier, coin shows 0 when used up): Smart Mesh P2.0 "Trial x2"; Generate in Parts "Trial x1"; 8K Texture "Trial x1"; Unwrap UV "Trial x2"; Segmentation "New Function Trial x1"; 8K Texture generation "Trial x1".
- Free retries: the Rig tool shows a "Retry" button at 20; per the Pricing page, paid tiers include more free retries. Free plan does not list free retries.
- Daily free credits: not observed on the workspace. The header has a creator EXP and reward popup ("You currently have — active benefits", "Reward", "View All") that was loading and not read.

## 7. Pricing modal (read only, closed without action)

- **Free**: $0 / month. 200 monthly credits (about 13 models). Standard efficiency, 1 concurrent task, standard queue, public models, non-commercial use. Includes HD Model access, up to 4K texture generation and edit, retopology (listed under "Essential Production Toolkit"). Limited image generation.
- **Pro**: $13 / month when billed annually ($156/year), $20 monthly. 3000 monthly credits (about 200 models, $0.07 per model). Boosted efficiency, 10 concurrent tasks, high queue priority, private models, commercial use, batch generation, 7-day history, more free retries, unlimited storage. Includes HD and Smart Mesh access, Multi-view to 3D, smart segmentation, Ultra Mesh Quality.
- **Max**: $45 / month when billed annually ($540/year), $90 monthly. 25000 monthly credits (about 1660 models, $0.03 per model). 100 concurrent tasks, dedicated queue priority, advanced batch generation, permanent edit history, unlimited free retries and storage, 3 free Pro refine. Unlimited image generation (including 1000 free image generations per month).

## 8. Side effects and restores in this recon

- Generate page: Smart Mesh was toggled and returned to HD Model. AI Model returned to H3.1. Ultra ON, AI Complete OFF, Texture ON, PBR ON, Triangle, polycount 2000000, Remove Lighting OFF, 8K Texture OFF, Generate in Parts OFF. Texture quality set to 4K (a later reading showed 8K selected after the HD toggle; set back to 4K, Generate reads 55).
- Retopo: restored to Quad, Smart Mesh ON, polygon count 10000 (Generate reads 40).
- Rig: "Other" was clicked during the cost test and set back to "Humanoid".
- Segment: Detail Level was set to Balanced then Detailed during the test. The original detail level was not recorded (likely Simple or Balanced). Please check if it matters.
- Texture: the quality buttons (2K, 4K, 8K) were clicked during the test. The last state set was 8K or 2K. The original state was not recorded (likely 4K). Please check the Texture page.
- Multi-stage Motion: 3 keyframes were added in the modal and not generated. Nothing was saved.

## 9. Not verified

- Smart Mesh "Number of Generation" cost: 100 shown for 1, 2 and 4. Per-generation pricing not confirmed.
- Generate in Parts: one reading of +5 (60 vs 55), not fully verified.
- Fill Parts cost (Recraft): not captured.
- Upscale cost for 4K vs 8K: not captured (only the 10 default).
- Whether presets require a rigged model: not tested.
- Free plan vs current plan: not confirmed (Upgrade button shown, plan name not read).
