# -*- coding: utf-8 -*-
"""小时候的日记本 OCR 复刻 Word 生成器（双版本）
1) 纯文字版：小时候的日记-OCR复刻版.docx
2) 带图版  ：小时候的日记-OCR复刻版-带图版.docx（在〔图〕标注后插入对应裁剪图+灰色图注）
页序来源：工作区域\\页序.txt（若存在，按内容连贯性重排后的顺序）；否则按 图片清单.txt（拍摄顺序）。
"""
import os, re, sys, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 颜色分段 import line_segments, strip_figures
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image

BASE = r"D:\我的godot项目\小时候的小说"
OCR_DIR = os.path.join(BASE, "工作区域", "OCR文本")
CROP_DIR = os.path.join(BASE, "工作区域", "裁剪图片")
LIST_TXT = os.path.join(BASE, "工作区域", "图片清单.txt")
ORDER_TXT = os.path.join(BASE, "工作区域", "页序.txt")
OUT_DIR = os.path.join(BASE, "素材")
COPY_DIR = os.path.join(BASE, "工作区域", "完整日记word输出")

# ── 调色 ──
C_PRIMARY = RGBColor(0x10, 0x18, 0x20)
C_BODY    = RGBColor(0x18, 0x20, 0x30)
C_GRAY    = RGBColor(0x50, 0x60, 0x70)
C_META    = RGBColor(0x70, 0x70, 0x70)

ANN_RE = re.compile(r"(〔[^〕]*〕)")
WORD_COLORS = {"": C_BODY, "r": RGBColor(0xB3, 0x36, 0x2C), "b": RGBColor(0x2F, 0x5D, 0xA8), "p": RGBColor(0x8F, 0x89, 0x7C)}

def set_ea(style_or_run, ea_font):
    rPr = style_or_run.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts'); rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), ea_font)

def add_runs_with_ann(par, text, base_color=C_BODY, ann_color=C_GRAY, size=Pt(12), bold=False):
    for seg in ANN_RE.split(text):
        if not seg:
            continue
        r = par.add_run(seg)
        r.font.size = size
        r.font.color.rgb = ann_color if seg.startswith("〔") else base_color
        r.bold = bold
        if seg.startswith("〔"):
            r.italic = True

def read_order():
    if os.path.exists(ORDER_TXT):
        with open(ORDER_TXT, encoding='utf-8') as f:
            photos = [l.strip() for l in f if l.strip()]
        print(f"页序来源：页序.txt（重排版，{len(photos)}项）")
        return photos
    with open(LIST_TXT, encoding='utf-8') as f:
        photos = [l.strip() for l in f if l.strip()]
    print(f"页序来源：图片清单.txt（拍摄顺序，{len(photos)}项）")
    return photos

def load_crop_map():
    """(stem, lineno) -> (seq_no, filename, desc)"""
    m = {}
    idx_path = os.path.join(CROP_DIR, "_索引.txt")
    with open(idx_path, encoding='utf-8') as f:
        for line in f:
            parts = line.split()
            if len(parts) < 4:
                continue
            no = int(parts[0][1:])
            stem, lineno, fn = parts[1], int(parts[2][1:]), parts[3]
            desc = line.split("|", 1)[1].strip() if "|" in line else ""
            m[(stem, lineno)] = (no, fn, desc)
    return m

# ══════════ 文档构建 ══════════

