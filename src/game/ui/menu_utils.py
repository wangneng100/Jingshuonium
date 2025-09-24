import pygame
from ..core import assets

class Button:
    def __init__(self, x, y, width, height, text, font, base_color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.current_color = base_color
        self.text_surf = self.font.render(self.text, True, assets.WHITE)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def handle_event(self, event):
        # Handle mouse hover for visual feedback
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.current_color = self.hover_color
            else:
                self.current_color = self.base_color
        
        # 最简单的点击检测 - 只检测MOUSEBUTTONDOWN
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, tuple(min(255, c + 40) for c in self.current_color[:3]), self.rect, 3, border_radius=8)
        surface.blit(self.text_surf, self.text_rect)

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.font = font
        
        self.knob_rect = pygame.Rect(0, 0, height, height)
        self.dragging = False

        self.label_surf = self.font.render(self.label, True, assets.WHITE)
        self.label_rect = self.label_surf.get_rect(midright=(x - 20, self.rect.centery))

    def get_value(self):
        return self.val

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.knob_rect.inflate(10, 10).collidepoint(mouse_pos) or self.rect.collidepoint(mouse_pos):
                self.dragging = True
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        if (event.type == pygame.MOUSEMOTION and self.dragging) or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(mouse_pos)):
            mouse_x = max(self.rect.x, min(mouse_pos[0], self.rect.right))
            ratio = (mouse_x - self.rect.x) / self.rect.width
            self.val = self.min_val + ratio * (self.max_val - self.min_val)
            return True
        
        return False

    def draw(self, surface):
        surface.blit(self.label_surf, self.label_rect)
        pygame.draw.rect(surface, (80, 80, 80), self.rect, border_radius=5)
        
        fill_ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        fill_width = self.rect.width * fill_ratio
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, (150, 150, 150), fill_rect, border_radius=5)

        knob_x = self.rect.x + fill_width
        self.knob_rect.center = (knob_x, self.rect.centery)
        knob_color = (220, 220, 220) if self.dragging else (180, 180, 180)
        pygame.draw.circle(surface, knob_color, self.knob_rect.center, self.rect.height * 0.8)
        pygame.draw.circle(surface, (120, 120, 120), self.knob_rect.center, self.rect.height * 0.8, 2)

        value_text = f"{int(self.val)}" if self.label == "Sensitivity" else f"{int(self.val * 100)}%"
        val_surf = self.font.render(value_text, True, assets.WHITE)
        val_rect = val_surf.get_rect(midleft=(self.rect.right + 20, self.rect.centery))
        surface.blit(val_surf, val_rect)