extends Control
## 标题画面：开始游戏 / 继续 / 读取存档 / 退出
## 设计：主视觉底图 + 左下金色标题排版 + 竖排文字菜单 + 星尘粒子 + 缓慢推镜

const TITLE_BG := "res://assets/cg/title_visual.png"
const FALLBACK_BG := "res://assets/sprites/bg/bg_eden.png"
## 标题主题曲（终章主题旋律复用）
const TITLE_BGM := "bgm_scan19"

@onready var continue_btn: Button = $Menu/ContinueButton
@onready var bg: TextureRect = $Bg
@onready var title_block: Control = $TitleBlock
@onready var menu: Control = $Menu


func _ready() -> void:
	$Menu/StartButton.pressed.connect(_on_start)
	continue_btn.pressed.connect(_on_continue)
	$Menu/LoadButton.pressed.connect(_on_load)
	$Menu/QuitButton.pressed.connect(_on_quit)
	# 没有自动存档时"继续游戏"不可点
	continue_btn.disabled = not GameManager.has_auto()
	_setup_visual()
	_setup_version()
	AudioManager.play_bgm(TITLE_BGM)


## 主视觉：优先用豆包生成的专属标题图，缺失时退回已有背景
func _setup_visual() -> void:
	var path := TITLE_BG if ResourceLoader.exists(TITLE_BG) else FALLBACK_BG
	bg.texture = load(path) as Texture2D
	# 缓慢推镜（Ken Burns）：以中心为轴放大 1.04↔1.10 循环
	bg.pivot_offset = size / 2.0
	bg.scale = Vector2(1.04, 1.04)
	var tw: Tween = create_tween().set_loops()
	tw.tween_property(bg, "scale", Vector2(1.1, 1.1), 16.0)\
		.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(bg, "scale", Vector2(1.04, 1.04), 16.0)\
		.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	# 标题块淡入 + 菜单按钮从左到右依次滑入
	title_block.modulate.a = 0.0
	title_block.position.y += 26.0
	var tw2: Tween = create_tween()
	tw2.set_parallel(true)
	tw2.tween_property(title_block, "modulate:a", 1.0, 0.7)
	tw2.tween_property(title_block, "position:y", title_block.position.y - 26.0, 0.7)\
		.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_animate_menu()


## 菜单四按钮：从左侧依次滑入（上→下），带回弹；动画结束后再把焦点给开始按钮
func _animate_menu() -> void:
	var buttons: Array[Button] = [
		$Menu/StartButton, $Menu/ContinueButton, $Menu/LoadButton, $Menu/QuitButton,
	]
	for i in buttons.size():
		var b := buttons[i]
		var target_x := b.position.x
		b.modulate.a = 0.0
		b.position.x = target_x - 110.0
		var tw: Tween = create_tween()
		tw.tween_interval(0.45 + i * 0.14)
		tw.tween_property(b, "modulate:a", 1.0, 0.32)
		tw.parallel().tween_property(b, "position:x", target_x, 0.42)\
			.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	var tw_end: Tween = create_tween()
	tw_end.tween_interval(1.3)
	tw_end.tween_callback(func () -> void: buttons[0].grab_focus())


func _setup_version() -> void:
	var v := String(ProjectSettings.get_setting("application/config/version", "1.0.0"))
	$VersionLabel.text = "宇宙快递员 v%s" % v


## 从头开始：必须清空进度，否则读过档后会接着旧进度走。
## 有自动存档时先弹确认，防止误触把进度从头覆盖
func _on_start() -> void:
	if GameManager.has_auto():
		_show_newgame_confirm()
		return
	_start_game()


func _start_game() -> void:
	GameManager.current_chapter = 1
	GameManager.current_line = 0
	GameManager.choice_history.clear()
	get_tree().change_scene_to_file("res://scenes/game.tscn")


## ── 重新开始确认弹窗（纯代码构建，不改场景文件）──
var _confirm_layer: Control

func _show_newgame_confirm() -> void:
	if _confirm_layer != null and is_instance_valid(_confirm_layer):
		return
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.08, 0.08, 0.12, 0.96)
	style.border_color = Color(0.85, 0.75, 0.54)
	style.set_border_width_all(2)
	style.set_corner_radius_all(6)
	style.content_margin_left = 52.0
	style.content_margin_right = 52.0
	style.content_margin_top = 40.0
	style.content_margin_bottom = 40.0

	var btn_style := StyleBoxFlat.new()
	btn_style.bg_color = Color(0.16, 0.16, 0.22)
	btn_style.border_color = Color(0.85, 0.75, 0.54)
	btn_style.set_border_width_all(1)
	btn_style.set_corner_radius_all(4)
	btn_style.content_margin_top = 18.0
	btn_style.content_margin_bottom = 18.0
	var btn_hover := btn_style.duplicate() as StyleBoxFlat
	btn_hover.bg_color = Color(0.26, 0.24, 0.30)

	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", style)
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 26)
	panel.add_child(vbox)

	var title := Label.new()
	title.text = "检测到自动存档"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 30)
	title.add_theme_color_override("font_color", Color(0.85, 0.75, 0.54))
	vbox.add_child(title)

	var msg := Label.new()
	msg.text = "重新开始将从第1章进行，\n自动存档的进度会被覆盖。\n确定要重新开始吗？"
	msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	msg.add_theme_font_size_override("font_size", 24)
	vbox.add_child(msg)

	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 30)
	vbox.add_child(row)
	var ok := Button.new()
	ok.text = "重新开始"
	ok.custom_minimum_size = Vector2(220, 72)
	ok.add_theme_font_size_override("font_size", 24)
	ok.add_theme_stylebox_override("normal", btn_style)
	ok.add_theme_stylebox_override("hover", btn_hover)
	ok.pressed.connect(func () -> void:
		_close_newgame_confirm()
		_start_game())
	row.add_child(ok)
	var cancel := Button.new()
	cancel.text = "返回"
	cancel.custom_minimum_size = Vector2(220, 72)
	cancel.add_theme_font_size_override("font_size", 24)
	cancel.add_theme_stylebox_override("normal", btn_style)
	cancel.add_theme_stylebox_override("hover", btn_hover)
	cancel.pressed.connect(_close_newgame_confirm)
	row.add_child(cancel)

	var layer := Control.new()
	layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	var shade := ColorRect.new()
	shade.color = Color(0.0, 0.0, 0.0, 0.62)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.gui_input.connect(func (ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.pressed:
			_close_newgame_confirm())
	layer.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.add_child(panel)
	layer.add_child(center)
	add_child(layer)
	_confirm_layer = layer


func _close_newgame_confirm() -> void:
	if _confirm_layer != null and is_instance_valid(_confirm_layer):
		_confirm_layer.queue_free()
	_confirm_layer = null


func _on_continue() -> void:
	if not GameManager.load_auto():
		return
	get_tree().change_scene_to_file("res://scenes/game.tscn")


func _on_load() -> void:
	GameManager.open_save_mode = "load"
	get_tree().change_scene_to_file("res://scenes/save_menu.tscn")


func _on_quit() -> void:
	get_tree().quit()
