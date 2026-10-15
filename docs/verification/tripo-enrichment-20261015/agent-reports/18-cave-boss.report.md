현재는 **`crystal_horror` 별칭을 유지하고, 기존 Studio 작업의 무과금 복구 가능성만 확인하는 것이 안전합니다.** 독립 사족보행 모델의 정상 리그는 확인되지 않았습니다.

요청 라우팅은 GPT-6 Astra High·fast/priority이며, 실제 모델·서비스 등급은 이 작업에서 검증하지 않았습니다. 자식 에이전트는 실행하지 않았습니다.

1. **높음 — 두 번의 리그 실패가 구체적으로 기록돼 있습니다.**  
   [prompts.md:24](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/hunter-bosses/crystal_cave_lord/candidates/prompts.md:24): 첫 결과는 30 bones, 7 vertex groups, 5,150 vertices 중 2,794개만 weighted입니다. 다리·꼬리는 weights가 없습니다. 두 번째 결과도 7 vertex groups에 그쳤고 다리·꼬리가 unweighted입니다. 기록된 누적 비용은 **130 credits**이며, 두 결과 모두 미설치입니다. 새 애니메이션을 구입하는 것으로 이 결함이 해결된다고 가정할 수 없습니다.

2. **높음 — 사이드카의 보관 기록과 현재 폴더가 일치하지 않습니다.**  
   [prompts.md:23](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/hunter-bosses/crystal_cave_lord/candidates/prompts.md:23)는 ZIP 및 `tripo_export/` 보관을 기록하지만, **현재 해당 자산 폴더**에는 `concept.png`, 후보 A–D, `prompts.md`만 있습니다. 이 경로에서는 실패 FBX를 재검사할 수 없습니다. 다른 체크아웃이나 백업에서 삭제됐다는 뜻은 아닙니다.

3. **중간 — 현재 데이터는 여전히 기존 모델을 명시적으로 사용합니다.**  
   [enemies.json:10331](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/enemies.json:10331)에 tint `[0.6, 0.85, 1, 1]`, model `crystal_horror`가 있습니다. [ArtVariants.cs:10](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Data/ArtVariants.cs:10)과 같은 파일 20–23행은 이 모델 선택 및 별칭 tint를 뒷받침합니다. 대상 `crystal_horror.fbx`도 존재합니다. 독립 모델 분리가 이미 완료됐다고 볼 근거는 없습니다.

4. **중간 — 과거 가격·옵션 기록은 재시도 허가가 아닙니다.**  
   [enemies.md:11](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/_briefs/enemies.md:11)는 **세 번째 유료 rig 금지**를 명시합니다. [_other_rig_animation_options.md:12](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/enemies/_other_rig_animation_options.md:12)는 Other preset의 무료 여부가 미검증이라고 기록합니다. 이 문서는 다른 생물의 과거 관찰이며, 이 보스의 현재 옵션·가격 증거가 아닙니다.

**부모 세션의 정확한 다음 행동과 중단 조건**

1. 부모 전용 Studio IAB에서 기존 task `e207ee73-40fd-4837-b072-580d5e49053f`를 찾아 원본, retopo, 두 rig 결과의 존속 여부만 확인합니다. 생성·Retry·구매는 누르지 않습니다.
2. 기존 결과를 추가 비용 없이 내려받을 수 있음이 확인되면, 프로젝트 ArtSource의 새 복구 폴더에 원본 그대로 보존하고 즉시 Studio 탭을 닫습니다. 기록된 retopo는 **10,316 triangles**이므로 처음부터 재생성·재retopo할 근거는 없습니다.
3. 무료 오류 복구가 실제로 제공되는지 확인하되, 이번 실패는 기록상 **완료된 rig의 품질 실패**입니다. 서버 오류 무료 재시도 대상이라고 추정하지 않습니다. 유료 Retry만 있거나 기존 작업이 없으면 별칭을 유지하고 중단합니다.
4. Studio가 수정 결과를 제공한 경우에만 후속 검증합니다. Blender에서는 weights를 작성하거나 수정하지 않고, 네 다리·꼬리의 실제 변형과 unweighted vertices를 검사합니다. 통과 전에는 Unity 설치·별칭 변경을 하지 않습니다. 이후 Studio 애니메이션도 가격과 사족보행 적합성을 별도로 확인해야 합니다.

검토 체크: 별칭 확인 ✓ 실패 기록 확인 ✓ 제한된 복구 경로 제안 ✓ 파일 변경 없음 ✓. 브라우저·API·Unity·테스트·스크린샷은 실행하지 않았으며, 리그 수치와 비용은 사이드카의 과거 기록입니다. 새 런타임 복구를 완료했다고 주장하지 않습니다.