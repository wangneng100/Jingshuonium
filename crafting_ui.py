import pygame
import assets
import definitions
from base_ui import InventoryUI

class CraftingUI(InventoryUI):
    def __init__(self, player_inventory):
        super().__init__(player_inventory)
        self.crafting_slots = [None] * 9
        self.result_slot = None

        # For QoL features
        self.last_click_time = 0
        self.last_clicked_slot_info = {'index': -1, 'is_crafting_grid': False, 'is_player_inv': False}
        self.last_drag_slot = -1
        
        # Reposition the main inventory panel to make space for crafting grid
        self.panel_rect.y += 60 
        for rect in self.slot_rects:
            rect.y += 60

        # Crafting grid layout
        self.crafting_grid_rects = [None] * 9
        grid_x_start = self.panel_rect.centerx - (1.5 * self.slot_size + self.gap)
        grid_y_start = self.panel_rect.y - (3 * self.slot_size + 4 * self.gap)
        for i in range(9):
            row, col = divmod(i, 3)
            x = grid_x_start + col * (self.slot_size + self.gap)
            y = grid_y_start + row * (self.slot_size + self.gap)
            self.crafting_grid_rects[i] = pygame.Rect(x, y, self.slot_size, self.slot_size)

        # Result slot layout
        result_x = self.panel_rect.centerx + (1.5 * self.slot_size + self.gap * 3)
        result_y = grid_y_start + self.slot_size + self.gap
        self.result_slot_rect = pygame.Rect(result_x, result_y, self.slot_size, self.slot_size)

    def toggle(self, held_item):
        is_opening = not self.is_open
        new_held_item = super().toggle(held_item)
        # If closing, return crafting items to inventory
        if not self.is_open and is_opening:
            for item in self.crafting_slots:
                if item: self.inventory.add_item(item['type'], item['count'])
            if self.result_slot:
                self.inventory.add_item(self.result_slot['type'], self.result_slot['count'])
            self.crafting_slots = [None] * 9
            self.result_slot = None
        return new_held_item

    def _get_shape_bounds(self, shape_grid):
        min_r, max_r, min_c, max_c = -1, -1, -1, -1
        for r, row in enumerate(shape_grid):
            for c, item in enumerate(row):
                if item is not None:
                    if min_r == -1: min_r = r
                    max_r = r
                    if min_c == -1 or c < min_c: min_c = c
                    if max_c == -1 or c > max_c: max_c = c
        if min_r == -1: return None
        return (min_r, min_c, max_r - min_r + 1, max_c - min_c + 1)

    def check_recipe(self):
        grid_types_3x3 = [[(self.crafting_slots[r*3+c]['type'] if self.crafting_slots[r*3+c] else None) for c in range(3)] for r in range(3)]
        
        user_bounds = self._get_shape_bounds(grid_types_3x3)
        if not user_bounds:
            self.result_slot = None
            return

        user_r, user_c, user_h, user_w = user_bounds
        user_subgrid = [row[user_c:user_c+user_w] for row in grid_types_3x3[user_r:user_r+user_h]]

        for recipe in definitions.CRAFTING_RECIPES:
            recipe_shape_2d = [[None]*3 for _ in range(3)]
            flat_shape = recipe['shape']
            for r, row_items in enumerate(flat_shape):
                for c, item_type in enumerate(row_items):
                    if r < 3 and c < 3: recipe_shape_2d[r][c] = item_type

            recipe_bounds = self._get_shape_bounds(recipe_shape_2d)
            if not recipe_bounds: continue

            recipe_r, recipe_c, recipe_h, recipe_w = recipe_bounds
            if user_h == recipe_h and user_w == recipe_w:
                recipe_subgrid = [row[recipe_c:recipe_c+recipe_w] for row in recipe_shape_2d[recipe_r:recipe_r+recipe_h]]
                if user_subgrid == recipe_subgrid:
                    self.result_slot = recipe['result'].copy()
                    return
        self.result_slot = None

    def _handle_drag_placement(self, event, held_item):
        if held_item and event.buttons[0]: # if left button is held
            mouse_pos = event.pos
            for i, rect in enumerate(self.crafting_grid_rects):
                if rect.collidepoint(mouse_pos) and self.crafting_slots[i] is None and i != self.last_drag_slot:
                    self.crafting_slots[i] = {'type': held_item['type'], 'count': 1}
                    held_item['count'] -= 1
                    if held_item['count'] <= 0:
                        held_item = None
                    self.last_drag_slot = i
                    self.check_recipe()
                    return held_item
        return held_item

    def handle_input(self, event, held_item):
        if not self.is_open:
            return held_item

        # Handle dragging to place items
        if event.type == pygame.MOUSEMOTION:
            return self._handle_drag_placement(event, held_item)

        if event.type != pygame.MOUSEBUTTONDOWN:
            return held_item

        # Reset drag tracking on a new click
        if event.button == 1:
            self.last_drag_slot = -1

        mouse_pos = event.pos

        keys = pygame.key.get_pressed()
        is_ctrl_click = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        # Handle crafting grid clicks
        for i, rect in enumerate(self.crafting_grid_rects):
            if rect.collidepoint(mouse_pos):
                slot_item = self.crafting_slots[i]
                # Left click
                if event.button == 1:
                    # "Gather All" on Ctrl+click
                    if is_ctrl_click and (held_item or slot_item):
                        type_to_collect = None
                        if held_item:
                            type_to_collect = held_item['type']
                        elif slot_item:
                            type_to_collect = slot_item['type']
                            held_item = slot_item
                            self.crafting_slots[i] = None

                        if type_to_collect:
                            # Collect from player inventory
                            for inv_idx, inv_slot in enumerate(self.inventory.slots):
                                if inv_slot and inv_slot['type'] == type_to_collect:
                                    held_item['count'] += inv_slot['count']
                                    self.inventory.set_slot(inv_idx, None)
                            # Collect from crafting grid
                            for craft_idx, craft_slot in enumerate(self.crafting_slots):
                                if craft_slot and craft_slot['type'] == type_to_collect:
                                    held_item['count'] += craft_slot['count']
                                    self.crafting_slots[craft_idx] = None
                            
                            # Put the originally clicked item back in the held_item if it was picked up
                            if slot_item and not self.crafting_slots[i]:
                                self.crafting_slots[i] = None # Ensure it's cleared before check_recipe

                    else: # Normal click
                        # Swap/Place
                        held_item, self.crafting_slots[i] = self.crafting_slots[i], held_item
                # Right click
                elif event.button == 3:
                    # Case 1: Hand is empty, slot has item -> Pick up half
                    if held_item is None and slot_item is not None:
                        take_amount = (slot_item['count'] + 1) // 2
                        held_item = {'type': slot_item['type'], 'count': take_amount}
                        slot_item['count'] -= take_amount
                        if slot_item['count'] <= 0:
                            self.crafting_slots[i] = None
                    # Case 2: Hand has item -> Place one
                    elif held_item is not None:
                        if slot_item is None:
                            self.crafting_slots[i] = {'type': held_item['type'], 'count': 1}
                            held_item['count'] -= 1
                        elif slot_item['type'] == held_item['type']:
                            # Assuming no stack limit in crafting grid for simplicity
                            slot_item['count'] += 1
                            held_item['count'] -= 1
                        
                        if held_item['count'] <= 0:
                            held_item = None
                self.check_recipe()
                return held_item

        # Handle player inventory clicks
        clicked_inv_slot_index = -1
        for i, rect in enumerate(self.slot_rects):
            if rect.collidepoint(mouse_pos):
                clicked_inv_slot_index = i
                break
        
        if clicked_inv_slot_index != -1:
            # If it's a Ctrl+Click, handle it here with the special gather logic
            if event.button == 1 and is_ctrl_click:
                slot_item = self.inventory.get_slot(clicked_inv_slot_index)
                type_to_collect = None
                if held_item:
                    type_to_collect = held_item['type']
                elif slot_item:
                    type_to_collect = slot_item['type']
                    held_item = slot_item
                    self.inventory.set_slot(clicked_inv_slot_index, None)

                if type_to_collect:
                    # Collect from player inventory
                    for inv_idx, inv_slot in enumerate(self.inventory.slots):
                        if inv_slot and inv_slot['type'] == type_to_collect:
                            held_item['count'] += inv_slot['count']
                            self.inventory.set_slot(inv_idx, None)
                    # Collect from crafting grid
                    for craft_idx, craft_slot in enumerate(self.crafting_slots):
                        if craft_slot and craft_slot['type'] == type_to_collect:
                            held_item['count'] += craft_slot['count']
                            self.crafting_slots[craft_idx] = None
                    self.check_recipe()
                return held_item
            else:
                # Otherwise, use the default inventory handling
                return super().handle_input(event, held_item)

        # Handle result slot click
        if self.result_slot_rect.collidepoint(mouse_pos) and self.result_slot:
            if event.button == 1:
                keys = pygame.key.get_pressed()
                is_shift_click = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

                if is_shift_click:
                    # Craft all possible items and move to inventory
                    max_crafts = 99999
                    for slot in self.crafting_slots:
                        if slot: max_crafts = min(max_crafts, slot['count'])
                    
                    if max_crafts > 0 and max_crafts != 99999:
                        result_item = self.result_slot
                        total_to_craft = result_item['count'] * max_crafts
                        
                        if self.inventory.can_add_item(result_item['type'], total_to_craft):
                            self.inventory.add_item(result_item['type'], total_to_craft)
                            for i in range(9):
                                if self.crafting_slots[i]:
                                    self.crafting_slots[i]['count'] -= max_crafts
                                    if self.crafting_slots[i]['count'] <= 0: self.crafting_slots[i] = None
                            self.check_recipe()

                else: # Normal click, craft one
                    if not held_item or (held_item['type'] == self.result_slot['type'] and held_item['count'] + self.result_slot['count'] <= self.inventory.max_stack_size):
                        if not held_item: held_item = self.result_slot.copy()
                        else: held_item['count'] += self.result_slot['count']
                        
                        for i in range(9):
                            if self.crafting_slots[i]:
                                self.crafting_slots[i]['count'] -= 1
                                if self.crafting_slots[i]['count'] <= 0: self.crafting_slots[i] = None
                        
                        self.check_recipe()

        return held_item

    def draw(self, surface, hotbar):
        if not self.is_open: return

        # Draw main inventory UI first
        super().draw(surface, hotbar)

        # Draw crafting grid
        for rect in self.crafting_grid_rects:
            surface.blit(assets.inventory_slot_texture, rect)
        
        # Draw items in crafting grid
        for i, item in enumerate(self.crafting_slots):
            if item:
                rect = self.crafting_grid_rects[i]
                item_type = item["type"]
                item_texture = assets.textures[item_type]

                if item_type in definitions.ITEM_SCALES:
                    scale = definitions.ITEM_SCALES[item_type]
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

        # Draw arrow
        arrow_start = (self.crafting_grid_rects[4].right + self.gap * 2, self.result_slot_rect.centery)
        arrow_end = (self.result_slot_rect.left - self.gap * 2, self.result_slot_rect.centery)
        pygame.draw.line(surface, assets.WHITE, arrow_start, arrow_end, 3)
        pygame.draw.polygon(surface, assets.WHITE, [(arrow_end[0], arrow_end[1] - 6), (arrow_end[0], arrow_end[1] + 6), (arrow_end[0] + 8, arrow_end[1])])

        # Draw result slot
        surface.blit(assets.inventory_slot_texture, self.result_slot_rect)
        if self.result_slot:
            rect = self.result_slot_rect
            item_type = self.result_slot["type"]
            item_texture = assets.textures[item_type]

            if item_type in definitions.ITEM_SCALES:
                scale = definitions.ITEM_SCALES[item_type]
                new_size = int(item_texture.get_width() * scale)
                item_texture = pygame.transform.scale(item_texture, (new_size, new_size))

            item_rect = item_texture.get_rect(center=rect.center)
            surface.blit(item_texture, item_rect)
            count_str = str(self.result_slot["count"])
            shadow_surf = assets.small_font.render(count_str, True, assets.BLACK)
            text_surf = assets.small_font.render(count_str, True, assets.WHITE)
            text_rect = text_surf.get_rect(bottomright=(rect.right - 3, rect.bottom - 3))
            shadow_rect = shadow_surf.get_rect(bottomright=(text_rect.right + 1, text_rect.bottom + 1))
            surface.blit(shadow_surf, shadow_rect)
            surface.blit(text_surf, text_rect)