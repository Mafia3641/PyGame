import pygame
import sys
from UI.button import Button
# Assuming constants.py is in the Scripts folder or accessible
# Adjust the path if necessary
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts'))
from constants import WINDOW_WIDTH, WINDOW_HEIGHT

# --- Action Constants --- #
ACTION_START_GAME = 'start_game'
ACTION_OPEN_SETTINGS = 'open_settings'
ACTION_EXIT = 'exit'

class MainMenu:
    def __init__(self):
        self.background_color = (255, 255, 255) # White background for now
        self.buttons = []
        self._setup_buttons()

    def _setup_buttons(self):
        # --- Button Callbacks --- #
        def start_game_callback():
            print("Start Game button clicked!")
            return ACTION_START_GAME
        
        def open_settings_callback():
            print("Settings button clicked!")
            return ACTION_OPEN_SETTINGS

        def exit_callback():
            print("Exit button clicked!")
            return ACTION_EXIT
            
        # --- Load Sprites (Paths relative to project root) --- #
        # Center Buttons
        try:
            start_unpressed = "UI/ui_sprites/play_button_unpressed.png"
            start_pressed = "UI/ui_sprites/play_button_pressed.png"
            settings_unpressed = "UI/ui_sprites/settings_button_unpressed.png"
            settings_pressed = "UI/ui_sprites/settings_button_pressed.png"
            exit_unpressed = "UI/ui_sprites/close_button_unpressed.png"
            exit_pressed = "UI/ui_sprites/close_button_pressed.png"

            # Get sprite dimensions for positioning
            temp_start_img = pygame.image.load(start_unpressed)
            btn_width, btn_height = temp_start_img.get_size()
            
            temp_exit_img = pygame.image.load(exit_unpressed)
            exit_btn_width, exit_btn_height = temp_exit_img.get_size()

        except pygame.error as e:
            print(f"Error loading button sprites: {e}")
            print("Please ensure button sprite files exist in UI/ui_sprites/")
            # Use placeholder rects if sprites fail to load?
            # For now, it will likely crash if sprites are missing.
            sys.exit(1) # Exit if essential sprites are missing
            
        spacing = 20 # Vertical space between center buttons
        
        # --- Start Button Positioning (Center Screen) --- #
        start_center_x = (WINDOW_WIDTH - btn_width) // 2
        start_center_y = (WINDOW_HEIGHT - btn_height) // 2
        self.start_button = Button(start_center_x, start_center_y, start_unpressed, start_pressed, start_game_callback)

        # --- Settings Button Positioning (Left Side, Vertical Center) --- #
        settings_x = 10 # 10px padding from left edge
        settings_center_y = (WINDOW_HEIGHT - btn_height) // 2 # Same vertical center as Start
        self.settings_button = Button(settings_x, settings_center_y, settings_unpressed, settings_pressed, open_settings_callback)
        
        # --- Top-right Exit Button --- #
        exit_x = WINDOW_WIDTH - exit_btn_width - 10 # 10px padding from right
        exit_y = 10 # 10px padding from top
        self.exit_button = Button(exit_x, exit_y, exit_unpressed, exit_pressed, exit_callback)

        self.buttons.extend([self.start_button, self.settings_button, self.exit_button])

    def handle_events(self, events):
        action_taken = None
        for event in events:
            for button in self.buttons:
                action = button.handle_event(event) # Button still handles one event at a time
                if action:
                    action_taken = action # Store the action
                    break # Stop processing this event for other buttons
            if action_taken: # If an action was taken for this event, stop processing other events
                break
        return action_taken # Return the first action detected from the list

    def update(self, dt):
        # Main menu might not need updates unless animated
        pass

    def draw(self, surface):
        surface.fill(self.background_color)
        for button in self.buttons:
            button.draw(surface) 