# --- WINDOW SETTINGS ---
WINDOW_TITLE = 'UrsinaCraft'
WINDOW_FULLSCREEN = False
WINDOW_SIZE = (1536, 864)
WINDOW_POSITION = (192, 108)

# --- TERRAIN SETTINGS ---
# The world will be a grid of width x depth chunks.
TERRAIN_WIDTH = 4
TERRAIN_DEPTH = 4

# --- PHYSICS SETTINGS ---
GRAVITY = 9.8

# --- PLAYER SETTINGS ---
# Movement
WALK_SPEED = 5
SPRINT_SPEED = 8
CROUCH_SPEED = 2
JUMP_HEIGHT = 64
MAX_JUMPS = 2
# Physics
GRAVITY_MULTIPLIER = 1.5
FRICTION = 6.0 # Higher value = more responsive, less sliding
AIR_FRICTION = 2.0 # How much friction is applied in the air.
STEP_HEIGHT = 0.4 # How high the player can step up automatically
JUMP_ROTATION_SPEED = 360 # degrees per second
# Camera
MOUSE_SENSITIVITY = 40 # A single value for both X and Y axes
FOV = 90
# Dimensions
STAND_HEIGHT = 1
CROUCH_HEIGHT = 0.5
# Gameplay
FALL_DAMAGE_THRESHOLD = 9999
HELD_ITEM_SIZE = 0.75 # As a factor of BLOCK_SIZE
HELD_ITEM_ROTATION_SPEED = 2.0 # Multiplier for spin speed
FALL_DAMAGE_MULTIPLIER = 1.2 # The base for exponential fall damage calculation.