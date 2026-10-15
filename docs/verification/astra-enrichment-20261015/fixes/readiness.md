# Readiness — report25 반영

- 요청 모델/effort: gpt-6-astra / high, Fast/priority 요청. 실제 실행 모델·effort·서비스 등급은 독립 런타임 메타데이터가 없어 확인됐다고 주장하지 않는다.
- 작업 브랜치: codex/astra-enrichment-20261015, 확인한 HEAD/base: efdc1517f48ac8887e1fcf6843b6df44df6ebc3c.
- 변경 범위: ExpeditionReadiness.cs, 새 ReadinessRepairTests.cs, 이 기록만 작성했다. GameState/CampaignMigration/DungeonGrid 및 UI 파일은 수정하지 않았다.

## 동작 변경

`Assets/_Game/Scripts/Logic/Game/ExpeditionReadiness.cs:68-83`에 안내 계산만 추가했다.

- 살아 있는 출전 헌터의 hero.Statuses에서 남은 턴이 양수이고 데이터에 정의된 해로운 상태를 찾는다.
- 해로운지 여부는 기존 `GameFlow.IsBeneficial`의 반대 분류를 사용한다. 이로운 상태, 만료된 상태, 정의되지 않은 상태는 경고하지 않는다. 전투 불능 헌터는 기존 KO 안내를 사용한다.
- 한 헌터의 여러 상태는 이름을 정렬해 한 줄로 합친다: `헌터명: 상태 이상 (중독, 화상). 치료 후 출발을 권장합니다.` 실제 이름 순서는 ordinal 정렬이다.
- 기존 IssueLines/HasWarnings/SummaryText를 사용하므로 “준비 양호” 대신 기존 주의 요약과 색상이 표시된다. 새로운 화면, 컨트롤, 스타일은 추가하지 않았다.
- 상태를 제거하거나 턴을 줄이지 않는다. HP/MP, 재화, RNG, 목표 선택 및 기존 HP/MP 경고 조건도 바꾸지 않는다.
- `TownServices.Depart`의 해금된 층 판정과 `DungeonRun`의 출발 동작은 그대로다. 경고는 출발 제한이 아니다.

근거 재확인: 실제 독 함정은 `DungeonRun.cs:253-256` → `PartyStats.ApplyTrap`을 호출하며, 일반 귀환(`DungeonRun.cs:421-426`, `GameFlow.cs:136-151`)은 독을 치료하지 않는다. 살아 있는 헌터의 양수 상태는 `PartyStats.BuildCombatSpec`의 :333-334에서 다음 전투로 복사된다. 따라서 단순 독 ID 하드코딩 대신 기존 상태 분류와 지속 턴을 사용했다.

## 작성한 테스트 — 실행하지 않음

새 파일: `Tools/LogicTests/ReadinessRepairTests.cs`.

1. `PoisonTrapTownReturnWarnsWithoutLockingDepartureOrCleansing` (:29): 독립 데이터 fixture의 실제 X 칸을 밟는다. RNG 상태 1로 독을 재현하고 HP/MP는 기존 저자원 경고 기준보다 높음을 확인하도록 작성했다. 실제 귀환 메서드와 마을 진입 후 경고·헌터/상태명·조회 무변경을 확인하고, 해금된 출발을 허용하며 재출발과 전투 사양까지 독이 유지되는지 확인한다.
2. `HealthyTownPartyStillReceivesAllClearAndDeparts` (:81): 정상 파티의 준비 양호, 무변경 조회, 실제 던전 재진입을 확인한다.
3. `BenefitsAndExpiredStatusesStayClearWhileLiveAilmentsAreGrouped` (:98): 공격력 상승 및 만료 독/화상은 경고하지 않고, 살아 있는 독/화상 두 상태는 헌터별 한 줄로 표시하며 상태 데이터는 바뀌지 않는지 확인한다.

함정 fixture는 GameDB를 별도로 로드하므로 결합 러너의 TestMain.DB나 원본 JSON을 수정하지 않는다. `[LogicTest]` 자동 검색과 Tools/LogicTests/**/*.cs 포함 방식에 맞췄으며 TestMain/러너/프로젝트 파일 수정은 필요 없다.

## 정적 확인과 부모 실행 인계

- diff를 읽어 프로덕션 변경이 준비도 계산의 17줄 추가뿐임을 확인했다. 바이트 역치환이 원본과 일치해 그 외 소스 바이트와 줄바꿈은 보존됐다.
- 테스트가 참조하는 DungeonRun 생성자/Move/ReturnToTown, GameFlow.EnterTown, TownServices.Depart, PartyStats.BuildCombatSpec 및 Assert API를 현재 소스와 대조했다.
- 테스트·컴파일·Unity·빌드·패키지 resolve·브라우저·하위 에이전트·커밋은 실행하지 않았다. 공유 Temp/LogicTests 출력도 건드리지 않았다.
- **3개 테스트는 작성 상태이며 통과 결과가 아니다.** DungeonArrival 작업자와의 컴파일 출력 충돌을 피하기 위해 부모가 다른 작업 종료 후 기존 결합 논리 러너로 실행한다. 기존 ExpeditionReadinessTests도 함께 수용 검증한다.

| 파일 | SHA-256 |
|---|---|
| ExpeditionReadiness.cs 수정 전 | 12cf5abe28ecd460ee069420d22ad2b8588a5256bb3113f5377263f27e8ff4f4 |
| ExpeditionReadiness.cs 수정 후 | 9469b374b0a8e0e0f9cb59409d94045c226bc697521b95c9200f48bbc21a20ae |
| ReadinessRepairTests.cs | de50b0a013e707bc58ffe6d0dfd02b70570002b30f42353a00e51c6d71770f9f |
