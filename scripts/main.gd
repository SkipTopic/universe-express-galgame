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
@onready var menu: VBoxContainer = $Menu


func _ready() -> void:
	$Menu/StartButton.pressed.connect(_on_start)
	continue_btn.pressed.connect(_on_continue)
	$Menu/LoadButton.pressed.connect(_on_load)
	$Menu/QuitButton.pressed.connect(_on_quit)
	# 没有自动存档时"继续游戏"不可点
	continue_btn.disabled = not GameManager.has_auto()
	$Menu/StartButton.grab_focus()
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
	# 标题块与菜单淡入
	title_block.modulate.a = 0.0
	menu.modulate.a = 0.0
	var tw2: Tween = create_tween()
	tw2.tween_property(title_block, "modulate:a", 1.0, 0.7)
	tw2.parallel().tween_property(menu, "modulate:a", 1.0, 0.7)


func _setup_version() -> void:
	var v := String(ProjectSettings.get_setting("application/config/version", "1.0.0"))
	$VersionLabel.text = "宇宙快递员 v%s" % v


## 从头开始：必须清空进度，否则读过档后会接着旧进度走
func _on_start() -> void:
	GameManager.current_chapter = 1
	GameManager.current_line = 0
	GameManager.choice_history.clear()
	get_tree().change_scene_to_file("res://scenes/game.tscn")


func _on_continue() -> void:
	if not GameManager.load_auto():
		return
	get_tree().change_scene_to_file("res://scenes/game.tscn")


func _on_load() -> void:
	GameManager.open_save_mode = "load"
	get_tree().change_scene_to_file("res://scenes/save_menu.tscn")


func _on_quit() -> void:
	get_tree().quit()
