
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
