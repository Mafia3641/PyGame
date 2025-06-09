import pygame
import os
from UI.button import Button
from Scripts.constants import WINDOW_WIDTH, WINDOW_HEIGHT

# Action constants
ACTION_CLOSE_SETTINGS = 'close_settings'

class SettingsMenu:
    def __init__(self):
        self.background_color = (30, 30, 50)  # Dark blue background
        
        # Audio manager will be set later
        self.audio_manager = None
        
        # Volume control variables
        self.slider_rect = pygame.Rect(0, 0, 300, 10)  # Will be centered later
        self.slider_handle_radius = 15
        self.is_dragging = False
        
        # Setup return button
        self._setup_return_button()
        
        # Setup fonts
        self.title_font = pygame.font.Font(None, 74)
        self.label_font = pygame.font.Font(None, 48)
        
        # Pre-render text
        self.title_text = self.title_font.render("НАСТРОЙКИ", True, (255, 255, 255))
        self.volume_label = self.label_font.render("Громкость", True, (255, 255, 255))
        
        # Center elements
        self._center_elements()
        
    def set_audio_manager(self, audio_manager):
        self.audio_manager = audio_manager
        
    def _setup_return_button(self):
        try:
            return_unpressed = "UI/ui_sprites/close_button_unpressed.png"
            return_pressed = "UI/ui_sprites/close_button_pressed.png"
            
            # Create button with text
            self.return_button = Button(
                0, 0,  # Position will be set in _center_elements
                return_unpressed,
                return_pressed,
                callback=self._on_return_click,
                scale=2.0
            )
        except (pygame.error, FileNotFoundError) as e:
            print(f"Error loading return button sprites: {e}")
            self.return_button = None
            
    def _center_elements(self):
        # Center title
        self.title_rect = self.title_text.get_rect(
            centerx=WINDOW_WIDTH // 2,
            top=50
        )
        
        # Center volume label
        self.volume_label_rect = self.volume_label.get_rect(
            centerx=WINDOW_WIDTH // 2,
            top=self.title_rect.bottom + 50
        )
        
        # Center slider
        self.slider_rect.centerx = WINDOW_WIDTH // 2
        self.slider_rect.top = self.volume_label_rect.bottom + 30
        
        # Position return button at the bottom
        if self.return_button:
            self.return_button.rect.centerx = WINDOW_WIDTH // 2
            self.return_button.rect.bottom = WINDOW_HEIGHT - 50
            
    def _on_return_click(self):
        return ACTION_CLOSE_SETTINGS
        
    def handle_events(self, events):
        for event in events:
            # Handle return button
            if self.return_button:
                action = self.return_button.handle_event(event)
                if action:
                    return action
                    
            # Handle slider interaction
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    handle_pos = (
                        self.slider_rect.left + (self.audio_manager.get_volume() if self.audio_manager else 0) * self.slider_rect.width,
                        self.slider_rect.centery
                    )
                    handle_rect = pygame.Rect(
                        handle_pos[0] - self.slider_handle_radius,
                        handle_pos[1] - self.slider_handle_radius,
                        self.slider_handle_radius * 2,
                        self.slider_handle_radius * 2
                    )
                    if handle_rect.collidepoint(event.pos):
                        self.is_dragging = True
                        
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    self.is_dragging = False
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.is_dragging and self.audio_manager:
                    # Update volume based on mouse position
                    rel_x = event.pos[0] - self.slider_rect.left
                    new_volume = max(0.0, min(1.0, rel_x / self.slider_rect.width))
                    self.audio_manager.set_volume(new_volume)
                    
        return None
        
    def update(self, dt):
        pass
        
    def draw(self, surface):
        # Fill background
        surface.fill(self.background_color)
        
        # Draw title
        surface.blit(self.title_text, self.title_rect)
        
        # Draw volume label
        surface.blit(self.volume_label, self.volume_label_rect)
        
        # Draw slider background
        pygame.draw.rect(surface, (100, 100, 100), self.slider_rect)
        
        # Draw filled portion of slider
        if self.audio_manager:
            filled_rect = pygame.Rect(
                self.slider_rect.left,
                self.slider_rect.top,
                self.slider_rect.width * self.audio_manager.get_volume(),
                self.slider_rect.height
            )
            pygame.draw.rect(surface, (200, 200, 200), filled_rect)
        
            # Draw slider handle
            handle_pos = (
                self.slider_rect.left + self.audio_manager.get_volume() * self.slider_rect.width,
                self.slider_rect.centery
            )
            pygame.draw.circle(surface, (255, 255, 255), handle_pos, self.slider_handle_radius)
        
        # Draw return button
        if self.return_button:
            self.return_button.draw(surface) 