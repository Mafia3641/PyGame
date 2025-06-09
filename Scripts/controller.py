import pygame
import sys
import os

# Assuming this file is in Scripts/ and main.py added project root to path
from Scripts.game import Game
from UI.ui_scenes.main_menu import MainMenu, ACTION_START_GAME, ACTION_OPEN_SETTINGS, ACTION_EXIT
from UI.ui_scenes.settings_menu import SettingsMenu, ACTION_CLOSE_SETTINGS
from Scripts.constants import WINDOW_WIDTH, WINDOW_HEIGHT, ACTION_NEW_GAME
from Scripts.game_states import STATE_MAIN_MENU, STATE_SETTINGS_MENU, STATE_GAMEPLAY, STATE_EXIT
from Scripts.audio_manager import AudioManager

# Constants for game states
# STATE_MAIN_MENU = 'main_menu'
# STATE_SETTINGS_MENU = 'settings_menu'
# STATE_GAMEPLAY = 'gameplay'
# STATE_EXIT = 'exit'

# Define action constants (can be expanded)
# ACTION_PLAY = 'play'

class GameController:
	def __init__(self):
		pygame.init()
		# Initialize display mode *before* loading scenes/images
		self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption("Terra - Main Menu")
		
		# self.screen = None # Will be set by the first scene/game -> Now initialized above
		self.clock = pygame.time.Clock()
		self.current_state = STATE_MAIN_MENU
		self.active_scene = MainMenu() 
		self.settings_menu = None
		self.game_instance = None
		
		# Initialize audio manager
		self.audio_manager = AudioManager()
		# Start playing menu music
		self.audio_manager.play_menu_music()

	def run(self):
		while self.current_state != STATE_EXIT:
			dt = self.clock.tick(60) / 1000 # Limit FPS, get delta time
			
			events = pygame.event.get()
			action = None # Action to be returned by scene event handlers
			
			# --- Process events once --- #
			for event in events:
				if event.type == pygame.QUIT:
					self.current_state = STATE_EXIT
					break # Exit event loop
					
			if self.current_state == STATE_EXIT: # Check after quit event
				break
				
			# --- Let the active scene handle the events --- #
			if self.active_scene:
				if self.current_state == STATE_GAMEPLAY:
					# OLD: Ignores return value and sets action to None
					# self.active_scene.handle_events(events)
					# action = None 
					# NEW: Capture the potential action returned by the Game scene (e.g., ACTION_NEW_GAME)
					action = self.active_scene.handle_events(events) 
				else: # Handle events for menu states
					action = self.active_scene.handle_events(events)
					# Menu scenes might return an action (like 'start_game')
							
			# --- Process action from event handling (mainly for menus) --- #
			if action:
				self._handle_action(action)
			
			# --- Update the active scene --- #
			if self.active_scene and self.current_state != STATE_EXIT: # Don't update if exiting
				self.active_scene.update(dt)

			# --- Draw the active scene --- #
			# Screen is guaranteed to be initialized now
			if self.active_scene and self.current_state != STATE_EXIT:
				self.active_scene.draw(self.screen)
				
			pygame.display.update()
			
		# Stop music before quitting
		self.audio_manager.stop_music()
		pygame.quit()
		sys.exit()

	def _handle_action(self, action):
		# print(f"DEBUG: GameController._handle_action received action: {action}")
		if action == ACTION_START_GAME:
			# print("Transitioning to Gameplay State...")
			self.active_scene = Game()
			self.active_scene.set_audio_manager(self.audio_manager)
			pygame.display.set_caption("Terra")
			self.current_state = STATE_GAMEPLAY
			# Switch to game music
			self.audio_manager.play_game_music()
			# The Game class needs its own main_loop structure now
			# or we need to integrate its logic here.
			# For now, assuming Game() runs its own loop logic in update/draw
			# --> Let's adapt Game class later. For now, this will break the flow.
			# --> TEMPORARY FIX: Just start the game's loop directly.
			# self.active_scene.main_loop() 
			# self.current_state = STATE_EXIT # Exit after game loop finishes (temporary)
			# print("Game instance created. Need to adapt Game class loop.")
			# We will integrate Game's loop into the GameController later.
			# For now, let's just switch the scene/state.
		
		elif action == ACTION_OPEN_SETTINGS:
			if not self.settings_menu:
				self.settings_menu = SettingsMenu()
				# Pass audio manager to settings menu
				self.settings_menu.set_audio_manager(self.audio_manager)
			self.active_scene = self.settings_menu
			self.current_state = STATE_SETTINGS_MENU
			pygame.display.set_caption("Terra - Settings")
		
		elif action == ACTION_CLOSE_SETTINGS:
			self.active_scene = MainMenu()
			self.current_state = STATE_MAIN_MENU
			pygame.display.set_caption("Terra - Main Menu")
		
		elif action == ACTION_EXIT:
			# print("Exiting game.")
			self.current_state = STATE_EXIT
		
		# Handle New Game action
		elif action == ACTION_NEW_GAME:
			# print("Restarting Game State...")
			self.active_scene = Game()
			self.active_scene.set_audio_manager(self.audio_manager)
			pygame.display.set_caption("Terra")
			self.current_state = STATE_GAMEPLAY
			# Switch to game music
			self.audio_manager.play_game_music()
		else:
			# print(f"Warning: Unhandled action '{action}'")
			pass # Do nothing for unhandled actions 