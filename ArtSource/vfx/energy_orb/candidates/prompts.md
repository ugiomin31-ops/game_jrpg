
## Batch B4 · energy_orb

- Model check (before prompt): model menu GPT-6 aria-checked=true; reasoning slider 3/4 (Extra High) verified.
- Chat: https://chatgpt.com/c/6acc10eb-8df4-83ee-95fb-b213aeef6910
- Source: chatgpt.com web, GPT-6 Extra High, 1 request, 4 images.
- Prompt (exact):
  > Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One solid round sphere with two broad raised swirling bands integrated into its surface, crossed like planet bands but not detached rings; shallow grooves separate the bands. No hollow transparent shell. (three-quarter view) One opaque, solid, chunky stylized effect sculpture for a modern Korean hunter RPG. Matte neutral-grey material, clean simple surface shading, no painted glow gradients, transparency, particles, motion blur, text or background effects. Single complete object with generous margins on a plain mid-grey background, square 1:1. Vary proportions and silhouette within the brief.

- candidate_A.png: round sphere, two raised bands crossing with clean grooves, opaque grey. Pass.
- candidate_B.png: round sphere, two raised bands with smooth grooves, slightly less defined band edges. Pass with reservation.
- candidate_C.png: egg-shaped, not a round sphere. Reject (silhouette).
- candidate_D.png: round sphere with bands, but the surface is heavily faceted, which breaks the clean simple shading. Pass with reservation.

- Suggested pick: candidate_A.png. Reason: round sphere with two integrated, clearly crossed bands, shallow grooves and the cleanest surface shading.

### Tripo pass (B4-VFX-TRIPO, 2026-10-12)
- Main final pick: candidate_A.png (main-approved; matches sidecar suggestion)
- Tripo task: e71754a6-e6c6-47fe-8c3b-ca66e0881901 (https://studio.tripo3d.ai/workspace/generate/e71754a6-e6c6-47fe-8c3b-ca66e0881901). Tripo titled it "spherical abstract ball with interwoven bands".
- Generate: H3.1 Best Quality, Geometry & Texture, 55 credits (2150 -> 2095)
- Retopo: Triangle, Smart Mesh on, target 500 (Tripo returned 540 faces), 35 credits (1860 -> 1825)
- Visual note: after retopo the surface reads as faceted plates; the two crossed bands are less legible than the pre-retopo mesh. Exported as-is; main session to judge.
- Rig: none. Export: FBX, texture 1k, Blender preset (Tripo default)
- Export path: ArtSource/vfx/energy_orb/tripo/ (tripo_convert_fff66dc6-4c65-4cbb-98a9-7c24351d1bfa.fbx + .fbm)
- Faces after retopo: 540 (target 500)

### Installed 2026-10-12 (V1 VFX-MESH-INSTALL)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/energy_orb.fbx. Headless Blender (Blender/lib/abyss_bpy.py export_fbx, forward -Z / up Y, scale 1, one mesh, one plain M_Vfx slot, no Tripo marker so force=False). Tris 484 (Tripo 540, collapse-decimated).
- Orientation/pivot/size: centre pivot, 0.6 m. Bands survive in the geometry (two crossing raised ribbons) and in the albedo shading, so no extra bake was needed; the dark camo blotches of the albedo remain in the mask (reads as surface variation); Col alpha 1 everywhere.
- Col vertex colour: white RGB + alpha fade mask (body 1, tips/edges 0.3, tail 0 where the contract asks).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_energy_orb.png, 256 px greyscale RGB, source Tripo albedo luminance; levels remapped by percentile (p5 -> .35 grooves, p50 -> .60 body, p95 -> .80 edges, clamp .30-.84).
- Verified by re-importing the FBX in Blender (bounds in Unity axes, single mesh, UV + Col present). Unity import check still pending (later task). Scripts: scratchpad v1/build.py, tex.py, verify.py.


### Restored 2026-10-13 (B5-RESTORE, user correction 3/4: Tripo retopo geometry retained; no credits)
- Local reduction REVERTED at the user's direction (same B6 rule: Tripo geometry, proportions, UVs and native texture are the source of truth). Historical reduced install above (540 -> 484 tris) stays as history; counts below are source -> restored.
- Mesh reinstalled from ArtSource/vfx/energy_orb/tripo/ (raw retopo FBX): source -> restored tris 540 -> 540, verts 272 -> 272 (identical; ALL original triangles kept; no decimate/dissolve/merge). Raw dims [0.97, 0.963, 0.959] -> restored dims [0.593, 0.595, 0.6] Unity-frame (m): UNIFORM scale 0.6183 only - proportions preserved. Rigid axis map: axis0->z (rise axis +Z); pivot translation only.
- Original UVs preserved (per-corner values equal the raw import as a multiset on the original layout; loop-order-only differences where outward normals were recalculated - values identical). No planar/sweep UV rewrite. Aux Col alpha mask 1.0-1.0 kept as auxiliary data on the original UV layout (NOT a substitute for the original).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_energy_orb.png (256 px greyscale) is the AUXILIARY runtime mask VfxLibrary loads by name from Vfx/Textures/ - regenerated over the ORIGINAL UV layout from the original .fbm basecolor luminance (p5 0.427 / p50 0.596 / p95 0.792). The ORIGINAL basecolor is now ALSO shipped at Assets/_Game/Resources/Vfx/Textures/original/energy_orb_basecolor.jpeg (byte-identical md5 to the ArtSource raw; not claimed to be the runtime mask). Which texture drives appearance: the greyscale mesh_energy_orb.png mask (VfxLibrary.MaterialFor loads it by name; U-repeat for scroll effects); the original basecolor is available at runtime paths since this restore.
- Visual check: side-by-side raw vs restored renders at matching pose/light/camera reviewed in this session (scratchpad prev/b5_*.png). Unity import check pending (later task).
