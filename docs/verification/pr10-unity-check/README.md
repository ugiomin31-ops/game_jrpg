# PR #10 Unity 플레이 확인 (2026-10-16)

사용자 PC에서 `2d41dbe`를 Windows 플레이어로 빌드해 ReviewBoot로 찍은 화면입니다. 게임 카메라를 오프스크린 렌더해 캡처해서 화면 UI(턴 순서·파티 초상화)는 나오지 않습니다.

- `01_town.png`: 마을의 헌터 4명, NPC 서 주임·백 길드장
- `02_battle.png`: 전투의 헌터 4명, 슬라임·버섯·박쥐
- `03_subway_floor1.png`: 지하철 던전 1층 바닥·벽·기둥·에스컬레이터

분홍(재질 없음)·흰색(텍스처 빠짐) 모델은 없었고, 플레이어 로그에 `Exception`·`Missing production` 오류도 없었습니다. 원본 기록은 `local-requests` 브랜치 `requests/unity_check_pr10.md`.
