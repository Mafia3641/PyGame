import pygame
from UI.button import Button
from Scripts.constants import WINDOW_WIDTH, WINDOW_HEIGHT

ACTION_CLOSE_SETTINGS = 'close_settings'


class SettingsMenu:
    """Класс для управления меню настроек"""
    def __init__(self):
        self.background_color = (30, 30, 50)
        
        self.audio_manager = None
        
        self.slider_rect = pygame.Rect(0, 0, 300, 10)
        self.slider_handle_radius = 15
        self.is_dragging = False
        
        self._setup_return_button()
        
        self.title_font = pygame.font.Font(None, 74)
        self.label_font = pygame.font.Font(None, 48)
        
        self.title_text = self.title_font.render("НАСТРОЙКИ", True, (255, 255, 255))
        self.volume_label = self.label_font.render("Громкость", True, (255, 255, 255))
        
        self._center_elements()
        
    def set_audio_manager(self, audio_manager):
        """Установка менеджера звука"""
        self.audio_manager = audio_manager
        
    def _setup_return_button(self):
        """Настройка кнопки возврата"""
        try:
            return_unpressed = "UI/ui_sprites/close_button_unpressed.png"
            return_pressed = "UI/ui_sprites/close_button_pressed.png"
            
            self.return_button = Button(
                0, 0,
                return_unpressed,
                return_pressed,
                callback=self._on_return_click,
                scale=2.0
            )
        except (pygame.error, FileNotFoundError) as e:
            print(f"Error loading return button sprites: {e}")
            self.return_button = None
            
    def _center_elements(self):
        """Центрирование элементов"""
        self.title_rect = self.title_text.get_rect(
            centerx=WINDOW_WIDTH // 2,
            top=50
        )
        
        self.volume_label_rect = self.volume_label.get_rect(
            centerx=WINDOW_WIDTH // 2,
            top=self.title_rect.bottom + 50
        )
        
        self.slider_rect.centerx = WINDOW_WIDTH // 2
        self.slider_rect.top = self.volume_label_rect.bottom + 30
        
        if self.return_button:
            self.return_button.rect.centerx = WINDOW_WIDTH // 2
            self.return_button.rect.bottom = WINDOW_HEIGHT - 50
            
    def _on_return_click(self):
        """Обработка нажатия на кнопку возврата"""
        return ACTION_CLOSE_SETTINGS
        
    def handle_events(self, events):
        """Обработка событий"""
        for event in events:
            # Обработка событий для кнопки возврата
            if self.return_button:
                action = self.return_button.handle_event(event)
                if action:
                    return action
                    
            # Обработка событий для слайдера громкости
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
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
                if event.button == 1:
                    self.is_dragging = False
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.is_dragging and self.audio_manager:
                    rel_x = event.pos[0] - self.slider_rect.left
                    new_volume = max(0.0, min(1.0, rel_x / self.slider_rect.width))
                    self.audio_manager.set_volume(new_volume)
                    
        return None
        
    def update(self, dt):
        """Обновление состояния меню"""
        pass
        
    def draw(self, surface):
        """Отрисовка меню"""
        surface.fill(self.background_color)
        
        # Отрисовка заголовка
        surface.blit(self.title_text, self.title_rect)
        
        # Отрисовка подписи для слайдера громкости
        surface.blit(self.volume_label, self.volume_label_rect)
        
        # Отрисовка слайдера громкости
        pygame.draw.rect(surface, (100, 100, 100), self.slider_rect)
        
        # Отрисовка заполненной части слайдера
        if self.audio_manager:
            filled_rect = pygame.Rect(
                self.slider_rect.left,
                self.slider_rect.top,
                self.slider_rect.width * self.audio_manager.get_volume(),
                self.slider_rect.height
            )
            pygame.draw.rect(surface, (200, 200, 200), filled_rect)
        
            # Расчет позиции ручки слайдера
            handle_pos = (
                self.slider_rect.left + self.audio_manager.get_volume() * self.slider_rect.width,
                self.slider_rect.centery
            )
            pygame.draw.circle(surface, (255, 255, 255), handle_pos, self.slider_handle_radius)
        
        if self.return_button:
            self.return_button.draw(surface)