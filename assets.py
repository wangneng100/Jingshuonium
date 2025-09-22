import pygame
import os

pygame.init() # Initialize pygame here to use its functions

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
AZURE = (240, 255, 255)
SKY_BLUE = (135, 206, 235)

# --- Fonts ---
try:
    font_name = "quicksand.otf" # Assumes quicksand.otf is in the same folder
    font = pygame.font.Font(font_name, 30)
    small_font = pygame.font.Font(font_name, 18)
    tiny_font = pygame.font.Font(font_name, 14)
    scaled_small_font = pygame.font.Font(font_name, int(18 * 1.2))
    big_font = pygame.font.Font(font_name, 60)
except FileNotFoundError:
    print(f"Warning: Font '{font_name}' not found. Falling back to Arial.")
    font = pygame.font.SysFont("Arial", 30)
    small_font = pygame.font.SysFont("Arial", 18)
    tiny_font = pygame.font.SysFont("Arial", 14)
    scaled_small_font = pygame.font.SysFont("Arial", int(18 * 1.2))
    big_font = pygame.font.SysFont("Arial", 60)

# --- TEXTURE AND SOUND LOADING ---
BLOCK_SIZE = 32
TEXTURE_DIR = 'texture'
SOUND_DIR = 'sound'

def load_image(filename, alpha=False):
    """Loads an image from the texture directory."""
    path = os.path.join(TEXTURE_DIR, filename)
    try:
        image = pygame.image.load(path)
        if alpha:
            return image.convert_alpha()
        else:
            return image.convert()
    except pygame.error as e:
        print(f"Warning: Could not load image {filename}: {e}")
        # Return a placeholder surface
        surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        surface.fill((255, 0, 255)) # Bright pink to indicate a missing texture
        return surface

def load_sound(filename):
    """Loads a sound from the sound directory."""
    path = os.path.join(SOUND_DIR, filename)
    try:
        return pygame.mixer.Sound(path)
    except pygame.error as e:
        print(f"Warning: Could not load sound {filename}: {e}")
        return None

