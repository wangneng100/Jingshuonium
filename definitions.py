# --- GAMEPLAY CONSTANTS ---
DAY_NIGHT_DURATION = 600 # 10 minutes for a full cycle

# --- CRAFTING RECIPES ---
CRAFTING_RECIPES = [
    { # 1 Wood -> 4 Planks
        "shape": [["wood"]],
        "result": {"type": "plank", "count": 4}
    },
    { # 3 Leaves -> 1 String
        "shape": [["leaf"], ["leaf"], ["leaf"]],
        "result": {"type": "string", "count": 1}
    },
    { # 3 Fiber -> 1 String
        "shape": [["fiber"], ["fiber"], ["fiber"]],
        "result": {"type": "string", "count": 1}
    },
    { # 2 Planks -> 4 Sticks
        "shape": [["plank"], ["plank"]],
        "result": {"type": "stick", "count": 4}
    },
    { # 8 Planks -> 1 Chest
        "shape": [["plank", "plank", "plank"], ["plank", None, "plank"], ["plank", "plank", "plank"]],
        "result": {"type": "chest", "count": 1}
    },
    { # Wooden Pickaxe
        "shape": [["plank", "plank", "plank"], [None, "stick", None], [None, "stick", None]],
        "result": {"type": "wooden_pickaxe", "count": 1}
    },
    { # Wooden Sword
        "shape": [[None, "plank", None], [None, "plank", None], [None, "stick", None]],
        "result": {"type": "wooden_sword", "count": 1}
    },
    { # Wooden Hoe
        "shape": [["plank", "plank"], ["stick", None], ["stick", None]],
        "result": {"type": "wooden_hoe", "count": 1}
    },
    { # Stone Pickaxe
        "shape": [["stone", "stone", "stone"], [None, "stick", None], [None, "stick", None]],
        "result": {"type": "stone_pickaxe", "count": 1}
    },
    { # Stone Sword
        "shape": [[None, "stone", None], [None, "stone", None], [None, "stick", None]],
        "result": {"type": "stone_sword", "count": 1}
    },
    { # Wooden Door
        "shape": [["plank", "plank"], ["plank", "plank"], ["plank", "plank"]],
        "result": {"type": "wooden_door", "count": 3}
    },
    { # Furnace
        "shape": [["stone", "stone", "stone"], ["stone", None, "stone"], ["stone", "stone", "stone"]],
        "result": {"type": "furnace", "count": 1}
    },
    { # Bucket
        "shape": [
            ["steel_ingot", None, "steel_ingot"],
            [None, "steel_ingot", None]
        ],
        "result": {"type": "bucket", "count": 1}
    },
    { # Iron Pickaxe
        "shape": [["iron_ingot", "iron_ingot", "iron_ingot"], [None, "stick", None], [None, "stick", None]],
        "result": {"type": "iron_pickaxe", "count": 1}
    },
    { # Iron Sword
        "shape": [[None, "iron_ingot", None], [None, "iron_ingot", None], [None, "stick", None]],
        "result": {"type": "iron_sword", "count": 1}
    },
    { # Steel Pickaxe
        "shape": [["steel_ingot", "steel_ingot", "steel_ingot"], [None, "stick", None], [None, "stick", None]],
        "result": {"type": "steel_pickaxe", "count": 1}
    },
    { # Steel Sword
        "shape": [[None, "steel_ingot", None], [None, "steel_ingot", None], [None, "stick", None]],
        "result": {"type": "steel_sword", "count": 1}
    },
    { # 9 Coal -> 1 Diamond
        "shape": [["coal", "coal", "coal"], ["coal", "coal", "coal"], ["coal", "coal", "coal"]],
        "result": {"type": "diamond", "count": 1}
    },
    { # Steel Bar
        "shape": [["steel_ingot"], ["steel_ingot"]],
        "result": {"type": "steel_bar", "count": 1}
    },
    { # Diamond Pickaxe
        "shape": [["diamond", "diamond", "diamond"], [None, "steel_bar", None], [None, "steel_bar", None]],
        "result": {"type": "diamond_pickaxe", "count": 1}
    },
    { # Diamond Staff
        "shape": [[None, None, "diamond"], [None, "steel_bar", None], ["diamond", None, None]],
        "result": {"type": "diamond_staff", "count": 1}
    },
    { # Sling
        "shape": [["string", "string", "string"], ["stick", None, "stick"], [None, "stick", None]],
        "result": {"type": "sling", "count": 1}
    },
    { # Gold Chip
        "shape": [["steel_ingot", "steel_ingot", "steel_ingot"], ["steel_ingot", "gold", "steel_ingot"], ["steel_ingot", "steel_ingot", "steel_ingot"]],
        "result": {"type": "gold_chip", "count": 1}
    },
    { # Gun
        "shape": [
            ["steel_ingot", "steel_ingot", "steel_ingot"],
            ["steel_bar", "gold_chip", None],
            [None, None, None]
        ],
        "result": {"type": "gun", "count": 1}
    },
    { # Wood Armor
        "shape": [["plank", "plank", "plank"], ["plank", "plank", "plank"], ["plank", "plank", "plank"]],
        "result": {"type": "wood_armor", "count": 1}
    },
    { # Stone Armor
        "shape": [["stone", "stone", "stone"], ["stone", "stone", "stone"], ["stone", "stone", "stone"]],
        "result": {"type": "stone_armor", "count": 1}
    },
    { # Iron Armor
        "shape": [["iron_ingot", "iron_ingot", "iron_ingot"], ["iron_ingot", "iron_ingot", "iron_ingot"], ["iron_ingot", "iron_ingot", "iron_ingot"]],
        "result": {"type": "iron_armor", "count": 1}
    },
    { # Steel Armor
        "shape": [["steel_ingot", "steel_ingot", "steel_ingot"], ["steel_ingot", "steel_ingot", "steel_ingot"], ["steel_ingot", "steel_ingot", "steel_ingot"]],
        "result": {"type": "steel_armor", "count": 1}
    },
    { # Diamond Armor
        "shape": [["diamond", "diamond", "diamond"], ["diamond", "diamond", "diamond"], ["diamond", "diamond", "diamond"]],
        "result": {"type": "diamond_armor", "count": 1}
    },
    { # Wire
        "shape": [
            ["rubber", "gold", "rubber"],
            ["rubber", "gold", "rubber"],
            ["rubber", "gold", "rubber"]
        ],
        "result": {"type": "wire", "count": 6}
    },
    { # Rubber Stick
        "shape": [
            ["rubber"],
            ["steel_bar"]
        ],
        "result": {"type": "rubber_stick", "count": 1}
    },
    { # Silicon Chip
        "shape": [
            [None, "silicon", None],
            ["silicon", "gold_chip", "silicon"],
            [None, "silicon", None]
        ],
        "result": {"type": "silicon_chip", "count": 1}
    },
    { # Power Drill
        "shape": [
            ["steel_ingot", "gold_chip", "steel_ingot"],
            ["steel_ingot", "silicon_chip", "steel_ingot"],
            [None, "diamond", None]
        ],
        "result": {"type": "power_drill", "count": 1}
    },
]

