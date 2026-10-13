# rock_debris (P1) — ChatGPT web candidates, 2026-10-12

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High).
Chat: https://chatgpt.com/c/6acc8096-3f78-83ee-ba73-d360e371c6d7
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. Five angular rocks arranged as one compact, clearly separated cluster. View: three-quarter. One opaque matte-grey sculptural reference of the subject, chunky stylised game geometry, clearly readable silhouette, neutral shading, plain mid-grey background, entire object with margins, square image. No glow, transparency, particles, motion blur, text or symbols. Vary proportions and silhouette within the brief.

Results (one response, 4 images):
- candidate_A.png: five rocks, one tall central rock; the big bottom-left rock touches the centre rock. Compact.
- candidate_B.png: five rocks spread in a wide row, low profile; not compact.
- candidate_C.png: five rocks, one large left rock, one tall rock; some rocks overlap at the base.
- candidate_D.png: five rocks, one tall rock at top-centre, the others separated; most compact and readable.

Suggested pick: candidate_D.png. Reason: five angular rocks in a compact cluster with the most separation between the pieces. Note: no candidate is fully separated; candidate_A is the alternative.

## Tripo (B5-TRIPO-2, 2026-10-12, third account)
- Image uploaded: candidates/candidate_D.png (the suggested pick above).
- Image-to-3D: studio.tripo3d.ai web, AI Model H3.1 Best Quality, Geometry & Texture: Ultra Mesh Quality on, Texture on, Texture Quality 2K, PBR on. Generate cost 45. Task id: 99061e0a-19f5-4d52-bad4-aad75ec4f635
- Balance: 3620 -> 3575
- Retopology: Topology Triangle, Smart Mesh on, polygon count 800 target, result 958 faces (binary count). Cost 35. Balance: 3575 -> 3540
- Export: FBX, Blender preset, texture 2k. Local file: ArtSource/vfx/rock_debris/tripo/tripo_convert_3f37eedf-0d02-434a-94a6-424e28813eb4.fbx (+ adjacent .fbm)

### Installed 2026-10-13 (B5-INSTALL-2, headless Blender, Blender/lib/abyss_bpy.py export_fbx)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/rock_debris.fbx. Tripo 958 tris -> 388 tris (budget 400). Single mesh, one plain M_Vfx slot, `Col` white / alpha 1, Tripo UVs kept. Cluster of rock chunks, pivot = bbox centre, longest side 0.6 m.
- Unity-axis bbox min [-0.303, -0.244, -0.244] max [0.301, 0.242, 0.245] (size [0.604, 0.486, 0.489] m).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_rock_debris.png, 256 px greyscale, levels p5 0.361 / p50 0.600 / p95 0.796.
- gen_effects.py: see shadow_tendril (mesh layers 202 -> 217 in total).


### Restored 2026-10-13 (B5-RESTORE, user correction 3/4: Tripo retopo geometry retained; no credits)
- Local reduction REVERTED at the user's direction (same B6 rule: Tripo geometry, proportions, UVs and native texture are the source of truth). Historical reduced install above (958 -> 388 tris) stays as history; counts below are source -> restored.
- Mesh reinstalled from ArtSource/vfx/rock_debris/tripo/ (raw retopo FBX): source -> restored tris 958 -> 958, verts 477 -> 477 (identical; ALL original triangles kept; no decimate/dissolve/merge). Raw dims [0.977, 0.797, 0.79] -> restored dims [0.485, 0.49, 0.6] Unity-frame (m): UNIFORM scale 0.614 only - proportions preserved. Rigid axis map: axis0->z (rise axis +Z); pivot translation only.
- Original UVs preserved (per-corner values equal the raw import as a multiset on the original layout; loop-order-only differences where outward normals were recalculated - values identical). No planar/sweep UV rewrite. Aux Col alpha mask 1.0-1.0 kept as auxiliary data on the original UV layout (NOT a substitute for the original).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_rock_debris.png (256 px greyscale) is the AUXILIARY runtime mask VfxLibrary loads by name from Vfx/Textures/ - regenerated over the ORIGINAL UV layout from the original .fbm basecolor luminance (p5 0.361 / p50 0.600 / p95 0.796). The ORIGINAL basecolor is now ALSO shipped at Assets/_Game/Resources/Vfx/Textures/original/rock_debris_basecolor.jpeg (byte-identical md5 to the ArtSource raw; not claimed to be the runtime mask). Which texture drives appearance: the greyscale mesh_rock_debris.png mask (VfxLibrary.MaterialFor loads it by name; U-repeat for scroll effects); the original basecolor is available at runtime paths since this restore.
- Visual check: side-by-side raw vs restored renders at matching pose/light/camera reviewed in this session (scratchpad prev/b5_*.png). Unity import check pending (later task).
