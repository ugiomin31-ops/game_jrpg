읽기 전용 감사를 마쳤습니다. 현재 브랜치는 `claude/motion-polish-pr9`입니다. **새 Generic Mixamo 몬스터의 재질·텍스처 보존에는 아래 조건부 위험이 있습니다.**

1. **P1 — 기존 재질 매핑을 자동 생성 Toon 재질로 덮어씁니다.**  
   [AbyssArtImporter.cs:564](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:564)의 `Sync()`는 `<id>_tex/<재질명>.png`마다 재질을 만들고, 기존 외부 매핑이 그 재질과 다르면 `AddRemap()`으로 교체합니다(577–580행). `Ensure()`는 원본 재질을 복사하지 않고 `Abyss/Toon`과 `_BaseMap`만 설정합니다(598–600행). 따라서 원본의 노멀·금속성·거칠기·발광 맵, UV 변환, 투명도 설정을 자동 보존하지 않습니다. 알파 클리핑도 `_FACE/_EYE/_HAIR` 이름 규칙에 의존합니다(504–507, 746–752행).  
   **다음 조치:** 새 모델의 실제 슬롯별 원본 설정을 확인하고, 기존 명시적 매핑을 보존하거나 승인된 Toon 변환을 명시적으로 적용해야 합니다.

2. **P1 — `_tex`의 노멀·데이터 맵까지 색상 텍스처로 강제 처리합니다.**  
   [AbyssArtImporter.cs:275](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:275)는 해당 폴더 PNG 전체에 `textureType = Default`, `sRGBTexture = true`를 설정합니다(279–280행). 정상적인 NormalMap/linear 설정도 재임포트 때 덮어씁니다. 또한 `Sync()`는 PNG마다 별도 재질 이름으로 취급하므로, 보조 맵을 원래 재질의 해당 슬롯에 연결하지 않습니다.  
   **다음 조치:** albedo와 normal/metallic/roughness/AO를 구분하는 명시적 맵 계약이 필요합니다.

3. **P2 — 런타임 효과가 원본 재질의 기본색을 대체합니다.**  
   [ArtLibrary.cs:94](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:94)의 팔레트 적용과 피격·디졸브 처리는 [CharacterModel.cs:294](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:294)의 `ApplyBlock()`으로 이어집니다. 여기서는 각 재질의 기존 `_BaseColor`를 읽지 않고 `_tint * _palette`를 renderer 전체에 설정합니다(302행). 원본 기본색이 흰색이 아닌 모델이나 여러 색상 슬롯을 가진 모델은 효과 적용 후 색이 달라질 수 있습니다. 텍스처 참조 자체를 삭제하는 문제는 아닙니다.  
   **다음 조치:** 재질 슬롯별 원본 기본색을 보존하여 효과색과 곱하도록 처리해야 합니다.

4. **P2 — Tripo 표식 누락·늦은 추가로 2K 텍스처가 1K로 제한될 수 있습니다.**  
   [AbyssArtImporter.cs:287](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:287)는 `TRIPO` 또는 `.tripo` 표식이 있어야 2048을 적용하고, 없으면 1024를 강제합니다(300행). 표식 파일 추가 자체는 `OnPostprocessAllAssets()`의 모델/텍스처 처리 대상이 아닙니다(315–317행).  
   **다음 조치:** 최초 임포트 전에 표식을 배치하고, 늦게 추가했다면 해당 모델의 텍스처만 명시적으로 재임포트해야 합니다.

확인된 보존 경로도 있습니다. [ArtLibrary.cs:108](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:108)는 가져온 프리팹을 그대로 복제합니다. Generic 경로 역시 `ImportStandard`·`InPrefab`을 사용하므로 **모든 재질을 일괄 제거하는 구조는 아닙니다.** 다만 `M_Toon/M_Emit/M_Clear` 이름은 공유 재질로 자동 매핑됩니다(임포터 189–197행).

검수 항목은 코드 경로 확인·위험 순위화·다음 조치 제시까지 완료했습니다. 파일·설정 변경, 자식 에이전트, Unity 실행, 테스트, 브라우저 사용은 없었습니다. 새 FBX의 실제 슬롯·맵·12k 삼각형 수와 렌더링은 검증하지 않았으며, 위 항목은 **발생 조건이 확인된 코드 위험**입니다. 요청된 Astra High/priority의 실제 라우팅은 이 작업에서 확인할 수 없었습니다.