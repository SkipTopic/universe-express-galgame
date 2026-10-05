class_name StoryParser
extends RefCounted
## 剧本解析器：把 story/chXX.txt 解析成步骤数组
## 一行一个步骤：
##   【章节】标题            → {type="title", value}
##   【背景】bg_xxx          → {type="bg", value}
##   【立绘】char_xxx        → {type="sprite", value}   （"无"=清空立绘）
##   【插图】cg_xxx.png      → {type="cg", value}
##   【音乐】bgm_xxx         → {type="bgm", value}      （"无"=停止）
##   【音效】sfx_xxx         → {type="sfx", value}
##   【标签】label_name      → {type="label", value}     （跳转目标，演出时自动跳过）
##   【跳转】label_name      → {type="jump", value}      （跳到同名【标签】处）
##   【选择】选项甲:标签A|选项乙:标签B → {type="choice", options:[{text,target}]}
##      冒号后可省略；省略则选择后顺序继续
##   角色名|台词             → {type="line", name, text}
##   普通文本                → {type="line", name="", text}

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
		elif s.begins_with("【转场】"):
			steps.append({"type": "fade", "value": s.trim_prefix("【转场】")})
		elif s.begins_with("【音乐】"):
			steps.append({"type": "bgm", "value": s.trim_prefix("【音乐】")})
		elif s.begins_with("【音效】"):
			steps.append({"type": "sfx", "value": s.trim_prefix("【音效】")})
		elif s.begins_with("【标签】"):
			steps.append({"type": "label", "value": s.trim_prefix("【标签】")})
		elif s.begins_with("【跳转】"):
			steps.append({"type": "jump", "value": s.trim_prefix("【跳转】")})
		elif s.begins_with("【选择】"):
			steps.append({"type": "choice", "options": _split_options(s.trim_prefix("【选择】"))})
		elif s.contains("|"):
			var pair := s.split("|", true, 1)
			steps.append({"type": "line", "name": pair[0].strip_edges(), "text": pair[1].strip_edges()})
		else:
			steps.append({"type": "line", "name": "", "text": s})
	return steps


## "文本:跳转标签|文本:跳转标签" → [{"text":..., "target":...}, ...]
## 兼容全角冒号；跳转目标可省略
static func _split_options(raw: String) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for o in raw.split("|"):
		var item: String = o.strip_edges().replace("：", ":")
		var text: String = item
		var target: String = ""
		if item.contains(":"):
			var pair := item.split(":", true, 1)
			text = pair[0].strip_edges()
			target = pair[1].strip_edges()
		out.append({"text": text, "target": target})
	return out
