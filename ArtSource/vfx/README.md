# VFX 메시 원본

각 `<id>/` 폴더는 이펙트 메시 하나의 제작 기록입니다. `candidates/prompts.md`에는 후보 이미지 프롬프트와 Tripo 작업 기록이, `<id>_basecolor.jpeg`에는 Tripo에서 받은 원본 색 텍스처가 있습니다.

게임은 `Assets/_Game/Resources/Vfx/Meshes/<id>.fbx`의 메시 모양만 쓰고, 색은 `Vfx/Textures/`의 이펙트 텍스처로 입힙니다(`VfxLibrary.cs`). 그래서 원본 색 텍스처는 2026-10-15에 `Resources/Vfx/Textures/original/`에서 이곳으로 옮겼습니다. 파일 내용은 바꾸지 않았습니다.
