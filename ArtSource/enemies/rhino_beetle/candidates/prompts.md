# rhino_beetle (enemies, Floor-2 zone 2, rank 0) — ChatGPT web candidates, 2026-10-13

Model check before send: model menu GPT-6 aria-checked=true; reasoning slider aria-valuenow=3 max=4 (Extra High, 4th of 5).
Chat: https://chatgpt.com/c/6acd6c95-f91c-83ee-b165-dc2eb3730231
Brief source: Assets/_Game/Resources/Data/enemies.json row id rhino_beetle: display_name 장수풍뎅이; text_ko enemy_desc_rhino_beetle "단단한 껍질의 장수풍뎅이. 찌르기와 베기를 튕겨 낸다. 불에 약하다." (hard-shelled rhinoceros beetle that bounces off thrusts and slashes, weak to fire). Style rules: ArtSource/_briefs/enemies.md (rhino_beetle: Base light, pale bronze shell, O! rig risk because of 6 legs, size S/N; brief "A chunky rhinoceros beetle with a big glossy shell and one thick horn, short stubby legs").
Prompt (sent exactly as below):

Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One cute chunky toon beetle creature for a modern Seoul hunter RPG: a chunky rhinoceros beetle with a big glossy hard shell in pale bronze, one thick forward horn on its head, short stubby legs (six, clearly separated and standing on the ground), round head with small recessed non-emissive eyes. Full body visible, standing on its legs. Stylised game-ready 3D asset look, clean toon shapes, chunky readable silhouette, 3D-modelling reference sheet feel, single subject centered, full body visible with margins, 3/4 front view, plain light-grey background, soft neutral shading, no shadow, square 1:1. Matte, opaque; no glow; no text, logos, UI, symbols, crown, cape, medieval armour, skulls, runes, gold filigree or fantasy ornament. Vary horn length, shell shape and leg length within the brief.

Results (one response, 4 images): candidate_A.png .. candidate_D.png.
pick: candidate_A.png. Reason: compact glossy shell, short stubby armoured legs, six clearly separated legs standing on the ground, one thick horn; O! rig risk from six legs. Alternative: candidate_B.png

## Tripo (B6-TRIPO-2, 2026-10-13, third account, quality-first)

- Source site: studio.tripo3d.ai (Tripo Studio web, subscription credits). No API, MCP or CLI used.
- Picked image: candidate_A.png (compact glossy shell, short stubby armoured legs, six clearly separated legs standing on the ground, one thick horn). Alternative candidate_B.png was not sent.
- Generate: task e8344222-c96a-4127-b549-10c8818eddf6. H3.1 Best Quality, Geometry & Texture, Ultra Mesh on, Texture on, Texture Quality 4K, PBR on, Triangle. Cost 55.
- Retopo: Triangle + Smart Mesh, target 10000, cost 35 (verified on page before click). Result 9529 faces, within the 6k-10k normal enemy target of 10000 for this asset.
- Export: static FBX, Blender preset, 4k textures (native, no extra cost). No rig, no animation.
- Balance: 625 read before retopo, 590 after. Pre-generate balance not recorded in this context.
- Local FBX: ArtSource/enemies/rhino_beetle/tripo/tripo_convert_8e06fa37-0bc2-4685-825d-c20bd7a82685.fbx (+ basecolor, metallic, normal, roughness JPEG and rm PNG; zip retained).
- Blender check: not required for a static export. Not run.


### Installed 2026-10-13 (INSTALL-B6-2, Claude Sonnet, headless Blender, no credits)
- Assets/_Game/Resources/Art/Enemies/rhino_beetle/rhino_beetle.fbx (+ TRIPO marker, rhino_beetle_tex/rhino_beetle.png raw 4096 px, pixel-identical). Old model + meta in ArtSource/_backup_20261013_b6_2/enemies/ (GUID kept). STATIC single mesh 'Body', material rhino_beetle, no armature, no takes (same shape as the slime install). 9529 tris = raw 9529, UV 100%, uniform 1.08 (anisotropy 1.0), rigid yaw +90 deg (the raw beetle faces -X; now faces -Y = Unity +Z), centred xy, base z=0, 0.916 x 1.0566 x 0.7712 m.
- Runtime: needs code (no authored takes exist): see the INSTALL-B6-2 ledger section.
