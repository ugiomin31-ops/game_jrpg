# World / input — 독립 읽기 전용 리뷰

- 요청 모델/effort: gpt-6-astra / high, Fast/priority 요청. 실제 모델·effort·서비스 등급은 독립적으로 노출된 런타임 증거가 없어 확인된 값으로 주장하지 않는다.
- 기준: codex/astra-enrichment-20261015, HEAD efdc1517f48ac8887e1fcf6843b6df44df6ebc3c 대비 현재 작업 트리의 TownWorld.cs, DungeonWorld.cs, UIInput.cs, GameUI.Town.cs 변경.
- 이 리뷰의 대상 소스는 수정하지 않았다. 관련 호출부·충돌체 생성 코드·마을 저작 소스만 추가로 읽었다. Unity/브라우저/빌드/테스트/하위 에이전트는 실행하지 않았다.
- 결론: 판매 수량 상한과 **메뉴 닫힘 프레임**의 차단은 정적으로 타당하다. 아래 두 항목은 추종 경로와 **메뉴 열림 프레임**에 남는 한계다. 플레이로 재현된 신규 회귀나 전체 런타임 통과를 주장하지 않는다.

## 1. 추종자 충돌은 추가됐지만 장애물 우회 경로는 없다

**위치:** `Assets/_Game/Scripts/Runtime/World/TownWorld.cs:328-335`.

앞 사람의 현재 위치에서 리더의 전역 heading을 0.95만큼 뺀 점으로 직진한다. 새 CharacterController.Move는 충돌면에서 정지/슬라이드하지만, 앞 사람이 실제로 지나온 경로, 중간 경유점, 막혔을 때의 우회 처리는 없다. 따라서 목표와 추종자 사이에 벽이 있고 목표 방향이 충돌면 안쪽을 향하면, 같은 막힌 방향을 매 프레임 다시 요청한다. 앞 사람과 리더가 멈추면 시간이 지나도 경로를 새로 찾지 못한다. 이는 종전의 관통 이동을 막은 뒤 새로 고려해야 하는 추종 동작의 한계다.

실제 장애물 근거:

- `Blender/town/town.py:218-230`은 중앙 분수에 3.4 × 3.4 × 2.5 충돌 상자를 저작한다.
- 배포 대상 `Assets/_Game/Resources/Art/Town/town.fbx` 바이트에도 `Col_Fountain` 이름이 존재함을 확인했다. FBX의 실제 import 결과/월드 bounds를 실행으로 측정한 것은 아니다.
- `Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:353-362`가 마을의 Col_ 메시를 BoxCollider로 만든다. `TownWorld.cs:60-61`에서 그 마을을 로드하고 처리한다.

**부모의 구체적 재현 확인:** 4인 파티로 중앙 분수의 모서리를 바짝 돌아 반대편에서 멈추고, 뒤쪽 추종자가 분수 앞면에 남는지 확인한다. 남은 경우 입력을 놓은 채 관찰해 앞으로만 미는 상태가 해소되는지 확인한다. 정면 충돌 상태에서 우회력이 없는 것은 코드로 확인되지만, 이 이동 조작으로 해당 상태가 실제 발생하는지는 이번 읽기 전용 작업에서 재현하지 않았다. 따라서 확정된 플레이 회귀로 승격하지 않는다.

**영향/권고:** 충돌 통과 방지와 파티 추종 완료는 별도 조건이다. 끼임이 재현되면 앞 사람의 충돌 검증된 이동 경로를 따라가도록 경유점을 유지하는 최소 수정이 적합하다. 충돌체를 끄거나 위치를 순간 이동시켜 해소하면 현재 변경의 목적을 잃는다.

## 2. Consume 가드는 메뉴를 여는 프레임 전체의 우선순위를 보장하지 않는다

**위치:** `Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:533-555`, `Assets/_Game/Scripts/Runtime/World/TownWorld.cs:293`, `Assets/_Game/Scripts/UI/Kit/UIInput.cs:112-115`.

ConsumedThisFrame은 Consume가 **이미** 호출됐는지만 확인한다. `GameUI.cs:269-277`의 Update가 메뉴 입력을 감지하고, `GameUI.cs:244-248`의 ShowPause에서 Consume 및 pause를 설정한다. 이 GameUI와 두 월드 클래스에는 DefaultExecutionOrder가 없고, 해당 .cs.meta에도 executionOrder가 없다. 현재 읽은 소스에는 UI 처리가 월드 Update보다 앞선다는 계약이 없다.

