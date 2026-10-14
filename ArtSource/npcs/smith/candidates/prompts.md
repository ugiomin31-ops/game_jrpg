# smith — candidates

Batch: B2 (ArtSource/_briefs/B2_prompts.md). Status: 4 candidates saved. Pick suggested, main session makes final pick.

## Model check (before send, 2026-10-11 23:20)
- Model menu: "GPT-6" aria-checked=true (GPT-5.6 Sol and GPT-5.5 unchecked)
- Reasoning slider: [role=slider] aria-valuenow=3, aria-valuemax=4 (Extra High, 4th of 5 stops)

## Chat
- URL: https://chatgpt.com/c/6acb9b01-6b8c-83ee-8801-7883d1c8c064 (new chat for this asset)
- Source site: chatgpt.com (web), GPT-6, Extra High
- Images returned in this response: 4 (separate images, md5 distinct)
- Downloads: viewer "이미지 다운로드" per image; images 1-4 mapped to candidate_A..D in order

## Prompt (sent verbatim)
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. A sturdy adult Korean man, the guild equipment craftsman, with short dark-brown hair and a short beard. Grey work shirt, dark trousers, a dark leather apron with muted brown edging, a lensless charcoal welding cap, thick work gloves and safety boots. The apron stays clear of the legs; no wrench or dangling tools. Present-day Seoul hunter RPG, slim adult Korean anime-toon proportions, stylized anime toon 3D figure, full-body straight front view, symmetric A-pose, empty hands, arms and legs clearly separated from the body, both feet visible, plain light-grey background, generous margins, portrait 3:4. Solid attached details; no text, logos, crosses, weapons, floating parts, transparent geometry or dangling accessories. Vary hairstyle details and small colour accents between the four images while keeping the description.

## Candidates
- candidate_A.png (1086x1448): full body, dark cap, grey shirt, dark leather apron with muted brown edging only, gloves, boots, both feet visible, arms separated. Fits closely; no extra colour accents.
- candidate_B.png (1086x1448): same build, apron edged brown with olive-green accents on the waist band and pockets. Fits; the olive accents go beyond "muted brown edging".
- candidate_C.png (1086x1448): same build, navy panels on shirt, pockets and gloves. Fits the silhouette; the navy accents are a stronger colour departure.
- candidate_D.png (1086x1448): same build, apron and pocket edging in orange-tan, orange stitching on trousers and shirt. Fits the silhouette; the orange accents are louder than the brief.

## Suggested pick (main session makes the final pick)
- candidate_A.png: the apron edging is the muted brown the brief names, there are no extra accent colours, the apron stays clear of the legs and the figure reads cleanly. Runner-up: candidate_B.png.

## Notes
- All four show a dark cap with a rounded crown; check at the pick stage that it reads as a lensless welding cap.

## Tripo submission (B2-NPC-TRIPO, second Tripo account, 2026-10-12)
- Main final pick: candidate_A.png (approved by main session; source site chatgpt.com, GPT-6 Extra High, prompt in the section above)
- Tripo Studio (studio.tripo3d.ai, web): HD Model, Geometry & Texture, AI model H3.1 - Best Quality
- Task id: 0e837bd1-d9f8-467a-aa89-39cf6ef3df5c (URL studio.tripo3d.ai/workspace/generate/0e837bd1-d9f8-467a-aa89-39cf6ef3df5c)
- Cost: 55 credits (balance 3645 -> 3590). Generated once, never regenerated.

