# Tree_plaza_5 — actual FBX evidence and bounded correction

## 후속 구현 — 사용자 승인 범위 적용

이 절이 현재 구현 상태이며, 아래의 FBX 측정·권고 절은 수정 전 조사 기록이다. 이번에는 승인된 소스 1줄, 새 헬퍼와 meta, 이 문서만 수정했다. 이전 절의 “문서만 작성”, “제안이며 적용하지 않음”은 첫 조사 시점의 상태다.

- `Blender/town/guild.py:351`: 다섯 번째 나무 좌표만 `(-14.0,1.0)`에서 `(-11.8,-5.4)`로 변경했다. 다음 줄의 크기 계수와 `tree()` 충돌 치수 계산은 그대로다. `town.fbx`는 재생성하지 않았다.
- `Assets/_Game/Scripts/Runtime/World/TownEnrichment.cs`: `Abyss.Runtime.World.TownEnrichment.Apply(GameObject town)`을 추가했다. 새 파일의 Unity meta GUID는 `d9ca5345dbae429a8bcc1b58c3d6a741`이다.
- 나무 보정은 정확한 이름 `Tree_plaza_5`와 `Col_Tree_plaza_-140_10`만 찾는다. 프록시 Transform의 world X/Z를 나무 Transform의 world X/Z로 맞추며 기존 world Y, 크기, 회전은 유지한다. Physics bounds 동기화에 의존하지 않는다. 둘 중 하나가 없으면 다른 프록시를 추측하여 이동하지 않는다.
- 점검대는 `ArtLibrary.SpawnStatic("Art/Props/GuildFieldStation/guild_field_gear_station", town.transform)`으로 불러온다. local position `(17.3,0.03,-4.9)`, local yaw `-90°`만 설정하며 scale은 변경하지 않는다.
- 렌더 모델 이름은 `Guild_Field_Gear_Station`이고, **렌더러 없는 별도 자식** `Col_Guild_Field_Gear_Station`에만 BoxCollider를 추가한다. center `(0,0.525,0)`, size **`(1.4,1.05,0.665)`**, `isTrigger=false`다. 사용자 승인된 실제 깊이 **0.665m**가 아래 초기 브리프의 0.65m를 대체한다. 모델 자체를 `Col_`로 명명하거나 렌더러를 비활성화/삭제하는 코드는 없다.
- `Apply`를 다시 호출하면 기존 점검대 자식과 박스를 재사용하여 중복 스폰/콜라이더 추가를 피한다. null town은 `ArgumentNullException`을 낸다.
- 필수 에셋 누락은 기존 ArtLibrary 정책을 따르며, `InvalidOperationException: Missing static art: Art/Props/GuildFieldStation/guild_field_gear_station`으로 경로를 명시한다. 조용히 생략하거나 대체 지오메트리를 만들지 않는다. 최초 구현 읽기에서는 에셋이 없었고, 최종 검토 시 부모가 복사한 해당 `.fbx` 파일의 존재를 확인했다. Unity import/Resources 로드 성공까지 검증한 것은 아니다.

호출 소유자는 TownWorld 담당자다. 필요한 순서는 다음과 같다.

```csharp
var town = ArtLibrary.SpawnStatic(ArtLibrary.TownPath, transform);
TownEnrichment.Apply(town);
layout = EnvironmentProcessor.Process(town, app.Atmosphere.Current.TorchColor, 2f, 7f);
// ...
rig.Collect(town.transform);
```

이 작업자는 **TownWorld.cs를 수정하지 않았다**. 최종 읽기에서는 다른 담당자가 `TownWorld.cs:98`에 Apply 호출을, `:99`에 Process를, `:124`에 Collect를 배치한 것을 확인했다. 따라서 별도 프록시 보정을 중복 추가할 필요가 없다. 향후 파일 변경 시 줄 번호보다 호출 순서를 기준으로 확인한다.

깊이 0.665m의 최종 외곽은 Blender X `[16.9675,17.6325]`, Y `[4.2,5.6]`이다. 이전 실제 FBX 측정값으로 계산한 마켓/작업장 간격은 여전히 각 1.6m이며, 화물 프록시까지의 간격은 1.7775m다. 이는 치수로 재계산한 값이고 새 Unity 플레이 검증은 아니다.

