# -*- coding: utf-8 -*-
r'''「我的日记」H5 网页生成器
- 从 OCR文本 提取正文，清洗掉所有识别标记（划掉内容不显示、问号标记去除）
- 拼音批注还原为字（甲+kai→铠），短中文批注按作者插入语还原
- 连续手写行合并成段（原文空行=分段），194张裁剪插图插入对应位置
- 输出：网页index.html（静态壳）+ data.js + images
'''
import os, re, json
from PIL import Image
from 颜色分段 import line_segments, strip_figures

BASE = r"D:\我的godot项目\小时候的小说"
OCR = os.path.join(BASE, "工作区域", "OCR文本")
CROP = os.path.join(BASE, "工作区域", "裁剪图片")
SITE = os.path.join(BASE, "我的日记网页")
IMG_OUT = os.path.join(SITE, "images")

CAT_NOVEL1 = "小说·宇宙快递员"
CAT_NOVEL0 = "小说·早期构思"
CAT_DREAM  = "梦日记"
CAT_GAME   = "游戏设计"
CAT_SONG   = "歌曲与配乐"
CAT_ESSAY  = "作文"
CAT_MISC   = "随笔·杂谈"
CAT_SCRAP  = "碎片·纸片"

OVERRIDES = {}
def ov(cat, *stems):
    for s in stems: OVERRIDES[s] = cat

ov(CAT_NOVEL1, "142829","142847","142911","143015","143026","143040",
   "143250","143309","143320","143338","143348","143417","143426","143439",
   "143449","143501","143510","143533","143545","143559","144434","144446",
   "144456","144513","144523","144706","144717","144734","144752","144811",
   "144826","144920","144934","144950","145046","145109","145124","145142",
   "145154","145210","145222","145237","145248","145302","145317","145334",
   "145345","145402","145416","145433","145443","145501","145512","145527",
   "145539","145623","145700","145712","145721","145733","145744","145755",
   "145804","145816","145823","145840","145853","145902")
ov(CAT_NOVEL0, "180358","180413","181026","181032","181041","181119","181131",
   "115458","120401","140812","141236","141521","121459","121448")
ov(CAT_DREAM, "180420","180445","180504","180518","180524","180537",
   "121031","121048","141856","141908","141931","141940")
ov(CAT_GAME, "180834","180849","180907","180913","180927","181002","181212",
   "120342","120356","120438","120455","120501","120514","120520","120548",
   "120558","120619","120636","120709","120732","120753","120800","120816",
   "140823","140838","140843","140859","140918","140933","140943","141002",
   "141020","141039","141051","141120","141132","141224","141250","141302",
   "141314","141326","141344","141419","141430","141444","141458","141537",
   "141548","141603","141618","141632","141643","141712","141724","141743",
   "141801","141825","141839","142012","142152","142315","142328","142340",
   "142458","142509","142525","142543","142612","142634","142652","142713",
   "142738","120320")
ov(CAT_SONG, "142025","142042","142054","142123","142136","142212","142229",
   "142243","142259","142421","142436")
ov(CAT_ESSAY, "121551","121604","140716","141353")
ov(CAT_MISC, "181046","181111","181216","115515","115546","120245","120253",
   "120325","120338","120413","120419","120431","120542","140749","140756",
   "141407","120826","120643","142754","121121","121137","121526","140843")
ov(CAT_SCRAP, "120130","120135","120203")

CAT_ORDER = [CAT_NOVEL1, CAT_NOVEL0, CAT_DREAM, CAT_GAME, CAT_SONG, CAT_ESSAY, CAT_MISC, CAT_SCRAP]
CAT_DESC = {
    CAT_NOVEL1: "科幻小说正稿：战争结束后的宇宙快递员、晓琳、伊甸园星球、核弹噩梦——五十多页逐页衔接的完整故事。",
    CAT_NOVEL0: "早期脑洞与设定：宝剑与软肋的开头、杀手起源、间谍学校、另一个世界的结局……",
    CAT_DREAM:  "记下来的梦：三个梦、做梦、回到2012年的医院、开进院子的车……",
    CAT_GAME:   "游戏设计：minecraft地图与Boss战、红石电路、孤独之岛、盗梦笔记、meta元素……",
    CAT_SONG:   "今日的歌：给故事配的曲子，从第4首到第25首，还有新U盘里的旋律。",
    CAT_ESSAY:  "正经写的作文：《删掉那首歌》《独乐》……",
    CAT_MISC:   "想到什么写什么：高考、warma、steam入场券、卖书卖血、给未来自己说的话……",
    CAT_SCRAP:  "散落的纸片与便签，字迹最潦草的灵感碎片。",
}

crop_map = {}
for line in open(os.path.join(CROP, "_索引.txt"), encoding="utf-8"):
    parts = line.split()
    if len(parts) < 4: continue
    crop_map[(parts[1], int(parts[2][1:]))] = parts[3]

RE_FIG   = re.compile(r"〔图｜[^〕]*〕")
RE_ANN   = re.compile(r"〔[上注下]+：([^〕]*)〕")
RE_CROSS = re.compile(r"〔划：[^〕]*〕|〔涂改〕|〔整行划掉：[^〕]*〕")
RE_UNK   = re.compile(r"〔\?〕|\(\?\)")
PINYIN_OK = re.compile(r"^[A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü\s'·\-]+$")
PINYIN_FIX = {("甲","kǎi"):"铠", ("软","lěi"):"肋"}

