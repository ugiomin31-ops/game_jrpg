# Hunter shared animation library (Tripo Studio)

- Rigged source task: `0b4952e7-f531-4174-a74c-da8f88102b85` (female tactical hunter, 13809 faces). Not re-rigged in this run.
- Tripo page: https://studio.tripo3d.ai/workspace/animate/0b4952e7-f531-4174-a74c-da8f88102b85
- Export: `tripo_export/tripo_convert_0860c4ca-c3c8-42da-8d15-1477434f2105.fbx` (+ `.fbm` textures). FBX, Blender preset, texture 512, Export Skeleton on, 10 animations, animation stay-in-place left off.
- Original zip kept beside it as `tripo_export/futuristic_female_export_2026-10-11.zip`.
- Date: 2026-10-11. Worker: Haiku 5.5 (TRIPO-RUN-3B).

## Takes in the FBX (exact names as stored)

| # | FBX take name | Source | Cost |
|---|---|---|---|
| 1 | `idle` | Tripo free preset `idle` | 0 |
| 2 | `run` | Tripo free preset `run` | 0 |
| 3 | `walk` | Tripo free preset `walk` | 0 |
| 4 | `slash` | Tripo free preset `slash` | 0 |
| 5 | `cast_a_spell` | Tripo free preset `cast_a_spell` | 0 |
| 6 | `hit_to_body_01` | Tripo free preset `hit_to_body_01` | 0 |
| 7 | `defeat_02` | Tripo free preset shown as `defeat` (first tile). Tripo stores it as `defeat_02`, same as in the pumpkin export. | 0 |
| 8 | `cheer` | Tripo free preset `cheer` | 0 |
| 9 | `Standing defensive guard stance: knees bent, both forearms rais` | Text-to-motion (prompt below). Take name is cut at 64 characters in the FBX. UI label: "Defensive Guard". | 20 |
| 10 | `Lying face up on the ground, then pushes up with the arms, gets` | Text-to-motion (prompt below). Take name is cut at 64 characters in the FBX. UI label: "Standing from Ground". | 20 |

Motion prompts (typed exactly, duration 5 s default, AI Animation tab):
- Guard: "Standing defensive guard stance: knees bent, both forearms raised in front of the face and chest to block, holds the pose with slight breathing, loops."
- Revive: "Lying face up on the ground, then pushes up with the arms, gets to one knee and stands up to a ready stance."

## Costs and balances (Tripo subscription credits)

- Balance before the Guard generation: 1770.
- Guard generation: 20 (balance 1750).
- Revive generation: 20 (balance 1730).
- Preset applications and the export: 0 credits.
- Final balance: 1730.

## Checks done and not done

- FBX byte check: `Skin` x1, `Cluster` x65, `Deformer` x133, `LimbNode` x130. The rig has skin data.
- Not done: a posing check in Blender (bone moves mesh). Blender was out of scope for this run. The main session must do it before import.

## TRIPO-MOTION-2 (2026-10-11, Haiku 5.5 worker)

Source: rigged task `0b4952e7-f531-4174-a74c-da8f88102b85` (Animate page, AI Animation tab, Text to Motion). Duration control: range 1-10 s, integer steps; 2 s was available and used. Clip length shown in the player: 1.96 s.

Prompts (typed exactly):
- Attack: "From a ready fighting stance, a quick one-handed overhead weapon swing: short wind-up, fast downward strike, then return to the ready stance. Feet stay in place."
- Cast: "From a ready stance, a quick spell cast: draw the right hand back, then thrust the palm forward to release, hold briefly, then return to the ready stance. Feet stay in place."

UI labels after generation: "Overhead Weapon Swing" (Attack), "Spell Casting Motion" (Cast).

