# -*- coding: utf-8 -*-
r"""按〔图〕标注从日记照片中裁剪大幅插图。
位置策略：标注文字里的位置词(左上/中部/第X-Y行/整页...) → 大致区域
         → 区域内按墨迹(深色/高饱和像素)自动收紧边界 → 裁剪保存。
输出：工作区域\裁剪图片\*.jpg + manifest.json + 检查\拼图N.jpg
"""
import os, re, json, glob
import numpy as np
from PIL import Image, ImageDraw

BASE = r"D:\我的godot项目\小时候的小说"
CAM  = os.path.join(BASE, "素材", "Camera")
OCR  = os.path.join(BASE, "工作区域", "OCR文本")
OUT  = os.path.join(BASE, "工作区域", "裁剪图片")
CHK  = os.path.join(OUT, "检查")
os.makedirs(OUT, exist_ok=True); os.makedirs(CHK, exist_ok=True)

# ── 需要裁剪的 (md文件名尾号, 标注起始行号=md文件真实行号) ──
SPEC_RAW = """
180358:15,20
180413:10
180420:8,16,17,24
180504:7,19,22
180518:10,14,20,22
180524:11,12,16,20,21,22
180834:22,29
180849:10
180907:7,8,18
180927:7,17,25,31
181002:9,17,18
181026:11
181046:7
181119:23,24,25
181131:8
181212:23
115546:20,23
120130:30,52
120135:11,33
120203:10,39
120320:13,15,17
120325:13,24
120342:7
120356:10
120401:9
120419:15
120431:15,16
120438:11
120455:12,15
120501:8,15
120514:6
120520:7,10,15,20,21
120548:13
120558:6,19
120619:10,14
120636:7,18
120709:11,12
120732:11,13,23,28
120753:11,12,14,19
120800:9,11
120816:11,19
120826:9,10,14
120845:7,8,11
121031:7
121048:9,16
121059:14
121121:7,14,32
121137:7,10,33,36
121542:10
140812:10,11,20,33,37
140823:19,26
140838:29
140859:22,23
140933:9,18,20
140943:7,8,10
141002:15
141120:7,8,9,10
141224:17
141250:19
141302:10,16
141314:9,13,14
141326:14,26
141344:15,17
141458:11
141521:20
141537:24,25
141548:8
141603:9,11
141618:13,18
141632:7
141643:12,13
141712:9
141724:11
141743:14
141839:8,10
141856:15,16
141908:8,14
141931:7,8,19,20
141940:13,14
142136:23
142340:22,23
142509:12
142525:12
142612:18
142634:20
142652:8
142713:14
142738:11,33
142754:9
142829:9,11,12
142847:8,10
142543:11
143015:15
143040:24
143309:15
143426:7,9,11
144811:9
145402:16
"""

def resolve_md(tail):
    hits = glob.glob(os.path.join(OCR, "*" + tail + ".md"))
    if len(hits) != 1:
        raise FileNotFoundError(f"{tail}: {hits}")
    return hits[0]

SPEC = []
for ln in SPEC_RAW.strip().splitlines():
    tail, lns = ln.split(":", 1)
    stem = os.path.basename(resolve_md(tail))[:-3]
    for l in lns.split(","):
        SPEC.append((stem, int(l)))

