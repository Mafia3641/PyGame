import pygame
import sys

from Scripts.game import Game
from UI.ui_scenes.main_menu import MainMenu, ACTION_START_GAME, ACTION_OPEN_SETTINGS, ACTION_EXIT
from UI.ui_scenes.settings_menu import SettingsMenu, ACTION_CLOSE_SETTINGS
from UI.ui_scenes.weapon_selection_menu import WeaponSelectionMenu, ACTION_START_MELEE, ACTION_START_RANGED
from Scripts.constants import WINDOW_WIDTH, WINDOW_HEIGHT, ACTION_NEW_GAME
from Scripts.game_states import (
	STATE_MAIN_MENU, STATE_SETTINGS_MENU, STATE_GAMEPLAY, 
	STATE_EXIT, STATE_GO_TO_MENU, STATE_WEAPON_SELECTION
)
from Scripts.audio_manager import AudioManager


class GameController:
	"""Основной класс для управления игровыми сценами и состояниями"""
	def __init__(self):
		"""Инициализация игры"""
		pygame.init()
		self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption("Terra - Main Menu")
		
		self.clock = pygame.time.Clock()
		self.current_state = STATE_MAIN_MENU
		self.active_scene = MainMenu() 
		self.settings_menu = None
		self.weapon_selection_menu = None
		self.game_instance = None
		
		self.audio_manager = AudioManager()
		self.audio_manager.play_menu_music()

	def run(self):
		while self.current_state != STATE_EXIT:
			dt = self.clock.tick(60) / 1000
			
			events = pygame.event.get()
			action = None
			
			for event in events:
				if event.type == pygame.QUIT:
					self.current_state = STATE_EXIT
					break
					
			if self.current_state == STATE_EXIT:
				break
				
			if self.active_scene:
				if self.current_state == STATE_GAMEPLAY:
					action = self.active_scene.handle_events(events) 
				else:
					action = self.active_scene.handle_events(events)
			
			if action:
				# Обработка действий
				self._handle_action(action)
			
			if self.active_scene and self.current_state != STATE_EXIT:
				# Обновление сцены
				self.active_scene.update(dt)

			if self.active_scene and self.current_state != STATE_EXIT:
				# Отрисовка сцены
				self.active_scene.draw(self.screen)
				
			pygame.display.update()
		
		self.audio_manager.stop_music()
		pygame.quit()
		sys.exit()

	def _handle_action(self, action):
		"""Обработка действий"""
		if action == ACTION_START_GAME:
			if not self.weapon_selection_menu:
				self.weapon_selection_menu = WeaponSelectionMenu()
				self.weapon_selection_menu.set_audio_manager(self.audio_manager)
			self.active_scene = self.weapon_selection_menu
			self.current_state = STATE_WEAPON_SELECTION
			pygame.display.set_caption("Terra - Choose Weapon")

		elif action == ACTION_START_MELEE or action == ACTION_START_RANGED:
			weapon_type = 'melee' if action == ACTION_START_MELEE else 'ranged'
			self.active_scene = Game(starting_weapon_type=weapon_type)
			self.active_scene.set_audio_manager(self.audio_manager)
			pygame.display.set_caption("Terra")
			self.current_state = STATE_GAMEPLAY
			self.audio_manager.play_game_music()

		elif action == ACTION_OPEN_SETTINGS:
			if not self.settings_menu:
				self.settings_menu = SettingsMenu()
				self.settings_menu.set_audio_manager(self.audio_manager)
			self.active_scene = self.settings_menu
			self.current_state = STATE_SETTINGS_MENU
			pygame.display.set_caption("Terra - Settings")
		
		elif action == ACTION_CLOSE_SETTINGS:
			self.active_scene = MainMenu()
			self.current_state = STATE_MAIN_MENU
			pygame.display.set_caption("Terra - Main Menu")
		
		elif action == ACTION_EXIT:
			self.current_state = STATE_EXIT
		
		elif action == STATE_GO_TO_MENU:
			self.active_scene = MainMenu()
			self.active_scene.set_audio_manager(self.audio_manager)
			self.current_state = STATE_MAIN_MENU
			pygame.display.set_caption("Terra - Main Menu")
			self.audio_manager.play_menu_music()
		
		elif action == ACTION_NEW_GAME:
			if not self.weapon_selection_menu:
				self.weapon_selection_menu = WeaponSelectionMenu()
				self.weapon_selection_menu.set_audio_manager(self.audio_manager)
			self.active_scene = self.weapon_selection_menu
			self.current_state = STATE_WEAPON_SELECTION
			pygame.display.set_caption("Terra - Choose Weapon")
		else:
			pass