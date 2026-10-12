
## Batch B4 · energy_arrow

- Model check (before prompt): model menu GPT-6 aria-checked=true; reasoning slider 3/4 (Extra High) verified.
- Chat: https://chatgpt.com/c/6acc1054-8c18-83e8-a43e-92e5aa7d5bf1
- Source: chatgpt.com web, GPT-6 Extra High, 1 request, 4 images.
- Prompt (exact):
  > Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One faceted energy arrow with a broad pointed arrowhead, a short sturdy shaft and three thick swept fins; no feathers, wood, bow or separate trail. (side-biased three-quarter view) One opaque, solid, chunky stylized effect sculpture for a modern Korean hunter RPG. Matte neutral-grey material, clean simple surface shading, no painted glow gradients, transparency, particles, motion blur, text or background effects. Single complete object with generous margins on a plain mid-grey background, square 1:1. Vary proportions and silhouette within the brief.

- candidate_A.png: broad head with barbs, tail with three fins, clean opaque grey. Pass with reservation (head reads as split).
- candidate_B.png: clear head and short shaft, but only two swept fins at the tail. Reject (fin count).
- candidate_C.png: broad pointed head, short sturdy shaft, three swept tail fins, side-biased three-quarter view. Pass.
- candidate_D.png: broad head, three tail fins, slightly heavier shaft. Pass.

- Suggested pick: candidate_C.png. Reason: meets all brief points (broad pointed head, sturdy shaft, three thick swept fins, clean opaque surface) with the clearest silhouette.

### Tripo pass (B4-VFX-TRIPO, 2026-10-12)
- Main final pick: candidate_C.png (main-approved; matches sidecar suggestion)
- Tripo task: b41ff4e5-eb91-43c4-ba1b-92757d5ece01 (https://studio.tripo3d.ai/workspace/generate/b41ff4e5-eb91-43c4-ba1b-92757d5ece01). Tripo titled it "low poly spear 3d model".
- Generate: H3.1 Best Quality, Geometry & Texture, 55 credits (2205 -> 2150)
- Retopo: Triangle, Smart Mesh on, target 500 (Tripo returned 674 faces, above target; exported as-is per instruction), 35 credits (1895 -> 1860)
- Rig: none. Export: FBX, texture 1k, Blender preset (Tripo default)
- Export path: ArtSource/vfx/energy_arrow/tripo/ (tripo_convert_a414c4c1-d6a2-40d8-adf8-86c8a5b3095a.fbx + .fbm)
- Faces after retopo: 674 (target 500)

### Installed 2026-10-12 (V1 VFX-MESH-INSTALL)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/energy_arrow.fbx. Headless Blender (Blender/lib/abyss_bpy.py export_fbx, forward -Z / up Y, scale 1, one mesh, one plain M_Vfx slot, no Tripo marker so force=False). Tris 388 (Tripo 674, collapse-decimated).
- Orientation/pivot/size: tip toward Unity +Z (Blender +Y, rotated +90 deg about Z), volume centre-of-mass pivot, 1.0 m long (0.995), fins fan vertically; Col alpha 0 at the fin tails ramping to 1 by 18% of length, tip 0.3.
- Col vertex colour: white RGB + alpha fade mask (body 1, tips/edges 0.3, tail 0 where the contract asks).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_energy_arrow.png, 256 px greyscale RGB, source Tripo albedo luminance; levels remapped by percentile (p5 -> .35 grooves, p50 -> .60 body, p95 -> .80 edges, clamp .30-.84).
- Verified by re-importing the FBX in Blender (bounds in Unity axes, single mesh, UV + Col present). Unity import check still pending (later task). Scripts: scratchpad v1/build.py, tex.py, verify.py.
