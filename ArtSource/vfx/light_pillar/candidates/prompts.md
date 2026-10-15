
## Batch B4 · light_pillar

- Model check (before prompt): model menu GPT-6 aria-checked=true; reasoning slider 3/4 (Extra High) verified.
- Chat: https://chatgpt.com/c/6acc12fb-9dd4-83ee-8843-bdd26483aebd
- Source: chatgpt.com web, GPT-6 Extra High, 1 request, 4 images. (First attempt in a fresh tab found no model button and sent nothing; the retry is the one logged here.)
- Prompt (exact):
  > Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One upright solid hexagonal column with an integrated flared base ring and a gently tapering top, broad clean facets; no rays or hovering rings. (low three-quarter view) One opaque, solid, chunky stylized effect sculpture for a modern Korean hunter RPG. Matte neutral-grey material, clean simple surface shading, no painted glow gradients, transparency, particles, motion blur, text or background effects. Single complete object with generous margins on a plain mid-grey background, square 1:1. Vary proportions and silhouette within the brief.

- candidate_A.png: upright hexagonal column, flared base ring, gently tapering top, clean facets. Pass (view reads closer to front than low three-quarter).
- candidate_B.png: squat, block-like column with a wide cap and bulky base; little taper. Pass with reservation (proportions).
- candidate_C.png: bottle-like column with a pinched neck and a strong taper. Pass with reservation (taper too strong).
- candidate_D.png: tall column with protruding blocks and a pointed top cap; too busy against the brief. Reject.

- Suggested pick: candidate_A.png. Reason: the closest match to the brief, with a clean hexagonal column, a flared base ring, a gentle top taper and no extra parts.

### Tripo pass (B4-VFX-TRIPO, 2026-10-12)
- Main final pick: candidate_A.png (main-approved)
- Tripo task: a16d60a7-00b8-4e7a-86e9-ff1cee3ec7be (https://studio.tripo3d.ai/workspace/generate/a16d60a7-00b8-4e7a-86e9-ff1cee3ec7be). Tripo titled it "slender faceted obelisk with a multi-tier base".
- Generate: H3.1 Best Quality, Geometry & Texture, 55 credits (1985 -> 1930)
- Retopo: Triangle, Smart Mesh on, target 600, 35 credits (1755 -> 1720). Retopo was started once from the retopo page; the 35-credit charge is the only one (1755 -> 1720). Retopo took several minutes to finish.
- Result: 460 faces (target 600, under target)
- Rig: none. Export: FBX, texture 1k, Blender preset (Tripo default)
- Export path: ArtSource/vfx/light_pillar/tripo/ (tripo_convert_*.fbx + .fbm, see folder)

### Installed 2026-10-12 (V1 VFX-MESH-INSTALL)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/light_pillar.fbx. Headless Blender (Blender/lib/abyss_bpy.py export_fbx, forward -Z / up Y, scale 1, one mesh, one plain M_Vfx slot, no Tripo marker so force=False). Tris 460 (Tripo 460, untouched).
- Orientation/pivot/size: base-centre pivot, +Y up, 3.0 m tall (1.2 x 1.1 m footprint); Col alpha 1 up to 88% height, tip 0.3.
- Col vertex colour: white RGB + alpha fade mask (body 1, tips/edges 0.3, tail 0 where the contract asks).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_light_pillar.png, 512 px greyscale RGB, source Tripo albedo luminance; levels remapped by percentile (p5 -> .35 grooves, p50 -> .60 body, p95 -> .80 edges, clamp .30-.84).
- Verified by re-importing the FBX in Blender (bounds in Unity axes, single mesh, UV + Col present). Unity import check still pending (later task). Scripts: scratchpad v1/build.py, tex.py, verify.py.


### Restored 2026-10-13 (B5-RESTORE, user correction 3/4: Tripo retopo geometry retained; no credits)
- Local reduction REVERTED at the user's direction (same B6 rule: Tripo geometry, proportions, UVs and native texture are the source of truth). Historical reduced install above (460 -> 460 tris) stays as history; counts below are source -> restored.
- Mesh reinstalled from ArtSource/vfx/light_pillar/tripo/ (raw retopo FBX): source -> restored tris 460 -> 460, verts 236 -> 236 (identical; ALL original triangles kept; no decimate/dissolve/merge). Raw dims [0.392, 0.358, 0.978] -> restored dims [1.204, 1.098, 3.0] Unity-frame (m): UNIFORM scale 3.069 only - proportions preserved. Rigid axis map: none (rise axis +Z); pivot translation only.
- Original UVs preserved (per-corner values equal the raw import as a multiset on the original layout; loop-order-only differences where outward normals were recalculated - values identical). No planar/sweep UV rewrite. Aux Col alpha mask 1.0-1.0 kept as auxiliary data on the original UV layout (NOT a substitute for the original).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_light_pillar.png (512 px greyscale) is the AUXILIARY runtime mask VfxLibrary loads by name from Vfx/Textures/ - regenerated over the ORIGINAL UV layout from the original .fbm basecolor luminance (p5 0.349 / p50 0.600 / p95 0.796). The ORIGINAL basecolor is now ALSO shipped at Assets/_Game/Resources/Vfx/Textures/original/light_pillar_basecolor.jpeg (byte-identical md5 to the ArtSource raw; not claimed to be the runtime mask). Which texture drives appearance: the greyscale mesh_light_pillar.png mask (VfxLibrary.MaterialFor loads it by name; U-repeat for scroll effects); the original basecolor is available at runtime paths since this restore.
- Visual check: side-by-side raw vs restored renders at matching pose/light/camera reviewed in this session (scratchpad prev/b5_*.png). Unity import check pending (later task).