Export: `tripo_export_short/tripo_convert_8dda4b54-3d59-45d3-9f20-9c55fe4159df.fbx` (+ `.fbm` textures), FBX, Blender preset, texture 512 (smallest offered: 512/1k/2k/4k/8k), Export Skeleton on, Number of Animations 2 (Choose Animations dialog, 0/12 list), Animation stay in Place left off. Original zip kept as `tripo_export_short/futuristic_female_export_short_2026-10-11.zip`.

Exact take names in the FBX (`AnimStack` names, cut by Tripo at 63 chars as read from the file):
1. `From a ready fighting stance, a quick one-handed overhead weapo` (Attack)
2. `From a ready stance, a quick spell cast: draw the right hand ba` (Cast)

Costs and balances (Tripo subscription credits):
- Start balance: 1730.
- Attack generation: 20 (balance 1710).
- Cast generation: 20 (balance 1690).
- Export: 0. Final balance: 1690.

Checks done: FBX byte check `Skin` x1, `Cluster` x65, `LimbNode` x130 (same rig as the 2026-10-11 export above). Zip entries checked for path traversal: none.
Not done: the Blender posing check (bone moves mesh). The main session must do it before import.
Not touched: the Defensive Guard and Standing from Ground takes from the earlier run are not in this export.

## TRIPO-CAST-3 (2026-10-11, Haiku 5.5 worker)

Source: rigged task `0b4952e7-f531-4174-a74c-da8f88102b85` (Animate page, AI Animation tab, Create Your Own Animation, text-to-motion). Duration 2 s (range 1-10 s). Generate cost shown on the button: 20.

Prompt (typed exactly):
- "Spell cast: from a ready stance, pull the right hand back beside the shoulder, then thrust the right arm straight forward at shoulder height until it is FULLY EXTENDED with the palm open facing forward, hold the fully extended arm still for half a second, then lower it back to the ready stance. Feet stay planted."

UI label after generation: "Spell Casting Motion" (same label as the TRIPO-MOTION-2 cast take, so the take is identified by the FBX take name below).

Export: `tripo_export_cast3/futuristic_female_cast3_2026-10-11.zip` (kept) and `tripo_export_cast3/extracted/tripo_convert_395a46c2-104c-43a3-8e5c-83bbfa757ce5.fbx` (+ `.fbm` textures). FBX, Blender preset, texture 512, Export Skeleton on, Number of Animations 1 (Choose Animations: only the new take, 1/13), Animation stay in Place off. Zip traversal check: 6 entries, none bad. Extraction into a new empty dir with `python -I`. A first Export click with 0 animations produced no download; the second, with 1 take selected, did.

Take name in the FBX (single `AnimStack`, cut by Tripo at 63 chars):
1. `Spell cast: from a ready stance, pull the right hand back besid` (CAST-3)

Costs and balances (Tripo subscription credits, read from the header):
- Balance before Generate: 1525 (last recorded value in this README was 1690 after TRIPO-MOTION-2; the difference is spend by other Tripo tabs in this session, not attributed here).
- CAST-3 generation: 20 (balance 1450 right after).
- Export: 0 (two Export clicks, one download).
- Balance when the tab was closed: 1120. The drop from 1450 to 1120 happened while the other worker's Tripo generations were running in parallel, so it is not attributed here.

Checks done: FBX binary header is `Kaydara FBX Binary`. Counts `Skin` x1, `Cluster` x65, `LimbNode` x130, `Deformer` x133 (same rig as the earlier exports). Skin data is present.
Not done: the Blender posing check (bone moves mesh). The main session must do it before import. Not verified: the cast motion itself (no visual check of the hand-extension pose).
Tripo tab closed after download. Original download kept at `C:/Users/User/Downloads/futuristic+female+3d+model (1).zip` (outside the project).

## TRIPO-TALK (2026-10-11, Haiku 5.5 worker)

Source: rigged task `0b4952e7-f531-4174-a74c-da8f88102b85` (Animate page, AI Animation tab, Text to Motion, "Friendly Conversation"). Cost 20 (balance 600 -> 580, paid by the main session, not by this worker). Duration 5 s (default). Generation finished and retargeting completed before export.

