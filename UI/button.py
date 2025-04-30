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
             print(f"Error: Button sprite not found at {unpressed_sprite_path} or {pressed_sprite_path}")
             placeholder_size = (100, 50)
             unpressed_sprite_base = pygame.Surface(placeholder_size, pygame.SRCALPHA)
             unpressed_sprite_base.fill((100, 100, 100, 150))
             pressed_sprite_base = pygame.Surface(placeholder_size, pygame.SRCALPHA)
             pressed_sprite_base.fill((50, 50, 50, 200))
             
        # --- Apply Scaling --- 
        self.scale = scale
        if self.scale != 1.0:
            new_width = int(unpressed_sprite_base.get_width() * self.scale)
            new_height = int(unpressed_sprite_base.get_height() * self.scale)
            # Use smoothscale for potentially better quality when enlarging
            self.unpressed_sprite_base = pygame.transform.smoothscale(unpressed_sprite_base, (new_width, new_height))
            # Assume pressed sprite has same original dimensions
            self.pressed_sprite_base = pygame.transform.smoothscale(pressed_sprite_base, (new_width, new_height))
        else:
            self.unpressed_sprite_base = unpressed_sprite_base
            self.pressed_sprite_base = pressed_sprite_base
        # --------------------

        # Get rect AFTER scaling
        self.rect = self.unpressed_sprite_base.get_rect()
        self.rect.topleft = (x, y)
        self.is_pressed = False
        self.callback = callback
        
        # --- Text Rendering (on scaled sprites) ---
        self.text_surface = None
        if text:
            try:
                # Adjust font size based on scale? Optional, can make text huge.
                # scaled_font_size = int(font_size * self.scale) 
                # font = pygame.font.Font(None, scaled_font_size) 
                font = pygame.font.Font(None, font_size) # Keep original font size for now
            except pygame.error:
                # font = pygame.font.SysFont('arial', scaled_font_size)
                font = pygame.font.SysFont('arial', font_size) # Fallback
                
            self.text_surface = font.render(text, True, font_color)
            self.text_rect = self.text_surface.get_rect()
            # Center text on the SCALED button
            self.text_rect.centerx = self.rect.width // 2
            self.text_rect.centery = self.rect.height // 2 + text_offset_y
            
            # Create final sprites with text blitted onto SCALED base sprites
            self.unpressed_sprite_with_text = self.unpressed_sprite_base.copy()
            self.unpressed_sprite_with_text.blit(self.text_surface, self.text_rect)
            
            self.pressed_sprite_with_text = self.pressed_sprite_base.copy()
            self.pressed_sprite_with_text.blit(self.text_surface, self.text_rect) 
        else:
            self.unpressed_sprite_with_text = self.unpressed_sprite_base
            self.pressed_sprite_with_text = self.pressed_sprite_base
            
        self.image = self.unpressed_sprite_with_text
        # Ensure this refers to the potentially scaled base sprite
        self.unpressed_sprite = self.unpressed_sprite_base 
        # ----------------------------------------

    def handle_event(self, event):
        action = None
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.is_pressed = True
                self.image = self.pressed_sprite_with_text # Use text version
        elif event.type == pygame.MOUSEBUTTONUP:
            # Important: Check if button *was* pressed before proceeding
            if event.button == 1 and self.is_pressed: 
                self.is_pressed = False
                self.image = self.unpressed_sprite_with_text # Use text version
                # Check if mouse is still over the button on release
                if self.rect.collidepoint(event.pos):
                    if self.callback:
                        # Execute the callback function. Return value depends on callback.
                        action = self.callback() 
                        # If callback returns None, action remains None. If it returns something, action gets that value.
                        # For _toggle_pause, action will be None. For menu actions, it might be a state string.
                        
        # We need to return True or False from handle_event in game.py to know if it was handled.
        # Let's return True if the button state changed or callback was called.
        # However, the previous code in game.py relied on the *action* returned by the callback.
        # Let's stick to returning the action from the callback for now, 
        # as game.py handles consumption based on that.
        # Revisit if consumption logic needs update based on Button return value.
                
        # Optional: Add hover effect logic here if needed
        
        return action # Return the result of the callback

    def draw(self, surface):
        surface.blit(self.image, self.rect) 