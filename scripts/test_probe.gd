extends Node
## 帧渲染验证探针（临时autoload，验证完删除）：
## 环境变量 TEST_CH / TEST_LINE / TEST_FRAMES 定位到任意章节行，
## 配合 --write-movie --fixed-fps 10 渲染 png 序列逐帧目检。

var _frames := 0
var _max_frames := 40

func _ready() -> void:
	var ch := OS.get_environment("TEST_CH")
	var fr := OS.get_environment("TEST_FRAMES")
	if not fr.is_empty():
		_max_frames = int(fr)
	if ch.is_empty():
		return  # 不切场景（渲染标题画面用），只按 TEST_FRAMES 计帧退出
	GameManager.current_chapter = int(ch)
	var ln := OS.get_environment("TEST_LINE")
	GameManager.current_line = int(ln) if not ln.is_empty() else 0
	get_tree().change_scene_to_file.call_deferred("res://scenes/game.tscn")


func _process(_d: float) -> void:
	_frames += 1
	if _frames >= _max_frames:
		set_process(false)
		get_tree().quit()
