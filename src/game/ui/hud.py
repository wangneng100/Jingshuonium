import pygame
import math
from ..core import config
from ..core import assets
from ..core import definitions

# --- HOTBAR --- 
class Hotbar:
    def __init__(self, player_inventory):
        self.inventory = player_inventory
        self.selected_slot = 0

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key >= pygame.K_1 and event.key <= pygame.K_9:
                self.selected_slot = event.key - pygame.K_1
        elif event.type == pygame.MOUSEWHEEL:
            self.selected_slot = (self.selected_slot - event.y) % 9

    def get_selected_item_type(self):
        slot = self.inventory.slots[self.selected_slot]
        if slot and slot["count"] > 0:
            return slot.get("type")
        return None

    def use_selected_item(self):
        slot = self.inventory.slots[self.selected_slot]
        if slot and slot["count"] > 0:
            slot["count"] -= 1
            if slot["count"] == 0:
                self.inventory.slots[self.selected_slot] = None
            return True
        return False

    def draw(self, surface):
        hotbar_slot_size = int(assets.BLOCK_SIZE * definitions.HOTBAR_SCALE)
        hotbar_width = 9 * hotbar_slot_size
        start_x = (config.WINDOW_SIZE[0] - hotbar_width) / 2
        y_pos = config.WINDOW_SIZE[1] - hotbar_slot_size - 10
        hotbar_slots = self.inventory.slots[:9]

        scaled_slot_texture = pygame.transform.scale(assets.inventory_slot_texture, (hotbar_slot_size, hotbar_slot_size))

        for i, slot_data in enumerate(hotbar_slots):
            slot_x = start_x + i * hotbar_slot_size
            surface.blit(scaled_slot_texture, (slot_x, y_pos))

            if slot_data:
                item_type = slot_data["type"]
                item_texture = assets.textures[item_type]

                item_base_scale = definitions.ITEM_SCALES.get(item_type, 1.0)
                final_size = int(assets.BLOCK_SIZE * item_base_scale * definitions.HOTBAR_SCALE)
                scaled_item_texture = pygame.transform.scale(item_texture, (final_size, final_size))

                item_rect = scaled_item_texture.get_rect(center=(slot_x + hotbar_slot_size / 2, y_pos + hotbar_slot_size / 2))
                surface.blit(scaled_item_texture, item_rect)

                # Draw item count with a shadow for visibility
                count_str = str(slot_data["count"])
                shadow_surf = assets.scaled_small_font.render(count_str, True, assets.BLACK)
                text_surf = assets.scaled_small_font.render(count_str, True, assets.WHITE)

                # Position text at the bottom-right of the slot
                text_rect = text_surf.get_rect(bottomright=(slot_x + hotbar_slot_size - 3, y_pos + hotbar_slot_size - 3))
                shadow_rect = shadow_surf.get_rect(bottomright=(text_rect.right + 1, text_rect.bottom + 1))
                surface.blit(shadow_surf, shadow_rect)
                surface.blit(text_surf, text_rect)

        # Highlight selected slot
        selected_rect = pygame.Rect(start_x + self.selected_slot * hotbar_slot_size, y_pos, hotbar_slot_size, hotbar_slot_size)
        pygame.draw.rect(surface, assets.WHITE, selected_rect, 3)

# --- HEALTH BAR ---
class HealthBar:
    def __init__(self, player):
        self.player = player
        self.health_icon = pygame.transform.scale(assets.health_texture, (int(assets.BLOCK_SIZE * 0.75), int(assets.BLOCK_SIZE * 0.75)))
        self.icon_size = self.health_icon.get_width()
        # Create a half-heart icon by taking the left half of the full heart icon
        try:
            self.half_health_icon = self.health_icon.subsurface(pygame.Rect(0, 0, self.icon_size // 2, self.icon_size))
        except ValueError: # Fallback in case subsurface fails
            self.half_health_icon = pygame.Surface((self.icon_size // 2, self.icon_size), pygame.SRCALPHA)
            self.half_health_icon.blit(self.health_icon, (0, 0))

    def draw(self, surface):
        # Position the health bar above the hotbar, aligned to the left
        hotbar_slot_size = int(assets.BLOCK_SIZE * definitions.HOTBAR_SCALE)
        hotbar_height = hotbar_slot_size + 10 # from Hotbar.draw
        start_y = config.WINDOW_SIZE[1] - hotbar_height - self.icon_size - 10

        hotbar_width = 9 * hotbar_slot_size
        start_x = (config.WINDOW_SIZE[0] - hotbar_width) / 2

        # Round health to the nearest 0.5 for display purposes
        display_health = round(self.player.health * 2) / 2
        full_hearts = math.floor(display_health)
        has_half_heart = (display_health % 1) != 0

        # Draw full hearts
        for i in range(full_hearts):
            surface.blit(self.health_icon, (start_x + i * (self.icon_size + 2), start_y))
        
        # Draw half heart if needed
        if has_half_heart:
            surface.blit(self.half_health_icon, (start_x + full_hearts * (self.icon_size + 2), start_y))

# --- TIME DISPLAY ---
class TimeDisplay:
    def __init__(self):
        self.font = assets.font

    def draw(self, surface, day, time_of_day, money):
        # Calculations
        day_duration = definitions.DAY_NIGHT_DURATION
        hour = (time_of_day % day_duration) / (day_duration / 24)
        minute = (hour % 1) * 60
        ampm = "AM" if hour < 12 else "PM"
        hour_12 = int(hour % 12)
        if hour_12 == 0: hour_12 = 12
        
        time_str = f"{hour_12:02d}:{int(minute):02d} {ampm}"
        day_str = f"Day {day}"
        money_str = f"${money}"

        # Render and blit
        time_surf = self.font.render(time_str, True, assets.WHITE)
        day_surf = self.font.render(day_str, True, assets.WHITE)
        money_surf = self.font.render(money_str, True, (255, 223, 0)) # Gold color

        # Shadow
        surface.blit(self.font.render(day_str, True, assets.BLACK), (config.WINDOW_SIZE[0] - day_surf.get_width() - 14, 11))
        surface.blit(self.font.render(time_str, True, assets.BLACK), (config.WINDOW_SIZE[0] - time_surf.get_width() - 14, 11 + day_surf.get_height()))
        surface.blit(self.font.render(money_str, True, assets.BLACK), (config.WINDOW_SIZE[0] - money_surf.get_width() - 14, 11 + day_surf.get_height() + time_surf.get_height()))
        # Text
        surface.blit(day_surf, (config.WINDOW_SIZE[0] - day_surf.get_width() - 15, 10))
        surface.blit(time_surf, (config.WINDOW_SIZE[0] - time_surf.get_width() - 15, 10 + day_surf.get_height()))
        surface.blit(money_surf, (config.WINDOW_SIZE[0] - money_surf.get_width() - 15, 10 + day_surf.get_height() + time_surf.get_height()))