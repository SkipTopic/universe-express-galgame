# -*- coding: utf-8 -*-
"""立绘重抠 v2：flood fill 从画布边缘连通去白底
修复 v1 全局白色阈值误删人脸/白大褂的 bug。
原则：只有与画布边缘连通的白色才是背景；人物内部的白色（脸、白大褂、眼白）一律保留。
流程：jpg原图 → 背景候选(高亮度+低饱和) → 边缘BFS → alpha → 轻羽化 → resize 1333x2000 → 覆盖游戏png
"""
import os
import numpy as np
from PIL import Image, ImageFilter
from collections import deque

SRC = r"D:\我的godot项目\小时候的小说\手绘素材提交\立绘"
DST = r"D:\我的godot项目\小时候的小说\godot项目galgame\assets\sprites\characters"
BAK = r"D:\我的godot项目\小时候的小说\工作区域\美术\旧立绘备份_v1"
OUT_W, OUT_H = 1333, 2000
BRIGHT = 228      # 亮度阈值：RGB全>此值才算白色候选
SAT_MAX = 22      # 最大通道差：饱和度高的一律不算白底（保护肤色/浅色衣物）

os.makedirs(BAK, exist_ok=True)

def matte(img):
    """jpg → RGBA 透明立绘（flood fill 边缘连通去白）"""
    rgb = np.asarray(img.convert("RGB")).astype(np.int16)
    h, w = rgb.shape[:2]
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    cand = (mn > BRIGHT) & ((mx - mn) < SAT_MAX)   # 白色候选（含柔和阴影灰）
    # flood fill：从四边所有候选像素出发
    bg = np.zeros((h, w), dtype=bool)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if cand[y, x] and not bg[y, x]:
                bg[y, x] = True
                dq.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if cand[y, x] and not bg[y, x]:
                bg[y, x] = True
                dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for ny, nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0 <= ny < h and 0 <= nx < w and cand[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                dq.append((ny, nx))
    # alpha：背景=0，人物=255
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    a_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.8))
    out = img.convert("RGB")
    out.putalpha(a_img)
    return out

files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".jpg"))
report = []
for f in files:
    src_path = os.path.join(SRC, f)
    img = Image.open(src_path)
    orig_size = img.size
    out = matte(img)
    # 统一到游戏标准尺寸（与现有豆包版一致）
    out = out.resize((OUT_W, OUT_H), Image.LANCZOS)
    name = os.path.splitext(f)[0]
    # 备份旧png再覆盖
    dst_path = os.path.join(DST, name + ".png")
    if os.path.exists(dst_path):
        bak_path = os.path.join(BAK, name + ".png")
        if not os.path.exists(bak_path):
            Image.open(dst_path).save(bak_path)
    out.save(dst_path)
    # normal 版同时覆盖基础名（char_charlie.png 等）
    if name.endswith("_normal"):
        base = name[:-len("_normal")] + ".png"
        dst_base = os.path.join(DST, base)
        if os.path.exists(dst_base):
            bak_base = os.path.join(BAK, base)
            if not os.path.exists(bak_base):
                Image.open(dst_base).save(bak_base)
        out.save(dst_base)
        report.append(f + " -> " + name + ".png + " + base)
    else:
        report.append(f + " -> " + name + ".png")
    print("%s 原尺寸%s 透明OK" % (f, orig_size))

print("\n".join(report))
print("完成：%d张" % len(files))
