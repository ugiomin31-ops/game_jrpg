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
| `lib_humanoid/produce.py`, `textured.py` | 영웅·NPC 제작 진입점(리그·클립·FBX·미리보기·JSON 보고서), 텍스처 영웅의 PNG 내보내기 |
| `lib_anime/` | VRoid 샘플(CC0) 기반 텍스처 애니풍 영웅 빌더 `heroes_anime.HERO_BUILDERS` |
| `heroes/`, `npcs/`, `weapons/`, `enemies_a/`, `enemies_b/`, `bosses/`, `environment/`, `town/`, `props/`, `icons/` | 그룹별 생성기 |
| `blend/` | 생성 결과 `.blend` (편집·검수용) |
| `preview/` | Workbench 미리보기 PNG (검수용, 게임에 포함되지 않음) |
| `ui/render_icons.py` | 실제 FBX를 촬영해 `Resources/Icons/`에 투명 512px 초상화·아이콘 160개와 Sprite 메타데이터 생성 |

출력 FBX는 `Assets/_Game/Resources/Art/<Category>/...` 에 바로 쓴다. Unity가 자동 임포트한다.

## 계약 (Unity 쪽 `AbyssArtImporter.cs`가 의존)

1. **단위·방향**: 1 unit = 1 m. 캐릭터는 z=0 바닥에 서고 **-Y를 바라본다**(Blender 정면도). Unity에서는 +Z가 정면이 된다.
   좌우 규약은 Blender 표준: 캐릭터의 왼쪽(`.L`)이 +X, 오른쪽(`.R`)이 -X. (Unity 임포트로 검증됨: 미러링 없음.)
2. **색**: 텍스처 없음. 색은 `Col` 컬러 속성(sRGB, 면 코너)에 둔다. `A.paint / A.gradient` 사용.
   예외는 텍스처 애니풍 영웅(아래 "텍스처 영웅")뿐이다.
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

적 28종(v1)의 실제 삼각형 수·리그·웨이트·클립·FBX 재임포트 결과는 `blend/enemy_production_all.json`에 기록된다. 일반/엘리트는 1,696–12,812 tris, 보스는 23,724–28,504 tris이며, 원형을 임의 감축하지 않았다. 영웅도 약 16.5–19.9k tris다. 저사양 성능이나 60 FPS는 이 수치만으로 보장하지 않으며 실제 플레이어 빌드 측정으로 판단한다.

전체 적 제작은 `Blender/enemies_a/generate_all.py`, 전체 무기·장비 제작은 `Blender/weapons/generate_all.py`, 네 바이옴 제작은 `Blender/environment/regenerate_all.py`로 실행한다. 초상화·아이콘은 FBX 제작 후 `Blender/ui/render_icons.py`를 실행한다. UI 패널·버튼 PNG와 9-slice Sprite 설정은 `python Tools/ui/gen_ui_sprites.py`가 함께 생성한다.

## 신규 몬스터 v2 (`enemies_c/`)

`enemies_c/monster_kit.py`(`Monster`: 애니 눈·각진 `chunk`·`gem`·`petal`·`flame` 등)로 만든 23종(일반 18 + 엘리트/FOE 5).
id·한국어 이름·바이옴·층·역할은 `enemies_c/roster.py`(`ROSTER`)에 있고, `enemies_a/generate_all.py`가 이를 SOURCES에 합쳐 같은 검증(FBX 재임포트·Rig/Body/Col·7클립)을 거친다.

```
blender -b --factory-startup --python-exit-code 1 -P Blender/enemies_c/generate_all.py [-- --only yeti ...]
blender -b --factory-startup -P Blender/enemies_c/contact_sheet.py -- CELLS_DIR [--ids yeti ...]
python Blender/enemies_c/compose_sheet.py CELLS_DIR sheet.png      # PIL, 한글 라벨
```
결과 증거는 `blend/enemy_v2_production_all.json`(예산: 일반 ≤10k, 엘리트 ≤14k tris). 새 id의 도감 아이콘은 `ui/render_icons.py -- Enemies/<id> ...`로 렌더한다.

## CC0 몬스터 (Quaternius Ultimate Monsters · KayKit Skeletons)

`enemies_cc0/`는 리깅·애니메이션된 CC0 몬스터(glTF, `third_party/quaternius_ultimate_monsters/`, `third_party/kaykit_skeletons/`)를
위 계약대로 변환한다: 본 셰이프 정리 → 텍스처를 면 코너별로 샘플링해 `Col`에 굽기 → `Body` 하나로 합치기 → 적별 재색칠(M_Toon/M_Emit/M_Clear) →
원본 클립을 7개 액션으로 리샘플(Attack 40 %, Cast 60 %, Die 마지막 자세 유지) → 기존 절차 모델 크기에 맞춤 → `A.export_fbx`.

```
blender -b --factory-startup --python-exit-code 1 -P Blender/enemies_cc0/generate_all.py -- --jobs 2 [--only bat ...]
blender -b --factory-startup -P Blender/enemies_cc0/contact_sheet.py -- --out sheet.png [--actions --ids skeleton]
```
적별 레시피·원본 매핑·제외 사유는 `enemies_cc0/specs.py`(`SPECS`, `GAPS`). 결과 증거는 `blend/enemy_cc0_production_*.json`.
**주의**: `enemies_a/generate_all.py`를 전체로 다시 돌리면 `SPECS`의 적도 절차 모델로 덮어쓴다. 그 뒤에 `enemies_cc0/generate_all.py`를 다시 실행한다.

## 텍스처 영웅 (VRoid 기반 애니풍)

