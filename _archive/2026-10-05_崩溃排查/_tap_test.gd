extends Node
## 自动点击测试：向真实game场景注入触摸+鼠标事件，验证台词推进
func _ready() -> void:
	var game: Control = load("res://scenes/game.tscn").instantiate()
	add_child(game)
	game.set_anchors_preset(Control.PRESET_FULL_RECT)
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().create_timer(0.3).timeout
	var before: int = GameManager.current_line
	for i in range(2):
		var ev := InputEventScreenTouch.new()
		ev.pressed = true
		ev.position = Vector2(500, 900)
		Input.parse_input_event(ev)
		var em := InputEventMouseButton.new()
		em.button_index = MOUSE_BUTTON_LEFT
		em.pressed = true
		em.position = Vector2(500, 900)
		Input.parse_input_event(em)
		await get_tree().create_timer(0.3).timeout
	var after: int = GameManager.current_line
	print("TAPTEST before=", before, " after=", after,
		" RESULT=", "OK" if after > before else "FAIL")
	get_tree().quit(0 if after > before else 1)