try:
    dirt_texture = pygame.transform.scale(load_image('dirt.png'), (BLOCK_SIZE, BLOCK_SIZE))
    stone_texture = pygame.transform.scale(load_image('stone.jpg'), (BLOCK_SIZE, BLOCK_SIZE))
    # Create grass block by adding a green top to the dirt texture, per user request.
    grass_block_texture = dirt_texture.copy()
    pygame.draw.rect(grass_block_texture, (34, 177, 76), (0, 0, BLOCK_SIZE, 8))
    tall_grass_texture = pygame.transform.scale(load_image('grass.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    wood_texture = pygame.transform.scale(load_image('wood.jpg'), (BLOCK_SIZE, BLOCK_SIZE))
    plank_texture = pygame.transform.scale(load_image('plank.jpg'), (BLOCK_SIZE, BLOCK_SIZE))
    leaf_texture = pygame.transform.scale(load_image('leaf.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    player_texture = load_image('player.png', True)
    inventory_slot_texture = pygame.transform.scale(load_image('inventory.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    health_texture = load_image('health.png', True)

    place_sound = load_sound('block.mp3')
    darkness_stinger_sound = load_sound('darkness2.mp3')
    if darkness_stinger_sound:
        darkness_stinger_sound.set_volume(1.0) # Louder, as requested
    damage_sound = load_sound('damage.mp3')

    chest_texture = pygame.transform.scale(load_image('chest.png'), (BLOCK_SIZE, BLOCK_SIZE))

    all_sounds = [place_sound, darkness_stinger_sound, damage_sound]
    stick_texture = pygame.transform.scale(load_image('stick.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    wooden_pickaxe_texture = pygame.transform.scale(load_image('wooden_pickaxe.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    wooden_sword_texture = pygame.transform.scale(load_image('wooden_sword.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    zombie_texture = load_image('zombie.jpg')
    zombie_texture.set_colorkey(WHITE)
    
    zombie_brute_texture = load_image('zombie_brute.jpg')
    zombie_brute_texture.set_colorkey(WHITE)
    
    # --- New Darkness Enemies ---
    crawler_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); crawler_texture.fill((100, 20, 20))
    goliath_texture = pygame.Surface((BLOCK_SIZE * 2, BLOCK_SIZE * 2)); goliath_texture.fill((60, 60, 70))

    # --- Boss Texture (Procedural) ---
    boss_texture = pygame.Surface((int(BLOCK_SIZE * 1.5), int(BLOCK_SIZE * 2.5)), pygame.SRCALPHA)
    boss_texture.fill((30, 30, 40)) # Dark, imposing color
    # Add a single, large, glowing red eye
    eye_pos = (boss_texture.get_width() // 2, boss_texture.get_height() // 4)
    pygame.draw.circle(boss_texture, (255, 20, 20), eye_pos, 8)
    pygame.draw.circle(boss_texture, (255, 100, 100), eye_pos, 4)

    # --- Boss Arrow Texture ---
    boss_arrow_texture = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.polygon(boss_arrow_texture, (255, 50, 50, 200), [(20, 0), (40, 40), (0, 40)])

    # --- Music ---
    # Note: darkness2.mp3 is loaded as a sound, not music, to allow it to play over darkness.mp3
    music_tracks = {
        'otherside': 'Otherside.mp3',
        'darkness': 'darkness.mp3'
    }
    # Load a default track to start with. The game loop will manage the correct one.
    pygame.mixer.music.load(os.path.join(SOUND_DIR, music_tracks['otherside']))
    pygame.mixer.music.set_volume(0.5) # Set volume to 50%
    pygame.mixer.music.play(-1) # -1 means loop forever

    # Chest open texture
    chest_open_texture = chest_texture.copy()
    highlight_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    highlight_surf.fill((255, 255, 0, 40)) # Yellow highlight
    chest_open_texture.blit(highlight_surf, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
    # --- New Ores and Materials ---
    coal_texture = pygame.transform.scale(load_image('coal.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    coal_ore_texture = pygame.transform.scale(load_image('coal_ore.png'), (BLOCK_SIZE, BLOCK_SIZE))
    raw_iron_texture = pygame.transform.scale(load_image('raw_iron.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    iron_ore_texture = pygame.transform.scale(load_image('iron_ore.webp'), (BLOCK_SIZE, BLOCK_SIZE))
    iron_ingot_texture = pygame.transform.scale(load_image('iron_ingot.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    steel_ingot_texture = pygame.transform.scale(load_image('steel_ingot.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    gold_ore_texture = pygame.transform.scale(load_image('gold_ore.jpg'), (BLOCK_SIZE, BLOCK_SIZE))
    diamond_texture = pygame.transform.scale(load_image('diamond.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    diamond_ore_texture = pygame.transform.scale(load_image('diamond_ore.webp'), (BLOCK_SIZE, BLOCK_SIZE))
    steel_bar_texture = pygame.transform.scale(load_image('steel_bar.webp', True), (BLOCK_SIZE, BLOCK_SIZE))

    # --- Sand and Glass ---
    sand_texture = pygame.transform.scale(load_image('sand.jpg'), (BLOCK_SIZE, BLOCK_SIZE))
    sus_sand_texture = pygame.transform.scale(load_image('sus_sand.webp'), (BLOCK_SIZE, BLOCK_SIZE))
    glass_texture = pygame.transform.scale(load_image('glass.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    sus_gold_texture = sand_texture.copy()
    gold_tint_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    gold_tint_surf.fill((255, 215, 0, 50)) # Gold tint
    sus_gold_texture.blit(gold_tint_surf, (0,0))

    # --- Water and Gold ---
    water_texture = pygame.transform.scale(load_image('water.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    gold_texture = pygame.transform.scale(load_image('gold.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    bucket_texture = pygame.transform.scale(load_image('bucket.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    water_bucket_texture = pygame.transform.scale(load_image('water_bucket.webp', True), (BLOCK_SIZE, BLOCK_SIZE))

    # --- New Crafting Items ---
    gold_chip_texture = pygame.transform.scale(load_image('gold_chip.jpg'), (BLOCK_SIZE, BLOCK_SIZE))
    gold_chip_texture.set_colorkey(WHITE)
    gun_texture = pygame.transform.scale(load_image('gun.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    # --- Furnace ---
    furnace_texture = pygame.transform.scale(load_image('furnace.png'), (BLOCK_SIZE, BLOCK_SIZE))
    furnace_on_texture = furnace_texture.copy()
    light_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    light_surf.fill((255, 150, 0, 50)) # Orange glow
    furnace_on_texture.blit(light_surf, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

    # --- Armor ---
    wood_armor_texture = pygame.transform.scale(load_image('wood_armor.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    stone_armor_texture = pygame.transform.scale(load_image('stone_armor.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    iron_armor_texture = pygame.transform.scale(load_image('iron_armor.jpg'), (BLOCK_SIZE, BLOCK_SIZE))
    iron_armor_texture.set_colorkey(WHITE)
    steel_armor_texture = pygame.transform.scale(load_image('steel_armor.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    diamond_armor_texture = pygame.transform.scale(load_image('diamond_armor.jpg'), (BLOCK_SIZE, BLOCK_SIZE))
    diamond_armor_texture.set_colorkey(WHITE)
    # --- New Tools ---
    iron_pickaxe_texture = pygame.transform.scale(load_image('iron_pickaxe.jpg'), (BLOCK_SIZE, BLOCK_SIZE))
    iron_pickaxe_texture.set_colorkey(WHITE)
    iron_sword_texture = pygame.transform.scale(load_image('iron_sword.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    steel_pickaxe_texture = pygame.transform.scale(load_image('steel_pickaxe.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    steel_sword_texture = pygame.transform.scale(load_image('steel_sword.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    diamond_pickaxe_texture = pygame.transform.scale(load_image('diamond_pickaxe.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    diamond_staff_texture = pygame.transform.rotate(pygame.transform.scale(load_image('diamond_staff.png', True), (BLOCK_SIZE, BLOCK_SIZE)), -90)
    # NOTE: Using .convert_alpha() is the standard way to load images with transparency (like PNGs).
    # If a tool still has a white background, it means the source image file itself has a white
    # background instead of a proper transparent one and should be edited. For JPGs, use .convert() and .set_colorkey().
    string_texture = pygame.transform.scale(load_image('string.png', True), (BLOCK_SIZE, BLOCK_SIZE))
    sling_texture = pygame.transform.rotate(pygame.transform.scale(load_image('slingshot.png', True), (BLOCK_SIZE, BLOCK_SIZE)), -45)
    # Load the full door texture, assuming it's for a 2-block high door
    full_door_texture = pygame.transform.scale(load_image('wooden_door.png', True), (BLOCK_SIZE, BLOCK_SIZE * 2))

    # The item texture is a scaled-down version of the full door
    wooden_door_texture = pygame.transform.scale(full_door_texture, (BLOCK_SIZE, BLOCK_SIZE))

    # The closed door textures are the top and bottom halves of the full image
    wooden_door_top_closed_texture = full_door_texture.subsurface((0, 0, BLOCK_SIZE, BLOCK_SIZE))
    wooden_door_bottom_closed_texture = full_door_texture.subsurface((0, BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

    # Open door block texture
    # This is generated procedurally to look like a thin slab, using a color from the door texture
    door_color = full_door_texture.get_at((BLOCK_SIZE // 2, BLOCK_SIZE // 2))
    open_door_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE * 2), pygame.SRCALPHA)
    open_door_surf.fill(door_color, (0, 0, 4, BLOCK_SIZE * 2)) # 4px wide open door on the left

    wooden_door_top_open_texture = open_door_surf.subsurface((0, 0, BLOCK_SIZE, BLOCK_SIZE))
    wooden_door_bottom_open_texture = open_door_surf.subsurface((0, BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

    # Create stone tool textures by tinting wooden ones
    # To correctly tint a texture while preserving its transparency, we create a copy
    # (which will have per-pixel alpha since the source was loaded with .convert_alpha())
    # and then blit a colored surface onto it using a multiplicative blend mode.
    gray_tint_surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), flags=pygame.SRCALPHA)
    gray_tint_surface.fill((180, 180, 180)) # A light-ish gray

    # Tint stone pickaxe
    stone_pickaxe_texture = wooden_pickaxe_texture.copy()
    stone_pickaxe_texture.blit(gray_tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Tint stone sword
    stone_sword_texture = wooden_sword_texture.copy()
    stone_sword_texture.blit(gray_tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Procedurally create graveyard texture
    graveyard_texture = stone_texture.copy()
    cross_color = (139, 90, 43) # wood color
    # vertical part
    pygame.draw.rect(graveyard_texture, cross_color, (BLOCK_SIZE // 2 - 2, 4, 4, BLOCK_SIZE - 8))
    # horizontal part
    pygame.draw.rect(graveyard_texture, cross_color, (4, 10, BLOCK_SIZE - 8, 4))

    # Bed and Shipping Bin
    bed_texture = pygame.transform.scale(load_image('bed.webp', True), (BLOCK_SIZE * 2, BLOCK_SIZE))
    shipping_bin_texture = pygame.transform.scale(load_image('chest.png'), (BLOCK_SIZE, BLOCK_SIZE))
    gray_tint_surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), flags=pygame.SRCALPHA)
    gray_tint_surface.fill((100, 100, 110))
    shipping_bin_texture.blit(gray_tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # New tech items
    rubber_texture = pygame.transform.scale(load_image('rubber.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    silicon_texture = pygame.transform.scale(load_image('silicon.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    wire_texture = pygame.transform.scale(load_image('wire.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    rubber_stick_texture = pygame.transform.scale(load_image('rubber_stick.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    silicon_chip_texture = pygame.transform.scale(load_image('silicon_chip.webp', True), (BLOCK_SIZE, BLOCK_SIZE))
    power_drill_texture = pygame.transform.scale(load_image('drill.png', True), (BLOCK_SIZE, BLOCK_SIZE))

    if place_sound:
        place_sound.set_volume(1.0) # Set volume to 100% (max volume)

except pygame.error as e:
    print(f"Warning: Could not load assets ({e}). Using fallbacks.")
    dirt_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); dirt_texture.fill((139, 69, 19))
    grass_block_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); grass_block_texture.fill((139, 69, 19))
    pygame.draw.rect(grass_block_texture, (34, 177, 76), (0, 0, BLOCK_SIZE, 8)) # Green top layer
    tall_grass_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    pygame.draw.line(tall_grass_texture, (34, 177, 76), (10, 30), (10, 10), 2)
    pygame.draw.line(tall_grass_texture, (34, 177, 76), (20, 30), (22, 8), 2)

    stone_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); stone_texture.fill((128, 128, 128))
    wood_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); wood_texture.fill((160, 82, 45))
    plank_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); plank_texture.fill((222, 184, 135))
    # Use SRCALPHA to allow for transparency in the fallback color
    leaf_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); leaf_texture.fill((34, 139, 34, 180))
    player_texture = None
    health_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); health_texture.fill((255, 0, 0, 200))
    inventory_slot_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); inventory_slot_texture.fill((80, 80, 80))
    chest_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); chest_texture.fill((139, 90, 43))
    chest_open_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); chest_open_texture.fill((160, 110, 65))
    stick_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); pygame.draw.rect(stick_texture, (139, 69, 19), (14, 4, 4, 24))
    wooden_pickaxe_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); wooden_pickaxe_texture.fill((100, 100, 200))
    wooden_sword_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); wooden_sword_texture.fill((200, 200, 100))
    # Fallbacks for stone tools
    stone_pickaxe_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); stone_pickaxe_texture.fill((100, 100, 120))
    stone_sword_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); stone_sword_texture.fill((150, 150, 150))
    graveyard_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); graveyard_texture.fill((100,100,100))
    # Fallbacks for bed and shipping bin
    bed_texture = pygame.Surface((BLOCK_SIZE * 2, BLOCK_SIZE)); bed_texture.fill((200, 50, 50))
    shipping_bin_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); shipping_bin_texture.fill((80, 80, 90))

    # Fallbacks for doors
    wooden_door_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); wooden_door_texture.fill((139, 90, 43))
    wooden_door_top_closed_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); wooden_door_top_closed_texture.fill((139, 90, 43))
    wooden_door_bottom_closed_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); wooden_door_bottom_closed_texture.fill((139, 90, 43))
    wooden_door_top_open_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); wooden_door_top_open_texture.fill((139, 90, 43, 255), (0, 0, 4, BLOCK_SIZE))
    wooden_door_bottom_open_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); wooden_door_bottom_open_texture.fill((139, 90, 43, 255), (0, 0, 4, BLOCK_SIZE))
    zombie_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE * 2), pygame.SRCALPHA); zombie_texture.fill((50, 150, 50))
    zombie_brute_texture = pygame.Surface((int(BLOCK_SIZE * 1.2), int(BLOCK_SIZE * 2.2)), pygame.SRCALPHA); zombie_brute_texture.fill((30, 100, 30))
    # Fallbacks for darkness enemies
    crawler_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); crawler_texture.fill((100, 20, 20))
    boss_texture = pygame.Surface((int(BLOCK_SIZE * 1.5), int(BLOCK_SIZE * 2.5)), pygame.SRCALPHA); boss_texture.fill((30, 30, 40))
    goliath_texture = pygame.Surface((BLOCK_SIZE * 2, BLOCK_SIZE * 2)); goliath_texture.fill((60, 60, 70))

    # Fallback for boss arrow
    boss_arrow_texture = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.polygon(boss_arrow_texture, (255, 50, 50, 200), [(20, 0), (40, 40), (0, 40)])


    # Fallbacks for new items
    coal_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); coal_texture.fill((50, 50, 50))
    coal_ore_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); coal_ore_texture.fill((80, 80, 80))
    raw_iron_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); raw_iron_texture.fill((210, 180, 140))
    iron_ore_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); iron_ore_texture.fill((180, 140, 100))
    iron_ingot_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); iron_ingot_texture.fill((200, 200, 200))
    gold_ore_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); gold_ore_texture.fill((180, 160, 50))
    steel_ingot_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); steel_ingot_texture.fill((100, 100, 110))    
    steel_bar_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); steel_bar_texture.fill((90, 90, 100))
    furnace_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); furnace_texture.fill((100, 100, 100))
    furnace_on_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); furnace_on_texture.fill((120, 120, 100))
    iron_pickaxe_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); iron_pickaxe_texture.fill((200, 200, 220))
    iron_sword_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); iron_sword_texture.fill((220, 220, 200))
    steel_pickaxe_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); steel_pickaxe_texture.fill((120, 120, 140))
    steel_sword_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); steel_sword_texture.fill((140, 140, 120))
    diamond_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); diamond_texture.fill((0, 255, 255))
    diamond_ore_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); diamond_ore_texture.fill((150, 150, 160))
    diamond_pickaxe_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); diamond_pickaxe_texture.fill((180, 255, 255))
    diamond_staff_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); diamond_staff_texture.fill((200, 255, 255))
    # Fallbacks for sling and string
    string_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    pygame.draw.lines(string_texture, (220, 220, 220), False, [(4, 5), (10, 12), (16, 15), (22, 23), (28, 27)], 2)
    sling_texture_unrotated = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    pygame.draw.line(sling_texture_unrotated, (139, 69, 19), (16, 28), (16, 14), 4) # Handle
    pygame.draw.line(sling_texture_unrotated, (139, 69, 19), (16, 16), (8, 8), 4)  # Left fork
    pygame.draw.line(sling_texture_unrotated, (139, 69, 19), (16, 16), (24, 8), 4) # Right fork
    pygame.draw.line(sling_texture_unrotated, (220, 220, 220), (6, 8), (26, 8), 2) # String
    sling_texture = pygame.transform.rotate(sling_texture_unrotated, -45)
    # Fallbacks for sand and glass
    sand_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); sand_texture.fill((244, 226, 198))
    sus_sand_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); sus_sand_texture.fill((230, 210, 180))
    sus_gold_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)); sus_gold_texture.fill((240, 220, 150))
    # Fallbacks for water and gold
    water_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); water_texture.fill((20, 100, 220, 150))
    gold_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); gold_texture.fill((255, 215, 0))
    bucket_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); bucket_texture.fill((192, 192, 192))
    water_bucket_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); water_bucket_texture.fill((192, 192, 192))
    pygame.draw.rect(water_bucket_texture, (20, 100, 220, 200), (8, 8, 16, 16))
    glass_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); glass_texture.fill((220, 220, 255, 100))
    # Fallbacks for armor
    wood_armor_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); wood_armor_texture.fill((160, 82, 45))
    stone_armor_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); stone_armor_texture.fill((140, 140, 140))
    iron_armor_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); iron_armor_texture.fill((210, 210, 210))
    steel_armor_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); steel_armor_texture.fill((110, 110, 120))
    diamond_armor_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); diamond_armor_texture.fill((180, 255, 255))

    # Fallbacks for new items
    gold_chip_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); gold_chip_texture.fill((255, 223, 0))
    gun_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); gun_texture.fill((80, 80, 80))
    # Fallbacks for tech items
    rubber_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); rubber_texture.fill((245, 245, 220))
    silicon_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); silicon_texture.fill((192, 192, 192))
    wire_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); pygame.draw.line(wire_texture, (255,215,0), (0,16), (32,16), 2)
    rubber_stick_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); rubber_stick_texture.fill((100,100,100))
    silicon_chip_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); silicon_chip_texture.fill((0,0,100))
    power_drill_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); power_drill_texture.fill((255,255,0))
    fiber_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); fiber_texture.fill((188, 214, 138))

    # No specific fallback for music, it will just be silent if files are missing.
    music_tracks = {}
    place_sound = None
    darkness_stinger_sound = None
    damage_sound = None
    all_sounds = []

