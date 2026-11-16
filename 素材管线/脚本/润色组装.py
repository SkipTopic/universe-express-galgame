# -*- coding: utf-8 -*-
"""润色版组装：12章 → 《宇宙快递员·正文（润色版）》，每章另起一页。"""
import os, re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image

BASE = r"D:\我的godot项目\小时候的小说"
RUN = os.path.join(BASE, "工作区域", "润色")
CROP = os.path.join(BASE, "工作区域", "裁剪图片")
OUT = os.path.join(BASE, "单独提取出来的小说", "宇宙快递员·正文.docx")

C_PRIMARY = RGBColor(0x10, 0x18, 0x20)
C_BODY    = RGBColor(0x18, 0x20, 0x30)
C_GRAY    = RGBColor(0x50, 0x60, 0x70)
C_META    = RGBColor(0x8a, 0x82, 0x74)

def set_ea(style_or_run, ea_font):
    rPr = style_or_run.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts'); rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), ea_font)

doc = Document()
normal = doc.styles['Normal']
normal.font.name = 'Calibri'; normal.font.size = Pt(12); normal.font.color.rgb = C_BODY
set_ea(normal, '宋体')
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(3)

h1 = doc.styles['Heading 1']
h1.font.name = 'Calibri'; h1.font.size = Pt(20); h1.bold = True
h1.font.color.rgb = C_PRIMARY; set_ea(h1, '黑体')
h1.paragraph_format.page_break_before = True
h1.paragraph_format.space_before = Pt(0)
h1.paragraph_format.space_after = Pt(18)
h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.3)
sec.left_margin = sec.right_margin = Cm(2.6)

fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fp.add_run()
f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin')
it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = " PAGE \\* arabic \\* MERGEFORMAT "
f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'end')
run._r.append(f1); run._r.append(it); run._r.append(f2)
run.font.size = Pt(9); run.font.color.rgb = C_GRAY

# ── 封面 ──
secPr = sec._sectPr
va = OxmlElement('w:vAlign'); va.set(qn('w:val'), 'center'); secPr.append(va)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(16)
r = p.add_run("宇宙快递员"); r.font.size = Pt(36); r.bold = True
r.font.color.rgb = C_PRIMARY; set_ea(r, '黑体'); r.font.name = 'Calibri'
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(50)
r = p.add_run("润 色 版"); r.font.size = Pt(16); r.font.color.rgb = C_GRAY
set_ea(r, '宋体'); r.font.name = 'Calibri'
for t in ["共十二章 · 五万余字", "写作时间：2023 年 6 月（写于手写日记本）", "整理完成：2026 年 10 月"]:
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(7)
    r = p.add_run(t); r.font.size = Pt(11.5); r.font.color.rgb = C_META
    set_ea(r, '宋体'); r.font.name = 'Calibri'

# ── 润色说明 ──
p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(24); p.paragraph_format.space_after = Pt(12)
r = p.add_run("整理说明"); r.font.size = Pt(20); r.bold = True
r.font.color.rgb = C_PRIMARY; set_ea(r, '黑体'); r.font.name = 'Calibri'
for t in [
    "全文按故事进展分为十二章，每章另起一页。",
    "润色仅限：修正错别字与笔误、规范标点与引号、合并手写碎行为段落、轻微顺平语病。",
    "情节、对话、设定与作者的叙事口吻未做任何改动；插叙与反转均为作者原设计。",
    "人物名前后不一致处已统一（李尊→李磊）。",
    "原稿逐字复刻见《小时候的日记-OCR复刻版》；网页版《我的日记》可按页对照原图。",
    "插图两处取自原稿：飞船 Gone-3 平面图（第二章）、游园会全景地图（第六章）。",
]:
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6); p.paragraph_format.line_spacing = 1.4
    r = p.add_run("· " + t); r.font.size = Pt(11.5); r.font.color.rgb = C_BODY
    set_ea(r, '宋体'); r.font.name = 'Calibri'

NUM_CN = {1:"一",2:"二",3:"三",4:"四",5:"五",6:"六",7:"七",8:"八",9:"九",10:"十",11:"十一",12:"十二"}

def add_para(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text); r.font.size = Pt(12); r.font.color.rgb = C_BODY
    set_ea(r, '宋体'); r.font.name = 'Calibri'

def add_image(fn):
    path = os.path.join(CROP, fn)
    if not os.path.exists(path): return
    with Image.open(path) as im: w0, h0 = im.size
    aspect = h0 / w0
    disp_h = min(10.5, 13.2 * aspect)
    disp_w = disp_h / aspect if aspect else 13.2
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(8)
    run = p.add_run()
    run.add_picture(path, width=Cm(disp_w))

total_chars = 0
for num in range(1, 13):
    path = os.path.join(RUN, f"ch{num:02d}_p.md")
    lines = [l.rstrip() for l in open(path, encoding="utf-8").read().splitlines()]
    lines = [l for l in lines if l.strip() and not re.match(r"^Subject[.．]?\s*Date", l.strip())]
    header = lines[0].strip() if lines else f"第{NUM_CN[num]}章"
    # 标题改用中文数字
    header = re.sub(r"^第\d+章", f"第{NUM_CN[num]}章", header)
    h = doc.add_paragraph(style='Heading 1')
    r = h.add_run(header); r.font.size = Pt(20); r.bold = True
    r.font.color.rgb = C_PRIMARY; set_ea(r, '黑体'); r.font.name = 'Calibri'
    for l in lines[1:]:
        s = l.strip()
        m = re.match(r"^\[插图：(.+?)\]$", s)
        if m:
            add_image(m.group(1)); continue
        s = s.replace("〔", "").replace("〕", "")
        if not s: continue
        total_chars += len(s)
        add_para(s)

doc.save(OUT)
print("saved", OUT, "| 正文字数:", total_chars)
