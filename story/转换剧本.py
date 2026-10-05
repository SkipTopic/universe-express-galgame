# -*- coding: utf-8 -*-
"""导演版剧本转换器 v2
润色小说(ch*_p.md) → 游戏剧本 story/chXX.txt
引语段落自动拆三段：旁白前缀 / 角色台词 / 旁白后缀
说话人判定四规则：XX说：模式 > 引语后缀我动作 > 引语后缀角色 > 纯引语第一人称
场景触发：换景+清人+换BGM；台词情绪→表情差分
"""
import os, re

BASE = r"D:\我的godot项目\小时候的小说"
RUN = os.path.join(BASE, "工作区域", "润色")
STORY = os.path.join(BASE, "godot项目galgame", "story")

SPRITES = {
    "查理": "char_charlie", "晓琳": "char_xiaolin", "照片": "char_photo",
    "毕福吉": "char_bi", "华福吉": "char_bi", "李磊": "char_lilei",
    "希朗首长": "char_xilang", "老船长": "char_charlie",
}
NAME_CHARS = sorted(SPRITES.keys(), key=len, reverse=True)
ROLE = r"(长官|军官|军长|老船长|船长|老爸|妈妈|爸爸|广播|老人|老头|女孩|少女|母亲|父亲)"

EXPR_RULES = [
    (r"笑|哈|高兴|开心|嘻嘻|没事了|好耶", "smile"),
    (r"怒|吼|闭嘴|混蛋|住手|可恶|开枪", "angry"),
    (r"哭|泪|难过|对不起|抱歉|别走|死去", "sad"),
    (r"什么？！|怎么可能|惊|愣住|震撼", "shock"),
]

def expr_for(text):
    for pat, expr in EXPR_RULES:
        if re.search(pat, text):
            return expr
    return "normal"

def detect_speaker(par):
    """旧版显式说话人：希朗首长：/查理说： 等开头模式"""
    for nm in NAME_CHARS:
        for suf in ("：", ":", "说：", "说:", "道：", "喊道：", "问道：", "心想："):
            if par.startswith(nm + suf):
                return nm, par[len(nm) + len(suf):].strip()
    for nm in NAME_CHARS:
        m = re.search(re.escape(nm) + r"[^，。！？\n]{0,6}[:：]\s*", par)
        if m and m.start() < 20:
            return nm, par[m.end():].strip()
    return None, None

def quote_speaker(pre, quote, post):
    """引语说话人判定，返回 (说话人或None)"""
    # 规则1：前缀"XX说："——先已知角色，再无名角色，"我"直判
    mp = re.search(r"([^“”\n]{0,24}?)(?:说|道|问|回答|喊|嘀咕)[：:]?\s*$", pre)
    if mp:
        subj = mp.group(1)
        s = subj.strip()
        if s == "我" or s.endswith("我"):
            return "我"
        for nm in NAME_CHARS:
            if nm in subj:
                return nm
        mr = re.search(ROLE, subj)
        if mr:
            return mr.group(1)
    # 规则2：后缀"我..."动作
    if re.match(r"^\s*我(?=(打断|说|心想|回答|喊|追问|拦|开口))", post):
        return "我"
    # 规则3：后缀紧跟无名角色
    mr = re.search(ROLE, post[:14])
    if mr:
        return mr.group(1)
    # 规则4：纯引语第一人称（段内无其他角色/角色词）
    if re.search(r"我|我们", quote) and not re.search(ROLE, pre + post) \
            and not any(nm in pre + post for nm in NAME_CHARS):
        return "我"
    return None

def split_quote(par):
    """段落 → (前缀旁白, 引语内容, 后缀旁文)。无引语返回 None。"""
    m = re.search(r"[“\"]", par)
    if not m:
        return None
    start = m.start()
    # 找配对引号（同型）
    q = par[start]
    end = par.find(q, start + 1)
    if end < 0:
        # 引号不配对：取到段尾
        end = len(par)
    pre = par[:start].strip()
    quote = par[start + 1:end].strip()
    post = par[end + 1:].strip()
    return pre, quote, post

def convert(num, ctitle, bg, bgm, triggers):
    src = os.path.join(RUN, "ch%02d_p.md" % num)
    paras = [l.strip() for l in open(src, encoding="utf-8").read().splitlines() if l.strip()]
    header = paras[0]
    out = ["【章节】%s" % header, "【音乐】%s" % bgm, "【背景】%s" % bg]
    cur_sprite = ""
    cur_speaker = ""
    done_triggers = set()

    def emit_line(who, text):
        nonlocal cur_sprite
        sp = SPRITES.get(who)
        if sp:
            expr = expr_for(text)
            want = sp if expr == "normal" else "%s_%s" % (sp, expr)
            if want != cur_sprite:
                out.append("【立绘】%s" % want)
                cur_sprite = want
        cur_speaker = who
        out.append("%s|%s" % (who, text))

    for par in paras[1:]:
        if re.match(r"^Subject", par):
            continue
        # 场景触发：黑场转场+换景+清人+换BGM
        for kw, newbg, newbgm in triggers:
            if kw in par and kw not in done_triggers:
                done_triggers.add(kw)
                out.append("【转场】")
                out.append("【背景】%s" % newbg)
                out.append("【音乐】%s" % newbgm)
                out.append("【立绘】无")
                cur_sprite = ""
                break
        m = re.match(r"^\[插图：(.+?)\]$", par)
        if m:
            out.append("【插图】%s" % m.group(1))
            continue
        sq = split_quote(par)
        if sq is None:
            # 纯旁白：更新说话人线索
            if re.search(ROLE, par) and not any(nm in par for nm in NAME_CHARS):
                cur_speaker = ""
            else:
                for nm in NAME_CHARS:
                    if nm in par:
                        cur_speaker = nm
            out.append(par)
            continue
        pre, quote, post = sq
        name = None
        # 先试显式开头模式（希朗首长：等）
        nm2, rest2 = detect_speaker(par)
        if nm2:
            emit_line(nm2, rest2)
            continue
        name = quote_speaker(pre, quote, post)
        if name is None:
            name = cur_speaker
        if name is None:
            name = "我"   # 实在判定不出且是引语：默认主角（引语几乎总是有人在说）
        # 拆三段
        if pre:
            out.append(pre)
        emit_line(name, quote)
        if post:
            out.append(post)
    path = os.path.join(STORY, "ch%02d.txt" % num)
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    n_dialog = sum(1 for l in out if "|" in l and not l.startswith("【"))
    n_me = sum(1 for l in out if l.startswith("我|"))
    print("ch%02d %s: %d行（台词%d，我方%d）" % (num, ctitle, len(out), n_dialog, n_me))

