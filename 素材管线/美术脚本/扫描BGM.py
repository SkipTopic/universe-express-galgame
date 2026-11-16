# -*- coding: utf-8 -*-
"""全盘扫描本机音乐文件 → 复制到 assets/audio/bgm/scan/（mp3/ogg/wav，≤25MB，跳过系统目录）"""
import os, shutil, hashlib

DST = r"D:\我的godot项目\小时候的小说\godot项目galgame\assets\audio\bgm\scan"
os.makedirs(DST, exist_ok=True)
SKIP_DIRS = {'windows', 'program files', 'program files (x86)', '$recycle.bin',
             'appdata', 'system volume information', 'godot项目galgame', 'android',
             'node_modules', '.git', 'godot', 'android-sdk', 'jdk-17', 'downloads'}
EXTS = {'.mp3', '.ogg', '.wav'}
found = []
seen_hash = set()

def scan(root, budget):
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIRS]
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext not in EXTS:
                continue
            p = os.path.join(dirpath, f)
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            if sz < 300_000 or sz > 25_000_000:
                continue
            try:
                h = hashlib.md5(open(p, 'rb').read(262144)).hexdigest()
            except OSError:
                continue
            if h in seen_hash:
                continue
            seen_hash.add(h)
            found.append(p)
            n += 1
            if n >= budget:
                return n
    return n

scan('C:/Users/admin', 40)
scan('D:/', 40)
scan('C:/Users/Public/Music', 10)
print('扫描到', len(found), '个音频文件')
copied = 0
for i, src in enumerate(sorted(found), 1):
    ext = os.path.splitext(src)[1].lower()
    dst = os.path.join(DST, 'bgm_scan%02d%s' % (i, ext))
    try:
        shutil.copy2(src, dst)
        copied += 1
        print('  ✓', os.path.basename(src), '->', os.path.basename(dst))
    except OSError as e:
        print('  ✗', src, e)
    if copied >= 24:
        break
print('已复制', copied, '个')
