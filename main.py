from ursina import *
from perlin_noise import PerlinNoise
from math import floor, sin, radians
import time, random

# --- Game Settings ---
WINDOW_TITLE = "UrsinaCraft Optimized"
WINDOW_COLOR = color.rgb(135, 206, 235)
CHUNK_SIZE = 4
GRAVITY = 3.2
JUMP_HEIGHT = 8
BASE_SPEED = 6
MIN_FOV = 70
MAX_FOV = 120
SPAWN_Y = 20
MOUSE_SENSITIVITY = 80

# --- Initialize app ---
app = Ursina(title=WINDOW_TITLE)
window.color = WINDOW_COLOR
window.borderless = False

# --- Sky ---
sky = Sky()
sky.color = color.black # Set a static black background

# --- Lighting ---
sun = DirectionalLight()
sun.shadows = True
sun.rotation = (60, -30, 0) # Start in the morning/afternoon
scene.ambient_light = color.rgba(40, 40, 40, 255) # Low constant ambient light for dark tones

# --- Noise & world ---
noise = PerlinNoise(octaves=3)
world_chunks = {}
world_data = {} # Store block data separate from visual entities

# --- Block class ---
class Block(Entity):
    def __init__(self, position=(0,0,0), block_type='grass', **kwargs):
        color_map = {
            'grass': color.rgb(0, 120, 5),
            'dark_grass': color.rgb(0, 90, 5),
            'darker_grass': color.rgb(0, 60, 5),
            'dirt': color.rgb(90, 60, 20),
            'stone': color.rgb(70, 70, 70),
            'sand': color.rgb(180, 170, 90)
        }
        block_color = color_map.get(block_type, color.rgb(70, 70, 70)) # Default to stone
        super().__init__(
            model='cube',
            position=position,
            color=block_color,
            scale=1, # Use full scale and let lighting create shades
            **kwargs
        )

# --- Chunk generation ---
def generate_chunk_data(chunk_coord):
    """Generates the block data for a chunk without creating entities."""
    cx, cz = chunk_coord
    if chunk_coord not in world_data:
        world_data[chunk_coord] = {}

    for x in range(CHUNK_SIZE):
        for z in range(CHUNK_SIZE):
            world_x = cx * CHUNK_SIZE + x
            world_z = cz * CHUNK_SIZE + z
            height = floor(noise([world_x/20, world_z/20])*5) + 10
            for y in range(height):
                if y == height - 1:
                    if noise([world_x / 50, world_z / 50]) > 0.4:
                        b_type = 'sand'
                    else:
                        # Choose a random grass type for variety
                        b_type = random.choice(['grass', 'dark_grass', 'darker_grass'])
                elif y > height - 5:
                    b_type = 'dirt'
                else:
                    b_type = 'stone'
                world_data[chunk_coord][(x, y, z)] = b_type

def build_chunk_mesh(chunk_coord):
    """Builds a visible, combined mesh from the chunk's data."""
    if chunk_coord in world_chunks and world_chunks[chunk_coord]:
        destroy(world_chunks[chunk_coord])

    cx, cz = chunk_coord
    chunk_parent = Entity(position=(cx*CHUNK_SIZE, 0, cz*CHUNK_SIZE))
    if chunk_coord not in world_data:
        return

    for local_pos, block_type in world_data[chunk_coord].items():
        Block(position=local_pos, block_type=block_type, parent=chunk_parent)
    chunk_parent.combine(auto_destroy=True)
    chunk_parent.collider = 'mesh'
    chunk_parent.shadow_caster = True
    chunk_parent.shadow_receiver = True
    world_chunks[chunk_coord] = chunk_parent

# --- Player ---
player = Entity(model='sphere', color=color.gray, scale=0.75, collider='sphere', position=(0, SPAWN_Y, 0))
player.shadow_caster = True
player.velocity = Vec3(0,0,0)
player.grounded = False
player.jumps_left = 1
first_person = True
chunks_to_generate = [] # Queue for chunks that need to be built

