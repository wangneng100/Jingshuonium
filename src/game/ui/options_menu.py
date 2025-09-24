import pygame
from ..core import config
from ..core import assets
from .menu_utils import Button, Slider

class OptionsMenu:
    def __init__(self):
        slider_width = 300
        slider_height = 15
        button_width = 250
        button_height = 50
        center_x = config.WINDOW_SIZE[0] / 2

        self.sensitivity_slider = Slider(
            center_x - slider_width / 2,
            config.WINDOW_SIZE[1] * 0.45,
            slider_width, slider_height,
            10, 150, config.MOUSE_SENSITIVITY,
            "Sensitivity", assets.font
        )
        
        initial_volume = pygame.mixer.music.get_volume()
        self.volume_slider = Slider(
            center_x - slider_width / 2,
            config.WINDOW_SIZE[1] * 0.55,
            slider_width, slider_height,
            0.0, 1.0, initial_volume,
            "Volume", assets.font
        )

        self.back_button = Button(
            center_x - button_width / 2,
            config.WINDOW_SIZE[1] * 0.65,
            button_width, button_height,
            "Back", assets.font, (100, 100, 100), (150, 150, 150)
        )
        
        self.controls = [self.sensitivity_slider, self.volume_slider, self.back_button]

    def handle_input(self, event):
        if self.sensitivity_slider.handle_event(event):
            config.MOUSE_SENSITIVITY = self.sensitivity_slider.get_value()
            return "options_changed"
        
        if self.volume_slider.handle_event(event):
            assets.set_global_volume(self.volume_slider.get_value())
            return "options_changed"

        if self.back_button.handle_event(event):
            return "back"
            
        return None

    def draw(self, surface):
        # The pause menu already draws the dark overlay. We just draw the options on top.
        title_surf = assets.big_font.render("OPTIONS", True, assets.WHITE)
        shadow_surf = assets.big_font.render("OPTIONS", True, assets.BLACK)
        text_pos_x = config.WINDOW_SIZE[0]/2 - title_surf.get_width()/2
        text_pos_y = config.WINDOW_SIZE[1] * 0.25
        surface.blit(shadow_surf, (text_pos_x + 3, text_pos_y + 3))
        surface.blit(title_surf, (text_pos_x, text_pos_y))

        for control in self.controls:
            control.draw(surface)