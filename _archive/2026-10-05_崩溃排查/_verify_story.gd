extends SceneTree
## 校验：12章剧本全部可解析且步骤数>0
func _init() -> void:
	var ok := true
	for i in range(1, 13):
		var steps = StoryParser.parse("res://story/ch%02d.txt" % i)
		var lines := 0
		for st in steps:
			if st.get("type", "") == "line":
				lines += 1
		print("ch%02d steps=%d lines=%d" % [i, steps.size(), lines])
		if steps.size() == 0:
			ok = false
	print("RESULT ", "OK" if ok else "FAIL")
	quit(0 if ok else 1)
