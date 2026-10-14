# Other-rig animation options (Tripo Studio, second account, 2026-10-12)

Investigation only. Nothing was bought or applied. Worker B3-TRIPO (Haiku), D2 step.

## Observed on
- bat, task 0f973850-8831-4c6b-b1dd-c800c07ffe50, Rig type "Other", Auto Rig (one attempt, 20 credits), skeleton on, 4988 faces.
- Animate page: https://studio.tripo3d.ai/workspace/animate/0f973850-8831-4c6b-b1dd-c800c07ffe50

## What the Animate page offers for an Other rig
1. Preset tab: grid of 97 preset motions. Names (read from the page):
   afraid, agree, angry_01, angry_02, angry_03, basketball_shot, bow, box_01, box_02, box_03, cast_a_spell, cheer, chop, clap, climb, complain_01, complain_02, crossover_dribble, cry, dance_01 to dance_06, defeat, defeat_02, depressed, dig, dive, dribble, fall, fire, flee_01, flee_02, flip, fold_arms, football_catch, football_save, football_pass, freaky, frightened, front_kick_01, front_kick_02, frustrated_01, frustrated_02, greet_01 to greet_04, heart_pose, hit_to_body_01, hit_to_body_02, hit_to_head, hit_to_side, hit_to_stomach, hug, idle, jump_down, jump, jump_rope_01, jump_rope_02, laugh_01, laugh_02, lift_heavy, look_around, make_a_call_01, make_a_call_02, pitch_baseball, play_mobile_game, play_video_game, run_upstairs, run, scared_01, scared_02, stretch, shoot, shovel, sing_01 to sing_04, sit, slash, sob, standing_relax, surf, swagger, swim, turn, volleyball, wait, walk, warm_up, wave_goodbye_01, wave_goodbye_02.
   - No price badge is visible on the cards. No preset was applied to the bat, so the cost on an Other rig is NOT verified. On the humanoid rigs (sewer_rat, horned_rabbit) the same presets were free: balance did not change.
2. AI Animation tab: empty list ("No matching animation"). It is a history list, not a generator.
3. "Create Your Own Animation" (text-to-motion): prompt box, duration slider (default 5 s), Generate button shows **20 credits**, greyed out until a prompt is typed. Text-to-motion is therefore available on Other rigs and costs 20 credits per generation.
4. "Multi-stage Motion" (keyframe editor: Start 2 s, Point A 2 s, Add Keyframe): Generate button shows **20 credits**.
5. Export dialog for a rigged model with no animations: FBX, Blender/Mixamo/3dsmax preset, texture 2k, Export Skeleton on, animation count 0.

## Not checked
- Whether the 97 presets are free on Other rigs (not applied). Verify with one preset before any batch.
- Blender skin-weight check on any Other rig export (not run; launcher forbids Blender use in this session).

## Per-model checks (added after the bee and elite bat steps)
- bat, task 0f973850 (rig Other): 97 presets in the Preset grid; text-to-motion 20 credits; Multi-stage Motion 20 credits. Nothing bought.
- elite_bat, task fbd2e6b1 (rig Other, 11605 faces): 97 presets in the Preset grid, same list as the bat (idle, run, slash, cast_a_spell, defeat, hit_to_body_01 all present). No cost badge on cards. Nothing applied.
- killer_bee, task 15884c64 (rig Other, 5054 faces): the Preset grid shows ONLY "Walk" (1 preset, 2 page loads checked). The Animate viewport shows no skeleton overlay, although the exported FBX contains a skeleton (LimbNode 80, Skin 1, Cluster 40 by a binary scan of the file). Not resolved: possibly the Animate page does not load this rig; a human should check in Tripo before buying anything for killer_bee.

## Exported FBX skeleton/skin scan (binary token scan, not a Blender check)
- sewer_rat (Humanoid): LimbNode 130, Skin 1, Cluster 65; animation names present: idle, run, slash, cast_a_spell, hit_to_body_01, defeat; AnimStack 8 tokens.
- horned_rabbit (Humanoid): LimbNode 130, Skin 1, Cluster 65; same six animation names present.
- bat (Other): LimbNode 80, Skin 1, Cluster 40; no animation names (no animations exported).
- killer_bee (Other): LimbNode 80, Skin 1, Cluster 40; no animations exported.
- elite_bat (Other): LimbNode 40, Skin 1, Cluster 20; no animations exported.
- Weapons and street_lamp: no skeleton (as specified).
- This only shows that skin deformers and bone clusters exist. Skin weight values and posing still need the Blender check (OPEN, not run by this worker).
