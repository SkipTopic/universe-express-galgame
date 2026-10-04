extends Control
## 章节播放器：读取 story/chXX.txt 剧本并演出
## 进度保存在 GameManager.current_chapter / current_line（配合9槽存档）
## 剧本格式见 story/格式说明.txt（记事本直接改）

const CPS := 28.0
const DIR_BG := "res://assets/sprites/bg/"
const DIR_CHAR := "res://assets/sprites/characters/"
const DIR_CG := "res://assets/cg/"

var steps: Array = []
var idx := 0            # 当前步骤下标
var line_no := 0        # 已播放的台词行数（存档用）
var typing := false
var chapter_done := false

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


func _trace(msg: String) -> void:
	var f := FileAccess.open("res://trace.txt", FileAccess.READ_WRITE if FileAccess.file_exists("res://trace.txt") else FileAccess.WRITE)
	f.seek_end()
	f.store_line("%d | %s" % [idx, msg])
	f.close()


func _ready() -> void:
	_trace("READY-A")
	$UILayer/MenuBtn.pressed.connect(_open_save)
	_trace("READY-B")
	_load_chapter(GameManager.current_chapter)
	_trace("READY-C steps=" + str(steps.size()))


func _open_save() -> void:
	GameManager.open_save_mode = "save"
	get_tree().change_scene_to_file("res://scenes/save_menu.tscn")


func _load_chapter(ch: int) -> void:
	_trace("load_chapter " + str(ch))
	var path := "res://story/ch%02d.txt" % ch
	steps = StoryParser.parse(path)
	idx = 0
	line_no = 0
	chapter_label.text = "第%d章 · %s" % [ch, GameManager.chapter_title(ch)]
	# 读档恢复：跳过存档行号之前的台词（背景/立绘照常应用）
	var target := GameManager.current_line
	while idx < steps.size() and line_no < target:
		var st: Dictionary = steps[idx]
		if st["type"] == "bg":
			_apply_bg(st["value"])
		elif st["type"] == "sprite":
			_apply_sprite(st["value"])
		elif st["type"] == "line":
			line_no += 1
		idx += 1
	GameManager.current_line = line_no
	if idx >= steps.size():
		_next_chapter()
	else:
		_show_current()


func _show_current() -> void:
	var st: Dictionary = steps[idx]
	print("STEP ", idx, " ", st["type"])
	match st["type"]:
		"title":
			chapter_label.text = str(st["value"])
			_finish_step()
		"bg":
			_apply_bg(st["value"])
			_finish_step()
		"sprite":
			_apply_sprite(st["value"])
			_finish_step()
		"cg":
			_apply_cg(st["value"])
			_finish_step()
		"choice":
			_show_choices(st["options"])
		"line":
			if st["name"] == "":
				name_plate.visible = false
			else:
				name_plate.visible = true
				name_label.text = st["name"]
			text_label.text = st["text"]
			text_label.visible_ratio = 0.0
			typing = true
			next_arrow.visible = false
			line_no += 1
			GameManager.current_line = line_no
		_:
			_finish_step()


func _finish_step() -> void:
	idx += 1
	if idx >= steps.size():
		_next_chapter()
	else:
		_show_current()


func _next_chapter() -> void:
	if GameManager.current_chapter >= 12:
		get_tree().change_scene_to_file("res://scenes/main.tscn")
		return
	GameManager.current_chapter += 1
	GameManager.current_line = 0
	_load_chapter(GameManager.current_chapter)


# ── 各类表现 ──
func _apply_bg(value: String) -> void:
	var path := DIR_BG + value + ".png"
	if ResourceLoader.exists(path):
		bg.texture = load(path)

func _apply_sprite(value: String) -> void:
	if value == "无":
		char_l.visible = false
		char_r.visible = false
		return
	var path := DIR_CHAR + value + ".png"
	if not ResourceLoader.exists(path):
		return
	var tex := load(path)
	# 新说话的角色站右侧，上一个挪到左侧
	if char_r.visible and char_r.texture != tex:
		char_l.texture = char_r.texture
		char_l.visible = true
	char_r.texture = tex
	char_r.visible = true

func _apply_cg(value: String) -> void:
	var path := DIR_CG + value
	if ResourceLoader.exists(path):
		cg_rect.texture = load(path)
		cg_rect.visible = true


# ── 输入：点击/触屏/回车推进 ──
func _process(delta: float) -> void:
	if not typing:
		return
	text_label.visible_ratio += delta * CPS / max(text_label.get_total_character_count(), 1)
	if text_label.visible_ratio >= 1.0:
		typing = false
		next_arrow.visible = true


func _unhandled_input(event: InputEvent) -> void:
	if choices.visible or chapter_done:
		return
	var clicked: bool = false
	var tapped: bool = false
	var keyed: bool = false
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		clicked = true
	if event is InputEventScreenTouch and event.pressed:
		tapped = true
	if event.is_action_pressed("ui_accept"):
		keyed = true
	if clicked or tapped or keyed:
		if cg_rect.visible:
			cg_rect.visible = false
			_finish_step()
		elif typing:
			_finish_typing()
		else:
			_finish_step()


func _finish_typing() -> void:
	text_label.visible_ratio = 1.0
	typing = false
	next_arrow.visible = true


# ── 选项：编辑器里预先放好4个按钮，用到几个显示几个 ──
func _show_choices(options: Array) -> void:
	for i in range(1, 5):
		var btn: Button = choices.get_node("Choice%d" % i)
		btn.visible = i <= options.size()
		if i <= options.size():
			btn.text = str(options[i - 1])
			for conn in btn.pressed.get_connections():
				btn.pressed.disconnect(conn["callable"])
			btn.pressed.connect(_on_choice.bind(i, options.size()))
	choices.visible = true


func _on_choice(chosen: int, total: int) -> void:
	choices.visible = false
	pass
