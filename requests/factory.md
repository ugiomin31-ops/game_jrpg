# Request: factory (zone 3, abandoned factory gate) 13 dungeon pieces

상태: **취소됨 (cancelled 2026-10-16 14:10 UTC) — 만들지 마세요. Do not generate anything more; do not spend credits.** The user stopped new asset work. torch was already made and stays unused on tripo-glb-drop.

From: cloud thread "Tripo 자산 모델링" (project 게임 자산 검토 및 모델링). Hunter theme, base branch `codex/astra-enrichment-20261015`. Same flow as `requests/verdant_ruins.md`. Don't ask the user; use your own judgement on picks.


> **CLAIMED (2026-10-16 22:50 KST) by the local asset session** (same one that did verdant_ruins). Starting with torch, in the listed order. Balance 1290 → all 13 fit under the 280 stop rule. Delay so far was a Claude usage-limit window (reset 22:40 KST), not a blocker.

## Credit rule (important)

About 1290 credits were left after verdant_ruins. Each piece costs about 80. **Before starting each piece, check the balance: if it is under 280, stop there** (so it never drops below 200) and note where you stopped. Work in the order listed below (most visible first). foe_marker and decor_1 are not needed.

## Per piece

1. ChatGPT web (GPT-6, Extra High): send that piece's prompt below once, verbatim. If ChatGPT returns contact sheets, crop the best single variant as in verdant_ruins.
2. Pick one: whole asset visible, one solid connected object, chunky silhouette, nothing thin or floating free. For overlay_1/2 prefer a variant **without a wall slab behind it**.
3. Tripo Studio image-to-3D: H3.1, Best Quality, Ultra Mesh Quality ON, Texture ON, Texture Quality 2K, PBR ON.
4. Retopology: Triangle, Smart Mesh ON, target 3500.
5. Export FBX, Blender preset, texture 2K.
6. Push to branch `tripo-glb-drop` under `ArtSource/terrain/factory/<piece>/`: `candidates/candidate_*.png`, `tripo/factory_<piece>.zip` (the unchanged Tripo download), `candidates/prompts.md` (prompt, pick + reason, Tripo task id, credits before/after).
7. Tick the piece below in this file when done.

## Status

- [x] torch — tripo-glb-drop db64920, 4316 tris, 80 cr (1290→1210)
- [ ] overlay_1
- [ ] overlay_2
- [ ] decor_2
- [ ] decor_3
- [ ] decor_4
- [ ] decor_5
- [ ] decor_6
- [ ] chest
- [ ] spring
- [ ] lore_stone
- [ ] warp
- [ ] trap

## Prompts (copy verbatim)

### torch

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): An industrial dome cage lamp on a wall arm with a chain. Wall-mounted lamp only, no wall behind it: a flat back plate that meets the wall, the arm reaching about 0.5 m out, the whole lamp about 1 m tall, the glowing bulb a solid shape inside the cage. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### overlay_1

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One wall-mounted dungeon fixture for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A bundle of flanged pipes running up a wall with a hazard plate at the foot. Only the pipe bundle and the plate, no wall slab or background wall behind them (the wall already exists): a flat back, about 1.5 m wide and 3.5 m tall, depth under 30 cm. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### overlay_2

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One wall-mounted dungeon fixture for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A grey electrical box with a warning sticker (symbol only) and a rusted round gauge. Only the box, gauge and their conduits, no wall slab or background wall behind them (the wall already exists): a flat back, about 1.2 m wide and 1.6 m tall, depth under 30 cm; the sticker is a plain lightning-bolt triangle. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_2

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A hydraulic machine press: steel base, column frame, piston head, round gauge, hazard stripes. Freestanding, about 2 m tall, footprint under 1.5 m. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_3

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): Three dented oil drums, two upright and one on its side, rolled bands, oil drips. One connected group on a small oil puddle, footprint under 1.6 m. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_4

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A small yellow pallet forklift cart with two forks, a seat and small wheels. About 1.5 m long, wheels touching the ground. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_5

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): Stacked wooden crates with a loose lid next to a plastic cargo box of gate stones. One connected group, footprint under 1.5 m, the gate stones softly glowing violet. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### decor_6

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A green industrial dumpster with a closed lid and rust patches. About 1.6 m long and 1.2 m tall, lid closed. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### chest

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A steel toolbox crate with yellow corner guards and a hazard-stripe band. About 1 m wide; lid closed but clearly a separate slab on top with a hinge line at the back. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### spring

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A blue coolant water tank on a steel stand with a pipe, a tap and a glowing gauge. About 1.6 m tall, footprint under 1.4 m, the gauge glowing cyan. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### lore_stone

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A safety notice board on a steel post with a yellow hazard header. About 1.8 m tall; the board face blank or with abstract stripes only (no text, no letters). Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### warp

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A large steel gear ring set in the floor with an orange glowing core. About 3 m across and low (under 0.5 m tall), the core a solid flat glowing disc. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

### trap

```
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet. One chunky dungeon prop for a stylised present-day Seoul hunter RPG, inside a gate dungeon that has swallowed an abandoned Seoul factory (grey steel, worn concrete, safety yellow-and-black hazard stripes, rust, small soft-glowing violet gate-crystal accents): A floor plate with a hazard-stripe border and rusted spikes. A thin floor plate about 2 m square with the spikes as one cluster rising from its centre. Front three-quarter view, whole asset visible with margins, solid attached parts, a clean readable silhouette. Stylised game-ready 3D asset look, clean toon shapes, chunky readable shapes, 3D-modelling reference sheet feel, plain light-grey background, no shadow, square 1:1. No readable text, no letters, no numbers, no logos, no UI, no people, no medieval knights, crosses, crowns or gold filigree. Vary silhouette and details within the brief.
```

