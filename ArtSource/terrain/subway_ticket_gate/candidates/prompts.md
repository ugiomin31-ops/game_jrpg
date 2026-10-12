# Subway ticket gate - reference candidates (sidecar)

## Current set: single-request batch (candidate_A..D.png)

- Source: ChatGPT web, chat URL https://chatgpt.com/c/6acb5f0f-1678-83ee-ab9f-9f508cdd8012 (new empty chat)
- Model/effort: GPT-6, reasoning slider Extra High (3 of 0..4 stops, 4th of 5), checked before sending
- Tripo credits spent: none (no Tripo use before main approval)
- Images returned: 4 in one reply (no follow-up sent)

Exact prompt sent (one request):

> Generate FOUR separate standalone square 1:1 images in this one response, each in its own image frame, not a grid or collage. All four show the same kind of object: a single Seoul subway fare gate (turnstile) unit, present-day Korean hunter RPG style, chunky clean stylized toon 3D look with thick attached parts. Brushed steel cabinet, yellow safety band, compact green and violet line-colour panel, sealed card reader, waist-high solid flap barrier, subtle attached violet gate-energy seam at the base. Whole unit visible, front three-quarter view, plain light grey background, generous margins, no ground slab, no floating particles, no thin dangling parts. No letters, numbers, text, logos, brands, runes, crowns, skulls, ornate gold or medieval motifs. Four distinct designs, not variations of one: Image 1 compact rounded steel unit with yellow corners and green panel; Image 2 charcoal unit with steel cap, warm yellow band and cyan reader; Image 3 ivory and teal short wide unit with violet sealed reader; Image 4 blue-grey brushed steel unit with rounded flap and muted violet corner band.

Mapping and review (each image checked by viewing the file):

| File | Reply image | Content | Notes |
|---|---|---|---|
| candidate_A.png | 1 | Brushed steel, yellow corner caps, green side panel, green flap, violet base seam | Single unit, plain grey background, no text. Best fit. Flap reads thick. |
| candidate_B.png | 2 | Charcoal body, steel cap, yellow band, cyan reader | Shows a two-post gate pair, not one unit. Brief said one object. Runner-up for the charcoal direction. |
| candidate_C.png | 3 | Ivory and teal, violet top panel, green/violet reader | Also a two-post gate pair. Reader is green/violet, not violet only. |
| candidate_D.png | 4 | Blue-grey steel, violet corner band, rounded navy flap | Single unit, clean. Runner-up for the blue-grey direction. |

Picked: candidate_A.png. Reason: single subject, clean silhouette, matches the requested steel/yellow/green direction, thick flap, plain background, no text. Sent to Tripo: no. Waiting for main approval.

## Earlier set: one prompt per candidate (kept for reference)

Folder: candidates/single_prompt_set/ (candidate_A..D.png). Chat URL https://chatgpt.com/c/6acb5d2f-46f0-83ee-9692-816a253ba733. Model GPT-6 + Extra High, same checks. Prompts were one per image (A steel/yellow/green; B charcoal/cap/cyan; C ivory/teal/violet; D blue-grey/violet band). Not used for the current pick.

## Tripo Studio run 2026-10-11 (candidate_A, main-approved pick)

- Input image: ArtSource/terrain/subway_ticket_gate/candidates/candidate_A.png (ChatGPT web, GPT-6 Extra High, see above). Image-to-3D only, no text prompt.
- Site: https://studio.tripo3d.ai (web, user's Chrome subscription credits; no API).
- Generate task id: eed82e7d-1e80-43cb-8b9a-6ce7f1806d47
  - URL: https://studio.tripo3d.ai/workspace/generate/eed82e7d-1e80-43cb-8b9a-6ce7f1806d47
  - Settings: Geometry & Texture default, AI model H3.1 - Best Quality, Sharing Only. Shown cost 55 (checked before click). Balance 2655 -> 2600.
  - Free server retry: none used. One paid generation only.
  - Tripo auto-name for the asset: "futuristic access panel 3d model".
- Retopology: same task id.
  - URL: https://studio.tripo3d.ai/workspace/retopology/eed82e7d-1e80-43cb-8b9a-6ce7f1806d47
  - Before settings change the button read 40 at Quad / 10000 polygons (not clicked). After Triangle, Smart Mesh P1.0 on, target 4500: cost 35 (expected). Balance 2600 -> 2565.
  - Result: Triangle faces 4126 / 4126, vertices 5871 / 5871 (inside the 3000-6000 target). Raw image-to-3D mesh was about 1.90M faces.
