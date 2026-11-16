# -*- coding: utf-8 -*-
"""辨认手册生成器：把 看不清内容清单.md 的 1046 条存疑按页配上原图，
分成 6 册 Word 放到 待辨认\，供用户对着照片直接填写"你的辨认"。"""
import os, re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image
import tempfile

BASE = r"D:\我的godot项目\小时候的小说"
CAM = os.path.join(BASE, "素材", "Camera")
LIST_MD = os.path.join(BASE, "工作区域", "待辨认", "看不清内容清单.md")
OUT_DIR = os.path.join(BASE, "工作区域", "待辨认")

C_PRIMARY = RGBColor(0x10, 0x18, 0x20)
C_BODY    = RGBColor(0x18, 0x20, 0x30)
C_GRAY    = RGBColor(0x50, 0x60, 0x70)
C_FILL    = RGBColor(0xB0, 0x30, 0x30)

def set_ea(style_or_run, ea_font):
    rPr = style_or_run.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts'); rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), ea_font)

# ── 直接从 OCR 源文件提取（编号逻辑与原清单一致，#号不变）──
import glob
pat_guess = re.compile(r'\(\?\)')
pat_unknown = re.compile(r'〔\?〕')
pat_crossed = re.compile(r'〔划：\?〕|〔整行划掉：\?〕')
with open(os.path.join(BASE, "工作区域", "图片清单.txt"), encoding='utf-8') as f:
    photos_all = [l.strip() for l in f if l.strip()]
pages = []
g = 0
for stem_full in photos_all:
    stem = stem_full.rsplit('.', 1)[0]
    p = os.path.join(OCR文本 := os.path.join(BASE, "工作区域", "OCR文本"), stem + ".md")
    if not os.path.exists(p):
        continue
    entries = []
    for line in open(p, encoding='utf-8'):
        s = line.strip()
        if not s or s.startswith('# '):
            continue
        kinds = []
        if pat_guess.search(s): kinds.append('猜测(?)')
        if pat_unknown.search(s): kinds.append('认不出〔?〕')
        if pat_crossed.search(s): kinds.append('涂黑不可辨')
        if kinds:
            g += 1
            entries.append((g, '/'.join(kinds), s))
    if entries:
        pages.append((stem, entries))
total = sum(len(e) for _, e in pages)
print(f"提取：{len(pages)} 页，{total} 条")

# ── 分册 ──
N_VOL = 6
per = (len(pages) + N_VOL - 1) // N_VOL
vols = [pages[i:i+per] for i in range(0, len(pages), per)]

tmpdir = tempfile.mkdtemp(prefix="manual_")
for vi, vol in enumerate(vols, 1):
    doc = Document()
    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'; normal.font.size = Pt(11); normal.font.color.rgb = C_BODY
    set_ea(normal, '宋体')
    normal.paragraph_format.line_spacing = 1.25
    h1 = doc.styles['Heading 1']
    h1.font.name = 'Calibri'; h1.font.size = Pt(14); h1.bold = True
    h1.font.color.rgb = C_PRIMARY; set_ea(h1, '黑体')
    h1.paragraph_format.page_break_before = True

    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = sec2_m = Cm(1.8); sec.bottom_margin = Cm(1.8)
    sec.left_margin = sec.right_margin = Cm(2.0)

    # 封面/用法说明（每册都带，防止用户只拿到一册）
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(30)
    r = p.add_run(f"看不清内容 · 辨认手册（第 {vi} / {len(vols)} 册）")
    r.font.size = Pt(22); r.bold = True; r.font.color.rgb = C_PRIMARY
    set_ea(r, '黑体'); r.font.name = 'Calibri'
    intro = [
        "本册收录本子里 AI 拿不准的字词，每页上方是当时的原始照片，下方列出该页存疑条目。",
        "用法一（推荐）：直接在本文档每条红色「你的辨认：＿＿＿」后面打字填上正确内容，保存后把文件交给 AI。",
        "用法二：口头/留言告诉 AI 编号和内容，如「第 12 条是烫伤的烫」「#87 到 #90 都不用改」。",
        "编号规则：#编号与《看不清内容清单.md》完全一致；填完的条目 AI 会按编号替换回正文并重新生成 Word/PDF。",
        "类型说明：「猜测(?)」=AI 猜过但没把握，请确认或纠正；「认不出〔?〕」=完全认不出，请直接告知；「涂黑不可辨」=原文被作者自己涂掉，可填可不填。",
        "看不清照片上的字时，可以用鼠标滚轮放大照片所在页，或对照原高清照片：素材\\Camera\\对应文件名.jpg。",
    ]
    for t in intro:
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(8); p.paragraph_format.line_spacing = 1.3
        r = p.add_run("· " + t); r.font.size = Pt(11); r.font.color.rgb = C_BODY
        set_ea(r, '宋体'); r.font.name = 'Calibri'

    for stem, entries in vol:
        h = doc.add_paragraph(style='Heading 1')
        r = h.add_run(stem); r.font.size = Pt(14); r.bold = True
        r.font.color.rgb = C_PRIMARY; set_ea(r, '黑体'); r.font.name = 'Calibri'

        # 原图（缩到宽1000px临时jpg，控制文件体积）
        src = os.path.join(CAM, stem + ".jpg")
        if os.path.exists(src):
            im = Image.open(src); im.thumbnail((1000, 1000), Image.LANCZOS)
            tmp = os.path.join(tmpdir, stem + ".jpg")
            im.convert("RGB").save(tmp, quality=78)
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(8)
            run = p.add_run(); run.add_picture(tmp, width=Cm(12.5))

        for no, kind, text in entries:
            p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(0)
            r = p.add_run(f"#{no}　〔{kind}〕")
            r.font.size = Pt(11); r.bold = True; r.font.color.rgb = C_PRIMARY
            set_ea(r, '黑体'); r.font.name = 'Calibri'
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0)
            r = p.add_run("原行：" + (text or "")); r.font.size = Pt(10.5); r.font.color.rgb = C_BODY
            set_ea(r, '宋体'); r.font.name = 'Calibri'
            p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(4)
            r = p.add_run("你的辨认：＿＿＿＿＿＿＿＿＿＿＿＿")
            r.font.size = Pt(11); r.bold = True; r.font.color.rgb = C_FILL
            set_ea(r, '宋体'); r.font.name = 'Calibri'

    out = os.path.join(OUT_DIR, f"辨认手册第{vi}册.docx")
    doc.save(out)
    print("已生成", out, f"（{len(vol)} 页，{sum(len(e[1]) for e in vol)} 条）")

import shutil
shutil.rmtree(tmpdir, ignore_errors=True)
print("全部完成")
