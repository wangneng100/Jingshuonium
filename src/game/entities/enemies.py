import pygame
import random
import math
from ..core import config
from ..core import assets
from ..core import definitions
# Placeholder imports for now, will be updated during full refactor
# from entities.particles import Particle, create_hit_particles, create_explosion_particles
# from utils.helpers import sign

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
