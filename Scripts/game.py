import pygame
import sys
import os
import random # Import random for upgrade selection
from utils import load_sprite
from player import Player
from constants import (WINDOW_WIDTH, WINDOW_HEIGHT, FPS, 
                     WAVE_INTRO_FADE_DURATION, WAVE_INTRO_HOLD_DURATION, 
                     WAVE_INTRO_MAX_FONT_SIZE, WAVE_INTRO_MIN_FONT_SIZE,
                     WAVE_INSCRIPTION_POSITION, SLIME_MAX_LEVEL,
                     GAME_OVER_ANIM_DURATION, GAME_OVER_MAX_FONT_SIZE,
                     GAME_OVER_MIN_FONT_SIZE, GAME_OVER_START_ALPHA, GAME_OVER_END_ALPHA,
                     NEW_GAME_BUTTON_DELAY, ACTION_NEW_GAME,
                     UPGRADE_CARD_SIZE, UPGRADE_CARD_Y_POS, UPGRADE_CARD_SPACING) # Import Upgrade UI constants
from camera import Camera
from enemy import Slime
from weapon import RangeWeapon, MeleeWeapon, Projectile
from UI.button import Button # Import Button
from Scripts.spawner import Spawner # Import Spawner
# Import Upgrade related modules
from UI.upgrade_box import UpgradeBox 
from Scripts.upgrades_list import get_upgrade_data, get_all_upgrade_names, UPGRADES

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
        
        # --- Spawner --- #
        self.spawner = Spawner(self.player, self.game_state)
        # --------------- #

        # Pause State
        self.is_paused = False
        self._setup_pause_button()
        self._setup_resume_button()
        self._setup_pause_overlay_elements()

        # Initial setup (moved from old main_loop)
        # self._spawn_initial_entities()

        # --- Wave Announcement State ---
        self.current_wave = 1
        self.is_showing_wave_intro = True
        self.wave_intro_timer = 0.0
        self.wave_intro_stage = 'fade_in' # Stages: 'fade_in', 'hold', 'fade_out'
        self.wave_font = None # Cache font object
        # -----------------------------

        # --- Game Over State ---
        self.is_game_over = False
        self.game_over_font = None
        self.game_over_timer = 0.0 # Timer for text animation
        self.new_game_button_appear_timer = 0.0 # Timer for button delay
        self.new_game_button = None # Button object placeholder
        # -----------------------

        # --- Upgrade State ---
        self.is_showing_upgrades = False
        self.available_upgrade_boxes = [] # List of UpgradeBox instances
        # Load all possible upgrade names once
        self.all_upgrade_names = get_all_upgrade_names() 
        # ---------------------

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
            # print(f"Error loading pause button sprite: {e}")
            self.pause_button = None # Handle gracefully if sprite is missing
        except FileNotFoundError:
            # print(f"Error: Pause button sprite not found at {pause_sprite_path}")
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
            # print(f"Error loading resume button sprite: {e}")
            pass # Continue without button if sprite load fails
        except FileNotFoundError:
            # print(f"Error: Resume button sprite not found at {resume_unpressed_path} or {resume_pressed_path}")
            pass # Continue without button if file not found
            
    def _toggle_pause(self):
        self.is_paused = not self.is_paused
        # print(f"Game Paused: {self.is_paused}") # Debug message

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

    # Remove initial entity spawning, handled by Spawner now
    # def _spawn_initial_entities(self):
    #     self._spawn_enemy(enemy_type='Slime', position=(420, 350))
    #     self._spawn_enemy(enemy_type='Slime', position=(450, 350))
    #     self.player.pickup_weapon('starter_sword')

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

        # --- Handle New Game Button Events (if game over) --- #
        if self.is_game_over and self.new_game_button:
            for event in events:
                action = self.new_game_button.handle_event(event)
                if action:
                    # print(f"DEBUG: Game.handle_events returning action: {action}") # Add Print
                    return action # Return the action immediately
            # If button exists but didn't handle any event, still consume events
            # so player can't interact with the game world underneath?
            # For now, let events pass through if button doesn't handle them.
        # -------------------------------------------------- #
        
        # --- Handle Upgrade Selection Events --- #
        if self.is_showing_upgrades:
            for event in events:
                for box in self.available_upgrade_boxes:
                    selected_upgrade_data = box.handle_event(event)
                    if selected_upgrade_data:
                        self._apply_upgrade(selected_upgrade_data)
                        self.is_showing_upgrades = False
                        self.available_upgrade_boxes = []
                        # Decide what happens next - start wave intro?
                        # print(f"Upgrade '{selected_upgrade_data.get('title')}' applied.")
                        # Start next wave intro immediately after upgrade
                        if self.spawner.is_active(): # Avoid intro if max level was reached
                            self._start_next_wave_intro()
                        return # Consume the click event
            # If showing upgrades, consume all other events?
            # return None # Prevents interaction with game behind upgrades
            # Let's allow pause for now
        # --------------------------------------- #

        # --- Normal Event Handling (if not game over or button didn't handle) --- #
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
        # --- Check for Game Over Trigger --- #
        if self.player.is_dying and not self.is_game_over:
            self.is_game_over = True
            self.game_over_timer = 0.0 # Reset animation timer
            # print("--- GAME OVER --- ") # Debug
        # -----------------------------------

        # --- Skip most updates if Game Over --- #
        if self.is_game_over:
            # print(f"DEBUG: In is_game_over block. Timer: {self.game_over_timer:.2f}") # Un-commented Print
            # Still update player death animation
            self.player.update(dt, self.camera, self.game_state)
            
            # Increment game over text animation timer (up to duration)
            if self.game_over_timer < GAME_OVER_ANIM_DURATION:
                self.game_over_timer += dt
            else:
                # Only start button timer AFTER text animation is done
                if self.new_game_button_appear_timer < NEW_GAME_BUTTON_DELAY:
                    self.new_game_button_appear_timer += dt
                    # print(f"DEBUG: Button appear timer: {self.new_game_button_appear_timer:.2f}") # Add Print
                
            # Check if button should appear (based on the new timer)
            # Ensure timer condition print uses the correct timer
            if self.new_game_button_appear_timer >= NEW_GAME_BUTTON_DELAY and self.new_game_button is None:
                # print(f"DEBUG: Button Timer condition met ({self.new_game_button_appear_timer:.2f} >= {NEW_GAME_BUTTON_DELAY}). Calling setup...") 
                self._setup_new_game_button()
                
            return # Skip other updates
        # -------------------------------------- #

        # --- Pause Game if showing Upgrades --- #
        if self.is_showing_upgrades:
            # We might want some animations for the boxes later,
            # but for now, just pause game logic.
            return # Skip normal update loop
        # -------------------------------------- #

        # --- Update Wave Intro Animation (if active) --- 
        if self.is_showing_wave_intro:
            self._update_wave_intro(dt)
        # ---------------------------------------------
        
        # --- Skip updates if paused --- #
        if self.is_paused:
            return 
        # ------------------------------ #
        
        # --- Spawner Update --- #
        self.spawner.update(dt)
        # -------------------- #
        
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
                # print(f"DEBUG: Enemy {id(enemy)} should be removed. Alive: {enemy.alive}, XP: {enemy.xp_reward}")
                # Removed XP granting here, now handled in enemy.die()
                self.enemies.remove(enemy)
        # -------------------------------

        # --- Check for Wave End based on Player Level --- #
        # Wave N ends when player reaches level N+1
        # Allow check even on the last wave (current_wave == SLIME_MAX_LEVEL)
        if self.player.current_level > self.current_wave and self.current_wave <= SLIME_MAX_LEVEL:
             self._end_wave()
        # ----------------------------------------------- #

        # --- Projectile Updates & Cleanup --- 
        for proj in self.projectiles[:]: # Iterate copy
            proj.update(dt, self.game_state)
            if proj.should_be_removed:
                self.projectiles.remove(proj)
        # -------------------------------------
        
    def _update_wave_intro(self, dt):
        """Updates the timer and state for the wave intro animation."""
        self.wave_intro_timer += dt
        total_fade_hold_duration = WAVE_INTRO_FADE_DURATION + WAVE_INTRO_HOLD_DURATION
        total_duration = WAVE_INTRO_FADE_DURATION * 2 + WAVE_INTRO_HOLD_DURATION

        if self.wave_intro_stage == 'fade_in':
            if self.wave_intro_timer >= WAVE_INTRO_FADE_DURATION:
                self.wave_intro_stage = 'hold'
                # Ensure timer doesn't overshoot into hold phase calculation
                # self.wave_intro_timer = WAVE_INTRO_FADE_DURATION 
        elif self.wave_intro_stage == 'hold':
            if self.wave_intro_timer >= total_fade_hold_duration:
                self.wave_intro_stage = 'fade_out'
                # Ensure timer doesn't overshoot into fade_out phase calculation
                # self.wave_intro_timer = total_fade_hold_duration 
        elif self.wave_intro_stage == 'fade_out':
            if self.wave_intro_timer >= total_duration:
                self.is_showing_wave_intro = False # Animation finished
                # print("Wave Intro Finished") # Debug

    def _end_wave(self):
        """Handles logic for ending the current wave and starting the next."""
        # print(f"--- Ending Wave {self.current_wave} --- ")
        
        # 1. Remove existing enemies (that aren't already dying)
        enemies_to_remove = [e for e in self.game_state.enemies if not e.dying]
        for enemy in enemies_to_remove:
            # print(f"Removing enemy {id(enemy)} at end of wave.")
            self.game_state.enemies.remove(enemy)
            
        # 2. Progress spawner to next enemy level
        self.spawner.next_wave()
        
        # 3. Check if spawner is still active (max level not reached)
        if self.spawner.is_active():
            # 4. Restore Player HP
            self.player.restore_hp()
            
            # 5. Trigger Upgrade Selection Screen
            self._show_upgrade_selection()
            
            # --- No longer starting wave intro here --- 
            # # 5. Increment Game's wave counter (for display/logic)
            # self.current_wave += 1 
            # print(f"--- Starting Wave {self.current_wave} --- ")
            # # 6. Start next wave intro animation
            # self.is_showing_wave_intro = True
            # self.wave_intro_timer = 0.0
            # self.wave_intro_stage = 'fade_in'
            # ------------------------------------------ #
        else:
             # print("--- Max enemy level reached. Spawning stopped. ---")
             # Optionally handle game win condition or further logic here
             pass # Add pass to maintain valid block after commenting print
             
    def _show_upgrade_selection(self):
        """Selects upgrades and sets up the display state."""
        self.is_showing_upgrades = True
        self.available_upgrade_boxes = [] # Clear previous boxes
        
        selected_names = self._select_upgrades() # Get 3 unique names
        if not selected_names:
            # print("Warning: Could not select any upgrades.")
            self.is_showing_upgrades = False # Skip showing if none selected
            self._start_next_wave_intro() # Start next wave anyway
            return

        num_cards = len(selected_names)
        total_width = num_cards * UPGRADE_CARD_SIZE[0] + (num_cards - 1) * UPGRADE_CARD_SPACING
        start_x = (WINDOW_WIDTH - total_width) // 2

        for i, name in enumerate(selected_names):
            upgrade_data = get_upgrade_data(name)
            if upgrade_data:
                card_x = start_x + i * (UPGRADE_CARD_SIZE[0] + UPGRADE_CARD_SPACING)
                card_y = UPGRADE_CARD_Y_POS
                box = UpgradeBox(upgrade_data, (card_x, card_y), UPGRADE_CARD_SIZE)
                self.available_upgrade_boxes.append(box)
            else:
                # print(f"Warning: Could not find data for upgrade '{name}'")
                pass # Silently skip if upgrade data missing
                
    def _select_upgrades(self, count=3):
        """Selects a number of unique upgrades from the available list."""
        available_count = len(self.all_upgrade_names)
        select_count = min(count, available_count) # Don't try to select more than available
        
        if select_count <= 0:
            return []
            
        try:
            return random.sample(self.all_upgrade_names, select_count)
        except ValueError as e:
            # print(f"Error selecting upgrades (not enough unique options?): {e}")
            # Fallback: return as many unique options as possible
            return random.sample(self.all_upgrade_names, available_count) 
            
    def _apply_upgrade(self, upgrade_data):
        """Applies the stats from the chosen upgrade to the player."""
        stats_to_apply = upgrade_data.get('stats', {})
        # print(f"Applying stats: {stats_to_apply}") # Debug
        
        for stat_name, value in stats_to_apply.items():
            if hasattr(self.player, stat_name):
                current_value = getattr(self.player, stat_name)
                # Basic handling for multipliers vs flat values
                if "mult" in stat_name:
                    # Handle potential mana multiplier
                    new_value = current_value * value
                    setattr(self.player, stat_name.replace('_mult', ''), new_value)
                    # print(f"  Applied {stat_name}: {current_value} -> {new_value}")
                    # Special case: If max_mana increased via multiplier, restore current mana
                    if 'max_mana' in stat_name:
                        self.player.current_mana = self.player.max_mana
                else:
                    new_value = current_value + value
                    setattr(self.player, stat_name, new_value)
                    # print(f"  Applied {stat_name}: {current_value} -> {new_value}")
                    # Special case: If max_hp or max_mana increased flat, restore current
                    if stat_name == 'max_hp':
                        self.player.hp = self.player.max_hp 
                    elif stat_name == 'max_mana':
                         self.player.current_mana = self.player.max_mana
            elif stat_name == 'attack_cooldown_mult': # Special case for weapon stats
                 if self.player.active_weapon and 'cooldown' in self.player.active_weapon.stats:
                     current_cooldown = self.player.active_weapon.stats['cooldown']
                     self.player.active_weapon.stats['cooldown'] *= value
                     # print(f"  Applied attack_cooldown_mult: {current_cooldown} -> {self.player.active_weapon.stats['cooldown']}")
                 else:
                    # print(f"  Warning: Player weapon or cooldown stat not found for {stat_name}")
                    pass
            else:
                # print(f"  Warning: Player attribute '{stat_name}' not found.")
                pass
                
    def _start_next_wave_intro(self):
        """Starts the intro animation for the next wave."""
        self.current_wave += 1 
        # print(f"--- Starting Wave {self.current_wave} --- ")
        self.is_showing_wave_intro = True
        self.wave_intro_timer = 0.0
        self.wave_intro_stage = 'fade_in'
    
    # Renamed _draw to draw, takes surface
    def draw(self, surface):
        self._draw_background(surface) # Pass surface to background drawing
        
        # --- Draw Game Objects --- (No longer conditional)
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
        # ------------------------------------------------- #
                
        # --- Draw Wave Intro (If active, drawn on top) ---
        if self.is_showing_wave_intro:
            self._draw_wave_intro(surface)
        # -------------------------------------------------- #
            
        # --- Draw Game Over (If active, drawn on top) ---
        if self.is_game_over:
            self._draw_game_over(surface)
            # Draw the New Game button if it exists
            if self.new_game_button:
                # print(f"DEBUG: Drawing new_game_button at {self.new_game_button.rect.topleft}") # Add Print
                self.new_game_button.draw(surface)
        # ------------------------------------------------ #

        # --- Draw Upgrade Boxes (If active, drawn on top) ---
        if self.is_showing_upgrades:
            for box in self.available_upgrade_boxes:
                box.draw(surface)
        # --------------------------------------------------- #

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
                # print(f"Rescaling background for zoom: {zoom}") # Debug print
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
        """Draws the player's health bar (top-left), mana bar (below HP), and XP bar (top-center)."""
        screen_width = surface.get_width()
        
        # --- Health Bar (Top-Left) --- #
        HP_BAR_WIDTH = 200
        HP_BAR_HEIGHT = 20
        HP_BAR_X = 10
        HP_BAR_Y = 10
        
        if self.player.max_hp > 0: # Avoid division by zero
            hp_ratio = max(0, self.player.hp / self.player.max_hp)
            
            hp_bg_color = (128, 0, 0) # Dark Red
            hp_fg_color = (0, 200, 0) # Green
            hp_border_color = (255, 255, 255) # White border
            
            hp_bg_rect = pygame.Rect(HP_BAR_X, HP_BAR_Y, HP_BAR_WIDTH, HP_BAR_HEIGHT)
            hp_fg_rect_width = int(HP_BAR_WIDTH * hp_ratio)
            hp_fg_rect = pygame.Rect(HP_BAR_X, HP_BAR_Y, hp_fg_rect_width, HP_BAR_HEIGHT)
            
            pygame.draw.rect(surface, hp_bg_color, hp_bg_rect)
            pygame.draw.rect(surface, hp_fg_color, hp_fg_rect)
            pygame.draw.rect(surface, hp_border_color, hp_bg_rect, 2) # Border thickness 2
        # ------------------------------ #

        # --- Mana Bar (Below HP Bar) --- #
        MANA_BAR_WIDTH = 180 # Slightly shorter than HP
        MANA_BAR_HEIGHT = 15 # Slightly thinner
        MANA_BAR_X = HP_BAR_X # Align with HP bar horizontally
        MANA_BAR_Y = HP_BAR_Y + HP_BAR_HEIGHT + 5 # Place below HP bar with padding
        
        if self.player.max_mana > 0: # Avoid division by zero
            mana_ratio = max(0, self.player.current_mana / self.player.max_mana)
            
            mana_bg_color = (0, 0, 100) # Dark Blue
            mana_fg_color = (0, 100, 255) # Bright Blue
            mana_border_color = (200, 200, 255) # Light Blue/White border
            
            mana_bg_rect = pygame.Rect(MANA_BAR_X, MANA_BAR_Y, MANA_BAR_WIDTH, MANA_BAR_HEIGHT)
            mana_fg_rect_width = int(MANA_BAR_WIDTH * mana_ratio)
            mana_fg_rect = pygame.Rect(MANA_BAR_X, MANA_BAR_Y, mana_fg_rect_width, MANA_BAR_HEIGHT)
            
            pygame.draw.rect(surface, mana_bg_color, mana_bg_rect)
            pygame.draw.rect(surface, mana_fg_color, mana_fg_rect)
            pygame.draw.rect(surface, mana_border_color, mana_bg_rect, 2) # Border thickness 2
        # ----------------------------- #

        # --- XP Bar (Top-Center) --- #
        XP_BAR_WIDTH = 300 # Make it wider than HP bar
        XP_BAR_HEIGHT = 15 # Make it slightly thinner
        XP_BAR_X = (screen_width - XP_BAR_WIDTH) // 2 # Center horizontally
        XP_BAR_Y = 10 # Align vertically with HP bar
        
        if self.player.xp_for_next_level > 0: # Avoid division by zero
            xp_ratio = max(0, self.player.current_xp / self.player.xp_for_next_level)

            xp_bg_color = (50, 50, 50) # Dark Grey
            xp_fg_color = (0, 180, 255) # Light Blue
            xp_border_color = (200, 200, 200) # Light Grey border
            
            xp_bg_rect = pygame.Rect(XP_BAR_X, XP_BAR_Y, XP_BAR_WIDTH, XP_BAR_HEIGHT)
            xp_fg_rect_width = int(XP_BAR_WIDTH * xp_ratio)
            xp_fg_rect = pygame.Rect(XP_BAR_X, XP_BAR_Y, xp_fg_rect_width, XP_BAR_HEIGHT)
            
            pygame.draw.rect(surface, xp_bg_color, xp_bg_rect)
            pygame.draw.rect(surface, xp_fg_color, xp_fg_rect)
            pygame.draw.rect(surface, xp_border_color, xp_bg_rect, 2) # Border thickness 2

            # Optional: Add Level Text near XP bar
            try:
                level_font = pygame.font.Font(None, 24) # Small font for level
                level_text = f"Level: {self.player.current_level}"
                level_surf = level_font.render(level_text, True, (255, 255, 255))
                level_rect = level_surf.get_rect(midtop=(xp_bg_rect.centerx, xp_bg_rect.bottom + 5)) # Place below the bar
                surface.blit(level_surf, level_rect)
            except pygame.error:
                # print("Warning: Could not load font for level text.") # Handle font loading error
                pass
        # --------------------------- #

    def _draw_pause_overlay(self, surface):
        """Draws the pre-rendered semi-transparent overlay and PAUSED text."""
        # Blit the pre-rendered overlay surface
        surface.blit(self.pause_overlay_surface, (0, 0))
        # Blit the pre-rendered text surface
        surface.blit(self.paused_text_surface, self.paused_text_rect)
        # Draw the resume button if it exists
        if self.resume_button:
            self.resume_button.draw(surface)

    def _draw_wave_intro(self, surface):
        """Draws the WAVE text animation based on the current stage and timer."""
        current_size = WAVE_INTRO_MIN_FONT_SIZE
        current_alpha = 0
        progress = 0.0
        total_fade_hold_duration = WAVE_INTRO_FADE_DURATION + WAVE_INTRO_HOLD_DURATION

        # --- Calculate Size and Alpha based on Stage --- #
        if self.wave_intro_stage == 'fade_in':
            progress = min(1.0, self.wave_intro_timer / WAVE_INTRO_FADE_DURATION)
            # Linear interpolation for size and alpha
            current_size = int(WAVE_INTRO_MIN_FONT_SIZE + (WAVE_INTRO_MAX_FONT_SIZE - WAVE_INTRO_MIN_FONT_SIZE) * progress)
            current_alpha = int(255 * progress)
        elif self.wave_intro_stage == 'hold':
            current_size = WAVE_INTRO_MAX_FONT_SIZE
            current_alpha = 255
        elif self.wave_intro_stage == 'fade_out':
            # Calculate progress relative to the start of the fade_out phase
            fade_out_timer = self.wave_intro_timer - total_fade_hold_duration
            progress = max(0.0, 1.0 - (fade_out_timer / WAVE_INTRO_FADE_DURATION))
            # Linear interpolation back down
            current_size = int(WAVE_INTRO_MIN_FONT_SIZE + (WAVE_INTRO_MAX_FONT_SIZE - WAVE_INTRO_MIN_FONT_SIZE) * progress)
            current_alpha = int(255 * progress)
        # ---------------------------------------------- #

        # Clamp alpha just in case
        current_alpha = max(0, min(255, current_alpha))
        # Ensure size is at least 1
        current_size = max(1, current_size)

        # --- Render and Draw Text --- #
        try:
            # Load font if size changed or not loaded yet
            # Basic caching - might need more robust font manager for many sizes
            if self.wave_font is None or self.wave_font.get_height() != current_size:
                 self.wave_font = pygame.font.Font(None, current_size) 
            
            wave_text = f"WAVE {self.current_wave}"
            text_surface = self.wave_font.render(wave_text, True, (255, 255, 255)) # White text
            text_surface.set_alpha(current_alpha)
            
            # Center the text based on the constant position
            text_rect = text_surface.get_rect(center=WAVE_INSCRIPTION_POSITION) # Use constant for center
            
            surface.blit(text_surface, text_rect)
        except pygame.error as e:
            # print(f"Error rendering wave intro text: {e}")
            # Fallback if font loading fails? For now, just print error.
            pass
        except AttributeError as e:
             # print(f"Error accessing wave font (likely not loaded yet): {e}")
             pass
        # ------------------------- #

    def _draw_game_over(self, surface):
        """Draws the GAME OVER text with fade-in animation."""
        # Calculate animation progress (0.0 to 1.0)
        progress = min(1.0, self.game_over_timer / GAME_OVER_ANIM_DURATION)
        
        # Define start values (80% of max/end)
        start_size = GAME_OVER_MAX_FONT_SIZE * 0.8
        start_alpha = GAME_OVER_END_ALPHA * 0.8
        
        # Interpolate size from 80% to 100%
        current_size = int(start_size + (GAME_OVER_MAX_FONT_SIZE - start_size) * progress)
        # Interpolate alpha from 80% to 100%
        current_alpha = int(start_alpha + (GAME_OVER_END_ALPHA - start_alpha) * progress)
        
        # Clamp alpha and ensure size is valid
        current_alpha = max(0, min(255, current_alpha))
        current_size = max(1, current_size)
        
        try:
            # Load font if size changed or not loaded yet
            if self.game_over_font is None or self.game_over_font.get_height() != current_size:
                self.game_over_font = pygame.font.Font(None, current_size) 
                
            text_surface = self.game_over_font.render("GAME OVER", True, (200, 0, 0)) # Dark Red
            text_surface.set_alpha(current_alpha) # Apply calculated alpha
            
            # Center the text on the screen
            screen_rect = surface.get_rect()
            text_rect = text_surface.get_rect(center=screen_rect.center)
            
            surface.blit(text_surface, text_rect)
        except pygame.error as e:
            # print(f"Error rendering GAME OVER text: {e}")
            pass
        except AttributeError as e:
            # print(f"Error accessing game over font (likely not loaded yet): {e}")
            pass

    def _setup_new_game_button(self):
        """Creates and positions the 'NEW GAME' button."""
        try:
            # Force using Play button sprites
            # print("DEBUG: Forcing use of Play button sprites for New Game button.")
            unpressed_path = "UI/ui_sprites/play_button_unpressed.png"
            pressed_path = "UI/ui_sprites/play_button_pressed.png"
            # Removed the check for specific new game sprites

            button_scale = 2.0 # Use a reasonable scale
            
            self.new_game_button = Button(
                0, 0, # Initial position, will be centered below text
                unpressed_path, 
                pressed_path, 
                callback=self._start_new_game, # Callback to signal controller
                # text="NEW GAME", # Optional text if sprites don't include it
                # font_size=24, 
                # font_color=(255, 255, 255),
                scale=button_scale
            )
            
            # Position the button below the game over text
            # Get screen center (assuming GAME OVER text is centered)
            screen_rect = pygame.display.get_surface().get_rect()
            game_over_text_center_y = screen_rect.centery 
            
            button_rect = self.new_game_button.rect
            button_x = screen_rect.centerx - button_rect.width // 2
            # Place it below the approximate position of GAME OVER text + some padding
            button_y = game_over_text_center_y + (GAME_OVER_MAX_FONT_SIZE // 2) + 50 
            self.new_game_button.rect.topleft = (button_x, button_y)
            
            # print(f"New Game button created at ({button_x}, {button_y})") # Debug
            
        except pygame.error as e:
            # print(f"Error loading new game button sprite: {e}")
            self.new_game_button = None # Ensure button is None if creation fails
        except FileNotFoundError as e:
            # print(f"Error: Button sprite file not found: {e}")
            self.new_game_button = None
            
        # print(f"DEBUG: _setup_new_game_button finished. self.new_game_button is {'set' if self.new_game_button else 'None'}.") # Add Print
            
    def _start_new_game(self):
        """Callback function for the New Game button."""
        print("New Game button clicked!") # Debug
        return ACTION_NEW_GAME # Signal the controller