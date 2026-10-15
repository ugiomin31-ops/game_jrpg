"""Enemy skills added for chapters 5-7, the new bosses and the superbosses. Every presentation id already exists in
presentation.json; statuses are existing statuses.json rows."""

# kind: 0 damage 1 heal 2 buff 3 debuff | scaling: 0 atk 1 mag | target: 0 enemy 1 ally 2 self | scope: 0 single 1 all
# 2 random | element: 0 none 1 slash 2 blunt 3 pierce 4 fire 5 ice 6 thunder 7 dark 8 holy


def S(id, name, desc, kind, scaling, target, scope, element, power, pres, hits=1, mp=0, status=None, chance=0.0,
      extra=None, drain=0.0, crit=0.0, ignore=0.0):
    row = {
        'id': id, 'display_name': name, 'description': desc, 'kind': kind, 'scaling_stat': scaling,
        'target_type': target, 'scope': scope, 'element': element, 'power': power, 'hit_count': hits,
        'mp_cost': mp, 'tp_cost': 0, 'crit_bonus': crit, 'defense_ignore': ignore, 'tier': 2,
        'status_chance': chance, 'bonus_vs_status': '', 'bonus_vs_status_mult': 1.0,
    }
    if status:
        row['status_effect'] = status
    if extra:
        row['extra_statuses'] = extra
    if drain:
        row['drain'] = drain
    row['presentation'] = pres
    row['_file'] = id
    return row


