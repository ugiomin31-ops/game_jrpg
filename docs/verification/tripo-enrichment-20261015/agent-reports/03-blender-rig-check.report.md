[Tools/verify_tripo_rig.py](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/verify_tripo_rig.py)만 추가했습니다.

- **36행:** 실제 변형 본의 정점 가중치와 미가중 정점 집계.
- **89행:** 새 씬에 FBX를 가져와 주요 사지 본 회전 전후의 평가 메시 이동량 검사. 가중치 없음·비유한 값·무변형을 실패 처리합니다.
- **67행:** 애니메이션 일시 중지·복원 및 action slot 보존 처리. 포즈는 예외 발생 시에도 복원합니다.
- **197행:** JSON 보고서 출력과 입력 원본 덮어쓰기 방지. FBX·씬 저장이나 메시 정리는 수행하지 않습니다.

**검증:** Python AST 구문 검사 통과. Blender 실행·실제 FBX 검증·Unity 테스트는 수행하지 않았으므로 런타임 호환성은 미검증입니다. 부분적으로 미가중인 정점은 보고하며, 그것만으로 실패시키지는 않습니다.

다음 검증 명령:

```powershell
blender --background --python Tools/verify_tripo_rig.py -- input.fbx output.json
```