def pinyin_preclean(s):
    def sub(m):
        ch, py = m.group(1), m.group(2)
        return PINYIN_FIX.get((ch, py), ch)
    return re.sub(r"([\u4e00-\u9fff])〔[上注下]+：([A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]+)〕", sub, s)

def clean_line(s):
    s = RE_FIG.sub("", s)
    s = RE_CROSS.sub("", s)
    def ann_sub(m):
        content = m.group(1).strip()
        if not content or PINYIN_OK.match(content):
            return ""
        return content if len(content) <= 6 else ""
    s = RE_ANN.sub(ann_sub, s)
    s = RE_UNK.sub("", s)
    s = re.sub(r"〔[^〕]*〕", "", s)      # 兜底：清除所有剩余〔〕类元标注（颜色/墨水/纸片布局等）
    s = s.replace("〔", "").replace("〕", "")  # 清掉不成对的孤立括号
    s = s.replace("[右对齐]", " ")
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()


def extract_page(stem):
    path = os.path.join(OCR, stem + ".md")
    date = ""
    blocks = []
    title = ""
    raw_lines = open(path, encoding="utf-8").read().splitlines()
    cleaned, full_fig, has_fig = strip_figures(raw_lines)
    for ln_no, ctext in cleaned:
        s = ctext.strip()
        if ln_no in full_fig:
            if (stem, ln_no) in crop_map:
                blocks.append({"t": "img", "src": "images/" + crop_map[(stem, ln_no)]})
            continue
        if not s or s.startswith("# "):
            continue
        m = re.match(r"〔拍摄：([^〕]+)〕", s)
        if m:
            date = m.group(1).strip(); continue
        if s.startswith(("〔本页状态：", "〔页面信息：", "〔备注：", "〔整行划掉")):
            continue
        if re.match(r"^(纸片\d*｜|｜|图旁|（以上)", s):
            continue
        m = re.match(r"^[^：]{0,24}?(红字|红笔|蓝字|蓝笔|黑笔)批注[^：]*[:：](.+)$", s)
        if m:
            col = "b" if "蓝" in m.group(1) else "r"
            s = ("〔红笔〕" if col == "r" else "〔蓝笔〕") + m.group(2)
        s = pinyin_preclean(s)
        s = RE_CROSS.sub("", s)
        def ann_sub(m):
            content = m.group(1).strip()
            if not content or PINYIN_OK.match(content):
                return ""
            return content if len(content) <= 6 else ""
        s = RE_ANN.sub(ann_sub, s)
        s = RE_UNK.sub("", s)
        segs = line_segments(s, strip_meta=True)
        if not segs:
            continue
        if not title:
            title = segs[0][0][:24]
        blocks.append({"t": "p", "s": segs})
    if not title:
        for raw in raw_lines:
            m = re.search(r"〔图｜[^：〕]*：([^〕]{4,20})", raw)
            if m:
                title = m.group(1).strip(); break
    return {"date": date, "title": title or stem, "blocks": blocks}


def classify(stem, text_all):
    key = stem[-6:]
    if key in OVERRIDES: return OVERRIDES[key]
    t = text_all
    if re.search(r"晓琳|查理|毕福吉|李磊|飞船|快递|希朗|凯特星|伊甸园|核弹", t):
        return CAT_NOVEL1
    if "梦" in t[:60] or re.search(r"我做了个梦|梦见", t):
        return CAT_DREAM
    if re.search(r"今日的歌|第[0-9一二三四五六七八九十]+首|钢琴|旋律|新U盘", t):
        return CAT_SONG
    if re.search(r"作文|《独乐》", t):
        return CAT_ESSAY
    if re.search(r"minecraft|Boss|BOSS|mod|服务器|红石|命令方块|npc|玩家|游戏|末影", t, re.I):
        return CAT_GAME
    return CAT_MISC

order_file = os.path.join(BASE, "工作区域", "页序.txt")
photos = [l.strip() for l in open(order_file, encoding="utf-8") if l.strip()]

os.makedirs(IMG_OUT, exist_ok=True)
pages = []
for photo in photos:
    stem = photo.rsplit(".", 1)[0]
    pg = extract_page(stem)
    pg["file"] = stem
    pg["cat"] = classify(stem, " ".join(
        "".join(seg[0] for seg in b["s"]) if b["t"] == "p" else ""
        for b in pg["blocks"]))
    pages.append(pg)

used = set()
for pg in pages:
    for b in pg["blocks"]:
        if b["t"] == "img": used.add(b["src"].split("/")[-1])
for fn in sorted(used):
    im = Image.open(os.path.join(CROP, fn)).convert("RGB")
    if im.size[0] > 1100:
        r = 1100 / im.size[0]
        im = im.resize((1100, int(im.size[1] * r)), Image.LANCZOS)
    im.save(os.path.join(IMG_OUT, fn), quality=82)

data = [{"i": i, "f": p["file"], "c": p["cat"], "d": p["date"],
         "t": p["title"], "b": p["blocks"]} for i, p in enumerate(pages, 1)]
with open(os.path.join(SITE, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.PAGES=")
    f.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")))

from collections import Counter
cnt = Counter(p["cat"] for p in pages)
print("页面:", len(pages), "| 插图:", len(used))
for c in CAT_ORDER: print(" ", c, cnt.get(c, 0))
