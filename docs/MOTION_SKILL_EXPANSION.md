# 동작·스킬 확장과 전수 점검 (2026-10-14, `claude/motion-polish-pr9`)

## 확인 범위

- 확인한 것: 엔진 독립 로직 테스트 **199/199 통과**(.NET 8, `python3 Tools/logic_test.py`), 런타임 스크립트 103개 타입 검사
  (UnityEngine 2021.3 참조 DLL + uGUI/InputSystem 소스, URP는 스텁; 오류·경고 0, `UITouch.cs`의 `Span<>`은 참조 환경 한계로 인한 거짓 양성),
  데이터 참조(스킬→연출→VFX·SFX, 적→모델·스킬·소환, 장비·아이템·상태·환경 조각→FBX) 전수 대조, 새 동작 FBX의 재임포트 검사와 Tripo 헌터에 입힌 렌더.
- 확인하지 못한 것: **Unity 에디터·플레이 실행**(이 클라우드 세션에는 Unity 라이선스·에디터가 없음). 새 동작의 Humanoid 아바타 자동 매핑,
  전투 중 실제 타이밍·카메라와의 조합, 모바일 성능은 Unity에서 직접 확인해야 합니다.
- 하지 못한 것: ChatGPT(웹 GPT-6) 이미지 생성, Tripo 3D 모델링·DCC Bridge 연결. 이 세션에는 해당 서비스의 커넥터·브라우저·계정 접근이 없습니다.
  보관된 Tripo 원본 중 게임에 아직 들어가지 않은 것은 `crystal_cave_lord`(보스, 현재는 `crystal_horror` 색 변형으로 대체) 정적 메시이며,
  원본은 초안 릴리스 `artsource-20261014` 압축본에만 있고 리깅·클립이 없어 Tripo Auto Rig가 필요합니다.

## 1. 새 헌터 동작 12종 (Blender 키프레임 제작)

`Blender/hunters_tripo/motion_author.py`가 공용 Humanoid 라이브러리의 뼈대(`HumanoidAnimations/Cast.fbx`, Mixamo 65본, 24fps)에
`motion_takes.py`의 키 포즈를 풀어 매 프레임 키를 찍습니다(팔·다리 2본 IK, 무기 방향 지정, 손가락 쥐기). 내보낸 뒤 다시 읽어 레스트 포즈가
원본과 2e-6 m 이내로 같은지 검사합니다. 기록: `docs/verification/authored_takes_report.json`, 렌더: `docs/verification/authored_takes_h_dohyun.jpg`.

| 동작 | 용도 | 타격 시점 |
|---|---|---|
| Spell | 무술식 `Cast`(쪼그려 가리키기) 대체: 무기를 들어 모았다가 앞으로 내지르는 시전 | 56% |
| Brace | 주먹 가드 `Guard` 대체: 무기를 가로로 받치고 자세를 낮춤 | — |
| Flinch | 권투식 `Hit` 대체: 상체가 젖혀지는 피격 (0.6초) | — |
| Slash / Thrust / Smash / Spin | 가로베기·찌르기·두 손 내려찍기·회전 베기 | 38/45/45/44% |
| Channel / Rally / Kneel / Throw | 두 손 들어 올리기(회복·버프)·함성·무릎 꿇고 손 뻗기(부활)·아이템 던지기 | 55/38/45/48% |
| RelaxLoop | 마을 대기(체중 이동·호흡·두리번), 거의 정지한 차렷 `Idle` 대체 | — |

Tripo 원본(`Cast/Guard/Hit/Idle` 등)은 그대로 두고 새 이름으로 추가했습니다. 직업·영웅 전용 Tripo 동작이 있으면 그것이 우선합니다.
다시 만들기: `blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/motion_author.py [-- --only Spell]`
미리보기: `blender -b --factory-startup -P Blender/hunters_tripo/clip_sheet.py -- h_dohyun out.png <take.fbx...>`

### Blender 리그 헌터 15명

20명 중 Tripo Humanoid 모델은 5명(도현·지호·민준·서아·유나)뿐이고, 나머지 15명(보라·다나·은비·건우·하나·하늘·이슬·재현·준·미래·리나·시우·소라·태양·영수)은
Blender로 만든 22본 Generic 리그라 공용 Humanoid 동작이 적용되지 않았습니다. 같은 키 포즈를 각 헌터의 뼈대(어깨·발 위치, 팔다리 길이,
무기 소켓 방향)에 맞춰 다시 풀어 `Characters/<id>/<id>_moves.fbx`(Slash·Thrust·Smash·Spin·Channel·Throw·Rally·Kneel, 궁수는 Throw 제외)로
내보내고, `ArtLibrary`가 모델의 고유 동작에 합칩니다. 재임포트 검사 기록: `docs/verification/hero_moves_report.json`.
다시 만들기: `blender -b --factory-startup --python-exit-code 1 -P Blender/hunters_tripo/motion_author.py -- --heroes all`,
미리보기: `Blender/hunters_tripo/hero_moves_sheet.py`.

