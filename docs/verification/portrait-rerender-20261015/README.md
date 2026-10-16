# 초상화 다시 렌더 (2026-10-15)

각 칸은 왼쪽이 이전 초상화, 오른쪽이 새 초상화입니다. 렌더는 `Blender/ui/render_icons.py`로 했고, Blender 5.2.1(bpy)을 썼습니다.

- `people.png`: Tripo로 바뀐 헌터 5명과 NPC 5명입니다. 이전 초상화는 Tripo 이전의 VRoid 모델이었습니다.
- `enemies.png`: 바뀐 적 초상화 39장입니다. 마지막 칸 crystal_cave_lord는 이번에 처음 생긴 초상화입니다.
  - Tripo 텍스처만 있는 모델(slime, bat, killer_bee 등)은 예전 스크립트가 렌더하지 못했습니다.
  - mushroom·pixie·rhino_beetle 같은 모델의 이전 초상화는 실제 텍스처 색과 달랐습니다.
  - 팔레트 변형은 이제 기본 모델 텍스처에 자기 `tint`를 곱해 렌더하고, 게임도 변형 자기 초상화를 먼저 씁니다(`UIArtwork.Enemy`).

나머지 118장은 다시 렌더해도 이전과 거의 같아서(픽셀 평균 차이 0.5 미만) 파일을 바꾸지 않았습니다.
