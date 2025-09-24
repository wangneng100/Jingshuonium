import pygame
from ..core import assets
from ..core import definitions
from .base_ui import InventoryUI

class FurnaceUI(InventoryUI):
    def __init__(self, player_inventory):
        super().__init__(player_inventory)
        self.active_furnace_pos = None

        # Reposition inventory panel
        self.panel_rect.y += 60
        for rect in self.slot_rects:
            rect.y += 60

        # Furnace-specific slots
        self.input_slot_rect = pygame.Rect(0,0, self.slot_size, self.slot_size)
        self.input_slot_rect.center = (self.panel_rect.centerx - self.slot_size - self.gap, self.panel_rect.y - 60)

        self.fuel_slot_rect = self.input_slot_rect.copy()
        self.fuel_slot_rect.y += self.slot_size + self.gap

        self.output_slot_rect = pygame.Rect(0,0, self.slot_size, self.slot_size)
        self.output_slot_rect.center = (self.panel_rect.centerx + self.slot_size + self.gap, self.input_slot_rect.centery)

    def open(self, furnace_pos):
        self.is_open = True
        self.active_furnace_pos = furnace_pos
        pygame.mouse.set_visible(True)

    def close(self, held_item):
        self.is_open = False
        self.active_furnace_pos = None
        pygame.mouse.set_visible(False)
        if held_item:
            if not self.inventory.add_item(held_item['type'], held_item['count']):
                print("Warning: Inventory full. Could not return held item.")
            held_item = None
        return held_item

    def handle_input(self, event, held_item, furnace_entity):
        if not self.is_open or event.type != pygame.MOUSEBUTTONDOWN:
            return held_item

        # First, handle clicks on the main inventory part
        held_item = super().handle_input(event, held_item)

        mouse_pos = event.pos
        furnace_slots = {
            "input": (self.input_slot_rect, furnace_entity['input']),
            "fuel": (self.fuel_slot_rect, furnace_entity['fuel']),
            "output": (self.output_slot_rect, furnace_entity['output']),
        }

        for slot_name, (rect, item) in furnace_slots.items():
            if rect.collidepoint(mouse_pos):
                # Left Click
                if event.button == 1:
                    # Taking from output slot
                    if slot_name == 'output' and item:
                        if not held_item:
                            held_item = item
                            furnace_entity['output'] = None
                        elif held_item['type'] == item['type']:
                            held_item['count'] += item['count']
                            furnace_entity['output'] = None
                    # Interacting with input/fuel slots
                    elif slot_name != 'output':
                        held_item, furnace_entity[slot_name] = furnace_entity[slot_name], held_item
                
                # Right Click (only for input/fuel)
                elif event.button == 3 and slot_name != 'output':
                    # Place one item
                    if held_item and not item:
                        furnace_entity[slot_name] = {'type': held_item['type'], 'count': 1}
                        held_item['count'] -= 1
                        if held_item['count'] <= 0: held_item = None
                    # Place one item to stack
                    elif held_item and item and held_item['type'] == item['type']:
                        item['count'] += 1
                        held_item['count'] -= 1
                        if held_item['count'] <= 0: held_item = None
                break # Stop after handling one slot

        return held_item

    def draw_slot(self, surface, item, rect):
        surface.blit(assets.inventory_slot_texture, rect)
        if item:
            item_type = item["type"]
            item_texture = assets.textures[item_type]
            scale = definitions.ITEM_SCALES.get(item_type, 1.0)
            new_size = int(item_texture.get_width() * scale)
            item_texture = pygame.transform.scale(item_texture, (new_size, new_size))
            item_rect = item_texture.get_rect(center=rect.center)
            surface.blit(item_texture, item_rect)

            count_str = str(item["count"])
            shadow_surf = assets.small_font.render(count_str, True, assets.BLACK)
            text_surf = assets.small_font.render(count_str, True, assets.WHITE)
            text_rect = text_surf.get_rect(bottomright=(rect.right - 3, rect.bottom - 3))
            shadow_rect = shadow_surf.get_rect(bottomright=(text_rect.right + 1, text_rect.bottom + 1))
            surface.blit(shadow_surf, shadow_rect)
            surface.blit(text_surf, text_rect)

    def draw(self, surface, furnace_entity, hotbar):
        if not self.is_open: return

        # Draw main inventory UI first
        super().draw(surface, hotbar)

        # Draw furnace slots
        self.draw_slot(surface, furnace_entity['input'], self.input_slot_rect)
        self.draw_slot(surface, furnace_entity['fuel'], self.fuel_slot_rect)
        self.draw_slot(surface, furnace_entity['output'], self.output_slot_rect)

        # Draw progress indicators
        # Smelting progress arrow
        arrow_start = (self.input_slot_rect.right + self.gap * 2, self.input_slot_rect.centery)
        arrow_end = (self.output_slot_rect.left - self.gap * 2, self.output_slot_rect.centery)
        arrow_len = arrow_end[0] - arrow_start[0]
        
        smelt_progress_ratio = 0
        if furnace_entity['input']:
            recipe = definitions.SMELTING_RECIPES.get(furnace_entity['input']['type'])
            if recipe:
                smelt_progress_ratio = furnace_entity['smelt_progress'] / recipe['time']

        # Background of arrow
        pygame.draw.line(surface, (60,60,60), arrow_start, arrow_end, 3)
        pygame.draw.polygon(surface, (60,60,60), [(arrow_end[0], arrow_end[1] - 6), (arrow_end[0], arrow_end[1] + 6), (arrow_end[0] + 8, arrow_end[1])])
        # Foreground (progress) of arrow
        if smelt_progress_ratio > 0:
            progress_end_x = arrow_start[0] + arrow_len * smelt_progress_ratio
            pygame.draw.line(surface, assets.WHITE, arrow_start, (progress_end_x, arrow_start[1]), 3)
            if progress_end_x >= arrow_end[0]: # Draw arrowhead if full
                pygame.draw.polygon(surface, assets.WHITE, [(arrow_end[0], arrow_end[1] - 6), (arrow_end[0], arrow_end[1] + 6), (arrow_end[0] + 8, arrow_end[1])])

        # Fuel burn progress
        fuel_bar_rect = pygame.Rect(self.fuel_slot_rect.x, self.fuel_slot_rect.y - self.gap - 14, self.fuel_slot_rect.width, 12)
        
        fuel_progress_ratio = 0
        if furnace_entity['fuel_left'] > 0 and furnace_entity['last_fuel_type']:
            max_fuel_time = definitions.FUEL_VALUES.get(furnace_entity['last_fuel_type'], 1)
            fuel_progress_ratio = furnace_entity['fuel_left'] / max_fuel_time

        # Fire icon
        fire_icon_rect = pygame.Rect(fuel_bar_rect.left, fuel_bar_rect.top, 12, 12)
        pygame.draw.rect(surface, (255,100,0) if fuel_progress_ratio > 0 else (100,100,100), fire_icon_rect)

        # Fuel bar
        bar_bg_rect = pygame.Rect(fire_icon_rect.right + 2, fuel_bar_rect.top, fuel_bar_rect.width - 14, 12)
        pygame.draw.rect(surface, (60,60,60), bar_bg_rect)
        if fuel_progress_ratio > 0:
            bar_fg_rect = bar_bg_rect.copy()
            bar_fg_rect.width *= fuel_progress_ratio
            pygame.draw.rect(surface, (255,165,0), bar_fg_rect)