Prompt (typed exactly):
- "Standing in place having a friendly conversation: relaxed stance, both hands making small natural talking gestures at chest height, slight head nods and weight shifts, then returns to the same relaxed stance it started in so it can loop. Feet stay planted."

Presets applied (Preset tab, no credit cost shown on the cards; balance unchanged at 580): `greet_01`, `agree`, `wave_goodbye_01`.

Export: `tripo_export_talk/futuristic_female_talk_2026-10-11.zip` (kept, from `Downloads/futuristic+female+3d+model (2).zip`) and `tripo_export_talk/extracted/tripo_convert_d68d3626-7e2d-45d9-b580-ea48515e304e.fbx` (+ `.fbm` textures). FBX, Blender preset, texture 512, Export Skeleton on, Number of Animations 4 (Choose Animations 4/17), Animation stay in Place off. Zip traversal check: 6 entries, none bad. Extraction into a new empty dir with `python -I`.

Exact take names in the FBX (as read from the file; the Friendly Conversation name is cut by Tripo at 64 characters):
1. `greet_01`
2. `Standing in place having a friendly conversation: relaxed stanc` (Friendly Conversation)
3. `wave_goodbye_01`
4. `agree`

Checks done: FBX binary header `Kaydara FBX Binary`. Counts `Skin` x1, `Cluster` x65, `LimbNode` x130, `Deformer` x133 (same rig as the earlier exports). Skin data is present.
Not done: the Blender posing check (bone moves mesh). The main session must do it before import.
Tripo tab closed after download.

## CLASS-MOTIONS (2026-10-12, Haiku 5.5 worker, Tripo Studio web)

Rig: shopkeeper task `bc94a7b1-e6ab-4ac7-9ec6-376808870742` (Humanoid Mixamo, already rigged on this account, not re-rigged). Animate page, AI Animation tab, Text to Motion, one generation per clip. Balance before the first Generate: 1720. Balance after the last Generate: 1540.

Clips (cost 20 each, read on the Generate button before each click):

| clip | duration set | balance after | FBX take name (exact, Tripo cuts at 63 chars) |
|---|---|---|---|
| BattleIdle | 3 s | 1700 | `Combat ready stance: feet shoulder-width apart, knees slightly ` |
| Attack_warrior | 2 s | 1680 | `From a combat ready stance, a powerful one-handed overhead swin` |
| Attack_archer | 2 s | 1660 | `Archery shot: from a ready stance, raise a bow held in the LEFT` |
| Attack_mage | 2 s | 1640 | `From a ready stance, flick a short wand held in the right hand ` |
| Attack_cleric | 2 s | 1620 | `From a ready stance, swing a walking cane held in the right han` |
| Skill_warrior | 3 s (requested 2.5 s) | 1600 | `Spinning slash: from a ready stance, spin the whole body once w` |
| Skill_archer | 3 s (requested 2.5 s) | 1580 | `Rapid triple shot: holding a bow in the LEFT hand extended forw` |
| Skill_mage | 3 s (requested 2.5 s) | 1560 | `Spell channel: raise both hands in front of the chest, gather e` |
| Skill_cleric | 3 s (requested 2.5 s) | 1540 | `Healing prayer: hold a cane upright in the right hand, raise it` |