- Export: FBX, Blender preset, texture 1k, no rig (static mesh). Downloaded as futuristic+access+panel+3d+model.zip.
  - Moved to: ArtSource/terrain/subway_ticket_gate/tripo/futuristic_access_panel_export.zip
  - Extracted (python -I, path-traversal check passed, 6 entries) to: ArtSource/terrain/subway_ticket_gate/tripo/extract_retopo_1k/
    - tripo/extract_retopo_1k/tripo_convert_00a0bfc3-4bfa-4791-b678-0cb0d3695fcd.fbx (147852 bytes)
    - tripo/extract_retopo_1k/tripo_convert_00a0bfc3-4bfa-4791-b678-0cb0d3695fcd.fbm/ (basecolor, normal, metallic, roughness JPEG; rm PNG)
- Tripo Studio tab closed right after download.
- Not verified: rig and skin weights (no rig exported; nothing imported into Assets; Blender check not run).

## Installed 2026-10-11
Source: Tripo candidate A (ArtSource/terrain/subway_ticket_gate/tripo/extract_retopo_1k/tripo_convert_00a0bfc3-4bfa-4791-b678-0cb0d3695fcd.fbx, 4126 tris). Applied to Assets/_Game/Resources/Art/Environment/subway/decor_1.fbx. No new Tripo credits were spent in this install step.

Cleanup in Blender (scratch scenes SubwayGateOld_20261011, SubwayGateTripo_20261011, SubwayGateExport_20261011): transforms applied; long horizontal axis was Y, so the mesh was rotated 90 degrees about Z to match the old X-long orientation; uniform scale 1.4149 to match old height.

Final dimensions 1.385 x 0.930 x 1.060 m vs old 1.740 x 0.814 x 1.060 m (X -20.4%, Y +14.2%, Z 0%). X and Y are outside the +-10% target; the model was not stretched non-uniformly, so the footprint proportions differ from the old prop. Final tris 4126 (re-import verified). Pivot: base centre (min Z 0, XY bounds centre 0).

Original GUID bce70ef33d24ef848a1fb06922678149 preserved; decor_1.fbx.meta untouched (sha256 matches backup).
Backup: ArtSource/terrain/subway_ticket_gate/backup_20261011/ (decor_1.fbx, decor_1.fbx.meta).
Texture: Assets/_Game/Resources/Art/Environment/subway/decor_1_tex/M_SubwayGate_Tripo.png (1024x1024, base colour only). Normal, roughness and metallic image nodes removed, so the normal-map detail is not carried into the export.
Marker: Assets/_Game/Resources/Art/Environment/subway/decor_1.tripo.
Collision: none; the old model had no Col_* objects.
Object name in Blender is decor_1.003 because the name decor_1 is taken by an object in another scratch scene; the FBX export uses that name.
No Unity play or QA run, no commit.

## Correction 2026-10-12 (decor-orientation fix, S13)
Bug: the 2026-10-11 install exported with a plain bpy.ops.export_scene.fbx(axis_forward='-Z', axis_up='Y', path_mode='AUTO'). That wrote Z-up vertices plus Lcl Rotation (-90,0,0), Lcl Scaling 100 and UnitScaleFactor 1.0, so the gate imported lying on its side in Unity. Neighbours (decor_2) are baked Y-up vertices, no Lcl rotation/scale, UnitScaleFactor 100.
Fix: same cleaned mesh (re-imported from the broken FBX, 4126 tris, 1.385 x 0.930 x 1.060 m, Z up, base at 0, one material M_SubwayGate_Tripo with base colour decor_1_tex/M_SubwayGate_Tripo.png) re-exported with Blender/lib/abyss_bpy.export_fbx (FBX_SCALE_ALL, bake_space_transform, axis -Z/Y, apply_unit_scale), only difference path_mode="RELATIVE" so the texture reference stays decor_1_tex\M_SubwayGate_Tripo.png. Object name decor_1.003 kept. decor_1.fbx.meta (GUID), .tripo marker and _tex PNG untouched. Re-import check: object rot 90 X like decor_2, world Z 0..1.06, 4126 tris. Not verified in Unity (no Unity run). No Tripo credits spent, no commit.
