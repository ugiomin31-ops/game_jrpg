# Request: verdant_ruins (forest ruin, zone 2) 15 dungeon pieces

From: cloud thread "Tripo 자산 모델링" (project 게임 자산 검토 및 모델링). Hunter theme, base branch `codex/astra-enrichment-20261015`. Don't ask the user; use your own judgement on picks.

> **RESUME (2026-10-16 03:50 UTC):** 10 of 15 are done and received, thank you. Please continue with the remaining 5: trap, warp, foe_marker, overlay_1, overlay_2, same steps and settings as below. The cloud thread is already installing the first 10.

## Per piece

1. ChatGPT web (GPT-6, Extra High): send that piece's prompt below once, verbatim, to get 4 images.
2. Pick one: whole asset visible, one solid connected object, chunky silhouette, nothing thin or floating free.
3. Tripo Studio image-to-3D: H3.1, Best Quality, Ultra Mesh Quality ON, Texture ON, Texture Quality 2K, PBR ON.
4. Retopology: Triangle, Smart Mesh ON, target 3500.
5. Export FBX, Blender preset, texture 2K (GLB if FBX fails).
6. Push to branch `tripo-glb-drop` (create it from `codex/astra-enrichment-20261015` if missing) under `ArtSource/terrain/verdant_ruins/<piece>/`:
   - `candidates/candidate_A.png` .. `candidate_D.png`
   - `tripo/` the exported FBX (or zip/GLB) with its textures
   - `candidates/prompts.md`: prompt used, pick letter + one-line reason, Tripo task id, credits before/after
   If a file is over 100 MB, put it in `C:\Users\tmdgn\Downloads` as `verdant_ruins_<piece>.fbx` instead and note that in prompts.md.
7. Tick the piece below in this file on `local-requests` (or note it in its prompts.md) when done.

Cost about 90 credits per piece, about 1350 total (2490 left at 23:02). STOP if credits drop below 200 and note where you stopped.

## Status

- [x] decor_1 — tripo-glb-drop 333df2e, 3073 tris, 80 cr (2490→2410)
- [x] decor_2 — tripo-glb-drop b11af39, 3497 tris, 80 cr (2410→2330)
- [x] decor_3 — tripo-glb-drop 2506d44, 3470 tris, 80 cr (2330→2250)
- [x] decor_4 — tripo-glb-drop 54422db, 3127 tris, 80 cr (2250→2170)
- [x] decor_5 — tripo-glb-drop d93df6f, 3542 tris, 80 cr (2170→2090)
- [x] decor_6 — tripo-glb-drop bd285e2, 3521 tris, 80 cr (2090→2010)
- [x] chest — tripo-glb-drop 025fab0, 3717 tris, 80 cr (2010→1930)
- [x] lore_stone — tripo-glb-drop c9e4883, 3554 tris, 80 cr (1930→1850)
- [x] spring — tripo-glb-drop 9c2f206, 3212 tris, 80 cr (1850→1770)
- [x] torch — tripo-glb-drop aeba68e, 3394 tris, 80 cr (1770→1690)
- [x] trap — tripo-glb-drop a9b1847, 3581 tris, 80 cr (1690→1610)
- [x] warp — tripo-glb-drop 800deea, 3677 tris, 80 cr (1610→1530)
- [x] foe_marker — tripo-glb-drop 795fafe, 3390 tris, 80 cr (1530→1450)
- [x] overlay_1 — tripo-glb-drop a4583ed, 3753 tris, 80 cr (1450→1370)
- [ ] overlay_2

## Prompts (copy verbatim)

### decor_1

Brief: A clump of ferns, ginkgo saplings and a few small green crystals.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A clump of ferns, ginkgo saplings and a few small green crystals. Freestanding, footprint under 1.5 m, plants as chunky solid leaf clusters (no thin strands). Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_2

Brief: A broken mossy stone column with a fallen fluted drum beside it.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A broken mossy stone column with a fallen fluted drum beside it. Freestanding, column about 2 m tall, footprint under 2 m. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_3

Brief: A small shallow pool ringed with mossy stones and lily pads.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A small shallow pool ringed with mossy stones and lily pads. Low and flat, about 1.8 m across, water as a solid glossy surface. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_4

Brief: A mossy stone urn on a plinth with a sprouting plant.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A mossy stone urn on a plinth with a sprouting plant. Freestanding, about 1.3 m tall. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_5

Brief: A fallen carved stone lintel with rubble and grass.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A fallen carved stone lintel with rubble and grass. Low, about 2 m long, carvings as abstract leaf bands (no letters). Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_6

Brief: A small mossy stone wayfinder idol with a glowing green gem.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A small mossy stone wayfinder idol with a glowing green gem. Freestanding, about 1.2 m tall, a round friendly idol face, gem set into the chest. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### chest

Brief: A moss-covered stone chest with root bands.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A moss-covered stone chest with root bands. About 1 m wide; lid closed but clearly a separate slab on top with a hinge line at the back. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### lore_stone

Brief: A mossy stone stele with a glowing green rift line.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A mossy stone stele with a glowing green rift line. About 2 m tall, the rift line a solid glowing groove (abstract, no runes or letters). Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### spring

Brief: A clear spring pool with a cyan glowing ring.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A clear spring pool with a cyan glowing ring. About 2.5 m across, low stone rim, water as a solid glossy surface, the ring a solid glowing band. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### torch

Brief: A stone post brazier with a warm flame.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A stone post brazier with a warm flame. About 1.8 m tall, the flame a chunky solid stylised shape attached to the bowl. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### trap

Brief: A mossy floor slab with thorny root spikes.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A mossy floor slab with thorny root spikes. A flat floor slab about 2 m square with the root spikes as one cluster rising from its centre. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### warp

Brief: A ring of mossy standing stones around a green-violet glow.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A ring of mossy standing stones around a green-violet glow. About 3 m across, the glow a solid flat disc on the ground inside the ring. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### foe_marker

Brief: A floor ring of moss with a floating orange gate crystal.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): A floor ring of moss with a floating orange gate crystal. Ring about 2 m across; the crystal is attached to the ring by a solid glow column (nothing floating free). Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### overlay_1

Brief: Ivy and flowering vines hanging from the wall top.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One wall decal panel for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): Ivy and flowering vines hanging from the wall top. One flat decal panel to be stuck on a 4 m wide stone wall face: vines hang from the top edge down about two thirds. Flat-backed, relief no deeper than a few centimetres. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### overlay_2

Brief: Thick roots creeping down the wall face.

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One wall decal panel for a stylised present-day Seoul hunter RPG, inside an E-rank gate dungeon that is an overgrown forest ruin (mossy grey-green stone, warm earth, fresh leaf green, small soft-glowing green gate-crystal accents): Thick roots creeping down the wall face. One flat decal panel to be stuck on a 4 m wide stone wall face: thick roots creep down from the top. Flat-backed, relief no deeper than a few centimetres. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```
