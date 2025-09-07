from ursina import *
from perlin_noise import PerlinNoise
from math import floor
import time

# --- Game Settings ---
WINDOW_TITLE = "UrsinaCraft Optimized"
WINDOW_COLOR = color.rgb(135, 206, 235)
CHUNK_SIZE = 4
RENDER_DISTANCE = 1
GRAVITY = 1.2
JUMP_HEIGHT = 8
BASE_SPEED = 6
MIN_FOV = 70
MAX_FOV = 120
SPAWN_Y = 20
MOUSE_SENSITIVITY = 80
HOTBAR_SIZE = 9

# --- Initialize app ---
app = Ursina(title=WINDOW_TITLE)
window.color = WINDOW_COLOR
window.borderless = False

# --- Sky ---
sky = Sky()

# --- Noise & world ---
noise = PerlinNoise(octaves=3)
world_chunks = {}

class Block(Entity):
    def __init__(self, parent, position=(0,0,0), block_type='grass'):
        color_map = {
            'grass': color.green,
            'dirt': color.rgb(150,100,50)
        }
        super().__init__(
            parent=parent,
            model='cube',
            position=position,
            color=color_map[block_type],
            scale=1,
        )

def generate_chunk(chunk_coord):
    cx, cz = chunk_coord
    chunk_parent = Entity(position=(cx*CHUNK_SIZE, 0, cz*CHUNK_SIZE))

    for x in range(CHUNK_SIZE):
        for z in range(CHUNK_SIZE):
            world_x = chunk_parent.x + x
            world_z = chunk_parent.z + z
            height = floor(noise([world_x/20, world_z/20])*5) + 10
            for y in range(height):
                b_type = 'grass' if y == height-1 else 'dirt'
                Block(parent=chunk_parent, position=(x, y, z), block_type=b_type)

    chunk_parent.combine(auto_destroy=True)
    chunk_parent.collider = 'mesh'
    world_chunks[chunk_coord] = chunk_parent

# --- Player ---
player = Entity(model='cube', color=color.red, scale=(0.8, 1.8, 0.8), collider='box', position=(0, SPAWN_Y, 0))
player.velocity = Vec3(0,0,0)
player.grounded = False
player.jumps_left = 1

player_chunk_x = floor(player.x / CHUNK_SIZE)
player_chunk_z = floor(player.z / CHUNK_SIZE)

# --- Camera ---
camera.fov = 90
camera_pivot = Entity()
mouse.locked = True
camera.parent = camera_pivot

# --- Perspective ---
first_person = True

# --- Inventory & Hotbar ---
inventory = [None]*HOTBAR_SIZE
selected_slot = 0

# --- Game Menu ---
game_menu = Entity(parent=camera.ui, model='quad', scale=(.4,.4), color=color.black.tint(-.3), enabled=False)
resume_btn = Button(parent=game_menu, text='Resume', y=0.2, scale=(.5,.2))
quit_btn = Button(parent=game_menu, text='Quit', y=-0.2, scale=(.5,.2), on_click=application.quit)

def toggle_game_menu():
    game_menu.enabled = not game_menu.enabled
    mouse.locked = not game_menu.enabled

resume_btn.on_click = toggle_game_menu

# --- Input ---
def input(key):
    global first_person, selected_slot
    if key == 'escape':
        toggle_game_menu()
    if key in [str(i) for i in range(1, HOTBAR_SIZE+1)]:
        selected_slot = int(key)-1
    if key == 'arrow up':
        camera.fov = clamp(camera.fov+5, MIN_FOV, MAX_FOV)
    if key == 'arrow down':
        camera.fov = clamp(camera.fov-5, MIN_FOV, MAX_FOV)
    if key == 'f1':
        first_person = not first_person
    if key == 'left mouse down' and not game_menu.enabled:
        # Break block in front of player
        hit = mouse.hovered_entity
        if hit and hit != player:
            destroy(hit)
    if key == 'right mouse down' and not game_menu.enabled:
        # Place block in front of player
        if mouse.world_point:
            pos = round(mouse.world_point)
            generate_block_at(pos)

