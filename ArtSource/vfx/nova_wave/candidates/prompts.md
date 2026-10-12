# nova_wave (P1) — ChatGPT web candidates, 2026-10-12

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High).
Chat: https://chatgpt.com/c/6acc7db6-fb20-83ee-9b75-6da7c13704a9
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. A thick annular wave with a curling outer crest and an open centre. View: high three-quarter. One opaque matte-grey sculptural reference of the subject, chunky stylised game geometry, clearly readable silhouette, neutral shading, plain mid-grey background, entire object with margins, square image. No glow, transparency, particles, motion blur, text or symbols. Vary proportions and silhouette within the brief.

Results (one response, 4 images):
- candidate_A.png: thick wave with a curling crest, open centre; the body is a closed rounded mass rather than a flat annulus.
- candidate_B.png: flat annular wave ring with a single curling crest on the back and an open centre; clean silhouette.
- candidate_C.png: rocky, faceted body with a crest; reads more as a boulder than a wave.
- candidate_D.png: annular wave with several curling crests around the rim and an open centre; crests are busier.

Suggested pick: candidate_B.png. Reason: clearest annular wave with one curling outer crest and an open centre, clean readable silhouette, and no closed rounded mass.

## Tripo pass (B5-TRIPO-1, 2026-10-12, second account)
- Main final pick: candidate_B.png (as specified)
- Generate: task b401102f-83fd-463c-aa1e-5e44bfb29bd9, https://studio.tripo3d.ai/workspace/generate/b401102f-83fd-463c-aa1e-5e44bfb29bd9, H3.1 Best Quality, Geometry & Texture, HD Model, 55 credits (1430 -> 1375)
- Retopo: Triangle, Smart Mesh on, target 900, 35 credits (1030 -> 995), result 880 faces
- Export: FBX, Blender preset, texture 1K, no rig. Path: ArtSource/vfx/nova_wave/tripo/


### Account-switch verification addendum (2026-10-12)
- Main final pick: candidate_B.png (task-selected; main-session final approval not performed by this worker).
- Source task: b401102f-83fd-463c-aa1e-5e44bfb29bd9; https://studio.tripo3d.ai/workspace/generate/b401102f-83fd-463c-aa1e-5e44bfb29bd9
- Final stage: retopo FBX, Triangle, Smart Mesh on, requested 900; **binary-verified 860 faces**, superseding earlier screenshot readings. No second paid retopo.
- H3.1 Best Quality / Geometry & Texture: 55 (1430 -> 1375); retopo 35 (1030 -> 995); export free.
- Exact local export: C:/Users/User/Desktop/game/ArtSource/vfx/nova_wave/tripo/tripo_convert_0221fd4e-e756-4a92-b0d1-1ee1a3f4f18d.fbx with adjacent .fbm textures; 1024px requested, no rig. Unity/Blender not run; no import approval implied.

### Installed 2026-10-12 (B5-INSTALL, headless Blender, Blender/lib/abyss_bpy.py export_fbx)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/nova_wave.fbx. Tripo 860 tris -> 776 tris (budget per skills_vfx.md section 4). Single mesh, one plain M_Vfx slot, `Col` white + alpha fade mask, Tripo UVs kept.
- Blender bbox (Blender axes, +Z = Unity +Y, +Y = Unity +Z) min [-1.0, -0.9921, -0.0002] max [1.0, 0.9921, 0.6243].
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_nova_wave.png, 512 px greyscale from the Tripo albedo luminance, percentile levels p5->.35 / p50->.60 / p95->.80 (out p5 0.349, p50 0.592, p95 0.796).
- Unity import checked only through the running editor log (no import errors); orientation of tip-aligned meshes still to be confirmed in a battle capture.
- nova_wave height scaled x0.5 (non-uniform, 2.0 m diameter x 0.62 m) so the wave stays a ground ring when the recipe grows it to 3.8x.
