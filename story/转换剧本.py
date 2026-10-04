# -*- coding: utf-8 -*-
"""step02: 把润色后的12章小说转换成游戏剧本 story/chXX.txt
格式（纯文本，记事本可编辑）：
  【背景】bg_xxx          切换背景
  【立绘】char_xxx        显示立绘（我=主角不显示立绘）
  【插图】crop_xxx.jpg    全屏CG
  【选择】选项A|选项B     选项（|分隔，暂存扩展）
  角色名|台词             有名字牌的台词
  普通文本                旁白
"""
import os, re

BASE = r"D:\我的godot项目\小时候的小说"
RUN = os.path.join(BASE, "工作区域", "润色")
STORY = os.path.join(BASE, "godot项目galgame", "story")
os.makedirs(STORY, exist_ok=True)

CHAPTERS = [
    (1,  "战争结束", "bg_battlefield"),
    (2,  "晓琳", "bg_hq"),
    (3,  "老船长的故事", "bg_ship_corridor"),
    (4,  "登船", "bg_deadplanet"),
    (5,  "死亡星球与伊甸园", "bg_deadplanet"),
    (6,  "凯特星之夜", "bg_nightmarket"),
    (7,  "口琴与往事", "bg_hospital"),
    (8,  "营救", "bg_street_night"),
    (9,  "B65楼", "bg_corridor_b65"),
    (10, "晓琳之死", "bg_corridor_b65"),
    (11, "核弹与梦醒", "bg_space"),
    (12, "尾声", "bg_street_night"),
]
# 说话人名字 → 立绘
SPRITES = {
    "查理": "char_charlie", "晓琳": "char_xiaolin", "照片": "char_photo",
    "毕福吉": "char_bi", "华福吉": "char_bi", "李磊": "char_lilei",
    "希朗首长": "char_xilang", "老船长": "char_charlie",
}
NAME_CHARS = sorted(SPRITES.keys(), key=len, reverse=True)

def detect_speaker(par):
    """从段落里识别说话人：X：“…” / X说：“…” / X喊道：“…”"""
    for name in NAME_CHARS:
        for pat in (name + "：", name + ":", name + "说：", name + "说:", name + "道：",
                    name + "喊道：", name + "问道：", name + "心想："):
            if par.startswith(pat):
                return name, par[len(pat):].strip()
    for name in NAME_CHARS:
        m = re.search(re.escape(name) + r"[^，。！？”]{0,6}[:：]\s*", par)
        if m and m.start() < 20:
            rest = par[m.end():].strip()
            return name, rest
    return None, None

def convert(num, ctitle, bg):
    src = os.path.join(RUN, f"ch{num:02d}_p.md")
    paras = [l.strip() for l in open(src, encoding="utf-8").read().splitlines() if l.strip()]
    header = paras[0]  # 第N章 标题
    out = [f"【章节】{header}", f"【背景】{bg}"]
    cur_sprite = ""
    cur_speaker = ""
    for par in paras[1:]:
        if re.match(r"^Subject", par):
            continue
        m = re.match(r"^\[插图：(.+?)\]$", par)
        if m:
            out.append(f"【插图】{m.group(1)}")
            continue
        is_quote = par.startswith("“") or par.startswith('"') or par.startswith("”")
        name, line = detect_speaker(par)
        if name is None and is_quote and cur_speaker:
            name, line = cur_speaker, par
        if name:
            if not is_quote:
                line = par
            sp = SPRITES.get(name)
            if sp and sp != cur_sprite:
                out.append(f"【立绘】{sp}")
                cur_sprite = sp
            cur_speaker = name
            out.append(f"{name}|{line}")
        else:
            last = ""
            for nm in NAME_CHARS:
                idx = par.rfind(nm)
                if idx >= 0:
                    last = nm
            if last:
                cur_speaker = last
            out.append(par)
    path = os.path.join(STORY, f"ch{num:02d}.txt")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    n_dialog = sum(1 for l in out if "|" in l and not l.startswith("【"))
    print(f"ch{num:02d} {ctitle}: {len(out)}行（台词{n_dialog}）")

for num, ctitle, bg in CHAPTERS:
    convert(num, ctitle, bg)

open(os.path.join(STORY, "格式说明.txt"), "w", encoding="utf-8").write(
"""游戏剧本格式说明（记事本直接改，保存即可生效）

【背景】bg_xxx        切换背景图（assets/sprites/bg/ 里的文件名，不带.png）
【立绘】char_xxx      显示立绘（assets/sprites/characters/ 文件名；写【立绘】无 会隐藏）
【插图】crop_xxx.jpg  全屏CG（assets/cg/ 文件名）
【选择】选项甲|选项乙  出现选项按钮（暂存扩展，当前版本选择后继续原剧情）
角色名|台词           显示名牌+台词（角色名可用：查理/晓琳/照片/毕福吉/李磊/希朗首长/老船长/我）
普通文本              旁白（无名牌）

规则：
- 引擎按行解析，一行一个指令；空行忽略
- 【立绘】char_me 是主角本人（主角不显示立绘，写【立绘】无 可清空立绘）
- 改完保存，重新运行游戏即生效（无需进编辑器）
""")
print("格式说明已写入")
