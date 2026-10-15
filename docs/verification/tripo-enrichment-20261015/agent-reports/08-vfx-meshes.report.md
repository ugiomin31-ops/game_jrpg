읽기 전용 검토 결과, **구체적인 축 불일치 1건(P2)**을 확인했습니다. 현재는 기본 28개와 `aid_kit`, `riot_shield`를 합쳐 **30개 메시**이며, 레시피가 모두 참조합니다.

- **P2 — `sword_phantom`의 검날 축과 궤도 진행 축 불일치.** FBX 좌표 범위는 X ±0.1904, Y −0.3981~1.0019, Z ±0.2233으로 검날이 +Y 방향입니다. 하지만 [VfxLibrary.cs:623](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:623)는 +Z를 궤도 접선에 정렬하며, [435행](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:435)의 축 보정에 이 메시가 없습니다. 따라서 검날은 진행 방향을 향하지 않고 위로 선 채 공전합니다.
  
  영향 레시피는 `ultimate_warrior`, `job_knight`, `job_shadow_stalker`, `phantom_raid`입니다. 근거는 [effects.json:2165](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Vfx/effects.json:2165) 및 같은 파일 2839·4414·15366행입니다. 모두 별도 회전 보정이 없습니다.

**다음 조치:** 부모가 검날의 접선 정렬 의도를 확정한 뒤, `sword_phantom`의 **orbit 사용에만** +Y→+Z 보정을 적용하십시오. 공용 캐시의 `Basis`를 일괄 변경하면 같은 메시를 세워 표시하는 `enchant`까지 회전합니다([effects.json:4961](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Vfx/effects.json:4961)). 원본 메시 수정·감면·대체는 필요 없습니다.

나머지 확인 결과:

- **로딩:** 30개 참조 모두 FBX 존재. 각 파일은 Geometry 1개이며 명시적인 비기본 모델 변환이 없었습니다.
- **피벗·스케일:** 기본 28개의 좌표 경계와 메타 설정에서 추가적인 확정 결함을 찾지 못했습니다. 전체 원본 최장 치수는 약 0.6~3m로 로더 허용 범위 0.05~6m 안입니다. 메타는 `globalScale: 1`, 파일 단위 사용, 축 변환 베이크로 일치합니다.
- **캐시:** [VfxLibrary.cs:422](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:422)의 ID별 재사용과 검증 후 등록 구조에서 현재 에셋에 대한 결함을 확인하지 못했습니다.

검토 항목인 로딩·피벗·캐시·스케일 대조를 마쳤습니다. 파일 변경, Unity 실행, 테스트, 스크린샷 촬영은 하지 않았습니다. 위 결과는 현재 FBX 바이너리·메타·코드의 정적 근거이며, Unity 임포트 결과와 실제 화면은 새로 검증하지 않았습니다.