try:
    fiber_texture = pygame.transform.scale(pygame.image.load('fiber.webp').convert_alpha(), (BLOCK_SIZE, BLOCK_SIZE))
except (pygame.error, FileNotFoundError):
    fiber_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA); fiber_texture.fill((188, 214, 138))


textures = {
    "dirt": dirt_texture,
    "stone": stone_texture,
    "grass_block": grass_block_texture,
    "tall_grass": tall_grass_texture,
    "wood": wood_texture,
    "plank": plank_texture,
    "leaf": leaf_texture,
    "chest_open": chest_open_texture,
    "chest": chest_texture,
    "string": string_texture,
    "sling": sling_texture,
    "stick": stick_texture,
    "wooden_pickaxe": wooden_pickaxe_texture,
    "wooden_sword": wooden_sword_texture,
    "stone_pickaxe": stone_pickaxe_texture,
    "stone_sword": stone_sword_texture,
    "graveyard": graveyard_texture,
    "wooden_door": wooden_door_texture,
    "wooden_door_top_closed": wooden_door_top_closed_texture,
    "wooden_door_bottom_closed": wooden_door_bottom_closed_texture,
    "wooden_door_top_open": wooden_door_top_open_texture,
    "wooden_door_bottom_open": wooden_door_bottom_open_texture,
    "zombie": zombie_texture,
    "zombie_brute": zombie_brute_texture,
    "crawler": crawler_texture,
    "goliath": goliath_texture,
    "boss": boss_texture,
    "boss_arrow": boss_arrow_texture,
    "coal": coal_texture,
    "coal_ore": coal_ore_texture,
    "raw_iron": raw_iron_texture,
    "gold_ore": gold_ore_texture,
    "iron_ore": iron_ore_texture,
    "iron_ingot": iron_ingot_texture,
    "steel_ingot": steel_ingot_texture,
    "furnace": furnace_texture,
    "furnace_on": furnace_on_texture,
    "iron_pickaxe": iron_pickaxe_texture,
    "iron_sword": iron_sword_texture,
    "steel_pickaxe": steel_pickaxe_texture,
    "steel_sword": steel_sword_texture,
    "diamond": diamond_texture,
    "diamond_ore": diamond_ore_texture,
    "diamond_pickaxe": diamond_pickaxe_texture,
    "diamond_staff": diamond_staff_texture,
    "sand": sand_texture,
    "sus_sand": sus_sand_texture,
    "sus_gold": sus_gold_texture,
    "glass": glass_texture,
    "steel_bar": steel_bar_texture,
    "water": water_texture,
    "gold": gold_texture,
    "bucket": bucket_texture,
    "water_bucket": water_bucket_texture,
    "gold_chip": gold_chip_texture,
    "gun": gun_texture,
    "wood_armor": wood_armor_texture,
    "stone_armor": stone_armor_texture,
    "iron_armor": iron_armor_texture,
    "steel_armor": steel_armor_texture,
    "diamond_armor": diamond_armor_texture,
    "bed": bed_texture,
    "shipping_bin": shipping_bin_texture,
    "fiber": fiber_texture,
    "rubber": rubber_texture,
    "silicon": silicon_texture,
    "wire": wire_texture,
    "rubber_stick": rubber_stick_texture,
    "silicon_chip": silicon_chip_texture,
    "power_drill": power_drill_texture,
}

