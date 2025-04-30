import pygame
import sys
from utils import load_sprite
from player import Player
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from camera import Camera
from enemy import Slime
from weapon import RangeWeapon, MeleeWeapon, Projectile
from UI.button import Button # Import Button

# Simple GameState container (can be expanded)
class GameState:
    def __init__(self, player, enemies, projectiles):
        self.player = player
        self.enemies = enemies
        self.projectiles = projectiles

class Game:
    def __init__(self):
        # Initialization handled by GameController now
        # self._init_pygame()
        # self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        # self.clock = pygame.time.Clock() # Controller handles clock
        
        self.background = load_sprite("grass", False)
        self.background_width = self.background.get_width()
        self.background_height = self.background.get_height()
        self.scaled_background = None # Cache for scaled background
        self.last_camera_zoom = None  # To detect zoom changes
    
        self.player = Player(position=(400, 300))
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.enemies = []
        self.projectiles = [] # Initialize projectile list

        # Create game state object
        self.game_state = GameState(self.player, self.enemies, self.projectiles)

        # Pause State
        self.is_paused = False
        self._setup_pause_button()
        self._setup_resume_button()
        self._setup_pause_overlay_elements()

        # Initial setup (moved from old main_loop)
        self._spawn_initial_entities()

    def _setup_pause_button(self):
        try:
            pause_sprite_path = "UI/ui_sprites/pause_button.png"
            # Load once to get dimensions
            temp_pause_img = pygame.image.load(pause_sprite_path)
            btn_width, btn_height = temp_pause_img.get_size()
            
            # Position top-right
            pause_x = WINDOW_WIDTH - btn_width - 10 # 10px padding
            pause_y = 10
            
            # Create button using the same sprite for both states
            self.pause_button = Button(
                pause_x, 
                pause_y, 
                pause_sprite_path, 
                pause_sprite_path, # Use same path for pressed state
                callback=self._toggle_pause
            )
        except pygame.error as e:
            print(f"Error loading pause button sprite: {e}")
            self.pause_button = None # Handle gracefully if sprite is missing
        except FileNotFoundError:
            print(f"Error: Pause button sprite not found at {pause_sprite_path}")
            self.pause_button = None
            
    def _setup_resume_button(self):
        """Sets up the Resume button for the pause menu."""
        self.resume_button = None # Initialize as None
        try:
            resume_unpressed_path = "UI/ui_sprites/resume_button_unpressed.png"
            resume_pressed_path = "UI/ui_sprites/resume_button_pressed.png"
            
            # Define text properties
            button_text = "RESUME"
            text_font_size = 28 # Adjust size as needed
            text_color = (255, 255, 255) # White
            
            # Create button instance with text
            self.resume_button = Button(
                0, 0, # Placeholder position (will be set later)
                resume_unpressed_path, 
                resume_pressed_path, 
                callback=self._toggle_pause, # Resume = toggle pause off
                text=button_text,
                font_size=text_font_size,
                font_color=text_color,
                scale=5.0 # Make button 5x bigger
            )
        except pygame.error as e:
            print(f"Error loading resume button sprite: {e}")
        except FileNotFoundError:
            print(f"Error: Resume button sprite not found at {resume_unpressed_path} or {resume_pressed_path}")
            
    def _toggle_pause(self):
        self.is_paused = not self.is_paused
        print(f"Game Paused: {self.is_paused}") # Debug message

    def _setup_pause_overlay_elements(self):
        """Pre-render elements needed for the pause overlay."""
        # Font Loading
        try:
            self.pause_font = pygame.font.Font(None, 74) # Use default font, size 74
        except pygame.error:
            self.pause_font = pygame.font.SysFont('arial', 60) # Fallback font
            
        # Text Rendering
        self.paused_text_surface = self.pause_font.render(
            "PAUSED", True, (255, 255, 255) # White text
        )
        # Get screen dimensions (assuming display mode is set by controller)
        screen_rect = pygame.display.get_surface().get_rect() 
        self.paused_text_rect = self.paused_text_surface.get_rect(
            center=screen_rect.center
        )
        
        # Overlay Surface
        overlay_color = (0, 0, 0, 150) # Black with alpha
        self.pause_overlay_surface = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        self.pause_overlay_surface.fill(overlay_color)
        
        # --- Position Resume Button --- #
        if self.resume_button:
            # Center the button horizontally with the text, place below text
            button_rect = self.resume_button.rect
            button_x = self.paused_text_rect.centerx - button_rect.width // 2
            button_y = self.paused_text_rect.bottom + 20 # 20px padding below text
            self.resume_button.rect.topleft = (button_x, button_y)
        # ---------------------------- #

    def _spawn_initial_entities(self):
        # Spawn initial enemies, setup player weapon, etc.
        self._spawn_enemy(enemy_type='Slime', position=(420, 350))
        self._spawn_enemy(enemy_type='Slime', position=(450, 350))
        self.player.pickup_weapon('starter_sword')

    # Removed main_loop - Controller handles the loop
    # def main_loop(self):
    #     ...
        
    # Removed _init_pygame - Controller handles init
    # def _init_pygame(self):
    #     ...

    # Renamed _handle_input to handle_events
    def handle_events(self, events):
        # --- Update Pause Button Rect for Collision --- #
        # Calculate the current screen rect for the button based on zoom
        current_button_rect = None
        if self.pause_button and self.pause_button.unpressed_sprite:
            original_sprite = self.pause_button.unpressed_sprite
            original_width, original_height = original_sprite.get_size()
            zoom = self.camera.zoom
            scale_factor = zoom * 2
            scaled_width = max(1, int(original_width * scale_factor))
            scaled_height = max(1, int(original_height * scale_factor))
            padding = 10
            scaled_x = WINDOW_WIDTH - scaled_width - padding
            scaled_y = padding
            # Update the button's internal rect (important for its drawing/internal logic)
            self.pause_button.rect.topleft = (scaled_x, scaled_y)
            self.pause_button.rect.size = (scaled_width, scaled_height)
            # Store the calculated rect for collision detection below
            current_button_rect = self.pause_button.rect
        # ------------------------------------------- #

        for event in events:
            # 1. Handle explicit pause toggles first (Escape key)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._toggle_pause()
                    continue # Consumed

            # 2. Check if event interacts with the pause button
            event_consumed_by_button = False
            if self.pause_button and current_button_rect:
                # Check if the event's position is relevant (for mouse events)
                mouse_over_button = False
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    mouse_over_button = current_button_rect.collidepoint(event.pos)
                
                # Pass relevant events to the button if the mouse is over it or if it's a MOUSEBUTTONUP event 
                # that needs to be processed regardless of current mouse position (to handle clicks started on button)
                if mouse_over_button or (event.type == pygame.MOUSEBUTTONUP and self.pause_button.is_pressed):
                    action = self.pause_button.handle_event(event)
                    if action is not None: # Button performed its action (callback was called)
                         # _toggle_pause doesn't return anything, 
                         # but we check if *any* action was returned in case Button class changes.
                         # The main goal is consuming the event if the button handled it.
                         event_consumed_by_button = True 
                    elif event.type == pygame.MOUSEBUTTONDOWN and mouse_over_button:
                        # If it was a MOUSEBUTTONDOWN on the button, consume it even if no action 
                        # was returned immediately, as the button is now in a pressed state.
                        event_consumed_by_button = True
                        
            # If the button handled the event, skip further processing for this event
            if event_consumed_by_button:
                continue

            # 2.5 Handle Resume button click specifically WHEN PAUSED
            event_consumed_by_resume_button = False
            if self.is_paused and self.resume_button:
                # Check if mouse is over the resume button
                mouse_over_resume_button = False
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                     # Use the button's own rect for collision
                     mouse_over_resume_button = self.resume_button.rect.collidepoint(event.pos)
                
                # Pass relevant events if mouse is over, or if it's a MOUSEBUTTONUP after a press
                if mouse_over_resume_button or (event.type == pygame.MOUSEBUTTONUP and self.resume_button.is_pressed):
                    action = self.resume_button.handle_event(event)
                    if action is not None: # Callback triggered
                        event_consumed_by_resume_button = True
                    elif event.type == pygame.MOUSEBUTTONDOWN and mouse_over_resume_button:
                        # Consume the MOUSEBUTTONDOWN on the button itself
                        event_consumed_by_resume_button = True
                        
            # If the resume button handled the event, skip further processing
            if event_consumed_by_resume_button:
                continue

            # 3. Handle other game events only if NOT paused
            if not self.is_paused:
                # Check for player input events (e.g., clicks not handled by the button)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.player.handle_input([event], self.camera, self.game_state)
                # elif event.type == pygame.KEYDOWN: # Example for other inputs
                #     self.player.handle_input([event], self.camera, self.game_state)

        # Continuous input (like movement) is handled in player.update
        
    # Renamed _process_game_logic to update
    def update(self, dt):
        # --- Skip updates if paused --- #
        if self.is_paused:
            return 
        # ------------------------------ #
        
        # Update player (passes dt, camera, game_state)
        self.player.update(dt, self.camera, self.game_state)
        
        # Update camera based on player position (AFTER player update)
        self.camera.update(self.player)

        # --- Stop OTHER updates if player is dying --- 
        if self.player.is_dying:
            return # Skip enemy/projectile updates
        # -------------------------------------------
        
        # --- Enemy Updates & Cleanup --- 
        for enemy in self.enemies[:]: # Iterate copy for safe removal
            enemy.update(dt) # Enemy update now takes dt only
            if enemy.should_be_removed:
                self.enemies.remove(enemy)
        # -------------------------------

        # --- Projectile Updates & Cleanup --- 
        for proj in self.projectiles[:]: # Iterate copy
            proj.update(dt, self.game_state)
            if proj.should_be_removed:
                self.projectiles.remove(proj)
        # -------------------------------------
        
    def _spawn_enemy(self, enemy_type: str, position: tuple):
        if enemy_type.lower() == 'slime':
            enemy = Slime(position, target=self.player)
            self.enemies.append(enemy)
            print("Slime created")
    
    # Renamed _draw to draw, takes surface
    def draw(self, surface):
        self._draw_background(surface) # Pass surface to background drawing
        
        # --- Determine objects to render --- 
        render_objects = [] 
        if not self.player.is_dying:
            render_objects.extend(self.enemies)
            render_objects.extend(self.projectiles)
            # Sort enemies and projectiles by y-coordinate for draw order
            render_objects.sort(key=lambda obj: obj.position.y)
        # -----------------------------------
        
        # Draw enemies and projectiles
        for obj in render_objects:
            obj.draw(surface, self.camera)
            
        # Draw the player (which includes the weapon) last, so it's on top
        self.player.draw(surface, self.camera)
        
        # Draw HUD (health bar) always, on top of everything
        self._draw_player_hud(surface) # Pass surface to HUD drawing
        
        # --- Draw Pause Button (Scaled with Camera Zoom) --- #
        if self.pause_button and self.pause_button.unpressed_sprite: # Check if button and sprite exist
            # Get original sprite and camera zoom
            original_sprite = self.pause_button.unpressed_sprite # Use unpressed sprite for original size
            original_width, original_height = original_sprite.get_size()
            zoom = self.camera.zoom
            
            # Calculate scaled dimensions (ensure minimum size of 1x1)
            scale_factor = zoom * 2 # Apply extra scaling factor
            scaled_width = max(1, int(original_width * scale_factor))
            scaled_height = max(1, int(original_height * scale_factor))
            
            # Scale the sprite (do this every frame)
            scaled_sprite = pygame.transform.scale(original_sprite, (scaled_width, scaled_height))
            
            # Calculate top-left position to keep top-right corner fixed
            padding = 10
            scaled_x = WINDOW_WIDTH - scaled_width - padding
            scaled_y = padding
            
            # Draw the scaled sprite
            surface.blit(scaled_sprite, (scaled_x, scaled_y))
            
            # We draw it manually, so don't call button.draw()
            # self.pause_button.draw(surface)
            
        # --- Draw Pause Overlay --- #
        if self.is_paused:
            self._draw_pause_overlay(surface)
            
        # pygame.display.update() # Controller handles update

    # Modified _draw_background to accept surface
    def _draw_background(self, surface):
        """
        Draws the background tiles, scaled and positioned correctly according to the camera zoom.
        Calculates the visible world area and draws only the necessary tiles.
        """
        surface.fill((0, 0, 0)) # Clear screen
        
        zoom = self.camera.zoom
        # --- Check if background needs rescaling --- 
        if zoom != self.last_camera_zoom or self.scaled_background is None:
            scaled_bg_width = int(self.background_width * zoom)
            scaled_bg_height = int(self.background_height * zoom)
            if scaled_bg_width > 0 and scaled_bg_height > 0:
                print(f"Rescaling background for zoom: {zoom}") # Debug print
                self.scaled_background = pygame.transform.scale(self.background, (scaled_bg_width, scaled_bg_height))
                self.last_camera_zoom = zoom
            else:
                # Handle invalid scale size (e.g., zoom too small)
                self.scaled_background = None 
        # -----------------------------------------

        if self.scaled_background is None: # If scaling failed or zoom is 0
            return # Don't draw background

        inv_zoom = 1.0 / zoom
        
        # Calculate the visible world area
        world_view_width = self.camera.width * inv_zoom
        world_view_height = self.camera.height * inv_zoom
        world_view_left = self.camera.camera.x
        world_view_top = self.camera.camera.y
        world_view_rect = pygame.Rect(world_view_left, world_view_top, world_view_width, world_view_height)

        # Use the cached scaled background dimensions
        scaled_bg_width = self.scaled_background.get_width()
        scaled_bg_height = self.scaled_background.get_height()

        # Calculate the range of tiles needed
        start_col = int(world_view_left // self.background_width)
        end_col = int((world_view_left + world_view_width) // self.background_width) + 1
        start_row = int(world_view_top // self.background_height)
        end_row = int((world_view_top + world_view_height) // self.background_height) + 1

        # Draw the necessary tiles
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                # World position of the top-left corner of the tile
                tile_world_x = col * self.background_width
                tile_world_y = row * self.background_height
                
                # Screen position calculation (similar to camera.apply)
                screen_x = (tile_world_x - world_view_left) * zoom
                screen_y = (tile_world_y - world_view_top) * zoom
                
                surface.blit(self.scaled_background, (int(screen_x), int(screen_y)))

    # Modified _draw_player_hud to accept surface
    def _draw_player_hud(self, surface):
        """Draws the player's health bar in the top-left corner."""
        BAR_WIDTH = 200
        BAR_HEIGHT = 20
        BAR_X = 10
        BAR_Y = 10
        
        if self.player.max_hp <= 0: return # Avoid division by zero if max_hp is invalid
        
        hp_ratio = max(0, self.player.hp / self.player.max_hp)
        
        bg_color = (128, 0, 0) # Dark Red
        fg_color = (0, 200, 0) # Green
        border_color = (255, 255, 255) # White border
        
        bg_rect = pygame.Rect(BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT)
        
        fg_rect_width = int(BAR_WIDTH * hp_ratio)
        fg_rect = pygame.Rect(BAR_X, BAR_Y, fg_rect_width, BAR_HEIGHT)
        
        # Draw background
        pygame.draw.rect(surface, bg_color, bg_rect)
        # Draw foreground
        pygame.draw.rect(surface, fg_color, fg_rect)
        # Draw border
        pygame.draw.rect(surface, border_color, bg_rect, 2) # Border thickness 2

    def _draw_pause_overlay(self, surface):
        """Draws the pre-rendered semi-transparent overlay and PAUSED text."""
        # Blit the pre-rendered overlay surface
        surface.blit(self.pause_overlay_surface, (0, 0))
        # Blit the pre-rendered text surface
        surface.blit(self.paused_text_surface, self.paused_text_rect)
        # Draw the resume button if it exists
        if self.resume_button:
            self.resume_button.draw(surface)