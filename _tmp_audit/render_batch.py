# -*- coding: utf-8 -*-
# 动态审核批量渲染：模拟引擎立绘状态机，每个视觉状态变化采一个样，
# 4并行 godot --write-movie 渲染，末帧缩略拼图。用完即删。
import os, re, glob, subprocess, sys, shutil
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(ROOT)
GODOT = r'D:\Godot\Godot_v4.7.2-stable_win64.exe'
SUF = r'_(normal|smile|angry|sad|shock)$'

def base(v):
    return re.sub(SUF, '', v)

def simulate():
    samples = []
    for f in sorted(glob.glob(os.path.join(PROJ, 'story', 'ch*.txt'))):
        ch = int(re.search(r'ch(\d+)', os.path.basename(f)).group(1))
        raw = [t.strip() for t in open(f, encoding='utf-8').read().splitlines()]
        lines = [t for t in raw if t]
        n = len(lines)
        L = R = None; bg = None; cg = None; ln = 0
        seen = set()
        for i, t in enumerate(lines):
            if t.startswith('【背景】'):
                v = t[4:]
                if v != bg and ln + 1 <= n:
                    if (ch, v, L, R, None) not in seen:
                        seen.add((ch, v, L, R, None)); samples.append((ch, ln + 1, f'bg={v}'))
                bg = v
            elif t.startswith('【立绘】'):
                v = t[4:]
                oL, oR = L, R
                if v == '无':
                    L = R = None
                else:
                    b = base(v)
                    if R is not None and base(R) == b:
                        R = v
                    elif L is not None and base(L) == b:
                        L = v
                    else:
                        L = R if R is not None else None
                        R = v
                if (L, R) != (oL, oR) and ln + 1 <= n:
                    key = (ch, bg, L, R, None)
                    if key not in seen:
                        seen.add(key); samples.append((ch, ln + 1, f'spr={v}'))
            elif t.startswith('【插图】'):
                v = t[4:]
                if (ch, bg, L, R, v) not in seen and ln + 1 <= n:
                    seen.add((ch, bg, L, R, v)); samples.append((ch, ln + 1, f'cg={v}'))
                cg = v
            elif t.startswith('【转场】'):
                oL, oR = L, R
                L = R = None; cg = None
                if (L, R) != (oL, oR) and ln + 1 <= n:
                    key = (ch, bg, L, R, None)
                    if key not in seen:
                        seen.add(key); samples.append((ch, ln + 1, 'fade'))
            else:
                ln += 1
    return samples

def render(s):
    ch, line, tag = s
    name = f"c{ch:02d}_L{line:04d}"
    d = os.path.join(ROOT, 'frames', name)
    os.makedirs(d, exist_ok=True)
    env = dict(os.environ, TEST_CH=str(ch), TEST_LINE=str(line), TEST_FRAMES='10')
    try:
        subprocess.run([GODOT, '--path', PROJ, '--write-movie', os.path.join(d, 'f.png'),
                        '--fixed-fps', '5'], env=env, capture_output=True, timeout=150)
    except subprocess.TimeoutExpired:
        shutil.rmtree(d, ignore_errors=True)
        return (name, None, tag)
    pngs = sorted(glob.glob(os.path.join(d, 'f*.png')))
    if not pngs:
        return (name, None, tag)
    return (name, pngs[-1], tag)

def main():
    samples = simulate()
    print(f'采样点: {len(samples)}', flush=True)
    os.makedirs(os.path.join(ROOT, 'frames'), exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for i, r in enumerate(ex.map(render, samples)):
            results.append(r)
            if r[1] is None:
                print(f'  [MISS] {r[0]} {r[2]}', flush=True)
            if (i + 1) % 20 == 0:
                print(f'  进度 {i+1}/{len(samples)}', flush=True)
    # 拼 2×2 网格审查图
    ok = [r for r in results if r[1]]
    miss = [r for r in results if not r[1]]
    TILE, COLS, ROWS = 800, 2, 2
    per = COLS * ROWS
    sheets = []
    for si in range(0, len(ok), per):
        grp = ok[si:si + per]
        sheet = Image.new('RGB', (TILE * COLS, (TILE * 9 // 16) * ROWS + 8), (15, 15, 20))
        d = ImageDraw.Draw(sheet)
        for j, (name, png, tag) in enumerate(grp):
            im = Image.open(png).convert('RGB')
            im.thumbnail((TILE, TILE * 9 // 16))
            x, y = (j % COLS) * TILE, (j // COLS) * (TILE * 9 // 16)
            sheet.paste(im, (x, y))
            d.text((x + 8, y + 8), f'{name} {tag}', fill=(255, 220, 120))
        p = os.path.join(ROOT, 'sheets', f'sheet{len(sheets)+1:02d}.jpg')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        sheet.save(p, quality=88)
        sheets.append(p)
    print(f'完成 {len(ok)} 失败 {len(miss)}; 图纸 {len(sheets)} 张', flush=True)
    if miss:
        print('MISS明细:', [f'{r[0]} {r[2]}' for r in miss], flush=True)

if __name__ == '__main__':
    main()