# --- Highlight block ---
highlight_block = Entity(
    model='cube',
    color=color.rgba(255, 255, 0, 100), # Yellowish glow
    scale=1.01, # Slightly larger to fit over the block
    enabled=False,
    blend_mode='additive'
)

# --- Camera ---
camera.fov = 90
camera_pivot = Entity()
mouse.locked = True
camera.parent = camera_pivot

# --- UI ---
crosshair = Text(parent=camera.ui, text='+', origin=(0,0), scale=3, color=color.white, enabled=True)

# --- Hotbar ---
hotbar_blocks = ['grass', 'dark_grass', 'darker_grass', 'dirt', 'stone', 'sand']
selected_block_index = 0
hotbar_text = Text(parent=camera.ui, origin=(-.5, .5), scale=1.5, color=color.white, x=-0.85, y=0.45)

def update_hotbar_text():
    hotbar_text.text = f'Selected: {hotbar_blocks[selected_block_index].capitalize()}'

update_hotbar_text()

# --- Game State ---
game_active = True

# --- Game Menu ---
game_menu = Entity(parent=camera.ui, model='quad', scale=(.4,.4), color=color.black.tint(-.3), enabled=False)
resume_btn = Button(parent=game_menu, text='Resume', y=0.2, scale=(.5,.2))
quit_btn = Button(parent=game_menu, text='Quit', y=-0.2, scale=(.5,.2), on_click=application.quit)

def toggle_game_menu():
    game_menu.enabled = not game_menu.enabled
    mouse.locked = not game_menu.enabled
    crosshair.enabled = mouse.locked

resume_btn.on_click = toggle_game_menu

# --- Input ---
def input(key):
    global first_person, selected_block_index

    if key == 'escape':
        toggle_game_menu()

    if game_menu.enabled:
        return

    # --- Block Breaking and Placing ---
    if key == 'left mouse down':
        hit_info = raycast(camera.world_position, camera.forward, distance=8, ignore=[player, highlight_block])
        if hit_info.hit:
            block_pos = hit_info.point - hit_info.normal * 0.5
            block_pos = Vec3(floor(block_pos.x), floor(block_pos.y), floor(block_pos.z))
            
            chunk_coord = (floor(block_pos.x / CHUNK_SIZE), floor(block_pos.z / CHUNK_SIZE))
            local_pos = (int(block_pos.x - chunk_coord[0] * CHUNK_SIZE), int(block_pos.y), int(block_pos.z - chunk_coord[1] * CHUNK_SIZE))

            if chunk_coord in world_data and local_pos in world_data[chunk_coord]:
                del world_data[chunk_coord][local_pos]
                build_chunk_mesh(chunk_coord)

    if key == 'right mouse down':
        hit_info = raycast(camera.world_position, camera.forward, distance=8, ignore=[player, highlight_block])
        if hit_info.hit:
            block_pos = hit_info.point + hit_info.normal * 0.5
            block_pos = Vec3(floor(block_pos.x), floor(block_pos.y), floor(block_pos.z))

            chunk_coord = (floor(block_pos.x / CHUNK_SIZE), floor(block_pos.z / CHUNK_SIZE))
            local_pos = (int(block_pos.x - chunk_coord[0] * CHUNK_SIZE), int(block_pos.y), int(block_pos.z - chunk_coord[1] * CHUNK_SIZE))

            if chunk_coord in world_data:
                world_data[chunk_coord][local_pos] = hotbar_blocks[selected_block_index]
                build_chunk_mesh(chunk_coord)

    if key == 'arrow up':
        camera.fov = clamp(camera.fov+5, MIN_FOV, MAX_FOV)
    if key == 'arrow down':
        camera.fov = clamp(camera.fov-5, MIN_FOV, MAX_FOV)
    if key == 'f1':
        first_person = not first_person
        crosshair.enabled = first_person # Hide crosshair in 3rd person
    if key == 'scroll up':
        selected_block_index = (selected_block_index + 1) % len(hotbar_blocks)
        update_hotbar_text()
    if key == 'scroll down':
        selected_block_index = (selected_block_index - 1) % len(hotbar_blocks)
        update_hotbar_text()

