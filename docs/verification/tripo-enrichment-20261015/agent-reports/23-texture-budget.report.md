읽기 전용 감사 결과, **수정 권고 1건과 정리 후보 1건**입니다. 현재 브랜치는 `claude/motion-polish-pr9`이며 파일은 수정하지 않았습니다.

1. **P2 — 소형 VFX 소품 2개가 1K 예산보다 크게 임포트됩니다.**  
   `mesh_aid_kit.png`, `mesh_riot_shield.png`는 실제 2048×2048이고 임포트 상한도 2048입니다.
   - [구급상자 메타데이터](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Vfx/Textures/mesh_aid_kit.png.meta:34)
   - [방패 메타데이터](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Vfx/Textures/mesh_riot_shield.png.meta:34)

   [효과 정의](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Vfx/effects.json:21125)에서도 각각 1초·1.25초짜리 소품으로 사용됩니다. **다음 조치:** 두 파일의 기본 임포트 상한을 1024로 낮추고 실제 화면에서 식별성을 검증하십시오. 동일 압축 형식이면 텍셀 수는 75% 감소하지만, 실제 GPU 절감량은 측정하지 않았습니다.

2. **P3 — 원본 JPEG 28개가 런타임 Resources 안에 남아 있습니다.**  
   `Vfx/Textures/original`에는 2K 14개, 1K 14개, 총 **8,478,954바이트**의 원본이 있습니다. 예: [feather 원본 메타데이터](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Vfx/Textures/original/feather_basecolor.jpeg.meta:34). 제한적으로 확인한 Vfx 메타데이터·머티리얼·프리팹·효과 정의에는 이 원본 GUID 참조가 없었습니다.

   이는 배포 용량 정리 후보이며 **중복 런타임 할당이 확인된 것은 아닙니다.** 다음 조치는 부모 작업에서 전체 참조를 확인한 뒤 원본을 `ArtSource`로 옮기는 것입니다.

나머지 확인 결과:

- 적 텍스처 16개 모두 기본·플랫폼 상한 2K입니다. 4K 원본 2개도 2K 제한이 있으므로 초과 임포트로 판정하지 않았습니다.
- 총 146개 외부 텍스처 모두 `isReadable: 0`. 각 폴더 내 SHA-256 동일 파일은 없습니다.
- 적 머티리얼 16개는 `_BaseMap`에 연결되어 있어 `sRGBTexture: 1`과 용도가 일치합니다. Vfx에서도 확정할 색 공간 오류는 발견하지 못했습니다.
- [VfxLibrary.cs:455](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:455)는 텍스처·블렌드 조합별 머티리얼을 캐시합니다. 확인한 경로에는 매 호출 텍스처 생성 코드가 없습니다.

**증거 한계:** 외부 이미지와 관련 메타데이터 중심의 정적 감사입니다. FBX 내장 텍스처, 실제 빌드 용량·GPU 할당·렌더링은 검증하지 않았으며 Unity·테스트는 실행하지 않았습니다. 요청된 Astra High/priority 라우팅은 이 세션에서 독립 확인할 수 없습니다.