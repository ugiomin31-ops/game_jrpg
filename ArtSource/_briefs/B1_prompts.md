# Batch B1 — image prompts (Sol-approved briefs, 2026-10-11)

One ChatGPT web request per asset (GPT-6, Extra High verified before each). Each request asks for four images at once.
Save as `ArtSource/<group>/<id>/candidates/candidate_A..D.png` with `prompts.md` beside them.
The main session picks; Tripo comes after the pick.

Groups: hunters → `ArtSource/hunters/<id>/`, weapons → `ArtSource/weapons/<id>/`, town → `ArtSource/town/<id>/`.
h_seoa already has candidates; save its new ones as `v2_A..D.png`.

## Shared lead sentence (start of every prompt)
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage.

## Hunter frame (append to every hunter prompt)
Adult Korean, slim adult anime proportions about seven heads tall, stylized anime toon 3D figure for a present-day Seoul hunter RPG. Full-body straight front view, symmetric A-pose, empty hands, arms and legs clearly separated from the body, both feet visible, plain light grey background, generous margins, portrait 3:4. No text, logos, floating parts, transparent geometry, weapons or props in hand. Vary hairstyle details, colour accents and small outfit details between the four images while keeping the description.

## Weapon / object frame (append to every weapon and town prompt)
Chunky clean stylized toon 3D game asset for a present-day Seoul Korean hunter RPG, thick attached parts, single solid object, entire object visible with generous margins, plain light grey background, soft studio light, no cast shadow, square 1:1. No hands, text, lettering, logos, numbers, runes, skulls, ornate gold, medieval decoration, floating effects, transparent parts or thin dangling parts. Vary proportions and colour accents between the four images while keeping the description.

## Hunters
- **h_jiho** 「윤지호」: Former national-team archer wearing a navy track jacket with white stripes, snapback cap, left forearm guard, joggers and trainers. A compact closed quiver/sports-bag silhouette sits firmly against the back with a broad attached strap; no exposed thin arrows or bow.
- **h_yuna**: Adult nursing student wearing a white cardigan over light-blue scrubs, white sneakers, low ponytail and an attached hip first-aid pouch. A plain red armband without cross, lettering or insignia; hair and pouch straps compact and attached.
- **h_seoa** 「한서아」: Adult university-student mage wearing a beige trench coat over a white knit, pleated skirt, black tights and ankle boots. Thick round glasses with opaque lenses. A small closed spellbook attaches directly to the belt; its short chain is a solid relief, not dangling links. The coat ends above the knees and stays clear of the separated legs.
- **h_minjun**: use the brief in `hunters.md` unchanged (the held manhole shield is omitted per the empty-hands rule).

## Weapons
- **bow_hunter**: One compact modern hunting compound bow, olive-drab riser, black limbs, thick attached cam discs at both tips and visibly thick connected strings/cables. Side three-quarter view shows the complete bow; no arrows, quiver, tiny open mechanisms or detached parts.
- **staff_crystal**: One modern gate-stone wand, about 60–70 cm long, brushed-aluminium shaft and rubber grip. An opaque pale-cyan faceted focus stone enclosed by a thick attached protective collar; no transparent crystal and no thin three-prong holder.
- **mace_silver**: One short contemporary emergency-rescue mace, white aluminium shaft, rounded silver head and plain red identification bands; no cross, insignia, lettering or glow particles.

## Town (front three-quarter view, whole structure visible)
- **guild_hq**: One closed four-storey Seoul guild headquarters, pale stone, blue accents, opaque painted glass, an attached sunrise relief and a blank sign. Wide low block about 27 m wide, 11.5 m deep, 15.4 m tall; entrance on the long front side. A thick attached blue-and-cream canopy over the entrance. No visible interiors, no separate kiosk, no people or vehicles.
- **gate_portal**: One connected modern gate structure: two thick steel pylons joined by a solid base and an opaque violet rift disc between them, about 5.3 m wide, 1 m deep, at most 5.75 m high. No transparent effects, runes, stone arch, floating fragments, booths or barricades.
- **guard_booth**: One closed white-and-navy security booth, about 1.6 × 1.6 m and 2 m tall with a slightly wider flat roof, opaque painted windows and a thick attached roof light. No interior.
- **fountain**: One connected modern granite plaza fountain, about 4.7 m across and 1.95 m high, three stepped basins and a small attached sunrise relief. Water shown as opaque blue surfaces; no transparent water and no airborne streams.

## Install notes (for the Sonnet installer, not for prompts)
- Hunters: scale to the existing hero contract; stage only until the required animations exist.
- Weapons: grip-centred pivot, existing attachment axes, measure against the current model.
- Town: guild_hq body 27 × 11.5 × 15.4 m, canopy ≤ 4 m; keep entrance, steps, kiosk and actor-marker clearances (Blender/town/guild.py:71, 289–307, 510–527, 603–641). gate_portal ≤ 5.75 m high. guard_booth roof ≤ 1.9 × 1.9 m, height 2.2 m. fountain 4.7 m diameter.
