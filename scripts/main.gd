extends Control
## 标题画面：开始游戏 / 继续 / 读取存档 / 退出

@onready var continue_btn: Button = $Menu/ContinueButton


func _ready() -> void:
	$Menu/StartButton.pressed.connect(_on_start)
	continue_btn.pressed.connect(_on_continue)
	$Menu/LoadButton.pressed.connect(_on_load)
	$Menu/QuitButton.pressed.connect(_on_quit)
	# 没有自动存档时"继续游戏"不可点
	continue_btn.disabled = not GameManager.has_auto()
	$Menu/StartButton.grab_focus()


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
