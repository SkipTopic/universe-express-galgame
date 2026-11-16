# -*- coding: utf-8 -*-
"""美术引擎：用PIL分层绘制galgame素材（背景/立绘/CG）。
风格：扁平赛璐璐动漫风 + 轻噪点。所有绘制2x超采样后缩小抗锯齿。"""
import math, random
from PIL import Image, ImageDraw, ImageFilter

SS = 2  # 超采样倍数

def new_bg(w=1920, h=1080):
    return Image.new("RGB", (w * SS, h * SS), (10, 10, 16))

def finish(img, w=1920, h=1080):
    return img.resize((w, h), Image.LANCZOS)


class SDraw:
    """设计坐标画笔：坐标/线宽自动×SS，解决超采样错位"""
    def __init__(self, img, ss=SS):
        self.dr = ImageDraw.Draw(img)
        self.ss = ss
    def _s(self, pts):
        if pts and isinstance(pts[0], (tuple, list)):
            return [tuple(v * self.ss for v in p) for p in pts]
        return [v * self.ss for v in pts]
    def _w(self, w): return max(1, int(w * self.ss))
    def rectangle(self, box, fill=None, outline=None, width=1):
        self.dr.rectangle(self._s(box), fill=fill, outline=outline, width=self._w(width))
    def rounded_rectangle(self, box, radius=0, fill=None, outline=None, width=1):
        self.dr.rounded_rectangle(self._s(box), radius=radius * self.ss, fill=fill, outline=outline, width=self._w(width))
    def ellipse(self, box, fill=None, outline=None, width=1):
        self.dr.ellipse(self._s(box), fill=fill, outline=outline, width=self._w(width))
    def polygon(self, pts, fill=None, outline=None):
        self.dr.polygon(self._s(pts), fill=fill, outline=outline)
    def line(self, pts, fill=None, width=1):
        self.dr.line(self._s(pts), fill=fill, width=self._w(width))
    def arc(self, box, a0, a1, fill=None, width=1):
        self.dr.arc(self._s(box), a0, a1, fill=fill, width=self._w(width))

def d(img):
    return ImageDraw.Draw(img)

# ── 通用：垂直/线性渐变 ──
def vgrad(img, y0, y1, c0, c1):
    dr = d(img)
    h = y1 - y0
    for y in range(max(0, int(y0 * SS)), min(img.height, int(y1 * SS))):
        t = (y - y0 * SS) / max(1, h * SS)
        c = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
        dr.line([(0, y), (img.width, y)], fill=c)

def vgrad_alpha(img, box, c0, c1):
    """在区域box内画带透明度的垂直渐变（RGBA覆盖层）"""
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = d(ov)
    x0, y0, x1, y1 = [int(v * SS) for v in box]
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0)
        c = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
        dr.line([(x0, y), (x1, y)], fill=c)
    img.alpha_composite(ov) if img.mode == "RGBA" else img.paste(ov, (0, 0), ov)

def circle(dr, cx, cy, r, fill, outline=None, width=0):
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)

def star_layer(img, n, seed, ymax=0.75, cmax=230, rmax=2.2):
    dr = d(img)
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.uniform(0, img.width); y = rnd.uniform(0, img.height * ymax)
        r = rnd.uniform(0.6, rmax) * SS
        a = rnd.randint(80, cmax)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a) if img.mode == "RGBA" else (a, a, a))

def noise(img, seed=1, amount=6):
    rnd = random.Random(seed)
    px = img.load()
    w, h = img.size
    for _ in range(int(w * h * 0.02)):
        x = rnd.randrange(w); y = rnd.randrange(h)
        r, g, b = px[x, y][:3]
        dv = rnd.randint(-amount, amount)
        px[x, y] = (max(0, min(255, r + dv)), max(0, min(255, g + dv)), max(0, min(255, b + dv)))

def silhouette_mountains(img, ybase, amp, color, seed, peaks=7):
    dr = d(img)
    rnd = random.Random(seed)
    pts = [(0, img.height), (0, ybase * SS)]
    x = 0
    while x < img.width:
        x += img.width / peaks * rnd.uniform(0.6, 1.3)
        pts.append((x, (ybase + rnd.uniform(-amp, amp)) * SS))
    pts.append((img.width, pts[-1][1]))
    pts.append((img.width, img.height))
    dr.polygon(pts, fill=color)

