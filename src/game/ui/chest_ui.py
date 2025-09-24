import pygame
from ..core import assets
from ..core import definitions
from .base_ui import InventoryUI
import math

class ChestUI(InventoryUI):
    def __init__(self, player_inventory):
        super().__init__(player_inventory)
        self.active_chest_pos = None
        self.active_chest_entity = None
        self.chest_slot_rects = []
        self.chest_panel_rect = pygame.Rect(0,0,0,0)

        # Reposition player inventory panel to make space for chest grid
        self.panel_rect.y += 60 
        for rect in self.slot_rects:
            rect.y += 60
    def open(self, chest_pos, chest_entity, inventory_size=27):
        self.is_open = True
        self.active_chest_pos = chest_pos
        self.active_chest_entity = chest_entity
        pygame.mouse.set_visible(True)

    def close(self, held_item):
        closed_pos = self.active_chest_pos
        self.is_open = False
        self.active_chest_pos = None
        self.active_chest_entity = None
        pygame.mouse.set_visible(False)
        if held_item:
            if not self.inventory.add_item(held_item['type'], held_item['count']):
                print("Warning: Inventory full. Could not return held item.")
            held_item = None
        return held_item, closed_pos

    def handle_input(self, event, held_item):
        if not self.is_open or event.type != pygame.MOUSEBUTTONDOWN:
            return held_item

        # First, handle clicks on the player inventory part
        held_item = super().handle_input(event, held_item)

        mouse_pos = event.pos
        # Handle clicks on chest slots
        for i, rect in enumerate(self.chest_slot_rects):
            if rect.collidepoint(mouse_pos):
                slot_item = self.active_chest_entity['inventory'][i]
                
                # Left Click
                if event.button == 1:
                    if held_item is None and slot_item is not None:
                        held_item = slot_item
                        self.active_chest_entity['inventory'][i] = None
                    elif held_item is not None:
                        if slot_item is None:
                            self.active_chest_entity['inventory'][i] = held_item
                            held_item = None
                        else:
                            if slot_item['type'] == held_item['type']:
                                can_add = self.inventory.max_stack_size - slot_item['count']
                                transfer_amount = min(can_add, held_item['count'])
                                slot_item['count'] += transfer_amount
                                held_item['count'] -= transfer_amount
                                if held_item['count'] <= 0: held_item = None
                            else:
                                self.active_chest_entity['inventory'][i], held_item = held_item, slot_item
                
                # Right Click
                elif event.button == 3:
                    if held_item is None and slot_item is not None:
                        take_amount = (slot_item['count'] + 1) // 2
                        held_item = {'type': slot_item['type'], 'count': take_amount}
                        slot_item['count'] -= take_amount
                        if slot_item['count'] <= 0: self.active_chest_entity['inventory'][i] = None
                    elif held_item is not None and slot_item is None:
                        self.active_chest_entity['inventory'][i] = {'type': held_item['type'], 'count': 1}
                        held_item['count'] -= 1
                        if held_item['count'] <= 0: held_item = None
                    elif held_item is not None and slot_item is not None and slot_item['type'] == held_item['type']:
                        if slot_item['count'] < self.inventory.max_stack_size:
                            slot_item['count'] += 1
                            held_item['count'] -= 1
                            if held_item['count'] <= 0: held_item = None
                break
        return held_item

    def draw(self, surface, hotbar):
        if not self.is_open: return

        # Draw player inventory UI first
        super().draw(surface, hotbar)

        # Draw chest inventory panel background
        pygame.draw.rect(surface, (20, 20, 20, 220), self.chest_panel_rect, border_radius=5)
        pygame.draw.rect(surface, (120, 120, 120), self.chest_panel_rect, 2, border_radius=5)

        # Chest grid layout (dynamic)
        num_rows = math.ceil(len(self.active_chest_entity['inventory']) / self.inventory_cols)
        chest_panel_width = self.inventory_cols * (self.slot_size + self.gap) - self.gap
        chest_panel_height = num_rows * (self.slot_size + self.gap) - self.gap
        
        self.chest_panel_rect = pygame.Rect(0, 0, chest_panel_width + self.gap*2, chest_panel_height + self.gap*2)
        self.chest_panel_rect.centerx = self.panel_rect.centerx
        self.chest_panel_rect.bottom = self.panel_rect.top - self.gap*2

        self.chest_slot_rects = [None] * len(self.active_chest_entity['inventory'])
        for i in range(len(self.chest_slot_rects)):
            col = i % self.inventory_cols
            row = i // self.inventory_cols
            x = self.chest_panel_rect.x + self.gap + col * (self.slot_size + self.gap)
            y = self.chest_panel_rect.y + self.gap + row * (self.slot_size + self.gap)
            self.chest_slot_rects[i] = pygame.Rect(x, y, self.slot_size, self.slot_size)

        # Draw chest inventory slots and items
        for i, rect in enumerate(self.chest_slot_rects):
            surface.blit(assets.inventory_slot_texture, rect)
            slot_data = self.active_chest_entity['inventory'][i]
            if slot_data:
                item_type = slot_data["type"]
                item_texture = assets.textures[item_type]

                if item_type in definitions.ITEM_SCALES:
                    scale = definitions.ITEM_SCALES[item_type]
                    new_size = int(item_texture.get_width() * scale)
                    item_texture = pygame.transform.scale(item_texture, (new_size, new_size))

                item_rect = item_texture.get_rect(center=rect.center)
                surface.blit(item_texture, item_rect)

                count_str = str(slot_data["count"])
                shadow_surf = assets.small_font.render(count_str, True, assets.BLACK)
                text_surf = assets.small_font.render(count_str, True, assets.WHITE)
                text_rect = text_surf.get_rect(bottomright=(rect.right - 3, rect.bottom - 3))
                shadow_rect = shadow_surf.get_rect(bottomright=(text_rect.right + 1, text_rect.bottom + 1))
                surface.blit(shadow_surf, shadow_rect)
                surface.blit(text_surf, text_rect)