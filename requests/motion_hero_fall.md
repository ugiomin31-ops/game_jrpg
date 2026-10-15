# 요청: 헌터 쓰러짐 동작 `fall` (motion_hero_fall)

- 상태: **대기 중** (끝나면 이 줄을 `완료`로 바꿔 주세요)
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

- 사용한 모델(task id):
- `fall` 끝 자세: 엎드림(얼굴이 바닥) / 누움(얼굴이 위)
- `fall` 길이(초), 끝에 바닥에서 멈추는지:
- 의견: 전투 쓰러짐으로 `fall`과 `defeat` 중 어느 쪽이 나아 보이는지:

## 받은 뒤 할 일 (클라우드 스레드)

Blender로 끝 자세와 길이를 확인하고 공용 `Die`를 교체해 PR #13에 반영합니다.
