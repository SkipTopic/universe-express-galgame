# -*- coding: utf-8 -*-
"""润色准备：把《宇宙快递员》正文62页按章节分组，清洗后导出原始文本供润色。
插图位置以 [插图：文件名] 占位标记，润色时保留原位。"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 颜色分段 import strip_figures, line_segments

BASE = r"D:\我的godot项目\小时候的小说"
OCR = os.path.join(BASE, "工作区域", "OCR文本")
CROP = os.path.join(BASE, "工作区域", "裁剪图片")
OUT = os.path.join(BASE, "工作区域", "润色")
os.makedirs(OUT, exist_ok=True)

crop_map = {}
for line in open(os.path.join(CROP, "_索引.txt"), encoding="utf-8"):
    parts = line.split()
    if len(parts) >= 4:
        crop_map[(parts[1], int(parts[2][1:]))] = parts[3]

RE_CROSS = re.compile(r"〔划：[^〕]*〕|〔涂改〕|〔整行划掉：[^〕]*〕")
RE_ANN   = re.compile(r"〔([上注下]+)：([^〕]*)〕")
RE_UNK   = re.compile(r"〔\?〕|\(\?\)")
PINYIN_OK = re.compile(r"^[A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü\s'·\-]+$")
PINYIN_FIX = {("甲", "kǎi"): "铠", ("软", "lěi"): "肋"}

def pinyin_preclean(s):
    def sub(m):
        ch, py = m.group(1), m.group(2)
        return PINYIN_FIX.get((ch, py), ch)
    return re.sub(r"([\u4e00-\u9fff])〔[上注下]+：([A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]+)〕", sub, s)

def page_lines(stem):
    raw_lines = open(os.path.join(OCR, stem + ".md"), encoding="utf-8").read().splitlines()
    cleaned, full_fig, has_fig = strip_figures(raw_lines)
    out = []
    for ln_no, ctext in cleaned:
        s = ctext.strip()
        if ln_no in full_fig:
            if (stem, ln_no) in crop_map:
                out.append(f"[插图：{crop_map[(stem, ln_no)]}]")
            continue
        if not s or s.startswith("# "):
            continue
        if s.startswith(("〔拍摄：", "〔本页状态：", "〔页面信息：", "〔备注：", "〔整行划掉")):
            continue
        if re.match(r"^(纸片\d*｜|｜|图旁|（以上)", s):
            continue
        m = re.match(r"^[^：]{0,24}?(红字|红笔|蓝字|蓝笔|黑笔)批注[^：]*[:：](.+)$", s)
        if m:
            col = "b" if "蓝" in m.group(1) else "r"
            s = ("〔红笔〕" if col == "r" else "〔蓝笔〕") + m.group(2)
        s = pinyin_preclean(s)
        def ann_sub(m):
            content = m.group(1).strip()
            if not content or PINYIN_OK.match(content):
                return ""
            return content if len(content) <= 6 else ""
        s = RE_ANN.sub(ann_sub, s)
        s = RE_UNK.sub("", s)
        segs = line_segments(s, strip_meta=True)
        if segs:
            out.append("".join(x[0] for x in segs))
        if (stem, ln_no) in crop_map:
            out.append(f"[插图：{crop_map[(stem, ln_no)]}]")
    return out

CHAPTERS = [
    (1,  "战争结束",      ["143250","143309","143320","143338"]),
    (2,  "晓琳",          ["143348","143417","143426","143439"]),
    (3,  "老船长的故事",  ["143449","143501"]),
    (4,  "登船",          ["143510","143533","143545"]),
    (5,  "死亡星球与伊甸园",["143559","144434","144446","144456","144513","144523"]),
    (6,  "凯特星之夜",    ["144706","144717","144734","144752","144811","144826","144920","144934","144950"]),
    (7,  "口琴与往事",    ["145046","145109","145124","145154"]),
    (8,  "营救",          ["145210","145222","145237","145248","145302","145317","145334",
                           "145345","145402","145416","145433","145443","145501","145512"]),
    (9,  "B65楼",         ["145527","145539","145623","145700","145712","145721","145733"]),
    (10, "晓琳之死",      ["145744","145755"]),
    (11, "核弹与梦醒",    ["145804","145816","145823","145840"]),
    (12, "尾声",          ["145853","145902"]),
]

for num, ctitle, tails in CHAPTERS:
    lines = [f"第{num}章 {ctitle}"]
    for t in tails:
        stems = [f[:-3] for f in os.listdir(OCR) if f.endswith(t + ".md")]
        for stem in stems:
            lines.extend(page_lines(stem))
    body = "\n".join(lines)
    path = os.path.join(OUT, f"ch{num:02d}.txt")
    open(path, "w", encoding="utf-8").write(body)
    print(f"ch{num:02d} {ctitle}: {len(body)}字")
