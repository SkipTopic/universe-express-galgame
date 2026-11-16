# -*- coding: utf-8 -*-
"""小说单独提取：从212页转写里抽出小说内容，输出干净docx到 单独提取出来的小说\
1) 宇宙快递员·正文.docx      —— 143250→145902 连续61页正文，连读无页标题，含船上图纸/游园会地图插图
2) 宇宙快递员·设定与草稿.docx —— 人设卡、修改清单、草稿碎片、大致走向提纲
3) 早期构思集.docx            —— 宝剑与软肋、杀手起源、间谍学校等早期小说点子
清洗规则与网页一致：无任何识别标记，划掉内容不显示，红/蓝墨水还原为字色，保留手写换行。
"""
import os, re, sys
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
OCR = os.path.join(BASE, "工作区域", "OCR文本")
CROP = os.path.join(BASE, "工作区域", "裁剪图片")
ORDER = os.path.join(BASE, "工作区域", "页序.txt")
OUT = os.path.join(BASE, "单独提取出来的小说")
os.makedirs(OUT, exist_ok=True)

C_PRIMARY = RGBColor(0x10, 0x18, 0x20)
C_BODY    = RGBColor(0x18, 0x20, 0x30)
C_GRAY    = RGBColor(0x50, 0x60, 0x70)
C_META    = RGBColor(0x8a, 0x82, 0x74)
COLORS    = {"": C_BODY, "r": RGBColor(0xB3, 0x36, 0x2C), "b": RGBColor(0x2F, 0x5D, 0xA8), "p": RGBColor(0x8F, 0x89, 0x7C)}

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

def clean_segments(s):
    """一行 → [(文字, 颜色)]；无任何标记残留"""
    s = pinyin_preclean(s)
    def ann_sub(m):
        content = m.group(1).strip()
        if not content or PINYIN_OK.match(content):
            return ""
        return content if len(content) <= 6 else ""
    s = RE_ANN.sub(ann_sub, s)
    s = RE_UNK.sub("", s)
    segs = line_segments(s, strip_meta=True)
    return segs

def page_blocks(stem, keep_fig_text=False):
    """页 → 块列表；keep_fig_text=False 时图注描述不出现，插图在原位"""
    path = os.path.join(OCR, stem + ".md")
    raw_lines = open(path, encoding="utf-8").read().splitlines()
    cleaned, full_fig, has_fig = strip_figures(raw_lines)
    blocks = []
    for ln_no, ctext in cleaned:
        s = ctext.strip()
        if ln_no in full_fig:
            if (stem, ln_no) in crop_map:
                blocks.append({"t": "img", "src": crop_map[(stem, ln_no)]})
            continue
        if not s or s.startswith("# "):
            continue
        if re.match(r"^Subject[.．]?\s*Date", s) or re.match(r"^(Subject|Date)[.．]\s*$", s):
            continue                       # 本子印刷抬头误入正文
        if s.startswith(("〔拍摄：", "〔本页状态：", "〔页面信息：", "〔备注：", "〔整行划掉")):
            continue
        if re.match(r"^(纸片\d*｜|｜|图旁|（以上)", s):
            continue
        m = re.match(r"^[^：]{0,24}?(红字|红笔|蓝字|蓝笔|黑笔)批注[^：]*[:：](.+)$", s)
        if m:
            col = "b" if "蓝" in m.group(1) else "r"
            s = ("〔红笔〕" if col == "r" else "〔蓝笔〕") + m.group(2)
        segs = clean_segments(s)
        if segs:
            blocks.append({"t": "p", "s": segs})
        if (stem, ln_no) in crop_map:
            blocks.append({"t": "img", "src": crop_map[(stem, ln_no)]})
    return blocks

def set_ea(style_or_run, ea_font):
    rPr = style_or_run.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts'); rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), ea_font)

def new_doc():
    doc = Document()
    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'; normal.font.size = Pt(12); normal.font.color.rgb = C_BODY
    set_ea(normal, '宋体')
    normal.paragraph_format.line_spacing = 1.4
    normal.paragraph_format.space_after = Pt(2)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2.3)
    sec.left_margin = sec.right_margin = Cm(2.6)
    return doc

def add_footer_pagenum(doc):
    sec = doc.sections[0]
    fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = " PAGE \\* arabic \\* MERGEFORMAT "
    f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'end')
    run._r.append(f1); run._r.append(it); run._r.append(f2)
    run.font.size = Pt(9); run.font.color.rgb = C_GRAY

