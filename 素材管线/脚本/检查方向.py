# -*- coding: utf-8 -*-
"""自动检测照片方向：印刷横线在正立页面呈水平周期分布。
对每张照片比较 0°/90°CW/180°/90°CCW 四个方向的横线周期强度，
给出最可能的方向。输出 检查\方向检测.txt
"""
import os, glob
import numpy as np
from PIL import Image

BASE = r"D:\我的godot项目\小时候的小说"
CAM = os.path.join(BASE, "素材", "Camera")
OUT = os.path.join(BASE, "工作区域", "裁剪图片", "检查", "方向检测.txt")

def orient_score(gray):
    """横线周期强度：对行墨迹剖面做去趋势自相关，取周期峰 strongest"""
    ink = (gray < 185).astype(np.float32)
    prof = ink.mean(axis=1)
    prof = prof - np.convolve(prof, np.ones(61) / 61, mode="same")
    n = len(prof)
    seg = prof[: n - n % 2]
    f = np.abs(np.fft.rfft(seg))
    # 周期 12~70px（600x800 缩略图上横线间距范围）
    freqs = np.fft.rfftfreq(len(seg))
    mask = (freqs > 1 / 70) & (freqs < 1 / 12)
    if not mask.any():
        return 0.0
    return float(f[mask].max())

def get_gray(im):
    im = im.resize((600, 800), Image.BILINEAR)
    return np.asarray(im.convert("L"), dtype=np.float32)

results = []
for p in sorted(glob.glob(os.path.join(CAM, "*.jpg"))):
    stem = os.path.basename(p)[:-4]
    g = get_gray(Image.open(p))
    s0 = orient_score(g)
    s_cw = orient_score(np.rot90(g, k=-1))    # 顺时针90°后
    s_180 = orient_score(np.rot90(g, k=2))
    s_ccw = orient_score(np.rot90(g, k=1))
    best = max(s0, s_cw, s_180, s_ccw)
    if best == s0:
        verdict = "正立"
    elif best == s_cw:
        verdict = "横置→需顺时针CW转正"
    elif best == s_ccw:
        verdict = "横置→需逆时针CCW转正"
    else:
        verdict = "倒置180°"
    results.append((stem, verdict, round(s0, 3), round(s_cw, 3), round(s_180, 3), round(s_ccw, 3)))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("stem | 判定 | s0(正) | sCW | s180 | sCCW\n")
    for r in results:
        f.write(" | ".join(map(str, r)) + "\n")

odd = [r for r in results if r[1] != "正立"]
print("总数:", len(results), "| 非正立:", len(odd))
for r in odd:
    print(" ".join(map(str, r)))
