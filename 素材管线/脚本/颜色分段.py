# -*- coding: utf-8 -*-
"""行级颜色分段：把手写转写里的墨色标记变成 (文字, 颜色) 段。
支持：[红笔]〔红〕〔红色墨水〕行首/行中切换；[/红笔]〔/红色〕结束；
     （红字）（红字，箭头…）行尾注 → 回染前段；（括号内为红字）→ 回染前一个括号段；
     （X为红字）→ 把前段中的 X 单独染色；〔以下恢复红色墨水〕等切换。
颜色：'' 默认黑、'r' 红、'b' 蓝、'p' 铅笔灰。
strip_meta=True（网页干净版）：非颜色元标注（涂黑/纸片/右对齐…）直接丢弃；
strip_meta=False（Word复刻版）：非颜色元标注保留在文字里（由上层灰显）。
"""
import re

TOKEN = re.compile(r"(〔[^〕]{0,120}〕|\[[^\]\n]{0,60}\]|[（(][^（）()\n]{0,90}[）)])")
META = re.compile(r"划掉|涂黑|涂改|不可辨|墨点|圈出|右对齐|纸片|页面信息|上注|下注|补字|旁注|标注|批注|括号框住|箭头")
END_NOTE = re.compile(r"^(红字|红笔|蓝字|蓝笔|黑字|黑笔)([，,][^）]*)?$")
WEI = re.compile(r"^(.{1,30})为(红字|蓝字|黑字)$")
PAREN_COLOR = {"红": "r", "蓝": "b", "黑": ""}

def _marker_color(inner):
    if META.search(inner): return "drop"
    if inner.startswith("/"): return ""
    if "恢复" in inner: return "" if "红" not in inner else "r"
    if "红" in inner: return "r"
    if "蓝" in inner: return "b"
    if re.search(r"铅笔|淡笔", inner): return "p"
    if re.search(r"黑|墨水", inner): return ""
    return "keep"

def _recolor_last(segs, c):
    if segs: segs[-1][1] = c

def line_segments(s, strip_meta=False):
    s = re.sub(r"\](?=\s*[：:])", "〕", s)   # 混用括号归一："]：" → "〕："
    segs = []
    box = {"cur": "", "col": ""}
    def flush():
        t = box["cur"].strip()
        if t: segs.append([t, box["col"]])
        box["cur"] = ""
    for tok in TOKEN.split(s):
        if not tok: continue
        if TOKEN.fullmatch(tok):
            inner = tok[1:-1].strip()
            if tok[0] in "（(":
                if END_NOTE.match(inner):
                    c = PAREN_COLOR.get(inner[0], "")
                    flush()
                    if segs: _recolor_last(segs, c)
                    else: box["col"] = c
                    continue
                if inner.startswith("括号内为"):
                    c = PAREN_COLOR.get(inner[4], "")
                    flush()
                    if segs: _recolor_last(segs, c)
                    continue
                m = WEI.match(inner)
                if m:
                    target, c = m.group(1), PAREN_COLOR.get(m.group(2)[0], "")
                    flush()
                    for i in range(len(segs) - 1, -1, -1):
                        if target in segs[i][0]:
                            pre, post = segs[i][0].split(target, 1)
                            rep = []
                            if pre.strip(): rep.append([pre, segs[i][1]])
                            rep.append([target, c])
                            if post.strip(): rep.append([post, segs[i][1]])
                            segs[i:i + 1] = rep
                            break
                    continue
                if strip_meta and re.search(r"批注|框住|箭头|指向|标注|红字|红笔|蓝字|蓝笔|黑字|黑笔", inner):
                    continue
                flush()
                box["cur"] = inner
                flush()
                continue
            c = _marker_color(inner)
            if c == "drop":
                if strip_meta: continue
                box["cur"] += tok; continue
            if c == "keep":
                box["cur"] += tok; continue
            flush(); box["col"] = c; continue
        box["cur"] += tok
    flush()
    if strip_meta:
        segs = [[re.sub(r"[\[〔\]〕]", "", x).strip(), c] for x, c in segs]
        segs = [[x, c] for x, c in segs if x]
    return segs


def strip_figures(lines):
    """跨行、嵌套感知地移除〔图...〕图注跨度。
    lines: 原始行列表。返回 (cleaned, full_fig, has_fig)
      cleaned:  [(行号1-based, 去掉图注跨度后的文本)]
      full_fig: 整行都属于图注的行号集合（Word灰显用）
      has_fig:  含图注跨度的行号集合
    """
    text = "\n".join(lines)
    n = len(text)
    starts = [0]
    for l in lines:
        starts.append(starts[-1] + len(l) + 1)
    spans = []
    i = 0
    while i < n - 1:
        if text[i:i + 2] == "〔图":
            depth = 0
            j = i
            while j < n:
                if text[j] == "〔": depth += 1
                elif text[j] == "〕":
                    depth -= 1
                    if depth == 0: break
                j += 1
            spans.append((i, min(j + 1, n)))
            i = j + 1
        else:
            i += 1
    covered = [False] * n
    for a, b in spans:
        for k in range(a, b): covered[k] = True
    cleaned, full_fig, has_fig = [], set(), set()
    for i, l in enumerate(lines):
        a = starts[i]; b = a + len(l)
        seg = "".join(text[k] for k in range(a, b) if not covered[k])
        if l and all(covered[a:b]): full_fig.add(i + 1)
        if any(covered[a:b]): has_fig.add(i + 1)
        cleaned.append((i + 1, seg))
    return cleaned, full_fig, has_fig
