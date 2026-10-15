읽기 전용 검토 결과, **P2 문제 2건**을 확인했습니다. 파일 변경·Unity 실행·테스트는 하지 않았습니다.

1. **P2 — 다단 주문의 두 번째 이후 발사가 캐스트 동작과 연결되지 않습니다.**  
   [BattleView.cs:1163](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1163)의 `PrepareHit`는 콤보 또는 `Attack`만 다시 재생하고, 나머지는 바로 `Shoot`합니다. 반면 주문 경로는 `Spell`/`Channel`을 선택하고 빈 콤보 상태로 반환합니다([MotionStyles.cs:246](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Battle/MotionStyles.cs:246)).  
   현재 데이터의 `sk_chain_spark`, `sk_e_crystal_spike`가 해당합니다. 최초 발사는 접촉 시점에 맞지만, 후속 발사는 이전 동작의 회복 구간이나 Idle에서 발생할 수 있습니다.  
   **다음 조치:** 후속 주문 발사에도 해당 클립을 release 직전부터 재생하고 `Contact`까지 기다리는 경로를 연결하십시오.

2. **P2 — 무작위 다단 공격의 사망 후 재지정 대상이 최초 투사체 목적지에 반영되지 않습니다.**  
   [BattleEngine.cs:986](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:986)는 시작 이벤트에 대상 목록을 복사합니다. 이후 사망 대상은 [BattleEngine.cs:1076](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1076)에서 다른 생존 대상으로 바꾸지만 시작 이벤트의 복사본은 그대로입니다.  
   `AreaVfx`가 있는 공격은 타격별 투사체를 사용하지 않고 그 복사본에만 일괄 발사합니다([BattleView.cs:795](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:795)). `sk_m_prism`, `ult_starfall_volley`에서 초기 대상 A가 첫 타격으로 죽으면, 후속 피해·충돌 효과는 B에 발생하면서 해당 투사체는 A로만 날아가는 불일치가 가능합니다.  
   **다음 조치:** 해당 무작위 다단 경로의 목적지를 실제 `DamageEvent`/`MissEvent` 대상에 연결하고 광역 효과는 별도로 유지하십시오.

**사망 후 피해 처리 자체에서는 결함을 확인하지 못했습니다.** 엔진은 매 타격 전 생존 여부를 확인하고 죽으면 중단합니다([BattleEngine.cs:1089](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1089)). 투사체 도착 콜백이 피해를 재적용하는 구조도 아닙니다.

검토 항목인 최초 release, 비행 대기, 사망·재지정 경로 대조는 마쳤습니다. 위 결과는 현재 코드·데이터 근거이며 화면 재현이나 새 런타임 검증 결과가 아닙니다. 요청된 Astra High/priority 라우팅의 실제 적용 여부는 이 작업자가 확인할 수 없습니다.