extends Node
## 全局游戏状态 + 存档系统（9个手动槽位 + 1个自动存档槽）
## 注册为自动加载单例（Autoload），名字：GameManager
## 生命周期：随进程常驻，只保存跨场景的进度数据，不承载任何演出逻辑

const SAVE_DIR := "user://saves/"
const SLOT_COUNT := 9
## 自动存档固定在槽位0，不与玩家手动槽位（1~9）冲突
const AUTO_SLOT := 0
## 最后一章编号（与 story/ 下 chXX.txt 的最大编号保持一致）
const LAST_CHAPTER := 12

## 12章的章节标题（与 story/chXX.txt 的【章节】行对应，存档界面显示用）
const CHAPTER_TITLES := {
	1: "战争结束", 2: "晓琳", 3: "老船长的故事", 4: "船上日常",
	5: "死亡星球与伊甸园", 6: "凯特星之夜", 7: "口琴与往事", 8: "营救",
	9: "B65楼", 10: "晓琳之死", 11: "核弹与梦醒", 12: "尾声",
}

## 当前阅读进度（存档内容就是这三个变量）
var current_chapter: int = 1
var current_line: int = 0
## 玩家在【选择】处做出的选择，按出现顺序记录（1基）
var choice_history: Array[int] = []
## 已读进度：章节号 → 该章已读到的最大行号（供"快进"和"跳过已读"判断）
var read_progress: Dictionary = {}
## 存档界面打开模式："save"=保存，"load"=读取
var open_save_mode: String = "load"


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(SAVE_DIR)


## ── 已读记录 ──
## 标记某章的第 line 行已读过
func mark_read(ch: int, line: int) -> void:
	if line > int(read_progress.get(ch, 0)):
		read_progress[ch] = line


## 某章第 line 行是否已读过
func is_read(ch: int, line: int) -> bool:
	return line <= int(read_progress.get(ch, 0))


## 章节标题查询
func chapter_title(ch: int) -> String:
	return CHAPTER_TITLES.get(ch, "第%d章" % ch)


## ── 存档 ──
## slot: 0=自动存档，1~9=手动槽位。保存当前进度，返回是否成功
func save_slot(slot: int) -> bool:
	if slot < AUTO_SLOT or slot > SLOT_COUNT:
		return false
	var data := {
		"chapter": current_chapter,
		"line": current_line,
		"title": chapter_title(current_chapter),
		"choices": choice_history,
		"read": read_progress,
		"timestamp": Time.get_datetime_string_from_system(false, true),
	}
	var f := FileAccess.open(SAVE_DIR + "slot_%d.json" % slot, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(data, "  "))
	f.close()
	return true


## ── 读档 ──
## 返回数据字典；空槽位返回空字典 {}
func load_slot(slot: int) -> Dictionary:
	var f := FileAccess.open(SAVE_DIR + "slot_%d.json" % slot, FileAccess.READ)
	if f == null:
		return {}
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if parsed is Dictionary:
		return parsed
	return {}


## 槽位是否有存档
func has_slot(slot: int) -> bool:
	return FileAccess.file_exists(SAVE_DIR + "slot_%d.json" % slot)


## 最近使用（有存档）的手动槽位号；没有则返回 0
func latest_slot() -> int:
	var best := 0
	var best_time := ""
	for i in range(1, SLOT_COUNT + 1):
		var d := load_slot(i)
		if not d.is_empty():
			var ts: String = d.get("timestamp", "")
			if ts > best_time:
				best_time = ts
				best = i
	return best


## 应用读档：把槽位数据恢复到当前进度
func apply_slot(slot: int) -> bool:
	var d := load_slot(slot)
	if d.is_empty():
		return false
	current_chapter = int(d.get("chapter", 1))
	current_line = int(d.get("line", 0))
	choice_history = _to_int_array(d.get("choices", []))
	read_progress = _to_int_dict(d.get("read", {}))
	return true


func _to_int_array(src: Variant) -> Array[int]:
	var out: Array[int] = []
	if src is Array:
		for v in src:
			out.append(int(v))
	return out


## JSON 的 key 一定是字符串，读回来要还原成 int 键
func _to_int_dict(src: Variant) -> Dictionary:
	var out: Dictionary = {}
	if src is Dictionary:
		for k in src:
			out[int(k)] = int(src[k])
	return out


## ── 自动存档 ──
## 每推进一句台词/每次章节切换都会调用，保证中途退出也能续玩
func autosave() -> bool:
	return save_slot(AUTO_SLOT)


func has_auto() -> bool:
	return has_slot(AUTO_SLOT)


## 读取自动存档到当前进度；返回是否成功
func load_auto() -> bool:
	return apply_slot(AUTO_SLOT)
