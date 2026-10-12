# elder — candidates

Batch: B2 (ArtSource/_briefs/B2_prompts.md). Status: 4 candidates saved. Pick suggested, main session makes final pick.

## Model check (before send, 2026-10-11 23:27)
- Model menu: "GPT-6" aria-checked=true (GPT-5.6 Sol and GPT-5.5 unchecked)
- Reasoning slider: [role=slider] aria-valuenow=3, aria-valuemax=4 (Extra High, 4th of 5 stops)

## Chat
- URL: https://chatgpt.com/c/6acb9cbe-71a4-83ee-9a47-03dff5fa1611 (new chat for this asset)
- Source site: chatgpt.com (web), GPT-6, Extra High
- Images returned in this response: 4 (separate images, md5 distinct)
- Downloads: viewer "이미지 다운로드" per image; images 1-4 mapped to candidate_A..D in order

## Prompt (sent verbatim)
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. A dignified older Korean man, the guild master, with swept-back silver hair and mature facial features. An open black suit jacket over a black waistcoat with restrained warm-metal edging, black trousers and polished shoes. A small abstract sunrise relief attached to the lapel, not a heraldic crest. No cane, crown or held object. Present-day Seoul hunter RPG, slim adult Korean anime-toon proportions, stylized anime toon 3D figure, full-body straight front view, symmetric A-pose, empty hands, arms and legs clearly separated from the body, both feet visible, plain light-grey background, generous margins, portrait 3:4. Solid attached details; no text, logos, crosses, weapons, floating parts, transparent geometry or dangling accessories. Vary hairstyle details and small colour accents between the four images while keeping the description.

## Candidates
- candidate_A.png (1086x1448): swept silver hair, open black jacket with copper-edged peak lapels and a patterned lapel facing, maroon tie, small round lapel pin, polished shoes, both feet visible. Fits; the lapel pin is a plain disc more than a sunrise.
- candidate_B.png (1086x1448): swept-back silver hair, open black jacket with copper edging, navy tie, small gold sunrise relief on the lapel, both feet visible. Fits; the sunrise relief reads clearly.
- candidate_C.png (1086x1448): wavy silver hair, open black jacket, patterned plum waistcoat with copper edging, a round lapel emblem, both feet visible. Fits; the hair is less swept-back and the plum pattern is an extra accent.
- candidate_D.png (1086x1448): swept-back silver hair, open black jacket with copper edging, dark green tie and pocket square, half-sun sunrise relief on the lapel, both feet visible. Fits; the green accents are extra.

## Suggested pick (main session makes the final pick)
- candidate_D.png: swept-back silver hair, the most literal abstract sunrise relief on the lapel, copper edging kept restrained and a clean silhouette with arms separated. Runner-up: candidate_B.png (navy tie, sunrise relief also clear).

