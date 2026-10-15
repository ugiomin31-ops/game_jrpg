# Town NPCs — brief catalog (data-driven)

Source of truth: names and greetings in `text_ko.json` (`npc_<id>_name`, `npc_<id>_greeting*`). The current look spec
is in the docstrings of `Blender/npcs/generate_staff.py:1-12, 41-118`. Spawned via `ArtLibrary.NpcPath(id)` =
`Art/NPCs/<id>/<id>` (`Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:16`). The required set is the five staff
(`Assets/_Game/Scripts/Editor/AbyssProjectSetup.cs:108`). Generated 2026-10-11.

Frame: same as hunters (adult, slim anime, ~7 heads, modern Seoul, symmetric A-pose front view, plain light-grey
background, square, solid attached details), but these are civilians/staff, not fighters. **Empty hands**: the props
in the current Blender spec (clipboard, calculator, wrench, tablet, cane) are dropped or moved onto the body as solid
attached shapes. Rig: Tripo Humanoid (Mixamo). Size: normal NPC 6–10k tris. Clips the NPC rig uses: Idle, Walk, Talk
(generate_staff.py:3). Status for all: TODO.

**innkeeper** · 「윤 간호사 · 의무실」 (guild infirmary nurse; the "inn" is the infirmary).
Greeting: 「어서 오세요. 소독약 냄새가 좀 나지만 침대는 따뜻해요. 오늘은 푹 쉬어요.」
Brief: A warm, friendly Korean nurse in light-pink scrubs with a small nurse cap and a first-aid cross badge, white clogs, hair in a bun, an ID card clipped on. No clipboard in hand.

**shopkeeper** · 「박 사장 · 헌터 마켓」 (hunter market owner).
Greeting: 「게이트 들어가기 전엔 회복 포션! 이건 상식이라고요.」
Brief: A cheerful middle-aged shop owner: plain teal shirt under a khaki work vest full of pockets, khaki trousers, brown work boots, cap worn backwards, a calculator clipped to the vest.

**smith** · 「곽 장인 · 장비 공방」 (equipment workshop master).
Greeting: 「재료만 가져와. 무기에 혼을 불어넣는 건 내 몫이니.」
Brief: A gruff craftsman with a short beard: grey work shirt, dark leather apron, welding cap, heavy gloves, safety boots; the big wrench hangs from the apron loop instead of in his hand.

**guild_clerk** · 「서 주임 · 접수처」 (guild reception).
Greeting: 「의뢰 게시판이 갱신됐어요. 보상은 확실하답니다!」
Brief: A smart young receptionist: navy blazer, red tie, blue lanyard with an ID card, navy skirt and low heels, neat hair; the tablet is held flat against the hip by a strap or dropped.

**elder** · 「백 길드장 · 길드장실」 (Dawn Guild master; also the story narrator `elder_1..5`).
Greeting: 「게이트가 모두 닫힐 그날까지, 이 길드는 그대들을 믿겠소.」
Brief: A dignified older guild master with silver swept-back hair: black three-piece suit with the jacket open over a gold-edged waistcoat, polished shoes, a small Dawn Guild sun pin. The cane is left out, or kept planted vertically with a solid join to the hand (rig risk).

## villager_a / villager_b / villager_c — probably orphaned, do not generate yet
The FBXs exist (`Art/NPCs/villager_a..c/`), but no data row, text key or script loads them. The `villager_1..3` town
spots now hold benched hunters (`Assets/_Game/Scripts/Runtime/World/TownWorld.cs:99-107`). Main should confirm before
spending a generation on them, or delete them in a later cleanup.