def city_silhouette(img, ybase, color, seed, cols=14, wmax=220, hmin=120, hmax=420, windows=None):
    dr = d(img)
    rnd = random.Random(seed)
    x = -20
    while x < img.width:
        w = rnd.uniform(wmax * 0.5, wmax) * SS
        h = rnd.uniform(hmin, hmax) * SS
        dr.rectangle([x, img.height - h * SS if False else ybase * SS - h, x + w, ybase * SS], fill=color)
        if windows:
            wc = windows
            for wy in range(int(ybase * SS - h) + int(20 * SS), int(ybase * SS) - int(16 * SS), int(34 * SS)):
                for wx in range(int(x) + int(14 * SS), int(x + w) - int(14 * SS), int(30 * SS)):
                    if rnd.random() < 0.5:
                        dr.rectangle([wx, wy, wx + int(10 * SS), wy + int(14 * SS)], fill=wc)
        x += w + rnd.uniform(8, 40) * SS

def vignette(img, strength=90):
    ov = Image.new("L", img.size, 0)
    dr = d(ov)
    w, h = img.size
    dr.ellipse([-w * 0.25, -h * 0.25, w * 1.25, h * 1.25], fill=255)
    ov = ov.filter(ImageFilter.GaussianBlur(w * 0.08))
    dark = Image.new("RGB", img.size, (0, 0, 0))
    img.paste(dark, (0, 0), ov.point(lambda v: int((255 - v) * strength / 255)))

def light_beam(img, x, y, w, h, color, alpha=60):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = d(ov)
    dr.polygon([(x * SS, y * SS), ((x + w) * SS, y * SS), ((x + w * 1.6) * SS, (y + h) * SS), ((x - w * 0.6) * SS, (y + h) * SS)],
               fill=color + (alpha,))
    img.alpha_composite(ov) if img.mode == "RGBA" else img.paste(ov, (0, 0), ov)

# ── 立绘：参数化少年/少女动漫角色（全身）──
OUTLINE = (42, 34, 30, 255)

