# 35 — TownWorld environment audit

- 요청 모델/effort: `gpt-6-astra` / `high`. 요청 서비스 등급: Fast/priority. 이 감사에 제공된 실행 결과에는 실제 모델·effort·서비스 등급을 독립적으로 검증할 메타데이터가 없으므로 관측값은 미확인이다. 설정 변경이나 모델 대체를 수행하지 않았다.
- 확인한 브랜치: `codex/astra-enrichment-20261015`; HEAD: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.
- 범위: TownWorld, EnvironmentProcessor, TownCamera, 관련 ArtLibrary/importer 부분, town 배치 생성 소스와 Tripo 배치 명세. 런타임 재현, 테스트, 빌드, Unity/브라우저 실행 없이 소스만 검토했다. 기존 작업은 수정하지 않았다.

## 발견 사항 (2건)

### 1. [P2] 다섯 번째 광장 나무의 메시와 충돌체 위치가 다르다

- 근거: `Blender/town/guild.py:351-352`는 다섯 번째 나무의 충돌 배치를 Blender 좌표 `(-14.0, 1.0)`에 scale `1.1`로 호출한다. `guild.py:246-254`는 Tripo 나무를 사용할 때도 이 위치에 줄기 충돌체를 생성한다. 반면 `Blender/town/tripo_pieces.json:682-689`의 실제 `Tree_plaza_5` 인스턴스는 `(-11.8, -5.4, 0)` / scale `0.9`이다. JSON 인스턴스 변환은 `guild.py:875-890`에서 적용되므로 두 배치는 자동 동기화되지 않는다.
- 재현 경로: 현재 배치 소스로 town을 생성·임포트한 상태에서 서쪽 광장 나무 `Tree_plaza_5`의 줄기 중심으로 걸어간다. 이어 기존 충돌 좌표 `(-14.0, 1.0)` 주변을 확인한다. 좌표는 Blender의 수평 X/Y이며 Unity 좌표로 그대로 입력하면 안 된다.
- 영향: 보이는 나무 줄기에는 대응 충돌체가 없고 약 6.8m 떨어진 위치에 나무 충돌체가 남는다. 기본적인 광장 이동에서 메시 관통 또는 시각적 근거가 없는 이동 차단을 만든다. 현재 체크인된 바이너리 FBX의 실제 배치는 실행·디코딩으로 확인하지 않았으며, 확정한 것은 생성 소스의 불일치다.
- 통합 제안: 나무 메시와 줄기 충돌체가 같은 JSON 인스턴스의 위치·scale을 사용하게 한다. 재생성 후 두 위치에서 리더 이동을 확인한다.

### 2. [P2] 동료가 장애물을 우회하지 않고 모서리를 가로지른다

- 근거: `Assets/_Game/Scripts/Runtime/World/TownWorld.cs:148-157`은 리더 `party[0]`에만 CharacterController를 붙인다. 같은 파일 `:292-300`은 동료를 앞 캐릭터의 현재 위치 뒤쪽으로 `Transform.position = Vector3.MoveTowards(...)`로 직접 이동시킨다. 이 경로에 충돌 검사나 리더가 실제 통과한 경로 추적이 없다.
- 실제 장애물 근거: `Blender/town/guild.py:227-229`는 벤치 충돌체를 만들고 `:360-361`은 북쪽 광장에 두 벤치를 둔다. `:398-401`은 Tripo 음식 카트에도 몸체 충돌체를 유지한다.
- 재현 경로: 두 명 이상 파티로 북쪽 광장 벤치의 긴 변을 따라 이동하다 끝에서 돌아 짧은 변을 지난다. 리더가 모서리를 우회하는 동안 동료는 갱신된 목표를 향해 직선으로 접근한다. 카트 모서리를 도는 일반 이동도 같은 경로를 사용한다.
- 영향: 리더를 막는 벤치·카트 몸체를 동료가 가로질러 통과하며 환경과 파티 실루엣이 겹친다. 소스에서 확인한 이동 경로에 따른 결과이며 실제 영상 재현은 수행하지 않았다.
- 통합 제안: 동료가 리더의 통과 위치 기록을 따라가게 하거나 충돌을 고려한 추종 이동을 사용한다. 리더의 기존 장애물 충돌은 유지한다.

## 소품 다양성·가시성 검토 및 Tripo 브리프 1개

배치 명세에는 이미 분수, 노점, 게시판, 배너, 나무, 가로등, 상자, 작업장 화물, 바리케이드가 있다. 나무와 노점은 동일 원본의 여러 인스턴스이므로 단순 복제보다 길드 활동을 설명하는 소품 하나가 적합하다. TownCamera는 건물 bounds, 지붕/차양 셀과 나무 투명화를 처리한다. 화면을 실행하지 않았으므로 전체 시야 확보나 소품 가독성 통과 판정은 하지 않는다.

**제안: 낮은 이동식 게이트 탐사 장비 점검대 (`guild_field_gear_station`) 1종.**

정확한 이미지 브리프: “Single standalone mobile equipment inspection station for a Korean urban hunter guild at dawn, stylized hand-painted game prop matching slate/navy guild buildings. Waist-high compact wheeled workbench, 1.4m wide × 0.65m deep × 1.05m tall, one closed rugged field case integrated on top, two securely clipped cyan crystal detector tools, a small coiled cable attached to the side, matte navy metal, restrained cyan trim and one amber safety latch, subtly worn edges. Clear compact silhouette, all parts visible, front three-quarter view, plain neutral background. No people, no scenery, no lettering or logo, no canopy, no floating parts, no tall poles.”

- 후속 제작 시 ChatGPT 웹 GPT-6 / Extra High에서 4–6개 후보를 비교하고 선택본 하나만 Tripo Studio에 전달한다. 여기서는 생성하지 않았다.
- Tripo 생성 1회, Retopo Triangle / Smart Mesh로 3k–6k triangles, 작은 소품용 1k 텍스처, 단일 정적 FBX, 바닥 중심 pivot. 리깅·애니메이션 불필요. 원본과 모델/effort·선택 사유·실제 표시 비용은 프로젝트 ArtSource sidecar에 보관한다.
- 배치 후보는 기존 작업장 화물 옆 시설 가장자리다. 실제 좌표는 부모 통합 시 메시 bounds를 보고 정한다. NPC 접근로 및 중앙 광장에는 놓지 않고, 통행 폭 1.5m 이상과 NPC 상호작용 반경을 확보한다. 몸체에 맞는 단순 충돌체 하나를 두고 높이 1.05m로 간판·인물·카메라 시야를 가리지 않게 한다. 이 수치는 제안 사양이며 검증된 배치 결과가 아니다.

## 완료 확인

- [x] 요청한 브랜치와 기준 HEAD 확인.
- [x] 최대 2건의 소스 근거, 정확한 줄, 재현 경로와 영향 기록.
- [x] Tripo 소품 브리프 정확히 1개 제시, 생성·크레딧 소비 없음.
- [x] 테스트/빌드/브라우저/중첩 에이전트/설정·게임 소스 변경 없음.
- [x] 이 지정 보고서만 작성. 런타임 검증과 수정·통합은 메인 담당자에게 남김.
