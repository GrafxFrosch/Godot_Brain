extends Node2D
@export var eyes: Camera2D
@export var body: CharacterBody2D
@export var task: String
@export var API_KEY: String
@export var smooth_movement: bool = false
@export var speed: int
@export var sprite: AnimatedSprite2D

var last_dir := Vector2.DOWN
var smoothness: float = 8.0
var save_path = "res://addons/brain/Server/last10/"
const MAX_IMAGES := 1
var image_counter := 0
const SERVER_URL = "http://127.0.0.1:8687/request/"
var velocity: Vector2 = Vector2.ZERO
var target_position: Vector2
var has_target: bool = false

#--------------------------------
### Start:
#--------------------------------
func _ready():
	var dir := DirAccess.open(save_path)
	if dir:
		dir.list_dir_begin()
		var f := dir.get_next()
		while f != "":
			if not dir.current_is_dir():
				dir.remove(f)
			f = dir.get_next()
		dir.list_dir_end()
	target_position = position
	await get_tree().create_timer(0.1).timeout
	await _capture_image()
	movementsycle()

#--------------------------------
### Struckturablauf für den NPC:
#--------------------------------
func movementsycle():
	# Define the absolute path to the Python interpreter
	var python_path := "C:/Users/pascal/AppData/Local/Programs/Python/Python313/python.exe"
	
	# Verify if the Python executable exists at the specified path
	print("Python interpreter found: ", FileAccess.file_exists(python_path))
	
	# Convert the relative project path of the server script to an absolute OS path
	var server_script := ProjectSettings.globalize_path("res://addons/brain/Server/app.py")
	
	# Start the Python server as a background process
	# "-u" forces the stdout and stderr streams to be unbuffered
	var pid := OS.create_process(python_path, ["-u", server_script])
	
	# Output the Process ID (PID) of the started server
	print("Server Process ID: ", pid)
	var response = await request(task, save_path + "shot.png", API_KEY)
	var json = JSON.new()
	json.parse(response)
	var codes = json.data.reply.output
	print("---------------")
	print("Server Response: ", codes)
	print("---------------")
	if codes == "xx" || codes == "":
		print("nicht bewegt!")
		return
	if codes.contains("[") || codes.contains("\""):
		print("lösche [/]")
		codes = codes.replace("[","")
		codes = codes.replace("]","")
		codes = codes.replace("\"","")
		print("Edited codes:",codes)
	processCodes(codes.split(","))


#--------------------------------
### Bewegungssteuerung:
#--------------------------------
func move_smooth(delta: float) -> void:
	if not has_target:
		return

	var distance := position.distance_to(target_position)

	if distance < 1.0:
		await _capture_image()
		movementsycle()
		position = target_position
		velocity = Vector2.ZERO
		has_target = false
		return

	var direction := (target_position - position).normalized()
	var target_velocity := direction * speed
	velocity = velocity.lerp(target_velocity, smoothness * delta)
	position += velocity * delta


func update_animation() -> void:
	# Bewegung?
	if velocity.length() > 1.0:
		last_dir = velocity

		# Vertikal hat Priorität
		if abs(velocity.y) > abs(velocity.x):
			if velocity.y < 0:
				sprite.play("Walk-Up")
			else:
				sprite.play("Walk-Down")
		else:
			sprite.play("Walk-Hor")

		# Links / Rechts spiegeln
		if velocity.x != 0:
			sprite.flip_h = velocity.x < 0

	else:
		# IDLE
		if abs(last_dir.y) > abs(last_dir.x):
			if last_dir.y < 0:
				sprite.play("Idle-Up")
			else:
				sprite.play("Idle-Down")
		else:
			sprite.play("Idle-Hor")


#--------------------------------
### Engine Callback:
#--------------------------------
func _physics_process(delta):
	if smooth_movement:
		move_smooth(delta)
	update_animation()

#--------------------------------
### Request return processing:
#--------------------------------
func processCodes(codes: Array[String]):
	var offset := Vector2.ZERO
	for c in codes:
		var t = c.split("|")
		var factor: float = float(t[1]) / 100
		if t[0] == "n":
			offset.y -= factor * eyes.get_viewport().get_visible_rect().size.y
		elif t[0] == "s":
			offset.y += factor * eyes.get_viewport().get_visible_rect().size.y
		elif t[0] == "e":
			offset.x += factor * eyes.get_viewport().get_visible_rect().size.x
		elif t[0] == "w":
			offset.x -= factor * eyes.get_viewport().get_visible_rect().size.x
	if smooth_movement:
		target_position = position + offset
		has_target = true
	else:
		position += offset

#--------------------------------
### request abgeben:
#--------------------------------
func request(task: String, image_path: String, key: String) -> String:
	# Create a temporary HTTPRequest node
	var http_request := HTTPRequest.new()
	add_child(http_request)

	# Setup request headers and serialize the dictionary to a JSON string
	var headers := ["Content-Type: application/json"]
	var body := JSON.stringify({"task": task, "image_path":image_path,"key":key})

	# Execute the POST request
	http_request.request(
		SERVER_URL,
		headers,
		HTTPClient.Method.METHOD_POST,
		body
	)

	# ⏳ WAIT FOR THE RESPONSE
	# The 'await' keyword pauses execution until the signal is emitted
	var result = await http_request.request_completed
	
	# Clean up the node immediately after the request finishes
	http_request.queue_free()

	# Extract response data from the result array
	var response_code: int = result[1]
	var response_body: PackedByteArray = result[3]
	var response_text := response_body.get_string_from_utf8()

	# Error handling: Check if the server returned a success code (200 OK)
	if response_code != 200:
		push_error("HTTP Error %d: %s" % [response_code, response_text])
		return ""

	return response_text

# ==============================================================================
# SIGNAL CALLBACKS
# ==============================================================================

## Callback function for handling completed HTTP requests (used for non-await calls)
func _on_request_completed(
	_result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	var response_text := body.get_string_from_utf8()
	var json = JSON.new()
	json.parse(response_text)
	print("---------------")
	print("HTTP Status Code: ", response_code)
	print("Server Response: ", json.data.reply)
	print("---------------")

func _capture_image():
	var viewport := eyes.get_viewport()
	var texture := viewport.get_texture()
	if texture == null:
		return

	var image := texture.get_image()



	var filename := "%sshot.png" % save_path
	await image.save_png(filename)

	image_counter += 1
	await _cleanup_old_images()

#--------------------------------
### Keep folder clean:
#--------------------------------
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
