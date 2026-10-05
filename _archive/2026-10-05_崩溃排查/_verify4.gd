extends SceneTree
func _init() -> void:
	var total := 0
	var ok := true
	for i in range(1, 13):
		var steps = StoryParser.parse("res://story/ch%02d.txt" % i)
		total += steps.size()
		if steps.size() == 0: ok = false
	print("TOTAL ", total, " ", "OK" if ok else "FAIL")
	quit(0)
