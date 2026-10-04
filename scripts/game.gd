extends Control
## 极简AVG演示：打字机文本框 + 选项 + 点击/触屏推进。
## 正式剧本数据后续替换为外部JSON/ Dialogue资源。

const CPS := 28.0

## 演示剧本（取自《宇宙快递员》开篇）
var D := [
	{"bg": Color(0.35, 0.22, 0.1), "name": "", "text": "轰——！"},
	{"name": "", "text": "随着一声巨响，天空完全被橙黄的光亮给覆盖住了，取而代之的是那令人睁不开眼的光芒。然而，在这持续了几分钟的光亮之后，天完全黑了下来。"},
	{"name": "", "text": "随之而来的，便是那无穷的寂静。听不见任何的枪声炮声，也看不到一束束由高能枪发出的耀眼的光芒。可就在几分钟前，这里还是一阵阵的炮火连天，枪声响彻云天。现在，便是一片死寂。"},
	{"name": "我", "text": "我紧握着手里的光枪，待上面的激光充满了之后，便将枪口对准敌人的营地，唯恐敌人再次发出进攻。"},
	{"name": "我", "text": "然而，奇怪的是，敌人这次没有任何的动静，你甚至连一点声音都听不见。"},
	{"name": "我", "text": "“奇怪。”心里想着。"},
	{"name": "通讯耳", "text": "“喂！那边的，圈划符号史历文长官叫我们集合！”"},
	{"name": "我", "text": "是吗？战争结束了吗？打了7年的战争这么快就结束了？我还什么都没感受到呢？"},
	{"name": "希朗首长", "text": "“我要感谢大家，让我们在这场战役中取得了完美的正义！”"},
	{"name": "希朗首长", "text": "“世界需要有人去引领它。如果没有有人去引领它，那么无论是哪个星球，最后的结局都会走向灭亡。因此，我，被选上了！”"},
	{"name": "我", "text": "就这样，我脱下军装，成为了一名宇宙快递员。", "end": true},
	{"choice": [
		{"t": "现在就出发，去领取第一份委托。"},
		{"t": "先回去睡一觉，明天再说。"},
	]},
	{"name": "", "text": "——宇宙尽头，也要把心意送达。（演示结束，点击返回标题）"},
]

var idx := -1
var typing := false

@onready var bg: ColorRect = $Bg
@onready var name_label: Label = $UI/VNBox/NamePlate/NameLabel
@onready var text_label: RichTextLabel = $UI/VNBox/Text
@onready var next_arrow: Label = $UI/VNBox/NextArrow
@onready var choices: VBoxContainer = $UI/Choices


func _ready() -> void:
	_next()


func _process(delta: float) -> void:
	if not typing:
		return
	text_label.visible_ratio += delta * CPS / max(text_label.get_total_character_count(), 1)
	if text_label.visible_ratio >= 1.0:
		_finish_typing()


func _unhandled_input(event: InputEvent) -> void:
	if choices.visible:
		return
	var clicked := event is InputEventMouseButton \
		and event.button_index == MOUSE_BUTTON_LEFT and event.pressed
	var tapped := event is InputEventScreenTouch and event.pressed
	var keyed := event.is_action_pressed("ui_accept")
	if clicked or tapped or keyed:
		if typing:
			_finish_typing()
		else:
			_next()


func _finish_typing() -> void:
	text_label.visible_ratio = 1.0
	typing = false
	next_arrow.visible = true


func _next() -> void:
	idx += 1
	if idx >= D.size():
		get_tree().change_scene_to_file("res://scenes/main.tscn")
		return
	var step: Dictionary = D[idx]
	if step.has("choice"):
		_show_choices(step["choice"])
		return
	if step.has("bg"):
		bg.color = step["bg"]
	if step.get("end", false):
		next_arrow.visible = false
	name_label.text = step.get("name", "")
	name_label.get_parent().visible = step.get("name", "") != ""
	text_label.text = step["text"]
	text_label.visible_ratio = 0.0
	typing = true
	next_arrow.visible = false


func _show_choices(options: Array) -> void:
	for child in choices.get_children():
		child.queue_free()
	for opt in options:
		var btn := Button.new()
		btn.text = opt["t"]
		btn.custom_minimum_size = Vector2(840, 90)
		btn.add_theme_font_size_override("font_size", 30)
		btn.add_theme_color_override("font_color", Color(0.93, 0.9, 0.84))
		btn.add_theme_color_override("font_hover_color", Color(1, 0.85, 0.6))
		btn.pressed.connect(_on_choice.bind(opt["t"]))
		choices.add_child(btn)
	choices.visible = true


func _on_choice(text: String) -> void:
	choices.visible = false
	idx += 1  # 跳过choice步，进入收尾行
	name_label.text = ""
	name_label.get_parent().visible = false
	text_label.text = "你选择了：「%s」" % text
	text_label.visible_ratio = 0.0
	typing = true
