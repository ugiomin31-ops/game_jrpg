# Tripo Studio humanoid animation presets (read-only inventory)

Date: 2026-10-11. Haiku 5.5 worker. Nothing applied, nothing bought, no credits spent.
Source: https://studio.tripo3d.ai/workspace/animate/0b4952e7-f531-4174-a74c-da8f88102b85 (h_seoa, already rigged Humanoid Mixamo), Animation > Preset tab, read through the Filter panel one category at a time (Basic, Interactive, Scene Specific, Emotional, Combat; each shown alone).
Costs: no per-preset cost is shown in the preset list (cards show only the name). The Generate button shows 20 for a custom motion prompt, which is not a preset. No preset was clicked.
Total presets: 97 (Basic 14, Interactive 15, Scene Specific 33, Emotional 21, Combat 14).

## Category: Basic (14)
idle, run, fold_arms, freaky, jump_down, jump, look_around, run_upstairs, stretch, sit, standing_relax, turn, wait, walk

## Category: Interactive (15)
agree, bow, greet_01, greet_02, greet_03, greet_04, heart_pose, hug, lift_heavy, make_a_call_01, make_a_call_02, play_mobile_game, play_video_game, wave_goodbye_01, wave_goodbye_02

## Category: Scene Specific (33)
basketball_shot, cast_a_spell, chop, climb, crossover_dribble, dance_01, dance_02, dance_03, dance_04, dance_05, dance_06, dig, dive, dribble, fall, flip, football_catch, football_save, football_pass, jump_rope_01, jump_rope_02, pitch_baseball, press-up, shovel, sing_01, sing_02, sing_03, sing_04, slash, surf, swim, volleyball, warm_up

## Category: Emotional (21)
afraid, angry_01, angry_02, angry_03, cheer, clap, complain_01, complain_02, cry, depressed, flee_01, flee_02, frightened, frustrated_01, frustrated_02, laugh_01, laugh_02, scared_01, scared_02, sob, swagger

## Category: Combat (14)
box_01, box_02, box_03, defeat, defeat_02, fire, front_kick_01, front_kick_02, hit_to_body_01, hit_to_body_02, hit_to_head, hit_to_side, hit_to_stomach, shoot

## Mapping to the game's needs
- Walk: `walk` (Basic). Also `run` (Basic) for a chase.
- Attack, weapon swing or slash: `slash` (Scene Specific), `chop` (Scene Specific). No plain punch preset. Melee kicks: `front_kick_01`, `front_kick_02` (Combat). Ranged: `shoot`, `fire` (Combat), `box_01..03` (Combat, punch-like, not confirmed).
- Cast (spell): `cast_a_spell` (Scene Specific).
- Hit or hurt: `hit_to_body_01`, `hit_to_body_02`, `hit_to_head`, `hit_to_side`, `hit_to_stomach` (Combat).
- Die, death or defeat: `defeat`, `defeat_02` (Combat). `fall` (Scene Specific) is a fall, not a death.
- Victory or cheer: `cheer` (Emotional), `clap` (Emotional), `swagger` (Emotional).
- Guard, block or defend: no preset found in the list.
- Revive, get up or stand up: no preset found. `standing_relax` (Basic) is an idle stance, not a get-up.

Notes: names are read from the DOM text and may not match the animation content exactly; preview each candidate before using it. Presets are filtered by category, so one preset can appear under only one category here.