def generate_block_at(pos):
    # Determine block type based on hotbar slot
    block_type = 'grass'  # For simplicity, always grass
    chunk_coord = (floor(pos.x / CHUNK_SIZE), floor(pos.z / CHUNK_SIZE))
    chunk = world_chunks.get(chunk_coord)
    if chunk:
        Block(parent=chunk, position=(pos.x - chunk.x, pos.y, pos.z - chunk.z), block_type=block_type)
        chunk.combine(auto_destroy=True)
        chunk.collider = 'mesh'

# --- Initial World Load ---
for x in range(player_chunk_x-RENDER_DISTANCE, player_chunk_x+RENDER_DISTANCE+1):
    for z in range(player_chunk_z-RENDER_DISTANCE, player_chunk_z+RENDER_DISTANCE+1):
        generate_chunk((x,z))

# --- Background music ---
if os.path.exists("Otherside.mp3"):
    music = Audio("Otherside.mp3", loop=True, autoplay=True)

# --- Update loop ---
def update():
    global player_chunk_x, player_chunk_z
    dt = time.dt

    # --- Mouse Look ---
    if first_person and mouse.locked:
        camera_pivot.rotation_y += mouse.dx * MOUSE_SENSITIVITY * dt
        camera.rotation_x -= mouse.dy * MOUSE_SENSITIVITY * dt
        camera.rotation_x = clamp(camera.rotation_x, -90, 90)

    # --- Player Movement ---
    move_direction = (camera.forward * (held_keys['w'] - held_keys['s']) +
                      camera.right * (held_keys['d'] - held_keys['a'])).normalized()
    speed = BASE_SPEED * (1.5 if held_keys['left shift'] else 1)
    player.position += move_direction * speed * dt

    # --- Gravity & Collision ---
    if not player.grounded:
        player.velocity.y -= GRAVITY * dt
    player.y += player.velocity.y * dt

    hit_info = player.intersects()
    if hit_info.hit:
        if hit_info.normal.y > 0.5:
            if not player.grounded:
                player.y = hit_info.world_point.y + 0.9
                player.velocity.y = 0
                player.grounded = True
                player.jumps_left = 1
        else:
            player.position -= hit_info.normal * hit_info.depth
    else:
        player.grounded = False

    # --- Jump ---
    if held_keys['space'] and player.jumps_left>0:
        player.velocity.y = JUMP_HEIGHT
        player.jumps_left -= 1
        player.grounded = False

    # --- Respawn in void ---
    if player.position.y < -10:
        player.position = Vec3(0, SPAWN_Y, 0)
        player.velocity = Vec3(0,0,0)

    # --- Camera follow ---
    if first_person:
        camera_pivot.position = player.position + Vec3(0,0.9,0)
    else:
        camera_pivot.position = player.position + Vec3(0,3,-6)
        camera_pivot.look_at(player.position + Vec3(0,1,0))

    # --- Dynamic chunk loading/unloading ---
    current_chunk_x = floor(player.x / CHUNK_SIZE)
    current_chunk_z = floor(player.z / CHUNK_SIZE)
    if (current_chunk_x, current_chunk_z) != (player_chunk_x, player_chunk_z):
        player_chunk_x, player_chunk_z = current_chunk_x, current_chunk_z
        for coord, chunk in list(world_chunks.items()):
            if abs(coord[0] - player_chunk_x) > RENDER_DISTANCE or abs(coord[1] - player_chunk_z) > RENDER_DISTANCE:
                destroy(chunk)
                del world_chunks[coord]
        for x in range(player_chunk_x - RENDER_DISTANCE, player_chunk_x + RENDER_DISTANCE + 1):
            for z in range(player_chunk_z - RENDER_DISTANCE, player_chunk_z + RENDER_DISTANCE + 1):
                if (x, z) not in world_chunks:
                    generate_chunk((x, z))

app.run()