avg_colors = {}
for name, texture in textures.items():
    try:
        avg_colors[name] = pygame.transform.average_color(texture)
    except (pygame.error, ValueError):
        if 'gold' in name: avg_colors[name] = (255, 215, 0)
        # Fallback for surfaces that can't be averaged or are fully transparent.
        if 'stone' in name or 'ore' in name or 'furnace' in name or 'stone_armor' in name or 'goliath' in name: avg_colors[name] = (128, 128, 128)
        elif 'dirt' in name or 'wood' in name or 'plank' in name or 'chest' in name: avg_colors[name] = (139, 69, 19)
        elif 'grass_block' in name: avg_colors[name].fill((80, 120, 50))
        elif 'tall_grass' in name or 'leaf' in name: avg_colors[name] = (34, 139, 34)
        elif 'sand' in name: avg_colors[name] = (244, 226, 198)
        elif 'water' in name: avg_colors[name] = (20, 100, 220)
        elif 'graveyard' in name: avg_colors[name] = (110, 110, 110)
        else: avg_colors[name] = (100, 100, 100) # Generic gray


def set_global_volume(volume_level):
    """Sets the volume for music and all sound effects."""
    pygame.mixer.music.set_volume(volume_level)
    for sound in all_sounds:
        if sound:
            sound.set_volume(volume_level)

def play_music(track_name):
    """Stops current music and plays a new track if it exists."""
    if track_name in music_tracks:
        # Check if the correct music is already playing to avoid restarting it
        # This is tricky without a way to get the current track name from pygame.
        # For simplicity, we'll just stop and restart.
        pygame.mixer.music.stop()
        pygame.mixer.music.load(os.path.join(SOUND_DIR, music_tracks[track_name]))
        pygame.mixer.music.play(-1)