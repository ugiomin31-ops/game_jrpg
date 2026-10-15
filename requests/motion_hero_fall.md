# 요청: 헌터 쓰러짐 동작 `fall` (motion_hero_fall)

- 상태: **완료** (끝나면 이 줄을 `완료`로 바꿔 주세요)
- 요청한 곳: 프로젝트 스레드 "어색한 캐릭터 모션 점검" (PR #13)
- 크레딧: **0** (이미 리깅된 모델에 무료 프리셋만 적용. 새 AI 동작 생성은 하지 마세요)

## 배경

도현·지호·민준·서아·유나가 공용으로 쓰는 쓰러짐 동작(Die)이 Tripo 프리셋 `defeat_02`라서 넘어지지 않고 선 채로 웅크립니다. 무료 프리셋 `fall`로 바꾸려 합니다.

## 할 일

1. Tripo Studio에서 **이미 Humanoid(Mixamo)로 리깅된 헌터 모델**의 Animate 페이지를 엽니다. 아래 순서로 먼저 보이는 것 하나만 쓰면 됩니다.
   - 도현 업로드 모델 `e6b794c1-a873-400a-863f-25fc43740a65` (2026-10-15 주문 동작 때 리깅)
   - 헌터 기본 몸 `5de41bd4-321d-4ff4-9487-7d4feaca58fb`
   - 공용 동작 원본 여성 헌터 `0b4952e7-f531-4174-a74c-da8f88102b85` (https://studio.tripo3d.ai/workspace/animate/0b4952e7-f531-4174-a74c-da8f88102b85)
   - 셋 다 없으면 리깅된 다른 사람형 헌터 모델 아무거나 괜찮습니다(Mixamo 65본). 리깅부터 해야 하면 20 크레딧으로 진행해도 됩니다.
2. **Preset** 탭에서 `fall`을 적용합니다.
3. 비교용으로 같은 모델에 `defeat`도 적용합니다.
4. Export 설정:
   - 형식 **FBX**, 프리셋 **Mixamo**(없으면 Blender)
   - **Export Skeleton 켬**, 텍스처는 가장 작은 것(512)
   - **Animation stay in place 끔**
   - 애니메이션은 `fall`, `defeat` **두 개만**
5. 받은 zip은 내용을 건드리지 말고 이름만 바꿉니다.

## 저장 이름과 전달

| 파일 | 내용 |
|---|---|
| `motion_hero_fall.zip` | 4번에서 받은 zip (fall + defeat) |

- 브랜치 **`tripo-glb-drop`**의 `motion/motion_hero_fall.zip` 경로로 push 해 주세요 (브랜치가 없으면 `codex/astra-enrichment-20261015`에서 만들어 주세요).
- 가능하면 같은 파일을 `C:\Users\tmdgn\Downloads`에도 둡니다.
- 끝나면 이 파일 맨 위 상태를 `완료`로 바꾸고, 아래 "회신"을 채워 `local-requests`에 push 해 주세요.

## 회신 (채워 주세요)

- 사용한 모델(task id): 도현 업로드 모델 `e6b794c1-a873-400a-863f-25fc43740a65` (이미 리깅됨, Mixamo 65본). 크레딧 0 (2490 → 2490).
- `fall` 끝 자세: **누움(얼굴이 위)** — 뒤로 넘어짐. Blender에서 마지막 프레임 Head 본 Z축이 +Z(0.97).
- `fall` 길이(초), 끝에 바닥에서 멈추는지: **3.0초 (72프레임 @24fps)**. 약 48프레임에 엉덩이가 바닥 높이(0.49 → 0.15)에 닿고 끝까지 누운 채 끝남(마지막에 아주 약간 흔들림). 단, stay in place를 끈 상태라 루트가 뒤로 약 0.8(키의 약 85%) 이동합니다. Unity에서 루트 모션 끄기나 Hips XY 고정이 필요할 수 있어요.
- 의견: 전투 쓰러짐으로는 **`fall`** 쪽이 낫습니다. UI의 `defeat` 카드는 내부 이름이 `defeat_02`(8.46초, 선 채로 웅크림)로, 지금 쓰는 공용 Die와 같은 동작이었습니다.

**주의**: 요청대로 두 동작을 한 번에 내보낸 `motion/motion_hero_fall.zip`에는 take가 **하나**(`defeat_02_fall`, 203프레임)만 들어 있습니다. Tripo가 합쳐 버려서 내용은 fall(약 45프레임에 넘어진 뒤 203프레임까지 누워 있음)이고, defeat는 따로 없습니다. 그래서 각각 따로 내보낸 파일도 함께 올렸습니다.
- `tripo-glb-drop` 커밋 a26f197: `motion/motion_hero_fall.zip`(요청본), `motion/motion_hero_fall_fall_only.zip`(take `fall`), `motion/motion_hero_fall_defeat_only.zip`(take `defeat_02`), 설명 `motion/motion_hero_fall.md`
- 세 파일 모두 스킨 정상: 4711/4711 정점 웨이트, LeftArm 본을 돌리면 정점 752개가 움직임. 모델은 텍스처가 없어 텍스처 크기 옵션은 안 나왔습니다.
- 사본은 `C:\Users\User\Downloads`에 있습니다(`C:\Users\tmdgn`는 이 PC에 없음).

## 받은 뒤 할 일 (클라우드 스레드)

Blender로 끝 자세와 길이를 확인하고 공용 `Die`를 교체해 PR #13에 반영합니다.
