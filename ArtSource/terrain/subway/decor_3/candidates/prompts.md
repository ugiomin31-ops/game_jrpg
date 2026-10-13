# terrain/subway · decor_3 — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd6dc4-a264-83ee-8b61-b9f1ddaa3de4
Brief source: ArtSource/_briefs/environment.md, subway table, decor_3 = "A round station waste bin with a recycling split lid and a tied trash bag slumped beside it." Prop frame: README.md §Prompt frame (prop). Subway palette: cream tiles, green line stripe, steel (no signage text).
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky toon environment prop for a stylised game set in a modern Seoul subway station: a round station waste bin with a recycling split lid in grey and a tied trash bag slumped beside it. Single object group centered, three-quarter view from slightly above, the whole object visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no logos, no UI, no signs with letters, no medieval or fantasy ornament, no skulls, no runes, no crowns, no gold filigree. Vary bin height, lid shape and bag size within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_A.png. Reason: round bin with a grey and white split lid with triangular openings and a tied bag slumped beside it; dense perforations are texture-level detail. Alternative: candidate_C.png

## Tripo (B6-TRIPO-2, 2026-10-13, third account, quality-first)
- Source task: https://studio.tripo3d.ai/workspace/retopology/3928c99b-689f-45f3-b83a-8158864e95b7 (generation from the earlier B6 run, not regenerated)
- Retopo: Triangle + Smart Mesh on, polygon count 6000, cost 35, balance 1695 -> 1660. Actual faces 6175 (on-page 6175/6175).
- Export: FBX, Blender preset, texture 2k (4k not selected), static, no rig. Settled 2026-10-13 13:18.
- Local files: ArtSource/terrain/subway/decor_3/tripo/tripo_convert_7cdf00d9-609c-4ca1-8f01-def3c5f42aa5.fbx (+ .fbm with basecolor, metallic, normal, roughness and rm maps). Source zip kept alongside as metal+trash+can+3d+model.zip.


### Installed 2026-10-13 (INSTALL-B6-2, Claude Sonnet, headless Blender, no credits)
- Assets/_Game/Resources/Art/Environment/subway/decor_3.fbx replaced in place (GUID kept; old file+meta in ArtSource/_backup_20261013_b6_2/subway/). Raw Tripo geometry only: 6175 tris = raw 6175, UV multiset 100%, single uniform scale (anisotropy 1.0), rigid rotation/pivot only, one mesh 'decor_3' (no children needed: the code looks up no anchors for this piece), material M_SubwayBin_Tripo.
- Placement: uniform 1.40; pivot = bin cylinder centre (raw xy 0,0.14) so the bin back stays 0.49 m from the origin (decor stands 1.45 m from the cell centre, wall face 2.0), base z=0; front (bag side) -Y; 0.98 x 1.37 x 0.90 m.
- Texture: raw 2048 basecolor JPEG -> decor_3_tex/M_SubwayBin_Tripo.png pixel-identical; decor_3.tripo marker written; Unity creates _mat on import.
