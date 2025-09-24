#!/usr/bin/env python3
"""
简单的按钮测试程序，用于诊断双击问题
"""

import pygame
import sys

# 初始化pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Button Test")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

class TestButton:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.text_surf = self.font.render(text, True, (255, 255, 255))
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        self.color = (100, 100, 100)
        self.hover_color = (150, 150, 150)
        self.current_color = self.color
        self.click_count = 0
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.current_color = self.hover_color
            else:
                self.current_color = self.color
                
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.click_count += 1
                print(f"按钮 '{self.text}' 被点击了! 点击次数: {self.click_count}")
                return True
        return False
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.current_color, self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        surface.blit(self.text_surf, self.text_rect)
        
        # 显示点击次数
        count_text = font.render(f"点击: {self.click_count}", True, (255, 255, 255))
        count_rect = count_text.get_rect(center=(self.rect.centerx, self.rect.bottom + 20))
        surface.blit(count_text, count_rect)

def main():
    button = TestButton(300, 200, 200, 60, "测试按钮")
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            button.handle_event(event)
        
        screen.fill((50, 50, 50))
        button.draw(screen)
        
        # 显示说明
        info_text = font.render("单击按钮测试 - 应该每次点击计数+1", True, (255, 255, 255))
        screen.blit(info_text, (50, 50))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()