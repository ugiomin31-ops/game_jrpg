# shadow_tendril (P1) — ChatGPT web candidates, 2026-10-12

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High).
Chat: https://chatgpt.com/c/6acc7e2e-fc18-83e8-8987-fde5c573bd83
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. A thick segmented root narrowing into one hooked claw, not several tentacles. View: side three-quarter. One opaque matte-grey sculptural reference of the subject, chunky stylised game geometry, clearly readable silhouette, neutral shading, plain mid-grey background, entire object with margins, square image. No glow, transparency, particles, motion blur, text or symbols. Vary proportions and silhouette within the brief.

Results (one response, 4 images):
- candidate_A.png: thick segmented body, narrows to one hooked claw; ragged root end. Matches the brief.
- candidate_B.png: thin S-curved tendril whose base splits into several prongs; reads as multiple tentacles.
- candidate_C.png: thick root with a stump-like base, long body and one hooked claw; base is heavy.
- candidate_D.png: segmented body that narrows strongly to one hooked claw; lumpy base. Good alternative.

Suggested pick: candidate_A.png. Reason: thickest segmented root that narrows into one hooked claw with a single readable silhouette. candidate_D is the alternative if a narrower taper is wanted.

## Tripo (B5-TRIPO-2, 2026-10-12, third account)
- Image uploaded: candidates/candidate_A.png (the suggested pick above).
- Image-to-3D: studio.tripo3d.ai web, AI Model H3.1 Best Quality, Geometry & Texture: Ultra Mesh Quality on, Texture on, Texture Quality 2K, PBR on. Generate cost 45. Task id: 7bfcc3f2-fd74-49ca-8e86-c17dd4377b06
- Balance: 3700 -> 3655
- Retopology: Topology Triangle, Smart Mesh on, polygon count 700 target, result 733 faces (binary count). Cost 35. Balance: 3655 -> 3620
- Export: FBX, Blender preset, texture 2k. Local file: ArtSource/vfx/shadow_tendril/tripo/tripo_convert_25e12eb1-600d-4c6e-b932-666c328d6472.fbx (+ adjacent .fbm)

### Installed 2026-10-13 (B5-INSTALL-2, headless Blender, Blender/lib/abyss_bpy.py export_fbx)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/shadow_tendril.fbx. Tripo 733 tris -> 679 tris (collapse decimate to the 700 budget, skills_vfx.md section 4). Single mesh, one plain M_Vfx slot, `Col` white + alpha fade mask (root 0.45 -> 1 over the first 10 %, tip fades to 0.4), Tripo UVs kept.
- Orientation (brief: root at origin, rises +Y, curls toward +Z): Tripo had the long axis along Y with the thick root at +Y and the hooked tip at -Y curling toward +X. Mapped Tripo (x, y, z) -> Blender (z, -x, -y) (proper rotation), scaled so the height is 1.8 m, pivot = root base centre. Unity-axis bbox min [-0.433, 0.0, -0.514] max [0.338, 1.8, 0.609] (size [0.771, 1.8, 1.124] m); numerically checked: tip (y > 1.5) mean z +0.47, root mean z 0.
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_shadow_tendril.png, 512 px greyscale from the Tripo albedo luminance, levels p5 0.357 / p50 0.592 / p95 0.796.
- Tools/vfx/gen_effects.py run after install: effects.json 227 recipes, mesh layers 202 -> 217 (shadow_tendril 7 layers, rock_debris 8 layers); 62 layers still waiting for the 12 meshes not installed yet.


### Restored 2026-10-13 (B5-RESTORE, user correction 3/4: Tripo retopo geometry retained; no credits)
- Local reduction REVERTED at the user's direction (same B6 rule: Tripo geometry, proportions, UVs and native texture are the source of truth). Historical reduced install above (733 -> 679 tris) stays as history; counts below are source -> restored.
- Mesh reinstalled from ArtSource/vfx/shadow_tendril/tripo/ (raw retopo FBX): source -> restored tris 733 -> 733, verts 368 -> 368 (identical; ALL original triangles kept; no decimate/dissolve/merge). Raw dims [0.61, 0.977, 0.417] -> restored dims [1.124, 0.768, 1.8] Unity-frame (m): UNIFORM scale 1.8419 only - proportions preserved. Rigid axis map: y->z (rise axis +Z); pivot translation only.
- Original UVs preserved (per-corner values equal the raw import as a multiset on the original layout; loop-order-only differences where outward normals were recalculated - values identical). No planar/sweep UV rewrite. Aux Col alpha mask 0.4-1.0 kept as auxiliary data on the original UV layout (NOT a substitute for the original).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_shadow_tendril.png (512 px greyscale) is the AUXILIARY runtime mask VfxLibrary loads by name from Vfx/Textures/ - regenerated over the ORIGINAL UV layout from the original .fbm basecolor luminance (p5 0.357 / p50 0.592 / p95 0.796). The ORIGINAL basecolor is now ALSO shipped at Assets/_Game/Resources/Vfx/Textures/original/shadow_tendril_basecolor.jpeg (byte-identical md5 to the ArtSource raw; not claimed to be the runtime mask). Which texture drives appearance: the greyscale mesh_shadow_tendril.png mask (VfxLibrary.MaterialFor loads it by name; U-repeat for scroll effects); the original basecolor is available at runtime paths since this restore.
- Visual check: side-by-side raw vs restored renders at matching pose/light/camera reviewed in this session (scratchpad prev/b5_*.png). Unity import check pending (later task).
