# h_yuna candidates (batch B1, 2026-10-11)

Prompt (exact, sent once):
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. Adult nursing student wearing a white cardigan over light-blue scrubs, white sneakers, low ponytail and an attached hip first-aid pouch. A plain red armband without cross, lettering or insignia; hair and pouch straps compact and attached. Adult Korean, slim adult anime proportions about seven heads tall, stylized anime toon 3D figure for a present-day Seoul hunter RPG. Full-body straight front view, symmetric A-pose, empty hands, arms and legs clearly separated from the body, both feet visible, plain light grey background, generous margins, portrait 3:4. No text, logos, floating parts, transparent geometry, weapons or props in hand. Vary hairstyle details, colour accents and small outfit details between the four images while keeping the description.

Model: GPT-6, reasoning Extra High (slider 3 of 4) verified before sending.
Chat: https://chatgpt.com/c/6acb78e0-a2a0-83ec-bc57-c0e8663bed14
Images: 4 separate images, 1086x1448 PNG (portrait), no follow-up needed.

Per image:
- candidate_A.png: white cardigan, blue scrubs with navy piping, hip pouch on the left side, red armband, white sneakers, low ponytail with blue tie.
- candidate_B.png: low ponytail, white cardigan, pouch on a thigh strap with grey-lilac accents, plain red armband, white sneakers. Strap reads as attached.
- candidate_C.png: low ponytail, pouch on a hip strap with mint accents, cardigan with mint trim, red armband, white sneakers. Mint trim is busier.
- candidate_D.png: low ponytail with pearl hair tie, pouch on coral strap, coral trim on shoes and pocket, red armband.

Suggested pick (main decides): candidate_B.png. Reason: plainest attached pouch and strap, fewest accent colours, armband and silhouette read clearly, feet and arms clear.

Method note: copy-image via real thumbnail click then copy button; clipboard verified by sentinel and per-file checksum; all four files differ.

## B1-TRIPO (2026-10-11 21:53)
Main final pick: candidate_A.png (main-approved; the prompt suggested B, main overrode).
Source: studio.tripo3d.ai (user Chrome), Image to 3D, model H3.1 - Best Quality, Geometry & Texture (Ultra Mesh on, Texture 4K for generation, Triangle, polycount 2000000 default). Generate cost 55.
Tripo task: https://studio.tripo3d.ai/workspace/generate/475fa2f0-623a-4efd-bcf3-ba143ff3c09c
Status: generation submitted once. Retopo, rig and export NOT yet done (see report).

## B1-FINISH (2026-10-11, Haiku worker)
Retopo: Tripo Retopology (Triangle, Smart Mesh on), target 15000 set via textbox and verified slider aria-valuenow=15000. Cost 35 credits. Balance before 1065, after 1030. Result faces 14221 (vertices 16672). Within hero range (10k-20k).
Rig: Humanoid, Mixamo preset, Auto Rig. Cost 20 credits. Balance after 1010. Skeleton overlay visible in Tripo viewport. Skin weights NOT verified (Blender check skipped per task rule NO Blender in this batch; main session must verify in Blender before import). No animations added.
Export: FBX, texture 2k, Export Skeleton on, default preset Blender (preset tab left at default). Export cost: none shown.
Files: ArtSource/hunters/h_yuna/tripo/tripo_convert_d7efbf92-72c9-4a92-b370-eef3ad29b6ad.fbx (+ .fbm texture folder, 5 maps). Source zip medical+scrubs+3d+model.zip, traversal check clean.
Tripo tab closed after download.

## Installed 2026-10-11
Installed Tripo model (Humanoid Mixamo rig, 14221 tris, 2k texture, no animation takes) as Assets/_Game/Resources/Art/Characters/h_yuna/h_yuna.fbx (GUID kept in h_yuna.fbx.meta). Source: ArtSource/hunters/h_yuna/tripo/*.fbx. Headless Blender 5.2.1 re-export: whole model (mesh + armature, rest pose untouched) uniformly scaled so the height equals the old VRoid model, feet at z=0, facing -Y, axes -Z forward / Y up (abyss_bpy.export_fbx settings), add_leaf_bones off, bone names/order identical to the HumanoidAnimations source. Material M_HYuna_Tripo, base colour h_yuna/h_yuna_tex/M_HYuna_Tripo.png (2048). Markers HUMANOID + TRIPO written in the character folder before the FBX/PNG. Old model, meta and _tex/_mat copies: ArtSource/hunters/h_yuna/backup_20261011/. Unity import not run (unverified).
