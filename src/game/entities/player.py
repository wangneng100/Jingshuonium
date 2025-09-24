import pygame
import math
import random
from ..core import config
from ..core import assets
from ..core import definitions
from ..ui.inventory import PlayerInventory
# Placeholder imports for now, will be updated during full refactor
# from entities.particles import Particle, create_hit_particles, create_explosion_particles

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
        # Only update facing if it would actually change to prevent micro-adjustments
        is_tool_held = selected_item_type and ('sword' in selected_item_type or 'pickaxe' in selected_item_type or 'staff' in selected_item_type or 'sling' in selected_item_type or 'gun' in selected_item_type)
        if is_tool_held and world_mouse_pos:
            # Face based on world coordinates of mouse vs player
            new_facing = 1 if world_mouse_pos.x > self.rect.centerx else -1
            if new_facing != self.facing:
                self.facing = new_facing
        else:
            # Only update facing if keys are pressed and would change the direction
            if keys[pygame.K_d] and self.facing != 1: 
                self.facing = 1
            elif keys[pygame.K_a] and self.facing != -1: 
                self.facing = -1

        # 添加蹲下状态稳定机制，防止频繁切换
        should_crouch = keys[pygame.K_s]
        
        # 添加蹲下状态切换的冷却时间
        if not hasattr(self, '_crouch_switch_cooldown'):
            self._crouch_switch_cooldown = 0
        
        if self._crouch_switch_cooldown > 0:
            self._crouch_switch_cooldown -= dt
        
        # 只有在冷却时间结束时才允许状态切换
        if self._crouch_switch_cooldown <= 0:
            if should_crouch and not self.is_crouching:
                self.crouch()
                self._crouch_switch_cooldown = 0.1  # 100ms冷却时间
            elif not should_crouch and self.is_crouching:
                self.stand(nearby_blocks) # Pass nearby blocks here
                self._crouch_switch_cooldown = 0.1  # 100ms冷却时间

        # Handle jump rotation animation - smooth rotation throughout jump
        is_pickaxe_held = selected_item_type and 'pickaxe' in selected_item_type
        
        # 首先强制重置地面时的旋转角度
        if self.grounded:
            self.rotation_angle = 0.0
        
        # 只有在空中且不持有镐子工具时才旋转
        if not self.grounded and not (self.is_tool_active and is_pickaxe_held):
            # Continue rotating throughout the entire jump for smooth animation
            # Use a scaled rotation speed based on velocity for natural feel
            velocity_factor = max(0.3, min(1.0, abs(self.vel.y) / 200))  # Scale from 0.3 to 1.0
            rotation_speed = config.JUMP_ROTATION_SPEED * velocity_factor
            self.rotation_angle += rotation_speed * dt

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
        
        # 强化防抖动机制 - 更严格的阈值
        if self.grounded:
            # 在地面上时，使用更大的阈值并强制静止
            if abs(self.vel.x) < 0.5:
                self.vel.x = 0
            if abs(self.vel.y) < 0.5:
                self.vel.y = 0
            # 如果没有按键输入且速度很小，强制静止
            if target_vel_x == 0 and abs(self.vel.x) < 1.0:
                self.vel.x = 0
        else:
            # 空中时使用较小的阈值
            if abs(self.vel.x) < 0.1:
                self.vel.x = 0
            
        # --- Collision Detection ---
        # 在完全静止状态下，锁定角色尺寸避免抖动
        is_completely_still = (abs(self.vel.x) < 0.1 and abs(self.vel.y) < 0.1 and 
                              self.grounded and target_vel_x == 0)
        
        # Only update rect dimensions if they actually changed and player is not completely still
        if not is_completely_still and (self.rect.width != self.width or self.rect.height != self.height):
            self.rect.width = self.width
            self.rect.height = self.height

        # X-axis collision
        self.pos.x += self.vel.x * dt
        # 确保位置精确同步 - 使用四舍五入而不是截断
        new_x = round(self.pos.x)
        new_y = round(self.pos.y)
        
        # 只有在位置真正变化时才更新rect
        if self.rect.x != new_x or self.rect.y != new_y:
            self.rect.x = new_x
            self.rect.y = new_y

        for block in effectively_solid_blocks:
            if block.rect.colliderect(self.rect):
                if self.vel.x > 0: # Moving right
                    self.rect.right = block.rect.left
                elif self.vel.x < 0: # Moving left
                    self.rect.left = block.rect.right
                # 碰撞后强制精确同步，防止漂移
                self.pos.x = float(self.rect.x)
                self.vel.x = 0
                # 碰撞时立即停止所有微小运动
                if abs(self.vel.y) < 1.0 and self.grounded:
                    self.vel.y = 0

        # Y-axis collision
        self.pos.y += self.vel.y * dt
        # Y轴也使用相同的精确同步机制
        new_y = round(self.pos.y)
        if self.rect.y != new_y:
            self.rect.y = new_y
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
                # 碰撞后强制精确同步，防止漂移
                self.pos.y = float(self.rect.y)
                self.vel.y = 0
                # 落地时立即稳定位置
                if self.grounded:
                    self.vel.x = 0 if abs(self.vel.x) < 0.5 else self.vel.x
        
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
                    # 对held item位置进行整数化，防止亚像素抖动
                    temp_pos = player_center + offset
                    self.held_item_pos = pygame.Vector2(round(temp_pos.x), round(temp_pos.y))

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
                # 对默认held item位置也进行整数化
                self.held_item_pos = pygame.Vector2(round(item_pos_x), round(item_pos_y))
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
        
        # 最终位置同步 - 确保每帧结束时pos和rect完全一致，消除所有抖动
        self.rect.x = round(self.pos.x)
        self.rect.y = round(self.pos.y)
        
        # 最终旋转角度强制重置 - 确保地面时完全没有旋转
        if self.grounded:
            self.rotation_angle = 0.0

    def draw(self, surface, camera_offset, break_progress=0, selected_item_type=None, world_mouse_pos=None):
        # Draw the player's character model
        if self.image:

            

            
            # 🔧 关键修复：确保缩放尺寸始终是稳定的整数
            target_width = int(self.rect.width)
            target_height = int(self.rect.height)
            target_size = (target_width, target_height)
            
            # 缓存缩放后的图像，避免每帧重新缩放
            if not hasattr(self, '_cached_scaled_image') or getattr(self, '_cached_size', None) != target_size:
                # 🔧 使用高质量缩放算法，减少缩放导致的抖动
                self._cached_scaled_image = pygame.transform.smoothscale(self.image, target_size)
                self._cached_size = target_size
                # 同时缓存翻转版本
                self._cached_flipped_image = pygame.transform.flip(self._cached_scaled_image, True, False)
            
            base_image = self._cached_flipped_image if self.facing == -1 else self._cached_scaled_image
            
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

            # 🔧 使用原始图像尺寸但保持简单处理
            # 直接使用原始图像，按rect尺寸缩放但保持稳定
            target_size = (self.rect.width, self.rect.height)
            
            # 简化的缓存系统
            if not hasattr(self, '_simple_cache'):
                self._simple_cache = {}
            
            cache_key = f"{target_size}_{self.facing}"
            if cache_key not in self._simple_cache:
                # 缩放到rect尺寸
                scaled_image = pygame.transform.scale(self.image, target_size)
                
                # 处理朝向
                if self.facing == -1:
                    final_image = pygame.transform.flip(scaled_image, True, False)
                else:
                    final_image = scaled_image
                    
                self._simple_cache[cache_key] = final_image
            
            # 获取缓存的图像
            base_image = self._simple_cache[cache_key]
            
            # 应用特效（如果需要）
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

            # 🔧 谨慎恢复旋转功能：只有在明确需要时才旋转
            if not self.grounded and abs(self.rotation_angle) > 5:  # 只有旋转角度较大时才渲染旋转
                # 跳跃旋转动画
                rotated_player_image = pygame.transform.rotate(base_image, -self.rotation_angle)
                draw_rect = rotated_player_image.get_rect(center=self.rect.center)
                draw_pos = (round(draw_rect.topleft[0] - camera_offset.x), 
                           round(draw_rect.topleft[1] - camera_offset.y))
                surface.blit(rotated_player_image, draw_pos)
            else:
                # 地面或小角度旋转时使用简单渲染
                draw_pos = (round(self.rect.x - camera_offset.x), 
                           round(self.rect.y - camera_offset.y))
                surface.blit(base_image, draw_pos)
        else: # Fallback to azure rectangle
            draw_rect = self.rect.copy()
            # Round the draw position to prevent sub-pixel jittering
            draw_rect.topleft = (round(self.rect.x - camera_offset.x), 
                               round(self.rect.y - camera_offset.y))
            pygame.draw.rect(surface, (0, 100, 200), draw_rect)

        # 稳定的held item渲染
        if self.held_item_final_surface and self.held_item_pos and not self.is_dying:
            # 🔧 简化held item渲染，减少复杂度
            if abs(self.held_item_angle) > 5:  # 只有角度较大时才旋转
                rotated_image = pygame.transform.rotate(self.held_item_final_surface, self.held_item_angle)
                center_pos = (round(self.held_item_pos.x), round(self.held_item_pos.y))
                new_rect = rotated_image.get_rect(center=center_pos)
                draw_pos = (round(new_rect.topleft[0] - camera_offset.x),
                           round(new_rect.topleft[1] - camera_offset.y))
                surface.blit(rotated_image, draw_pos)
            else:
                # 小角度或静止时使用简单渲染
                draw_pos = (round(self.held_item_pos.x - self.held_item_final_surface.get_width()//2 - camera_offset.x),
                           round(self.held_item_pos.y - self.held_item_final_surface.get_height()//2 - camera_offset.y))
                surface.blit(self.held_item_final_surface, draw_pos)
            
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

            # 强制所有静止状态都使用非旋转渲染
            if abs(self.vel.x) < 0.1 and abs(self.vel.y) < 0.1 and self.grounded:
                # 完全静止时，强制使用简单渲染
                draw_pos = (round(self.rect.x - camera_offset.x), 
                           round(self.rect.y - camera_offset.y))
                surface.blit(base_image, draw_pos)
            elif not self.grounded or self.is_dying:
                # Rotate the image for the jump animation, but keep the original hitbox.
                rotated_player_image = pygame.transform.rotate(base_image, -self.rotation_angle)
                draw_rect = rotated_player_image.get_rect(center=self.rect.center)
                # Round the draw position to prevent sub-pixel jittering
                draw_pos = (round(draw_rect.topleft[0] - camera_offset.x), 
                           round(draw_rect.topleft[1] - camera_offset.y))
                surface.blit(rotated_player_image, draw_pos)

