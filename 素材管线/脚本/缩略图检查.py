# -*- coding: utf-8 -*-
"""33张疑似横置页 → 缩略图拼图目检 + 3张存疑裁剪原图导出"""
import os, math
from PIL import Image, ImageDraw

BASE = r"D:\我的godot项目\小时候的小说"
CAM = os.path.join(BASE, "素材", "Camera")
OUT = os.path.join(BASE, "工作区域", "裁剪图片", "检查")
CROP = os.path.join(BASE, "工作区域", "裁剪图片")

SUS = """120130 120135 120203 120320 120542 120548 120558 120619 120636 120643
120709 120718 120732 120736 120753 120800 120816 120826 120845 142421
142436 142458 142509 142525 142543 142612 142634 142652 142713 142738
142754 142847 142911""".split()

files = []
for tail in SUS:
    hits = [x for x in os.listdir(CAM) if x.endswith(tail + ".jpg")]
    if hits:
        files.append((tail, os.path.join(CAM, hits[0])))

TW, TH, COLS = 300, 400, 6
rows = math.ceil(len(files) / COLS)
sheet = Image.new("RGB", (TW * COLS, TH * rows), (245, 245, 245))
d = ImageDraw.Draw(sheet)
for k, (tail, path) in enumerate(files):
    im = Image.open(path).resize((TW - 8, TH - 28))
    cx, cy = (k % COLS) * TW, (k // COLS) * TH
    sheet.paste(im, (cx + 4, cy + 24))
    d.text((cx + 6, cy + 4), tail, fill=(200, 0, 0))
sheet.save(os.path.join(OUT, "横置嫌疑页.jpg"), quality=80)
print("嫌疑页拼图:", len(files))

# 3张存疑裁剪单独导出
import json
mf = json.load(open(os.path.join(CROP, "manifest.json"), encoding="utf-8"))
for tail, line in [("120340", "22"), ("120927", "7"), ("121026", "11")]:
    stem = [k for k in mf if k.endswith(tail)][0]
    src = os.path.join(CROP, mf[stem][line]["file"])
    im = Image.open(src)
    im.thumbnail((900, 900))
    im.save(os.path.join(OUT, f"存疑_{tail}_L{line}.jpg"), quality=85)
print("存疑3张已导出")
