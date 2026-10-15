읽기 전용으로 수용 순서를 작성했습니다. **Unity 실행·캡처·테스트·파일 수정은 하지 않았습니다.** 요청 라우팅은 Astra High/priority이며 실제 라우팅은 이 작업에서 확인하지 못했습니다.

우선순위별 확인 사항:

- **P1 — 신규 자산 하네스 실행 전 보완 필요.** [TripoEnrichmentAcceptance.eval.cs:39](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/TripoEnrichmentAcceptance.eval.cs:39)의 `Check(string, bool, …)` 선언과 173·174행 호출의 인수 순서가 반대입니다. 27행 manifest도 비어 있습니다. 담당 워커가 호출 순서와 실제 자산 경로·take 목록을 준비해야 합니다.
- **P1 — 기존 전투 캡처의 대상 제한.** [TripoBattleAcceptance.eval.cs:146](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/TripoBattleAcceptance.eval.cs:146)은 고정 영웅 4명과 슬라임 2마리를 사용합니다. 신규 적·캐릭터가 해당 슬롯에 연결되었다는 확인 없이는 신규 자산 증거가 아닙니다.
- **P2 — 정적 검사와 실제 시각 증거 구분.** 신규 자산 하네스는 512×512 개별 렌더를 만들며, [TripoVfxTimingChecks.eval.cs:4](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/TripoVfxTimingChecks.eval.cs:4)는 실제 잔상 수명 전환·정지 모습을 증명하지 않는다고 명시합니다.

부모가 수행할 순서는 다음과 같습니다.

1. **대상 확정:** 신규 적·캐릭터·소품의 Resources 경로, 실제 게임 연결 위치, 필수 모션 take, 연결된 VFX/스킬을 기록합니다. 선언만 있고 실제 게임에서 등장하지 않는 자산은 통과시키지 않습니다.

2. **개별 자산 검사:** 위 보완 후 초기화된 Play Mode에서 실행합니다.
   ```text
   unity command eval_file --file Tools/TripoEnrichmentAcceptance.eval.cs
   ```
   반환된 디렉터리의 `DONE`을 15–25초 간격으로 확인합니다. `checks.json`에서 로드·삼각형 예산·재질·가중치·take·메시 변형을 확인하고 생성 PNG를 직접 검토합니다. 이는 두 해상도 게임 화면 검증의 사전 단계입니다.

3. **VFX 보조 검사:** 활성 VFX가 없는 idle Play Mode에서 실행합니다.
   ```text
   unity command eval_file --file Tools/TripoVfxTimingChecks.eval.cs
   ```
   `TRAIL_TIMING_PASS`를 보관하되 시각 통과로 처리하지 않습니다.

4. **기존 전투 화면 기준 확보:** 다른 QA/ReviewBoot가 없는 새 Play 세션의 Title에서 실행합니다.
   ```text
   unity command eval_file --file Tools/TripoBattleAcceptance.eval.cs
   ```
   [192행](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/TripoBattleAcceptance.eval.cs:192)부터 생성하는 `battle-1280x720`, `battle-915x412`, `overview-1280x720`, `overview-915x412` PNG 네 장과 `checks.json`을 확인합니다. 종료 후 일반 플레이 전에 **Stop Play**가 필요합니다.

5. **실제 신규 콘텐츠 확인:** 격리된 QA 플레이에서 **1280×720 → 915×412** 순서로 같은 장면·행동을 반복하고, 해상도별 아래 증거를 남깁니다.

   | 대상 | 실제 입력과 관찰 | 통과 조건 |
   |---|---|---|
   | 신규 적 | 등장→대기→공격→피격→사망 | 올바른 자산, 스케일·접지·재질 정상, 메시 변형, HUD에 몸체 가림 없음 |
   | 캐릭터 동작 | 대기→공격/스킬→복귀, 취소 후 재선택 | 필수 take 재생, 의도치 않은 T포즈·순간이동·루프 끊김 없음 |
   | VFX | 실제 스킬 발동, 1×/2×, 일시정지·재개, 반복 발동 | 발생점·타격 시점 일치, 잔상·효과 잔류 없음, UI와 대상 식별 유지 |
   | 소품 | 실제 배치 장소에서 접근·카메라 이동 | 크기·접지·재질 정상, 깜빡임·부당한 가림 없음; 상호작용 소품이면 실제 작동 |

   모션/VFX는 정지 이미지 외에 시작·타격·복귀의 연속 증거가 필요합니다. 915×412에서는 3개 선택지와 페이지 이동, 행동/비용 헤더, 하단 파티, 터치 영역도 함께 확인합니다.

6. **최종 판정:** 현재 실행의 콘솔/Player 로그, 실제 해상도, 자산 ID, 캡처를 묶어 부모가 직접 승인합니다. 네이티브 플레이어 캡처에 기존 [Pr6NativeCapture.py:25](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/Pr6NativeCapture.py:25)를 사용한다면 `--compact`/`--position`은 목표 해상도를 보장하지 않으므로 사용하지 말고 반환된 `clientBounds`를 확인합니다.

**정확한 다음 조치:** 부모가 신규 자산 manifest를 확정하고 지정 Tools 담당 워커에게 두 `Check` 호출 수정을 전달한 뒤, 위 순서로 실행합니다. 이전 259개 테스트 결과는 재실행하지 않았으며 신규 런타임 수용 근거로 사용하지 않았습니다.