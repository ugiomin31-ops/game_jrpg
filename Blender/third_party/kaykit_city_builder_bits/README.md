# KayKit City Builder Bits 1.0 (CC0)

By Kay Lousberg — https://kaylousberg.com
License: Creative Commons Zero (CC0 1.0), see `LICENSE.txt`. Credit is appreciated, not required.

Only the glTF parts used by the town hub and the hunter-theme dungeon kits are copied here (each `.gltf` with its `.bin` buffer and the
1024 px gradient atlas `citybits_texture.png`). `Blender/environment/cc0_kit.py` (pack `kc`) samples the atlas per face corner,
bakes the colour into the `Col` attribute and the output FBX carries no texture.
Used by `Blender/town/guild.py` (Dawn Guild street): City buildings (building_A..H, two-row skyline ring; some stretched 1.5-2.5x in height), cars (incl. station wagon), bench, bush, streetlight, traffic light, trash bins. Scale 4.6 m per unit (KC in guild.py).
Used by `Blender/environment/hunter_kits/`: bench, trash_A, dumpster (street props for the subway platform and arena edge).