## Tripo follow-up (B2-NPC-TRIPO, second Tripo account, 2026-10-12)
- Task id: 0e837bd1-d9f8-467a-aa89-39cf6ef3df5c. Source faces before retopo: 1993241 / vertices 1028415.
- Retopo: Triangle (data-state=on), Smart Mesh on, Polygon Count 15000 (textbox and slider both 15000). Cost 35 credits (balance 3480 -> 3445).
- Retopo result: Triangle, 14550 faces / 20314 vertices (target 15000 requested, Tripo output 14550). Balance 3480 -> 3445.
- Rig: Humanoid, Mixamo preset, Auto Rig. Skeleton visible on the Tripo viewer. Cost 20 (balance 3445 -> 3425). Skin weights NOT verified in Blender (excluded by B2 rules). Binary FBX scan: 2 Skin, 50 Cluster deformers present; no AnimationStack.
- Export: FBX (Mixamo preset in the dialog), Texture Resolution 2k, Export Skeleton on, no animations. Zip "workwear+outfit+3d+model.zip" (55.7 MB), path check clean, extracted to scratchpad and copied to ArtSource/npcs/smith/tripo/ (tripo_convert_6440a2f7-551b-4b84-b581-e4ddc363e256.fbx 28.4 MB + .fbm textures). Export costs no credits.
- Note: the FBX is 28 MB, much larger than the shopkeeper FBX (0.67 MB). The cause is not known yet; flag for the main session.
- Tab closed after download. Balance after this asset: 3425.
- Asset status: DONE (Tripo task 0e837bd1-d9f8-467a-aa89-39cf6ef3df5c). Credits this asset: generate 55 + retopo 35 + rig 20 = 110. Export free.

## Installed 2026-10-12
- Source: `ArtSource/npcs/smith/tripo/tripo_convert_6440a2f7-551b-4b84-b581-e4ddc363e256.fbx`. Same recipe as the elder (HUMANOID + TRIPO markers, mesh "Body" + armature "Rig", 65 Mixamo bones, no actions).
- Rig gate (headless Blender 5.2.1): 0 of 7280 vertices unweighted, 50 weighted groups, max 4 influences; RightArm 50 deg moved 1005 vertices (max 0.30 m), LeftUpLeg 1820, RightUpLeg 1848 (max 0.43 m). Source height 0.9764 (after baking).
- Bone names: names identical (mixamorig: prefix already present, no rename). The Mixamo-preset export has the armature object at scale 0.01 with bones in cm and the mesh at scale 0.01 rotated 90 deg X; this was baked (mesh vertices and bone positions in metres, object transforms identity). Sibling order differed (RightUpLeg subtree last); the armature was rebuilt with the same heads, tails, rolls and parents in the library bone order. The 28 MB source size is five lossless 2048 PNGs embedded in the FBX; only the base colour is used.
- Backup (copied, nothing deleted): `ArtSource/npcs/smith/backup_20261012/` = smith.fbx, smith.fbx.meta, smith_mat/, smith_tex/.
- Written in this order in `Assets/_Game/Resources/Art/NPCs/smith/`: `HUMANOID` and `TRIPO` markers (empty), `smith_tex/M_Smith_Tripo.png` (Tripo base colour, 2048x2048 RGB), then `smith.fbx`. `smith.fbx.meta` kept untouched (GUID). Old smith_mat/ and smith_tex/ files left in place.
- `smith.fbx`: mesh "Body" (7280 vertices, 14550 triangles) + armature "Rig" (65 bones), no actions, one material `M_Smith_Tripo` -> `M_Smith_Tripo.png`. Uniformly scaled by 1.7820 to a height of 1.74 m (bbox z 0 to 1.74, feet at z 0), faces -Y. Exporter: -Z forward / Y up, FBX_SCALE_ALL, add_leaf_bones False, bake_anim False, bake_space_transform False, path_mode STRIP. Triangle count kept at about 14k (key town NPC next to hunters), above the 6k-10k NPC target by decision.
- Re-import check: 65 bones, LIB order and parents identical to HumanoidAnimations, bone heads equal source x scale within ~1e-6 m, bone axes within 1e-5, vertices within 3e-7 m, first-300-vertex weights identical (zero-weight entries dropped only), 0 unweighted, 0 actions. Front render old vs new: `scratchpad/s10/smith_old_vs_new_front.png`.
- Not verified (Unity not run): Humanoid avatar mapping, material sync, look against the town marker.
- Rollback: copy back `backup_20261012/smith.fbx`, delete `HUMANOID`, `TRIPO`, `smith_tex/M_Smith_Tripo.png`.
