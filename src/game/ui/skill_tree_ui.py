import pygame
from ..core import config
from ..core import assets
from ..core import definitions
from .menu_utils import Button

class SkillTreeUI:
    def __init__(self, player):
        self.player = player
        self.is_open = False
        
        self.panel_rect = pygame.Rect(0, 0, 600, 450)
        self.panel_rect.center = (config.WINDOW_SIZE[0] / 2, config.WINDOW_SIZE[1] / 2)

        self.skill_buttons = {}
        self.setup_skill_buttons()

    def setup_skill_buttons(self):
        self.skill_buttons.clear()
        start_x = self.panel_rect.left + 30
        start_y = self.panel_rect.top + 80
        y_offset = 0
        
        for skill_id, skill_data in definitions.SKILLS.items():
            button_rect = pygame.Rect(start_x + 400, start_y + y_offset + 10, 120, 40)
            self.skill_buttons[skill_id] = {
                "button": Button(button_rect.x, button_rect.y, button_rect.width, button_rect.height, "Upgrade", assets.small_font, (50, 150, 50), (80, 200, 80)),
                "skill_id": skill_id,
                "data": skill_data,
                "y_pos": start_y + y_offset
            }
            y_offset += 80

    def toggle(self):
        self.is_open = not self.is_open
        pygame.mouse.set_visible(self.is_open)

    def handle_input(self, event):
        if not self.is_open or event.type != pygame.MOUSEBUTTONDOWN:
            return

        for skill_id, button_info in self.skill_buttons.items():
            if button_info["button"].handle_event(event):
                current_level = self.player.get_skill_level(skill_id)
                max_level = button_info["data"]["max_level"]
                cost = button_info["data"]["cost"]

                if self.player.skill_points >= cost and current_level < max_level:
                    self.player.skill_points -= cost
                    self.player.skills[skill_id] += 1

    def draw(self, surface):
        if not self.is_open:
            return

        panel_surf = pygame.Surface(config.WINDOW_SIZE, pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 180))
        surface.blit(panel_surf, (0, 0))

        pygame.draw.rect(surface, (20, 20, 20, 220), self.panel_rect, border_radius=5)
        pygame.draw.rect(surface, (120, 120, 120), self.panel_rect, 2, border_radius=5)

        title_surf = assets.font.render("Skill Tree", True, assets.WHITE)
        title_rect = title_surf.get_rect(centerx=self.panel_rect.centerx, top=self.panel_rect.top + 15)
        surface.blit(title_surf, title_rect)

        sp_text = f"Skill Points: {self.player.skill_points}"
        sp_surf = assets.small_font.render(sp_text, True, assets.WHITE)
        sp_rect = sp_surf.get_rect(right=self.panel_rect.right - 20, top=self.panel_rect.top + 20)
        surface.blit(sp_surf, sp_rect)

        for skill_id, button_info in self.skill_buttons.items():
            y_pos = button_info["y_pos"]
            skill_data = button_info["data"]
            
            name_surf = assets.small_font.render(skill_data["name"], True, assets.WHITE)
            surface.blit(name_surf, (self.panel_rect.left + 30, y_pos))

            desc_surf = assets.tiny_font.render(skill_data["description"], True, (200, 200, 200))
            surface.blit(desc_surf, (self.panel_rect.left + 30, y_pos + 25))

            current_level = self.player.get_skill_level(skill_id)
            max_level = skill_data["max_level"]
            level_text = f"Level: {current_level} / {max_level}"
            level_surf = assets.small_font.render(level_text, True, assets.WHITE)
            surface.blit(level_surf, (self.panel_rect.left + 30, y_pos + 45))

            button = button_info["button"]
            can_upgrade = self.player.skill_points >= skill_data["cost"] and current_level < max_level
            
            button.base_color = (50, 150, 50) if can_upgrade else (80, 80, 80)
            button.hover_color = (80, 200, 80) if can_upgrade else (80, 80, 80)
            if not button.rect.collidepoint(pygame.mouse.get_pos()):
                button.current_color = button.base_color
            
            if current_level >= max_level:
                button.text = "Maxed"
            
            button.draw(surface)