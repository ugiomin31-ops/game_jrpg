**새 `elite_mushroom`의 임포트 계약은 Generic 리그 + 자체 애니메이션 7종 + TRIPO 마커입니다.** 읽기 전용 검토를 마쳤으며 파일 변경, Unity 실행, 테스트는 하지 않았습니다.

발견 사항은 우선순위순입니다.

1. **높음 — Generic 적은 Humanoid 공용 클립으로 보충되지 않습니다.** 공용 클립 대체는 `animator.isHuman && !HasIdle(clips)`일 때만 실행됩니다. 적의 별도 `_moves.fbx`도 자동 병합 대상이 아닙니다. 따라서 새 모델 FBX 안에 필요한 take를 함께 넣어야 합니다. [ArtLibrary.cs:124](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:124)

2. **높음 — 이전 `.meta`의 클립 범위를 새 모델의 계약으로 복사하면 안 됩니다.** 임포터는 `defaultClipAnimations`에서 매번 클립 목록을 재작성합니다. take 이름의 마지막 `|` 뒤 문자열을 이름으로 사용하고, 같은 이름은 최초 하나만 남깁니다. `mixamo.com` 같은 원본 이름을 `Attack`으로 추론하지 않습니다. [AbyssArtImporter.cs:243](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:243)

3. **중간 — TRIPO와 HUMANOID는 독립적인 마커입니다.** 현재 대상 폴더에는 FBX와 `.meta`만 있고 두 마커 모두 없습니다. 이는 현재 파일 상태이며 새 Tripo 자산의 설치 실패를 뜻하지 않습니다. `TRIPO`는 Tripo 처리 여부, `HUMANOID`는 Human 리그 분기를 결정합니다. [AbyssArtImporter.cs:113](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:113)

정확한 설치·임포트 계약:

| 항목 | 새 `elite_mushroom` 요구사항 |
|---|---|
| 모델 위치 | `Assets/_Game/Resources/Art/Enemies/elite_mushroom/elite_mushroom.fbx` |
| 마커 | 같은 폴더의 확장자 없는 `TRIPO` **또는** `elite_mushroom.tripo`. `TRIPO.meta`만으로는 인식되지 않음 |
| 리그 | `HUMANOID`를 추가하지 않음. Generic, CreateFromThisModel, Import Animation 활성 |
| 자동 설정 | `optimizeGameObjects=false`, `resampleCurves=true`, KeyframeReduction, `globalScale=1`, `useFileScale=true` |
| 클립 이름 | `Idle`, `Run`, `Attack`, `Cast`, `Hit`, `Die`, `Victory`. 예: `Rig|Attack` → `Attack` |
| 루프 | 위 7종 중 `Idle`, `Run`만 루프. `loopPose=false`, 루트 회전/Y/XZ 잠금 모두 false |
| 텍스처 | `elite_mushroom_tex/<FBX 머티리얼명>.png` |
| 머티리얼 | `elite_mushroom_mat/<동일 이름>.mat`으로 생성·매핑 |
| 텍스처 설정 | TRIPO 인식 시 최대 2048, Default/Android override 2048, sRGB·mipmap 활성, 압축 적용 |
| 기존 식별자 | 기존 FBX `.meta`와 GUID `0752ea6cdbed5224cb2778d56065f4da` 보존 |

근거: [Generic 설정:205](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:205), [루프 설정:253](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:253), [텍스처 설정:274](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:274), [텍스처 경로 규약:477](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:477).

현재 [elite_mushroom.fbx.meta:48](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Art/Enemies/elite_mushroom/elite_mushroom.fbx.meta:48)에 기록된 범위는 다음과 같습니다. **새 export의 고정 요구 프레임 수는 아닙니다.**

| 클립 | 현재 프레임 | 루프 |
|---|---:|---|
| Attack | 0–25 | 아니오 |
| Cast | 0–35 | 아니오 |
| Die | 0–30 | 아니오 |
| Hit | 0–12 | 아니오 |
| Idle | 0–48 | 예 |
| Run | 0–20 | 예 |
| Victory | 0–44 | 아니오 |

**부모의 다음 행동:** 새 export의 스킨 웨이트와 위 7개 take를 확인한 뒤, 기존 `.meta`를 보존하여 지정 경로에 설치하고 TRIPO 마커·텍스처를 함께 배치하십시오. 이후 대상 자산만 재임포트하여 실제 클립 이름·길이·루프·메시 변형·재질을 확인해야 합니다. 마커만 추가하는 것으로 기존 텍스처가 재처리된다고 가정하면 안 됩니다.

검토 항목인 리그 분기, 마커, `.meta` 클립, 적용 순서는 모두 확인했습니다. 새 FBX의 실제 내용과 런타임 재생은 검증하지 않았으며, 요청된 Astra High/priority 라우팅도 이 세션의 관측 가능한 정보로 확인하지 못했습니다.