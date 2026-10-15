# Painted VFX textures (ChatGPT web)

These replace the procedural shapes of the same name in `gen_textures.py`. Each PNG here is the
GPT image reduced to the game's three cel plateaus (0 = empty, 128 = dim fringe, 210 = mid body,
255 = white-hot core) at the final texture size. `gen_textures.py` converts them to the RGBA layout the
`Abyss/VfxUnlit` shader reads (alpha plateaus + red-channel heat).

## Batch 1 — 2026-10-15

- Site: chatgpt.com (Claude desktop built-in browser), GPT-6, reasoning Extra High (4th of 5 stops).
- One request, four images returned together, all four accepted by the main session (compared against the
  procedural versions: sharper anime impact-frame shapes, cleaner silhouettes).
- Conversion: luminance thresholds < .25 / < .62 / < .90 / above → 0 / 128 / 210 / 255, resampled to
  hit_flash 256², shockwave 512², slash_arc 512×256, sunburst 512². The full-size originals stay in that
  ChatGPT conversation; the built-in browser offers no file download.

Prompt (verbatim):

> Generate 4 separate images in this one reply (4 images, not one combined sheet). They are hit-impact effect textures for a 3D anime-style JRPG battle (cel-shaded, Genshin / Honkai Star Rail / Persona 5 impact-frame feel). Rules for ALL 4: pure solid black background (#000000) edge to edge; the effect drawn ONLY in white and greys (no colour at all, the game tints it per element); flat cel-shaded look with exactly three clear brightness steps: a pure white hot core, a light grey (~80%) body, and a mid grey (~50%) outer fringe, hard clean edges between steps, no soft airbrush glow, no gradients, no noise, no particles floating loose; a single effect centred with a clear black margin of at least 6% on every side (nothing touches the edges); no text, no letters, no runes, no watermark, no frame, flat 2D front view. Image 1 (square 1:1) "hit flash": a generic melee hit impact burst, a solid round white core with 10 to 12 sharp uneven spikes of different lengths radiating out, a few spikes split into two, punchy anime impact-frame shape. Image 2 (square 1:1) "shockwave": a ring shockwave seen straight on, a thick circular band about 12% of the width, with a jagged torn inner edge and a cleaner outer edge, a few short broken arc fragments just outside the ring, the centre fully black and empty. Image 3 (wide 2:1, landscape) "slash arc": one crescent sword-slash streak arching across the top of the frame from lower left up and over to lower right (like a frown shape), thick in the middle and tapering to razor-sharp tips at both ends, white hot along the outer leading edge, light grey body, mid grey ragged smear trailing on the inner side. Image 4 (square 1:1) "critical burst": a big critical-hit burst, a white core with 16 to 20 long thick-and-thin alternating star rays, a second ring of short spikes between them, plus a few thin straight speed lines radiating out; more dramatic and larger than image 1.

| file | image | used by (recipe layers) |
|---|---|---|
| hit_flash.png | 1 | 103 |
| shockwave.png | 2 | 76 |
| slash_arc.png | 3 | 16 |
| sunburst.png | 4 (critical burst) | 20 |

## Batch 2 — 2026-10-15 (same chat, follow-up request, same model and reasoning level)

Three of four accepted. Rejected: image 4 "spark" — at its 128×32 size the needle came out thinner than the
procedural spark and would read worse as a small hit spark, so `spark` stays procedural.

Prompt (verbatim):

> Great, all 4 are approved. Now generate the next 4 separate images in one reply, exactly the same rules and style as before (pure black background, white and greys only, exactly three flat brightness steps: white hot core, ~80% light grey body, ~50% mid grey fringe, hard clean edges, no glow, no gradients, no noise, black margin of at least 6% on every side, no text, flat 2D front view). Image 1 (wide 2:1 landscape) "bite": a monster bite mark impact seen from the front, an upper row of 6 big curved triangular fangs pointing down across the top half of the frame, attached to a thick gently curved jaw band, the fangs white hot at their tips and light grey at the base, a mid grey ragged rim around the band; the bottom half of the frame stays empty black. Image 2 (square 1:1) "claw": three parallel diagonal beast claw slashes from upper left to lower right, each a long curved blade-shaped streak thick in the middle and razor-sharp at both ends, white hot centre line, light grey body, mid grey torn fringe, slightly different lengths, evenly spaced. Image 3 (square 1:1) "cross slash": two crossing crescent sword slashes forming a big X, one from upper left to lower right and one from upper right to lower left, each tapering to sharp tips, white hot cutting edges, light grey body, mid grey smear on the trailing side, a small white star flash where they cross. Image 4 (very wide 4:1 landscape) "spark": a single horizontal needle-shaped hit spark, a long thin lens / diamond shape pointed at both ends, white hot core line, light grey body, mid grey thin fringe, filling about 85% of the width.

| file | image | sizes |
|---|---|---|
| bite.png | 1 | 256×128 |
| claw.png | 2 | 256×256 (diagonal; the procedural one was vertical) |
| slash_cross.png | 3 | 512×512 |
