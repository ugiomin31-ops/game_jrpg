# 휴머노이드 캐릭터 넣는 법 (VRoid · 에셋 스토어 · Mixamo)

애니풍 툰 방향(2026-10-06 결정)에 맞춰, 블렌더 생성 캐릭터 대신 Unity Humanoid 모델을 그대로 쓸 수 있다.
기존 블렌더 캐릭터는 그대로 동작한다. 폴더에 휴머노이드 모델을 넣은 캐릭터만 새 방식으로 바뀐다.

## 1. 캐릭터 모델
`Assets/_Game/Resources/Art/Characters/<id>/<id>` 경로에 모델을 둔다(NPC는 `NPCs/`). `<id>`는 `warrior`, `mage`, `archer`, `cleric` 등 기존 id.

- **VRM (VRoid Studio)**: UniVRM 패키지를 설치하고 `.vrm`을 넣으면 UniVRM이 프리팹을 만든다. 프리팹 이름을 `<id>`로 맞춘다.
- **FBX (에셋 스토어, Mixamo)**: `<id>.fbx`와 같은 폴더에 빈 파일 `HUMANOID`를 만든다. 그러면 Humanoid로 임포트되고 모델의 원래 머티리얼을 유지한다.

## 2. 공용 애니메이션
`Assets/_Game/Resources/Art/HumanoidAnimations/`에 FBX 한 개당 동작 하나를 넣는다. **파일 이름이 곧 클립 이름**이다.
모델에 자체 `Idle` 클립이 없으면 이 공용 동작을 쓴다.

필수: `Idle` `Run` `Walk` `Attack` `Cast` `Hit` `Die` `Victory` `Guard` `Revive` (NPC는 `Talk`도 필요)

- `Idle`, `Run`, `Walk`는 자동으로 루프한다.
- `Attack`은 40% 지점이 타격 순간, `Cast`는 60% 지점이 발동 순간이 되도록 고른다.
- Mixamo에서 받을 때는 "In Place"를 켠다.

## 3. 무기
휴머노이드에는 `weapon.R`/`weapon.L` 본이 없으므로 오른손/왼손 뼈에 붙는다. 쥐는 위치와 각도는 모델마다 조정이 필요하다.

## 알려진 차이
- VRM은 자체 MToon 셰이더를 쓰므로 피격 번쩍임과 사망 디졸브(`Abyss/Toon` 기능)가 적용되지 않는다. 모델이 들어오면 MToon 쪽에 맞춰 연결한다.