# Hardness values for different block types (in seconds)
BLOCK_HARDNESS = {
    "bed": float('inf'),
    "shipping_bin": float('inf'),
    "dirt": 1.5,
    "grass_block": 1.5,
    "farmland": 1.5,
    "tall_grass": 0.1, "stone": 4.0, "wood": 3.0, "plank": 3.0, "graveyard": 4.0,
    "leaf": 0.2,
    "chest": 3.0,
    "wooden_door_top_closed": 3.0,
    "wooden_door_bottom_closed": 3.0,
    "wooden_door_top_open": 3.0,
    "wooden_door_bottom_open": 3.0,
    "furnace": 4.0,
    "coal_ore": 3.5,
    "iron_ore": 5.0,
    "gold_ore": 6.0,
    "diamond_ore": 7.0,
    "sand": 0.5,
    "sus_sand": 0.5,
    "sus_gold": 0.5,
    "glass": 0.3,
    "water": 99999, # Effectively unbreakable
    "default": 2.0 # Fallback for any other block type
}

# --- ENEMY DEFINITIONS ---
ENEMY_STATS = {
    'zombie':       {'health': 200, 'damage': 1.0, 'speed_mult': 0.5, 'aggro': 10, 'xp': 5},
    'zombie_brute': {'health': 600, 'damage': 2.5, 'speed_mult': 0.4, 'aggro': 12, 'xp': 20},
    'crawler':      {'health': 96, 'damage': 1.5, 'speed_mult': 0.8, 'aggro': 15, 'xp': 10},
    'goliath':      {'health': 1000, 'damage': 4.0, 'speed_mult': 0.2, 'aggro': 18, 'xp': 50},
    'boss':         {'health': 8000, 'damage': 5.0, 'speed_mult': 0.3, 'aggro': 50, 'xp': 500}
}


# --- TOOL DEFINITIONS ---
TOOL_TIERS = {
    "wooden_pickaxe": 1,
    "stone_pickaxe": 2,
    "iron_pickaxe": 3,
    "steel_pickaxe": 4,
    "diamond_pickaxe": 5,
    "default": 0 # Hand
}
BLOCK_MINING_LEVEL = {
    "stone": 1,
    "coal_ore": 1,
    "iron_ore": 2,
    "gold_ore": 3, # Requires at least an iron pickaxe
    "furnace": 1,
    "diamond_ore": 4, # Requires a steel pickaxe
}