**정적 검토 결과:**

- [x] guild.py diff가 좌표 1줄뿐이고 크기 계산은 보존됨.
- [x] 헬퍼 API·네임스페이스, 정확한 노드명·리소스 경로·위치·회전·BoxCollider 치수 확인.
- [x] EnvironmentProcessor가 제거하는 `Col_` MeshRenderer와 시각 모델을 분리한 구성 확인.
- [x] 자기 호출의 재진입 시 자식/박스 재사용과 Transform 기반 나무 보정 확인.
- [x] 기존/신규 소스 읽기 검토 및 `git diff --check` 수행. Unity 테스트·컴파일·빌드·아트 재생성은 수행하지 않음.
- [x] `town.fbx` SHA-256은 아래 조사 때와 같은 `4C128381CFD9097A96175563BDCF7CE5FEDAE1106ED5E4AE589F2ABA9711C6C4`.

구현 직후 `guild.py` SHA-256: `4B48463DE85A00D416075A721318F74A75EBBE1AA13C98570A5D1DF0C3D07C6F`.
구현 직후 `TownEnrichment.cs` SHA-256: `C9CA9FF24F7DE6B4B3309D37442B348D4941FA46BDBE037C2A06C2BFE4906AE4`.

## 최초 FBX 조사 기록

2026-10-15 22:39 KST. Checkout: `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`, HEAD `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c`.

요청 모델/effort는 `gpt-6-astra` / `high`다. 모델·effort 및 Fast/priority 서비스 등급을 독립적으로 확인할 실행 메타데이터는 제공되지 않았다. 모델/설정 변경, 중첩 에이전트, Unity 실행, 게임 소스·FBX 수정은 하지 않았다. 이번 작업의 유일한 작성 파일은 이 문서다.

## 결론

보고서 35의 나무 배치 불일치는 **현재 체크인된 town.fbx에도 존재한다.** 실제 메시가 있는 위치는 Blender `(-11.8, -5.4, 0)`, 해당 줄기 충돌체의 수평 중심은 `(-14, 1)`이다. 수평 이격은 **6.76757m**다. JSON의 나무 위치가 실제 FBX 메시와 일치하며, `guild.py`의 오래된 다섯 번째 나무 좌표가 FBX 충돌체와 일치한다.

최소 수정은 **나무 메시를 그대로 두고 기존 충돌체 하나의 수평 위치만 옮기는 것**이다. 현재 FBX를 유지하는 통합이라면 TownWorld 초기화에서 해당 인스턴스의 충돌체를 정렬하는 작은 보정으로 해결할 수 있다. 전체 아트 재생성이 필요하지 않다. 아래는 제안이며 적용하지 않았다.

## 실제 FBX를 읽은 방법과 측정값

`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`의 headless FBX importer를 사용했다. 관측 버전은 **Blender 5.2.1 LTS**, build hash `9e2066aef7ef`이다. 실행 옵션은 `--background --factory-startup --disable-autoexec --threads 2 --python-expr`였으며, 배치 측정 재실행에는 `--python-exit-code 1`도 사용했다. 새 임시 프로세스의 기본 씬만 사용했고 설정 저장·blend 저장·FBX export·guild.py 실행·렌더링은 하지 않았다.

측정은 `bpy.ops.import_scene.fbx(..., use_anim=False)`로 **Assets/_Game/Resources/Art/Town/town.fbx**를 읽고, 각 정점에 `object.matrix_world @ vertex.co`를 적용한 실제 월드 좌표로 수행했다. FBX를 재임포트한 오브젝트에는 축 보정 회전이 있으므로 local bounds나 Euler 값만으로 판정하지 않았다.

아래 좌표는 모두 Blender X/Y 수평, Z 위쪽, 단위 m다.