**정적 재현 순서:** 던전에서 held-input 반복 간격이 지난 프레임에 W를 누른 채 Tab을 누른다. DungeonWorld.Update가 먼저 실행되면 아직 pause/consume가 없어 :547의 이동을 실행하고, 뒤이어 GameUI.Update가 pause를 연다. 역순이면 이동이 차단된다. 정상 입력 조합이지만 실제 플레이에서 어느 순서가 관측되는지는 실행하지 않았다. 이미 열린 메뉴의 닫힘 문제와 구별해야 하며, 새 변경이 이 열림 문제를 처음 도입했다고 주장하지 않는다.

**영향/권고:** 메뉴를 열려는 프레임에도 던전 한 걸음/턴이 먼저 처리될 수 있다. 열림 입력까지 일관되게 우선 처리하려면 전역 입력 처리 순서를 명시하거나, 월드 이동 전에 pause/map 요청을 중재해야 한다. 부모는 W+Tab / W+Escape / W+M과 HUD 클릭+이동 입력을 함께 확인하는 것이 적합하다. 공개 DungeonWorld 액션에 무조건 ConsumedThisFrame 가드를 옮기면 아래 HUD 경로를 막으므로 피해야 한다.

## 타당한 부분과 보존된 호출 경로

- **메뉴 닫힘 순서:** 월드가 먼저 실행되면 기존 Paused/BlocksWorldInput이 차단한다. 닫힘 콜백이 먼저 실행되면 Consume가 같은 프레임의 월드 원시 입력을 차단한다. `GameUI.cs:266`의 pause 닫힘과 `TownWorld.cs:293`, `DungeonWorld.cs:432,536`을 대조했다. 열림 프레임의 한계를 닫힘 수정의 실패로 혼동하지 않았다.
- **HUD 액션:** `GameUI.DungeonHud.cs:165-169`는 Consume 후 action을 실행한다. `DungeonWorld.cs:433-436`의 공개 Move/Turn/Interact/WaitTurn은 기존 CanAct를 사용하고, 새 consume 가드는 Update에만 있다. 따라서 HUD가 스스로 소비한 입력 때문에 항상 무효화되는 문제는 보이지 않는다.
- **파티 내부 충돌:** `TownWorld.cs:157-187`은 리더/추종자 및 추종자 상호 간 IgnoreCollision을 설정한다. 의상 교체(:192-214) 시 새 컨트롤러에 다시 적용하고, 로스터 교체(:143-153)는 followers를 비운 뒤 재구성한다. 목록과 파티 인덱스에 새 불일치는 찾지 못했다.
- **정지 애니메이션:** :293,298의 IdleParty는 차단/대화 대기 중 리더뿐 아니라 추종자도 idle로 바꾼다. 실제 이동량(:336-343)으로 추종자의 보행 여부를 판단하는 변경은 벽을 향해 걷는 애니메이션을 줄이는 방향이다.
- **판매 수량:** `GameUI.Town.cs:120`의 Math.Min(count, GameState.MaxStack)은 `GameState.cs:129`의 99와 `TownServices.cs:226,263`의 거래 상한에 일치한다. 소유 수량 표시, 판매 연산 콜백, 거래 확인 및 재고 자체는 바꾸지 않는다. 이 한 줄에서 새 결함은 찾지 못했다.

## 읽은 변경의 식별값

다른 작업자가 같은 작업 트리에서 계속 수정할 수 있으므로 아래 파일 해시에 대한 리뷰다. 최종 수용은 부모가 통합한 파일로 다시 판단한다.

| 파일 | SHA-256 |
|---|---|
| Assets/_Game/Scripts/Runtime/World/TownWorld.cs | 29687581a996f4e6ff97aeef7d0ea9c88b19fd22e34d79289f55e34e4c4241e3 |
| Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs | 6035abdd9a27dc06b133bc09684c7699518b7a9f64bc53123f19e54d62a36d71 |
| Assets/_Game/Scripts/UI/Kit/UIInput.cs | f5cb7632ce27ce28f3e39199ac759b3ded32a7e7adf24f0e524393aeb1be33ee |
| Assets/_Game/Scripts/UI/Screens/GameUI.Town.cs | 163e1abeb1565b02e5309140e1248a0d07c69df81c0077e9b8a07983d545b963 |

수정 제안만 기록했다. 이 네 소스 파일, 실행 순서 설정, 모델/에셋을 변경하지 않았다.
