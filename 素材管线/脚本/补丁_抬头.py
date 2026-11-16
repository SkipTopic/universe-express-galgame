# -*- coding: utf-8 -*-
"""补丁：在 提取小说.py 的 page_blocks 中过滤印刷抬头行"""
p = r"D:\我的godot项目\小时候的小说\工作区域\提取小说.py"
t = open(p, encoding="utf-8").read()
old = """        if not s or s.startswith("# "):
            continue
        if s.startswith(("〔拍摄：", "〔本页状态：", "〔页面信息：", "〔备注：", "〔整行划掉")):
            continue"""
new = """        if not s or s.startswith("# "):
            continue
        if re.match(r"^Subject[.．]?\\s*Date", s) or re.match(r"^(Subject|Date)[.．]\\s*$", s):
            continue                       # 本子印刷抬头误入正文
        if s.startswith(("〔拍摄：", "〔本页状态：", "〔页面信息：", "〔备注：", "〔整行划掉")):
            continue"""
assert old in t, "pattern not found"
t = t.replace(old, new)
open(p, "w", encoding="utf-8").write(t)
print("patched ok")
