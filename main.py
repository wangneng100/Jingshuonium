import pygame
import sys
import os

# Add the project root directory to the Python path.
# This ensures that modules like 'ui' can be found regardless of how the script is run.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

# --- Initialization ---
# This block must come BEFORE other game module imports (like assets)
# because they rely on the display mode being set.
pygame.init()
screen = pygame.display.set_mode(tuple(config.WINDOW_SIZE))
pygame.display.set_caption(config.WINDOW_TITLE)
clock = pygame.time.Clock()

import assets
import definitions
import math
import json
from perlin_noise import PerlinNoise
import random
from inventory import PlayerInventory
from pause_menu import PauseMenu
from base_ui import InventoryUI
from crafting_ui import CraftingUI
from chest_ui import ChestUI
from furnace_ui import FurnaceUI
from hud import Hotbar, HealthBar, TimeDisplay
from menu_utils import Button

# --- Placeholder Definitions ---
# These are added to resolve NameErrors for features that are not yet fully implemented.

class MapMenu:
    """UI for traveling between different areas."""
    def __init__(self, current_area):
        self.current_area = current_area
        self.font = assets.font
        self.title_text = "Travel Map"
        self.areas = ['farm', 'lakes', 'lumber', 'mines', 'plains', 'dungeon']

        self.buttons = []
        
        button_width = 200
        button_height = 50
        total_width = len(self.areas) * (button_width + 20) - 20
        start_x = (config.WINDOW_SIZE[0] - total_width) / 2
        y_pos = config.WINDOW_SIZE[1] / 2 - button_height / 2

        for i, area_name in enumerate(self.areas):
            x_pos = start_x + i * (button_width + 20)
            button = Button(
                x_pos,
                y_pos,
                button_width, button_height,
                area_name.title(), assets.font,
                (100, 100, 100), (150, 150, 150)
            )
            # Disable button for current area
            if area_name == self.current_area:
                button.base_color = (60, 60, 60)
                button.hover_color = (60, 60, 60)
            self.buttons.append({'button': button, 'area': area_name})

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN and (event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE):
            return "close"

        for btn_info in self.buttons:
            # Don't process clicks on the disabled button for the current area
            if btn_info['area'] == self.current_area:
                continue
            if btn_info['button'].handle_event(event):
                return f"travel_{btn_info['area']}"
        return None

    def draw(self, surface):
        # Simple dark overlay
        overlay = pygame.Surface(config.WINDOW_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Title
        title_surf = self.font.render(self.title_text, True, assets.WHITE)
        title_rect = title_surf.get_rect(center=(config.WINDOW_SIZE[0] / 2, config.WINDOW_SIZE[1] / 2 - 80))
        surface.blit(title_surf, title_rect)

        # Draw buttons
        for btn_info in self.buttons:
            btn_info['button'].draw(surface)
            if btn_info['area'] == self.current_area:
                # Draw an indicator for the current area
                pygame.draw.rect(surface, (255, 223, 0), btn_info['button'].rect.inflate(4, 4), 2, border_radius=10)

def save_game(game_state, save_file_name="world.json"):
    """Saves the current game state to a file."""
    player_data = {
        'pos': [game_state['player'].pos.x, game_state['player'].pos.y],
        'health': game_state['player'].health,
        'inventory': game_state['player'].inventory.slots,
        'armor_slot': game_state['player'].inventory.armor_slot
    }
    
    current_area_name = game_state['current_area']
    game_state['areas'][current_area_name] = {
        'blocks': game_state['blocks'], 'enemies': [], 'block_entities': game_state['block_entities'],
        'player_pos': list(game_state['player'].pos), 'generated_chunks': game_state['generated_chunks']
    }

    serializable_areas = {}
    for area_name, area_data in game_state['areas'].items():
        area_blocks_data = [{'pos': [b.grid_pos.x, b.grid_pos.y], 'type': b.type, 'layer': b.layer} for b in area_data['blocks']]
        area_be_data = {f"{pos[0]},{pos[1]}": entity for pos, entity in area_data['block_entities'].items()}
        serializable_areas[area_name] = {'blocks': area_blocks_data, 'block_entities': area_be_data, 'player_pos': area_data['player_pos']}

    world_data = {
        'player': player_data, 'time_of_day': game_state['time_of_day'], 'day': game_state['day'],
        'difficulty': game_state['difficulty'], 'money': game_state['money'], 'current_area': game_state['current_area'],
        'areas': serializable_areas
    }

    try:
        with open(save_file_name, 'w') as f:
            json.dump(world_data, f, indent=4)
        print(f"Game saved to {save_file_name}")
    except Exception as e:
        print(f"Error saving game: {e}")

def load_game(save_file_name="world.json"):
    """Loads the game state from a file."""
    if not os.path.exists(save_file_name):
        print(f"Save file {save_file_name} not found.")
        return None
    
    try:
        with open(save_file_name, 'r') as f:
            data = json.load(f)
            
        player_data = data['player']
        player = PlayerController(player_data['pos'])
        player.health = player_data['health']
        player.inventory.slots = player_data['inventory']
        player.inventory.armor_slot = player_data.get('armor_slot')

        areas = {}
        for area_name, area_data in data.get('areas', {}).items():
            area_blocks = [Voxel(b['pos'], b['type'], b.get('layer', 1)) for b in area_data['blocks']]
            area_be = {tuple(map(int, pos_str.split(','))): entity for pos_str, entity in area_data.get('block_entities', {}).items()}
            areas[area_name] = {'blocks': area_blocks, 'enemies': [], 'block_entities': area_be, 'player_pos': area_data['player_pos'], 'generated_chunks': {0}}

        current_area = data.get('current_area', 'farm')
        if current_area not in areas: return None

        current_area_data = areas[current_area]
        blocks, block_entities = current_area_data['blocks'], current_area_data['block_entities']
        player.pos = pygame.Vector2(current_area_data['player_pos'])
        player.start_pos = pygame.Vector2(current_area_data['player_pos'])

        for pos, entity in block_entities.items():
            block = next((b for b in blocks if tuple(b.grid_pos) == pos), None)
            if block and 'inventory' in entity: block.inventory = entity['inventory']

        enemies, time_of_day, day = [], data['time_of_day'], data.get('day', 1)
        generated_chunks = set(areas.get(current_area, {}).get('generated_chunks', {0}))
        difficulty, money = data.get('difficulty', 'normal'), data.get('money', 0)

        print(f"Game loaded from {save_file_name}")
        return blocks, player, enemies, block_entities, time_of_day, generated_chunks, difficulty, day, money, current_area, areas

    except Exception as e:
        print(f"Error loading game: {e}")
        import traceback
        traceback.print_exc()
        return None

def sign(n):
    """A helper function to get the sign of a number (-1, 0, or 1)."""
    return (n > 0) - (n < 0)

def generate_chunk(chunk_x):
    """Generates all the blocks for a single vertical chunk of the world."""
    blocks = []
    chunk_start_x = chunk_x * CHUNK_WIDTH
    terrain_noise = PerlinNoise(octaves=2, seed=NOISE_SEED)
    for x_offset in range(CHUNK_WIDTH):
        world_x = chunk_start_x + x_offset
        height_val = terrain_noise([world_x * 0.01])
        surface_y = int(height_val * 15) + 30
        blocks.append(Voxel((world_x, surface_y), "grass_block"))
        for y in range(surface_y + 1, surface_y + 8):
            blocks.append(Voxel((world_x, y), "dirt"))
        for y in range(surface_y + 8, 100):
            if CAVE_NOISE([world_x * 0.05, y * 0.05]) > 0.3: continue
            block_type = "stone"
            if IRON_NOISE([world_x * 0.1, y * 0.1]) > 0.3: block_type = "iron_ore"
            elif COAL_NOISE([world_x * 0.1, y * 0.1]) > 0.25: block_type = "coal_ore"
            blocks.append(Voxel((world_x, y), block_type))
    return blocks

def generate_farm():
    """Generates a static farm area with predefined features."""
    blocks, enemies, block_entities = [], [], {}
    for x in range(-50, 51):
        blocks.append(Voxel((x, 30), 'grass_block'))
        for y in range(31, 40): blocks.append(Voxel((x, y), 'dirt'))
        for y in range(40, 60): blocks.append(Voxel((x, y), 'stone'))
    house_x, house_y = -5, 29
    for x in range(house_x, house_x + 6): blocks.append(Voxel((x, house_y), 'plank'))
    for y_offset in range(1, 5):
        blocks.append(Voxel((house_x, house_y - y_offset), 'plank'))
        blocks.append(Voxel((house_x + 5, house_y - y_offset), 'plank'))
    for x in range(house_x, house_x + 6): blocks.append(Voxel((x, house_y - 5), 'plank'))
    blocks.append(Voxel((house_x + 1, house_y - 1), 'bed'))
    block_entities[(house_x + 1, house_y - 1)] = {'type': 'bed'}
    blocks.append(Voxel((house_x + 8, house_y - 1), 'shipping_bin'))
    block_entities[(house_x + 8, house_y - 1)] = {'type': 'shipping_bin', 'inventory': [None] * 27}
    return blocks, enemies, block_entities

def game_loop(initial_data, save_file_name="world.json"):
    """Main loop of the game."""
    if len(initial_data) == 7: # New world
        blocks, player, enemies, block_entities, time_of_day, generated_chunks, difficulty = initial_data
        day, money, current_area = 1, 0, 'farm'
        areas = {'farm': {'blocks': blocks, 'enemies': enemies, 'block_entities': block_entities, 'player_pos': list(player.pos), 'generated_chunks': generated_chunks}}
    else: # Loaded world
        blocks, player, enemies, block_entities, time_of_day, generated_chunks, difficulty, day, money, current_area, areas = initial_data

    game_state = {
        'blocks': blocks, 'player': player, 'enemies': enemies, 'block_entities': block_entities, 'time_of_day': time_of_day, 'day': day,
        'generated_chunks': generated_chunks, 'difficulty': difficulty, 'money': money, 'current_area': current_area, 'areas': areas,
        'projectiles': [], 'thrown_staffs': [], 'particles': [], 'camera_offset': pygame.Vector2(0, 0), 'running': True, 'paused': False,
        'active_ui': None, 'held_item': None, 'breaking_block_pos': None, 'break_start_time': 0, 'last_music_track': None,
    }
    
    hotbar, health_bar, time_display, pause_menu = Hotbar(player.inventory), HealthBar(player), TimeDisplay(), PauseMenu()
    inventory_ui = InventoryUI(player.inventory)
    spatial_grid = SpatialGrid(cell_size=assets.BLOCK_SIZE * 4)
    spatial_grid.rebuild(game_state['blocks'] + game_state['enemies'])

    while game_state['running']:
        dt = clock.tick(60) / 1000.0
        mouse_pos, world_mouse_pos = pygame.mouse.get_pos(), pygame.Vector2(pygame.mouse.get_pos()) + game_state['camera_offset']

        for event in pygame.event.get():
            if event.type == pygame.QUIT: game_state['running'] = False
            
            hotbar.handle_input(event)

            if game_state['paused']:
                result = pause_menu.handle_input(event)
                if result == "resume": game_state['paused'] = False
                elif result == "quit": save_game(game_state, save_file_name); return
                continue

            if game_state['active_ui']:
                game_state['held_item'] = game_state['active_ui'].handle_input(event, game_state['held_item'])
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    game_state['held_item'] = game_state['active_ui'].toggle(game_state['held_item'])
                    if not game_state['active_ui'].is_open:
                        game_state['active_ui'] = None
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state['paused'] = True
                elif event.key == pygame.K_e:
                    if not game_state['active_ui']:
                        game_state['active_ui'] = inventory_ui
                    game_state['held_item'] = game_state['active_ui'].toggle(game_state['held_item'])
                    if not game_state['active_ui'].is_open:
                        game_state['active_ui'] = None

        if not game_state['paused'] and not game_state['active_ui']:
            nearby_blocks = spatial_grid.get_nearby(player.rect.inflate(assets.BLOCK_SIZE * 2, assets.BLOCK_SIZE * 2))
            player.update(dt, nearby_blocks, game_state['blocks'], game_state['block_entities'], spatial_grid, mouse_pos, hotbar.get_selected_item_type(), world_mouse_pos, game_state['enemies'], game_state['particles'])
            game_state['camera_offset'].x += (player.rect.centerx - game_state['camera_offset'].x - config.WINDOW_SIZE[0] / 2) * 0.1
            game_state['camera_offset'].y += (player.rect.centery - game_state['camera_offset'].y - config.WINDOW_SIZE[1] / 2) * 0.1

        screen.fill(assets.SKY_BLUE)
        visible_blocks = spatial_grid.get_nearby(pygame.Rect(game_state['camera_offset'], config.WINDOW_SIZE))
        for block in sorted(visible_blocks, key=lambda b: b.layer): draw_block_lod(screen, block, player.pos, game_state['camera_offset'])
        player.draw(screen, game_state['camera_offset'])
        hotbar.draw(screen); health_bar.draw(screen); time_display.draw(screen, game_state['day'], game_state['time_of_day'], game_state['money'])
        if game_state['active_ui']:
            game_state['active_ui'].draw(screen, hotbar)
        if game_state['paused']: pause_menu.draw(screen) # noqa
        pygame.display.flip()

def process_new_day(game_state):
    """Handles daily events, including resource regeneration."""
    print(f"A new day has begun! It is now Day {game_state['day'] + 1}.")
    game_state['day'] += 1
    # --- Resource Regeneration ---
    for area_name, area_data in game_state['areas'].items():
        if area_name in AREA_RESOURCES:
            target_counts = AREA_RESOURCES[area_name]
            
            if 'resource_counts' not in area_data: area_data['resource_counts'] = {}
            current_counts = area_data['resource_counts']
            blocks_in_area = area_data.get('blocks', [])
            if not blocks_in_area: continue # Skip if area not generated yet

            print(f"Checking resources for {area_name}...")
            for resource_type, target_count in target_counts.items():
                # Count current resources to get an accurate number
                if resource_type == 'wood':
                    current_count = sum(1 for b in blocks_in_area if b.type == 'wood')
                else:
                    current_count = sum(1 for b in blocks_in_area if b.type == resource_type)
                
                current_counts[resource_type] = current_count

                if current_count < target_count:
                    needed = target_count - current_count
                    print(f"Regenerating {needed} {resource_type} in {area_name}...")
                    
                    spawn_resource(resource_type, needed, blocks_in_area, area_name)

    return game_state

# --- World Generation Settings ---
NOISE_SEED = random.randint(1, 10000)
TERRAIN_NOISE = PerlinNoise(octaves=2, seed=NOISE_SEED)
COAL_NOISE = PerlinNoise(octaves=4, seed=NOISE_SEED + 1)
IRON_NOISE = PerlinNoise(octaves=5, seed=NOISE_SEED + 2)
DIAMOND_NOISE = PerlinNoise(octaves=6, seed=NOISE_SEED + 3)
GOLD_NOISE = PerlinNoise(octaves=5, seed=NOISE_SEED + 8) # New noise for gold
CAVE_NOISE = PerlinNoise(octaves=3, seed=NOISE_SEED + 4)
RAVINE_NOISE = PerlinNoise(octaves=1, seed=NOISE_SEED + 5) # Low octave for long, smooth shapes
ISLAND_NOISE = PerlinNoise(octaves=1, seed=NOISE_SEED + 6) # For island placement
RIVER_NOISE = PerlinNoise(octaves=1, seed=NOISE_SEED + 7) # For river paths
CHUNK_WIDTH = 16 # How many blocks wide a chunk is
FARM_CLAIM_RECT = pygame.Rect(-6 * assets.BLOCK_SIZE, 25 * assets.BLOCK_SIZE, 12 * assets.BLOCK_SIZE, 15 * assets.BLOCK_SIZE)

AREA_RESOURCES = {
    'lumber': {'wood': 150},
    'mines': {'iron_ore': 100},
    'plains': {'tall_grass': 200},
    'lakes': {'sand': 150},
}

def create_hit_particles(particles_list, pos):
    # White slice
    slice_image = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.line(slice_image, assets.WHITE, (5, 35), (35, 5), 4)
    particles_list.append(Particle(pos, slice_image, (0,0), 0, 0.15))
    # Red blood/spark particles
    for _ in range(8):
        particle_img = pygame.Surface((random.randint(3, 6), random.randint(3, 6)))
        particle_img.fill((200, 30, 30))
        vel = (random.uniform(-150, 150), random.uniform(-150, 50))
        lifespan = random.uniform(0.3, 0.6)
        particles_list.append(Particle(pos, particle_img, vel, 300, lifespan))

def create_explosion_particles(particles_list, pos, block_texture, num_particles=15):
    try:
        # Create small fragments of the block texture
        fragment_size = max(1, block_texture.get_width() // 4)
        for _ in range(num_particles):
            # Get a random small piece of the texture
            start_x = random.randint(0, block_texture.get_width() - fragment_size)
            start_y = random.randint(0, block_texture.get_height() - fragment_size)
            fragment_img = block_texture.subsurface((start_x, start_y, fragment_size, fragment_size)).copy()
            
            # Scale it down even more
            particle_img = pygame.transform.scale(fragment_img, (random.randint(6, 10), random.randint(6, 10)))

            # Particle physics
            vel_x = random.uniform(-180, 180)
            vel_y = random.uniform(-300, -50)
            lifespan = random.uniform(0.5, 0.9)
            gravity = 500
            particles_list.append(Particle(pos, particle_img, (vel_x, vel_y), gravity, lifespan))
        
        # Add generic dust particles
        for _ in range(num_particles // 2):
            particle_img = pygame.Surface((random.randint(3, 6), random.randint(3, 6)), pygame.SRCALPHA)
            dust_color = block_texture.get_at((block_texture.get_width()//2, block_texture.get_height()//2))
            dust_color = (min(255, dust_color[0]+20), min(255, dust_color[1]+20), min(255, dust_color[2]+20), random.randint(100, 180))
            particle_img.fill(dust_color)
            vel_x = random.uniform(-120, 120)
            vel_y = random.uniform(-200, -40)
            lifespan = random.uniform(0.5, 1.0)
            gravity = 400
            particles_list.append(Particle(pos, particle_img, (vel_x, vel_y), gravity, lifespan))
    except (AttributeError, ValueError, KeyError):
        # This can happen if a texture is missing or subsurface fails on a 1x1 texture.
        pass # Silently fail to avoid crashing on particle effect

def get_neighbors(pos, all_blocks):
    """Gets a block (if any) at pos and its 8 neighbors."""
    neighbors_to_update = []
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            check_pos = pygame.Vector2(pos[0] + dx, pos[1] + dy)
            found_block = next((b for b in all_blocks if b.grid_pos == check_pos), None)
            if found_block:
                neighbors_to_update.append(found_block)
    return neighbors_to_update

def update_lighting(blocks_to_update, all_blocks):
    """Calculates and applies ambient occlusion for a given list of blocks."""
    # Create a set of all foreground solid block positions for fast lookups
    solid_block_grid = {tuple(b.grid_pos) for b in all_blocks if b.layer == 1 and b.is_solid}

    for block in blocks_to_update:
        if block.layer == 2:
            continue # Layer 2 blocks have their own darkening, no AO.

        # Check if the block is exposed to the "sky" (no solid block directly above)
        is_exposed = (block.grid_pos.x, block.grid_pos.y - 1) not in solid_block_grid

        if is_exposed:
            light_level = 1.0
        else:
            # If not exposed, calculate light based on neighbors (Ambient Occlusion)
            neighbor_count = 0
            # Check 8 neighbors
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    neighbor_pos = (block.grid_pos.x + dx, block.grid_pos.y + dy)
                    if neighbor_pos in solid_block_grid:
                        neighbor_count += 1
            
            occlusion_ratio = neighbor_count / 8.0
            min_light = 0.3 # The darkest a block can get from AO
            light_level = 1.0 - (1.0 - min_light) * occlusion_ratio

        block.apply_lighting(light_level)

def calculate_fov(player_pos, solid_blocks_grid, view_radius_blocks):
    """Calculates a set of visible grid coordinates using raycasting."""
    visible_tiles = set()
    player_grid_pos = (int(player_pos.x / assets.BLOCK_SIZE), int(player_pos.y / assets.BLOCK_SIZE))
    
    # The player's own tile is always visible
    visible_tiles.add(player_grid_pos)

    # Cast rays in a circle around the player. A step of 2 degrees is a good balance.
    for angle in range(0, 360, 2):
        rad = math.radians(angle)
        dx, dy = math.cos(rad), math.sin(rad)
        
        # Cast a ray out to the view_radius
        for i in range(1, view_radius_blocks):
            x = player_grid_pos[0] + round(i * dx)
            y = player_grid_pos[1] + round(i * dy)
            
            current_pos = (x, y)
            visible_tiles.add(current_pos)
            
            if current_pos in solid_blocks_grid:
                break # Ray is blocked, stop this ray
    
    return visible_tiles

def is_accessible(player_rect, target_block, spatial_grid):
    """
    Checks if a target block is accessible by casting a line from the player.
    Returns False if a foreground block is in the way.
    """
    player_center = pygame.Vector2(player_rect.center)
    target_center = pygame.Vector2(target_block.rect.center)
    
    line_vec = target_center - player_center
    distance = line_vec.length()

    # Find potential obstacles along the line of sight using the spatial grid
    line_rect = pygame.Rect(player_center, (0,0)).union(pygame.Rect(target_center, (0,0)))
    line_rect.normalize() # Ensure width/height are positive
    potential_obstacles = spatial_grid.get_nearby(line_rect)
    obstacle_grid_positions = {tuple(b.grid_pos) for b in potential_obstacles if b.layer == 1 and b.is_solid and b != target_block}

    if distance < assets.BLOCK_SIZE: return True # If we are very close, assume accessible
    
    # Step a quarter block at a time along the line from player to target
    step_vec = line_vec.normalize() * (assets.BLOCK_SIZE / 4)
    num_steps = int(distance / step_vec.length())

    for i in range(1, num_steps):
        current_pos = player_center + step_vec * i
        current_grid_pos = (math.floor(current_pos.x / assets.BLOCK_SIZE), math.floor(current_pos.y / assets.BLOCK_SIZE))
        if current_grid_pos in obstacle_grid_positions:
            return False # Blocked
    return True # Not blocked

# --- PARTICLE SYSTEM ---
class Particle:
    def __init__(self, pos, image, vel, gravity, lifespan, collides_with_ground=False, is_firefly=False, is_swaying_leaf=False):
        self.pos = pygame.Vector2(pos)
        self.image = image.copy() # Use a copy to modify alpha independently
        self.vel = pygame.Vector2(vel)
        self.gravity = gravity
        self.initial_lifespan = lifespan
        self.lifespan = lifespan
        self.collides_with_ground = collides_with_ground
        self.active = True
        self.is_firefly = is_firefly
        if self.is_firefly:
            self.meander_timer = random.uniform(0, 1)
        self.is_swaying_leaf = is_swaying_leaf
        if self.is_swaying_leaf:
            self.sway_offset = random.uniform(0, 2 * math.pi)

    def update(self, dt, spatial_grid=None):
        if not self.active:
            return

        if self.is_swaying_leaf:
            # Apply a gentle swaying motion. The force is based on a sine wave to create a back-and-forth effect.
            sway_force = math.sin(pygame.time.get_ticks() * 0.003 + self.sway_offset) * 25 # pixels/sec
            # Gently interpolate current x velocity towards the sway force
            self.vel.x += (sway_force - self.vel.x) * 0.05
            # Apply damping to prevent the particle from flying off horizontally
            self.vel.x *= 0.98

        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt

        if self.is_firefly:
            self.meander_timer -= dt
            if self.meander_timer <= 0:
                self.meander_timer = random.uniform(0.5, 1.5)
                # Change direction gently
                self.vel += (random.uniform(-20, 20), random.uniform(-20, 20))
                # Clamp velocity to prevent them from flying too fast
                if self.vel.length() > 20:
                    self.vel.scale_to_length(20)
            # Pulsing light effect
            pulse = (math.sin(pygame.time.get_ticks() * 0.005 + self.pos.x * 0.1) + 1) / 2 # 0 to 1
            alpha = 150 + (pulse * 105) # 150 to 255
            self.image.set_alpha(alpha)

        if self.collides_with_ground and spatial_grid is not None:
            particle_rect = self.image.get_rect(center=self.pos)
            for block in spatial_grid.get_nearby(particle_rect):
                if block.is_solid and block.rect.colliderect(particle_rect):
                    self.active = False
                    return # Particle is dead, stop processing
            # Also remove if it falls too far out of the world
            if self.pos.y > 200 * assets.BLOCK_SIZE:
                self.active = False
        else:
            self.lifespan -= dt
            if self.lifespan <= 0:
                self.active = False
            elif not self.is_firefly: # Fireflies have their own alpha logic, but leaves will fade.
                # Fade out for non-colliding particles
                alpha = max(0, 255 * (self.lifespan / self.initial_lifespan))
                self.image.set_alpha(alpha)

    def draw(self, surface, camera_offset):
        if self.active:
            surface.blit(self.image, self.pos - camera_offset)

# --- THROWN STAFF ENTITY ---
class ThrownStaff:
    def __init__(self, pos, target_pos, owner, initial_velocity=pygame.Vector2(0,0)):
        self.pos = pygame.Vector2(pos)
        self.owner = owner
        # Make the thrown staff large, similar to the held staff
        # The user requested this in a previous prompt, keeping it.
        staff_size = (assets.BLOCK_SIZE - 4) * 3
        self.image = pygame.transform.rotate(pygame.transform.scale(assets.textures['diamond_staff'], (staff_size, staff_size)), -90)
        self.rect = self.image.get_rect(center=self.pos)
        self.angle = 0
        self.spin_speed = 720 # degrees per second
        
        self.state = 'outbound'
        self.speed = 1000
        self.damage = definitions.WEAPON_DAMAGE.get('diamond_staff', 3.5) * 0.5 # Thrown damage is less
        
        direction = (target_pos - self.pos)
        if direction.length_squared() > 0:
            direction.normalize_ip()
        # Add player's velocity to the throw
        self.vel = direction * self.speed + initial_velocity
        
        self.active = True
        self.hit_entities = []
        self.lifespan = 5.0 # Failsafe
        self.distance_traveled = 0.0

    def update(self, dt, spatial_grid, enemies, player, particles_list, camera_offset, window_size):
        if not self.active: return
        
        self.lifespan -= dt
        # If lifespan runs out, return to player
        if self.lifespan <= 0 and self.state == 'outbound':
            self.state = 'inbound'
            self.lifespan = 5.0 # Reset failsafe for return trip

        # The user requested this in a previous prompt, keeping it.
        # --- Staff Trail ---
        if random.random() < 0.4: # Reduced particle spawn rate for performance
            for _ in range(1): # Spawn one particle at a time
                sparkle_img = pygame.Surface((random.randint(4, 7), random.randint(4, 7)), pygame.SRCALPHA)
                pygame.draw.circle(sparkle_img, (180, 255, 255, random.randint(150, 220)), sparkle_img.get_rect().center, sparkle_img.get_width() // 2)
                
                # Particles move slowly away from the staff
                vel = (-self.vel.x * 0.02 + random.uniform(-30, 30), -self.vel.y * 0.02 + random.uniform(-30, 30))
                lifespan = random.uniform(0.4, 0.8)
                gravity = 50
                particles_list.append(Particle(self.pos.copy(), sparkle_img, vel, gravity, lifespan))

        self.angle = (self.angle + self.spin_speed * dt) % 360
        
        if self.state == 'outbound':
            self.distance_traveled += self.vel.length() * dt
            # Bounce off screen edges
            screen_rect = pygame.Rect(camera_offset.x, camera_offset.y, window_size[0], window_size[1])
            if not self.rect.colliderect(screen_rect.inflate(10, 10)):
                self.state = 'inbound'
        
        if self.state == 'inbound':
            direction_to_player = player.rect.center - self.pos
            if direction_to_player.length_squared() > 0: self.vel = direction_to_player.normalize() * self.speed
            if self.rect.colliderect(player.rect):
                self.active = False; player.staff_is_thrown = False
                return

        self.pos += self.vel * dt; self.rect.center = self.pos

        for block in spatial_grid.get_nearby(self.rect):
            if block.is_solid and block.rect.colliderect(self.rect):
                self.state = 'inbound'; self.vel *= -0.8 # Bounce and lose some speed
                break

        for enemy in enemies:
            if enemy not in self.hit_entities and enemy.rect.colliderect(self.rect):
                # Damage increases the further the staff travels
                damage_bonus_per_10_blocks = 2.0
                blocks_traveled = self.distance_traveled / assets.BLOCK_SIZE
                damage_bonus = (blocks_traveled / 10) * damage_bonus_per_10_blocks
                max_bonus = 7.0 # Cap the bonus damage
                final_damage = self.damage + min(damage_bonus, max_bonus)
                enemy.take_damage(final_damage, player, knockback_vector=self.vel); self.hit_entities.append(enemy)

    def draw(self, surface, camera_offset):
        if self.active:
            rotated_image = pygame.transform.rotate(self.image, -self.angle)
            draw_rect = rotated_image.get_rect(center=self.pos - camera_offset)
            surface.blit(rotated_image, draw_rect)

# --- PROJECTILE SYSTEM ---
class Projectile:
    def __init__(self, pos, vel, image, damage, owner, gravity=0, lifespan=5.0, has_trail=False, pierce_count=0, pierce_ignore_types=None):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.image = image
        self.damage = damage
        self.owner = owner
        self.gravity = gravity
        self.lifespan = lifespan
        self.active = True
        self.has_trail = has_trail
        self.pierce_count = pierce_count
        self.pierce_ignore_types = pierce_ignore_types if pierce_ignore_types is not None else []
        self.hit_entities = [] # Prevent hitting the same entity multiple times

    def update(self, dt, spatial_grid, enemies, particles_list):
        if not self.active:
            return

        # Particle trail for sling stones
        if self.has_trail and random.random() < 0.35: # Reduced particle spawn rate for performance
            # Create a small, semi-transparent gray surface for the dust particle
            particle_img = pygame.Surface((random.randint(2, 4), random.randint(2, 4)), pygame.SRCALPHA)
            particle_img.fill((120, 120, 120, 180))
            
            spawn_pos = self.pos.copy()
            # Velocity is slightly opposite to projectile, with some randomness, to create a trailing effect
            vel = (-self.vel.x * 0.05 + random.uniform(-20, 20), -self.vel.y * 0.05 + random.uniform(-20, 20))
            lifespan = random.uniform(0.3, 0.6)
            gravity = 50 # A little gravity to make it feel like dust settling
            # The Particle class will handle fading out since collides_with_ground is False by default
            particles_list.append(Particle(spawn_pos, particle_img, vel, gravity, lifespan))

        self.lifespan -= dt
        if self.lifespan <= 0:
            self.active = False
            return

        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt

        # Collision with blocks
        proj_rect = self.image.get_rect(center=self.pos)
        nearby_blocks = spatial_grid.get_nearby(proj_rect)
        for block in nearby_blocks:
            if block.is_solid and block.rect.colliderect(proj_rect):
                if block.type in self.pierce_ignore_types:
                    continue # Go through this block type

                if self.pierce_count > 0:
                    self.pierce_count -= 1
                    create_explosion_particles(particles_list, self.pos, assets.textures.get(block.type, assets.dirt_texture), num_particles=5)
                    # Don't return, let it continue, but break to avoid hitting multiple blocks in a wall at once
                    break
                else:
                    self.active = False
                    create_explosion_particles(particles_list, self.pos, assets.textures.get(block.type, assets.dirt_texture), num_particles=10)
                    return

        # Collision with enemies
        for enemy in enemies:
            if enemy not in self.hit_entities and enemy.rect.colliderect(proj_rect):
                enemy.take_damage(self.damage, self.owner, source_pos=self.pos, knockback_vector=self.vel)
                self.hit_entities.append(enemy)
                if self.pierce_count <= 0:
                    self.active = False
                    return
                else:
                    self.pierce_count -= 1 # Piercing an enemy also counts
    def draw(self, surface, camera_offset):
        if self.active:
            surface.blit(self.image, self.pos - camera_offset)

# --- SPATIAL HASH GRID FOR OPTIMIZATION ---
class SpatialGrid:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.grid = {}

    def _get_cell_coords(self, pos):
        return (math.floor(pos[0] / self.cell_size), math.floor(pos[1] / self.cell_size))

    def add(self, obj, rect):
        # Add object to all cells it overlaps
        min_cell = self._get_cell_coords(rect.topleft)
        max_cell = self._get_cell_coords(rect.bottomright)
        for x in range(min_cell[0], max_cell[0] + 1):
            for y in range(min_cell[1], max_cell[1] + 1):
                cell_key = (x, y)
                if cell_key not in self.grid:
                    self.grid[cell_key] = []
                self.grid[cell_key].append(obj)

    def remove(self, obj, rect):
        # Remove object from all cells it was in
        min_cell = self._get_cell_coords(rect.topleft)
        max_cell = self._get_cell_coords(rect.bottomright)
        for x in range(min_cell[0], max_cell[0] + 1):
            for y in range(min_cell[1], max_cell[1] + 1):
                cell_key = (x, y)
                if cell_key in self.grid:
                    try:
                        self.grid[cell_key].remove(obj)
                        if not self.grid[cell_key]: # Clean up empty cells
                            del self.grid[cell_key]
                    except ValueError:
                        pass # Object might not be in this cell if its rect was slightly off

    def get_nearby(self, rect):
        nearby_objs = set()
        min_cell = self._get_cell_coords(rect.topleft)
        max_cell = self._get_cell_coords(rect.bottomright)
        for x in range(min_cell[0], max_cell[0] + 1):
            for y in range(min_cell[1], max_cell[1] + 1):
                cell_key = (x, y)
                if cell_key in self.grid:
                    nearby_objs.update(self.grid[cell_key])
        return list(nearby_objs)

    def rebuild(self, objects):
        self.grid.clear()
        for obj in objects:
            # Assuming obj has a .rect attribute
            self.add(obj, obj.rect)

# --- VOXEL DEFINITION ---
class Voxel:
    def __init__(self, grid_pos, block_type="dirt", layer=1, lifespan=None):
        self.grid_pos = pygame.Vector2(grid_pos)
        self.rect = pygame.Rect(self.grid_pos.x * assets.BLOCK_SIZE, self.grid_pos.y * assets.BLOCK_SIZE, assets.BLOCK_SIZE, assets.BLOCK_SIZE) # noqa
        self.type = block_type
        self.layer = layer
        self.light_level = 1.0
        self.is_solid = 'open' not in self.type and self.type not in ['glass', 'tall_grass', 'water']

        self.lifespan = lifespan
        # Special case for bed, which is 2 blocks wide visually
        if self.type == 'bed':
            self.rect.width = assets.BLOCK_SIZE * 2

        # For block entities like furnaces
        if self.type == 'furnace':
            self.inventory = {
                "input": None,
                "fuel": None,
                "output": None
            }
        elif self.type == 'shipping_bin':
            self.inventory = {
                "items": [None] * 27
            }




        base_image = assets.textures.get(self.type, assets.dirt_texture).copy()
        if self.layer == 2:
            darken_surf = pygame.Surface(base_image.get_size(), pygame.SRCALPHA)
            darken_surf.fill((0, 0, 0, 128)) # 50% transparent black
            base_image.blit(darken_surf, (0, 0))

        self.image = base_image.copy()
        self.original_image = base_image.copy()

    def get_rect_for_grid(self):
        # Returns the 1x1 rect for grid logic, ignoring visual size like for beds
        return pygame.Rect(self.grid_pos.x * assets.BLOCK_SIZE, self.grid_pos.y * assets.BLOCK_SIZE, assets.BLOCK_SIZE, assets.BLOCK_SIZE)

    def update_break_visual(self, progress_ratio):
        if progress_ratio <= 0:
            self.image = self.original_image.copy()
        else:
            # Scaling logic
            scale = 1.0 - (progress_ratio * 0.2) # Scale from 1.0 down to 0.8
            new_size = int(assets.BLOCK_SIZE * scale)
            
            # Create a scaled version of the original image
            scaled_image = pygame.transform.scale(self.original_image, (new_size, new_size))

            # Apply darkening effect to the scaled image
            darken_surface = pygame.Surface(scaled_image.get_size(), pygame.SRCALPHA)
            darken_value = int(255 * progress_ratio)
            darken_surface.fill((0, 0, 0, darken_value))
            scaled_image.blit(darken_surface, (0, 0))

            # Create a final transparent surface and center the result
            self.image = pygame.Surface((assets.BLOCK_SIZE, assets.BLOCK_SIZE), pygame.SRCALPHA)
            blit_pos = ((assets.BLOCK_SIZE - new_size) // 2, (assets.BLOCK_SIZE - new_size) // 2)
            self.image.blit(scaled_image, blit_pos)

    def apply_lighting(self, light_level):
        self.light_level = light_level
        self.image = self.original_image.copy()

        # Calculate darkness based on light level. 1.0 is full light, 0.0 is full dark.
        max_darkness_alpha = 220
        darkness = int(max_darkness_alpha * (1.0 - self.light_level))
        
        if darkness > 0:
            darken_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            darken_surf.fill((0, 0, 0, darkness))
            self.image.blit(darken_surf, (0, 0))

    def draw(self, surface, camera_offset):
        # Use the 1x1 grid rect for positioning, but draw the potentially larger image
        draw_pos = (self.grid_pos.x * assets.BLOCK_SIZE - camera_offset.x, self.grid_pos.y * assets.BLOCK_SIZE - camera_offset.y)
        surface.blit(self.image, draw_pos)


def draw_block_lod(surface, block, player_pos, camera_offset):
    """Draws a block with Level of Detail based on distance to player."""
    # Using squared distances is faster as it avoids square roots
    LOD_DIST_SQUARED_HIGH = (25 * assets.BLOCK_SIZE)**2
    LOD_DIST_SQUARED_MEDIUM = (50 * assets.BLOCK_SIZE)**2
    
    dist_sq = player_pos.distance_squared_to(pygame.Vector2(block.rect.center))

    if dist_sq <= LOD_DIST_SQUARED_HIGH:
        block.draw(surface, camera_offset)
    elif dist_sq <= LOD_DIST_SQUARED_MEDIUM:
        # Medium detail: solid average color
        avg_color = assets.avg_colors.get(block.type, (100, 100, 100))
        
        light_level = block.light_level
        final_color = (
            int(avg_color[0] * light_level),
            int(avg_color[1] * light_level),
            int(avg_color[2] * light_level)
        )

        draw_rect = block.get_rect_for_grid().move(-camera_offset.x, -camera_offset.y)
        
        if block.type in ['water', 'glass', 'leaf', 'tall_grass']:
            # For transparent blocks, draw a semi-transparent rect
            s = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
            alpha = 150 if block.type == 'water' else 200
            s.fill(final_color + (alpha,)) # Add alpha
            surface.blit(s, draw_rect.topleft)
        else:
            pygame.draw.rect(surface, final_color, draw_rect)
    # else: Low detail: don't draw very far blocks at all.

def generate_tree(base_pos):
    """Generates a tree at a specific grid position. base_pos is the grass_block to grow on."""
    tree_blocks = []
    x, base_y = base_pos.x, base_pos.y
    
    tree_height = random.randint(5, 12)
    for i in range(tree_height):
        tree_blocks.append(Voxel((x, base_y - 1 - i), "wood"))
    
    leaf_center_y = base_y - tree_height
    leaf_radius = random.uniform(2.5, 3.5)
    for lx in range(-4, 5):
        for ly in range(-3, 3):
            dist = math.sqrt(lx**2 + ((ly - 1) * 1.2)**2)
            if dist < leaf_radius and not (lx == 0 and ly >= 0):
                tree_blocks.append(Voxel((x + lx, leaf_center_y + ly), "leaf"))
    return tree_blocks

def spawn_resource(resource_type, count, blocks_list, area_name):
    """Attempts to spawn a number of a given resource into an area's block list."""
    if not blocks_list: return

    if resource_type.endswith('_ore') or resource_type == 'sand' or resource_type == 'sus_gold':
        # Find 'stone' blocks to replace for ores, or 'dirt' for sand/sus_gold in lakes
        replaceable_type = 'dirt' if area_name == 'lakes' else 'stone'
        replaceable_blocks = [b for b in blocks_list if b.type == replaceable_type]
        if not replaceable_blocks: return

        for _ in range(count):
            if not replaceable_blocks: break
            block_to_replace = random.choice(replaceable_blocks)
            block_to_replace.type = resource_type
            block_to_replace.original_image = assets.textures[resource_type].copy()
            block_to_replace.image = block_to_replace.original_image.copy()
            replaceable_blocks.remove(block_to_replace)

    elif resource_type == 'wood':
        # A tree has multiple wood blocks. Let's say avg 8 wood blocks per tree.
        trees_to_spawn = math.ceil(count / 8)
        grass_blocks = [b for b in blocks_list if b.type == 'grass_block']
        if not grass_blocks: return
        solid_positions = {tuple(b.grid_pos) for b in blocks_list if b.is_solid}
        
        for _ in range(trees_to_spawn):
            spawned = False; attempts = 0
            while not spawned and attempts < 50: # Try 50 times to find a spot for a tree
                attempts += 1
                if not grass_blocks: break
                grass_block = random.choice(grass_blocks)
                is_space_clear = not any((grass_block.grid_pos.x, grass_block.grid_pos.y - y_offset) in solid_positions for y_offset in range(1, 15))
                if is_space_clear:
                    new_tree_blocks = generate_tree(grass_block.grid_pos)
                    blocks_list.extend(new_tree_blocks)
                    for b in new_tree_blocks:
                        if b.is_solid: solid_positions.add(tuple(b.grid_pos))
                    spawned = True

    elif resource_type == 'tall_grass':
        grass_blocks = [b for b in blocks_list if b.type == 'grass_block']
        if not grass_blocks: return
        non_solid_positions = {tuple(b.grid_pos) for b in blocks_list if not b.is_solid}
        for _ in range(count):
            if not grass_blocks: break
            grass_block = random.choice(grass_blocks)
            spot_above = (grass_block.grid_pos.x, grass_block.grid_pos.y - 1)
            if spot_above not in non_solid_positions:
                new_grass = Voxel(spot_above, 'tall_grass')
                blocks_list.append(new_grass)
                non_solid_positions.add(spot_above)

def generate_chunk(chunk_x, world_type='farm'):
    """Generates all blocks for a single vertical chunk of the world, customized by world_type."""
    # --- World Type Parameters ---
    params = {
        'farm':    {'terrain_mult': 5, 'tree_chance': 0.15, 'tree_cooldown': (5, 10), 'grass_chance': 0.4, 'lake_chance': 0.25, 'ravine_thresh': 0.02, 'cave_thresh': 0.3},
        'plains':  {'terrain_mult': 2, 'tree_chance': 0.02, 'tree_cooldown': (10, 20), 'grass_chance': 0.8, 'lake_chance': 0.05, 'ravine_thresh': 0.0, 'cave_thresh': 0.4},
        'lumber':  {'terrain_mult': 6, 'tree_chance': 0.6, 'tree_cooldown': (2, 4), 'grass_chance': 0.2, 'lake_chance': 0.1, 'ravine_thresh': 0.02, 'cave_thresh': 0.3},
        'lakes':   {'terrain_mult': 4, 'tree_chance': 0.1, 'tree_cooldown': (6, 12), 'grass_chance': 0.3, 'lake_chance': 0.6, 'ravine_thresh': 0.035, 'cave_thresh': 0.3},
    }
    p = params.get(world_type, params['farm'])

    new_blocks = []
    chunk_offset_x = chunk_x * CHUNK_WIDTH
    tree_cooldown = 0
    world_vertical_offset = 64 # Creates more sky
    bedrock_y_level = world_vertical_offset + 70 # Bedrock starts below the deepest caves

    surface_points = [] # To store (x, y) of surface blocks

    for x_in_chunk in range(CHUNK_WIDTH):
        x = chunk_offset_x + x_in_chunk
        height = math.floor(TERRAIN_NOISE(x * 0.05) * p['terrain_mult']) + world_vertical_offset

        # Surface layer
        new_blocks.append(Voxel((x, height - 1), "grass_block"))
        surface_points.append((x, height - 1)) # Store surface point
        if random.random() < p['grass_chance']:
            new_blocks.append(Voxel((x, height - 2), "tall_grass"))

        # Dirt layers
        for y in range(3):
            new_blocks.append(Voxel((x, height + y), "dirt"))

        # Underground layers
        for y in range(3, 60): # Much deeper stone layer
            y_world = height + y

            # --- Cave and Ravine Generation ---
            # Ravines are long, vertical cuts. Use stretched noise.
            ravine_val = RAVINE_NOISE([x * 0.02, y_world * 0.005])
            cave_val = CAVE_NOISE([x * 0.06, y_world * 0.06])
            if cave_val > p['cave_thresh'] or (p['ravine_thresh'] > 0 and abs(ravine_val) < p['ravine_thresh']):
                continue # Skip placing a block, creating air

            block_type = "stone"
            
            # Ore generation
            if y_world > 3 and COAL_NOISE([x * 0.08, y_world * 0.08]) > 0.3:
                block_type = "coal_ore"
            elif y_world > 8 and IRON_NOISE([x * 0.09, y_world * 0.09]) > 0.35:
                block_type = "iron_ore"
            elif y_world > 25 and GOLD_NOISE([x * 0.09, y_world * 0.09]) > 0.4: # Gold is less common than iron
                block_type = "gold_ore"
            elif y_world > 40 and DIAMOND_NOISE([x * 0.1, y_world * 0.1]) > 0.45: # Diamonds are very rare and deep
                block_type = "diamond_ore"
            
            new_blocks.append(Voxel((x, y_world), block_type))

        # Add bedrock layer
        for y_offset in range(5):
            new_blocks.append(Voxel((x, bedrock_y_level + y_offset), "stone"))

        if tree_cooldown > 0:
            tree_cooldown -= 1

        if tree_cooldown == 0 and random.random() < p['tree_chance']:
            tree_height = random.randint(5, 12)
            for i in range(tree_height):
                new_blocks.append(Voxel((x, height - 2 - i), "wood"))
            
            leaf_center_y = height - 1 - tree_height
            leaf_radius = random.uniform(2.5, 3.5)
            for lx in range(-4, 5):
                for ly in range(-3, 3):
                    dist = math.sqrt(lx**2 + ((ly - 1) * 1.2)**2)
                    if dist < leaf_radius and not (lx == 0 and ly >= 0):
                        new_blocks.append(Voxel((x + lx, leaf_center_y + ly), "leaf"))
            tree_cooldown = random.randint(*p['tree_cooldown'])

    # --- Lake Generation on main terrain ---
    if random.random() < p['lake_chance']:
        lake_center_x = chunk_offset_x + random.randint(0, CHUNK_WIDTH - 1)

        surface_y_at_center = -1
        for x_surf, y_surf in surface_points:
            if x_surf == lake_center_x:
                surface_y_at_center = y_surf
                break

        if surface_y_at_center != -1:
            lake_radius_x = random.randint(8, 20)
            lake_radius_y = random.randint(4, 7)

            basin_points = set()
            # Carve out an elliptical basin starting from the surface downwards
            for x_offset in range(-lake_radius_x, lake_radius_x + 1):
                for y_offset in range(0, lake_radius_y + 1):
                    # Check if point is inside the ellipse
                    if (x_offset / lake_radius_x)**2 + (y_offset / lake_radius_y)**2 < 1:
                        basin_points.add((lake_center_x + x_offset, surface_y_at_center + y_offset))

            if basin_points:
                # Remove blocks that are being replaced by the lake
                new_blocks = [b for b in new_blocks if tuple(b.grid_pos) not in basin_points]

                # Add the new lake blocks
                for pos in sorted(list(basin_points), key=lambda p: p[1]):
                    is_bottom = (pos[0], pos[1] + 1) not in basin_points
                    block_type = "sand" if is_bottom else "water"
                    new_blocks.append(Voxel(pos, block_type))

    return new_blocks

# --- PLAYER CONTROLLER (2D) ---
class PlayerController:
    def __init__(self, pos):
        self.start_pos = pygame.Vector2(pos)
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)
        # Make player slightly narrower than a block to avoid getting stuck
        self.width = assets.BLOCK_SIZE - 2
        # All entities are 1 block high
        self.stand_height = assets.BLOCK_SIZE - 4
        self.crouch_height = config.CROUCH_HEIGHT * assets.BLOCK_SIZE
        self.height = self.stand_height
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.width, self.height)
        
        self.grounded = False
        self.max_health = 10
        self.health = self.max_health
        self.is_crouching = False
        self.jumps_left = config.MAX_JUMPS
        self.facing = 1 # 1 for right, -1 for left
        self.is_falling = False
        self.fall_start_y = 0
        self.in_water = False
        self.is_sleeping = False
        self.rotation_angle = 0
        self.image = assets.player_texture
        self.held_item_surface = None
        self.block_below = None
        self.is_dying = False
        self.damage_flash_timer = 0
        self.damage_flash_duration = 0.3

        # XP and Leveling
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 100
        self.death_action = None

        # Skills (for skill_tree_ui.py and saving)
        self.skill_points = 0
        self.skills = {}

        # Tool state
        self.is_tool_active = False
        self.last_hit_times = {} # {enemy: last_hit_time_ms}
        self.death_flash_timer = 0

        # New state variables
        self.diamond_pickaxe_normal_mode = False
        self.is_staff_charging_throw = False
        self.staff_is_thrown = False
        self.place_cooldown = 0.0

        # Held item physics state
        self.held_item_pos = None
        self.last_held_item_pos = None
        self.held_item_vel = pygame.Vector2(0, 0)
        self.held_item_angle = 0
        self.held_item_final_surface = None

        # Sling state
        self.is_charging_sling = False
        self.sling_charge_time = 0.0
        self.max_sling_charge_time = 1.5 # seconds

        # Gun state
        self.gun_cooldown = 0.0
        self.sniper_cooldown = 0.0
        # Knockback
        self.knockback_strength = 300
        self.knockback_lift = 150

        # Link to inventory for pickup
        self.inventory = PlayerInventory()

    def get_skill_level(self, skill_id):
        return self.skills.get(skill_id, 0)

    def add_xp(self, amount):
        self.xp += amount
        print(f"Gained {amount} XP! Total: {self.xp}/{self.xp_to_next_level}")
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.skill_points += 1
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            print(f"Leveled up to Level {self.level}! You have {self.skill_points} skill points.")

    def set_held_item(self, item_type):
        if item_type == 'diamond_staff' and self.staff_is_thrown:
            self.held_item_surface = None
            return

        if item_type and item_type in assets.textures:
            item_pixel_size = int(assets.BLOCK_SIZE * config.HELD_ITEM_SIZE)

            if item_type in definitions.ITEM_SCALES:
                scale = definitions.ITEM_SCALES[item_type]
                item_pixel_size = int(item_pixel_size * scale)

            base_surface = pygame.transform.scale(assets.textures[item_type], (item_pixel_size, item_pixel_size))

            self.held_item_surface = base_surface
        else:
            self.held_item_surface = None

    def crouch(self):
        if not self.is_crouching:
            self.is_crouching = True
            self.pos.y += self.stand_height - self.crouch_height
            self.height = self.crouch_height

    def jump(self):
        if self.jumps_left > 0:
            self.vel.y = -math.sqrt(2 * config.JUMP_HEIGHT * assets.BLOCK_SIZE * config.GRAVITY * config.GRAVITY_MULTIPLIER)
            self.jumps_left -= 1
            self.grounded = False
    def reset_tool_state(self):
        self.is_tool_active = False # noqa
        self.last_hit_times.clear()

    def take_damage(self, amount, source=None, source_pos=None, particles_list=None, knockback_vector=None):

        if self.is_dying:
            return

        # Play damage sound for any damage that isn't self-inflicted continuous damage (like darkness)
        if source is not self and assets.damage_sound:
            assets.damage_sound.play()

        # --- Armor Damage Reduction ---
        if self.inventory and self.inventory.armor_slot:
            armor_type = self.inventory.armor_slot['type']
            reduction = definitions.ARMOR_VALUES.get(armor_type, 0.0)
            amount *= (1.0 - reduction)
        self.health -= amount
        self.damage_flash_timer = self.damage_flash_duration

        if knockback_vector:
            self.vel += pygame.Vector2(knockback_vector) * 0.15
            self.vel.y -= self.knockback_lift * 0.4
            self.grounded = False
        elif source_pos:
            knockback_dir = self.pos - pygame.Vector2(source_pos)
            if knockback_dir.length_squared() > 0:
                knockback_dir.normalize_ip()
                self.vel += knockback_dir * self.knockback_strength
                self.vel.y -= self.knockback_lift
                self.grounded = False

        print(f"Took {amount} damage, {self.health} health remaining.")
        if self.health <= 0:
            self.health = 0 # noqa
            self.die()
    def respawn(self, difficulty='normal', all_blocks=None, block_entities=None, spatial_grid=None):
        print("You died!")

        if difficulty == 'darkness':
            print("You died! Your belongings are lost to the darkness... but you find some gear.")
            if self.inventory:
                self.inventory.slots, self.inventory.armor_slot = [None] * 36, None
                self.inventory.add_item('gun', 1)
                self.inventory.add_item('stone', 50) # Ammo for the gun

        self.pos.x, self.pos.y = self.start_pos.x, self.start_pos.y
        self.vel.x, self.vel.y = 0, 0
        self.is_falling = False
        self.health = self.max_health
        self.rect.topleft = self.pos # Immediately sync rect to prevent physics glitches on respawn
        self.is_dying = False
        self.rotation_angle = 0
        self.death_flash_timer = 0

    def die(self):
        if not self.is_dying:
            self.is_dying = True
            self.rotation_angle = 0 # Start rotation from 0
            self.death_action = 'create_graveyard'
    def stand(self, nearby_blocks): # noqa
        if self.is_crouching:
            # Check for overhead collision before standing
            test_rect = pygame.Rect(self.rect.x, self.rect.y - (self.stand_height - self.crouch_height), self.width, self.stand_height)
            if not any(b.is_solid and b.rect.colliderect(test_rect) for b in nearby_blocks):
                self.is_crouching = False
                self.pos.y -= self.stand_height - self.crouch_height
                self.height = self.stand_height # noqa
    def update(self, dt, nearby_blocks, all_blocks, block_entities, spatial_grid, mouse_pos=None, selected_item_type=None, world_mouse_pos=None, enemies=None, particles_list=None, break_progress=0, difficulty='normal', darkness_multiplier=0): # noqa

        if self.place_cooldown > 0:
            self.place_cooldown -= dt

        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= dt

        if self.gun_cooldown > 0:
            self.gun_cooldown -= dt

        if self.sniper_cooldown > 0:
            self.sniper_cooldown -= dt

        if self.is_dying:
            # Death animation: slowly rotate to 90 degrees
            self.rotation_angle += 225 * dt # 90 degrees in 0.4 seconds
            self.death_flash_timer = (self.death_flash_timer + dt) % 0.2 # Cycle every 0.2 seconds
            
            if self.rotation_angle >= 90: # Death animation finished, respawn regardless of difficulty.
                self.respawn(difficulty, all_blocks, block_entities, spatial_grid)
            return # Skip normal update logic

        # --- Water Physics Check ---
        self.in_water = False
        player_center_grid_pos = (math.floor(self.rect.centerx / assets.BLOCK_SIZE), math.floor(self.rect.centery / assets.BLOCK_SIZE))
        block_at_player = next((b for b in nearby_blocks if tuple(b.grid_pos) == player_center_grid_pos and b.type == 'water'), None)
        if block_at_player:
            self.in_water = True
            self.jumps_left = 0 # Can't jump in water
            self.is_falling = False # Reset fall damage when in water

        keys = pygame.key.get_pressed()
        
        # New facing logic: face mouse if holding a tool, otherwise use keys.
        is_tool_held = selected_item_type and ('sword' in selected_item_type or 'pickaxe' in selected_item_type or 'staff' in selected_item_type or 'sling' in selected_item_type or 'gun' in selected_item_type)
        if is_tool_held and world_mouse_pos:
            # Face based on world coordinates of mouse vs player
            if world_mouse_pos.x > self.rect.centerx:
                self.facing = 1
            else:
                self.facing = -1
        else:
            if keys[pygame.K_d]: self.facing = 1
            if keys[pygame.K_a]: self.facing = -1

        if keys[pygame.K_s]:
            self.crouch()
        else:
            self.stand(nearby_blocks) # Pass nearby blocks here

        # Handle jump rotation animation
        is_pickaxe_held = selected_item_type and 'pickaxe' in selected_item_type
        if not self.grounded and not (self.is_tool_active and is_pickaxe_held):
            self.rotation_angle += config.JUMP_ROTATION_SPEED * dt
        else:
            self.rotation_angle = 0

        # Determine which blocks are "effectively solid" for collision this frame
        effectively_solid_blocks = []
        for block in nearby_blocks:
            if block.is_solid or (block.type == 'leaf' and not self.is_crouching):
                effectively_solid_blocks.append(block)
        speed = (config.CROUCH_SPEED if self.is_crouching else config.WALK_SPEED)
        if self.in_water:
            speed *= 0.5 # Slower in water

        target_vel_x = (keys[pygame.K_d] - keys[pygame.K_a]) * speed * assets.BLOCK_SIZE
        
        if self.in_water:
            friction = config.FRICTION * 2.0 # Water drag
            
            # Apply gravity/sinking force
            water_gravity_multiplier = 0.4
            if self.is_crouching:
                water_gravity_multiplier *= 2.0 # Sink 2x faster when crouching
            self.vel.y += config.GRAVITY * config.GRAVITY_MULTIPLIER * water_gravity_multiplier * assets.BLOCK_SIZE * dt

            # Buoyancy/Swim up
            if keys[pygame.K_w]:
                self.vel.y -= 800 * dt
            # Cap fall speed in water
            if self.vel.y > 100: self.vel.y = 100 # Increased cap to allow faster sinking
            self.grounded = False # Can't be grounded in water

            # --- Water Splash Particles ---
            if abs(self.vel.x) > 20 and random.random() < 0.6 and particles_list is not None: # Chance to spawn splash particles when moving
                splash_img = pygame.Surface((random.randint(3, 6), random.randint(3, 6)), pygame.SRCALPHA)
                splash_color = (100, 150, 255, random.randint(150, 200))
                pygame.draw.circle(splash_img, splash_color, splash_img.get_rect().center, splash_img.get_width() // 2)
                
                spawn_pos = (self.rect.centerx + random.uniform(-self.width/2, self.width/2), self.rect.centery)
                vel = (random.uniform(-20, 20) - self.vel.x * 0.1, random.uniform(-80, -40)) # Upwards splash
                lifespan = random.uniform(0.4, 0.7)
                gravity = 250
                particles_list.append(Particle(spawn_pos, splash_img, vel, gravity, lifespan))
        else:
            friction = config.FRICTION if self.grounded else config.AIR_FRICTION
            self.vel.y += config.GRAVITY * config.GRAVITY_MULTIPLIER * assets.BLOCK_SIZE * dt
            if self.vel.y > assets.BLOCK_SIZE * 20: self.vel.y = assets.BLOCK_SIZE * 20

        # Handle continuous jumping when 'W' is held on the ground
        if keys[pygame.K_w] and self.grounded and not self.in_water:
            self.jump()

        self.vel.x += (target_vel_x - self.vel.x) * friction * dt
            
        # --- Collision Detection ---
        self.rect.width = self.width
        self.rect.height = self.height

        # X-axis collision
        self.pos.x += self.vel.x * dt
        self.rect.x = int(self.pos.x)
        # Sync rect's y-position before x-collision check. This is crucial because
        # crouching/standing changes pos.y, and the rect needs the correct vertical
        # position to avoid false horizontal collisions.
        self.rect.y = int(self.pos.y)

        for block in effectively_solid_blocks:
            if block.rect.colliderect(self.rect):
                if self.vel.x > 0: # Moving right
                    self.rect.right = block.rect.left
                elif self.vel.x < 0: # Moving left
                    self.rect.left = block.rect.right
                self.pos.x = self.rect.x
                self.vel.x = 0

        # Y-axis collision
        self.pos.y += self.vel.y * dt
        self.rect.y = int(self.pos.y)
        self.grounded = False
        self.block_below = None # Reset each frame
        for block in effectively_solid_blocks:
            if block.rect.colliderect(self.rect):
                if self.vel.y > 0: # Moving down
                    self.rect.bottom = block.rect.top
                    self.grounded = True
                    self.block_below = block
                    self.jumps_left = config.MAX_JUMPS
                elif self.vel.y < 0: # Moving up
                    self.rect.top = block.rect.bottom
                self.pos.y = self.rect.y
                self.vel.y = 0
        
        # --- Held Item Logic & Physics ---
        self.last_held_item_pos = self.held_item_pos.copy() if self.held_item_pos else None
        self.held_item_pos = None # Reset each frame

        is_weapon_held = selected_item_type and ('sword' in selected_item_type or 'staff' in selected_item_type)
        if self.held_item_surface and not self.is_dying:
            is_staff_held = selected_item_type and 'staff' in selected_item_type
            is_pickaxe_held = selected_item_type and 'pickaxe' in selected_item_type
            is_sling_held = selected_item_type == 'sling'
            is_gun_held = selected_item_type == 'gun'

            # Logic to calculate item position, moved from draw()
            # Tools like swords and pickaxes follow the mouse.
            if (is_weapon_held or is_pickaxe_held or is_sling_held or is_gun_held) and world_mouse_pos:
                player_center = pygame.Vector2(self.rect.center)
                direction_to_mouse = world_mouse_pos - player_center

                if direction_to_mouse.length() > 0:
                    rads = math.atan2(-direction_to_mouse.y, direction_to_mouse.x)
                    degs = math.degrees(rads)

                    orbit_radius = self.rect.width * 0.7
                    if self.is_charging_sling and is_sling_held:
                        charge_ratio = min(1.0, self.sling_charge_time / self.max_sling_charge_time)
                        pull_back_distance = self.rect.width * 0.6 * charge_ratio
                        orbit_radius -= pull_back_distance

                    offset = direction_to_mouse.normalize() * orbit_radius
                    self.held_item_pos = player_center + offset

                    # Calculate rotation and final surface
                    self.held_item_final_surface = self.held_item_surface
                    if is_staff_held:
                        staff_length = self.stand_height * 3
                        original_w, original_h = self.held_item_surface.get_size()
                        if original_h > 0:
                            aspect_ratio = original_w / original_h
                            staff_width = int(staff_length * aspect_ratio)
                            self.held_item_final_surface = pygame.transform.scale(self.held_item_surface, (staff_width, int(staff_length)))
                        self.held_item_angle = degs - 45
                    else:
                        if self.facing == 1:
                            self.held_item_angle = degs
                        else:
                            self.held_item_final_surface = pygame.transform.flip(self.held_item_surface, True, False)
                            self.held_item_angle = 180 - degs

                    # Add mining animation for pickaxe
                    if break_progress > 0 and is_pickaxe_held:
                        animation_duration = 0.4  # seconds for one swing
                        animation_time = break_progress % animation_duration
                        animation_progress_ratio = animation_time / animation_duration
                        swing_progress = math.sin(animation_progress_ratio * math.pi) # 0->1->0
                        # A negative angle results in a clockwise swing, which looks correct for mining.
                        swing_angle = -90
                        self.held_item_angle += swing_progress * swing_angle

            else: # Default item position
                item_pos_x = self.rect.centerx
                item_pos_y = self.rect.top - (self.held_item_surface.get_height() / 2)
                self.held_item_pos = pygame.Vector2(item_pos_x, item_pos_y)
                self.held_item_angle = 0
                self.held_item_final_surface = self.held_item_surface
                if self.facing == -1:
                    self.held_item_final_surface = pygame.transform.flip(self.held_item_surface, True, False)

        # Calculate velocity
        if self.held_item_pos and self.last_held_item_pos and dt > 0:
            self.held_item_vel = (self.held_item_pos - self.last_held_item_pos) / dt
        else:
            self.held_item_vel.x = 0
            self.held_item_vel.y = 0

        # --- Sword Damage Logic ---
        if self.is_tool_active and is_weapon_held and self.held_item_pos and enemies and particles_list is not None:
            velocity_magnitude = self.held_item_vel.length()
            swing_velocity_threshold = 400 # Still need this to register a swing vs just holding the tool

            if velocity_magnitude > swing_velocity_threshold:
                # Add swoosh particles
                if random.random() < 0.8: # Higher chance to spawn trail particles
                    # Trail length and transparency based on speed
                    max_velocity_for_scaling = 2000.0
                    speed_ratio = min(1.0, (velocity_magnitude - swing_velocity_threshold) / (max_velocity_for_scaling - swing_velocity_threshold))
                    
                    trail_length = 10 + 40 * speed_ratio
                    trail_alpha = 80 + 100 * speed_ratio
                    
                    swoosh_img = pygame.Surface((trail_length, 4), pygame.SRCALPHA)
                    swoosh_img.fill((200, 200, 200, trail_alpha)) # Grayish and transparent
                    angle = math.degrees(math.atan2(-self.held_item_vel.y, self.held_item_vel.x))
                    swoosh_img = pygame.transform.rotate(swoosh_img, angle)

                    # Calculate direction from player to weapon to offset the particle
                    player_center = pygame.Vector2(self.rect.center)
                    direction_from_player = self.held_item_pos - player_center
                    if direction_from_player.length_squared() > 0:
                        direction_from_player.normalize_ip()
                    
                    # The swoosh is centered on the weapon, but pushed 15px further from the player
                    base_pos = self.held_item_pos + direction_from_player * 25
                    spawn_pos = base_pos + self.held_item_vel.normalize() * (-trail_length / 2)

                    particles_list.append(Particle(spawn_pos, swoosh_img, self.held_item_vel * 0.05, 0, 0.15))

                # Get rotated item rect for collision
                rotated_image = pygame.transform.rotate(self.held_item_final_surface, self.held_item_angle)
                item_rect = rotated_image.get_rect(center=self.held_item_pos)

                for enemy in enemies:
                    if enemy.rect.colliderect(item_rect):
                        ATTACK_SPEED = 0.8 # seconds for full damage charge
                        current_time_ms = pygame.time.get_ticks()
                        last_hit_ms = self.last_hit_times.get(enemy, 0)
                        time_since_last_hit = (current_time_ms - last_hit_ms) / 1000.0

                        # Debounce to prevent one swing from hitting multiple times
                        if time_since_last_hit > 0.2:
                            min_hit_interval = ATTACK_SPEED / 5.0
                            if time_since_last_hit >= min_hit_interval: # noqa
                                base_damage = definitions.WEAPON_DAMAGE.get(selected_item_type, 0)
                                damage_ratio = time_since_last_hit / ATTACK_SPEED
                                damage_multiplier = min(1.0, damage_ratio)**2
                                damage = base_damage * damage_multiplier
                                if not self.grounded: damage *= 1.5 # Crit
                                damage = round(damage, 1)

                                if damage > 0: # noqa
                                    # Pogo jump logic: if mid-air, get a jump boost and reset double jump. This is now an innate, infinite ability.
                                    if not self.grounded and not self.is_crouching:
                                        # If we are falling downwards, the pogo gives a small hop but preserves
                                        # the fall for damage calculation. Otherwise, it's a full boost.
                                        if self.is_falling and self.vel.y > 0:
                                            self.vel.y = -150 # A small, fixed hop to reset jumps without negating the fall.
                                            # Reset fall height to the enemy's position
                                            self.fall_start_y = enemy.rect.bottom
                                        else:
                                            # A full pogo jump boost if moving upwards or stationary.
                                            # Formerly based on skill level, now a fixed value equivalent to the old level 2.
                                            pogo_boost_multiplier = 1.0
                                            # A full pogo jump is like a new jump, so it should reset any existing fall.
                                            self.is_falling = False
                                            self.vel.y = -math.sqrt(2 * config.JUMP_HEIGHT * pogo_boost_multiplier * assets.BLOCK_SIZE * config.GRAVITY * config.GRAVITY_MULTIPLIER)
                                        self.jumps_left = config.MAX_JUMPS - 1 # Reset double jump
                                    
                                    final_knockback_vel = self.held_item_vel.copy()
                                    # User request: reduce knockback during bullet time (staff charge)
                                    if self.is_staff_charging_throw:
                                        final_knockback_vel *= 0.1

                                    if selected_item_type == 'diamond_staff':
                                        staff_lift_force = 400
                                        final_knockback_vel.y -= staff_lift_force # Always lift
                                    
                                    enemy.take_damage(damage, self, knockback_vector=final_knockback_vel)
                                    self.last_hit_times[enemy] = current_time_ms # Record this hit
                                    create_hit_particles(particles_list, enemy.rect.center)

        # --- Diamond Pickaxe Instant Mining ---
        blocks_to_destroy = []
        is_diamond_pickaxe_held = selected_item_type == 'diamond_pickaxe'
        if self.is_tool_active and is_diamond_pickaxe_held and not self.diamond_pickaxe_normal_mode and self.held_item_pos:
            velocity_magnitude = self.held_item_vel.length()
            break_velocity_threshold = 500 # Lower threshold for easier use

            if velocity_magnitude > break_velocity_threshold:
                rotated_image = pygame.transform.rotate(self.held_item_final_surface, self.held_item_angle)
                item_rect = rotated_image.get_rect(center=self.held_item_pos)

                for block in nearby_blocks: # 'blocks' is nearby_blocks
                    player_grid_pos = pygame.Vector2(self.rect.centerx / assets.BLOCK_SIZE, self.rect.centery / assets.BLOCK_SIZE)
                    if block.is_solid and block not in blocks_to_destroy and item_rect.colliderect(block.rect) and player_grid_pos.distance_to(block.grid_pos) <= 4:
                        
                        required_level = definitions.BLOCK_MINING_LEVEL.get(block.type, 0)
                        held_item_tier = definitions.TOOL_TIERS.get(selected_item_type, 0)
                        
                        if held_item_tier >= required_level:
                            blocks_to_destroy.append(block)

        self.handle_fall_damage(particles_list)
        return blocks_to_destroy

    def handle_fall_damage(self, particles_list):
        # The death plane is now relative to the player's starting Y position.
        death_plane_y = self.start_pos.y + 200 * assets.BLOCK_SIZE
        if self.pos.y > death_plane_y: # Death plane
            self.die()
            return

        if not self.grounded and not self.is_falling:
            # Only start tracking a fall if the player is actually moving downwards.
            if self.vel.y > 0:
                self.is_falling = True
                self.fall_start_y = self.pos.y
        
        if self.grounded and self.is_falling:
            fall_distance = (self.pos.y - self.fall_start_y) / assets.BLOCK_SIZE
            damage_threshold = config.FALL_DAMAGE_THRESHOLD
            if fall_distance >= 1.5: # Any fall greater than 1.5 blocks
                # Spawn dust particles
                num_dust = min(15, int(fall_distance * 2))
                if self.block_below and particles_list is not None:
                    try:
                        block_texture = assets.textures.get(self.block_below.type, assets.dirt_texture)
                        dust_color = pygame.transform.average_color(block_texture)
                        for _ in range(num_dust):
                            particle_img = pygame.Surface((random.randint(4, 8), random.randint(4, 8)))
                            particle_img.fill(dust_color)
                            particle_img.set_alpha(random.randint(100, 150))
                            spawn_pos = (self.rect.centerx + random.uniform(-self.width/2, self.width/2), self.rect.bottom)
                            vel = (random.uniform(-50, 50), random.uniform(-80, -20))
                            lifespan = random.uniform(0.4, 0.8)
                            particles_list.append(Particle(spawn_pos, particle_img, vel, 100, lifespan))
                    except: pass

            if fall_distance >= damage_threshold:
                # Damage is 0.5 (half a heart) for each block fallen past the threshold, rounded to one decimal.
                damage = round((fall_distance - damage_threshold) * 0.5, 1)
                self.take_damage(damage, particles_list=particles_list)

                # --- High Fall Particle Effect ---
                if particles_list is not None:
                    num_impact_particles = min(25, 5 + int(damage * 5)) # More particles for more damage
                    if self.block_below:
                        try:
                            block_texture = assets.textures.get(self.block_below.type, assets.dirt_texture)
                            create_explosion_particles(particles_list, self.rect.midbottom, block_texture, num_particles=num_impact_particles)
                        except: pass
            self.is_falling = False

    def draw(self, surface, camera_offset, break_progress=0, selected_item_type=None, world_mouse_pos=None):
        # Draw the player's character model
        if self.image:
            base_image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
            if self.facing == -1:
                base_image = pygame.transform.flip(base_image, True, False)
            
            # Apply damage flash if not dying
            if self.damage_flash_timer > 0 and not self.is_dying:
                flash_image = base_image.copy()
                flash_image.fill((255, 100, 100), special_flags=pygame.BLEND_RGB_ADD)
                base_image = flash_image

            if self.is_dying:
                # Flash red for 0.1s every 0.2s
                if self.death_flash_timer < 0.1:
                    base_image.set_alpha(255)
                    red_tint = pygame.Surface(base_image.get_size(), pygame.SRCALPHA)
                    red_tint.fill((255, 0, 0, 100)) # Semi-transparent red
                    base_image.blit(red_tint, (0,0))

            if not self.grounded or self.is_dying:
                # Rotate the image for the jump animation, but keep the original hitbox.
                rotated_player_image = pygame.transform.rotate(base_image, -self.rotation_angle)
                draw_rect = rotated_player_image.get_rect(center=self.rect.center)
                surface.blit(rotated_player_image, draw_rect.topleft - camera_offset)
            else:
                surface.blit(base_image, self.rect.topleft - camera_offset)
        else: # Fallback to azure rectangle
            draw_rect = self.rect.copy()
            draw_rect.topleft -= camera_offset
            pygame.draw.rect(surface, assets.AZURE, draw_rect)

        # Draw held item
        if self.held_item_final_surface and self.held_item_pos and not self.is_dying:
            rotated_image = pygame.transform.rotate(self.held_item_final_surface, self.held_item_angle)
            new_rect = rotated_image.get_rect(center=self.held_item_pos)
            surface.blit(rotated_image, new_rect.topleft - camera_offset)

# --- ENEMY CONTROLLER ---
class EnemyController:
    def __init__(self, pos, enemy_type='zombie'):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)
        self.enemy_type = enemy_type # noqa

        stats = definitions.ENEMY_STATS.get(self.enemy_type, definitions.ENEMY_STATS['zombie'])
        
        self.max_health = stats['health']
        self.damage = stats['damage']
        self.walk_speed_multiplier = stats['speed_mult']
        self.aggro_radius = assets.BLOCK_SIZE * stats['aggro']
        self.xp_value = stats['xp']

        if self.enemy_type == 'zombie_brute':
            self.width = assets.BLOCK_SIZE - 2
            self.height = assets.BLOCK_SIZE - 4
        elif self.enemy_type == 'crawler':
            self.width = assets.BLOCK_SIZE - 2
            self.height = assets.BLOCK_SIZE - 4
        elif self.enemy_type == 'goliath':
            self.width = assets.BLOCK_SIZE * 2 - 4
            self.height = assets.BLOCK_SIZE * 2 - 4
        else: # Default zombie
            self.width = assets.BLOCK_SIZE - 2
            self.height = assets.BLOCK_SIZE - 4 # Making regular zombie 1 block high

        self.knockback_strength = 150
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.width, self.height)
        
        self.image = pygame.transform.scale(assets.textures[self.enemy_type], (self.width, self.height))

        self.grounded = False
        self.health = self.max_health
        self.facing = -1 # Start facing left
        self.block_below = None
        
        # State
        self.is_dying = False
        self.damage_flash_timer = 0
        self.damage_flash_duration = 0.2
        self.is_attacking = False
        self.attack_windup_duration = 0.5 # seconds
        self.attack_windup_timer = 0.0

        # AI
        self.ai_state = 'wandering'
        self.ai_timer = random.uniform(2, 5) # Time to walk in one direction
        self.attack_cooldown = 0
        self.jump_cooldown = 0
        
        self.knockback_lift = 120

    def take_damage(self, amount, player, source_pos=None, knockback_vector=None):
        if self.is_dying: return
        self.health -= amount
        self.damage_flash_timer = self.damage_flash_duration
        
        if knockback_vector:
            # Apply knockback from a given vector, scaled.
            self.vel += pygame.Vector2(knockback_vector) * 0.15 # Scale the incoming velocity
            self.vel.y -= self.knockback_lift * 0.4 # Apply some base lift
            self.grounded = False
        elif source_pos:
            # Default knockback away from a source position
            knockback_dir = self.pos - pygame.Vector2(source_pos)
            if knockback_dir.length_squared() > 0:
                knockback_dir.normalize_ip()
                self.vel += knockback_dir * self.knockback_strength
                self.vel.y -= self.knockback_lift
                self.grounded = False

        print(f"Zombie took {amount} damage, {self.health} health remaining.")
        if self.health <= 0:
            self.health = 0
            self.die(player)

    def jump(self):
        if self.grounded and self.jump_cooldown <= 0:
            jump_height_blocks = 3
            jump_height_pixels = jump_height_blocks * assets.BLOCK_SIZE
            self.vel.y = -math.sqrt(2 * jump_height_pixels * assets.BLOCK_SIZE * config.GRAVITY * config.GRAVITY_MULTIPLIER)
            self.grounded = False
            self.jump_cooldown = random.uniform(0.5, 1.5) # Randomize cooldown too
    def die(self, player):
        self.is_dying = True
        player.add_xp(self.xp_value)

    def update(self, dt, blocks, player, particles_list, darkness_multiplier, light_cone_tiles, difficulty): # noqa
        if self.is_dying: return

        # --- Water Physics Check ---
        self.in_water = False
        enemy_center_grid_pos = (math.floor(self.rect.centerx / assets.BLOCK_SIZE), math.floor(self.rect.centery / assets.BLOCK_SIZE))
        block_at_enemy = next((b for b in blocks if tuple(b.grid_pos) == enemy_center_grid_pos and b.type == 'water'), None)
        if block_at_enemy:
            self.in_water = True

        speed_multiplier = 1.0 # Default for normal/sandbox
        if difficulty == 'darkness':
            # --- Light Weakness & Speed Boost Logic for Darkness ---
            is_in_light = False
            # Check 1: Daylight (which is minimal on darkness)
            if darkness_multiplier < 0.1: 
                is_in_light = True
            
            # Check 2: Flashlight
            if not is_in_light:
                enemy_grid_pos = (int(self.rect.centerx / assets.BLOCK_SIZE), int(self.rect.centery / assets.BLOCK_SIZE))
                if enemy_grid_pos in light_cone_tiles:
                    is_in_light = True

            if is_in_light:
                speed_multiplier = 0.0 # Can't move in light
            else:
                speed_multiplier = 3.0 # "really fast" in the dark

        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= dt

        if self.jump_cooldown > 0:
            self.jump_cooldown -= dt
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # --- AI Logic ---
        target_vel_x = self.vel.x # Default to current velocity to allow knockback to decay
        if self.is_attacking:
            self.attack_windup_timer -= dt
            if self.attack_windup_timer <= 0:
                # Attack connects
                if self.rect.colliderect(player.rect):
                     player.take_damage(self.damage, source=self, source_pos=self.pos, particles_list=particles_list)
                self.is_attacking = False
                self.attack_cooldown = 1.0 # Cooldown after attack connects
            target_vel_x = 0 # Stand still while attacking
        else:
            dist_to_player = self.pos.distance_to(player.pos)

            if dist_to_player < self.aggro_radius:
                self.ai_state = 'chasing'
            else:
                self.ai_state = 'wandering'

            if self.ai_state == 'chasing':
                if abs(player.pos.x - self.pos.x) > 5:
                    self.facing = sign(player.pos.x - self.pos.x)
            elif self.ai_state == 'wandering':
                self.ai_timer -= dt
                if self.ai_timer <= 0:
                    self.ai_timer = random.uniform(2, 5)
                    self.facing *= -1
            target_vel_x = self.facing * (config.WALK_SPEED * self.walk_speed_multiplier * assets.BLOCK_SIZE * speed_multiplier * 0.5) # noqa
            
            # --- Player Interaction ---
            attack_range_rect = self.rect.inflate(assets.BLOCK_SIZE, 0) # 1 block horizontal range
            if attack_range_rect.colliderect(player.rect) and self.attack_cooldown <= 0:
                # Start attack wind-up instead of instant damage
                self.is_attacking = True
                self.attack_windup_timer = self.attack_windup_duration
                self.vel.x = 0 # Stop moving to attack
        
        friction = config.FRICTION if self.grounded else config.AIR_FRICTION
        self.vel.x += (target_vel_x - self.vel.x) * friction * dt

        # --- Physics ---
        self.vel.y += config.GRAVITY * config.GRAVITY_MULTIPLIER * assets.BLOCK_SIZE * dt
        if self.vel.y > assets.BLOCK_SIZE * 20: self.vel.y = assets.BLOCK_SIZE * 20

        # X-axis collision
        self.pos.x += self.vel.x * dt
        self.rect.x = int(self.pos.x)
        for block in [b for b in blocks if b.is_solid]:
            if block.rect.colliderect(self.rect):
                if self.vel.x > 0: self.rect.right = block.rect.left
                elif self.vel.x < 0: self.rect.left = block.rect.right
                self.pos.x = self.rect.x
                self.vel.x = 0
                if self.ai_state == 'chasing':
                    self.jump()
                elif self.ai_state == 'wandering': self.facing *= -1; self.ai_timer = random.uniform(1, 3)

        # Y-axis collision
        self.pos.y += self.vel.y * dt
        self.rect.y = int(self.pos.y)
        self.grounded = False
        self.block_below = None
        for block in [b for b in blocks if b.is_solid]:
            if block.rect.colliderect(self.rect):
                if self.vel.y > 0: # Moving down
                    self.rect.bottom = block.rect.top
                    self.grounded = True
                    self.block_below = block
                elif self.vel.y < 0: # Moving up
                    self.rect.top = block.rect.bottom
                self.pos.y = self.rect.y
                self.vel.y = 0

    def draw(self, surface, camera_offset, difficulty='normal'):
        final_image = pygame.transform.flip(self.image, True, False) if self.facing == 1 else self.image
        # Apply damage flash
        if self.damage_flash_timer > 0:
            flash_image = final_image.copy()
            flash_image.fill((255, 100, 100), special_flags=pygame.BLEND_RGB_ADD)
            draw_pos = self.rect.topleft - camera_offset
            surface.blit(flash_image, draw_pos)
        else:
            draw_pos = self.rect.topleft - camera_offset
            surface.blit(final_image, draw_pos)

        if difficulty == 'darkness':
            eye_y = self.rect.top - camera_offset.y + self.height * 0.25
            eye_x1 = self.rect.centerx - camera_offset.x - 4
            eye_x2 = self.rect.centerx - camera_offset.x + 4
            pygame.draw.circle(surface, (255, 0, 0), (eye_x1, eye_y), 3)
            pygame.draw.circle(surface, (255, 0, 0), (eye_x2, eye_y), 3)
            pygame.draw.circle(surface, (255, 100, 100), (eye_x1, eye_y), 1)
            pygame.draw.circle(surface, (255, 100, 100), (eye_x2, eye_y), 1)

        # Draw health bar if recently damaged
        if self.damage_flash_timer > 0:
            health_ratio = self.health / self.max_health
            bar_width = self.rect.width
            bar_height = 5
            bar_x = self.rect.x - camera_offset.x
            bar_y = self.rect.y - camera_offset.y - bar_height - 3

            pygame.draw.rect(surface, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(surface, (220, 0, 0), (bar_x, bar_y, bar_width * health_ratio, bar_height))

class BossController(EnemyController):
    def __init__(self, pos):
        super().__init__(pos, enemy_type='boss')
        self.width = assets.BLOCK_SIZE * 1.5
        self.height = assets.BLOCK_SIZE * 2.5
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.width, self.height)
        self.image = pygame.transform.scale(assets.textures['boss'], (int(self.width), int(self.height)))

        # Held item logic from PlayerController
        self.held_item_surface = None
        self.held_item_pos = None
        self.last_held_item_pos = None
        self.held_item_vel = pygame.Vector2(0, 0)
        self.held_item_angle = 0
        self.held_item_final_surface = None
        self.is_tool_active = True # Always active for boss
        self.last_hit_time = 0
        self.set_held_item('diamond_staff')

        # New attack state
        self.is_charging_attack = False
        self.attack_windup_timer = 0.0
        self.attack_windup_duration = 1.5 # Slower windup for telegraph
        self.special_attack_cooldown = 0.0
        self.attack_target_pos = None

        # New melee attack state & slow rotation
        self.is_in_melee_attack = False
        self.melee_timer = 0.0
        self.melee_cooldown = 0.0
        self.visual_angle = 0.0
        self.rotation_speed = 45 # degrees per second, for slow tracking

        # New dash attack state
        self.is_charging_dash = False
        self.is_dashing = False
        self.dash_windup_timer = 0.0
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.dash_target_vector = pygame.Vector2(0, 0)
        self.dash_spin_angle = 0.0

    def take_damage(self, amount, player, source_pos=None, knockback_vector=None):
        # Make boss invulnerable during telegraphed attacks to prevent unintended damage.
        if self.is_charging_attack or self.is_charging_dash:
            return
        super().take_damage(amount, player, source_pos, knockback_vector)

    def set_held_item(self, item_type):
        if item_type and item_type in assets.textures:
            item_pixel_size = int(assets.BLOCK_SIZE * config.HELD_ITEM_SIZE * 2) # Boss is bigger
            scale = definitions.ITEM_SCALES.get(item_type, 1.0)
            item_pixel_size = int(item_pixel_size * scale)
            base_surface = pygame.transform.scale(assets.textures[item_type], (item_pixel_size, item_pixel_size))
            self.held_item_surface = base_surface
        else:
            self.held_item_surface = None

    def jump(self):
        # Boss can jump/glide in mid-air to stay aloft, like Flappy Bird.
        if self.jump_cooldown <= 0:
            jump_height_blocks = 4 # A bit less than a normal jump to be more "flappy"
            jump_height_pixels = jump_height_blocks * assets.BLOCK_SIZE
            # Using the same (if potentially buggy) formula as other enemies for consistency
            self.vel.y = -math.sqrt(2 * jump_height_pixels * assets.BLOCK_SIZE * config.GRAVITY * config.GRAVITY_MULTIPLIER)
            self.grounded = False
            self.jump_cooldown = 0.4 # Short cooldown for rapid "flaps"

    def update(self, dt, blocks, player, particles_list, darkness_multiplier, light_cone_tiles, difficulty):
        if self.is_dying: return

        # Decrement timers
        if self.damage_flash_timer > 0: self.damage_flash_timer -= dt
        if self.jump_cooldown > 0: self.jump_cooldown -= dt
        if self.special_attack_cooldown > 0: self.special_attack_cooldown -= dt
        if self.melee_cooldown > 0: self.melee_cooldown -= dt
        if self.dash_cooldown > 0: self.dash_cooldown -= dt

        # --- AI and Attack Logic ---
        target_vel_x = 0
        special_attack_range = self.aggro_radius * 0.9
        melee_attack_range_rect = self.rect.inflate(assets.BLOCK_SIZE * 1.5, assets.BLOCK_SIZE * 0.5)
        dash_attack_range = self.aggro_radius * 0.6 # Medium range for dash

        is_currently_attacking = self.is_charging_attack or self.is_in_melee_attack or self.is_charging_dash or self.is_dashing

        # --- Gliding/Flying AI ---
        # If falling and player is generally above, try to fly up.
        if self.vel.y > -50 and player.rect.bottom < self.rect.top + assets.BLOCK_SIZE * 2:
            self.jump()

        if self.is_charging_attack:
            target_vel_x = 0 # Stop moving
            self.attack_windup_timer -= dt
            # Telegraph phase: spawn glowing particles at the target location
            if self.attack_windup_timer > 0:
                if random.random() < 0.6: # Spawn particles frequently
                    glow_img = pygame.Surface((random.randint(25, 45), random.randint(25, 45)), pygame.SRCALPHA)
                    color = (255, 50, 50, random.randint(100, 180))
                    radius = glow_img.get_width() // 2
                    pygame.draw.circle(glow_img, color, (radius, radius), radius)
                    
                    # Particles appear in a shrinking circle
                    spawn_angle = random.uniform(0, 2 * math.pi)
                    spawn_radius = assets.BLOCK_SIZE * 1.5 * (self.attack_windup_timer / self.attack_windup_duration)
                    spawn_offset = pygame.Vector2(math.cos(spawn_angle), math.sin(spawn_angle)) * spawn_radius
                    spawn_pos = pygame.Vector2(self.attack_target_pos) + spawn_offset
                    
                    particles_list.append(Particle(spawn_pos, glow_img, (0,0), 0, 0.2))
            # Attack phase: windup is over
            else:
                self.is_charging_attack = False
                self.special_attack_cooldown = 5.0 # Increased from 3.0 seconds

                # Create explosion at target
                attack_rect = pygame.Rect(0,0, assets.BLOCK_SIZE * 3, assets.BLOCK_SIZE * 3)
                attack_rect.center = self.attack_target_pos
                
                # Big particle explosion
                for _ in range(40):
                    particle_img = pygame.Surface((random.randint(6, 12), random.randint(6, 12)))
                    particle_img.fill((255, random.randint(40, 100), 40))
                    vel = (random.uniform(-300, 300), random.uniform(-300, 300))
                    lifespan = random.uniform(0.5, 0.9)
                    particles_list.append(Particle(attack_rect.center, particle_img, vel, 400, lifespan))

                # Damage player if in range
                if attack_rect.colliderect(player.rect):
                    player.take_damage(self.damage * 1.5, self, source_pos=self.pos)
        elif self.is_in_melee_attack:
            self.melee_timer -= dt
            target_vel_x = 0 # Stand still during attack

            # Damage check during swing phase
            if self.melee_timer <= 0.3: # Swing phase is the last 0.3s
                rotated_image = pygame.transform.rotate(self.held_item_final_surface, self.held_item_angle)
                item_rect = rotated_image.get_rect(center=self.held_item_pos)
                if player.rect.colliderect(item_rect) and self.last_hit_time == 0:
                    player.take_damage(self.damage, self, knockback_vector=self.held_item_vel)
                    self.last_hit_time = 1 # Mark as hit for this swing
                    create_hit_particles(particles_list, player.rect.center)

            if self.melee_timer <= 0:
                self.is_in_melee_attack = False
        else:
            # --- Dash Attack Logic ---
            if self.is_charging_dash:
                self.dash_windup_timer -= dt
                self.dash_spin_angle = (self.dash_spin_angle + 1080 * dt) % 360 # Fast spin
                target_vel_x = 0 # Stand still

                if self.dash_windup_timer <= 0:
                    self.is_charging_dash = False
                    self.is_dashing = True
                    self.dash_timer = 0.7 # Dash for 0.7 seconds
                    direction_to_player = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
                    if direction_to_player.length_squared() > 0:
                        self.dash_target_vector = direction_to_player.normalize()
                    else:
                        self.dash_target_vector = pygame.Vector2(self.facing, 0)
            elif self.is_dashing:
                self.dash_timer -= dt
                self.dash_spin_angle = (self.dash_spin_angle + 1080 * dt) % 360 # Continue spinning

                dash_speed = 1200
                self.vel = self.dash_target_vector * dash_speed

                # Override normal physics for the dash
                self.pos += self.vel * dt
                self.rect.center = self.pos

                # Damage player on contact during dash
                if self.rect.colliderect(player.rect):
                    player.take_damage(self.damage * 2.0, self, knockback_vector=self.vel * 0.5)
                    self.dash_timer = 0 # End dash early on hit

                # Stop dash on hitting a wall
                for block in [b for b in blocks if b.is_solid]:
                    if block.rect.colliderect(self.rect):
                        self.dash_timer = 0
                        create_explosion_particles(particles_list, self.rect.center, assets.textures['stone'], num_particles=20)
                        break

                if self.dash_timer <= 0:
                    self.is_dashing = False
                    self.dash_cooldown = 4.0
                    self.vel = pygame.Vector2(0, 0) # Stop immediately
            else:
                # Decide which attack to use, or chase
                dist_to_player = self.pos.distance_to(player.pos)

                if melee_attack_range_rect.colliderect(player.rect) and self.melee_cooldown <= 0: # noqa
                    self.is_in_melee_attack = True; self.melee_timer = 3.3; self.melee_cooldown = 4.0; self.last_hit_time = 0
                elif dash_attack_range < dist_to_player < special_attack_range and self.dash_cooldown <= 0:
                    self.is_charging_dash = True; self.dash_windup_timer = 1.2
                elif dist_to_player < special_attack_range and self.special_attack_cooldown <= 0:
                    self.is_charging_attack = True; self.attack_windup_timer = self.attack_windup_duration; self.attack_target_pos = player.rect.center
                else:
                    self.facing = sign(player.pos.x - self.pos.x); target_vel_x = self.facing * (config.WALK_SPEED * self.walk_speed_multiplier * assets.BLOCK_SIZE * 0.5)

        if not self.is_dashing:
            # --- Physics (from EnemyController) ---
            friction = config.FRICTION if self.grounded else config.AIR_FRICTION
            self.vel.x += (target_vel_x - self.vel.x) * friction * dt
            self.vel.y += config.GRAVITY * config.GRAVITY_MULTIPLIER * assets.BLOCK_SIZE * dt
            if self.vel.y > assets.BLOCK_SIZE * 20: self.vel.y = assets.BLOCK_SIZE * 20

            # X-axis collision
            self.pos.x += self.vel.x * dt
            self.rect.x = int(self.pos.x)
            for block in [b for b in blocks if b.is_solid]:
                if block.rect.colliderect(self.rect):
                    if self.vel.x > 0: self.rect.right = block.rect.left
                    elif self.vel.x < 0: self.rect.left = block.rect.right
                    self.pos.x = self.rect.x
                    self.vel.x = 0
                    self.jump()

            # Y-axis collision
            self.pos.y += self.vel.y * dt
            self.rect.y = int(self.pos.y)
            self.grounded = False
            self.block_below = None
            for block in [b for b in blocks if b.is_solid]:
                if block.rect.colliderect(self.rect):
                    if self.vel.y > 0:
                        self.rect.bottom = block.rect.top
                        self.grounded = True
                        self.block_below = block
                    elif self.vel.y < 0:
                        self.rect.top = block.rect.bottom
                    self.pos.y = self.rect.y
                    self.vel.y = 0

        # --- Held Item Visuals ---
        self.last_held_item_pos = self.held_item_pos.copy() if self.held_item_pos else None
        self.held_item_pos = None

        if self.held_item_surface and not self.is_dying:
            boss_center = pygame.Vector2(self.rect.center)
            direction_to_player = pygame.Vector2(player.rect.center) - boss_center
            
            target_angle = self.visual_angle
            orbit_radius = self.rect.width * 0.8
            current_rotation_speed = self.rotation_speed

            if direction_to_player.length() > 0:
                rads = math.atan2(-direction_to_player.y, direction_to_player.x)
                degs = math.degrees(rads)
                
                if self.is_in_melee_attack:
                    windup_time = 0.3 # The swing is the last 0.3s
                    if self.melee_timer > windup_time: # Wind-up phase
                        # Lift the weapon straight up to telegraph the attack.
                        target_angle = 90; orbit_radius = self.rect.height * 0.6
                    else: # Swing phase
                        target_angle = degs; orbit_radius = self.rect.width * 1.1; current_rotation_speed = 1200
                elif not self.is_charging_attack: # Normal aiming
                    target_angle = degs

            angle_diff = (target_angle - self.visual_angle + 180) % 360 - 180
            self.visual_angle += sign(angle_diff) * min(abs(angle_diff), current_rotation_speed * dt)
            self.visual_angle %= 360

            orbit_rads = math.radians(self.visual_angle)
            offset = pygame.Vector2(math.cos(orbit_rads), -math.sin(orbit_rads)) * orbit_radius
            self.held_item_pos = boss_center + offset

            staff_length = self.height * 1.5
            original_w, original_h = self.held_item_surface.get_size()
            if original_h > 0:
                aspect_ratio = original_w / original_h
                staff_width = int(staff_length * aspect_ratio)
                self.held_item_final_surface = pygame.transform.scale(self.held_item_surface, (staff_width, int(staff_length)))
            self.held_item_angle = self.visual_angle - 45
            
        if self.held_item_pos and self.last_held_item_pos and dt > 0: self.held_item_vel = (self.held_item_pos - self.last_held_item_pos) / dt
        else: self.held_item_vel.x = 0; self.held_item_vel.y = 0

    def draw(self, surface, camera_offset, difficulty='normal'):
        # We override the base draw to handle the spinning animation
        base_image = self.image
        if self.is_charging_dash or self.is_dashing:
            base_image = pygame.transform.rotate(self.image, self.dash_spin_angle)
        
        # Apply damage flash
        final_image = base_image
        if self.damage_flash_timer > 0:
            flash_image = base_image.copy()
            flash_image.fill((255, 100, 100, 150), special_flags=pygame.BLEND_RGBA_ADD)
            final_image = flash_image

        # Blit the final image, centered on the boss's rect
        draw_rect = final_image.get_rect(center=self.rect.center - camera_offset)
        surface.blit(final_image, draw_rect)

        # Draw health bar (copied from EnemyController.draw)
        if self.damage_flash_timer > 0:
            health_ratio = self.health / self.max_health
            bar_width = self.rect.width
            bar_height = 5
            bar_x = self.rect.x - camera_offset.x
            bar_y = self.rect.y - camera_offset.y - bar_height - 3
            pygame.draw.rect(surface, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(surface, (220, 0, 0), (bar_x, bar_y, bar_width * health_ratio, bar_height))

        # Draw held item
        if self.held_item_final_surface and self.held_item_pos and not self.is_dying:
            rotated_image = pygame.transform.rotate(self.held_item_final_surface, self.held_item_angle)
            new_rect = rotated_image.get_rect(center=self.held_item_pos)
            surface.blit(rotated_image, new_rect.topleft - camera_offset)

def new_world():
    print("Generating new world...")
    blocks = []
    block_entities = {} # noqa
    enemies = []
    generated_chunks = set()

    # Generate initial area around spawn
    for x in range(-3, 4): # Generate 7 chunks
        chunk_blocks = generate_chunk(x)
        blocks.extend(chunk_blocks)
        generated_chunks.add(x)

    # Find a safe spawn point
    spawn_x = 0
    highest_y_at_spawn = 1000
    for block in blocks:
        if block.grid_pos.x == spawn_x and block.is_solid:
            if block.grid_pos.y < highest_y_at_spawn:
                highest_y_at_spawn = block.grid_pos.y
    spawn_y = (highest_y_at_spawn - config.STAND_HEIGHT - 1) * assets.BLOCK_SIZE
    player = PlayerController((spawn_x * assets.BLOCK_SIZE, spawn_y))

    # A new world should start at a set time, like midday.
    time_of_day = definitions.DAY_NIGHT_DURATION * 0.25

    return blocks, player, enemies, block_entities, time_of_day, generated_chunks

def generate_dungeon(width=60, height=60):
    # 1. Create a grid full of stone
    grid = [['stone' for _ in range(width)] for _ in range(height)]
    
    # 2. Use recursive backtracking to carve a maze
    stack = [(1, 1)]
    visited = set()
    
    while stack:
        x, y = stack[-1]
        grid[y][x] = None # Carve path
        visited.add((x, y))
        
        neighbors = []
        for dx, dy in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
            nx, ny = x + dx, y + dy
            if 1 <= nx < width - 1 and 1 <= ny < height - 1 and (nx, ny) not in visited:
                neighbors.append((nx, ny))
        
        if neighbors:
            nx, ny = random.choice(neighbors)
            # Carve path between current and next cell
            grid[(y + ny) // 2][(x + nx) // 2] = None
            stack.append((nx, ny))
        else:
            stack.pop()

    # 3. Convert grid to Voxel objects
    blocks = []
    enemies = []
    block_entities = {} # noqa
    
    for y, row in enumerate(grid):
        for x, cell_type in enumerate(row):
            if cell_type:
                blocks.append(Voxel((x, y), cell_type))
            else: # It's a path
                # Randomly place chests and enemies in open spaces
                if random.random() < 0.02: # 2% chance for a chest
                    chest_block = Voxel((x, y), 'chest')
                    blocks.append(chest_block)
                    # Populate chest with loot
                    loot = []
                    for _ in range(random.randint(1, 5)):
                        loot_item = random.choice(['iron_ingot', 'gold', 'diamond'])
                        loot_count = random.randint(1, 10)
                        loot.append({'type': loot_item, 'count': loot_count})
                    # Pad with None to fill inventory
                    loot.extend([None] * (27 - len(loot)))
                    block_entities[(x, y)] = {"type": "chest", "inventory": loot}
                elif random.random() < 0.03: # 3% chance for an enemy
                    enemy_type = random.choice(['zombie', 'zombie_brute', 'crawler'])
                    enemies.append(EnemyController((x * assets.BLOCK_SIZE, y * assets.BLOCK_SIZE), enemy_type))

    return blocks, enemies, block_entities

def new_dungeon():
    print("Generating dungeon...")
    blocks, enemies, block_entities = generate_dungeon()
    
    # Player
    player = PlayerController((1.5 * assets.BLOCK_SIZE, 1.5 * assets.BLOCK_SIZE)) # Spawn at start of maze
    player.inventory = PlayerInventory()
    player.inventory.add_item("diamond_staff", 1)
    player.inventory.add_item("plank", 64)

    time_of_day = definitions.DAY_NIGHT_DURATION * 0.25 # permanent day
    generated_chunks = {0} # no chunk generation
    difficulty = 'normal'

    return blocks, player, enemies, block_entities, time_of_day, generated_chunks, difficulty

def generate_arena():
    blocks = []
    # The user requested to remove the fighting platform for the boss.
    # This will result in an aerial battle where both player and boss will fall.
    # The user now wants a floor to prevent the boss and player from falling out of the world.
    width = 150 # Make platform wider to be safe
    floor_y = 40 # A y-level low enough to catch falling entities.
    # Make the floor thicker to prevent entities from clipping through on a long fall.
    for y in range(floor_y, floor_y + 5):
        for x in range(-width//2, width//2):
            blocks.append(Voxel((x, y), "stone"))
    return blocks

def new_test_arena():
    print("Generating test arena...")
    blocks = generate_arena()
    block_entities = {}
    
    # Player
    player = PlayerController((7 * assets.BLOCK_SIZE, 28 * assets.BLOCK_SIZE))
    player.inventory = PlayerInventory()
    player.inventory.add_item("diamond_staff", 1)
    player.inventory.add_item("gun", 1)
    player.inventory.add_item("stone", 999) # ammo

    # Boss
    boss = BossController((10 * assets.BLOCK_SIZE, 27 * assets.BLOCK_SIZE))
    enemies = [boss]

def new_world(difficulty='normal'):
    print(f"Generating new world with difficulty: {difficulty}...")
    
    blocks, enemies, block_entities = generate_farm()
    generated_chunks = {0} # It's a static world, but let's keep this for compatibility.

    # --- Set a fixed, safe spawn point inside the farm claim area ---
    spawn_x = 0
    spawn_y = 24 * assets.BLOCK_SIZE
    player = PlayerController((spawn_x, spawn_y))
    player.start_pos = pygame.Vector2(spawn_x, spawn_y)

    # --- Give starter items based on difficulty ---
    # player.inventory is now initialized in PlayerController __init__
    player.inventory.add_item('wooden_pickaxe', 1)
    player.inventory.add_item('wooden_sword', 1)

    # A new world should start at a set time, like midday.
    time_of_day = definitions.DAY_NIGHT_DURATION * 0.25

    return blocks, player, enemies, block_entities, time_of_day, generated_chunks, difficulty

def loading_screen(load_new_world=True, difficulty='normal', save_file_name="world.json"):
    loading_bar_width = 400
    loading_bar_height = 50
    center_x = config.WINDOW_SIZE[0] / 2
    center_y = config.WINDOW_SIZE[1] / 2
    
    bar_rect = pygame.Rect(center_x - loading_bar_width / 2, center_y, loading_bar_width, loading_bar_height)

    if load_new_world:
        loading_text = "Generating World..."
    else:
        loading_text = "Loading World..."

    # Fake loading for a fixed duration
    start_time = pygame.time.get_ticks()
    load_duration = 1500 # 1.5 seconds

    while pygame.time.get_ticks() - start_time < load_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        progress = (pygame.time.get_ticks() - start_time) / load_duration
        
        screen.fill(assets.BLACK)
        
        # Loading text
        loading_text_surf = assets.font.render(loading_text, True, assets.WHITE)
        text_rect = loading_text_surf.get_rect(center=(center_x, center_y - 40))
        screen.blit(loading_text_surf, text_rect)

        # Loading bar
        pygame.draw.rect(screen, (50, 50, 50), bar_rect) # Background
        progress_bar_rect = pygame.Rect(bar_rect.x, bar_rect.y, bar_rect.width * progress, bar_rect.height)
        pygame.draw.rect(screen, (100, 200, 100), progress_bar_rect) # Progress
        pygame.draw.rect(screen, assets.WHITE, bar_rect, 2) # Border

        pygame.display.flip()
        clock.tick(60)

    game_data = None
    if load_new_world:
        game_data = new_world(difficulty)
    else:
        game_data = load_game(save_file_name)

    if game_data:
        game_loop(initial_data=game_data, save_file_name=save_file_name)
    else:
        # This can happen if loading fails. We should just return to the menu.
        print("Error: Could not load or create game data.")

def world_selection_menu():
    pygame.mouse.set_visible(True)
    menu_running = True
    while menu_running:
        # This menu will show 3 save slots.
        num_slots = 3
        world_buttons = []
        delete_buttons = []
        slot_info = []

        button_width = 400
        button_height = 80
        center_x = config.WINDOW_SIZE[0] / 2
        start_y = config.WINDOW_SIZE[1] * 0.3

        for i in range(num_slots):
            save_file_name = f"world_{i+1}.json"
            y_pos = start_y + i * (button_height + 20)
            
            text = f"World {i+1}"
            color = (50, 100, 150)
            hover_color = (80, 130, 200)
            exists = os.path.exists(save_file_name)

            if exists:
                text += " (Saved)"
                color = (50, 150, 50)
                hover_color = (80, 200, 80)
            else:
                text += " (Empty)"

            world_buttons.append(Button(
                center_x - button_width / 2,
                y_pos,
                button_width, button_height,
                text, assets.font, color, hover_color
            ))
            
            if exists:
                delete_buttons.append(Button(
                    center_x + button_width / 2 + 20,
                    y_pos + (button_height - 40) / 2,
                    80, 40,
                    "Delete", assets.small_font, (180, 50, 50), (220, 80, 80)
                ))
            else:
                delete_buttons.append(None)

            slot_info.append({'save_file': save_file_name, 'exists': exists})

        back_button = Button(
            center_x - 150, 
            config.WINDOW_SIZE[1] * 0.85, 
            300, 50, 
            "Back", assets.font, (150, 50, 50), (200, 80, 80)
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            for i, button in enumerate(world_buttons):
                if button.handle_event(event):
                    info = slot_info[i]
                    if info['exists']:
                        # Load game
                        loading_screen(load_new_world=False, save_file_name=info['save_file'])
                    else:
                        # Create new world - this needs to go to difficulty selection
                        difficulty = 'normal' # Default 'idle' difficulty
                        loading_screen(load_new_world=True, difficulty=difficulty, save_file_name=info['save_file'])
                    # After game, we come back to main menu, so we can exit this loop.
                    menu_running = False
                    return # Return to main menu
            
            for i, button in enumerate(delete_buttons):
                if button and button.handle_event(event):
                    info = slot_info[i]
                    if info['exists']:
                        try:
                            os.remove(info['save_file'])
                        except OSError as e:
                            print(f"Error deleting file {info['save_file']}: {e}")
                        break # Re-draw the menu

            if back_button.handle_event(event):
                menu_running = False

        # Drawing
        screen.fill(assets.SKY_BLUE)
        title_surf = assets.big_font.render("Select a World", True, assets.WHITE)
        title_rect = title_surf.get_rect(center=(center_x, config.WINDOW_SIZE[1] * 0.15))
        screen.blit(title_surf, title_rect)

        for button in world_buttons:
            button.draw(screen)
        for button in delete_buttons:
            if button: button.draw(screen)
        back_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

def main_menu():
    # Setup buttons
    button_width = 300
    button_height = 60
    center_x = config.WINDOW_SIZE[0] / 2
    
    play_button = Button(
        center_x - button_width / 2, 
        config.WINDOW_SIZE[1] * 0.4, 
        button_width, button_height, 
        "Play", assets.big_font, (50, 150, 50), (80, 200, 80)
    )
    quit_button = Button(
        center_x - button_width / 2, 
        config.WINDOW_SIZE[1] * 0.55, 
        button_width, button_height,
        "Quit", assets.big_font, (150, 50, 50), (200, 80, 80)
    )
    buttons = [play_button, quit_button]

    pygame.mouse.set_visible(True)

    menu_running = True
    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
            
            if play_button.handle_event(event):
                world_selection_menu()
                pygame.mouse.set_visible(True)
            
            if quit_button.handle_event(event):
                menu_running = False

        # Drawing
        screen.fill(assets.SKY_BLUE)
        
        # Title
        title_surf = assets.big_font.render(config.WINDOW_TITLE, True, assets.WHITE)
        title_shadow_surf = assets.big_font.render(config.WINDOW_TITLE, True, assets.BLACK)
        title_rect = title_surf.get_rect(center=(center_x, config.WINDOW_SIZE[1] * 0.2))
        shadow_rect = title_shadow_surf.get_rect(center=(title_rect.centerx + 3, title_rect.centery + 3))
        screen.blit(title_shadow_surf, shadow_rect)
        screen.blit(title_surf, title_rect)

        for button in buttons:
            button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

# --- INITIALIZE AND RUN ---
if __name__ == '__main__':
    # This check is to prevent the main game logic from running when imported by other scripts,
    # which can be useful for testing or utility scripts in the future.
    # It ensures that main_menu() is the entry point only when main.py is executed directly.

    # --- Populate world.json with texture data ---
    texture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'texture')
    if os.path.exists(texture_path):
        texture_files = [f for f in os.listdir(texture_path) if os.path.isfile(os.path.join(texture_path, f))]
        
        # Use a specific file for the texture list to avoid conflicts with save files
        texture_data_file = "world.json"
        
        world_data = {}
        if os.path.exists(texture_data_file):
            try:
                with open(texture_data_file, 'r') as f:
                    # Check if file is not empty
                    content = f.read()
                    if content:
                        world_data = json.loads(content)
                    else:
                        world_data = {}
            except json.JSONDecodeError:
                # world.json is empty or corrupted, start with an empty dict
                world_data = {}
        
        world_data['textures'] = texture_files
        
        try:
            with open(texture_data_file, 'w') as f:
                json.dump(world_data, f, indent=4)
            print(f"Updated {texture_data_file} with texture list.")
        except Exception as e:
            print(f"Error writing to {texture_data_file}: {e}")

    try:
        main_menu()
    except Exception as e:
        print(f"\n--- An error occurred: ---\n{e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit.")

