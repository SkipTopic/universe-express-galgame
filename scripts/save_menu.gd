extends Control
## 存档界面：9个槽位，保存/读取两用
## 打开方式：GameManager.open_save_mode = "save"（游戏中保存） 或 "load"（读档）

const SLOT_COUNT := 9
## true=保存模式，false=读取模式
var save_mode := true

@onready var title_label: Label = $Title
@onready var back_btn: Button = $Back


func _ready() -> void:
	save_mode = GameManager.open_save_mode != "load"
	title_label.text = "保存进度" if save_mode else "读取进度"
	for i in range(1, SLOT_COUNT + 1):
		var btn: Button = get_node("Grid/Slot%d" % i)
		_refresh_slot_text(btn, i)
		btn.pressed.connect(_on_slot.bind(i))
	back_btn.pressed.connect(_on_back)


func _refresh_slot_text(btn: Button, i: int) -> void:
	var d := GameManager.load_slot(i)
	if d.is_empty():
		btn.text = "%d\n\n空" % i
	else:
		var chapter: int = int(d.get("chapter", 1))
		var line: int = int(d.get("line", 0))
		btn.text = "%d\n第%d章 %s\n%s · 第%d行" % [i, chapter, d.get("title", ""), d.get("timestamp", ""), line]


func _on_slot(i: int) -> void:
	if save_mode:
		GameManager.save_slot(i)
		_refresh_all()
		title_label.text = "已保存到槽位 %d" % i
	elif GameManager.has_slot(i):
		GameManager.apply_slot(i)
		get_tree().change_scene_to_file("res://scenes/game.tscn")


func _refresh_all() -> void:
	for i in range(1, SLOT_COUNT + 1):
		_refresh_slot_text(get_node("Grid/Slot%d" % i), i)
	title_label.text = "保存进度" if save_mode else "读取进度"


func _on_back() -> void:
	if save_mode:
		# 从游戏里来：回到游戏现场（进度在GameManager里，会自动续播）
		get_tree().change_scene_to_file("res://scenes/game.tscn")
	else:
		get_tree().change_scene_to_file("res://scenes/main.tscn")