def draw_character(w=1000, h=1900, cfg=None):
    """参数化全身立绘。cfg: skin/hair/hair_shade/hair_style(long/short/twin/white_old/buzz)
       eyes/outfit/outfit_shade/collar/tie/pants/glasses/beard/blush/expression/short_sleeve/coat"""
    cfg = cfg or {}
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    dr = SDraw(img)
    skin = cfg.get("skin", (255, 232, 214))
    skin_sh = tuple(int(c * 0.92) for c in skin)
    hair = cfg.get("hair", (46, 38, 36))
    hair_sh = tuple(int(c * 0.72) for c in hair)
    eyes = cfg.get("eyes", (90, 120, 170))
    cx = w // 2

    head_top, head_bot = 200, 470
    face_r = 118
    style = cfg.get("hair_style", "short")

    if style == "long":
        dr.rounded_rectangle([cx - 170, head_top + 60, cx + 170, h - 260], 150, fill=hair + (255,))
        dr.rounded_rectangle([cx - 190, head_top + 200, cx - 120, h - 420], 60, fill=hair + (255,))
        dr.rounded_rectangle([cx + 120, head_top + 200, cx + 190, h - 420], 60, fill=hair + (255,))
    elif style == "twin":
        dr.rounded_rectangle([cx - 160, head_top + 40, cx + 160, 900], 120, fill=hair + (255,))
        dr.ellipse([cx - 272, 698, cx - 148, 822], fill=hair + (255,))
        dr.ellipse([cx + 148, 698, cx + 272, 822], fill=hair + (255,))
    elif style == "white_old":
        dr.rounded_rectangle([cx - 150, head_top + 60, cx + 150, 640], 110, fill=hair + (255,))
    elif style == "buzz":
        pass
    else:
        dr.rounded_rectangle([cx - 158, head_top + 40, cx + 158, 560], 110, fill=hair + (255,))

    cy_ = cfg.get("outfit", (52, 66, 110))
    cy_sh = tuple(int(c * 0.78) for c in cy_)
    shoulder = 640
    dr.rounded_rectangle([cx - 195, shoulder, cx + 195, shoulder + 120], 80, fill=cy_ + (255,))
    dr.polygon([(cx - 175, shoulder + 90), (cx + 175, shoulder + 90), (cx + 150, 1260), (cx - 150, 1260)],
               fill=cy_ + (255,))
    pants = cfg.get("pants", (44, 48, 66))
    dr.rounded_rectangle([cx - 130, 1240, cx - 20, 1800], 46, fill=pants + (255,))
    dr.rounded_rectangle([cx + 20, 1240, cx + 130, 1800], 46, fill=pants + (255,))
    dr.rounded_rectangle([cx - 140, 1770, cx - 10, 1852], 36, fill=(38, 34, 40, 255))
    dr.rounded_rectangle([cx + 10, 1770, cx + 140, 1852], 36, fill=(38, 34, 40, 255))
    arm = skin if cfg.get("short_sleeve") else cy_
    dr.rounded_rectangle([cx - 232, shoulder + 60, cx - 150, 1180], 52, fill=arm + (255,))
    dr.rounded_rectangle([cx + 150, shoulder + 60, cx + 232, 1180], 52, fill=arm + (255,))
    if cfg.get("short_sleeve"):
        dr.rounded_rectangle([cx - 232, 1020, cx - 150, 1180], 52, fill=skin + (255,))
        dr.rounded_rectangle([cx + 150, 1020, cx + 232, 1180], 52, fill=skin + (255,))

    if cfg.get("collar"):
        dr.polygon([(cx - 90, shoulder + 20), (cx, shoulder + 130), (cx + 90, shoulder + 20)],
                   fill=cfg["collar"] + (255,))
    if cfg.get("tie"):
        dr.polygon([(cx - 26, shoulder + 60), (cx + 26, shoulder + 60), (cx + 14, shoulder + 320), (cx - 14, shoulder + 320)],
                   fill=cfg["tie"] + (255,))
    if cfg.get("coat"):
        dr.line([(cx, shoulder + 30), (cx, 1240)], fill=cy_sh + (255,), width=8)
        for yy in range(shoulder + 120, 1200, 160):
            dr.ellipse([cx - 72, yy - 12, cx - 48, yy + 12], fill=(200, 180, 120, 255))

    dr.rounded_rectangle([cx - 52, head_bot - 60, cx + 52, shoulder + 60], 30, fill=skin_sh + (255,))
    dr.ellipse([cx - face_r, head_top, cx + face_r, head_bot], fill=skin + (255,))
    dr.polygon([(cx - face_r, head_bot - 120), (cx + face_r, head_bot - 120), (cx, head_bot + 40)],
               fill=skin + (255,))
    dr.ellipse([cx - face_r - 26, 330, cx - face_r + 26, 400], fill=skin + (255,))
    dr.ellipse([cx + face_r - 26, 330, cx + face_r + 26, 400], fill=skin + (255,))

    fr = [(cx - face_r - 12, head_top + 40), (cx - face_r + 30, head_top + 20),
          (cx - 60, head_top - 6), (cx + 70, head_top - 2),
          (cx + face_r - 20, head_top + 30), (cx + face_r + 10, head_top + 60)]
    zig = []
    n = 5
    for k in range(n + 1):
        zx = cx - face_r - 12 + (2 * face_r + 22) * k / n
        zy = head_top + 60 + (28 if k % 2 == 0 else 74)
        zig.append((zx, zy))
    dr.polygon(fr + list(reversed(zig)), fill=hair + (255,))
    dr.ellipse([cx - face_r - 6, head_top - 30, cx + face_r + 6, head_top + 130], fill=hair + (255,))

    eye_y = 345
    expr = cfg.get("expression", "normal")
    if expr == "shock":
        eye_s = 1.18   # 瞪大
    else:
        eye_s = 1.0
    for sx in (-1, 1):
        ex = cx + sx * 58
        ew, eh = int(46 * eye_s), int(32 * eye_s)
        dr.ellipse([ex - ew, eye_y - eh, ex + ew, eye_y + eh + int(2 * eye_s)], fill=(250, 248, 246, 255))
        iw, ih = int(34 * eye_s), int(26 * eye_s)
        dr.ellipse([ex - iw, eye_y - ih + 4, ex + iw, eye_y + ih + 4], fill=eyes + (255,))
        dr.ellipse([ex - int(18 * eye_s), eye_y - int(12 * eye_s) + 4, ex + int(18 * eye_s), eye_y + int(26 * eye_s) + 4],
                   fill=tuple(int(c * 0.55) for c in eyes) + (255,))
        dr.ellipse([ex - 21, eye_y - 15, ex - 3, eye_y + 3], fill=(255, 255, 255, 235))
        dr.line([(ex - ew, eye_y - eh + 2), (ex + ew, eye_y - eh + 2)], fill=OUTLINE, width=6)
        # 眉毛：按表情倾斜
        if expr == "angry":
            bx = -14 if sx < 0 else 14
            dr.line([(ex - 40, eye_y - 58), (ex + 40, eye_y - 78 - bx)], fill=hair_sh + (255,), width=9)
        elif expr == "sad":
            bx = 16 if sx < 0 else -16
            dr.line([(ex - 40, eye_y - 62 + bx), (ex + 40, eye_y - 70 - bx)], fill=hair_sh + (255,), width=9)
        elif expr == "shock":
            dr.line([(ex - 40, eye_y - 84), (ex + 40, eye_y - 88)], fill=hair_sh + (255,), width=9)
        else:
            dr.line([(ex - 40, eye_y - 62), (ex + 40, eye_y - 70)], fill=hair_sh + (255,), width=8)
    # 鼻子
    dr.line([(cx, 395), (cx - 6, 408)], fill=(210, 160, 140, 255), width=5)
    # 嘴：按表情
    if expr == "smile":
        dr.arc([cx - 34, 408, cx + 34, 448], 15, 165, fill=(190, 110, 100, 255), width=8)
    elif expr == "angry":
        dr.arc([cx - 26, 432, cx + 26, 462], 195, 345, fill=(190, 110, 100, 255), width=8)
    elif expr == "sad":
        dr.arc([cx - 22, 434, cx + 22, 460], 200, 340, fill=(190, 110, 100, 255), width=7)
    elif expr == "shock":
        dr.ellipse([cx - 14, 424, cx + 14, 452], fill=(150, 80, 75, 255))
    elif expr == "calm":
        dr.line([(cx - 20, 432), (cx + 20, 432)], fill=(190, 110, 100, 255), width=6)
    else:
        dr.arc([cx - 26, 415, cx + 26, 445], 20, 160, fill=(190, 110, 100, 255), width=6)
    # 腮红
    if cfg.get("blush") or expr == "smile":
        a = 120 if expr == "smile" else 90
        for sx in (-1, 1):
            dr.ellipse([cx + sx * 108 - 34, 392, cx + sx * 108 + 34, 416], fill=(255, 170, 150, a))
    # 附加符号：汗滴(惊)/泪(悲)/怒符(怒)
    if expr == "shock":
        dr.ellipse([cx + face_r - 10, 300, cx + face_r + 22, 346], fill=(150, 200, 240, 220))
    if expr == "sad":
        dr.ellipse([cx - face_r - 4, 356, cx - face_r + 20, 402], fill=(140, 190, 235, 220))
    if expr == "angry":
        dr.line([(cx - face_r - 6, 268), (cx - face_r + 26, 300)], fill=(200, 70, 60, 220), width=8)
        dr.line([(cx - face_r + 26, 268), (cx - face_r - 6, 300)], fill=(200, 70, 60, 220), width=8)
    if cfg.get("glasses"):
        gc = (70, 60, 56, 255)
        for sx in (-1, 1):
            ex = cx + sx * 58
            dr.rounded_rectangle([ex - 52, eye_y - 36, ex + 52, eye_y + 40], 14, outline=gc, width=6)
        dr.line([(cx - 6, eye_y), (cx + 6, eye_y)], fill=gc, width=6)
    if cfg.get("beard"):
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d2 = SDraw(ov)
        d2.polygon([(cx - 90, head_bot - 60), (cx + 90, head_bot - 60), (cx, head_bot + 44)],
                   fill=(90, 82, 76, 110))
        img.alpha_composite(ov)

    img = img.resize((w, h), Image.LANCZOS)
    # 轮廓描边：alpha膨胀一圈深色，立绘在任何背景上都清晰
    alpha = img.getchannel("A")
    edge = alpha.filter(ImageFilter.MaxFilter(9))
    outline_img = Image.new("RGBA", img.size, OUTLINE)
    outline_img.putalpha(edge.point(lambda v: 255 if v > 10 else 0))
    base = Image.new("RGBA", img.size, (0, 0, 0, 0))
    base.alpha_composite(outline_img)
    base.alpha_composite(img)
    return base
