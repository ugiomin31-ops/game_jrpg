# shopkeeper — candidates

Batch: B2 (ArtSource/_briefs/B2_prompts.md). Status: 4 candidates saved. Pick suggested, main session makes final pick.

## Model check (before send, 2026-10-11 23:16)
- Model menu: "GPT-6" aria-checked=true (GPT-5.6 Sol and GPT-5.5 unchecked)
- Reasoning slider: [role=slider] aria-valuenow=3, aria-valuemax=4 (Extra High, 4th of 5 stops)

## Chat
- URL: https://chatgpt.com/c/6acb99ff-4a74-83ee-ac9f-0fe01863b412 (new chat for this asset)
- Source site: chatgpt.com (web), GPT-6, Extra High
- Images returned in this response: 4 (separate images, md5 distinct)
- Downloads: viewer "이미지 다운로드" per image; images 1-4 mapped to candidate_A..D in order

## Prompt (sent verbatim)
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. A cheerful middle-aged Korean man running the hunter market, wearing a plain teal shirt, a khaki pocketed work vest and trousers, brown work boots and a backwards rust-orange baseball cap. Short dark-brown hair. A compact calculator-shaped case sits flush against a vest pocket, with blank solid buttons; no held calculator. Present-day Seoul hunter RPG, slim adult Korean anime-toon proportions, stylized anime toon 3D figure, full-body straight front view, symmetric A-pose, empty hands, arms and legs clearly separated from the body, both feet visible, plain light-grey background, generous margins, portrait 3:4. Solid attached details; no text, logos, crosses, weapons, floating parts, transparent geometry or dangling accessories. Vary hairstyle details and small colour accents between the four images while keeping the description.

## Candidates
- candidate_A.png (1086x1448): full body, backwards orange cap, calculator on the right vest pocket with a strap, arms angled and separated, both feet visible. Fits; the calculator shows a keypad face.
- candidate_B.png (1086x1448): full body, cap, calculator flush on the right vest pocket, arms separated, both feet visible. Fits; the figure is slightly slimmer and the body reads a little narrower.
- candidate_C.png (1086x1448): full body, cap, calculator flush on the right pocket with a clip, brown-edged pockets, arms clearly separated from the body, both feet visible. Fits.
- candidate_D.png (1086x1448): full body, cap, calculator flush on a brown-trimmed pocket, arms separated, both feet visible. Fits; trouser cuffs are rolled.

## Suggested pick (main session makes the final pick)
- candidate_C.png: the calculator sits flush on the vest pocket as the brief asks, the arms are clearly separated from the body, the silhouette is clean and the cap reads well. Runner-up: candidate_A.png.

## Notes
- Calculator face shows a keypad pattern in all four; the brief asks for blank solid buttons, so a small deviation to check at the pick stage.

