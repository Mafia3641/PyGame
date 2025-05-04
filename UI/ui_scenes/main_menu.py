import pygame
import sys
from UI.button import Button
# Assuming constants.py is in the Scripts folder or accessible
# Adjust the path if necessary
import os
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')) # Removed redundant path modification
# Import specific constants relative to project root (added by main.py)
from Scripts.constants import PLAY_BUTTON_POSITION, SETTINGS_BUTTON_POSITION, EXIT_BUTTON_POSITION

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
            # print("Start Game button clicked!")
            return ACTION_START_GAME
        
        def open_settings_callback():
            # print("Settings button clicked!")
            return ACTION_OPEN_SETTINGS

        def exit_callback():
            # print("Exit button clicked!")
            return ACTION_EXIT
            
        # --- Define Scale Factor ---
        button_scale = 2.0 

        # --- Load Sprite Paths --- #
        # (No need to load images just for size calculation anymore)
        start_unpressed = "UI/ui_sprites/play_button_unpressed.png"
        start_pressed = "UI/ui_sprites/play_button_pressed.png"
        settings_unpressed = "UI/ui_sprites/settings_button_unpressed.png"
        settings_pressed = "UI/ui_sprites/settings_button_pressed.png"
        exit_unpressed = "UI/ui_sprites/close_button_unpressed.png"
        exit_pressed = "UI/ui_sprites/close_button_pressed.png"

        # --- Instantiate Buttons using Constant Positions --- #
        try:
            self.start_button = Button(
                PLAY_BUTTON_POSITION[0], PLAY_BUTTON_POSITION[1], 
                start_unpressed, start_pressed, start_game_callback, 
                scale=button_scale
            )
            self.settings_button = Button(
                SETTINGS_BUTTON_POSITION[0], SETTINGS_BUTTON_POSITION[1], 
                settings_unpressed, settings_pressed, open_settings_callback, 
                scale=button_scale
            )
            self.exit_button = Button(
                EXIT_BUTTON_POSITION[0], EXIT_BUTTON_POSITION[1], 
                exit_unpressed, exit_pressed, exit_callback, 
                scale=button_scale
            )
        except pygame.error as e:
            # print(f"Error loading button sprites during instantiation: {e}")
            # Decide how to handle missing sprites - exit or use placeholders?
            sys.exit(1) 
        except FileNotFoundError as e:
             # print(f"Error: Button sprite not found during instantiation: {e}")
             sys.exit(1)

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