## 2. 전투 연출 다양화 (`MotionStyles`, `BattleView.Moves.cs`)

- 몬스터 접근 10종: 기본 달리기, 덮치기(높은 도약), 돌진(뒷발 긁고 지나쳤다 미끄러져 복귀), 몸통 박치기(높이 솟았다 내리꽂기+지진),
  급강하(비행형), 순간이동(유령형), 땅굴 기습(가라앉았다 대상 밑에서 솟구침), 통통 튀기(슬라임·작은 식물), 지그재그(곤충·작은 짐승), 회전 베기.
  스킬 이름(땅굴·급강하·박치기·휩쓸기·물기 등)과 몸 형태(짐승·중장갑·뱀·비행·슬라임·식물·영체·곤충)로 고르고, 기본 공격은 쓸 때마다 돌아가며 바뀝니다.
  보스는 뛰거나 튀지 않습니다. 돌아갈 때 순간이동·땅굴형은 같은 방식으로 돌아갑니다.
- 몬스터 시전: 숨결·포효는 몸을 젖혔다 내지르기, 지진·경화는 제자리 뛰어 구르기, 비행·영체는 떠오르기.
- 헌터: 스킬별 동작(내려찍기=도약 착지, 찌르기=저공 돌진, 회오리=360도 회전, 궁수 일부=뒤로 뛰며 사격, 마법사 3티어=부유),
  기본 근접 공격 순환(공격→가로베기→공격→찌르기, 성직자는 찌르지 않음), 다단히트 콤보는 타마다 다른 동작, 회복·버프=Channel, 부활=Kneel, 함성=Rally, 아이템=Throw.
- 몬스터 일반 공격(128종)의 타격 이펙트·효과음이 몸 형태별로 다릅니다: 짐승=물기·할퀴기, 인간형=베기·둔기, 중장갑=쿵·충격,
  비행=쪼기, 슬라임=산성 튀김, 식물=덩굴, 영체=어둠·영혼불, 곤충=찌르기·독. 기존에는 전부 같은 `impact` 불꽃이었습니다.
  하나의 연출(`pr_heavy_enemy`)을 같이 쓰던 몬스터 기술 6개(미늘창·닻·급강하·땅굴·조개 물기·꼬리)에 각자 연출을 주었습니다.
- 궁수의 화살비·일제사격은 뛰어올라 쏘고, 궁수가 다가가는 기술은 활 동작을 유지하며, 광역 마법은 두 손을 들어 올립니다.
  `warlock`·`ward`가 함성(`war`)으로 잘못 분류되던 문제를 고쳤습니다.
- 빗나가면 대상이 옆으로 피합니다. 모든 연출은 전투 속도·일시정지를 따르고, 동작 줄이기 설정에서는 이전 연출 그대로입니다.

## 3. 스킬 확장 (`Tools/content/skill_expansion.py`)

- 새 규칙: **처형**(`execute_below`/`execute_mult`, 체력 30% 이하 대상 추가 피해), **실드 파쇄**(`break_power`, 약점과 무관하게 맞을 때마다 실드 추가 감소),
  **자기 강화**(`self_status`, 공격이 맞으면 자신에게 상태 부여). 예측 표시(실드 감소·브레이크)도 같은 규칙을 씁니다.
- 직업별 3개씩 12개: 실드 크러시·처형의 일격·기세 연참 / 결정 파쇄·영혼 소각·마력 폭주 / 실드 브레이커·마무리 사격·질풍 연사 /
  심판의 망치·종언의 의식·수호의 빛 (Lv 5~19 사이 빈 레벨에 배치, 헌터 20명 전원 습득표 반영).
- 몬스터 기술 10개(급강하·덮치기·몸통 박치기·뿔 돌진·목덜미 물기·뼈 돌격·거미줄·짓누르기·포자 폭발·처단)와 연출 14개.
  기술이 2개뿐이던 일반 몬스터 25종에 세 번째 기술(가중치 1)을 붙였습니다. 해파리는 빙결 크라켄 보스 밸런스 때문에 제외했습니다.
- 밸런스: `CampaignBalanceTable`의 모든 구역 목표 범위 유지(보스 승률 변화 ±7%p 이내).

## 4. 점검에서 고친 것

- VFX 생성기의 연출 참조 검증에 `heal_vfx` 추가(PR8 인계 미완 항목).
- 적이 TP 스킬을 쓰면 없는 효과음 `sfx_ultimate_<적id>`를 찾다 예외가 날 수 있던 경로 차단.
- `build_world.py`가 손으로 추가된 층 이벤트(구조 이벤트 26개)를 모르고 덮어써 지우던 문제: 이제 잃을 항목을 출력하고 쓰기를 거부합니다(`--force`로만 진행).
- 공격 후 자기 강화가 걸릴 때 공격 타격 이펙트가 시전자에게 다시 터지던 문제 → 버프 이펙트로 교체.
- 회전 연출이 끝나기 전에 귀환 회전이 겹칠 수 있던 경합 제거.