Prompts (typed exactly as given in the task):
- BattleIdle (3 s): "Combat ready stance: feet shoulder-width apart, knees slightly bent, weight forward, right hand holding a short weapon low at the side, left hand relaxed in front, light rhythmic breathing bounce, eyes forward; ends in exactly the same pose it starts so it loops."
- Attack_warrior (2 s): "From a combat ready stance, a powerful one-handed overhead swing with a short club in the right hand: quick wind-up over the right shoulder, hard downward strike in front, follow-through, then back to the ready stance. Feet planted."
- Attack_archer (2 s): "Archery shot: from a ready stance, raise a bow held in the LEFT hand with the left arm straight forward at shoulder height, draw the string back to the cheek with the right hand, hold briefly, release, then lower back to the ready stance. Feet planted."
- Attack_mage (2 s): "From a ready stance, flick a short wand held in the right hand forward toward the enemy with a snappy wrist and forearm thrust, small step forward, then return to the ready stance."
- Attack_cleric (2 s): "From a ready stance, swing a walking cane held in the right hand in a horizontal arc from right to left in front of the body, then return to the ready stance. Feet planted."
- Skill_warrior (2.5 s): "Spinning slash: from a ready stance, spin the whole body once while swinging a short club in the right hand in a wide horizontal circle, land balanced in the ready stance."
- Skill_archer (2.5 s): "Rapid triple shot: holding a bow in the LEFT hand extended forward, quickly draw and release the string three times with the right hand, then return to the ready stance."
- Skill_mage (2.5 s): "Spell channel: raise both hands in front of the chest, gather energy with a circular motion, then thrust both palms forward to release a spell, hold, return to the ready stance."
- Skill_cleric (2.5 s): "Healing prayer: hold a cane upright in the right hand, raise it high, place the left hand on the chest, bow the head briefly, then lower the cane back to the ready stance."

Duration deviation: the duration control accepts whole seconds only. Typing 2.5 shows 2.5 but rounds to 3 on blur, and the slider steps by 1 s. The four Skill clips were therefore generated at 3 s, not 2.5 s.

Free presets applied (Preset tab, no cost badge on the cards, balance unchanged at each step): `shoot` (take `shoot`), `standing_relax` (take `standing_relax`), `chop` (take `chop`).

Export: FBX, Blender preset, texture 512, Export Skeleton on, Number of Animations 12 (Choose Animations 12/12 after Select All; the 12 listed were exactly the 9 clips + 3 presets above), Animation stay in Place off. Export cost: 0 (balance 1540 before and after). One download: `Downloads/tactical+outfit+3d+model (1).zip` (6,831,521 bytes; the zip kept outside the project). Zip check with `python -I`: 6 entries, no absolute or `..` paths, testzip OK. Extracted into a new empty scratchpad dir, then copied to `ArtSource/hunters/_anim_library/tripo_export_class/`:
- `tripo_convert_14929035-2017-4838-9393-54e539bdf647.fbx` (5,358,108 bytes)
- `tripo_convert_14929035-2017-4838-9393-54e539bdf647.fbm/` (textures: basecolor, metallic, normal, roughness JPEG; rm PNG)

Take names in the FBX (12 AnimStacks, read from the binary; the 63-char cut is Tripo's):
1. `Combat ready stance: feet shoulder-width apart, knees slightly ` (BattleIdle)
2. `From a combat ready stance, a powerful one-handed overhead swin` (Attack_warrior)
3. `Archery shot: from a ready stance, raise a bow held in the LEFT` (Attack_archer)
4. `From a ready stance, flick a short wand held in the right hand ` (Attack_mage, trailing space)
5. `From a ready stance, swing a walking cane held in the right han` (Attack_cleric)
6. `Spinning slash: from a ready stance, spin the whole body once w` (Skill_warrior)
7. `Rapid triple shot: holding a bow in the LEFT hand extended forw` (Skill_archer)
8. `Spell channel: raise both hands in front of the chest, gather e` (Skill_mage)
9. `Healing prayer: hold a cane upright in the right hand, raise it` (Skill_cleric)
10. `standing_relax` (preset)
11. `shoot` (preset)
12. `chop` (preset)

Checks done: FBX header `Kaydara FBX Binary`. Counts: `Skin` x1, `Cluster` x65, `LimbNode` x130, `Deformer` x133 (same rig as the earlier exports).
Not done: the Blender posing check (bone moves mesh). This worker has no Blender access in this task, so the main session must run it before any import. The motion quality itself was not visually verified beyond the Tripo viewport preview.
Tripo tab closed after download.
