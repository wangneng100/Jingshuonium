import pygame
from ..core import config
from ..core import assets
from ..core import definitions

class InventoryUI:
    def __init__(self, player_inventory):
        self.inventory = player_inventory
        self.is_open = False

        self.hotbar_cols = 9
        self.inventory_cols = 9
        self.inventory_rows = 3
        
        self.slot_size = assets.BLOCK_SIZE
        self.gap = 4

        # Calculate dimensions for the inventory panel
        inv_width = self.inventory_cols * (self.slot_size + self.gap) - self.gap
        inv_height = self.inventory_rows * (self.slot_size + self.gap) - self.gap
        hotbar_height = self.slot_size
        
        total_height = inv_height + hotbar_height + self.gap * 3 # Extra gaps for title and between sections
        
        self.panel_rect = pygame.Rect(0, 0, inv_width + self.gap * 2, total_height)
        self.panel_rect.center = (config.WINDOW_SIZE[0] / 2, config.WINDOW_SIZE[1] / 2)

        # Armor slot
        self.armor_slot_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
        self.armor_slot_rect.center = (self.panel_rect.left - self.slot_size, self.panel_rect.centery - self.slot_size)

        # Pre-calculate slot rects
        self.slot_rects = [None] * len(self.inventory.slots)
        for i in range(len(self.inventory.slots)):
            col = i % self.hotbar_cols
            # Hotbar is the last row in the UI (slots 0-8)
            if i < self.hotbar_cols: 
                row = self.inventory_rows 
            # Main inventory (slots 9-35)
            else:
                row = (i - self.hotbar_cols) // self.inventory_cols
            
            x = self.panel_rect.x + self.gap + col * (self.slot_size + self.gap)
            # Add extra gap between inventory and hotbar
            y_offset = self.gap if row < self.inventory_rows else self.gap * 2
            y = self.panel_rect.y + self.gap + row * (self.slot_size + self.gap) + y_offset
            
            self.slot_rects[i] = pygame.Rect(x, y, self.slot_size, self.slot_size)

    def toggle(self, held_item):
        self.is_open = not self.is_open
        pygame.mouse.set_visible(self.is_open)
        # If closing with an item held, return it to inventory
        if not self.is_open and held_item:
            if not self.inventory.add_item(held_item['type'], held_item['count']):
                print("Warning: Inventory full. Could not return held item.") # Item is lost
            held_item = None
        return held_item

    def handle_input(self, event, held_item):
        if not self.is_open or event.type != pygame.MOUSEBUTTONDOWN:
            return held_item

        mouse_pos = event.pos

        # Handle armor slot click
        if self.armor_slot_rect.collidepoint(mouse_pos):
            if event.button == 1: # Left click
                # Check if held item is armor
                is_armor = held_item and 'armor' in held_item['type']
                if is_armor:
                    # Swap with whatever is in the armor slot
                    held_item, self.inventory.armor_slot = self.inventory.armor_slot, held_item
                elif held_item is None and self.inventory.armor_slot:
                    # Pick up equipped armor
                    held_item = self.inventory.armor_slot
                    self.inventory.armor_slot = None
            return held_item


        # Handle clicks on inventory slots
        clicked_slot_index = -1
        for i, rect in enumerate(self.slot_rects):
            if rect.collidepoint(mouse_pos):
                clicked_slot_index = i
                break
        
        if clicked_slot_index != -1:
            slot_item = self.inventory.get_slot(clicked_slot_index)
            
            # Left Click
            if event.button == 1:
                # Case 1: Holding nothing, clicking an item -> Pick it up
                if held_item is None and slot_item is not None:
                    held_item = slot_item
                    self.inventory.set_slot(clicked_slot_index, None)
                
                # Case 2: Holding something, clicking a slot
                elif held_item is not None:
                    # Subcase 2a: Clicking an empty slot -> Place item
                    if slot_item is None:
                        self.inventory.set_slot(clicked_slot_index, held_item)
                        held_item = None
                    
                    # Subcase 2b: Clicking a slot with an item
                    else:
                        # Stacking
                        if slot_item['type'] == held_item['type']:
                            can_add = self.inventory.max_stack_size - slot_item['count']
                            transfer_amount = min(can_add, held_item['count'])
                            slot_item['count'] += transfer_amount
                            held_item['count'] -= transfer_amount
                            if held_item['count'] <= 0:
                                held_item = None
                        # Swapping
                        else:
                            self.inventory.set_slot(clicked_slot_index, held_item)
                            held_item = slot_item
            
            # Right Click
            elif event.button == 3:
                # Holding nothing, right click item -> pick up half OR equip armor
                if held_item is None and slot_item is not None:
                    # Check if the item is armor to equip it
                    if 'armor' in slot_item['type']:
                        # Equip it by swapping with the armor slot.
                        # The item that was in the armor slot (if any) goes into the clicked inventory slot.
                        self.inventory.set_slot(clicked_slot_index, self.inventory.armor_slot)
                        # The clicked armor goes into the armor slot.
                        self.inventory.armor_slot = slot_item
                    else: # Original logic for non-armor items (pick up half)
                        take_amount = (slot_item['count'] + 1) // 2
                        held_item = {'type': slot_item['type'], 'count': take_amount}
                        slot_item['count'] -= take_amount
                        if slot_item['count'] <= 0:
                            self.inventory.set_slot(clicked_slot_index, None)

                # Holding something, right click empty slot -> place one
                elif held_item is not None and slot_item is None:
                    self.inventory.set_slot(clicked_slot_index, {'type': held_item['type'], 'count': 1})
                    held_item['count'] -= 1
                    if held_item['count'] <= 0:
                        held_item = None
                
                # Holding something, right click same-type slot -> place one
                elif held_item is not None and slot_item is not None and slot_item['type'] == held_item['type']:
                    if slot_item['count'] < self.inventory.max_stack_size:
                        slot_item['count'] += 1
                        held_item['count'] -= 1
                        if held_item['count'] <= 0:
                            held_item = None

        return held_item

    def draw(self, surface, hotbar):
        if not self.is_open:
            return

        # Draw semi-transparent background
        panel_surf = pygame.Surface(tuple(config.WINDOW_SIZE), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 180))
        surface.blit(panel_surf, (0,0))

        # Draw inventory panel background
        pygame.draw.rect(surface, (20, 20, 20, 220), self.panel_rect, border_radius=5)
        pygame.draw.rect(surface, (120, 120, 120), self.panel_rect, 2, border_radius=5)

        # Draw armor slot
        surface.blit(assets.inventory_slot_texture, self.armor_slot_rect)
        if self.inventory.armor_slot:
            rect = self.armor_slot_rect
            slot_data = self.inventory.armor_slot
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
        # Draw slots and items
        for i, rect in enumerate(self.slot_rects):
            is_hotbar_slot = i < self.hotbar_cols
            is_selected_hotbar_slot = is_hotbar_slot and i == hotbar.selected_slot

            surface.blit(assets.inventory_slot_texture, rect)
            if is_selected_hotbar_slot:
                pygame.draw.rect(surface, assets.WHITE, rect, 3)

            slot_data = self.inventory.get_slot(i)
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