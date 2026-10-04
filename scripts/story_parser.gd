class_name StoryParser
extends RefCounted
## 剧本解析器：把 story/chXX.txt 解析成步骤数组
## 一行一个步骤：
##   【背景】bg_xxx        → {type="bg", value}
##   【立绘】char_xxx      → {type="sprite", value}   （"无"=清空立绘）
##   【插图】cg_xxx.png    → {type="cg", value}
##   【选择】甲|乙|丙      → {type="choice", options:[...]}
##   【章节】标题          → {type="title", value}
##   角色名|台词           → {type="line", name, text}
##   普通文本              → {type="line", name="", text}

static func parse(path: String) -> Array[Dictionary]:
	var steps: Array[Dictionary] = []
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("剧本文件不存在: " + path)
		return steps
	var raw := f.get_as_text()
	f.close()
	for line in raw.split("\n"):
		var s: String = line.strip_edges()
		if s.is_empty():
			continue
		if s.begins_with("【章节】"):
			steps.append({"type": "title", "value": s.trim_prefix("【章节】")})
		elif s.begins_with("【背景】"):
			steps.append({"type": "bg", "value": s.trim_prefix("【背景】")})
		elif s.begins_with("【立绘】"):
			steps.append({"type": "sprite", "value": s.trim_prefix("【立绘】")})
		elif s.begins_with("【插图】"):
			steps.append({"type": "cg", "value": s.trim_prefix("【插图】")})
		elif s.begins_with("【选择】"):
			steps.append({"type": "choice", "options": _split_options(s.trim_prefix("【选择】"))})
		elif s.contains("|"):
			var pair := s.split("|", true, 1)
			steps.append({"type": "line", "name": pair[0].strip_edges(), "text": pair[1].strip_edges()})
		else:
			steps.append({"type": "line", "name": "", "text": s})
	return steps


static func _split_options(raw: String) -> Array[String]:
	var out: Array[String] = []
	for o in raw.split("|"):
		out.append(o.strip_edges())
	return out
