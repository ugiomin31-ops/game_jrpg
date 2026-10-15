**P2 문제 1건 확인했습니다.** 읽기 전용 검토이며 파일 수정·테스트·Unity 실행은 하지 않았습니다.

1. **보스 페이즈 Cast 종료 대기가 전투 배속과 불일치합니다.**  
   [BattleView.cs:471](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:471)에서 `Time.time`으로 시작 시각을 기록하고, 480행에서 클립 길이에서 실제 경과 시간을 뺍니다. 그러나 남은 시간을 기다리는 [Wait:1685](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1685)는 `unscaledDeltaTime × BattleSpeed`를 사용합니다. 애니메이션에도 배속이 적용되므로 서로 다른 시간 단위를 섞습니다.  
   예를 들어 **2초 Cast·2배속·대사 없음**이면 애니메이션은 약 1초에 끝나지만 페이즈 대기는 약 1.275초가 됩니다(프레임 오차 제외).  
   **다음 조치:** `Time.time` 차감 대신 일시정지·히트스톱을 제외한 전투 시간으로 경과량을 누적하거나, 실제 Cast 재생 종료 상태를 기다리도록 통일하십시오. 이후 부모가 1배속/2배속에서 확인하면 됩니다.

그 외 요청 범위에서는 **확정 가능한 매핑 누락을 찾지 못했습니다.**

- **Channel/Rally/Throw:** [DefaultContact:910](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:910)의 `.548 / .375 / .48`은 [motion_takes.py:145](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Blender/hunters_tripo/motion_takes.py:145)의 `(18−1)/(32−1)`, `(13−1)/(33−1)`, `(13−1)/(26−1)`과 일치합니다. 해당 FBX 메타의 구간도 각각 `0–31 / 0–32 / 0–25`입니다.
- **몬스터 Cast:** [ArtLibrary.cs:201](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:201)에 sprout `.50`, mushroom `.27`, pixie `.42`, forest_guardian `.37`이 이미 있으며, `ModelTimingLayer → ContactFraction → contactTime`으로 연결됩니다. 이 네 종을 매핑 누락으로 보고할 근거는 없습니다.

체크리스트: 접촉 비율 대조 완료, 시간 단위 검토 완료, 몬스터 매핑 연결 확인 완료. 현재 브랜치는 `claude/motion-polish-pr9`입니다. 실제 손·발 접촉 및 VFX 동기화는 이번 검토에서 검증하지 않았고, 기존 259개 테스트도 재실행하지 않았습니다. 요청된 Astra High·priority의 실제 라우팅은 이 세션에서 확인할 수 없습니다.