def cover(doc, title, sub, notes):
    secPr = doc.sections[0]._sectPr
    va = OxmlElement('w:vAlign'); va.set(qn('w:val'), 'center'); secPr.append(va)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(16)
    r = p.add_run(title); r.font.size = Pt(30); r.bold = True
    r.font.color.rgb = C_PRIMARY; set_ea(r, '黑体'); r.font.name = 'Calibri'
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(46)
    r = p.add_run(sub); r.font.size = Pt(14); r.font.color.rgb = C_GRAY
    set_ea(r, '宋体'); r.font.name = 'Calibri'
    for t in notes:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(7)
        r = p.add_run(t); r.font.size = Pt(11.5); r.font.color.rgb = C_META
        set_ea(r, '宋体'); r.font.name = 'Calibri'

def emit_blocks(doc, blocks):
    for b in blocks:
        if b["t"] == "p":
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.4
            p.paragraph_format.space_after = Pt(2)
            for text, c in b["s"]:
                r = p.add_run(text)
                r.font.size = Pt(12); r.font.color.rgb = COLORS.get(c, C_BODY)
                set_ea(r, '宋体'); r.font.name = 'Calibri'
        elif b["t"] == "img":
            path = os.path.join(CROP, b["src"])
            if not os.path.exists(path): continue
            with Image.open(path) as im: w0, h0 = im.size
            aspect = h0 / w0
            disp_h = min(10.5, 13.2 * aspect)
            disp_w = disp_h / aspect if aspect else 13.2
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(6)
            run = p.add_run()
            run.add_picture(path, width=Cm(disp_w))

def page_ref(doc, stem):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14); p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f"· 原稿 {stem} ·")
    r.font.size = Pt(9); r.italic = True; r.font.color.rgb = C_META
    set_ea(r, '宋体'); r.font.name = 'Calibri'

order = [l.strip() for l in open(ORDER, encoding="utf-8") if l.strip()]
order_stems = [p.rsplit(".", 1)[0] for p in order]
def tail6(s): return s[-6:]

NOVEL_BODY = [s for s in order_stems if tail6(s) in
    {"143250","143309","143320","143338","143348","143417","143426","143439",
     "143449","143501","143510","143533","143545","143559","144434","144446",
     "144456","144513","144523","144706","144717","144734","144752","144811",
     "144826","144920","144934","144950","145046","145109","145124","145142",
     "145154","145210","145222","145237","145248","145302","145317","145334",
     "145345","145402","145416","145433","145443","145501","145512","145527",
     "145539","145623","145700","145712","145721","145733","145744","145755",
     "145804","145816","145823","145840","145853","145902"}]
NOVEL_PREP = [s for s in order_stems if tail6(s) in
    {"142829","142847","142911","143015","143026","143040"}]
EARLY = [s for s in order_stems if tail6(s) in
    {"180358","180413","181026","181032","181041","181119","181131",
     "115458","120401","140812","141236","141521","121459","121448"}]
print("正文页数:", len(NOVEL_BODY), "| 设定草稿:", len(NOVEL_PREP), "| 早期构思:", len(EARLY))

# ── 1) 正文 ──
doc = new_doc()
cover(doc, "宇宙快递员",
      "长篇小说原稿 · 连读复刻版",
      ["写作时间：2023 年 6 月（写于手写日记本）",
       "正文共 61 页原稿，按写作顺序连排",
       "红字/蓝字为原稿墨色；被划掉的字句未收录；插图取自原稿"])
add_footer_pagenum(doc)
doc.add_page_break()
for stem in NOVEL_BODY:
    emit_blocks(doc, page_blocks(stem))
out1 = os.path.join(OUT, "宇宙快递员·正文.docx")
doc.save(out1); print("saved", out1)

# ── 2) 设定与草稿 ──
doc = new_doc()
cover(doc, "宇宙快递员 · 设定与草稿",
      "人设卡 · 修改清单 · 走向提纲",
      ["正稿动笔前的准备材料，与《宇宙快递员·正文》配套阅读"])
add_footer_pagenum(doc)
doc.add_page_break()
for stem in NOVEL_PREP:
    page_ref(doc, stem)
    emit_blocks(doc, page_blocks(stem))
out2 = os.path.join(OUT, "宇宙快递员·设定与草稿.docx")
doc.save(out2); print("saved", out2)

# ── 3) 早期构思集 ──
doc = new_doc()
cover(doc, "早期构思集",
      "宝剑与软肋的开头 · 杀手起源 · 间谍学校 · 另一个世界的结局",
      ["正式的长篇动笔之前，散落在日记本里的小说点子与片段"])
add_footer_pagenum(doc)
doc.add_page_break()
for stem in EARLY:
    page_ref(doc, stem)
    emit_blocks(doc, page_blocks(stem))
out3 = os.path.join(OUT, "早期构思集.docx")
doc.save(out3); print("saved", out3)
print("全部输出到", OUT)
