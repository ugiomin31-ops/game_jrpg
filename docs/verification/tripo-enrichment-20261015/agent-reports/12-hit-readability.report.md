읽기 전용 검토 결과, **숫자 배치 결함 1건과 다단 VFX 검증 필요 항목 2건**을 확인했습니다.

1. **P2 — 살아 있는 피해 숫자의 배치 공간을 재사용합니다.**  
   [UINumberPopup.cs:176](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/UI/Kit/UINumberPopup.cs:176)는 최근 0.35초 이내 팝업 개수로 수직 위치를 정하지만, 숫자는 1.25초, 치명타는 1.45초 유지됩니다. 같은 위치에 0.2초 간격으로 세 번 생성하면 두 번째·세 번째가 모두 `48` 오프셋을 받습니다. 기존 숫자가 여전히 보이는 동안 같은 배치 공간이 재사용되며, 무작위 가로 이동 ±16만으로 분리를 보장하지 못합니다.  
   **다음 조치:** 활성 팝업에 실제 점유 슬롯을 부여하고 소멸 시 반환하도록 최소 수정합니다. 동일 대상 5·7타에서 숫자와 합계 표시의 겹침을 확인해야 합니다.

2. **P3 — 치명타는 타격마다 전체 화면 플래시를 재시작합니다.**  
   [BattleView.cs:1240](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1240)에서 일반 스킬 플래시는 `_flashed`로 제한하지만 치명타는 제한하지 않습니다. 다단 치명타에서 흰색 플래시가 반복되는 경로는 확인되며, 실제 가독성 저하는 미측정입니다.  
   **다음 조치:** 부모가 5·7타 연속 치명타를 1×/2×로 확인한 뒤, 필요하면 화면 플래시를 행동당 한 번으로 제한하고 개별 타격 강조는 유지합니다.

3. **P3 — 중첩 효과 전체의 밝기 상한은 없습니다.**  
   [VfxLibrary.cs:639](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:639)의 밝기 감쇠는 개별 레이어의 화면 점유율을 사용합니다. [BattleView.cs:1233](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1233)는 매 타격마다 별도 효과를 생성하므로 작은 가산 레이어들의 누적 밝기는 이 계산에 포함되지 않습니다. **화이트아웃 발생을 확정한 것은 아닙니다.**  
   **다음 조치:** 동일 대상 다단 공격에서 몸체 윤곽과 숫자가 유지되는지 먼저 확인하고, 실패할 경우에만 대상별 중첩 감쇠를 적용합니다.

이전 콤보의 **40ms 조기 타격 문제는 현재 [BattleView.cs:1165](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1165)의 접촉 잔여시간 계산으로 수정되어 재보고하지 않았습니다.** 직전 보고서의 259/259 및 VFX 검증 결과는 기존 증거로 존중했습니다.

수락 체크: 현재 코드·이전 보고서 대조 완료, 파일 변경 없음, 자식 실행 없음, 테스트·Unity·브라우저 실행 없음. 새 런타임 통과를 주장하지 않습니다. 요청한 Astra/high/priority의 실제 서버 라우팅은 이 작업자에서 확인할 수 없습니다.