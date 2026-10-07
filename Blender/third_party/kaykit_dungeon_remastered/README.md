# KayKit Dungeon Remastered 1.0 (CC0)

By Kay Lousberg — https://kaylousberg.com · source: https://github.com/KayKit-Game-Assets/KayKit-Dungeon-Remastered-1.0
License: Creative Commons Zero (CC0 1.0), see `LICENSE.txt`. Credit is appreciated, not required.

Only the glTF binaries used by the dungeon kits are copied here (each `.glb` embeds the 1024 px gradient atlas
`dungeon_texture.png`). `Blender/environment/cc0_kit.py` samples the atlas per face corner, bakes the colour into
the `Col` attribute and recolours it per biome; the output FBX files carry no texture.
Used by `Blender/environment/dungeon_cc0.py`: crypt and ruin walls (wall, wall_gated, wall_broken, wall_doorway
incl. its door leaf), floors (floor_tile_large/small/broken/weeds, floor_dirt_large, floor_dirt_large_rocky,
floor_tile_big_grate, floor_tile_big_spikes incl. spikes), stairs_narrow, chest_gold (+ lid), torch_mounted /
torch_lit, barrier, banner_white (torn crypt banners), box_small, shelf_small_candles, sword_shield_gold.
(Ember and frost walls are procedural rock / ice, see `arch_geo.py`.)
