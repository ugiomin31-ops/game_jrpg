프리플라이트 판정: **단일 파일럿 준비는 진행 가능하지만, 후속 유료 배치 확대 전 아래 위험을 해소해야 합니다.** 파일 변경·테스트·Unity 실행·브라우저 접근은 하지 않았습니다.

1. **P1 — 보조 검증 코드의 인자 순서 오류**
   [TripoEnrichmentAcceptance.eval.cs:39](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/TripoEnrichmentAcceptance.eval.cs:39)의 선언은 `Check(string, bool, …)`인데, 173–174행은 `(bool, string)`으로 호출합니다. 정적 검토상 컴파일 오류입니다.
   **다음 조치:** 담당 쓰기 권한자에게 두 호출의 순서 수정을 전달하고, 부모가 실행 가능 여부를 확인해야 합니다.

2. **P1 — 파일럿 확대 조건이 너무 이릅니다**
   [계획:21](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/plan/2026-10-15-tripo-enrichment.md:21)은 FBX 내보내기까지를 확대 전 조건으로 명시합니다. Blender 변형 검증과 실제 게임 비교는 별도 후속 항목입니다.
   **다음 조치:** 확대 조건을 **원본 보존 → Blender 실제 변형 → 게임 연결 → 실제 플레이 검증 → 부모 승인**까지 묶으십시오. 정적 소품 통과로 캐릭터 리깅까지 검증됐다고 간주하면 안 됩니다.

3. **P1 — 스킨 검사가 부분 실패를 놓칠 수 있습니다**
   [검증 코드:113](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/TripoEnrichmentAcceptance.eval.cs:113)은 가중치가 있는 정점이 하나만 있어도 해당 조건을 통과합니다. 242–243행은 모든 스킨 중 최대 정점 이동량만 검사하므로 일부 메시만 움직여도 변형 조건이 통과할 수 있습니다.
   **다음 조치:** 메시별 가중치 적용 범위와 주요 관절 포즈의 실제 변형을 Blender에서 확인하고 기록하십시오. 이 보조 검사의 성공은 Blender 확인을 대체하지 못합니다.

4. **P1 — dirty 기준선은 식별되지만 복구 가능성은 별도입니다**
   [계획:15](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/plan/2026-10-15-tripo-enrichment.md:15)에 대응하는 패치, 상태 261개, 해시 393개 기록은 실제 존재합니다. 다만 해시는 복구용 사본이 아니며, 이 확인만으로 untracked·바이너리 파일 전체의 복구 가능성을 보장할 수 없습니다.
   **다음 조치:** 교체 대상별 기존 바이트와 `.meta`를 별도 보존하고, 병렬 작업의 쓰기 경로를 분리하십시오. 적용 직전·직후 해시 비교에서 승인된 변경만 허용해야 합니다.

5. **P2 — 출처·크레딧 기록을 연결하는 필드가 부족합니다**
   [계획:22](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/plan/2026-10-15-tripo-enrichment.md:22)는 비용·잔액·원본 보존을 요구하지만 통합 기록 형식은 정하지 않습니다. 9·51행의 브라우저 미해결 문구도 19·53행의 승인 기록과 충돌합니다.
   **다음 조치:** 자산별 sidecar에 선택 후보·정확한 프롬프트·모델/effort·사이트·Studio 작업 ID·단계별 표시 비용/전후 잔액·원본 해시·게임 경로를 연결하십시오. 유료 조작과 잔액 기록은 부모가 단독 소유해야 합니다.

6. **P2 — 로드 성공은 게임 내 사용 증거가 아닙니다**
   [검증 코드:194](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/TripoEnrichmentAcceptance.eval.cs:194)는 자산을 직접 로드·생성합니다. 실제 게임에서 참조하지 않는 자산도 이 방식으로 검사할 수 있습니다. [계획:31](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/plan/2026-10-15-tripo-enrichment.md:31)의 미사용 자산 제외 원칙에는 별도 증거가 필요합니다.
   **다음 조치:** 실제 적/스킬/상호작용 ID, 연결 설정, 재현 가능한 플레이 경로를 기록하고 그 경로에서 관찰된 자산만 납품 수에 포함하십시오.

요청한 다섯 위험 영역의 문서·코드 검토는 끝났습니다. 이전 259개 테스트는 재실행하지 않았으며 새 런타임 완료 근거로 사용하지 않았습니다. Astra High·fast/priority는 요청 사항으로만 확인했으며 실제 실행 라우팅은 검증하지 못했습니다.