`lib_anime/heroes_anime.py`의 `HERO_BUILDERS`(archer부터)는 VRoid 샘플 몸체를 게임의 20본 리그에 웨이트를 옮겨
**한 개의 스킨 메시**로 만든다. 본·클립 이름은 치비 영웅과 같으므로 Unity Humanoid 경로(`HUMANOID` 마커)가 아니라
기존 Generic 경로로 들어간다.

```
blender -b --factory-startup -P Blender/heroes/generate_anime.py -- archer
```

`produce()`가 몸체에 이미지 텍스처가 있으면 자동으로 텍스처 경로를 탄다(`lib_humanoid/textured.py`).
- 출력: `Characters/<id>/<id>.fbx` + `Characters/<id>/<id>_tex/<머티리얼 이름>.png`.
  PNG는 메모리에서 재색칠된 현재 픽셀을 straight alpha sRGB로 쓰고, 최대 1024 px로 줄인다(알파 가중 박스 필터).
  다시 내보낼 때 같은 이름의 PNG는 덮어써서 Unity `.meta`(GUID)를 유지하고, 사라진 머티리얼의 PNG만 지운다.
- **PNG 파일 이름 = FBX 머티리얼 이름**이다. FBX에는 `<id>_tex/…png` 상대 경로 텍스처 참조도 들어간다.
- 머티리얼 이름은 VRoid 접미사를 유지한다: `_FACE`(눈썹·입·속눈썹·아이라인), `_EYE`(홍채·하이라이트·흰자), `_SKIN`, `_CLOTH`, `_HAIR`.
  텍스처 없는 절차 파츠(부츠·벨트·화살통)는 그대로 `M_Toon`/`M_Emit`/`M_Clear` + `Col` 정점색.
  쓰이지 않는 슬롯(표정 전용 눈, 교체된 신발)은 내보내기 전에 지운다.
- Unity(`AbyssArtImporter` → `TexturedMaterials`)는 PNG마다 `Characters/<id>/<id>_mat/<이름>.mat`(Abyss/Toon, `_BaseMap`=PNG)을
  한 번 만들어 FBX 머티리얼에 리맵한다. `_FACE`/`_EYE`: 알파 컷아웃, 외곽선 0, 그림자 캐스팅 끔. `_HAIR`: 컷아웃 + 양면.
  `_CLOTH`: 양면. 그 외 불투명. 만든 `.mat`은 재임포트해도 덮어쓰지 않으므로 손으로 조정해도 되고, 지우면 다시 만들어진다
  (메뉴 `Abyss/Sync Textured Hero Materials`).
- `.blend`에는 원래 VRoid 머티리얼과 (재색칠을 다시 pack한) 원본 해상도 이미지가 남는다. Workbench 미리보기는 TEXTURE 색 모드라
  `M_Toon` 파츠는 회색으로 보인다(검수용 한계).

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
| 몬스터 | `Enemies/<id>/<id>.fbx` | 데이터의 적 51종 전부(v1 28 + `enemies_c` v2 23, 엘리트·grave_bat 포함). 엘리트는 기본형 생성기에 장식(왕관·갑주·뿔 등)+팔레트 변경 |
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

바이옴별 구조(생성기 `environment/dungeon_cc0.py` + 절차 형상 `environment/arch_geo.py`):
ember_caverns = 불규칙 현무암 동굴 벽(용암 균열이 면에 박힘, 위로 갈수록 안쪽으로 기울어짐)·흑요석 기둥·육각 현무암/용암 웅덩이 바닥 ·
frost_grotto = 큰 면의 얼음 벽(일부 반투명, 뒤에 짙은 파란 코어)·눈더미·얼음 기둥·얼어붙은 폭포 ·
haunted_crypt = 고딕 베이(벽기둥·코니스)·납골 벽감·쇠창살·첨두 아치 제단·리브 볼트 천장 ·
verdant_ruins = 하늘이 열린 폐허(나무·잎 덩어리 벽, 낮은 무너진 석벽+나무, 열주 잔해), 꽃밭 바닥.
- 동굴/묘지 3종의 `floor_*`와 `stairs_down`에는 두 번째 루트 오브젝트 `Ceiling`(z ≤ 4.48에 매달림)이 있다. `DungeonWorld`가 그림자 캐스팅을 끈다.
- 자연 벽면은 칸 경계에서 같은 단면(base(z))을 쓰므로 이웃 블록과 이음매 없이 맞물린다. 면은 통로 쪽으로 최대 ~0.35 m(천장 아래는 ~0.9 m) 튀어나온다.
- `decor_N`은 `DungeonWorld.Dress`가 벽 옆에 놓는다: 칸 중심에서 벽 쪽 1.45 m, 옆으로 1 m, 로컬 -Y가 통로를 향함 → 반경 ~0.5 m 안에 둘 것.
  `overlay_N`은 벽 칸에 생성되고 -Y 면(y=-2)이 열린 칸을 향하도록 회전된다. 배치는 칸 좌표 해시로 결정적이며 충돌체가 없다.

### Empty·충돌 규약 (마을·아레나)
- 이름이 `Spot_`으로 시작하는 Empty = 위치 표식 (`Spot_spawn`, `Spot_innkeeper`, `Spot_shopkeeper`, `Spot_smith`, `Spot_guild_clerk`, `Spot_elder`, `Spot_gate`, `Spot_villager_1..n`, `Spot_camera_title`).
- 이름이 `Col_`로 시작하는 메시 = 보이지 않는 충돌체(Unity가 렌더러 제거 + MeshCollider). 바닥은 `Col_Ground`.
- 이름이 `LightAnchor`로 시작하는 Empty = 점광원 위치(따뜻한 색 기본).
