# ABYSS — original store illustration sources

These materials are **promotional illustrations, not gameplay screenshots**. Actual Unity captures are managed separately in `Store/screenshots/`; this generator never writes there.

## Requested working exports

| File | Pixels |
| --- | --- |
| `capsules/abyss-main-1232x706.png` | 1232 × 706 |
| `capsules/abyss-header-920x430.png` | 920 × 430 |
| `capsules/abyss-small-462x174.png` | 462 × 174 |
| `capsules/abyss-vertical-748x896.png` | 748 × 896 |
| `capsules/abyss-library-600x900.png` | 600 × 900 |
| `key-art/abyss-key-art-3840x2160.png` | 3840 × 2160 |

The dimension names are working deliverable names, **not a claim of Steam or other platform acceptance**. No platform compliance review is represented by this package. Artwork contains only the ABYSS title and decorative illustration, with no feature claims, badges or fictional gameplay labels.

## Reproduce

From the project root, with Python + Pillow and the installed Blender executable:

```powershell
python Tools/store/generate.py
```

Use `--blender "C:/path/to/blender.exe"` for another installation. The default is the locally provided Blender. Production runs locally: no network service, model generation, paid tool or purchase is used.

To change layouts/title treatments without rerendering the retained 3D plates:

```powershell
python Tools/store/generate.py --compose-only
```

To regenerate only the four hero plates while keeping the existing native antagonist/environment scenes:

```powershell
& "C:/Users/User/Tools/Blender/blender.exe" --background --factory-startup --python Tools/store/render_art.py -- --heroes-only
python Tools/store/generate.py --compose-only
```

For one hero, replace `--heroes-only` with `--hero=warrior`, `--hero=mage`, `--hero=archer` or `--hero=cleric`. Multiple `--hero=...` arguments are supported. Run the compositor afterward to refresh all six exports and native layer stacks.

`Tools/store/render_art.py` imports the existing production FBX geometry, preserves its `Col` vertex colors, poses the original rigs for illustration, attaches the original weapon meshes to their authored sockets, and renders Cycles stills. It writes only inside this Store package; it does not regenerate or alter Unity assets. The saved Blender file retains separate editable hero, antagonist and world scenes with lighting and cameras.

`Tools/store/generate.py` composes those actual rendered plates with original vector lettering, a dark-teal editorial ground, dawn-gold detail and deterministic decorative rings/motes. The gold palette derives from the existing `UITheme.cs` gold/bright-gold tokens; its left-aligned title language also references the existing `GameTitleScreen.cs`. Portrait layouts are separately art-directed rather than mechanically cropping the wide artwork. The small capsule concentrates on two heroes to preserve thumbnail clarity.

## Native and intermediate sources

- `source/abyss-key-art.blend` — original production meshes/rigs, illustration poses, equipped weapons, cameras and lights in six named hero, antagonist and crypt scenes.
- `source/abyss-title.svg` — original editable ABYSS vector letterforms, not a stock logo.
- `source/*.ora` — each final composition as an editable OpenRaster layer stack, with merged image and thumbnail embedded. Layer names identify the original characters, antagonist, environment, editorial treatment and title.
- `source/{warrior,mage,archer,cleric,abyss-antagonist,crypt-world}.png` — high-resolution 3D render plates retained for recomposition.
- `source/asset-sources.json` and `source-manifest.json` — exact imported project asset paths, generators, export dimensions and native-source references.
- `artwork-proof-sheet.png` — a visual contact sheet of the six illustrations, not a gameplay screenshot.

## Original asset references

The heroes are `Characters/{warrior,mage,archer,cleric}/{id}.fbx`; the giant background adversary is the authored abyss sorcerer `Enemies/boss/boss.fbx`. Hero equipment is `Weapons/{sword_bronze,staff_crystal,bow_hunter,mace_silver}.fbx`. The environment is the authored `Environment/haunted_crypt/{arena,boss_gate}.fbx`. All are under `Assets/_Game/Resources/Art/`.

Their retained original production generators are `Blender/heroes/generate.py` + `Blender/lib_humanoid/`, `Blender/bosses/boss.py`, `Blender/weapons/generate_all.py`, `Blender/environment/haunted_crypt/kit.py` and `Blender/environment/_arenas_a.py`. The existing project Blender files remain separate and unmodified.

The antagonist's enlarged editorial scale and hero poses are illustrative composition choices, not an assertion about a captured encounter or relative in-game scale. Source provenance is recorded; **commercial clearance, third-party IP clearance, storefront approval, Windows build success, performance and complete playthrough are not established by this artwork**.