# --- Initial chunks ---
for x in range(-1, 2): # Generate a 3x3 grid of chunks
    for z in range(-1, 2):
        chunks_to_generate.append((x,z))

# --- Update loop ---
def update():
    if not game_active:
        return # Don't run any game logic if we are in a menu (e.g., start menu)

    # Process one chunk from the generation queue per frame to prevent lag spikes
    if chunks_to_generate:
        coord = chunks_to_generate.pop(0)
        generate_chunk_data(coord)
        build_chunk_mesh(coord)

    # --- Day/Night Cycle & Shading ---
    # Keep the sun rotating for dynamic shadows against the black sky
    sun.rotation_x += time.dt * 8

    dt = time.dt

    if game_menu.enabled:
        return # Pause game logic if menu is open

    # --- Block highlighting ---
    if first_person and mouse.locked:
        # Cast a ray from the camera to see what it's pointing at
        hit_info = raycast(camera.world_position, camera.forward, distance=8, ignore=[player, highlight_block])
        if hit_info.hit and hasattr(hit_info.entity, 'collider') and hit_info.entity.collider == 'mesh':
            # If we hit a chunk, enable and position the highlight block
            highlight_block.enabled = True
            # The position is the integer coordinate of the block we hit
            highlight_block.position = floor(hit_info.point - hit_info.normal * 0.5)
        else:
            # If we're not looking at a block, disable the highlight
            highlight_block.enabled = False
    else:
        # Also disable if not in first person or game is paused
        highlight_block.enabled = False

    # --- Mouse Look ---
    if mouse.locked:
        camera_pivot.rotation_y += mouse.velocity[0] * MOUSE_SENSITIVITY
        camera.rotation_x -= mouse.velocity[1] * MOUSE_SENSITIVITY
        camera.rotation_x = clamp(camera.rotation_x, -90, 90)

    # --- Movement & Collision ---
    move_dir = (camera.forward * (held_keys['w'] - held_keys['s']) +
                camera.right * (held_keys['d'] - held_keys['a'])).normalized()
    speed = BASE_SPEED * (1.5 if held_keys['left shift'] else 1)
    movement = move_dir * speed * dt

    # --- Gravity ---
    if not player.grounded:
        player.velocity.y -= GRAVITY * dt
    y_movement = player.velocity.y * dt

    # Move and check for collisions on each axis separately for wall sliding
    player.x += movement.x
    if player.intersects().hit:
        player.x -= movement.x

    player.z += movement.z
    if player.intersects().hit:
        player.z -= movement.z

    player.y += y_movement
    hit_info = player.intersects()
    if hit_info.hit:
        if y_movement < 0 and hit_info.normal.y > 0.5: # Landed on ground
            player.y = hit_info.world_point.y + player.scale_y / 2
            player.velocity.y = 0
            player.grounded = True
            player.jumps_left = 1
        else: # Hit a ceiling or wall
            player.y -= y_movement
            player.velocity.y = 0
    else:
        player.grounded = False

    # --- Jump ---
    if held_keys['space'] and player.jumps_left>0:
        player.velocity.y = JUMP_HEIGHT
        player.jumps_left -= 1
        player.grounded = False

    # --- Void respawn ---
    if player.position.y < -10:
        player.position = Vec3(0, SPAWN_Y, 0)
        player.velocity = Vec3(0,0,0)

    # --- Camera follow ---
    # The pivot is always at the player's eye level.
    camera_pivot.position = player.position + Vec3(0,0.3,0)
    if first_person:
        player.visible = False
        camera.position = (0,0,0) # Camera is at the pivot point.
    else: # 3rd person
        player.visible = True
        # Camera is positioned behind and above the pivot.
        camera.position = (0, 2, -8)

app.run()
