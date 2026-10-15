**정상 반복 재생에서 메시·머티리얼이 매번 복제되는 경로는 발견하지 못했습니다.** 남은 위험은 다음 두 가지입니다.

1. **P2 — VFX 생성 실패 시 미등록 객체가 남습니다.**  
   [VfxLibrary.cs:271](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:271)의 `Build()`는 루트와 레이어를 먼저 생성하고, 모두 성공한 뒤 `_effects`에 등록합니다. 도중에 `MaterialFor()` 또는 `MeshFor()`가 예외를 던지면 부분 생성된 루트가 정리되지 않습니다. 같은 효과를 다시 시도하면 비활성 객체가 추가로 쌓이며, `StopAll()`도 미등록 객체에는 접근하지 못합니다. 라이브러리 객체가 파괴될 때까지 남는 조건부 누수입니다.  
   **다음 조치:** 레이어 생성 구간에 예외 정리를 추가해 실패한 루트를 파괴한 뒤 예외를 다시 전달하십시오. 현재 리소스가 실제로 실패한다는 증거는 없습니다.

2. **P3 — 동시 재생량 증가가 스킬 실행 중 할당과 장기 풀 보유로 이어집니다.**  
   [VfxLibrary.cs:213](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:213)은 빈 슬롯이 없으면 즉시 `Build()`를 실행합니다. [같은 파일:743](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:743)의 반환은 비활성화만 수행하며 축소 정책은 없습니다. 확인한 전투 경로에는 `Prewarm()` 호출도 없습니다. 특히 `arcana_nova`는 18개 레이어이며, 종료 후 레이어 수명만큼 추가 배출 시간을 두므로 연속 사용이 겹치면 새 객체가 필요할 수 있습니다. 전투 종료도 [BattleView.cs:1798](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:1798)에서 핸들을 중지할 뿐 풀을 해제하지 않습니다.  
   **다음 조치:** 부모의 런타임 검증에서 반복 사용 전후 풀 크기·GC 할당·프레임 시간을 측정하고, 확인된 동시 사용량에 맞춰 사전 생성 또는 유휴 풀 축소를 적용하십시오. 이는 최대 사용량을 유지하는 캐시이며, 사용 횟수에 비례하는 무조건적 누수는 아닙니다.

기존 방어는 확인했습니다. `sharedMesh/sharedMaterial` 사용, 머티리얼 캐시, 생성 메시 4종과 캐시 머티리얼의 `OnDestroy()` 정리, 반환 시 파티클·트레일 초기화, 세대 번호 기반 핸들 보호가 있습니다.

**검토 완료 범위:** 수명주기·메시 소유권·머티리얼 할당의 정적 검토. 파일 수정, Unity 조작, 테스트 실행은 하지 않았습니다. 기존 259개 테스트 결과를 이번 런타임 검증으로 재해석하지 않았으며, 실제 메모리 증가나 프레임 지연은 미측정입니다.