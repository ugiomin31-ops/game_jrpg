읽기 전용 점검 결과, **개찰구는 연결되어 있고, `foe_marker`는 현재 런타임 생성 경로에서 사용되지 않습니다.** 신규 런타임 결함으로 확정할 스케일 오류는 발견하지 못했습니다.

1. **P2 — `foe_marker` 자산과 실제 표시 경로 불일치**
   - [AbyssProjectSetup.cs:116](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssProjectSetup.cs:116)는 `foe_marker`를 필수 자산으로 검사합니다.
   - 실제 FOE 표시는 [DungeonWorld.cs:151](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:151)에서 별도 생성하며, 171·194·205행에서 자체 quad와 ring/beacon을 사용합니다. 따라서 지하철 `foe_marker.fbx`를 개선해도 이 표시에는 반영되지 않습니다.
   - **다음 조치:** 부모가 해당 FBX를 실제 표시로 연결할지, 보관 자산으로 명시하고 필수 검사에서 제외할지 결정해야 합니다. 자동 삭제 대상은 아닙니다.

2. **P3 — 개찰구 크기 편차는 존재하지만 미사용·눕힘 문제는 아님**
   - 원래 `_ticket_gate()`는 [subway.py:438](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Blender/environment/hunter_kits/subway.py:438)에서 `decor_1`로 매핑됩니다. 현재 런타임도 [DungeonWorld.cs:309](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:309)의 `decor_1..6` 선택 경로로 해당 리소스를 사용합니다.
   - 설치 FBX를 직접 읽은 치수는 **폭 1.3854 × 높이 1.0600 × 깊이 0.9299m**입니다. 로컬 회전 0, 스케일 1이며, 과거 눕힘 문제를 현재 문제로 재보고할 근거가 없습니다.
   - [설치 기록:55](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/terrain/subway_ticket_gate/candidates/prompts.md:55)의 기존 모델 대비 폭 −20.4%, 깊이 +14.2% 편차는 남아 있습니다. 공통 배치는 크기를 조정하지 않고 위치만 보정합니다.
   - **다음 조치:** 부모의 Unity 검증에서 회전된 장식의 통로 여유를 확인하십시오. 수치 편차만으로 재생성이나 스케일 변경을 권하지 않습니다.

3. **P3 — 이 체크아웃에 개찰구 원본 파일 누락**
   - 위 설치 기록이 가리키는 `candidate_A.png`와 원본 Tripo FBX 모두 `Test-Path=False`입니다. `subway_ticket_gate`에는 후보 설명 문서만 확인되었습니다.
   - **다음 조치:** 원본 보관 위치에서 정확한 파일을 복원하고 설치 자산과 대응 관계를 확인해야 합니다. 추가 유료 생성은 필요 근거가 없습니다.

추가로 FBX 직접 측정값은 `decor_5` **1.3000 × 0.8895 × 1.8402m**, `foe_marker` **2.2000 × 0.6156 × 2.2000m**입니다. 후자의 과거 높이 `0.246m`는 이후 균일 스케일 복원 기록으로 대체되었으므로 현재값으로 사용하면 안 됩니다.

확인 항목: 소스 연결·배치 코드·FBX 치수·원본 존재 여부 완료. 파일 수정, 하위 작업자, Unity 실행, 테스트, 화면 검증은 수행하지 않았습니다. 요청 모델은 Astra High/priority이나 실제 라우팅은 이 작업에서 검증하지 못했습니다.