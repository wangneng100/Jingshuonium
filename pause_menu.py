import pygame
import config
import assets
from menu_utils import Button

class PauseMenu:
    def __init__(self):
        button_width = 350
        button_height = 50
        center_x = config.WINDOW_SIZE[0] / 2
        
        self.resume_button = Button(
            center_x - button_width / 2,
            config.WINDOW_SIZE[1] * 0.45,
            button_width, button_height,
            "Back to Game", assets.font, (100, 100, 100), (150, 150, 150)
        )
        self.quit_button = Button(
            center_x - button_width / 2,
            config.WINDOW_SIZE[1] * 0.60,
            button_width, button_height,
            "Save & Quit to Title", assets.font, (100, 100, 100), (150, 150, 150)
        )
        self.buttons = [self.resume_button, self.quit_button]

    def handle_input(self, event):
        if self.resume_button.handle_event(event):
            return "resume"
        if self.quit_button.handle_event(event):
            return "quit"
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "resume"
            
        return None

    def draw(self, surface):
        panel_surf = pygame.Surface(tuple(config.WINDOW_SIZE), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 180))
        surface.blit(panel_surf, (0,0))
        
        # Paused text
        paused_text_surf = assets.big_font.render("PAUSED", True, assets.WHITE)
        paused_shadow_surf = assets.big_font.render("PAUSED", True, assets.BLACK)
        text_pos_x = config.WINDOW_SIZE[0]/2 - paused_text_surf.get_width()/2
        text_pos_y = config.WINDOW_SIZE[1] * 0.25
        surface.blit(paused_shadow_surf, (text_pos_x + 3, text_pos_y + 3))
        surface.blit(paused_text_surf, (text_pos_x, text_pos_y))

        for button in self.buttons:
            button.draw(surface)