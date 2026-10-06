# Blender 에셋 파이프라인 — 심연의 미궁

모든 3D 에셋은 이 폴더의 Python 생성기로 만들어진다. 손으로 편집한 `.blend`는 `blend/`에 저장되지만,
**원본은 생성기 스크립트**다. 수정은 스크립트에서 하고 다시 실행한다.

```
blender -b --factory-startup -P Blender/<group>/<script>.py
```
(`C:\Users\User\Tools\Blender\blender.exe` 사용. `blender.cmd` 래퍼는 깨져 있으므로 쓰지 않는다.)

## 폴더

| 경로 | 내용 |
|---|---|
| `lib/abyss_bpy.py` | 공용 헬퍼: 프리미티브, 색, 리그, 애니메이션, FBX 내보내기, 미리보기 렌더 |
| `heroes/`, `npcs/`, `weapons/`, `enemies_a/`, `enemies_b/`, `bosses/`, `environment/`, `town/`, `props/`, `icons/` | 그룹별 생성기 |
| `blend/` | 생성 결과 `.blend` (편집·검수용) |
| `preview/` | Workbench 미리보기 PNG (검수용, 게임에 포함되지 않음) |
| `ui/render_icons.py` | 실제 FBX를 촬영해 `Resources/Icons/`에 투명 512px 초상화·아이콘 160개와 Sprite 메타데이터 생성 |

출력 FBX는 `Assets/_Game/Resources/Art/<Category>/...` 에 바로 쓴다. Unity가 자동 임포트한다.

## 계약 (Unity 쪽 `AbyssArtImporter.cs`가 의존)

1. **단위·방향**: 1 unit = 1 m. 캐릭터는 z=0 바닥에 서고 **-Y를 바라본다**(Blender 정면도). Unity에서는 +Z가 정면이 된다.
   좌우 규약은 Blender 표준: 캐릭터의 왼쪽(`.L`)이 +X, 오른쪽(`.R`)이 -X. (Unity 임포트로 검증됨: 미러링 없음.)
2. **색**: 텍스처 없음. 색은 `Col` 컬러 속성(sRGB, 면 코너)에 둔다. `A.paint / A.gradient` 사용.
3. **머티리얼 슬롯은 3개뿐**: `M_Toon`(불투명 툰), `M_Emit`(발광: 눈·수정·불꽃·룬), `M_Clear`(반투명: 슬라임·해파리·얼음·유령).
   Unity가 이름으로 공용 머티리얼에 매핑한다(캐릭터/환경 세트 분리, 외곽선·노이즈 자동).
4. **애니메이션 에셋** (`Characters/`, `Enemies/`, `NPCs/`):
   - 아마추어 오브젝트 이름 `Rig`, 스킨 메시 하나 `Body`(파츠별 본 1개 강체 웨이트, `A.skin`).
   - 액션 이름(정확히): `Idle`(루프), `Run`(루프), `Attack`, `Cast`, `Hit`, `Die`, `Victory`. 영웅/NPC는 `Walk`(루프)도 추가.
     비행형의 `Idle`/`Run`은 공중 정지 비행.
   - 타이밍 규약: `Attack`은 **40 %** 지점이 타격 순간, `Cast`는 **60 %** 지점이 발동 순간. `Die`는 마지막 프레임 자세 유지(눕거나 무너짐).
   - 30 fps. Idle 40–60f, Run 16–24f, Attack 18–30f, Cast 30–40f, Hit 10–14f, Die 24–36f, Victory 36–48f.
   - FBX take 이름 `Rig|Idle` → Unity 클립 `Idle`. `Idle/Run/Walk/Fly/Float/Hover/BattleIdle/*Loop`는 자동 루프.
5. **무기 소켓**: 영웅 리그에 `weapon.R`(오른손 무기)와 `weapon.L`(왼손: 활·방패) 본. 본 head = 손잡이, tail = 무기가 뻗는 방향.
   Unity에서 무기 FBX를 이 본의 자식으로 로컬 0/0/0에 붙인다.
6. **무기 FBX**: 정적 메시 1개. 원점 = 손잡이(쥐는 점), 날/자루는 **+Z 방향**으로 뻗음, 날의 앞면(날카로운 쪽)은 -Y.
7. **정적 에셋** (`Environment/`, `Town/`, `Props/`, `Weapons/`): 아마추어 없음. 한 FBX에 여러 루트 오브젝트 가능.
   움직이는 부분(문짝, 상자 뚜껑)은 별도 오브젝트로 두고 피벗을 경첩에 둔다(이름 `Lid`, `Door`).
8. **목표 폴리곤 예산**: 영웅 6–12k tris, 일반 몬스터 3–8k, 보스 10–25k, 환경 타일 조각 200–3k. 현재 제작물에는 이 목표를 넘는 모델이 있으므로 목표를 실측값으로 오인하지 않는다.
9. 각 생성기는 끝에 `A.render_preview(...)`로 `preview/`에 검수 이미지를 남기고, `A.save_blend(...)`로 `.blend`를 남긴다.

적 28종의 실제 삼각형 수·리그·웨이트·클립·FBX 재임포트 결과는 `blend/enemy_production_all.json`에 기록된다. 일반/엘리트는 1,696–12,812 tris, 보스는 23,724–28,504 tris이며, 원형을 임의 감축하지 않았다. 영웅도 약 16.5–19.9k tris다. 저사양 성능이나 60 FPS는 이 수치만으로 보장하지 않으며 실제 플레이어 빌드 측정으로 판단한다.

