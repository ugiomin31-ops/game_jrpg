# Batch B2 — image prompts (Sol-approved briefs, 2026-10-11)

One ChatGPT web request per asset (GPT-6, Extra High verified before each), four images per request.
Save as `ArtSource/<group>/<id>/candidates/candidate_A..D.png` with `prompts.md` beside them. If files already exist, use `v2_` and never overwrite.
Groups: NPCs → `ArtSource/npcs/<id>/`, town → `ArtSource/town/<id>/`.

Every prompt = lead sentence + brief + frame.

## Lead sentence
Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage.

## NPC frame
Present-day Seoul hunter RPG, slim adult Korean anime-toon proportions, stylized anime toon 3D figure, full-body straight front view, symmetric A-pose, empty hands, arms and legs clearly separated from the body, both feet visible, plain light-grey background, generous margins, portrait 3:4. Solid attached details; no text, logos, crosses, weapons, floating parts, transparent geometry or dangling accessories. Vary hairstyle details and small colour accents between the four images while keeping the description.

## Town frame
One complete connected object, chunky modern Seoul toon-3D style, front three-quarter view, plain light-grey background, generous margins, square 1:1. Thick attached construction, opaque painted windows, closed doors; no interiors, people, vehicles, transparent parts, floating effects, lettering, logos, medieval decoration or thin dangling pieces. Vary proportions and colour accents between the four images while keeping the description.

## NPCs
- **innkeeper**: A friendly adult Korean woman serving as the guild infirmary nurse, wearing a light-pink scrub top and trousers, white practical shoes and a small rounded nurse cap. Warm brown hair in a compact bun; a blank ID badge attached directly to the chest and a plain pink identification band. No clipboard or medical emblem.
- **shopkeeper**: A cheerful middle-aged Korean man running the hunter market, wearing a plain teal shirt, a khaki pocketed work vest and trousers, brown work boots and a backwards rust-orange baseball cap. Short dark-brown hair. A compact calculator-shaped case sits flush against a vest pocket, with blank solid buttons; no held calculator.
- **smith**: A sturdy adult Korean man, the guild equipment craftsman, with short dark-brown hair and a short beard. Grey work shirt, dark trousers, a dark leather apron with muted brown edging, a lensless charcoal welding cap, thick work gloves and safety boots. The apron stays clear of the legs; no wrench or dangling tools.
- **guild_clerk**: A smart young-adult Korean woman serving as receptionist, with neat compact dark hair, a navy blazer and skirt, a red tie and practical low-heeled dark shoes. A blue lanyard shown as a broad attached relief with a blank chest ID card. No tablet, loose straps or lettering.
- **elder**: A dignified older Korean man, the guild master, with swept-back silver hair and mature facial features. An open black suit jacket over a black waistcoat with restrained warm-metal edging, black trousers and polished shoes. A small abstract sunrise relief attached to the lapel, not a heraldic crest. No cane, crown or held object.

## Town
- **guild_clinic**: One closed two-storey guild infirmary, white and mint walls, a dark-teal flat roof, opaque blue painted windows and a closed entrance on the long façade. A blank mint sign panel with a simple abstract colour band, no cross. Body about 5.2 m deep, 10.2 m frontage, 6.8 m high; a thick attached teal-and-white canopy. No separate flagpole.
- **guild_market**: One closed contemporary hunter-market shop, warm-yellow walls, a red-and-cream striped attached awning, a blank illuminated sign band, an opaque painted shopfront and a closed door. Body about 5.2 m deep, 8.2 m frontage, 5.6 m high. No visible merchandise, crates, fridge or separate street furniture.
- **guild_workshop**: One closed modern equipment-repair workshop, steel-blue walls, a dark flat roof, a broad closed charcoal roller shutter and a blank amber sign band. Body about 5.2 m deep, 6.8 m frontage, 6 m high. No open garage, furnace interior, cargo or workbench.
- **notice_board**: One freestanding guild notice board: a thick cork-coloured rectangular panel in a sturdy contemporary frame, two robust attached posts and a compact top cap, about 1.98 m wide, 0.12 m deep, 2.18 m high. Several blank pastel rectangular notices sit flush against the panel; no writing, pins or loose paper.
- **banner**: One rigid contemporary guild pennant assembly: a sturdy steel pole with an attached solid blue rectangular banner slab, a restrained abstract sunrise relief and a plain warm-metal lower band, about 0.9 m wide, 0.16 m deep, 4.8 m high; banner 2.2 m tall. No fabric flutter, thin cords, text or heraldic ornament.

## Install notes (for the installer, not for prompts)
- NPC heights: innkeeper 1.58, shopkeeper 1.72, smith 1.74, guild_clerk 1.62, elder 1.70 m (NPC spawning does not normalise height). Stage NPCs until a valid Humanoid rig and Idle/Walk/Talk exist (the hunter library has no Talk).
- Town: all five pieces are currently part of the combined `town.fbx` (Blender/town/guild.py:77–79, 360–378, 540–587); keep body footprints, façade orientation, colliders and actor markers; clinic/market canopy ≤ 1.8 m; clinic/workshop roof ≤ 7.1 / 6.3 m. Stage Tripo sources for town-build integration.
