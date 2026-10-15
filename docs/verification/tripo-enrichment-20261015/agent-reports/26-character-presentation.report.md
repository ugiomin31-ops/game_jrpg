**P2 — Humanoid 무기의 그립 보정이 발사체 시작 위치에 반영되지 않습니다.**

- [CharacterModel.cs:192](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:192)는 손목에서 손가락 방향으로 `0.6 × 손 길이`, 손바닥 바깥으로 `0.22 × 손 길이`만큼 보정한 그립 위치를 계산합니다. 227–229행에서 무기에 이 위치와 회전을 적용합니다.
- 그러나 [CharacterModel.cs:136](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:136)의 `MuzzlePoint()`는 장착 무기를 참조하지 않고 `bone.position`을 반환합니다. Humanoid에서는 150–151행에 따라 이 본이 손 본이므로, 보정된 무기 원점과 발사 시작점이 서로 다릅니다.
- [BattleView.cs:943](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:943)는 이 좌표를 그대로 발사체에 전달합니다. 따라서 해당 Humanoid 경로에서 공격·시전 중 발사체가 무기 그립 대신 손목 위치에서 출발합니다. 현재 `h_seoa.fbx.meta`에는 Humanoid 설정과 손·손가락 매핑이 존재하므로, 지원하지 않는 가상 리그만의 문제는 아닙니다.

**정확한 다음 조치:** `MuzzlePoint()`가 장착 무기의 명시적인 발사 앵커를 우선 사용하고, 앵커가 없으면 장착 무기 원점, 무기가 없으면 기존 본/가슴 위치를 사용하도록 수정하십시오. 이후 부모 세션에서 활·지팡이의 발사 프레임을 확인해야 합니다.

**검토 한계:** 크기 보정과 방향 계산도 읽었지만, 현재 에셋에서 잘못된 크기·방향이 발생한다고 확정할 근거는 확보하지 못했습니다. 위 발견은 현재 코드의 좌표 불일치이며 화면상 심각도는 미검증입니다. 파일 수정, 테스트, Unity 실행, 브라우저 사용, 자식 작업자 생성은 하지 않았습니다. 요청된 Astra High·fast/priority의 실제 라우팅은 이 세션에서 확인할 수 없습니다.