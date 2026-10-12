
## Batch B4 · shield_dome

- Model check (before prompt): model menu GPT-6 aria-checked=true; reasoning slider 3/4 (Extra High) verified.
- Chat: https://chatgpt.com/c/6acc120d-54a8-83ee-815d-3847f25dc1e8
- Source: chatgpt.com web, GPT-6 Extra High, 1 request, 4 images.
- Prompt (exact):
  > Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One open-bottom hemispherical shield shell made of connected broad hexagonal panels with a thick continuous base rim; no detached tiles, not a closed sphere. (low three-quarter view showing the open underside) One opaque, solid, chunky stylized effect sculpture for a modern Korean hunter RPG. Matte neutral-grey material, clean simple surface shading, no painted glow gradients, transparency, particles, motion blur, text or background effects. Single complete object with generous margins on a plain mid-grey background, square 1:1. Vary proportions and silhouette within the brief.

- candidate_A.png: wide hemisphere, hex panels, thick base rim, open underside visible. Pass with reservation (rather flat profile).
- candidate_B.png: taller, egg-like ovoid profile rather than a hemisphere. Reject (silhouette).
- candidate_C.png: hemispherical shell, connected hex panels, thick continuous base rim, open underside visible. Pass.
- candidate_D.png: hemispherical shell with larger irregular panels; base rim fine. Pass with reservation (panels less hexagonal).

- Suggested pick: candidate_C.png. Reason: the most accurate hemisphere with connected hexagonal panels and a thick continuous base rim, and an open underside that reads clearly.

### Tripo pass (B4-VFX-TRIPO, 2026-10-12)
- Main final pick: candidate_A.png (main-approved; the sidecar suggestion above was candidate_C.png)
- Tripo task: a65981fe-9c32-4b55-8fc5-2633735a3882 (https://studio.tripo3d.ai/workspace/generate/a65981fe-9c32-4b55-8fc5-2633735a3882). Tripo titled it "geodesic dome helmet".
- Generate: H3.1 Best Quality, Geometry & Texture, 55 credits (2040 -> 1985)
- Retopo: Triangle, Smart Mesh on, target 1000 (Tripo returned 1178 faces, above target; exported as-is per instruction), 35 credits (1790 -> 1755)
- Visual note: after retopo several hex panels show dark circular recesses; check in Blender before import.
- Rig: none. Export: FBX, texture 1k, Blender preset (Tripo default)
- Export path: ArtSource/vfx/shield_dome/tripo/ (tripo_convert_*.fbx + .fbm, see folder)
- Faces after retopo: 1178 (target 1000)

### Installed 2026-10-12 (V1 VFX-MESH-INSTALL)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/shield_dome.fbx. Headless Blender (Blender/lib/abyss_bpy.py export_fbx, forward -Z / up Y, scale 1, one mesh, one plain M_Vfx slot, no Tripo marker so force=False). Tris 970 (Tripo 1178, collapse-decimated).
- Orientation/pivot/size: base-centre pivot, +Y up, 2.4 m diameter / 1.62 m high, open underside with the inner shell kept; dark circular recesses of the albedo were normalised (grey-closing lift of blobs larger than the seams, mean lift 0.23, seams kept); Col alpha 0.3 at the base edge rising to 1 by 8% height.
- Col vertex colour: white RGB + alpha fade mask (body 1, tips/edges 0.3, tail 0 where the contract asks).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_shield_dome.png, 512 px greyscale RGB, source Tripo albedo luminance + recess normalisation; levels remapped by percentile (p5 -> .35 grooves, p50 -> .60 body, p95 -> .80 edges, clamp .30-.84).
- Verified by re-importing the FBX in Blender (bounds in Unity axes, single mesh, UV + Col present). Unity import check still pending (later task). Scripts: scratchpad v1/build.py, tex.py, verify.py.
