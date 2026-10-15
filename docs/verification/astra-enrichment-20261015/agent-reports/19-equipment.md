# 19-equipment — bounded read-only audit

- 요청 모델: `gpt-6-astra`; 요청 reasoning effort: `high`; 요청 service tier: Fast/priority.
- 관측 한계: 이 세션에서 실제 모델 ID/effort/service-tier를 독립적으로 증명하는 런타임 메타데이터는 제공되지 않았다. 요청값을 실행 확인값으로 간주하지 않는다. 모델·설정 변경 및 하위 에이전트 호출 없음.
- 확인 checkout: `codex/astra-enrichment-20261015`, HEAD `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c` (요청 base 일치).
- 범위: AutoEquip.cs, PartyStats.cs, equipment.json 및 직접 연결된 Enhancement.cs, GameState.cs 슬롯 정의, heroes.json의 해당 캐릭터 값, GameUI.Party.cs의 호출/비교 경로. 보고서 01..07 파일명 범위에서 장비 관련 키워드를 검색했으며 중복 항목은 발견하지 못했다.
- 방법: 소스/데이터 정적 추적만 수행. 아래 재현 절차는 실행하지 않았다. 테스트·빌드·Unity·브라우저·네트워크·인증정보 접근 없음. 이 보고서 외 파일 변경 없음.

## 1. [P2] 파티 자동 장비가 한 후속 멤버에게 같은 슬롯 후보들을 모두 예약하여 유효한 업그레이드를 남김

**위치:** `Assets/_Game/Scripts/Logic/Game/AutoEquip.cs:188-189`, `:198-207` (예약 판정), `:93-104` (앞선 멤버 재방문 없음).

**재현:** 마을에서 같은 레벨(예: 20), 기본 warrior 직업, 강화/씨앗 없는 `h_dohyun`을 `h_minjun`보다 앞에 배치한다. 도현은 `sword_iron`, 민준은 `sword_bronze`를 장착하고, 가방에는 `sword_knight`와 `sword_runic`을 각각 1개 둔다. 다른 슬롯 업그레이드 후보 없이 ‘파티 전체 최강 장비’를 한 번 승인한다. 모두 실제 데이터의 제한 없는 warrior 무기이며 상점에서 획득 가능하다 (`equipment.json:3824-3851`, `:3655-3682`, `:3854-3881`, `:3920-3951`).

**소스상 결과:** 민준의 현재 무기가 더 약하므로 두 후보 모두 민준의 점수 증가가 더 크다. `WantedByLater`는 후보별로 독립적으로 민준에게 예약하여 도현의 후보에서 두 무기를 모두 제외한다. 이후 민준은 더 높은 점수의 `sword_runic` 하나만 선택한다. 도현은 `sword_iron`을 유지하고 명백한 업그레이드인 `sword_knight`는 가방에 남는다. 실제 UI 진입은 `Assets/_Game/Scripts/UI/Screens/GameUI.Party.cs:178-184`이다.

**영향:** 재고 부족이나 중복 소비 없이 가능한 업그레이드인데도 한 번의 전체 최강 장비 작업이 놓친다. 같은 버튼을 다시 누르면 도현이 남은 장비로 올라가므로, 사용자에게 표시하는 일괄 최강 조합이 첫 적용에서 완성되지 않는다. 이는 전역 최적화 요구가 아니라 후속 멤버가 최종적으로 쓰지 않은 예약을 회수하지 않는 문제다.

## 2. [P2] 효과 전용 장신구 해제를 비교 화면이 ‘동일 능력’으로 표시하고 손실 효과를 생략함

**위치:** `Assets/_Game/Scripts/UI/Screens/GameUI.Party.cs:283-291`, `:300-312`; 해제 확인 진입 `:152`.

**재현:** 상점 tier 2에서 구매 가능한 `acc_exp_charm`을 장착한 뒤 장비 메뉴의 ‘해제’를 선택해 확인 화면을 읽는다 (`Assets/_Game/Resources/Data/equipment.json:468-494`). 이 장신구는 정수 능력치/명중/회피/치명타가 모두 0이고 저항/면역도 없으며, 경험치 +30%만 가진다. `acc_gold_charm`도 보상금 +25%로 같은 문제가 발생한다 (`equipment.json:610-636`).

**소스상 결과:** `PartyStats.EffectiveStats`는 경험치/보상금 효과를 정확히 반환한다 (`Assets/_Game/Scripts/Logic/Game/PartyStats.cs:203-204`). 그러나 `GearVerdict`의 비교 대상에는 ExpBonus/GoldBonus가 없어 해제를 ‘동일 능력’으로 판정하고, `GearComparison`에도 해당 효과의 전후 값이 없다. 해제 확인은 이 비교 문자열만 표시하므로 기존 장신구 효과가 사라진다는 설명도 없다. 실제 효과는 승리 보상에서 사용된다 (`PartyStats.cs:487-492`).

**영향:** 플레이어가 효과 손실이 없는 해제로 오인할 수 있고, 이후 받는 경험치 또는 보상금이 감소한다. 교체 후보의 설명을 따로 보여주는 경로와 달리, 해제 경로에는 효과 설명으로 보완할 기회도 없다.

## Acceptance

- [x] 요청 브랜치/base 확인.
- [x] 비교·실효 능력치·중복 장비 수량·효과의 직접 연결 경로 검토.
- [x] 도달 가능한 실제 데이터 사례 2개 이하, 경로/라인/재현/영향 기록.
- [x] 수량 이동은 Equip의 가방 1개 차감/기존 장비 1개 반환, 파티 계획의 가방 사본 갱신을 확인했으며 별도의 중복 생성 결함은 보고하지 않음. 강화가 동일 ID의 모든 복사본에 공유되는 것은 Enhancement.cs에 명시된 설계임.
- [x] 실행 검증을 하지 않았음을 명시하고 지정 보고서만 작성. 게임 수정 및 통합 판단은 coordinator에 남김.
