extends Node2D
@export var eyes: Camera2D
@export var body: CharacterBody2D
@export var task: String
@export var API_KEY: String

var save_path = "res://addons/brain/Server/last10/"
const MAX_IMAGES := 1
var image_counter := 0

func _ready():
	# Ordner sicherstellen
	var dir := DirAccess.open(save_path)
	if dir:
		dir.list_dir_begin()
		var f := dir.get_next()
		while f != "":
			if not dir.current_is_dir():
				dir.remove(f)
			f = dir.get_next()
		dir.list_dir_end()

	# Timer starten
	var timer := Timer.new()
	timer.wait_time = 1.0
	timer.autostart = true
	timer.timeout.connect(_capture_image)
	add_child(timer)

func _capture_image():
	var viewport := eyes.get_viewport()
	var texture := viewport.get_texture()
	if texture == null:
		return

	var image := texture.get_image()
	image.flip_y() # Wichtig für korrektes Bild

	var filename := "%sshot_%03d.png" % [save_path, image_counter]
	image.save_png(filename)

	image_counter += 1
	_cleanup_old_images()

func _cleanup_old_images():
	var dir := DirAccess.open(save_path)
	if dir == null:
		return

	var files := []
	dir.list_dir_begin()
	var file := dir.get_next()
	while file != "":
		if file.ends_with(".png"):
			files.append(file)
		file = dir.get_next()
	dir.list_dir_end()

	files.sort()

	while files.size() > MAX_IMAGES:
		var to_delete := files.pop_front()
		DirAccess.remove_absolute(save_path + to_delete)
