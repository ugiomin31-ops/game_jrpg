읽기 전용 검토에서 **전용 클립 우선순위가 전투 선택 단계에서 깨지는 경로 2건**을 확인했습니다. 파일 수정·테스트·Unity 실행은 하지 않았습니다.

1. **P2 — 도현의 고유 연속기 두 번째 타격이 공통 동작으로 교체됩니다.**  
   `sig_dohyun`은 2회 타격이고, 첫 동작은 전용 `h_dohyun/Skill.fbx`를 유지합니다. 그러나 일반 근접 동작에서 만든 `_plan.Combo`가 남아 있어 두 번째 타격에서는 공통 `Thrust` 또는 `Slash`를 재생합니다. 전용 연속기를 유지한다는 코드 주석과 선택 동작이 다릅니다. 실제 어느 포즈에서 끊기는지는 런타임 확인이 필요합니다.  
   근거: [BattleView.Moves.cs:117](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.Moves.cs:117), [ComboWave:564](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.Moves.cs:564), [BattleView.cs:1164](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1164).  
   **최소 수정:** `PlanHeroTake`에서 `IsSignature(e) && actor.Model.HasClassClip("Skill")`로 전용 `Skill`을 보존할 때 `_plan.Combo`를 비웁니다. 전용 클립의 두 번째 접촉 시점과 피해 표시 간 동기화는 별도 확인해야 합니다.

2. **P2 — 마법사 광역 주문용 직업 `Skill` 선택이 공통 `Channel`로 덮입니다.**  
   `BattleView.cs:709–711`은 자체 `Cast`가 없고 직업 `Skill`이 있는 마법사의 광역 주문에 `Skill`을 선택합니다. 이어지는 `PlanHeroTake`는 비접근 `Skill`에서 계획된 `Channel`을 우선합니다. 두 클립 모두 실제 설치되어 있으므로 해당 경로에서 직업 클립이 우회됩니다. **마법사 `Skill` 전체가 미사용이라는 의미는 아닙니다**—단일 대상 고유기 등에는 도달 경로가 있습니다.  
   근거: [BattleView.cs:709](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:709), [BattleView.Moves.cs:118](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.Moves.cs:118), [MotionStyles.cs:247](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Battle/MotionStyles.cs:247).  
   **최소 수정:** 비접근 `Skill` 분기에서 적 대상 공격이고 `HasClassClip("Skill")`이면 기존 `clip`을 반환하도록 먼저 처리합니다. 아군 지원용 `Kneel`·`Rally` 선택은 유지합니다.

실제 설치된 영웅 전용 클립은 다음 **12개**입니다. FBX와 `.meta`의 클립명이 일치합니다.

| 영웅 | 전용 클립 |
|---|---|
| 도현 | Attack, Skill |
| 지호 | BattleIdle, Victory |
| 민준 | Attack, BattleIdle, Cast |
| 서아 | Attack |
| 유나 | Attack, BattleIdle, Cast, Victory |

[ArtLibrary.cs:167](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:167)의 공통 → 직업 → 영웅 덮어쓰기와 클립별 타이밍 소유자 전달은 연결되어 있습니다. 이는 클립 선택 계층이며, 상·하체 마스크를 합성하는 Animator 레이어 구조는 아닙니다.

**다음 조치:** 부모 세션에서 `BattleView.Moves.cs`의 위 두 분기만 수정하고, 도현 고유기와 서아 광역 주문을 대상으로 재생 클립·접촉 시점을 확인하십시오. 이번 검토는 현재 파일의 정적 연결 증거에 한정하며, 기존 259개 테스트 결과를 새 변경의 검증으로 사용하지 않았습니다.