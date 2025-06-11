import pygame
from UI.button import Button
from Scripts.constants import WINDOW_WIDTH, WINDOW_HEIGHT

ACTION_START_MELEE = 'start_melee'
ACTION_START_RANGED = 'start_ranged'

class WeaponSelectionMenu:
    def __init__(self):
        self._setup_buttons()
        self.title_font = pygame.font.Font(None, 74)
        self.title_surf = self.title_font.render("Choose your Weapon", True, (255, 255, 255))
        self.title_rect = self.title_surf.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT * 0.25))
        self.audio_manager = None

    def _setup_buttons(self):
        melee_button_pos = (WINDOW_WIDTH * 0.3, WINDOW_HEIGHT / 2)
        ranged_button_pos = (WINDOW_WIDTH * 0.7, WINDOW_HEIGHT / 2)

        def start_melee_callback():
            return ACTION_START_MELEE

        def start_ranged_callback():
            return ACTION_START_RANGED

        button_unpressed = "UI/ui_sprites/play_button_unpressed.png"
        button_pressed = "UI/ui_sprites/play_button_pressed.png"
        
        self.melee_button = Button(
            0, 0,
            button_unpressed, button_pressed, start_melee_callback,
            text="Melee", font_size=40, scale=3.0
        )
        self.melee_button.rect.center = melee_button_pos

        self.ranged_button = Button(
            0, 0,
            button_unpressed, button_pressed, start_ranged_callback,
            text="Ranged", font_size=40, scale=3.0
        )
        self.ranged_button.rect.center = ranged_button_pos

        self.buttons = [self.melee_button, self.ranged_button]

    def handle_events(self, events):
        for event in events:
            for button in self.buttons:
                action = button.handle_event(event)
                if action:
                    return action
        return None

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill((30, 30, 50))
        surface.blit(self.title_surf, self.title_rect)
        for button in self.buttons:
            button.draw(surface)
            
    def set_audio_manager(self, audio_manager):
        self.audio_manager = audio_manager 