extends Node
## 过转场压力测试：连点40次，必须越过原卡死点（第1章换演讲厅转场后的行）
func _ready() -> void:
	var game: Control = load("res://scenes/game.tscn").instantiate()
	add_child(game)
	game.set_anchors_preset(Control.PRESET_FULL_RECT)
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().create_timer(0.3).timeout
	var stall := 0
	var last := -1
	for i in range(40):
		var ev := InputEventScreenTouch.new()
		ev.pressed = true
		ev.position = Vector2(500, 900)
		Input.parse_input_event(ev)
		await get_tree().create_timer(0.12).timeout
		var cur: int = GameManager.current_line
		if cur == last:
			stall += 1
		else:
			stall = 0
		last = cur
		if cur >= 16:
			break
	await get_tree().create_timer(0.5).timeout
	var final: int = GameManager.current_line
	print("FADETEST final_line=", final, " RESULT=", "OK" if final >= 15 else "FAIL(卡在", final, ")")
	get_tree().quit(0 if final >= 15 else 1)
