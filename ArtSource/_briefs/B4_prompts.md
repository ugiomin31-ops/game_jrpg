# Batch B4 — image prompts (Sol-approved briefs, 2026-10-12)

One ChatGPT web request per asset (GPT-6, Extra High verified before each), four images per request.
Save as `ArtSource/<group>/<id>/candidates/candidate_A..D.png` with `prompts.md` beside them (use `v2_` if files exist; never overwrite).
Groups: effect meshes → `ArtSource/vfx/<id>/`, monsters → `ArtSource/enemies/<id>/`.
Every prompt = lead sentence + brief + matching frame.

## Lead sentence
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet.

## Effect frame
One opaque, solid, chunky stylized effect sculpture for a modern Korean hunter RPG. Matte neutral-grey material, clean simple surface shading, no painted glow gradients, transparency, particles, motion blur, text or background effects. Single complete object with generous margins on a plain mid-grey background, square 1:1. Vary proportions and silhouette within the brief.

## Monster frame
One cute, chunky toon gate creature from a Seoul park gate. Full-body front view, upright on two separated feet, symmetric A-pose, identifiable shoulders, elbows, wrists and knees, arms clear of the torso. Small recessed non-emissive eyes; glow only in narrow violet rift cracks. Plain light-grey background, no shadow, text, crown, cape or medieval armour, square 1:1.

## Effect meshes
- **slash_crescent** (near-front three-quarter view): One thick continuous crescent blade arc with bevelled edges, a chunky middle tapering to two pointed tips, a slight twist but no separate streaks. Keep a readable arc, not a complete ring.
- **energy_arrow** (side-biased three-quarter view): One faceted energy arrow with a broad pointed arrowhead, a short sturdy shaft and three thick swept fins; no feathers, wood, bow or separate trail.
- **energy_orb** (three-quarter view): One solid round sphere with two broad raised swirling bands integrated into its surface, crossed like planet bands but not detached rings; shallow grooves separate the bands. No hollow transparent shell.
- **impact_crater** (high three-quarter view, not edge-on): One shallow solid circular crater slab with a low chunky cracked rim, a recessed centre and broad radial grooves. No floating rocks, dust or tall spikes.
- **shield_dome** (low three-quarter view showing the open underside): One open-bottom hemispherical shield shell made of connected broad hexagonal panels with a thick continuous base rim; no detached tiles, not a closed sphere.
- **light_pillar** (low three-quarter view): One upright solid hexagonal column with an integrated flared base ring and a gently tapering top, broad clean facets; no rays or hovering rings.

## Monsters
- **sprout 「풀뿌리」**: A young walking tree spirit growing from ruin cracks: a round short stump torso, two distinct thick root legs ending in broad feet, two sturdy branch arms with readable elbows and blunt hand-like ends, an attached ginkgo-leaf tuft. Warm bark, moss patches and restrained violet cracks; a friendly determined face. No thin twig fingers or extra roots bridging the limbs.
- **mandragora 「만드라고라」**: A pale radish-root creature with a broad open screaming mouth, a compact leafy tuft, two separated chunky root legs and two substantial root arms with recognisable joints. Cute startled expression, small dark socketed eyes, subtle violet cracks. No sprawling root skirt, tangled tendrils or foliage hiding the shoulders.
- **goblin 「고블린」**: A small green goblin with a cheeky grin, an oversized soft leather cap and simple modern park-scavenger clothing, holding its short thick wooden club close to one outward-facing hand, clear of the torso, elbow and the other arm; no dangling strap. Two sturdy legs, broad feet and unobstructed arm anatomy.
- **goblin_shaman 「고블린 주술사」**: A small green goblin healer with a compact attached feather headpiece and a necklace of solid attached beads, holding a short root staff beside one outward hand, clear of all joints; palms do not glow. Simple park-scavenger clothing, a sympathetic mischievous face, violet rift cracks only. No robe skirt, trailing feathers or hovering pose.

## Install gates (installer only)
- Monsters: small 3–6k tris; Tripo Triangle Smart Mesh → Humanoid/Mixamo → Tripo presets (idle, run, slash, cast_a_spell, hit_to_body_01, defeat → Idle/Run/Attack/Cast/Hit/Die, trim Attack 40% / Cast 60%, constant hips offset so feet touch z 0); keep old model height and GUIDs. No tint split needed. goblin_shaman does NOT use the flyer backend.
- Effects (ArtSource/_briefs/skills_vfx.md §mesh contract): Tripo retopo first; slash_crescent arc in XY facing +Z, swing-centre pivot, 2 m chord, ≤600 tris, U along the sweep; energy_arrow tip +Z (Blender +Y), centre-of-mass pivot, 1 m, ≤400; energy_orb centre pivot, 0.6 m, ≤500; impact_crater bottom-centre pivot, flat XZ, 2.4 m, ≤900; shield_dome base-centre pivot, +Y up, 2.4 m, ≤1000; light_pillar bottom-centre pivot, +Y up, 3 m, ≤600. Greyscale luminance texture body ~0.6, grooves ~0.35, edges ~0.8; white `Col` attribute.