NEW_SKILLS = [
    # ---- chapter 5: 가라앉은 신전
    S('sk_e_thunder', '전격', '번개를 내리꽂아 한 명을 감전시킵니다.', 0, 1, 0, 0, 6, 1.3, 'pr_thunder', mp=4, status='stun', chance=0.12),
    S('sk_e_thunder_all', '뇌우', '번개 비를 내려 전체를 공격합니다.', 0, 1, 0, 1, 6, 0.75, 'pr_thunder_all', mp=10),
    S('sk_e_water_jet', '물대포', '압축한 물줄기를 쏘아 한 명을 꿰뚫습니다.', 0, 1, 0, 0, 5, 1.35, 'pr_ice', mp=4, status='slow', chance=0.3),
    S('sk_e_tidal_wave', '해일', '거대한 물결로 전체를 덮쳐 발을 묶습니다.', 0, 1, 0, 1, 5, 0.8, 'pr_freezing_tide', mp=10, status='slow', chance=0.25),
    S('sk_e_spike_burst', '가시 폭발', '온몸의 가시를 터뜨려 전체를 찌릅니다.', 0, 0, 0, 1, 3, 0.6, 'pr_arrow_all', status='bleed', chance=0.25),
    S('sk_e_puff_up', '부풀기', '몸을 잔뜩 부풀려 방어력을 높입니다.', 2, 0, 2, 0, 0, 0.0, 'pr_harden', status='defense_up', chance=1.0),
    S('sk_e_coral_spear', '산호 창찌르기', '산호 창으로 날카롭게 찌릅니다.', 0, 0, 0, 0, 3, 1.35, 'pr_arrow_snipe', crit=0.1),
    S('sk_e_shell_bash', '방패 밀치기', '조개 방패로 밀쳐 기절시킵니다.', 0, 0, 0, 0, 2, 1.1, 'stunning_slam', status='stun', chance=0.3),
    S('sk_e_lure', '유혹의 등불', '흔들리는 빛으로 한 명을 잠재웁니다.', 3, 1, 0, 0, 0, 0.0, 'pr_dread_stare', status='sleep', chance=0.5),
    S('sk_e_deep_bite', '심해의 이빨', '커다란 턱으로 물어뜯어 체력을 빼앗습니다.', 0, 0, 0, 0, 1, 1.3, 'pr_bite', drain=0.3),
    S('sk_e_clamp', '조개 물기', '두 껍데기로 꽉 물어 움직임을 묶습니다.', 0, 0, 0, 0, 2, 1.4, 'pr_heavy_enemy', status='slow', chance=0.4),
    S('sk_e_pearl_beam', '진주 광선', '진주에 모은 빛을 쏘아 전체를 태웁니다.', 0, 1, 0, 1, 8, 0.75, 'pr_holy_all', mp=8),
    S('sk_e_halberd', '미늘창 내려치기', '무거운 미늘창으로 내려칩니다.', 0, 0, 0, 0, 1, 1.5, 'pr_heavy_enemy'),
    S('sk_e_stone_skin', '석화 피부', '돌처럼 굳어 받는 피해를 크게 줄입니다.', 2, 0, 2, 0, 0, 0.0, 'pr_harden', status='defense_up_l', chance=1.0),
    S('sk_e_constrict', '휘감기', '긴 몸으로 휘감아 조입니다.', 0, 0, 0, 0, 2, 1.25, 'pr_root', status='slow', chance=0.5),
    S('sk_e_venom_fang', '맹독 이빨', '맹독을 주입합니다.', 0, 0, 0, 0, 3, 1.1, 'pr_arrow_poison', status='poison_strong', chance=0.6),
    S('sk_e_anchor_smash', '닻 내려찍기', '녹슨 닻을 내려찍어 기절시킵니다.', 0, 0, 0, 0, 2, 1.6, 'pr_heavy_enemy', status='stun', chance=0.3),
    S('sk_e_drowning_sweep', '익사의 휩쓸기', '물살과 함께 전체를 휩씁니다.', 0, 0, 0, 1, 2, 0.9, 'pr_blunt_all', status='slow', chance=0.2),
    S('sk_e_naga_hymn', '나가의 찬가', '물의 찬가로 동료 전체를 치유합니다.', 1, 1, 1, 1, 0, 0.55, 'pr_heal_all', mp=12),
    S('sk_e_trident', '삼지창 저주', '삼지창 끝의 저주로 한 명을 공격합니다.', 0, 1, 0, 0, 7, 1.4, 'pr_dark', mp=6, status='silence', chance=0.25),
    S('sk_e_shell_quake', '등껍질 지진', '신전을 짊어진 등으로 바닥을 흔듭니다.', 0, 0, 0, 1, 2, 1.0, 'pr_blunt_all', status='stun', chance=0.1),
    S('sk_e_siren_song', '세이렌의 노래', '아름다운 노래로 전체를 잠재웁니다.', 3, 1, 0, 1, 0, 0.0, 'pr_lullaby', status='sleep', chance=0.3),
    S('sk_e_feather_storm', '깃털 폭풍', '날카로운 깃털을 흩뿌립니다.', 0, 0, 0, 2, 1, 0.45, 'pr_crow_swarm', hits=4),
    # ---- chapter 6: 심연의 핵
    S('sk_e_void_gaze', '공허의 시선', '수많은 눈이 한 명을 꿰뚫어 봅니다.', 0, 1, 0, 0, 7, 1.4, 'pr_dark', mp=5, status='silence', chance=0.3),
    S('sk_e_shadow_bite', '그림자 송곳니', '그림자 이빨로 물어 출혈을 일으킵니다.', 0, 0, 0, 0, 7, 1.3, 'pr_bite', status='bleed', chance=0.4),
    S('sk_e_tentacle_flail', '촉수 난타', '촉수를 마구 휘둘러 무작위로 때립니다.', 0, 0, 0, 2, 2, 0.5, 'pr_crow_swarm', hits=4),
    S('sk_e_devour', '집어삼키기', '거대한 입으로 삼켜 체력을 빼앗습니다.', 0, 0, 0, 0, 7, 1.5, 'pr_m_drain', drain=0.5),
    S('sk_e_stone_dive', '석상 낙하', '높이 날아올라 돌의 몸으로 내리꽂힙니다.', 0, 0, 0, 0, 2, 1.55, 'pr_heavy_enemy'),
    S('sk_e_nightmare', '악몽', '끔찍한 꿈을 보여 전체를 잠재우고 저주합니다.', 3, 1, 0, 1, 0, 0.0, 'pr_curse_screech', status='sleep', chance=0.25, extra=['attack_down']),
    S('sk_e_dark_trample', '어둠의 질주', '보랏빛 갈기를 휘날리며 전체를 짓밟습니다.', 0, 0, 0, 1, 7, 0.85, 'pr_blunt_all'),
    S('sk_e_mirror_strike', '거울 반격', '상대의 기술을 비춰 되받아칩니다.', 0, 1, 0, 0, 0, 1.5, 'pr_void_lance', mp=6),
    S('sk_e_mirror_guard', '거울 장막', '깨진 거울로 몸을 감싸 피해를 줄입니다.', 2, 1, 2, 0, 0, 0.0, 'pr_abyss_wall', status='barrier', chance=1.0),
    S('sk_e_burrow_strike', '땅속 기습', '땅속에서 솟구쳐 한 명을 들이받습니다.', 0, 0, 0, 0, 2, 1.6, 'pr_heavy_enemy', status='stun', chance=0.2),
    S('sk_e_fallen_blade', '타락의 대검', '부러진 후광의 빛을 담아 내려벱니다.', 0, 0, 0, 0, 7, 1.7, 'pr_w_giga', crit=0.1),
    S('sk_e_black_wings', '검은 날개', '찢어진 날개로 전체를 베어 냅니다.', 0, 0, 0, 1, 1, 0.95, 'pr_slash_all', status='bleed', chance=0.2),
    S('sk_e_void_scythe', '공허의 낫', '공허의 낫으로 전체의 영혼을 벱니다.', 0, 1, 0, 1, 7, 0.95, 'pr_harvest_reap', mp=8),
    S('sk_e_death_mark', '죽음의 표식', '한 명에게 죽음의 표식을 새깁니다.', 3, 1, 0, 0, 0, 0.0, 'pr_debuff', status='defense_down', chance=0.9, extra=['slow']),
    S('sk_e_crystal_spike', '수정 가시', '수정 가시를 무작위로 쏘아 댑니다.', 0, 0, 0, 2, 3, 0.6, 'pr_ice_shard', hits=3),
    S('sk_e_crystal_shell', '수정 갑각', '수정을 덧씌워 몸을 보호합니다.', 2, 1, 2, 0, 0, 0.0, 'pr_abyss_wall', status='barrier', chance=1.0, extra=['defense_up']),
    # ---- chapter 5 boss: 레비아탄
    S('sk_lev_tail_crush', '꼬리 강타', '거대한 꼬리로 한 명을 짓누릅니다.', 0, 0, 0, 0, 2, 1.6, 'pr_heavy_enemy'),
    S('sk_lev_maelstrom', '대소용돌이', '바다를 소용돌이치게 해 전체를 휩씁니다.', 0, 1, 0, 1, 5, 0.95, 'pr_freezing_tide', status='slow', chance=0.3),
    S('sk_lev_thunder_fin', '뇌광 지느러미', '발광하는 지느러미에서 번개를 뿜습니다.', 0, 1, 0, 1, 6, 0.9, 'pr_thunder_all', status='stun', chance=0.12),
    S('sk_lev_deep_roar', '심해의 포효', '포효로 전체의 기세를 꺾습니다.', 3, 1, 0, 1, 0, 0.0, 'pr_screech', status='attack_down', chance=0.6, extra=['defense_down']),
    S('sk_lev_abyss_breath', '심연의 숨결', '심해의 냉기를 내뿜어 전체를 얼립니다.', 0, 1, 0, 1, 5, 1.35, 'pr_breath', status='freeze', chance=0.2),
    # ---- chapter 6 boss: 심연의 군주
    S('sk_lord_void_blade', '공허의 검', '양손검에 공허를 실어 벱니다.', 0, 0, 0, 0, 7, 1.75, 'pr_w_giga', crit=0.1),
    S('sk_lord_dominion', '지배', '심연의 의지로 전체를 짓누릅니다.', 0, 1, 0, 1, 7, 1.0, 'pr_dark_all', status='attack_down', chance=0.35),
    S('sk_lord_eclipse', '일식', '빛을 삼켜 전체의 눈과 입을 막습니다.', 3, 1, 0, 1, 0, 0.0, 'pr_curse_screech', status='blind', chance=0.45, extra=['silence']),
    S('sk_lord_crown', '뿔의 왕관', '왕관이 빛나며 힘과 방어가 오릅니다.', 2, 1, 2, 0, 0, 0.0, 'pr_sun_aegis', status='attack_up', chance=1.0, extra=['defense_up']),
    S('sk_lord_annihilation', '소멸', '모든 것을 공허로 되돌립니다.', 0, 1, 0, 1, 7, 1.55, 'pr_m_abyss_gate'),
    S('sk_lord_soul_drain', '영혼 흡수', '한 명의 영혼을 빨아들여 회복합니다.', 0, 1, 0, 0, 7, 1.35, 'pr_m_drain', drain=0.5),
    # ---- superboss signatures (시련의 회랑)
    S('sk_ex_ancient_wrath', '태고의 분노', '숲 전체의 뿌리가 솟구쳐 모두를 꿰뚫습니다.', 0, 0, 0, 1, 3, 1.15, 'pr_vine_lash', status='slow', chance=0.4),
    S('sk_ex_abyss_tide', '심해의 만조', '끝없는 만조가 모두를 얼려 버립니다.', 0, 1, 0, 1, 5, 1.2, 'pr_freezing_tide', status='freeze', chance=0.25),
    S('sk_ex_solar_apocalypse', '태양 종언', '태양 그 자체를 떨어뜨립니다.', 0, 1, 0, 1, 4, 1.45, 'pr_sun_judgment', status='burn', chance=0.4),
    S('sk_ex_requiem', '망자의 진혼곡', '묘소의 모든 영혼이 함께 울부짖습니다.', 0, 1, 0, 1, 7, 1.25, 'pr_soul_reap', status='silence', chance=0.3),
    S('sk_ex_true_void', '진공', '빛도 소리도 남지 않는 완전한 공허.', 0, 1, 0, 1, 7, 1.8, 'pr_m_abyss_gate', ignore=0.2),
]
