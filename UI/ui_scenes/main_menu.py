import pygame
import sys
from UI.button import Button
# Assuming constants.py is in the Scripts folder or accessible
# Adjust the path if necessary
import os
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Scripts')) # Removed redundant path modification
# Import specific constants relative to project root (added by main.py)
from Scripts.constants import PLAY_BUTTON_POSITION, SETTINGS_BUTTON_POSITION, EXIT_BUTTON_POSITION, WINDOW_WIDTH, WINDOW_HEIGHT

# --- Action Constants --- #
ACTION_START_GAME = 'start_game'
ACTION_OPEN_SETTINGS = 'open_settings'
ACTION_EXIT = 'exit'

# --- OpenCV Video Background Imports ---
try:
    import cv2
    import numpy # moviepy often uses numpy arrays for frames
    OPENCV_AVAILABLE = True
except ImportError:
    print("Warning: OpenCV library (cv2) not found. Video background disabled. Install with 'pip install opencv-python'")
    OPENCV_AVAILABLE = False
# -----------------------------

class MainMenu:
    def __init__(self):
        self.background_color = (255, 255, 255) # White background for now
        self.buttons = []
        self._setup_buttons()

        # --- OpenCV Video Background Setup ---
        self.video_capture = None
        self.current_frame_surface = None

        if OPENCV_AVAILABLE:
            try:
                video_path = "Videos/background_1.mp4"
                self.video_capture = cv2.VideoCapture(video_path)
                if not self.video_capture.isOpened():
                    print(f"Error: Could not open video file: {video_path}")
                    self.video_capture = None
                else:
                    # Get video properties (optional, useful for debugging)
                    # width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                    # height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    # fps = self.video_capture.get(cv2.CAP_PROP_FPS)
                    # print(f"Video opened: {width}x{height} @ {fps:.2f} FPS")
                    pass # Successfully opened

            except Exception as e:
                print(f"Error initializing video capture: {e}")
                self.video_capture = None
        # -----------------------------

    def set_audio_manager(self, audio_manager):
        self.audio_manager = audio_manager

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
        # Update button states (e.g., for hover effects if any)
        # Currently, buttons don't have separate update logic

        # --- Update OpenCV Video Frame ---
        if self.video_capture:
            success, frame = self.video_capture.read()

            if not success:
                # End of video, loop back to the beginning
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                success, frame = self.video_capture.read()

            try:
                if success:
                    # --- Fit Inside Logic --- 
                    frame_h, frame_w = frame.shape[:2]
                    window_w, window_h = int(WINDOW_WIDTH), int(WINDOW_HEIGHT)
                    
                    # Calculate scale factor to fit within the window (preserving aspect ratio)
                    scale_w = window_w / frame_w
                    scale_h = window_h / frame_h
                    scale_factor = min(scale_w, scale_h)

                    # Calculate new dimensions and resize
                    new_w = int(frame_w * scale_factor)
                    new_h = int(frame_h * scale_factor)
                    scaled_frame = cv2.resize(frame, (new_w, new_h))

                    # --- End Fit Inside --- 

                    # OpenCV uses BGR, convert to RGB for Pygame
                    frame_rgb = cv2.cvtColor(scaled_frame, cv2.COLOR_BGR2RGB)
                    # Convert to Pygame surface (requires rotation/flip)
                    # OpenCV frames are typically (height, width, channels)
                    # We need to rotate and flip for correct pygame display
                    rotated_frame = numpy.rot90(frame_rgb)
                    flipped_frame = numpy.flipud(rotated_frame)
                    self.current_frame_surface = pygame.surfarray.make_surface(flipped_frame)
                else:
                    # If reading failed even after reset, stop trying
                    self.current_frame_surface = None
                    self.video_capture.release()
                    self.video_capture = None

            except Exception as e:
                print(f"Error processing video frame: {e}")
                self.current_frame_surface = None # Clear frame on error
                if self.video_capture: # Release capture on error
                    self.video_capture.release()

    def draw(self, surface):
        # --- Draw Video Background --- 
        if self.current_frame_surface:
            # Calculate position to center the scaled frame
            frame_rect = self.current_frame_surface.get_rect()
            screen_rect = surface.get_rect()
            top_left_x = (screen_rect.width - frame_rect.width) // 2
            top_left_y = (screen_rect.height - frame_rect.height) // 2
            surface.blit(self.current_frame_surface, (top_left_x, top_left_y))
        else:
            # Fallback background color if video fails or isn't available
            surface.fill((30, 30, 50))
        # ---------------------------

        # Draw buttons on top of the background
        for button in self.buttons:
            button.draw(surface) 