전체 적 제작은 `Blender/enemies_a/generate_all.py`, 전체 무기·장비 제작은 `Blender/weapons/generate_all.py`, 네 바이옴 제작은 `Blender/environment/regenerate_all.py`로 실행한다. 초상화·아이콘은 FBX 제작 후 `Blender/ui/render_icons.py`를 실행한다. UI 패널·버튼 PNG와 9-slice Sprite 설정은 `python Tools/ui/gen_ui_sprites.py`가 함께 생성한다.

## 아트 디렉션

- 레퍼런스: 기존 2D 원화(치비 애니메 JRPG, 굵은 실루엣, 채도 높은 팔레트). 영웅은 2.5–3등신, 머리 큼, 큰 눈.
- 툰 셰이딩 + 외곽선이 Unity에서 입혀지므로, Blender에서는 **실루엣과 색 구분**에 집중한다.
  면 하나에 한 색, 큰 형태 → 중간 디테일(벨트·장식·테두리) 순서. 금색 테두리, 보석 같은 발광 포인트로 상업 게임 느낌을 낸다.
- 매끈한 곡면은 `A.subdivide`(레벨 1–2)나 높은 세그먼트로. 각진 돌/바위는 bevel 상자 + `A.deform` 노이즈.

## 에셋 목록과 경로 (Unity 코드가 이 경로를 그대로 로드한다)

경로는 `Assets/_Game/Resources/Art/` 기준. id는 `docs/CONTENT_DESIGN.md`·데이터 JSON의 id와 같다.

| 분류 | 경로 | 비고 |
|---|---|---|
| 영웅 | `Characters/<id>/<id>.fbx` | warrior, mage, archer, cleric. 무기 미포함(검사 방패는 몸에 포함) |
| NPC | `NPCs/<id>/<id>.fbx` | innkeeper(마사), shopkeeper(피핀), smith(브론), guild_clerk(리나), elder(에드윈), villager_a/b/c(주민). 액션 Idle/Walk/Talk(+Wave 선택) |
| 몬스터 | `Enemies/<id>/<id>.fbx` | 데이터의 적 28종 전부(엘리트·grave_bat 포함). 엘리트는 기본형 생성기에 장식(왕관·갑주·뿔 등)+팔레트 변경 |
| 무기 | `Weapons/<equipment_id>.fbx` | sword_*, staff_*, bow_*, mace_* 20종 |
| 방어구·장신구 전시 모델 | `Props/Equipment/<equipment_id>.fbx` | 아이콘 촬영용(armor_*, garb_*, robe_*, acc_*) |
| 아이템 | `Props/Items/<item_id>.fbx` | 소비 14 + 재료 16 |
| 상태 엠블럼 | `Props/Status/<status_id>.fbx` | 22종 |
| 속성 엠블럼 | `Props/Elements/<name>.fbx` | slash, blunt, pierce, fire, ice, thunder, dark, holy |
| UI 엠블럼 | `Props/UI/<name>.fbx` | attack, skill, ultimate, item, guard, flee, auto, gold, key, map, party, camp |
| 공용 소품 | `Props/Common/<name>.fbx` | chest_common/chest_rare(뚜껑 `Lid`), gold_pile, key_item, campfire, banner_party |
| 던전 키트 | `Environment/<tileset>/<piece>.fbx` | tileset ∈ verdant_ruins, frost_grotto, ember_caverns, haunted_crypt. 조각 목록은 아래 |
| 전투 아레나 | `Environment/<tileset>/arena.fbx` | 원점 중심 반경 ~9 m 평지 무대 + 가장자리 장식 + 원경. 아군은 -Y 쪽, 적은 +Y 쪽, 카메라는 -Y에서 +Y를 봄 |
| 마을 | `Town/town.fbx` | 마을 전체 레이아웃 한 파일. 위치용 Empty와 충돌용 `Col_` 메시 포함 (아래) |

### 던전 키트 조각 (각 tileset 동일 이름)
그리드 1칸 = **4 m × 4 m**. 원점 = 칸 중심 바닥(z=0).
`floor_a, floor_b, floor_c` (4×4 바닥 타일, 윗면 z=0) · `wall_a, wall_b, wall_c` (4×4 칸을 꽉 채우는 벽 블록, 높이 4.5 m, 네 면 모두 장식, 윗면 장식) ·
`door`(칸 경계 문틀 + `Door` 문짝, 경첩 피벗, 통로는 Y축 방향) · `door_locked`(문 + 자물쇠) · `stairs_down` · `stairs_up` ·
`chest`(본체 + `Lid`, 뚜껑 피벗은 뒤쪽 경첩) · `lore_stone`(발광 룬 비석) · `trap`(바닥판 + `Spikes`) · `spring`(회복의 샘) · `warp`(마법진 발판) ·
`torch`(광원 소품, 불꽃은 M_Emit, 빛 위치 Empty `LightAnchor`) · `decor_1`…`decor_6`(작은 장식 소품) · `overlay_1`, `overlay_2`(바이옴 오버레이: 덩굴/고드름/종유석/거미줄, 벽 블록 옆면에 붙이는 장식) ·
`boss_gate`(보스 칸 장식) · `foe_marker`(FOE 위치 경고 장식, 선택) · `arena`.

### Empty·충돌 규약 (마을·아레나)
- 이름이 `Spot_`으로 시작하는 Empty = 위치 표식 (`Spot_spawn`, `Spot_innkeeper`, `Spot_shopkeeper`, `Spot_smith`, `Spot_guild_clerk`, `Spot_elder`, `Spot_gate`, `Spot_villager_1..n`, `Spot_camera_title`).
- 이름이 `Col_`로 시작하는 메시 = 보이지 않는 충돌체(Unity가 렌더러 제거 + MeshCollider). 바닥은 `Col_Ground`.
- 이름이 `LightAnchor`로 시작하는 Empty = 점광원 위치(따뜻한 색 기본).
