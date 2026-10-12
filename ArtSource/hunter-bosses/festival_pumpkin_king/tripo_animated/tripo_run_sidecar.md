# festival_pumpkin_king - Tripo rig + animation + FBX export (TRIPO-RUN-3B, 2026-10-11, Haiku worker)
- Source: studio.tripo3d.ai, task 678a991a-bd56-439f-8e08-2c6fe3ba7df6 (retopo already 15641 faces; not redone).
- Auto Rig: Humanoid, Skeleton Preset Mixamo, Skeleton on. Cost 20. Balance 1790 -> 1770. Result on page: rigging completed, skeleton overlay visible.
- Animate presets (free, applied one at a time): idle, run, slash, cast_a_spell, hit_to_body_01, defeat, cheer. The export dialog listed 7 animations and all 7 were selected (7/7). Balance unchanged by presets (1770 after export, read at export time).
- Export: FBX, Blender preset, texture 2k, Export Skeleton on, Number of Animations 7, Animation stay in Place left off (default). Zip moved here as pumpkin_animated_export_2026-10-11.zip (python -I extraction, no unsafe entries).
- Output: tripo_convert_01272dde-5e3a-4da6-95d5-dda795376f36.fbx (+ .fbm). FBX byte check: Skin x1, Cluster x65, Deformer x133, LimbNode x130, take names present x4 each (idle, run, slash, cast_a_spell, hit_to_body_01, defeat, cheer).
- NOT DONE: Blender posing check (skin weights visually verified by posing a bone). Blender was out of scope for this run. The main session must do it before import.
