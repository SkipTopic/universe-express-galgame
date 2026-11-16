# -*- coding: utf-8 -*-
"""立绘画布归一化（对齐）：解决豆包差分构图漂移导致的"换表情人物跳动"。
对每个角色：以 base(char_x.png) 的 alpha bbox 为基准，
把 6 张（base+5差分）等比缩放到 base 内容高度，
水平中心统一放到画布中央(666)，脚底统一放到 y=1970。
身高差异按角色保留（小孩比成人矮）。输出仍为 1333x2000，原文件备份到 旧立绘备份_v3。
用法：python 对齐立绘.py            # 全部7角色
      python 对齐立绘.py xiaolin    # 只处理指定角色
"""
import os
import re
import sys
import numpy as np
from PIL import Image

DST = r"D:\我的godot项目\小时候的小说\godot项目galgame\assets\sprites\characters"
BAK = r"D:\我的godot项目\小时候的小说\工作区域\美术\旧立绘备份_v3"
W, H = 1333, 2000
TARGET_CX, TARGET_FEET = W // 2, 1970
SUF = ("_normal", "_smile", "_angry", "_sad", "_shock")
ALL = ["me", "xilang", "bi", "lilei", "photo", "xiaolin", "charlie"]

def bbox_of(img):
    a = img.getchannel("A")
    return a.getbbox()  # (x0,y0,x1,y1) 或 None

def normalize(img, bw, bb):
    """把 img 的内容按基准 bbox(bw,bb) 缩放+摆位，返回新画布"""
    b = bbox_of(img)
    if b is None:
        print("  !! 空内容，跳过")
        return img
    s = (bb[3] - bb[1]) / max(1, (b[3] - b[1]))   # 等比：内容高对齐基准
    icx, ibot = (b[0] + b[2]) / 2.0, b[3]
    # 仿射系数：输出(x,y) → 输入 = a x + b y + c
    a, f = 1.0 / s, 1.0 / s
    c = icx - a * TARGET_CX
    g = ibot - f * TARGET_FEET
    out = img.transform((W, H), Image.AFFINE, (a, 0, c, 0, f, g),
                        resample=Image.BICUBIC)
    return out

def main(names):
    os.makedirs(BAK, exist_ok=True)
    for name in names:
        files = [f"char_{name}.png"] + [f"char_{name}{s}.png" for s in SUF]
        paths = [os.path.join(DST, f) for f in files]
        if not all(os.path.exists(p) for p in paths):
            print(f"char_{name}: 文件不全，跳过")
            continue
        imgs = {f: Image.open(p).convert("RGBA") for f, p in zip(files, paths)}
        bb = bbox_of(imgs[f"char_{name}.png"])
        if bb is None:
            print(f"char_{name}: base 无内容，跳过")
            continue
        bw = (bb[0] + bb[2]) / 2.0
        print(f"char_{name}: base bbox={bb} 中心x={bw:.0f} 内容高={bb[3]-bb[1]}")
        for f, img in imgs.items():
            out = normalize(img, bw, bb)
            p = os.path.join(DST, f)
            bak = os.path.join(BAK, f)
            if os.path.exists(p) and not os.path.exists(bak):
                Image.open(p).save(bak)
            out.save(p)
            nb = bbox_of(out)
            print(f"  {f}: -> bbox={nb}")
        # base 与 normal 保持同一张（引擎两名字共用）
        if os.path.exists(os.path.join(DST, f"char_{name}_normal.png")):
            imgs_n = Image.open(os.path.join(DST, f"char_{name}_normal.png"))
            imgs_n.save(os.path.join(DST, f"char_{name}.png"))

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg:
        main([re.sub(r'^char_', '', arg)])
    else:
        main(ALL)
