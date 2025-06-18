import pygame

class Button:
    def __init__(self, x, y, unpressed_sprite_path, pressed_sprite_path, callback=None,
                 text="", font_size=30, font_color=(255, 255, 255), text_offset_y=0,
                 scale=1.0):
        try:
            unpressed_sprite_base = pygame.image.load(unpressed_sprite_path).convert_alpha()
            pressed_sprite_base = pygame.image.load(pressed_sprite_path).convert_alpha()
        except pygame.error as e:
            print(f"Error loading button sprite: {e}")
            placeholder_size = (100, 50)
            unpressed_sprite_base = pygame.Surface(placeholder_size, pygame.SRCALPHA)
            unpressed_sprite_base.fill((100, 100, 100, 150))
            pressed_sprite_base = pygame.Surface(placeholder_size, pygame.SRCALPHA)
            pressed_sprite_base.fill((50, 50, 50, 200))
        except FileNotFoundError:
             placeholder_size = (100, 50)
             unpressed_sprite_base = pygame.Surface(placeholder_size, pygame.SRCALPHA)
             unpressed_sprite_base.fill((100, 100, 100, 150))
             pressed_sprite_base = pygame.Surface(placeholder_size, pygame.SRCALPHA)
             pressed_sprite_base.fill((50, 50, 50, 200))
             
        self.scale = scale
        if self.scale != 1.0:
            new_width = int(unpressed_sprite_base.get_width() * self.scale)
            new_height = int(unpressed_sprite_base.get_height() * self.scale)
            self.unpressed_sprite_base = pygame.transform.smoothscale(unpressed_sprite_base, (new_width, new_height))
            self.pressed_sprite_base = pygame.transform.smoothscale(pressed_sprite_base, (new_width, new_height))
        else:
            self.unpressed_sprite_base = unpressed_sprite_base
            self.pressed_sprite_base = pressed_sprite_base

        self.rect = self.unpressed_sprite_base.get_rect()
        self.rect.topleft = (x, y)
        self.is_pressed = False
        self.callback = callback
        
        self.text_surface = None
        if text:
            try:
                font = pygame.font.Font(None, font_size)
            except pygame.error:
                font = pygame.font.SysFont('arial', font_size)
                
            self.text_surface = font.render(text, True, font_color)
            self.text_rect = self.text_surface.get_rect()
            self.text_rect.centerx = self.rect.width // 2
            self.text_rect.centery = self.rect.height // 2 + text_offset_y
            
            self.unpressed_sprite_with_text = self.unpressed_sprite_base.copy()
            self.unpressed_sprite_with_text.blit(self.text_surface, self.text_rect)
            
            self.pressed_sprite_with_text = self.pressed_sprite_base.copy()
            self.pressed_sprite_with_text.blit(self.text_surface, self.text_rect)
        else:
            self.unpressed_sprite_with_text = self.unpressed_sprite_base
            self.pressed_sprite_with_text = self.pressed_sprite_base
            
        self.image = self.unpressed_sprite_with_text
        self.unpressed_sprite = self.unpressed_sprite_base

    def handle_event(self, event):
        action = None
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.is_pressed = True
                self.image = self.pressed_sprite_with_text
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed:
                self.is_pressed = False
                self.image = self.unpressed_sprite_with_text
                if self.rect.collidepoint(event.pos):
                    if self.callback:
                        action = self.callback()
                        
                
        
        return action

    def draw(self, surface):
        surface.blit(self.image, self.rect)