CHAPTERS = [
    (1,  "战争结束", "bg_battlefield", "bgm_scan13",
        [("演讲台", "bg_hall", "bgm_scan18"), ("军需处", "bg_office_military", "bgm_scan08"),
         ("宿舍", "bg_dorm", "bgm_scan19")]),
    (2,  "晓琳", "bg_hq", "bgm_scan15",
        [("飞船", "bg_ship_corridor", "bgm_scan16"), ("孤儿院", "bg_park", "bgm_scan12"),
         ("公园", "bg_park", "bgm_scan12")]),
    (3,  "老船长的故事", "bg_ship_corridor", "bgm_scan17",
        [("控制室", "bg_control", "bgm_scan06"), ("船舱", "bg_cabin", "bgm_scan17")]),
    (4,  "登船", "bg_deadplanet", "bgm_scan11",
        [("船舱", "bg_cabin", "bgm_scan05"), ("房间", "bg_cabin", "bgm_scan05")]),
    (5,  "死亡星球与伊甸园", "bg_deadplanet", "bgm_scan05",
        [("伊甸园", "bg_eden", "bgm_scan09"), ("飞船", "bg_cabin", "bgm_scan16")]),
    (6,  "凯特星之夜", "bg_nightmarket", "bgm_scan09",
        [("警局", "bg_office_military", "bgm_scan10"), ("街上", "bg_street_night", "bgm_scan21"),
         ("市场", "bg_market_day", "bgm_scan14")]),
    (7,  "口琴与往事", "bg_cabin", "bgm_scan08",
        [("医院", "bg_hospital", "bgm_scan13"), ("病房", "bg_hospital", "bgm_scan13"),
         ("兵营", "bg_war_end", "bgm_scan15"), ("军营", "bg_war_end", "bgm_scan15")]),
    (8,  "营救", "bg_deadplanet", "bgm_scan03",
        [("废墟", "bg_ruins_night", "bgm_scan22"), ("兵营", "bg_war_end", "bgm_scan03"),
         ("军营", "bg_war_end", "bgm_scan03"), ("大厅", "bg_hall", "bgm_scan18")]),
    (9,  "B65楼", "bg_corridor_b65", "bgm_scan22",
        [("电梯", "bg_elevator", "bgm_scan22"), ("机房", "bg_server", "bgm_scan01")]),
    (10, "晓琳之死", "bg_corridor_b65", "bgm_scan19",
        [("牢房", "bg_prison", "bgm_scan19")]),
    (11, "核弹与梦醒", "bg_space", "bgm_scan06",
        [("控制室", "bg_control", "bgm_scan06"), ("床", "bg_dorm", "bgm_scan19"),
         ("宿舍", "bg_dorm", "bgm_scan19"), ("医院", "bg_hospital", "bgm_scan13")]),
    (12, "尾声", "bg_street_night", "bgm_scan21",
        [("地铁", "bg_subway", "bgm_scan21"), ("站台", "bg_subway", "bgm_scan21")]),
]

for num, ctitle, bg, bgm, triggers in CHAPTERS:
    convert(num, ctitle, bg, bgm, triggers)

open(os.path.join(STORY, "格式说明.txt"), "w", encoding="utf-8").write(
"""游戏剧本格式说明（记事本直接改，保存即可生效）

【章节】标题        章节名
【背景】bg_xxx      切换背景（assets/sprites/bg/ 文件名）
【立绘】char_xxx    显示立绘（assets/sprites/characters/ 文件名；"无"=清空；可带表情如 char_charlie_smile）
【插图】xxx.jpg     全屏CG（assets/cg/）
【音乐】bgm_xxx     切换BGM（assets/audio/bgm/scan/ 文件名，"无"=停止）
【音效】sfx_xxx     播放音效（assets/audio/sfx/）
【转场】            黑场转场：清空立绘和CG
【标签】xx / 【跳转】xx   分支跳转
【选择】甲:标签A|乙:标签B  选项（跳到对应标签）
角色名|台词         名牌+台词；普通文本=旁白

引擎按行解析；改完保存重开游戏生效。
""")
print("完成")
