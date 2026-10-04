extends Control
## 章节播放器：读取 story/chXX.txt 剧本并演出
## 进度保存在 GameManager.current_chapter / current_line（配合9槽存档 + 自动存档）
## 剧本格式见 story/格式说明.txt（记事本直接改）

const CPS := 28.0
const DIR_BG := "res://assets/sprites/bg/"
const DIR_CHAR := "res://assets/sprites/characters/"
const DIR_CG := "res://assets/cg/"

var steps: Array[Dictionary] = []
var idx: int = 0            # 当前步骤下标
var line_no: int = 0        # 已播放的台词行数（存档用）
var typing: bool = false
var awaiting_choice: bool = false
var _typed_chars: float = 0.0

@onready var bg: TextureRect = $Bg
@onready var char_l: TextureRect = $CharL
@onready var char_r: TextureRect = $CharR
@onready var cg_rect: TextureRect = $CG
@onready var chapter_label: Label = $ChapterLabel
@onready var name_plate: Panel = $UILayer/VNBox/NamePlate
@onready var name_label: Label = $UILayer/VNBox/NamePlate/NameLabel
@onready var text_label: RichTextLabel = $UILayer/VNBox/Text
@onready var next_arrow: Label = $UILayer/VNBox/NextArrow
@onready var choices: VBoxContainer = $UILayer/Choices


func _ready() -> void:
	$UILayer/MenuBtn.pressed.connect(_open_save)
	if not _load_chapter(GameManager.current_chapter):
		_next_chapter()


func _open_save() -> void:
	GameManager.open_save_mode = "save"
	get_tree().change_scene_to_file("res://scenes/save_menu.tscn")


## ── 章节装载 ──
## 返回 true 表示已装载并停在某个待玩家交互的步骤上
func _load_chapter(ch: int) -> bool:
	var path := "res://story/ch%02d.txt" % ch
	if not FileAccess.file_exists(path):
		push_warning("剧本缺失: " + path)
		return false
	steps = StoryParser.parse(path)
	if steps.is_empty():
		push_warning("剧本为空: " + path)
		return false

	idx = 0
	line_no = 0
	chapter_label.text = "第%d章 · %s" % [ch, GameManager.chapter_title(ch)]

	# 读档恢复：快进到存档行号之前（背景/立绘照常应用，台词只计数不显示）
	var target: int = GameManager.current_line
	while idx < steps.size() and line_no < target:
		var st: Dictionary = steps[idx]
		match String(st.get("type", "")):
			"bg":
				_apply_bg(String(st.get("value", "")))
			"sprite":
				_apply_sprite(String(st.get("value", "")))
			"line":
				line_no += 1
		idx += 1
	GameManager.current_line = line_no

	if idx >= steps.size():
		return false
	_advance()
	return true


func _next_chapter() -> void:
	while GameManager.current_chapter < GameManager.LAST_CHAPTER:
		GameManager.current_chapter += 1
		GameManager.current_line = 0
		if _load_chapter(GameManager.current_chapter):
			return
	_return_to_title()


## 切回标题画面。defer 是必须的：本函数可能处在 _ready 的调用栈里，
## 此刻 SceneTree 正在添加/删除子节点，同步切场景会报
## "Parent node is busy adding/removing children" 并静默失败。
func _return_to_title() -> void:
	GameManager.autosave()
	_goto_main.call_deferred()


func _goto_main() -> void:
	get_tree().change_scene_to_file("res://scenes/main.tscn")


## ── 推进：自动步骤连续执行，遇到对话 / 选项 / CG 停下等玩家 ──
func _advance() -> void:
	while idx < steps.size():
		var st: Dictionary = steps[idx]
		match String(st.get("type", "")):
			"title":
				chapter_label.text = String(st.get("value", ""))
			"bg":
				_apply_bg(String(st.get("value", "")))
			"sprite":
				_apply_sprite(String(st.get("value", "")))
			"cg":
				# CG 是一次点击关闭的展示步骤，停下等待
				if _apply_cg(String(st.get("value", ""))):
					idx += 1
					return
			"line":
				_show_line(st)
				idx += 1
				return
			"choice":
				_show_choices(st.get("options", []))
				idx += 1
				return
			_:
				push_warning("未知指令类型: %s" % str(st))
		idx += 1
	_next_chapter()


