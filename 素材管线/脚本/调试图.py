# -*- coding: utf-8 -*-
"""为需要人工校正的页生成调试图：整页缩小 + 现有裁剪框(红) + 10%网格"""
import os, json
from PIL import Image, ImageDraw

BASE = r"D:\我的godot项目\小时候的小说"
CAM  = os.path.join(BASE, "素材", "Camera")
OUT  = os.path.join(BASE, "工作区域", "裁剪图片", "检查")
manifest = json.load(open(os.path.join(BASE, "工作区域", "裁剪图片", "manifest.json"), encoding="utf-8"))

PAGES = ["IMG_20230625_180524","IMG_20230625_180834","IMG_20230625_180927",
         "IMG_20230625_181026","IMG_20230625_181119","IMG_20230626_121048",
         "IMG_20230626_141314","IMG_20230626_141537","IMG_20230626_142340",
         "IMG_20230626_142543","IMG_20230626_142525","IMG_20230626_142738",
         "IMG_20230626_141618"]

# 从裁剪脚本导出的框信息：重算 band（不重裁剪，只画框）
import importlib.util
spec = importlib.util.spec_from_file_location("cg", os.path.join(BASE, "工作区域", "裁剪插图.py"))
# 不能直接import（会重跑）。改为复制关键函数：
import re, glob
OCR = os.path.join(BASE, "工作区域", "OCR文本")
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

OV = {  # 与裁剪插图.py一致的手工覆盖
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
}

for stem in PAGES:
    im = Image.open(os.path.join(CAM, stem + ".jpg")).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im)
    for i in range(1, 10):  # 10%网格
        d.line([(W * i / 10, 0), (W * i / 10, H)], fill=(255, 150, 150), width=3)
        d.line([(0, H * i / 10), (W, H * i / 10)], fill=(255, 150, 150), width=3)
        d.text((W * i / 10 + 8, 8), str(i * 10), fill=(255, 0, 0))
        d.text((8, H * i / 10 + 8), str(i * 10), fill=(255, 0, 0))
    for lineno in manifest.get(stem, {}):
        lines = open(os.path.join(OCR, stem + ".md"), encoding="utf-8").read().splitlines()
        text = lines[int(lineno) - 1]
        if "〕" not in text.split("〔图｜", 1)[1]:
            for nxt in lines[int(lineno):]:
                text += nxt
                if "〕" in nxt: break
        m = re.search(r"〔图｜(.{0,500}?)〕", text, re.S)
        loc = (m.group(1) if m else text).split("：", 1)[0]
        if (stem, int(lineno)) in OV:
            y0, y1, x0, x1 = OV[(stem, int(lineno))]
        else:
            yy, xx = yband(loc), xband(loc)
            y0, y1, x0, x1 = yy[0], yy[1], xx[0], xx[1]
        d.rectangle([x0 * W, y0 * H, x1 * W, y1 * H], outline=(0, 0, 255), width=6)
        d.text((x0 * W + 10, y0 * H + 40), f"L{lineno}", fill=(0, 0, 255))
    im = im.resize((1100, int(H * 1100 / W)))
    im.save(os.path.join(OUT, f"调试_{stem[-6:]}.jpg"), quality=85)
print("done:", len(PAGES))