| 실제 FBX 오브젝트 | 원점/중심 | 월드 정점 AABB min | 월드 정점 AABB max |
|---|---|---|---|
| `Tree_plaza_5` | 원점 `(-11.8,-5.4,0)` | `(-13.51045,-6.91041,0)` | `(-10.28201,-3.92984,3.24)` |
| `Col_Tree_plaza_-140_10` | 중심 `(-14,1,0.66)` | `(-14.22,0.78,0)` | `(-13.78,1.22,1.32)` |
| `Workshop_Cargo` | 원점 `(14.6,5.2,0)` | `(14.01059,4,0)` | `(15.18941,6.4,1.34797)` |
| `Col_Workshop_Cargo` | 중심 `(14.6,5.2,0.6)` | `(14.01,4,0)` | `(15.19,6.4,1.2)` |
| `Guild_Workshop` | 원점 `(15.6,10.6,0)` | `(15.44018,7.2,0)` | `(20.77628,14,4.81725)` |
| `Col_Workshop` | 중심 `(18.188,10.6,0.6)` | `(15.6,7.2,0)` | `(20.776,14,1.2)` |
| `Guild_Market` | 원점 `(15.6,-1.5,0)` | `(14.94111,-5.6,0)` | `(20.4128,2.6,5.40754)` |
| `Col_Market` | 중심 `(18.0065,-1.5,0.6)` | `(15.6,-5.6,0)` | `(20.413,2.6,1.2)` |

`Tree_plaza_5`는 실제 정점 2,046개이며 수관·바닥 장식을 포함한 AABB다. 전체 AABB를 몸체 충돌체로 사용하면 기존 통행 공간을 크게 줄이므로 사용하면 안 된다. 참고로 높이 0.15–0.4m의 실제 정점 8개는 X `[-12.04372,-11.65032]`, Y `[-5.64702,-5.20972]`에 있다. 이 값은 하부 형상의 참고값이며 새 정밀 콜라이더 적합성 판정은 아니다.

임포터의 동작도 확인했다. `Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:353-362`는 Town의 `Col_*` 메시 local bounds로 BoxCollider를 만든다. `Assets/_Game/Scripts/Runtime/World/EnvironmentProcessor.cs:34-39`는 이를 수집하고 프록시 렌더러만 제거한다. 따라서 현재 FBX에 측정된 원격 프록시는 런타임 충돌 위치에 영향을 주는 실제 입력이다. Unity에서의 실행 결과·화면 캡처는 이 문서의 증거 범위에 포함하지 않는다.

## 소스와의 대응 및 정확한 최소 수정안

- `Blender/town/tripo_pieces.json:682-689`: `Tree_plaza_5`, location `[-11.8,-5.4,0]`, yaw `280`, uniform visual scale `0.9`. **실제 메시와 일치하므로 변경하지 않는다.**
- `Blender/town/guild.py:351-352`: 다섯 번째 위치 `(-14.0,1.0)`, 줄기 프록시 크기 계수 `1.1`.
- `Blender/town/guild.py:246-254`: Tripo 나무가 있어도 전달받은 위치에 `Col_Tree_*`를 생성한다.
- `Blender/town/guild.py:875-890`: 시각 메시에는 JSON 인스턴스 위치·회전·scale을 적용한다. 줄기 프록시와 별도의 배치 경로다.

**현재 FBX를 보존하는 권고:** `TownWorld.Initialize`에서 `EnvironmentProcessor.Process` 직후, `TownCamera.Collect` 이전에 정확한 이름의 나무와 프록시를 찾아 프록시만 수평 정렬한다. 현재 읽은 파일에서는 각각 `TownWorld.cs:61`, `:86` 근처다. 다른 작업자의 변경으로 줄 번호가 움직일 수 있으므로 메서드/호출을 기준으로 통합한다.

제안 로직은 아래와 같다. 이 코드 블록은 문서일 뿐이며 소스에 적용하지 않았다.

```csharp
var tree = EnvironmentProcessor.Find(town.transform, "Tree_plaza_5");
var proxy = EnvironmentProcessor.Find(town.transform, "Col_Tree_plaza_-140_10");
var box = proxy != null ? proxy.GetComponent<BoxCollider>() : null;
if (tree != null && box != null)
{
    Vector3 center = box.transform.TransformPoint(box.center);
    Vector3 offset = Vector3.ProjectOnPlane(tree.position - center, town.transform.up);
    proxy.position += offset;
}
```

기존 BoxCollider의 크기·회전·세로 높이와 참조는 유지한다. 재호출 시 수평 오차가 0이므로 중복 이동하지 않는다. 모든 나무나 모든 Col_ 노드에 일괄 적용하지 않는다. 해당 노드를 찾지 못하는 새 아트 버전에서는 임의의 다른 노드를 보정하지 않는다.