# Defines which block types a tool is effective against
TOOL_EFFECTIVENESS = {
    "wooden_pickaxe": ["stone", "coal_ore", "furnace", "wood", "plank", "chest"],
    "stone_pickaxe": ["stone", "coal_ore", "furnace", "iron_ore", "wood", "plank", "chest"],
    "iron_pickaxe": ["stone", "coal_ore", "furnace", "iron_ore", "gold_ore", "wood", "plank", "chest"],
    "steel_pickaxe": ["stone", "coal_ore", "furnace", "iron_ore", "gold_ore", "diamond_ore", "wood", "plank", "chest"],
    "diamond_pickaxe": ["stone", "coal_ore", "furnace", "iron_ore", "gold_ore", "diamond_ore", "wood", "plank", "chest"],
    "wooden_sword": ["leaf", "tall_grass"],
    "stone_sword": ["leaf", "tall_grass"],
    "iron_sword": ["leaf", "tall_grass"],
    "steel_sword": ["leaf", "tall_grass"],
}
# How much faster a correct tool breaks a block
TOOL_SPEEDS = {
    "wooden_pickaxe": 2.0,
    "stone_pickaxe": 3.0,
    "iron_pickaxe": 4.5,
    "steel_pickaxe": 6.0,
    "diamond_pickaxe": 12.0,
    "wooden_sword": 10.0,
    "stone_sword": 10.0,
    "iron_sword": 10.0,
    "steel_sword": 10.0,
}

# Defines base damage for different weapons. This is ready for when enemies are added.
WEAPON_DAMAGE = {
    "wooden_sword": 5.0,
    "stone_sword": 7.0,
    "iron_sword": 9.0,
    "steel_sword": 13.0,
    "diamond_staff": 20.0,
    "sling": 3.75,
    "gun": 12.5,
}

# --- ARMOR ---
ARMOR_VALUES = {
    # Damage reduction percentage (0.0 to 1.0)
    "wood_armor": 0.10,    # Takes 90% damage
    "stone_armor": 0.15,   # Takes 85% damage
    "iron_armor": 0.25,    # Takes 75% damage
    "steel_armor": 0.50,   # Takes 50% damage
    "diamond_armor": 0.70,   # Takes 30% damage
}

# --- SMELTING ---
SMELTING_RECIPES = {
    "raw_iron": {"result": "iron_ingot", "time": 5.0},
    "iron_ingot": {"result": "steel_ingot", "time": 8.0},
    "gold_ore": {"result": "gold", "time": 6.0},
    "sand": {"result": "glass", "time": 3.0},
    "wood": {"result": "rubber", "time": 4.0},
    "stone": {"result": "silicon", "time": 4.0},
}
FUEL_VALUES = {
    "coal": 10.0, # seconds of burn time
}

# Defines custom scaling for specific non-block items
ITEM_SCALES = {
    'bed': 1.0,
    'shipping_bin': 1.0,
    'wooden_pickaxe': 1.3,
    'wooden_sword': 1.1,
    'wooden_hoe': 1.3,
    'stick': 1.2,
    'string': 1.0,
    'sling': 1.1,
    'stone_pickaxe': 1.3,
    'stone_sword': 1.1,
    'wooden_door': 1.0,
    'fiber': 1.0,
    'coal': 1.0,
    'raw_iron': 1.0,
    'iron_ingot': 1.0,
    'steel_ingot': 1.0,
    'iron_pickaxe': 1.3,
    'iron_sword': 1.1,
    'steel_pickaxe': 1.3,
    'steel_sword': 1.1,
    'steel_bar': 1.0,
    'diamond': 1.0,
    'diamond_pickaxe': 1.3,
    'diamond_staff': 1.1,
    'gold': 1.0,
    'gold_chip': 1.0,
    'gold_ore': 1.0,
    'gun': 1.3,
    'bucket': 1.0,
    'water_bucket': 1.0,
    'wood_armor': 1.0,
    'stone_armor': 1.0,
    'iron_armor': 1.0,
    'steel_armor': 1.0,
    'diamond_armor': 1.0,
    'rubber': 1.0,
    'silicon': 1.0,
    'wire': 1.0,
    'rubber_stick': 1.0,
    'silicon_chip': 1.0,
    'power_drill': 1.0,
}

# --- UI SCALING ---
HOTBAR_SCALE = 1.2

# --- ECONOMY ---
ITEM_PRICES = {
    "dirt": 1, "stone": 2, "grass_block": 1, "wood": 5, "plank": 2, "leaf": 1,
    "coal": 10, "raw_iron": 15, "iron_ingot": 30, "steel_ingot": 60,
    "gold": 100, "diamond": 500, "sand": 1, "glass": 3,
    "fiber": 2, "string": 5, "stick": 1, "rubber": 20, "silicon": 10, "wire": 50,
    "default": 1 # Default price for unlisted items
}