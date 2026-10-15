# meteor_rock (vfx, skill effect mesh #28, optional) — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd6a7d-87b8-83ee-8e9a-ed59e67e8e63
Brief source: ArtSource/_briefs/skills_vfx.md row 28 (meteor_rock, optional: round rock with deep glowing cracks, cracks as grooves, centre, 1.0 Ø, <=600 tris).
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One solid matte light-grey sculpted mesh of a meteor rock: a round rock with deep grooves cut into its surface where cracks would glow, centre, chunky stylised game geometry for a modern Seoul hunter RPG skill effect. Stylised game-ready 3D asset look, clean toon shapes, 3D-modelling reference sheet feel, single subject centered, 3/4 front view, the full object visible with margins, plain light-grey background, soft neutral shading, square 1:1. Matte, opaque, colour-free; no glow, no transparency, no particles, no motion blur, no thin floating particles, no text, runes, logos, symbols, skulls, crowns or gold filigree, no medieval or fantasy ornament. Vary rock size, crack depth and crack pattern within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_B.png. Reason: round rock with grooves that read as glowing cracks; A is too fragmented for 600 tris, C and D are egg-shaped. Alternative: candidate_A.png


## Tripo (B6-TRIPO, 2026-10-13, third account)
- Source generate slot: https://studio.tripo3d.ai/workspace/generate/7ac08765-cc4d-4318-b507-599b9f8bcf65 (UUID copied from ArtSource/_tripo_ledger.md B6-TRIPO checkpoint, NOT inferred from the export filename UUID).
- Checked settings (verbatim ledger row): "G-cost, R 700 -> 684, E" - verification levels (G-full/G-model/G-cost/R/E) as defined in that ledger section; raw result <raw> faces actual (ledger row). Export file: ArtSource/vfx/meteor_rock/tripo/tripo_convert_8478a6a7-a7d5-4e92-9b09-d7109656bfee.fbx with adjacent .fbm.
- Credits: generate 45 / 1900 -> 1855; retopo 35 / 1855 -> 1820. Exports free; no duplicate paid generation or retopo.
- E level: FBX, Blender preset, 2K export textures observed. No rigs or animation takes.

### Installed 2026-10-13 (B6-LOCAL-INSTALL, headless Blender 5.2.1, Blender/lib/abyss_bpy.py export_fbx; no credits)
- Mesh: Assets/_Game/Resources/Vfx/Meshes/meteor_rock.fbx, raw -> installed tris 684 -> 582 (collapse decimate to the 600 budget) (<=1200 importer-warning contract met). One mesh, one plain M_Vfx slot, "UVMap" UV kept, "Col" BYTE_COLOR RGB white + alpha fade mask. No Tripo marker (force=False overwrite allowed).
- Normalisation: tumbling rock blob, centre pivot (origin at bbox centre), longest dimension 1.0 m (scale 1.052); solid Col alpha 1.0.
- Unity-axis bbox (m): x [-0.500,0.502] y [-0.479,0.478] z [-0.496,0.496] (raw scale 1.0517).
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_meteor_rock.png, 256 px greyscale RGB from the Tripo albedo luminance (percentile remap p5 -> .35 grooves, p50 -> .60 body, p95 -> .80, clamp .30-.84; measured on the output p5 0.357 / p50 0.592 / p95 0.792).
- Visual check: raw turntable + built flat/lit renders reviewed in this session (scratchpad prev/mesh_meteor_rock_sheet.png); silhouette preserved. Unity import check still pending (later task).


### Restored 2026-10-13 (B6-RESTORE, user direction: Tripo retopo geometry retained; no credits)
- Local simplification REVERTED at the user's request (user: "왜 tripo 원본을 안쓰는거야? 최적화하니까 퀄리티가 다 떨어지네;" - why not use the Tripo original, quality dropped with the optimisation). Tripo retopo geometry retained. The reduced install stays documented as history in the B6-LOCAL-INSTALL section above (reduced 684 -> 582); current installed count below is source -> restored.
- Mesh reinstalled from ArtSource/vfx/meteor_rock/tripo/tripo_convert_8478a6a7-a7d5-4e92-9b09-d7109656bfee.fbx: source -> restored tris 684 -> 684, verts 342 -> 342 (identical; ALL original triangles kept; verified on fresh factory imports of both files: counts equal, no decimate/dissolve/merge). Unity-axis bbox (m): x [-0.500,0.500] y [-0.478,0.478] z [-0.496,0.496].
- Transform only (game mapping): uniform scale 1.0517, bbox centre pivot. Original UVs preserved (UVMap; per-corner values equal the raw import as a multiset - winding-order-only differences where outward normals were recalculated; no planar/sweep UV rewrite).
- Col: auxiliary runtime BYTE_COLOR alpha mask (auxiliary data, NOT a substitute for the original; sampled on the ORIGINAL UV mapping) alpha 1.0-1.0 (mean 1.0). No topology change.
- Texture: Assets/_Game/Resources/Vfx/Textures/mesh_meteor_rock.png (256 px greyscale) is the AUXILIARY runtime mask VfxLibrary loads by name from Vfx/Textures/ - derived from the original .fbm basecolor luminance at the ORIGINAL UV layout (regenerated after the restore; p5 0.357 / p50 0.596 / p95 0.796). It is not claimed to be the unchanged original; the asset's own original texture is the Tripo .fbm basecolor, untouched in ArtSource.
- Visual check: side-by-side raw vs restored renders at matching pose/light/camera (front + 3-quarter) reviewed in this session (scratchpad prev/restore_sheet_*.png): silhouettes identical, surface detail preserved. Unity import check pending (later task).


### Addendum 2026-10-13 (B6 corrections 1/2: originals at runtime paths)
- Correction 2 applied: the ORIGINAL Tripo basecolor for this asset is now also shipped at Assets/_Game/Resources/Vfx/Textures/original/meteor_rock_basecolor.jpeg (byte-identical md5 to the raw .fbm file in ArtSource; native resolution and bytes preserved; JPEG container as downloaded). Raw untouched.
- Which texture drives appearance exactly: the greyscale auxiliary mask Vfx/Textures/mesh_meteor_rock.png (VfxLibrary.MaterialFor loads Vfx/Textures/<name> by the effects.json layer "texture"; U-wrap Repeat / V-clamp for scroll effects; shader multiplies POSITION/Col/mask with the effect colour). The original basecolor at original/ is an additional runtime asset, not currently referenced by effects.json; no runtime/shader/importer edit was made (another owner).
- No rewrite of the original to satisfy scroll effects; if U-scroll highlights are wanted, that is an effects.json/auxiliary-mask decision for the owner, not a texture rewrite.
