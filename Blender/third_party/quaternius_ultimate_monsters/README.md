# Quaternius — Ultimate Monsters (CC0)

Rigged and animated low-poly monsters by **Quaternius** (https://quaternius.com, pack "Ultimate Monsters",
https://quaternius.com/packs/ultimatemonsters.html). License: **CC0 1.0 Universal** (public domain dedication),
see `License.txt` copied from the pack. Attribution is not required; this note records the source.

Only the glTF files that `Blender/enemies_cc0/specs.py` uses are kept here (each is self-contained: mesh,
skin, clips and the 32 px / 1024 px palette atlas are embedded). The copies came from the pack's `glTF/` folders
as redistributed in the public GitHub repo `320trankt/warcell` (`assets/3d/Ultimate Monsters/<Blob|Big|Flying>/glTF/`),
exported by Quaternius with Blender glTF I/O 1.7.33. For the full pack (50 monsters, also FBX/OBJ/.blend) download it
from the URL above.

| file | used for |
|---|---|
| `Blob/GreenBlob.gltf` | slime |
| `Blob/GreenSpikyBlob.gltf` | magma_slime |
| `Blob/Mushnub.gltf`, `Blob/Mushnub_Evolved.gltf` | mushroom, elite_mushroom |
| `Blob/Alien.gltf` | sprout |
| `Big/Birb.gltf` | penguin_mage |
| `Flying/Goleling.gltf`, `Flying/Goleling_Evolved.gltf` | bat, grave_bat, elite_bat |
| `Flying/Dragon.gltf`, `Flying/Dragon_Evolved.gltf` | fire_drake, elite_fire_drake |
| `Flying/Pigeon.gltf` | phoenix |
| `Flying/Ghost.gltf` | wisp candidate only (`specs.CANDIDATES`, not built by default) |

Only the source of a shipped enemy is kept here (`Blob/GreenSpikyBlob.gltf` → magma_slime). The other matches in
`enemies_cc0/specs.py` CANDIDATES need the full pack: set `ABYSS_CC0_DIR` to a folder holding
`quaternius_ultimate_monsters/<Category>/<Name>.gltf`.