# 特殊区域覆盖 (y0,y1,x0,x1)
OVERRIDES = {
    ("IMG_20230626_120342", 7):  (0.01, 0.99, 0.01, 0.99),
    ("IMG_20230626_120514", 6):  (0.01, 0.99, 0.01, 0.99),
    ("IMG_20230626_121542", 10): (0.01, 0.99, 0.01, 0.99),
    ("IMG_20230626_144811", 9):  (0.01, 0.99, 0.01, 0.99),
    ("IMG_20230626_142754", 9):  (0.01, 0.99, 0.01, 0.99),
    ("IMG_20230626_120438", 11): (0.30, 0.70, 0.01, 0.99),
    ("IMG_20230626_143040", 24): (0.40, 0.99, 0.01, 0.99),
    ("IMG_20230626_141743", 14): (0.06, 0.97, 0.01, 0.99),
    ("IMG_20230626_145402", 16): (0.08, 0.94, 0.01, 0.99),
    ("IMG_20230626_120800", 9):  (0.02, 0.73, 0.01, 0.99),
    ("IMG_20230626_120800", 11): (0.60, 0.99, 0.01, 0.99),
    ("IMG_20230626_121031", 7):  (0.02, 0.66, 0.20, 1.00),
    ("IMG_20230626_115546", 20): (0.42, 0.90, 0.01, 0.99),
    ("IMG_20230626_121059", 14): (0.02, 0.65, 0.35, 1.00),
    ("IMG_20230626_140859", 22): (0.50, 0.90, 0.01, 0.64),
    ("IMG_20230626_140859", 23): (0.64, 0.98, 0.01, 0.64),
    # ── 人工看图校正的框 (y0,y1,x0,x1) ──
    ("IMG_20230625_180524", 11): (0.03, 0.36, 0.05, 0.42),
    ("IMG_20230625_180524", 12): (0.19, 0.40, 0.37, 0.83),
    ("IMG_20230625_180524", 16): (0.30, 0.60, 0.02, 0.34),
    ("IMG_20230625_180524", 20): (0.52, 0.77, 0.06, 0.37),
    ("IMG_20230625_180524", 21): (0.68, 0.96, 0.18, 0.52),
    ("IMG_20230625_180524", 22): (0.55, 0.96, 0.42, 1.00),
    ("IMG_20230625_180834", 29): (0.52, 0.78, 0.06, 0.60),
    ("IMG_20230625_180927", 7):  (0.04, 0.24, 0.26, 0.54),
    ("IMG_20230625_180927", 17): (0.36, 0.62, 0.05, 0.46),
    ("IMG_20230625_181026", 11): (0.215, 0.36, 0.10, 0.38),
    ("IMG_20230625_181119", 23): (0.27, 0.50, 0.02, 0.44),
    ("IMG_20230625_181119", 24): (0.47, 0.68, 0.04, 0.46),
    ("IMG_20230625_181119", 25): (0.63, 0.85, 0.05, 0.46),
    ("IMG_20230625_180413", 10): (0.14, 0.62, 0.01, 0.99),
    ("IMG_20230626_121048", 9):  (0.26, 0.38, 0.05, 0.27),
    ("IMG_20230626_121048", 16): (0.35, 0.52, 0.01, 0.24),
    ("IMG_20230626_141314", 9):  (0.09, 0.30, 0.18, 0.58),
    ("IMG_20230626_141314", 13): (0.32, 0.64, 0.03, 0.20),
    ("IMG_20230626_141314", 14): (0.31, 0.68, 0.30, 0.82),
    ("IMG_20230626_141537", 24): (0.57, 0.77, 0.61, 0.93),
    ("IMG_20230626_141537", 25): (0.60, 0.96, 0.09, 0.80),
    ("IMG_20230626_142340", 22): (0.615, 0.71, 0.01, 0.95),
    ("IMG_20230626_142340", 23): (0.63, 0.98, 0.06, 0.62),
    ("IMG_20230626_142525", 12): (0.33, 0.59, 0.25, 0.53),
    ("IMG_20230626_142738", 11): (0.22, 0.60, 0.02, 0.28),
    ("IMG_20230626_142738", 33): (0.02, 0.82, 0.66, 1.00),
    ("IMG_20230626_141618", 13): (0.24, 0.40, 0.74, 0.96),
    ("IMG_20230626_141618", 18): (0.07, 0.70, 0.01, 0.50),
    # ── 第三轮目检校正（横置页用原始照片坐标，裁剪后才旋转）──
    ("IMG_20230626_142543", 11): (0.13, 0.31, 0.20, 0.34),
    ("IMG_20230626_120558", 6):  (0.06, 0.90, 0.66, 1.00),
    ("IMG_20230626_120558", 19): (0.26, 0.64, 0.25, 0.48),
    ("IMG_20230626_120826", 10): (0.10, 0.37, 0.56, 0.78),
    ("IMG_20230626_120826", 14): (0.01, 0.33, 0.15, 0.48),
    ("IMG_20230626_120753", 11): (0.09, 0.26, 0.70, 0.86),
    ("IMG_20230626_120753", 12): (0.36, 0.54, 0.70, 0.86),
    ("IMG_20230626_120753", 14): (0.09, 0.28, 0.52, 0.70),
    ("IMG_20230626_120753", 19): (0.17, 0.68, 0.47, 0.62),
}
WHOLE = {k for k, v in OVERRIDES.items() if v == (0.01, 0.99, 0.01, 0.99)}