## Tripo submission (B2-NPC-TRIPO, second Tripo account, 2026-10-12)
- Main final pick: candidate_C.png (approved by main session; source site chatgpt.com, GPT-6 Extra High, prompt in the section above)
- Tripo Studio (studio.tripo3d.ai, web): HD Model, Geometry & Texture, AI model H3.1 - Best Quality
- Task id: bc94a7b1-e6ab-4ac7-9ec6-376808870742 (URL studio.tripo3d.ai/workspace/generate/bc94a7b1-e6ab-4ac7-9ec6-376808870742)
- Cost: 55 credits (balance 3700 -> 3645). Generated once, never regenerated.
- Retopo: Triangle (data-state=on), Smart Mesh on, Polygon Count 15000 (textbox and slider both 15000). Cost 35 credits (balance 3535 -> 3500). Source faces before retopo: 1974017.
- Retopo result: Triangle, 14120 faces / 19726 vertices (Tripo rounded the 15000 target down; target field was set to 15000). Cost 35 (balance 3535 -> 3500).
- Rig: Humanoid, Skeleton Preset Mixamo, Auto Rig. Cost 20 (balance 3500 -> 3480). Rig result: pending check (see below).
- Rig result: Humanoid, Mixamo preset, Skeleton overlay visible and fitted to the body on the Tripo viewer. Skin weights NOT verified: Blender check was excluded by the B2 task rules, so this check is still open. Cost 20 (balance 3500 -> 3480).
- Export: FBX (Blender preset), Texture Resolution 2k, Export Skeleton on, no animations. Zip "tactical+outfit+3d+model.zip" downloaded from Tripo (9.3 MB), zip path check clean, extracted to scratchpad and copied to ArtSource/npcs/shopkeeper/tripo/ (tripo_convert_ceb5606f-594c-4116-86f7-45dfcf797ec3.fbx 667436 bytes + .fbm textures). Export costs no credits.
- Faces 14120 / vertices 19732 (target 15000 requested; NPC normal target 6k-10k per CLAUDE.md: this is above that range, flag to main session).
- Tab closed after download. Balance after this asset: 3480.
- Asset status: DONE (Tripo task bc94a7b1-e6ab-4ac7-9ec6-376808870742). Credits this asset: generate 55 + retopo 35 + rig 20 = 110. Export free.

## Installed 2026-10-12
- Source: `ArtSource/npcs/shopkeeper/tripo/tripo_convert_ceb5606f-594c-4116-86f7-45dfcf797ec3.fbx`. Same recipe as the elder (HUMANOID + TRIPO markers, mesh "Body" + armature "Rig", 65 Mixamo bones, no actions).
- Rig gate (headless Blender 5.2.1): 0 of 7068 vertices unweighted, 52 weighted groups, max 4 influences; RightArm 50 deg moved 873 vertices (max 0.31 m), LeftUpLeg 2065, RightUpLeg 2071 (max 0.44 m). Source height 0.9785 m.
- Bone names: identical to the library (names, order, parents); no renaming.
- Backup (copied, nothing deleted): `ArtSource/npcs/shopkeeper/backup_20261012/` = shopkeeper.fbx, shopkeeper.fbx.meta, shopkeeper_mat/, shopkeeper_tex/.
- Written in this order in `Assets/_Game/Resources/Art/NPCs/shopkeeper/`: `HUMANOID` and `TRIPO` markers (empty), `shopkeeper_tex/M_Shopkeeper_Tripo.png` (Tripo base colour, 2048x2048 RGB), then `shopkeeper.fbx`. `shopkeeper.fbx.meta` kept untouched (GUID). Old shopkeeper_mat/ and shopkeeper_tex/ files left in place.
- `shopkeeper.fbx`: mesh "Body" (7068 vertices, 14120 triangles) + armature "Rig" (65 bones), no actions, one material `M_Shopkeeper_Tripo` -> `M_Shopkeeper_Tripo.png`. Uniformly scaled by 1.7578 to a height of 1.72 m (bbox z 0 to 1.72, feet at z 0), faces -Y. Exporter: -Z forward / Y up, FBX_SCALE_ALL, add_leaf_bones False, bake_anim False, bake_space_transform False, path_mode STRIP. Triangle count kept at about 14k (key town NPC next to hunters), above the 6k-10k NPC target by decision.
- Re-import check: 65 bones, LIB order and parents identical to HumanoidAnimations, bone heads equal source x scale within ~1e-6 m, bone axes within 1e-5, vertices within 3e-7 m, first-300-vertex weights identical (zero-weight entries dropped only), 0 unweighted, 0 actions. Front render old vs new: `scratchpad/s10/shopkeeper_old_vs_new_front.png`.
- Not verified (Unity not run): Humanoid avatar mapping, material sync, look against the town marker.
- Rollback: copy back `backup_20261012/shopkeeper.fbx`, delete `HUMANOID`, `TRIPO`, `shopkeeper_tex/M_Shopkeeper_Tripo.png`.