이 FBX에서 예상되는 정확한 변화:

| 항목 | 보정 후 값 |
|---|---|
| Blender 이동량 | `(2.2,-6.4,0)` |
| Blender 충돌체 중심 | `(-11.8,-5.4,0.66)` |
| Blender 충돌체 AABB | min `(-12.02,-5.62,0)`, max `(-11.58,-5.18,1.32)` |
| Blender 충돌체 크기 | `(0.44,0.44,1.32)` 유지 |
| Unity 예상 이동량 | `(2.2,0,6.4)` |
| Unity 예상 중심/크기 | 중심 `(-11.8,0.66,5.4)`, 크기 `(0.44,1.32,0.44)` |

Unity 수치는 `guild.py:15`에 명시된 `(x,z,-y)` 변환 및 `Blender/lib/abyss_bpy.py:503-515`의 FBX export 축 설정에 근거한 값이다. 루트 변환을 고려한 실제 정렬에는 위의 Transform 기반 코드를 우선한다. Unity에서 직접 측정한 수치로 표현하지 않는다.

**다음 생성에서의 재발 방지:** 부모가 소스 변경을 승인해 통합할 때 `guild.py:351`의 다섯 번째 좌표만 `(-14.0,1.0)` → `(-11.8,-5.4)`로 맞추는 것이 가장 작은 소스 수정이다. 기존 프록시 크기 계산은 유지하면 위 보정과 동일한 0.44×0.44×1.32m 박스가 나온다. 시각 메시 scale `0.9`를 콜라이더 크기에 무조건 적용하지 않는다. 두 값은 별도의 형상 사양이다. 이 한 줄 수정만으로 이미 존재하는 FBX가 바뀌지는 않으므로, 현재 아트에 대해서는 위 런타임 보정이 필요하다. 전체 생성·FBX 수정은 이번 권고 실행 범위가 아니다.

부모의 최종 확인 항목은 나무 주변에서 리더가 줄기를 통과하지 않는지, 이전 `(-14,1)` 위치의 이동 차단이 사라졌는지, 다른 나무/시설의 충돌과 카메라가 유지되는지다. 이는 이번에 실행한 검증이 아니다.

## guild_field_gear_station 권고 배치

기존 화물의 동쪽, 마켓과 작업장 사이에 새 정적 소품을 별도 자식으로 부착하는 위치를 권고한다. 새 town.fbx로 병합할 필요가 없다. 자산이 준비된 뒤 부모가 `town.transform` 아래에 배치하고, 필요한 충돌체를 준비한 다음 `EnvironmentProcessor.Process` 및 `TownCamera.Collect`가 수행되게 통합하면 된다. 현재는 새 소품 파일·노드·콜라이더를 만들지 않았다.

| 사양 | 권고 |
|---|---|
| Blender 위치 | **`(17.3,4.9,0.03)`**, 바닥 중심 pivot |
| Blender 회전 | **Z `-90°`**, 기본 전면이 local `-Y`인 자산 기준, 광장 쪽 `-X`를 향함 |
| 크기 | local 폭 X **1.4m**, 깊이 Y **0.65m**, 높이 Z **1.05m**, scale 1 |
| Blender 최종 footprint | X `[16.975,17.625]`, Y `[4.2,5.6]`; 상단 Z `1.08` |
| Unity 대응 | local position **`(17.3,0.03,-4.9)`**, yaw **`-90°`**, 기본 전면이 local `+Z`인 정규화된 자산 기준 |
| Unity 자산 치수 | 폭 X `1.4`, 높이 Y `1.05`, 깊이 Z `0.65`; yaw 적용 후 수평 외곽 X 0.65 × Z 1.4 |
| 충돌 | 몸체 외곽을 넘지 않는 단순 박스 1개; 넓은 보이지 않는 interaction blocker나 지붕 없음 |

**실제 지형 높이:** 후보 중심에서 위에서 아래로 FBX 삼각형 raycast를 수행했다. `Plaza` 표면 Z **0.03**, `Col_Ground` Z **-0.030001**, `City_Ground` Z **-0.04**다. 시각 소품의 바닥을 Plaza 높이 0.03에 두어 포장면에 묻히지 않게 한다.

