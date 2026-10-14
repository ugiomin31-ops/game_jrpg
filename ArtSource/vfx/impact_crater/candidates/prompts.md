
## Batch B4 · impact_crater

- Model check (before prompt): model menu GPT-6 aria-checked=true; reasoning slider 3/4 (Extra High) verified.
- Chat: https://chatgpt.com/c/6acc117e-b9dc-83ee-b015-90df12ff8dce
- Source: chatgpt.com web, GPT-6 Extra High, 1 request, 4 images.
- Prompt (exact):
  > Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One shallow solid circular crater slab with a low chunky cracked rim, a recessed centre and broad radial grooves. No floating rocks, dust or tall spikes. (high three-quarter view, not edge-on) One opaque, solid, chunky stylized effect sculpture for a modern Korean hunter RPG. Matte neutral-grey material, clean simple surface shading, no painted glow gradients, transparency, particles, motion blur, text or background effects. Single complete object with generous margins on a plain mid-grey background, square 1:1. Vary proportions and silhouette within the brief.

- candidate_A.png: crater with tall chunky rim blocks and many small facets; rim reads taller than "low". Pass with reservation.
- candidate_B.png: crater with tall, busy rim pieces and a few small chunks on the outer edge. Pass with reservation.
- candidate_C.png: broad radial grooves, recessed centre, clean low-to-medium chunky cracked rim. Pass.
- candidate_D.png: low chunky cracked rim, recessed centre, radial grooves, no floating pieces. Pass.

- Suggested pick: candidate_D.png. Reason: closest to "low chunky cracked rim" with a clear recessed centre and broad radial grooves, and nothing floating.

### Tripo pass (B4-VFX-TRIPO, 2026-10-12)
- Main final pick: candidate_D.png (main-approved; matches sidecar suggestion)
- Tripo task: ba838f8f-33ce-434a-b4f2-eb997553454a (https://studio.tripo3d.ai/workspace/generate/ba838f8f-33ce-434a-b4f2-eb997553454a). Tripo titled it "stone circular cracked platform".
- Generate: H3.1 Best Quality, Geometry & Texture, 55 credits (2095 -> 2040)
- Retopo: Triangle, Smart Mesh on, target 900 (Tripo returned 1017 faces, above target; exported as-is per instruction), 35 credits (1825 -> 1790)
- Rig: none. Export: FBX, texture 1k, Blender preset (Tripo default)
- Export path: ArtSource/vfx/impact_crater/tripo/ (tripo_convert_*.fbx + .fbm, see folder)
- Faces after retopo: 1017 (target 900)

### Installed 2026-10-12 (V1 VFX-MESH-INSTALL)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/impact_crater.fbx. Headless Blender (Blender/lib/abyss_bpy.py export_fbx, forward -Z / up Y, scale 1, one mesh, one plain M_Vfx slot, no Tripo marker so force=False). Tris 873 (Tripo 1017: 92 hidden underside faces deleted, then collapse-decimated).
- Orientation/pivot/size: bottom-centre pivot, flat in Unity XZ, 2.4 m diameter, rim 0.34 m high; Col alpha fades to 0.3 over the outer 18% radius.
- Col vertex colour: white RGB + alpha fade mask (body 1, tips/edges 0.3, tail 0 where the contract asks).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_impact_crater.png, 512 px greyscale RGB, source Tripo albedo luminance; levels remapped by percentile (p5 -> .35 grooves, p50 -> .60 body, p95 -> .80 edges, clamp .30-.84).
- Verified by re-importing the FBX in Blender (bounds in Unity axes, single mesh, UV + Col present). Unity import check still pending (later task). Scripts: scratchpad v1/build.py, tex.py, verify.py.


### Restored 2026-10-13 (B5-RESTORE, user correction 3/4: Tripo retopo geometry retained; no credits)
- Local reduction REVERTED at the user's direction (same B6 rule: Tripo geometry, proportions, UVs and native texture are the source of truth). Historical reduced install above (1017 -> 873 tris) stays as history; counts below are source -> restored.
- Mesh reinstalled from ArtSource/vfx/impact_crater/tripo/ (raw retopo FBX): source -> restored tris 1017 -> 1017, verts 501 -> 501 (identical; ALL original triangles kept; no decimate/dissolve/merge). Raw dims [0.98, 0.976, 0.159] -> restored dims [2.4, 2.391, 0.39] Unity-frame (m): UNIFORM scale 2.4495 only - proportions preserved. Rigid axis map: none (rise axis +Z); pivot translation only.
- Original UVs preserved (per-corner values equal the raw import as a multiset on the original layout; loop-order-only differences where outward normals were recalculated - values identical). No planar/sweep UV rewrite. Aux Col alpha mask 0.3-1.0 kept as auxiliary data on the original UV layout (NOT a substitute for the original).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_impact_crater.png (512 px greyscale) is the AUXILIARY runtime mask VfxLibrary loads by name from Vfx/Textures/ - regenerated over the ORIGINAL UV layout from the original .fbm basecolor luminance (p5 0.369 / p50 0.600 / p95 0.796). The ORIGINAL basecolor is now ALSO shipped at Assets/_Game/Resources/Vfx/Textures/original/impact_crater_basecolor.jpeg (byte-identical md5 to the ArtSource raw; not claimed to be the runtime mask). Which texture drives appearance: the greyscale mesh_impact_crater.png mask (VfxLibrary.MaterialFor loads it by name; U-repeat for scroll effects); the original basecolor is available at runtime paths since this restore.
- Visual check: side-by-side raw vs restored renders at matching pose/light/camera reviewed in this session (scratchpad prev/b5_*.png). Unity import check pending (later task).
