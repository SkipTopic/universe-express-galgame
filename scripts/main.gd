extends Control
## 标题画面：开始游戏 / 退出


func _ready() -> void:
	$Menu/StartButton.pressed.connect(_on_start)
	$Menu/QuitButton.pressed.connect(_on_quit)
	$Menu/StartButton.grab_focus()


func _on_start() -> void:
	get_tree().change_scene_to_file("res://scenes/game.tscn")


func _on_quit() -> void:
	get_tree().quit()
