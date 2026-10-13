# vine_coil (vfx, skill effect mesh #26) — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd696e-8878-83ee-96ca-b81022b198f5
Brief source: ArtSource/_briefs/skills_vfx.md row 26 (vine_coil: thorny vine twisting in a 2-turn open spiral, bottom centre, +Y, 1.6 tall, <=800 tris).
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One solid matte light-grey sculpted mesh of a vine coil: a thorny vine twisting in a two-turn open spiral, bottom centre, chunky stylised game geometry for a modern Seoul hunter RPG skill effect. Stylised game-ready 3D asset look, clean toon shapes, 3D-modelling reference sheet feel, single subject centered, 3/4 front view, the full object visible with margins, plain light-grey background, soft neutral shading, square 1:1. Matte, opaque, colour-free; no glow, no transparency, no particles, no motion blur, no thin floating particles, no text, runes, logos, symbols, skulls, crowns or gold filigree, no medieval or fantasy ornament. Vary thorn size, coil tightness and vine thickness within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_A.png. Reason: two-turn open spiral with chunky thorns; D's thorns are small and thin. Alternative: candidate_D.png


## Tripo (B6-TRIPO, 2026-10-13, third account)
- Source generate slot: https://studio.tripo3d.ai/workspace/generate/50454651-2fa2-45ce-8c80-c9095c2cdda2 (UUID copied from ArtSource/_tripo_ledger.md B6-TRIPO checkpoint, NOT inferred from the export filename UUID).
- Checked settings (verbatim ledger row): "G-cost, R 800 -> 754, E" - verification levels (G-full/G-model/G-cost/R/E) as defined in that ledger section; raw result <raw> faces actual (ledger row). Export file: ArtSource/vfx/vine_coil/tripo/tripo_convert_1e9d076a-fc14-44f7-a92d-be0bd639a1c2.fbx with adjacent .fbm.
- Credits: generate 45 / 2060 -> 2015; retopo 35 / 2015 -> 1980. Exports free; no duplicate paid generation or retopo.
- E level: FBX, Blender preset, 2K export textures observed. No rigs or animation takes.

### Installed 2026-10-13 (B6-LOCAL-INSTALL, headless Blender 5.2.1, Blender/lib/abyss_bpy.py export_fbx; no credits)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/vine_coil.fbx, raw -> installed tris 754 -> 754 (no reduction; already under the 800 budget) (<=1200 importer-warning contract met). One mesh, one plain M_Vfx slot, "UVMap" UV kept, "Col" BYTE_COLOR RGB white + alpha fade mask. No Tripo marker (force=False overwrite allowed).
- Normalisation: upright standing, bottom pivot, 1.6 m tall (scale 1.636); Col alpha fade-in over the bottom 12%, fade-out above 90%
- Unity-axis bbox (m): x [-0.750,0.750] y [0.000,1.600] z [-0.778,0.778] (raw scale 1.636).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_vine_coil.png, 512 px greyscale RGB from the Tripo albedo luminance (percentile remap p5 -> .35 grooves, p50 -> .60 body, p95 -> .80, clamp .30-.84; measured on the output p5 0.357 / p50 0.596 / p95 0.796).
- Visual check: raw turntable + built flat/lit renders reviewed in this session (scratchpad prev/mesh_vine_coil_sheet.png); silhouette preserved. Unity import check still pending (later task).


### Restored 2026-10-13 (B6-RESTORE, user direction: Tripo retopo geometry retained; no credits)
- Local simplification REVERTED at the user's request (user: "왜 tripo 원본을 안쓰는거야? 최적화하니까 퀄리티가 다 떨어지네;" - why not use the Tripo original, quality dropped with the optimisation). Tripo retopo geometry retained. The reduced install stays documented as history in the B6-LOCAL-INSTALL section above (reduced 754 -> 754); current installed count below is source -> restored.
- Mesh reinstalled from ArtSource/vfx/vine_coil/tripo/tripo_convert_1e9d076a-fc14-44f7-a92d-be0bd639a1c2.fbx: source -> restored tris 754 -> 754, verts 378 -> 378 (identical; ALL original triangles kept; verified on fresh factory imports of both files: counts equal, no decimate/dissolve/merge). Unity-axis bbox (m): x [-0.750,0.750] y [0.000,1.600] z [-0.778,0.778].
- Transform only (game mapping): uniform scale 1.636, bottom pivot. Original UVs preserved (UVMap; per-corner values equal the raw import as a multiset - winding-order-only differences where outward normals were recalculated; no planar/sweep UV rewrite).
- Col: auxiliary runtime BYTE_COLOR alpha mask (auxiliary data, NOT a substitute for the original; sampled on the ORIGINAL UV mapping) alpha 0.4-1.0 (mean 0.934). No topology change.
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_vine_coil.png (512 px greyscale) is the AUXILIARY runtime mask VfxLibrary loads by name from Vfx/Textures/ - derived from the original .fbm basecolor luminance at the ORIGINAL UV layout (regenerated after the restore; p5 0.357 / p50 0.596 / p95 0.796). It is not claimed to be the unchanged original; the asset's own original texture is the Tripo .fbm basecolor, untouched in ArtSource.
- Visual check: side-by-side raw vs restored renders at matching pose/light/camera (front + 3-quarter) reviewed in this session (scratchpad prev/restore_sheet_*.png): silhouettes identical, surface detail preserved. Unity import check pending (later task).


### Addendum 2026-10-13 (B6 corrections 1/2: originals at runtime paths)
- Correction 2 applied: the ORIGINAL Tripo basecolor for this asset is now also shipped at Assets/_Game/Resources/Vfx/Textures/original/vine_coil_basecolor.jpeg (byte-identical md5 to the raw .fbm file in ArtSource; native resolution and bytes preserved; JPEG container as downloaded). Raw untouched.
- Which texture drives appearance exactly: the greyscale auxiliary mask Vfx/Textures/mesh_vine_coil.png (VfxLibrary.MaterialFor loads Vfx/Textures/<name> by the effects.json layer "texture"; U-wrap Repeat / V-clamp for scroll effects; shader multiplies POSITION/Col/mask with the effect colour). The original basecolor at original/ is an additional runtime asset, not currently referenced by effects.json; no runtime/shader/importer edit was made (another owner).
- No rewrite of the original to satisfy scroll effects; if U-scroll highlights are wanted, that is an effects.json/auxiliary-mask decision for the owner, not a texture rewrite.