# ── 横置照片页：裁剪后整体转正 (CW=顺时针90°, CCW=逆时针90°) ──
# 依据：检查\方向对比_*.jpg 逐页 CW/CCW 对比目检定案（2026-10-04 第二会话）
ROT90 = {
    "IMG_20230626_142738": "CW",
    "IMG_20230626_142543": "CW",
    "IMG_20230626_142634": "CW",
    "IMG_20230626_120548": "CCW",
    "IMG_20230626_120558": "CCW",
    "IMG_20230626_120826": "CCW",
    "IMG_20230626_121031": "CCW",
    "IMG_20230626_142612": "CW",
}

def yband(s):
    if "下半页" in s or s.startswith("下半"): return (0.45, 0.99)
    if "中部大半页" in s: return (0.10, 0.93)
    if "占约2/3" in s: return (0.02, 0.73)
    m = re.search(r"第(\d+)\s*[-～~—]\s*(\d+)\s*行", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return (max(0.02, 0.05 + (a - 1) / 30 * 0.92 - 0.03), min(0.99, 0.05 + b / 30 * 0.92 + 0.03))
    m = re.search(r"第(\d+)\s*行", s)
    if m:
        y = 0.05 + (int(m.group(1)) - 0.5) / 30 * 0.92
        return (max(0.02, y - 0.08), min(0.99, y + 0.08))
    if "中上" in s: return (0.15, 0.58)
    if "中下" in s: return (0.45, 0.88)
    if "中部" in s or s.startswith("中") or "页中" in s: return (0.28, 0.80)
    if any(k in s for k in ("左中下", "右中下", "中左", "中右", "左中", "右中")): return (0.30, 0.80)
    if any(k in s for k in ("上部", "顶部", "页顶", "页首", "上左", "上中", "上右", "左上", "右上")): return (0.02, 0.38)
    if "标题下" in s: return (0.04, 0.42)
    if any(k in s for k in ("首行", "标题行", "行首")): return (0.02, 0.22)
    if any(k in s for k in ("下部", "底部", "下中", "下左", "下右", "左下", "右下", "下方", "下半")): return (0.55, 0.99)
    if "左缘" in s or "右缘" in s: return (0.12, 0.92)
    if "左侧" in s or "右侧" in s or s.startswith("左") or s.startswith("右"): return (0.08, 0.92)
    return (0.05, 0.95)

def xband(s):
    if "整页" in s: return (0.01, 0.99)
    if "左缘" in s: return (0.01, 0.42)
    if "右缘" in s: return (0.58, 0.99)
    if "左" in s: return (0.01, 0.64)
    if "右" in s: return (0.36, 0.99)
    return (0.01, 0.99)

_md_cache = {}
def marker_lines(stem):
    if stem not in _md_cache:
        with open(os.path.join(OCR, stem + ".md"), encoding="utf-8") as f:
            _md_cache[stem] = [l.rstrip("\n") for l in f]
    return _md_cache[stem]

img_cache = {}
def get_img(stem):
    if stem not in img_cache:
        img_cache[stem] = Image.open(os.path.join(CAM, stem + ".jpg")).convert("RGB")
    return img_cache[stem]

manifest = {}
records = []
idx = 0
# 清掉上一轮的旧编号crop与拼图，避免重编号后残留孤儿文件
for old in glob.glob(os.path.join(OUT, "crop*.jpg")) + glob.glob(os.path.join(CHK, "拼图*.jpg")):
    os.remove(old)
for stem, lineno in SPEC:
    lines = marker_lines(stem)
    text = lines[lineno - 1] if lineno - 1 < len(lines) else ""
    if "〔图｜" not in text:
        print(f"[跳过] {stem} L{lineno} 未找到图标注"); continue
    full = text
    if "〕" not in full.split("〔图｜", 1)[1]:
        for nxt in lines[lineno:]:
            full += nxt
            if "〕" in nxt: break
    m = re.search(r"〔图｜(.{0,500}?)〕", full, re.S)
    desc = m.group(1) if m else full
    loc = desc.split("：", 1)[0]
    pencil = ("铅笔" in desc) or ("淡画" in desc) or ("淡铅笔" in desc)
    im = get_img(stem)
    W, H = im.size
    if (stem, lineno) in OVERRIDES:
        y0, y1, x0, x1 = OVERRIDES[(stem, lineno)]
    else:
        yy, xx = yband(loc), xband(loc)
        y0, y1, x0, x1 = yy[0], yy[1], xx[0], xx[1]
    bx0, by0, bx1, by1 = int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)
    band = im.crop((bx0, by0, bx1, by1))
    if (stem, lineno) not in WHOLE:
        a = np.asarray(band)
        gray = a[:, :, 0] * 0.299 + a[:, :, 1] * 0.587 + a[:, :, 2] * 0.114
        sat = a.max(axis=2).astype(int) - a.min(axis=2).astype(int)
        tg = 178 if pencil else 150
        ink = (gray < tg) | ((sat > 70) & (gray < 215))
        rows = ink.sum(axis=1); cols = ink.sum(axis=0)
        rh = max(4, 0.003 * band.size[0]); ch = max(4, 0.003 * band.size[1])
        ry = np.where(rows > rh)[0]; cx = np.where(cols > ch)[0]
        if len(ry) and len(cx):
            pad_x, pad_y = int(0.018 * W), int(0.015 * H)
            nx0 = max(0, int(cx[0]) - pad_x); nx1 = min(band.size[0], int(cx[-1]) + pad_x)
            ny0 = max(0, int(ry[0]) - pad_y); ny1 = min(band.size[1], int(ry[-1]) + pad_y)
            if not ((nx1 - nx0) > 0.965 * band.size[0] and (ny1 - ny0) > 0.965 * band.size[1]):
                bx0, by0, bx1, by1 = bx0 + nx0, by0 + ny0, bx0 + nx1, by0 + ny1
    crop = im.crop((bx0, by0, bx1, by1))
    if ROT90.get(stem) == "CW":
        crop = crop.transpose(Image.ROTATE_270)   # 顺时针90°
    elif ROT90.get(stem) == "CCW":
        crop = crop.transpose(Image.ROTATE_90)    # 逆时针90°
    if max(crop.size) > 1500:
        r = 1500 / max(crop.size)
        crop = crop.resize((max(1, int(crop.size[0] * r)), max(1, int(crop.size[1] * r))), Image.LANCZOS)
    idx += 1
    fn = f"crop{idx:03d}_{stem[-6:]}_L{lineno}.jpg"
    crop.save(os.path.join(OUT, fn), quality=80)
    manifest.setdefault(stem, {})[str(lineno)] = {"file": fn, "desc": desc[:60]}
    records.append((idx, stem, lineno, fn, desc[:44]))

