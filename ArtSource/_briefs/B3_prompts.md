# Batch B3 — image prompts (Sol-approved briefs, 2026-10-12)

One ChatGPT web request per asset (GPT-6, Extra High verified before each), four images per request.
Save as `ArtSource/<group>/<id>/candidates/candidate_A..D.png` with `prompts.md` beside them (use `v2_` if files exist; never overwrite).
Groups: enemies → `ArtSource/enemies/<id>/`, weapons → `ArtSource/weapons/<id>/`, props → `ArtSource/props/<id>/`.

Every prompt = lead sentence + brief + matching frame.

## Lead sentence
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage.

## Creature frame
One complete creature per image, chunky cute modern Seoul hunter-game toon 3D style, small socketed non-emissive eyes, glow only inside small blue/violet rift cracks, plain light-grey background, generous margins, square 1:1. No text, logos, crowns, capes, medieval ornament, transparent geometry, floating effects or thin dangling parts. Vary proportions and colour accents slightly between the four images while keeping the description.

## Weapon / object frame
Chunky clean stylized toon 3D game asset for a present-day Seoul Korean hunter RPG, thick attached parts, single solid object, entire object visible with generous margins, plain light grey background, soft studio light, no cast shadow, square 1:1. No hands, text, lettering, logos, numbers, runes, skulls, ornate gold, medieval decoration, floating effects, transparent parts or thin dangling parts. Vary proportions and colour accents between the four images while keeping the description.

## Enemies
- **sewer_rat**: One plump grey-brown subway burrowing rat wearing a thick attached yellow safety helmet and a simple painted high-visibility belly band. Large front incisors, compact ears and a thick tail attached close to the body. It stands upright on two separated feet, two distinct paw arms spread diagonally downward, palms empty, front view. Keep a rat muzzle, not a human face.
- **horned_rabbit**: One round cream-white horned rabbit standing upright on two separated large feet, short distinct forelimbs spread diagonally downward, long thick ears separated from the head. One sturdy opaque spiral forehead horn with a small violet rift crack; the whole horn does not glow. Compact attached tail, empty paws, front view. No sitting pose.
- **bat**: One fuzzy pale grey-violet cave bat, compact body, small socketed eyes, a tiny fang and two clearly separated feet. Broad opaque leathery wings spread symmetrically, continuous thick membranes and readable shoulder and elbow joints; no finger filaments or transparent skin. Neutral wing edges and subtle violet rift cracks. Front view, no accessories.
- **killer_bee**: One chunky giant wasp, warm-yellow body with charcoal abdominal stripes, small socketed eyes and one short thick opaque stinger. Four compact, individually separated legs and two broad solid opaque wings spread symmetrically; short thick antennae; no transparent wings or needle-thin appendages. A subtle violet rift crack along the abdomen. No helmet or humanoid costume.
- **elite_bat**: One larger red-and-charcoal nocturnal bat, broad thick opaque wings spread symmetrically, separated feet and sturdy claws attached to the wing hands. Small fierce socketed eyes and restrained violet rift cracks. One tiny blank poster-coloured patch lies flush on a wing; no ragged dangling paper, crown or cape.

## Weapons
- **sword_knight**: One short contemporary steel hunting dagger, clip-point blade, black polymer grip and a small thick finger guard. Clearly a dagger, not a longsword; all parts attached, no sheath. Whole weapon upright, grip downward, front three-quarter view.
- **bow_composite**: One modern compound bow with carbon-black and steel-grey laminated limbs, a sturdy machined riser, thick attached cam discs, visibly thick connected strings and cables and a short attached stabilizer. Side three-quarter view; no arrows, quiver or tiny open mechanisms.
- **staff_sage**: One tactical casting wand, about 60–70 cm long, matte-black polymer shaft, a broad shallow rail-like grip relief and an opaque blue focus stone enclosed by a thick protective collar. No thin cage bars or transparent crystal.
- **mace_blessed**: One contemporary rescue mace, short white shaft and a rounded pale-metal head with thick blunt flanges. A sealed muted-green head panel suggests healing equipment; no religious symbols, ornate gold, particles or floating glow.

## Prop
- **street_lamp**: One contemporary Seoul street lamp, sturdy upright steel pole, a compact curved attached arm and a thick sealed lamp head with an opaque warm-light underside, about 3.4 m tall, full object visible; no wires, separate pavement slab or transparent lens.

## Install notes (installer only)
- Rigs: sewer_rat and horned_rabbit Humanoid/Mixamo (3–6k tris; verify mapping and weights). bat and killer_bee: Tripo "Other", ONE attempt, 3–6k. elite_bat: "Other", one attempt, 10–20k. For Other rigs first establish a real Tripo animation/export route; if unavailable or weights fail, stage the model and keep the current runtime art. No Blender-authored animation.
- Enemy clips needed: Idle, Run, Attack, Hit, Die, Cast (Victory not needed). Measure each against the current model before replacing.
- Variants: cream rabbit supports snow_rabbit; neutral bat supports tunnel_bat; elite_bat colours baked (own-model tint ignored). frost_bee, ember_bee, syringe_bee need their own models later (syringe_bee with a syringe stinger).
- Weapons keep grip pivot and export axes; measure against the current held dimensions.
- street_lamp is embedded in combined town art; dungeon reuse keeps a LightAnchor under the head near 3.1 m (not baked into visible geometry).
