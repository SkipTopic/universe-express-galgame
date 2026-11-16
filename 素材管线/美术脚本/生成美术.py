# -*- coding: utf-8 -*-
"""生成全部galgame美术素材：背景/立绘/CG → godot项目galgame/assets/"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
from 美术引擎 import (new_bg, finish, vgrad, star_layer, noise, silhouette_mountains,
                    city_silhouette, vignette, light_beam, draw_character, SDraw, SS)

PROJ = r"D:\我的godot项目\小时候的小说\godot项目galgame"
BG = os.path.join(PROJ, "assets", "sprites", "bg")
CH = os.path.join(PROJ, "assets", "sprites", "characters")
CG = os.path.join(PROJ, "assets", "cg")
os.makedirs(BG, exist_ok=True); os.makedirs(CH, exist_ok=True); os.makedirs(CG, exist_ok=True)

def save(img, folder, name):
    img.save(os.path.join(folder, name + ".png"))
    print("  ✓", name)

# ═══════════ 背景 ═══════════
def bg_battlefield():
    img = new_bg()
    vgrad(img, 0, 540, (168, 108, 70), (94, 62, 84))       # 黄昏硝烟天
    vgrad(img, 540, 1080, (60, 44, 52), (28, 22, 30))
    star_layer(img, 60, 7, ymax=0.3, cmax=140)
    dr = SDraw(img)
    rnd = random.Random(3)
    for _ in range(9):                                       # 硝烟团
        x = rnd.uniform(0, 1920); y = rnd.uniform(180, 480); r = rnd.uniform(120, 320)
        dr.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(120, 96, 96))
    img = img.filter(ImageFilter.GaussianBlur(6))
    dr = SDraw(img)
    silhouette_mountains(img, 820, 40, (30, 24, 30), 11, 9)  # 远山废墟
    for _ in range(14):                                      # 碎石
        x = rnd.uniform(0, 1920); y = rnd.uniform(880, 1040)
        w = rnd.uniform(30, 120); h = rnd.uniform(14, 60)
        dr.polygon([(x, y), (x + w * 0.3, y - h), (x + w, y - h * 0.4), (x + w * 1.1, y)], fill=(38, 30, 36))
    light_beam(img, 1350, 300, 120, 700, (255, 200, 120), 40)  # 远处光束
    vignette(img, 100)
    noise(img, 5)
    return finish(img)

def bg_hall():
    img = new_bg()
    vgrad(img, 0, 1080, (64, 52, 40), (30, 24, 22))
    dr = SDraw(img)
    for k in range(6):                                       # 柱子
        x = 140 + k * 300
        dr.rectangle([x, 160, x + 70, 900], fill=(84, 68, 52))
        dr.rectangle([x + 8, 170, x + 20, 890], fill=(102, 84, 62))
    dr.rectangle([0, 860, 1920, 1080], fill=(40, 32, 28))    # 地板
    for y in range(880, 1080, 40):
        dr.line([(0, y), (1920, y)], fill=(48, 38, 34))
    dr.rectangle([720, 240, 1200, 620], fill=(56, 44, 36))   # 讲台背景墙
    dr.rectangle([760, 300, 1160, 340], fill=(150, 120, 70))
    dr.polygon([(860, 300), (1060, 300), (1100, 200), (820, 200)], fill=(120, 90, 56))  # 旗
    light_beam(img, 880, 120, 200, 800, (255, 220, 160), 34)
    vignette(img, 90); noise(img, 9)
    return finish(img)

def bg_dorm():
    img = new_bg()
    vgrad(img, 0, 620, (36, 42, 66), (24, 28, 46))
    vgrad(img, 620, 1080, (46, 40, 38), (30, 26, 26))
    star_layer(img, 90, 21, ymax=0.5)
    dr = SDraw(img)
    dr.rectangle([1180, 180, 1660, 620], fill=(60, 70, 100))  # 窗
    dr.line([(1420, 180), (1420, 620)], fill=(30, 36, 56), width=10)
    dr.line([(1180, 400), (1660, 400)], fill=(30, 36, 56), width=10)
    dr.rectangle([120, 660, 900, 1000], fill=(70, 58, 52))    # 床
    dr.rectangle([140, 620, 880, 700], fill=(180, 174, 160))  # 被子
    dr.rectangle([120, 640, 300, 720], fill=(220, 214, 198))  # 枕头
    vignette(img, 95); noise(img, 11)
    return finish(img)

def bg_hq():
    img = new_bg()
    vgrad(img, 0, 700, (40, 48, 78), (26, 30, 52))
    vgrad(img, 700, 1080, (70, 62, 58), (40, 36, 36))
    star_layer(img, 70, 31, ymax=0.55)
    dr = SDraw(img)
    dr.polygon([(1200, 100), (1880, 100), (1880, 720), (1200, 720)], fill=(18, 24, 44))  # 大窗
    for k in range(5):
        dr.line([(1200 + k * 170, 100), (1200 + k * 170, 720)], fill=(60, 70, 100), width=8)
    dr.rectangle([0, 720, 1920, 780], fill=(90, 84, 76))      # 柜台
    dr.rectangle([0, 780, 1920, 1080], fill=(52, 46, 44))
    for k in range(4):
        x = 200 + k * 420
        dr.rectangle([x, 560, x + 90, 720], fill=(110, 120, 140))  # 屏幕柱
    vignette(img, 85); noise(img, 13)
    return finish(img)

def bg_ship_corridor():
    img = new_bg()
    vgrad(img, 0, 1080, (22, 30, 44), (14, 18, 30))
    dr = SDraw(img)
    dr.polygon([(760, 0), (1160, 0), (1560, 1080), (360, 1080)], fill=(30, 40, 58))
    for k in range(5):                                       # 舷窗（沿透视）
        t = k / 4
        cx = 960 + (140 - 300) * (t - 0.5)
        w = 320 - 200 * t
        y = 260 + 160 * t
        dr.rounded_rectangle([960 - w / 2, y, 960 + w / 2, y + w * 0.62], 20, fill=(120, 150, 190))
    for k in range(6):                                       # 顶部灯带
        t = k / 5
        w = 240 - 150 * t
        dr.rectangle([960 - w / 2, 120 + 140 * t, 960 + w / 2, 132 + 140 * t], fill=(160, 200, 230))
    dr.rectangle([0, 940, 1920, 1080], fill=(20, 26, 40))
    vignette(img, 95); noise(img, 15)
    return finish(img)

def bg_deadplanet():
    img = new_bg()
    vgrad(img, 0, 560, (86, 44, 60), (40, 24, 44))
    vgrad(img, 560, 1080, (52, 36, 52), (30, 22, 34))
    star_layer(img, 50, 41, ymax=0.4, cmax=120)
    dr = SDraw(img)
    dr.ellipse([1500 - 90, 240 - 90, 1500 + 90, 240 + 90], fill=(170, 90, 90))                 # 红色卫星
    silhouette_mountains(img, 780, 70, (36, 26, 40), 43, 8)
    silhouette_mountains(img, 880, 40, (28, 20, 32), 44, 10)
    rnd = random.Random(45)
    for _ in range(8):                                       # 地面裂谷
        x = rnd.uniform(0, 1800); y = rnd.uniform(950, 1060)
        dr.line([(x, y), (x + rnd.uniform(80, 300), y + rnd.uniform(-30, 30))], fill=(20, 14, 24), width=8)
    vignette(img, 110); noise(img, 17)
    return finish(img)

def bg_castle():
    img = new_bg()
    vgrad(img, 0, 1080, (44, 36, 30), (26, 22, 20))
    dr = SDraw(img)
    for row in range(7):                                     # 石墙
        y = 60 + row * 150
        for k in range(8):
            x = (k * 260 + (row % 2) * 130) % 2100 - 90
            dr.rounded_rectangle([x, y, x + 240, y + 130], 14, fill=(70 + row * 3, 60 + row * 2, 52))
    dr.rectangle([300, 300, 460, 480], fill=(255, 190, 110)) # 窗光
    dr.rectangle([1460, 300, 1620, 480], fill=(255, 190, 110))
    dr.rectangle([0, 900, 1920, 1080], fill=(40, 34, 30))
    for x in (360, 1540):                                    # 烛台
        dr.rectangle([x - 8, 480, x + 8, 760], fill=(90, 76, 60))
        dr.ellipse([x - 26, 440, x + 26, 496], fill=(255, 210, 130))
    light_beam(img, 300, 260, 220, 600, (255, 200, 120), 40)
    light_beam(img, 1460, 260, 220, 600, (255, 200, 120), 40)
    vignette(img, 100); noise(img, 19)
    return finish(img)

def bg_eden():
    img = new_bg()
    vgrad(img, 0, 640, (110, 175, 235), (185, 220, 245))
    dr = SDraw(img)
    rnd = random.Random(51)
    for _ in range(7):                                       # 云
        x = rnd.uniform(-100, 1800); y = rnd.uniform(80, 420); r = rnd.uniform(90, 190)
        dr.ellipse([x, y, x + r * 2.2, y + r * 0.8], fill=(245, 250, 252))
    vgrad(img, 640, 1080, (120, 190, 105), (70, 140, 80))
    dr.ellipse([1560 - 190, 660 - 190, 1560 + 190, 660 + 190], fill=(60, 120, 75))                # 大树冠
    dr.rectangle([1530, 640, 1590, 800], fill=(96, 66, 48))
    rnd2 = random.Random(52)
    for _ in range(40):                                      # 花
        x = rnd2.uniform(0, 1920); y = rnd2.uniform(760, 1050)
        r2 = rnd2.uniform(4, 9)
        c = rnd2.choice([(240, 240, 250), (250, 220, 120), (235, 150, 160)])
        dr.ellipse([x - r2, y - r2, x + r2, y + r2], fill=c)
    noise(img, 21)
    return finish(img)

def bg_nightmarket():
    img = new_bg()
    vgrad(img, 0, 640, (16, 20, 44), (30, 26, 52))
    star_layer(img, 80, 61, ymax=0.45)
    dr = SDraw(img)
    dr.ellipse([300 - 64, 170 - 64, 300 + 64, 170 + 64], fill=(235, 230, 210))                # 双月
    dr.ellipse([520 - 40, 120 - 40, 520 + 40, 120 + 40], fill=(210, 215, 230))
    city_silhouette(img, 700, (22, 18, 36), 62, cols=16, hmin=200, hmax=520)
    vgrad(img, 700, 1080, (40, 30, 34), (22, 18, 22))
    rnd = random.Random(63)
    for k in range(9):                                       # 灯笼
        x = 120 + k * 210 + rnd.uniform(-30, 30); y = 300 + rnd.uniform(-40, 40)
        dr.rounded_rectangle([x - 34, y, x + 34, y + 64], 26, fill=(235, 120, 70))
        dr.line([(x, y - 40), (x, y)], fill=(120, 90, 70), width=5)
    for k in range(5):                                       # 摊位棚
        x = 100 + k * 400
        dr.rectangle([x, 700, x + 300, 980], fill=(34, 26, 30))
        dr.polygon([(x - 30, 700), (x + 330, 700), (x + 300, 620), (x, 620)], fill=(70, 40, 44))
        dr.rectangle([x + 40, 740, x + 260, 900], fill=(255, 200, 120))
    dr.rectangle([0, 980, 1920, 1080], fill=(24, 20, 24))
    vignette(img, 100); noise(img, 23)
    return finish(img)

def bg_hospital():
    img = new_bg()
    vgrad(img, 0, 760, (188, 200, 208), (160, 176, 188))
    vgrad(img, 760, 1080, (150, 158, 166), (120, 130, 140))
    dr = SDraw(img)
    dr.rectangle([1250, 140, 1800, 640], fill=(214, 228, 234))  # 窗
    dr.line([(1525, 140), (1525, 640)], fill=(140, 156, 168), width=8)
    dr.rectangle([100, 640, 950, 1010], fill=(226, 230, 234))   # 病床
    dr.rectangle([100, 600, 950, 680], fill=(200, 206, 214))
    dr.rectangle([60, 1010, 990, 1060], fill=(110, 118, 128))
    dr.rectangle([1500, 520, 1560, 1010], fill=(140, 148, 158)) # 输液架
    dr.rectangle([1150, 260, 1420, 460], fill=(180, 200, 210))  # 显示器
    noise(img, 25)
    return finish(img)

def bg_snow_village():
    img = new_bg()
    vgrad(img, 0, 620, (140, 160, 185), (185, 200, 218))
    dr = SDraw(img)
    silhouette_mountains(img, 640, 60, (150, 168, 192), 71, 6)
    vgrad(img, 620, 1080, (205, 214, 228), (175, 188, 205))
    rnd = random.Random(72)
    for hx, hy, s in [(300, 620, 1.0), (860, 600, 1.15), (1420, 635, 0.9)]:  # 雪屋
        dr.polygon([(hx - 200 * s, hy), (hx + 200 * s, hy), (hx + 140 * s, hy - 240 * s), (hx - 140 * s, hy - 240 * s)],
                   fill=(96, 84, 76))
        dr.polygon([(hx - 230 * s, hy - 230 * s), (hx + 230 * s, hy - 230 * s), (hx, hy - 380 * s)],
                   fill=(214, 222, 234))
        dr.rectangle([hx - 50 * s, hy - 140 * s, hx + 50 * s, hy], fill=(70, 56, 50))
        dr.rectangle([hx - 14 * s, hy - 330 * s, hx + 14 * s, hy - 250 * s], fill=(90, 80, 74))
    for _ in range(220):                                     # 雪
        x = rnd.uniform(0, 1920); y = rnd.uniform(0, 1080); r = rnd.uniform(2, 6)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(235, 240, 248))
    noise(img, 27)
    return finish(img)

def bg_corridor_b65():
    img = new_bg()
    vgrad(img, 0, 1080, (16, 16, 20), (8, 8, 12))
    dr = SDraw(img)
    dr.polygon([(700, 0), (1220, 0), (1500, 1080), (420, 1080)], fill=(24, 24, 30))
    for k in range(6):                                       # 应急灯
        t = k / 5
        w = 200 - 120 * t
        dr.rectangle([960 - w / 2, 160 + 150 * t, 960 + w / 2, 168 + 150 * t], fill=(200, 60, 50))
    for k in range(5):                                       # 管线
        y = 240 + k * 40
        dr.line([(300, y), (1620, y)], fill=(40, 40, 48), width=10)
    dr.rectangle([0, 900, 1920, 1080], fill=(14, 14, 18))
    vignette(img, 120); noise(img, 29)
    return finish(img)

def bg_server():
    img = new_bg()
    vgrad(img, 0, 1080, (10, 12, 16), (6, 7, 10))
    dr = SDraw(img)
    rnd = random.Random(81)
    for k in range(6):                                       # 服务器架
        x = 120 + k * 300
        dr.rectangle([x, 120, x + 220, 1000], fill=(20, 22, 28))
        for y in range(150, 980, 46):
            dr.rectangle([x + 12, y, x + 208, y + 34], fill=(28, 32, 40))
            for led in range(4):
                lx = x + 22 + led * 44
                c = rnd.choice([(80, 220, 140), (220, 180, 80), (90, 140, 220)])
                if rnd.random() < 0.8:
                    dr.rectangle([lx, y + 12, lx + 16, y + 22], fill=c)
    vignette(img, 120); noise(img, 31)
    return finish(img)

def bg_street_night():
    img = new_bg()
    vgrad(img, 0, 620, (14, 16, 34), (26, 22, 42))
    star_layer(img, 60, 91, ymax=0.4)
    dr = SDraw(img)
    city_silhouette(img, 660, (18, 16, 30), 92, cols=18, hmin=260, hmax=560,
                    windows=(235, 200, 130))
    vgrad(img, 660, 1080, (30, 26, 30), (18, 16, 20))
    for k in range(5):                                       # 路灯
        x = 200 + k * 400
        dr.rectangle([x, 420, x + 12, 940], fill=(50, 48, 54))
        dr.ellipse([x - 26, 396, x + 38, 442], fill=(255, 220, 150))
        light_beam(img, x, 440, 60, 520, (255, 220, 150), 26)
    rnd = random.Random(93)
    for _ in range(10):                                      # 人影
        x = rnd.uniform(100, 1800); y = 980; h = rnd.uniform(120, 210); w = h * 0.34
        dr.rounded_rectangle([x - w / 2, y - h, x + w / 2, y], 26, fill=(12, 10, 14))
    vignette(img, 105); noise(img, 33)
    return finish(img)

def bg_space():
    img = new_bg()
    vgrad(img, 0, 1080, (6, 7, 14), (10, 10, 22))
    star_layer(img, 260, 101, ymax=1.0, rmax=2.6)
    dr = SDraw(img)
    rnd = random.Random(102)
    for _ in range(3):                                       # 星云
        x, y = rnd.uniform(200, 1700), rnd.uniform(150, 800)
        r = rnd.uniform(200, 380)
        c = rnd.choice([(70, 50, 120), (40, 70, 130), (110, 60, 100)])
        dr.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=c)
    img = img.filter(ImageFilter.GaussianBlur(30))
    star_layer(img, 140, 103, ymax=1.0)
    return finish(img)

def bg_express_office():
    img = new_bg()
    vgrad(img, 0, 1080, (40, 44, 62), (26, 28, 42))
    dr = SDraw(img)
    dr.rectangle([0, 760, 1920, 820], fill=(80, 84, 96))     # 柜台
    dr.rectangle([0, 820, 1920, 1080], fill=(46, 48, 58))
    for k in range(3):                                       # 委托屏
        x = 260 + k * 560
        dr.rounded_rectangle([x, 300, x + 440, 700], 16, fill=(22, 26, 40))
        dr.rounded_rectangle([x + 20, 320, x + 420, 660], 10, fill=(60, 90, 130))
        dr.rectangle([x + 40, 360, x + 240, 390], fill=(200, 210, 225))
        dr.rectangle([x + 40, 410, x + 300, 434], fill=(150, 165, 190))
    noise(img, 35)
    return finish(img)

def bg_war_end():  # 旧战场白昼版（给回忆）
    img = new_bg()
    vgrad(img, 0, 500, (190, 170, 140), (120, 110, 105))
    vgrad(img, 500, 1080, (80, 74, 70), (44, 40, 40))
    dr = SDraw(img)
    rnd = random.Random(111)
    silhouette_mountains(img, 760, 50, (60, 54, 52), 111, 8)
    for _ in range(10):
        x = rnd.uniform(0, 1920); y = rnd.uniform(900, 1050)
        w = rnd.uniform(40, 160); h = rnd.uniform(20, 70)
        dr.polygon([(x, y), (x + w * 0.3, y - h), (x + w, y - h * 0.4), (x + w * 1.1, y)], fill=(52, 46, 46))
    vignette(img, 95); noise(img, 37)
    return finish(img)

BGS = {
    "bg_battlefield": bg_battlefield, "bg_hall": bg_hall, "bg_dorm": bg_dorm,
    "bg_hq": bg_hq, "bg_ship_corridor": bg_ship_corridor, "bg_deadplanet": bg_deadplanet,
    "bg_castle": bg_castle, "bg_eden": bg_eden, "bg_nightmarket": bg_nightmarket,
    "bg_hospital": bg_hospital, "bg_snow_village": bg_snow_village,
    "bg_corridor_b65": bg_corridor_b65, "bg_server": bg_server,
    "bg_street_night": bg_street_night, "bg_space": bg_space,
    "bg_express_office": bg_express_office, "bg_war_end": bg_war_end,
}

# ═══════════ 立绘 ═══════════
CHARS = {
    "char_me":     dict(hair=(40, 36, 40), hair_style="short", eyes=(70, 100, 150),
                        outfit=(44, 58, 96), outfit_shade=(34, 46, 78), collar=(200, 200, 205),
                        pants=(40, 44, 60)),
    "char_charlie": dict(hair=(122, 88, 60), hair_style="short", eyes=(120, 150, 120),
                         outfit=(226, 222, 214), outfit_shade=(196, 192, 184), collar=(90, 96, 120),
                         tie=(150, 70, 70), glasses=True, pants=(70, 74, 92)),
    "char_xiaolin": dict(hair=(28, 26, 32), hair_style="long", eyes=(110, 90, 140),
                         outfit=(150, 150, 158), outfit_shade=(126, 126, 134), pants=(120, 118, 126),
                         expression="calm", blush=False, skin=(255, 236, 220)),
    "char_photo":  dict(hair=(120, 126, 138), hair_style="short", eyes=(230, 190, 90),
                        outfit=(140, 146, 158), outfit_shade=(116, 122, 134), collar=(220, 220, 224),
                        pants=(90, 94, 104), blush=True),
    "char_bi":     dict(hair=(80, 76, 72), hair_style="short", eyes=(90, 90, 95),
                        outfit=(84, 88, 96), outfit_shade=(66, 70, 78), collar=(220, 218, 210),
                        tie=(90, 100, 130), beard=True, pants=(60, 62, 70)),
    "char_lilei":  dict(hair=(34, 30, 30), hair_style="buzz", eyes=(100, 130, 100),
                        outfit=(58, 70, 92), outfit_shade=(46, 56, 76), collar=(70, 82, 104),
                        pants=(52, 58, 74), blush=True),
    "char_xilang": dict(hair=(210, 208, 200), hair_style="white_old", eyes=(120, 120, 130),
                        outfit=(52, 62, 86), outfit_shade=(40, 48, 68), coat=True,
                        collar=(200, 195, 180), pants=(44, 50, 66)),
}

def gen_chars():
    for name, cfg in CHARS.items():
        img = draw_character(cfg=cfg)
        img.save(os.path.join(CH, name + ".png"))
        print("  ✓", name)

# ═══════════ CG ═══════════
def cg_nuclear():
    img = new_bg()
    vgrad(img, 0, 700, (250, 246, 238), (255, 220, 170))
    vgrad(img, 700, 1080, (120, 90, 70), (40, 30, 30))
    dr = SDraw(img)
    dr.ellipse([960 - 260, 520 - 260, 960 + 260, 520 + 260], fill=(255, 250, 240))               # 光核
    dr.ellipse([960 - 380, 520 - 380, 960 + 380, 520 + 380], fill=None, outline=(255, 230, 190), width=26)
    for k in range(12):                                      # 蘑菇云
        ang = k / 12 * math.pi * 2
        x = 960 + math.cos(ang) * 420; y = 480 + math.sin(ang) * 190
        r = 120 + (k % 3) * 50
        dr.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=(240, 210, 170))
    img = img.filter(ImageFilter.GaussianBlur(14))
    vignette(img, 130)
    return finish(img)

def cg_wake():
    img = new_bg()
    vgrad(img, 0, 1080, (232, 236, 240), (206, 212, 220))
    dr = SDraw(img)
    dr.rectangle([400, 700, 1520, 1080], fill=(236, 240, 244))  # 天花板下被褥
    for k in range(5):
        dr.line([(420 + k * 230, 700), (420 + k * 230, 1080)], fill=(214, 220, 228), width=10)
    vgrad(img, 0, 320, (210, 216, 224), (232, 236, 240))
    noise(img, 41)
    return finish(img)

def cg_farewell():
    img = new_bg()
    vgrad(img, 0, 700, (70, 66, 80), (40, 38, 48))
    vgrad(img, 700, 1080, (52, 50, 60), (34, 32, 40))
    dr = SDraw(img)
    dr.rectangle([420, 640, 1500, 860], fill=(225, 223, 218))  # 白布
    dr.polygon([(420, 860), (1500, 860), (1420, 1000), (500, 1000)], fill=(200, 198, 194))
    for x in (600, 960, 1320):                                # 白蜡烛
        dr.rectangle([x - 16, 700, x + 16, 1000], fill=(235, 232, 224))
        dr.ellipse([x - 26, 664, x + 26, 712], fill=(255, 214, 130))
    vignette(img, 110); noise(img, 43)
    return finish(img)

def cg_launch():
    img = bg_space()
    dr = SDraw(img)
    dr.polygon([(880, 1080), (1040, 1080), (1000, 700), (920, 700)], fill=(255, 200, 110))   # 尾焰
    dr.polygon([(920, 1080), (1000, 1080), (980, 760), (940, 760)], fill=(255, 245, 220))
    dr.ellipse([880, 560, 1040, 780], fill=(210, 214, 222))  # 船体
    dr.polygon([(880, 620), (1040, 620), (960, 520)], fill=(230, 232, 238))
    img = img.filter(ImageFilter.GaussianBlur(2))
    return finish(img)

CGS = {"cg_nuclear": cg_nuclear, "cg_wake": cg_wake, "cg_farewell": cg_farewell, "cg_launch": cg_launch}

if __name__ == "__main__":
    print("背景...")
    for name, fn in BGS.items():
        save(fn(), BG, name)
    print("立绘...")
    gen_chars()
    print("CG...")
    for name, fn in CGS.items():
        save(fn(), CG, name)
    print("全部完成")