def build_doc(illustrated, crop_map, photos, out_path):
    doc = Document()

    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'; normal.font.size = Pt(12)
    normal.font.color.rgb = C_BODY
    set_ea(normal, '宋体')
    pf = normal.paragraph_format
    pf.line_spacing = 1.3
    pf.space_after = Pt(2)

    h1 = doc.styles['Heading 1']
    h1.font.name = 'Calibri'; h1.font.size = Pt(15); h1.bold = True
    h1.font.color.rgb = C_PRIMARY
    set_ea(h1, '黑体')
    h1.paragraph_format.page_break_before = True
    h1.paragraph_format.space_before = Pt(0)
    h1.paragraph_format.space_after = Pt(10)
    h1.paragraph_format.keep_with_next = True

    sec1 = doc.sections[0]
    sec1.page_width, sec1.page_height = Cm(21.0), Cm(29.7)
    sec1.top_margin = sec1.bottom_margin = Cm(2.0)
    sec1.left_margin = sec1.right_margin = Cm(2.4)

    sectPr = sec1._sectPr
    vAlign = OxmlElement('w:vAlign'); vAlign.set(qn('w:val'), 'center')
    sectPr.append(vAlign)

    # ── 封面 ──
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)
    r = p.add_run("小时候的日记本"); r.font.size = Pt(34); r.bold = True
    r.font.color.rgb = C_PRIMARY; set_ea(r, '黑体'); r.font.name = 'Calibri'

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(60)
    sub = "手写日记 OCR 忠实复刻版 · 带图版" if illustrated else "手写日记 OCR 忠实复刻版"
    r = p.add_run(sub); r.font.size = Pt(16); r.font.color.rgb = C_GRAY
    set_ea(r, '宋体'); r.font.name = 'Calibri'

    for label, val in [
        ("素材来源", "素材\\Camera（212 张照片）"),
        ("拍摄时间", "2023 年 6 月 25 日 — 26 日"),
        ("复刻方式", "AI 逐页识别，忠实保留原文（含错别字、涂改、拼音与涂鸦说明）"),
        ("页面顺序", "按内容连贯性重排（页标题保留照片文件名可对照原图）"),
        ("复刻完成", "2026 年 10 月 4 日"),
    ]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(f"{label}｜{val}"); r.font.size = Pt(12)
        r.font.color.rgb = C_META; set_ea(r, '宋体'); r.font.name = 'Calibri'

    # ── 第二节：说明页 + 正文 ──
    sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
    sec2.top_margin = sec2.bottom_margin = Cm(2.0)
    sec2.left_margin = sec2.right_margin = Cm(2.4)
    pgNumType = OxmlElement('w:pgNumType'); pgNumType.set(qn('w:start'), '1')
    sec2._sectPr.append(pgNumType)
    sec2.footer.is_linked_to_previous = False
    fp = sec2.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    fld1 = OxmlElement('w:fldChar'); fld1.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = " PAGE \\* arabic \\* MERGEFORMAT "
    fld2 = OxmlElement('w:fldChar'); fld2.set(qn('w:fldCharType'), 'end')
    run._r.append(fld1); run._r.append(instr); run._r.append(fld2)
    run.font.size = Pt(9); run.font.color.rgb = C_GRAY

    def body_par(text, size=Pt(12), color=C_BODY, italic=False, ea='宋体',
                 align=None, before=0, after=2):
        p = doc.add_paragraph()
        if align: p.alignment = align
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.3
        if text:
            r = p.add_run(text)
            r.font.size = size; r.font.color.rgb = color; r.italic = italic
            set_ea(r, ea); r.font.name = 'Calibri'
        return p

    def add_figure(stem, ln_no):
        """插入裁剪图+灰图注；返回是否真的插入了"""
        if (stem, ln_no) not in crop_map:
            return False
        no, fn, desc = crop_map[(stem, ln_no)]
        img_path = os.path.join(CROP_DIR, fn)
        if not os.path.exists(img_path):
            return False
        with Image.open(img_path) as im:
            w0, h0 = im.size
        aspect = h0 / w0
        disp_h_cm = min(11.0, 13.5 * aspect)
        disp_w_cm = disp_h_cm / aspect if aspect else 13.5
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(2)
        run = p.add_run()
        run.add_picture(img_path, width=Cm(disp_w_cm))
        cap = body_par("", after=8)
        r = cap.add_run(f"▲ 裁剪插图 #{no:03d}")
        r.font.size = Pt(9); r.italic = True; r.font.color.rgb = C_GRAY
        set_ea(r, '宋体'); r.font.name = 'Calibri'
        return True

    # ── 说明页 ──
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(24); p.paragraph_format.space_after = Pt(12)
    r = p.add_run("使用说明 · 转写符号"); r.font.size = Pt(20); r.bold = True
    r.font.color.rgb = C_PRIMARY; set_ea(r, '黑体'); r.font.name = 'Calibri'

    notes = [
        ("页标题", "每页标题的序号即本册排列顺序，后附照片文件名，可与原图一一对照。"),
        ("(?)", "该字结合上下文猜测辨认，把握不大。"),
        ("〔?〕", "完全无法辨认的单个字或词。"),
        ("〔划：××〕", "作者自己写错后划掉的内容，按原样保留。"),
        ("〔整行划掉：××〕", "整行被划掉，××为可辨认的部分。"),
        ("〔上注〕〔下注〕", "写在行上方/下方的小字批注（拼音、补字等）。"),
        ("〔图｜位置：描述〕", "手绘涂鸦、插图的位置与内容说明。"),
        ("[右对齐]", "原文靠页面右侧书写。"),
        ("〔页面信息〕", "笔记本印刷抬头、纸张状态等背景信息，非手写内容。"),
        ("透印字迹", "纸张背面透过来的反字一律未计入正文。"),
        ("重要原则", "所有错别字、病句、拼音、英文均按原文保留，未做任何修改润色。"),
    ]
    if illustrated:
        notes.append(("带图版说明", "灰色『▲ 裁剪插图 #N』图注下方为本子上的原画裁剪，与〔图〕说明对应；全本共 194 张裁剪图。"))
    for term, expl in notes:
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6); p.paragraph_format.line_spacing = 1.3
        r = p.add_run(f"{term}　")
        r.font.size = Pt(12); r.bold = True; r.font.color.rgb = C_PRIMARY; set_ea(r, '黑体'); r.font.name = 'Calibri'
        r = p.add_run(expl)
        r.font.size = Pt(12); r.font.color.rgb = C_BODY; set_ea(r, '宋体'); r.font.name = 'Calibri'

    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(18); p.paragraph_format.line_spacing = 1.3
    r = p.add_run("全本共 212 张照片，其中 1 组为同一页的两次拍摄（121031 与 121048，正文以 121048 为准，121031 补充记录了另一角度可见的插画），其余 211 张均为独立页面。")
    r.font.size = Pt(11); r.font.color.rgb = C_GRAY; set_ea(r, '宋体'); r.font.name = 'Calibri'; r.italic = True

    # ── 正文 ──
    n_fig = 0
    for idx, photo in enumerate(photos, 1):
        stem = photo.rsplit(".", 1)[0]
        md = os.path.join(OCR_DIR, stem + ".md")
        if not os.path.exists(md):
            print(f"[缺失] {md}", file=sys.stderr); continue
        with open(md, encoding='utf-8') as f:
            lines = [l.rstrip("\n") for l in f]

        h = doc.add_paragraph(style='Heading 1')
        r = h.add_run(f"{idx:03d} · {stem}")
        r.font.size = Pt(15); r.bold = True; r.font.color.rgb = C_PRIMARY
        set_ea(r, '黑体'); r.font.name = 'Calibri'

        cleaned, full_fig, has_fig = strip_figures(lines)
        for ln_no, ctext in cleaned:
            raw_s = lines[ln_no - 1].strip()
            s = ctext.strip()
            if ln_no in full_fig:
                body_par(raw_s, size=Pt(10.5), color=C_GRAY, italic=True, ea='楷体', after=3)
                if illustrated and add_figure(stem, ln_no): n_fig += 1
                continue
            if not s or s.startswith("# "):
                continue
            if s.startswith("〔拍摄：") or s.startswith("〔本页状态：") or s.startswith("〔页面信息："):
                body_par(s, size=Pt(9), color=C_META, italic=True, after=1)
                continue
            if re.match(r"^[（(](?:红|蓝|黑)[笔字]", s) and re.search(r"框住|箭头|指向|批注|标注", s):
                continue
            if s.startswith("〔图"):
                body_par(s, size=Pt(10.5), color=C_GRAY, italic=True, ea='楷体', after=3)
            elif s.startswith("[右对齐]"):
                p = body_par("", after=2)
                for seg_text, seg_c in line_segments(s):
                    add_runs_with_ann(p, seg_text, base_color=WORD_COLORS.get(seg_c, C_BODY))
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            else:
                p = body_par("", after=2)
                for seg_text, seg_c in line_segments(s):
                    add_runs_with_ann(p, seg_text, base_color=WORD_COLORS.get(seg_c, C_BODY))
            if illustrated and (stem, ln_no) in crop_map:
                no, fn, desc = crop_map[(stem, ln_no)]
                img_path = os.path.join(CROP_DIR, fn)
                if os.path.exists(img_path):
                    with Image.open(img_path) as im:
                        w0, h0 = im.size
                    aspect = h0 / w0
                    disp_h_cm = min(11.0, 13.5 * aspect)
                    disp_w_cm = disp_h_cm / aspect if aspect else 13.5
                    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(2)
                    run = p.add_run()
                    run.add_picture(img_path, width=Cm(disp_w_cm))
                    cap = body_par("", after=8)
                    r = cap.add_run(f"▲ 裁剪插图 #{no:03d}")
                    r.font.size = Pt(9); r.italic = True; r.font.color.rgb = C_GRAY
                    set_ea(r, '宋体'); r.font.name = 'Calibri'
                    n_fig += 1

    doc.save(out_path)
    tag = "带图版" if illustrated else "纯文字版"
    print(f"已生成{tag}：{out_path}（插图{n_fig}张）")

# ══════════ 主流程 ══════════
if __name__ == "__main__":
    crop_map = load_crop_map()
    photos = read_order()
    out1 = os.path.join(OUT_DIR, "小时候的日记-OCR复刻版.docx")
    out2 = os.path.join(OUT_DIR, "小时候的日记-OCR复刻版-带图版.docx")
    build_doc(False, crop_map, photos, out1)
    build_doc(True, crop_map, photos, out2)
    for f in (out1, out2):
        shutil.copy2(f, os.path.join(COPY_DIR, os.path.basename(f)))
    print("副本已同步到", COPY_DIR)