**실제 메시·프록시 외곽과의 간격:**

| 대상 | 후보 몸체와의 수평 가장자리 간격 |
|---|---:|
| 마켓 메시 / Col_Market | **1.600m** |
| 작업장 메시 / Col_Workshop | **1.600m** |
| Workshop_Cargo 메시 | **1.785588m** |
| Col_Workshop_Cargo | **1.784999m** |
| Spot_smith에서 후보 footprint까지 | **5.647178m** |

실제 FBX의 `Spot_smith`는 `(13.2,9.8,0)`이다. 후보 중심까지 6.389053m이며, 몸체 외곽도 시설의 기존 3.2m 상호작용 반경 밖이다 (`TownWorld.UpdateNearest`, 현재 `TownWorld.cs:459`). 작업장 서쪽 접근로를 그대로 두고, 마켓 북쪽·작업장 남쪽·화물 동쪽에도 각각 통로가 남는다. 리더 반지름 0.28m를 양옆으로 제외해도 1.6m 간격에는 중심 이동 폭 약 **1.04m**가 남는다.

**병합된 장식 메시까지 포함한 형상 검사:** 전체 FBX의 메시 삼각형을 실제 월드 좌표로 변환하고 아래 상자에 대해 6개 면 polygon clipping으로 교차를 집계했다. 특정 이름의 충돌체만 확인한 결과가 아니다. 후보 형상 자체는 생성하지 않았고, 제안 치수의 공간만 계산했다.

| 검사 영역 (Blender min → max) | 교차하는 기존 메시 삼각형 |
|---|---:|
| 몸체 상부: `(16.975,4.2,0.16)` → `(17.625,5.6,1.21)` | **0** |
| 몸체 수평 반지름 0.28 확장: `(16.695,3.92,0.24)` → `(17.905,5.88,1.60)` | **0** |
| 남쪽 통로: `(15.3,2.65,0.24)` → `(20.25,4.15,1.60)` | **0** |
| 북쪽 통로: `(15.3,5.65,0.24)` → `(20.25,7.15,1.60)` | **0** |
| 화물 동쪽 통로: `(15.24,4,0.24)` → `(16.925,6.4,1.60)` | **0** |

높이 범위는 포장면을 제외하고 몸체·보행 장애를 확인하기 위한 것이다. 바닥 전체의 기복이나 실제 캐릭터 이동, 화면 구도·그림자·카메라 가시성까지 통과했다고 해석하지 않는다. 현 높이 1.05m는 주변 시설 간판/차양보다 낮으며 실제 배치 뒤 시각 검토는 부모가 수행해야 한다.

첫 배치 측정은 정점이 없는 메시에서 `ValueError: min() iterable argument is empty`로 중단됐다. 원본 파일을 변경하지 않고, 빈 메시 `Dungeon_Gate`를 명시적으로 건너뛰게 한 후 같은 범위의 측정만 재실행했다. 재실행은 `PLACEMENT_AUDIT`의 모든 결과를 출력하고 exit code **0**으로 종료했다. 나무/시설 좌표 측정 프로세스도 정상 종료했다.

## 파일 보존과 완료 범위

다음 세 파일의 SHA-256은 측정 전후 동일했고, 이 세 경로의 `git status --short` 출력은 없었다.

```text
Assets/_Game/Resources/Art/Town/town.fbx
4C128381CFD9097A96175563BDCF7CE5FEDAE1106ED5E4AE589F2ABA9711C6C4
Blender/town/guild.py
202942B6E8273D7BA596C7BE81F935C1A1844DD326C7A9DD86A4AB30B56CFE94
Blender/town/tripo_pieces.json
A9D1B149601E2B3920CDB228A220EAB097C9B8C7B0E5DC1E7B845BC47A61B6CB
```

- [x] 소스에 더해 실제 FBX 메시/충돌 프록시 위치 확인.
- [x] 위치만 바꾸는 정확한 최소 수정안과 현재 FBX 보존 방법 제시.
- [x] 점검대의 위치·회전·크기·바닥 높이·주변 간격을 실제 형상으로 확인.
- [x] 실행한 모든 headless 프로세스의 종료 확인.
- [x] 이 증거 문서만 작성. 소스 수정·아트 재생성·Unity 실행·설정 변경·reset/commit 없음.
