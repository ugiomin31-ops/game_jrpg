# aid_kit: Tripo source (account 3, 2026-10-14)

- Picked image: ArtSource/props/aid_kit/candidates/candidate_A.png
- Why picked: open lid shows bandages and injector clearly, cyan accents match the UI, cleanest silhouette.
- Site: studio.tripo3d.ai (Tripo Studio web, user's subscription credits)
- Task id: 3373ae8e-a4dc-46fb-9a79-45e36716b080 (generate, texture and export all on this task)

## Steps and credits
1. Image to 3D, Smart Mesh P2.0, Number of Generation 1, Topology Quad, Polycount 3000, Smart Mesh trial (coin 0). Generate showed 100 with trial. Balance 210 -> 210 (trial free). Result: Quad, Faces 3420, Vertices 3196 (on-page). No texture in this output (the FBX has no texture references).
2. Texture: Generate Texture, Texture Resolution 2K, cost 10. Balance 210 -> 200. This step was added because Smart Mesh output has no texture and the spec asks for texture ON.
3. Export: FBX, Blender preset, Texture Resolution 2k, static (no skeleton / no animation). Free.

Total spent: 10 credits (Smart Mesh trial 0). Balance after: 200.

## Files
- tripo/first+aid+kit+3d+model.fbx (234464 bytes) with tripo/first+aid+kit+3d+model.fbm/first+aid+kit+3d+model_basecolor.jpg (2K). This is the textured export.
- tripo/first+aid+kit+3d+model.fbm/ (texture folder, see above)
- tripo/first aid kit 3d model.zip (download archive, kept as given)
- tripo/untextured_geometry/first aid kit 3d model.fbx (147824 bytes): the first export made before the texture step, geometry only, no texture. Kept for reference, do not import.
