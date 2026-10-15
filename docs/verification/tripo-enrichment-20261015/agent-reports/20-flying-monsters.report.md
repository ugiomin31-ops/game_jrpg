**P2 — 비행 적의 이펙트 기준점이 실제 애니메이션 위치를 따라가지 않습니다.**

- [RiglessFlyerAnimator.cs:301](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/RiglessFlyerAnimator.cs:301)는 자식 `Visual`만 이동합니다. 공격 접촉 시에는 모델 높이의 30%만큼 전진하고, Cast 방출 시에는 22%만큼 상승합니다(56·64행).
- 그러나 [CharacterModel.cs:133](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:133)의 `CenterPoint`와 139행의 무기 소켓 없는 `MuzzlePoint`는 **부모 위치와 고정 Height만 사용**합니다. `Visual`의 이동·회전을 반영하지 않습니다.
- 이 값은 실제 [BattleView.cs:943](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:943)의 투사체 출발점과 1597–1601행의 피격 이펙트 위치에 사용됩니다. 따라서 비행 몸체가 움직여도 이펙트 기준점은 이전 위치에 남는 코드 경로입니다.

**다음 조치:** 비행형의 몸체 로컬 기준점을 저장하고 현재 `Visual.TransformPoint`로 변환하여 중심점·발사점에 사용하십시오. 접근 거리 계산에 쓰이는 기존 rest-pose `Height/Radius`는 유지해야 합니다.

허용 목록과 현재 에셋 연결에서는 추가 결함을 확인하지 못했습니다.

- [ArtLibrary.cs:120](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:120): 모델 ID, 정확한 적 리소스 경로, Idle 부재를 함께 검사합니다. 목록은 `bat/killer_bee/elite_bat`입니다.
- 세 모델 모두 FBX와 `FLYER` 표식이 존재하며, 현재 메타 설정은 `importAnimation: 0`, `animationType: 0`입니다.
- 설치 기록에는 세 모델 모두 0.30m 공중 오프셋을 메시에 반영했다고 명시되어 있습니다. 따라서 공중 오프셋 누락이나 리그 없는 모델 지원 부재를 현재 결함으로 보고하지 않습니다.

검토 체크: 허용 목록·임포트 설정·애니메이션 이동·이펙트 소비 경로 확인 완료. **파일 변경, 테스트, Unity 실행, 화면 검증은 하지 않았습니다.** 발견 사항은 현재 코드의 위치 계산 불일치이며, 실제 화면에서의 오차 크기는 미측정입니다. 요청된 Astra High/priority 라우팅은 이 세션에서 독립적으로 확인하지 못했습니다.