func _show_line(st: Dictionary) -> void:
	var who: String = String(st.get("name", ""))
	name_plate.visible = who != ""
	name_label.text = who
	text_label.text = String(st.get("text", ""))
	text_label.visible_characters = 0
	_typed_chars = 0.0
	typing = true
	next_arrow.visible = false
	line_no += 1
	GameManager.current_line = line_no
	GameManager.autosave()


## ── 素材 ──
## 把剧本里的文件名解析成真实存在的资源路径；找不到返回空串
func _resolve(dir: String, file_name: String) -> String:
	var path := dir + file_name
	if ResourceLoader.exists(path):
		return path
	# 容错：剧本里写 .jpg 但实际素材导出成了 .png
	if file_name.get_extension().to_lower() in ["jpg", "jpeg"]:
		var alt := dir + file_name.get_basename() + ".png"
		if ResourceLoader.exists(alt):
			return alt
	push_warning("素材缺失: " + path)
	return ""


func _apply_bg(value: String) -> void:
	var path := _resolve(DIR_BG, value + ".png")
	if not path.is_empty():
		bg.texture = load(path) as Texture2D


func _apply_sprite(value: String) -> void:
	if value == "无":
		char_l.visible = false
		char_r.visible = false
		return
	var path := _resolve(DIR_CHAR, value + ".png")
	if path.is_empty():
		return
	var tex := load(path) as Texture2D
	# 新说话的角色站右侧，上一个挪到左侧
	if char_r.visible and char_r.texture != tex:
		char_l.texture = char_r.texture
		char_l.visible = true
	char_r.texture = tex
	char_r.visible = true


func _apply_cg(value: String) -> bool:
	var path := _resolve(DIR_CG, value)
	if path.is_empty():
		return false
	cg_rect.texture = load(path) as Texture2D
	cg_rect.visible = true
	return true


## ── 打字机 ──
func _process(delta: float) -> void:
	if not typing:
		return
	_typed_chars += delta * CPS
	text_label.visible_characters = int(_typed_chars)
	if text_label.visible_characters >= text_label.get_total_character_count():
		_finish_typing()


func _finish_typing() -> void:
	text_label.visible_characters = -1
	typing = false
	next_arrow.visible = true


## ── 输入：点击 / 触屏 / 回车推进 ──
func _unhandled_input(event: InputEvent) -> void:
	if awaiting_choice or not _is_confirm(event):
		return
	if cg_rect.visible:
		cg_rect.visible = false
		_advance()
	elif typing:
		_finish_typing()
	else:
		_advance()


func _is_confirm(event: InputEvent) -> bool:
	if event is InputEventMouseButton:
		return event.button_index == MOUSE_BUTTON_LEFT and event.pressed
	if event is InputEventScreenTouch:
		return event.pressed
	return event.is_action_pressed("ui_accept")


## ── 选项：场景里预置4个按钮，用到几个显示几个 ──
func _show_choices(options: Array) -> void:
	var opt: Array[String] = []
	for o in options:
		opt.append(String(o))
	awaiting_choice = true
	for i in range(1, 5):
		var btn: Button = choices.get_node("Choice%d" % i)
		btn.visible = i <= opt.size()
		if i <= opt.size():
			btn.text = opt[i - 1]
			for conn in btn.pressed.get_connections():
				btn.pressed.disconnect(conn["callable"])
			btn.pressed.connect(_on_choice.bind(i))
	choices.visible = true


func _on_choice(chosen: int) -> void:
	choices.visible = false
	awaiting_choice = false
	GameManager.choice_history.append(chosen)
	_advance()