with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "_索引.txt"), "w", encoding="utf-8") as f:
    for i, stem, lineno, fn, desc in records:
        f.write(f"#{i:03d} {stem} L{lineno} {fn} | {desc}\n")

CELL_W, CELL_H, COLS = 520, 460, 3
per = COLS * 4
for si in range(0, len(records), per):
    chunk = records[si:si + per]
    sheet = Image.new("RGB", (CELL_W * COLS, CELL_H * 4), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    for k, (i, stem, lineno, fn, desc) in enumerate(chunk):
        im = Image.open(os.path.join(OUT, fn))
        r = min((CELL_W - 12) / im.size[0], (CELL_H - 30) / im.size[1], 1.0)
        im = im.resize((max(1, int(im.size[0] * r)), max(1, int(im.size[1] * r))), Image.LANCZOS)
        cx, cy = (k % COLS) * CELL_W, (k // COLS) * CELL_H
        sheet.paste(im, (cx + 6, cy + 26))
        d.text((cx + 8, cy + 6), f"#{i:03d} {stem[-6:]} L{lineno}", fill=(180, 0, 0))
        d.rectangle([cx + 5, cy + 25, cx + 6 + im.size[0], cy + 26 + im.size[1]], outline=(200, 200, 200))
    sheet.save(os.path.join(CHK, f"拼图{si // per + 1:02d}.jpg"), quality=82)
print(f"裁剪 {len(records)} 张 → {OUT}")
print(f"拼图 {(len(records) + per - 1) // per} 张 → {CHK}")
