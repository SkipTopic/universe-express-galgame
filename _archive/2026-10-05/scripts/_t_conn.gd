extends Control

func _ready() -> void:
	var f := FileAccess.open("res://conn_trace.txt", FileAccess.WRITE)
	f.store_line("before connect")
	f.close()
	$UI/B.pressed.connect(_on_b)
	var f2 := FileAccess.open("res://conn_trace.txt", FileAccess.READ_WRITE)
	f2.seek_end()
	f2.store_line("after connect OK")
	f2.close()

func _on_b() -> void:
	pass