## Tripo Studio (web) — B2 run, 2026-10-12
- Main final pick: candidate_D.png (main-approved B2 table; the Haiku note above was only a suggestion)
- Source site: studio.tripo3d.ai (web, Tripo subscription credits). Model H3.1 Best Quality, Geometry & Texture.
- Generation task: 14944c4a-ad6b-4204-aa51-81091d2f742c (https://studio.tripo3d.ai/workspace/generate/14944c4a-ad6b-4204-aa51-81091d2f742c). Cost 55, balance 305 -> 250.
- Retopo: Triangle (data-state=on), Smart Mesh on, target 15000 (set only after Triangle was selected, because the max drops to 10000 under Quad; textbox and slider aria-valuenow both 15000 of max 20000). Cost 35, balance 75 -> 40. Result: 13362 faces / 16548 vertices.
- Rig: Humanoid, Skeleton Preset Mixamo, Auto Rig. Cost 20, balance 40 -> 20. Skeleton shown in viewer. FBX scan: 130 LimbNode, 65 Cluster, 133 Deformer, 1 Skin object, 0 AnimationStack. Skin deformers are present; actual bone-weight check in Blender is NOT done here (Blender is out of scope for this worker), so it is still pending.
- Export: FBX, Texture Resolution 2k (verified: 2048x2048), Export Skeleton on, no animations, Blender preset (default). Zip extracted to ArtSource/npcs/elder/tripo/ (tripo_convert_c3585e8e-6def-4370-99b3-1e3c9367006c.fbx + .fbm textures).
- Balance after this asset: 20.

## Rig gate and runtime check (2026-10-12, headless Blender 5.2.1)
Source: `ArtSource/npcs/elder/tripo/tripo_convert_c3585e8e-6def-4370-99b3-1e3c9367006c.fbx`.
- 6697 vertices, 13362 triangles, 1 mesh, 1 material, 1 UV set, 0 actions. 52 weighted groups, max 4 influences per vertex.
- 0 of 6697 vertices unweighted. Posing RightArm 50 deg moved 1024 vertices (max 0.31 m), LeftUpLeg moved 1477, RightUpLeg 1493 (max 0.45 m). Passed.
- 65 bones; names, order and parents identical to the HumanoidAnimations source (`tripo_export/...0860c4ca...fbx`). Rest pose differs in proportions only (hips z 0.551 vs 0.587 at the library's own scale), which Unity Humanoid retargeting absorbs.
- Height 0.977 m, T/A-pose hands at x = +/-0.17 m, faces -Y (toe y < foot y), same as the library.
- Runtime path: `TownWorld.cs:53` `ArtLibrary.SpawnNpc(id)` -> `SpawnCharacter(NpcPath(id))`. `AbyssArtImporter.IsAnimated` includes `NPCs/`, so a `HUMANOID` marker next to the FBX makes it a Unity Humanoid exactly as for heroes; `IsTripo` (TRIPO marker) gives it the textured-hero material path and 2048 textures. `ArtLibrary.cs:113` loads `Art/HumanoidAnimations` when the Animator is human and the model has no own "Idle". Supported without code edits.
- Height: `SpawnNpc` does not normalise (the 1.3 m clamp at `ArtLibrary.cs:72-74` is for heroes only), so the FBX was scaled to the target 1.70 m at export. The old elder was 1.768 m. `CharacterModel.Height` is measured from renderer bounds in bind pose, the label sits at Height + 0.3.
- The only clip the NPC flow requests is "Talk" (`PlayOnce("Talk")`, then Idle); both come from the shared library, `Talk.fbx` added.

## Installed 2026-10-12
- Backup (copied, nothing deleted): `ArtSource/npcs/elder/backup_20261012/` = elder.fbx, elder.fbx.meta, elder_mat/, elder_tex/.
- Written in this order in `Assets/_Game/Resources/Art/NPCs/elder/`: `HUMANOID` and `TRIPO` markers (empty), `elder_tex/M_Elder_Tripo.png` (the Tripo base colour, 2048x2048 RGB, converted from JPEG), then `elder.fbx`. `elder.fbx.meta` kept untouched. Old elder_mat/ and elder_tex/ files were left in place (as for the hunters).
- `elder.fbx`: mesh "Body" (6697 vertices, 13362 triangles) + armature "Rig" (65 bones), no actions, material `M_Elder_Tripo` referencing `M_Elder_Tripo.png`. Whole model uniformly scaled by 1.7401 so the height is 1.700 m (bbox z 0 to 1.700, x +/-0.328, y +/-0.158), feet at z 0. Scaling applied to vertex data and bone rest positions; bone roll and weights untouched. Exporter settings: -Z forward / Y up, FBX_SCALE_ALL, add_leaf_bones False, bake_anim False, bake_space_transform False, path_mode STRIP. (bake_space_transform True, as in `abyss_bpy.export_fbx`, leaves a 90 degree rotation on the Body node after re-import; False gives rotation 0 like the installed hunters and like the library files.)
- Re-import check: 65 bones, order/parents identical, bone heads equal source x 1.7401 within 1.1e-6 m, bone axes within 6.4e-6, vertices within 2.5e-7 m, first 300 vertices' weights identical, 0 unweighted, 0 actions; RightArm 50 deg moved 1104 vertices, LeftUpLeg 1611. Front render with the PNG (`scratchpad/s3/elder_front.png`): textured black suit, silver hair, correct UVs.
- Not verified (Unity not run): Humanoid avatar mapping, material sync, how the 1.70 m elder looks against the town marker and service spot.
- Rollback: copy back `backup_20261012/elder.fbx`, delete `HUMANOID`, `TRIPO`, `elder_tex/M_Elder_Tripo.png`.
