import pygame
from pygame.math import Vector2

from utils import load_sprite
from constants import (SPEED, BASE_DAMAGE, INITIAL_XP_TO_LEVEL_UP, XP_LEVEL_MULTIPLIER,
                     BASE_MAX_MANA, BASE_PLAYER_HP)
from weapon import MeleeWeapon, RangeWeapon, Pistol
from game_object import GameObject
from weapon_stats import WEAPON_STATS
from camera import Camera


class Player(GameObject):
	"""Класс для управления игровым персонажем"""
	def __init__(self, position: tuple, starting_weapon_type: str):
		self.direction = Vector2(0, 0)
		self.speed = SPEED
		self.damage = BASE_DAMAGE
		self.max_hp = BASE_PLAYER_HP
		self.hp = self.max_hp
		self.max_mana = BASE_MAX_MANA
		self.current_mana = self.max_mana
		self.current_level = 1
		self.current_xp = 0
		self.xp_for_next_level = INITIAL_XP_TO_LEVEL_UP
		self.xp_multiplier = 1.0

		self.idle_sprites = [
			load_sprite('Player/Player_Idle/player_idle_1'),
			load_sprite('Player/Player_Idle/player_idle_2'),
			load_sprite('Player/Player_Idle/player_idle_3'),
			load_sprite('Player/Player_Idle/player_idle_4'),
			load_sprite('Player/Player_Idle/player_idle_5'),
			load_sprite('Player/Player_Idle/player_idle_6'),
		]
		self.move_sprites = [
			load_sprite('Player/Player_Move/player_move_1'),
			load_sprite('Player/Player_Move/player_move_2'),
			load_sprite('Player/Player_Move/player_move_3'),
			load_sprite('Player/Player_Move/player_move_4'),
			load_sprite('Player/Player_Move/player_move_5'),
			load_sprite('Player/Player_Move/player_move_6'),
		]
		self.death_sprites = [
			load_sprite('Player/Player_Die/player_die_1'),
			load_sprite('Player/Player_Die/player_die_2'),
			load_sprite('Player/Player_Die/player_die_3'),
		]
		# Инициализация переменных для анимации
		self.last_direction = Vector2(1, 0)
		self.current_sprite_index = 0
		self.current_animation = self.idle_sprites
		self.previous_animation = self.current_animation
		self.animation_speed = 0.5
		self.animation_timer = 0
		self.is_dying = False
		self.death_frame_index = 0
		self.death_timer = 0.0
		self.death_frame_duration = 0.4
		# Инициализация базовых переменных
		super().__init__(position, self.idle_sprites[0], Vector2(0))
		self.active_weapon = None
		# Выбор начального оружия
		if starting_weapon_type == 'melee':
			self.pickup_weapon('starter_sword')
		elif starting_weapon_type == 'ranged':
			self.pickup_weapon('pistol')
		else:
			self.pickup_weapon('pistol')
	
	def pickup_weapon(self, weapon_name: str):
		"""Выбор оружия"""
		if weapon_name not in WEAPON_STATS:
			raise ValueError(f"Unknown weapon requested: {weapon_name}")
		stats = WEAPON_STATS[weapon_name].copy()
		weapon_type = stats.get('type')
		if weapon_name == 'pistol':
			self.active_weapon = Pistol(owner=self)
			return
		# Общие аргументы для всех оружий
		common_args = {
			'owner': self,
			'offset': Vector2(stats['offset']),
			'stats': stats
		}
		if weapon_type == 'melee':
			attack_sprites = [
				stats['attack_sprite_pattern'].format(i)
				for i in range(1, stats['attack_sprite_count'] + 1)
			]
			melee_args = {
				'idle_sprite_name': stats['idle_sprite_name'],
				'attack_sprite_names': attack_sprites,
				'frame_duration': stats.get('frame_duration', 0.1)
			}
			self.active_weapon = MeleeWeapon(**common_args, **melee_args)
		
		elif weapon_type == 'range':
			range_args = {
				'weapon_idle_sprite': stats['weapon_idle_sprite'],
				'projectile_sprite_name': stats['projectile_sprite_name'],
			}
			self.active_weapon = RangeWeapon(**common_args, **range_args)
		
		else:
			raise ValueError(f"Unknown weapon type '{weapon_type}' in stats for {weapon_name}")
	
	def take_damage(self, amount):
		"""Получение урона"""
		if self.hp > 0 and not self.is_dying:
			self.hp -= amount

			if self.hp <= 0:
				self.hp = 0
				self.is_dying = True
				self.death_frame_index = 0
				self.death_timer = 0.0

				if self.death_sprites:
					self.sprite = self.death_sprites[0]
					self.rect.size = self.sprite.get_size()
	
	def gain_xp(self, amount):
		"""Получение опыта"""
		leveled_up = False

		if self.is_dying:
			return leveled_up
		
		self.current_xp += amount

		while self.current_xp >= self.xp_for_next_level:
			self.level_up()
			leveled_up = True
		return leveled_up
	
	def level_up(self):
		"""Повышение уровня"""
		self.current_xp -= self.xp_for_next_level
		self.current_level += 1
		self.xp_for_next_level = int(self.xp_for_next_level * XP_LEVEL_MULTIPLIER)
	
	def consume_mana(self, amount):
		"""Потребление маны"""
		if self.current_mana >= amount:
			self.current_mana -= amount
			return True
		return False
	
	def restore_mana(self, amount):
		"""Восстановление маны"""
		self.current_mana += amount
		if self.current_mana > self.max_mana:
			self.current_mana = self.max_mana
	
	def restore_hp(self):	
		"""Восстановление здоровья (и маны)"""
		self.hp = self.max_hp
		self.current_mana = self.max_mana = self.max_mana
	
	def handle_input(self, events, camera: Camera, game_state):
		"""Обработка ввода"""
		for event in events:
			if event.type == pygame.MOUSEBUTTONDOWN:
				if event.button == 1:
					if self.active_weapon and not self.is_dying:
						mouse_screen_pos = pygame.mouse.get_pos()
						mouse_world_pos = camera.screen_to_world(mouse_screen_pos)
						self.active_weapon.attack(mouse_world_pos, game_state)
	
	def update(self, dt, camera: Camera, game_state):
		"""Обновление состояния игрока"""
		if self.is_dying:
			self.velocity = Vector2(0, 0)
			self.death_timer += dt
			target_frame_index = int(self.death_timer // self.death_frame_duration)
			current_frame_index = min(target_frame_index, len(self.death_sprites) - 1)
			if current_frame_index != self.death_frame_index:
				self.death_frame_index = current_frame_index
				self.sprite = self.death_sprites[self.death_frame_index]
				self.rect.size = self.sprite.get_size()
			self.rect.center = (int(self.position.x), int(self.position.y))
			return
		# Обработка движения игрока
		keys = pygame.key.get_pressed()
		self.direction = Vector2(0, 0)
		self.direction.x = keys[pygame.K_d] - keys[pygame.K_a]
		self.direction.y = keys[pygame.K_s] - keys[pygame.K_w]

		# Обработка направления движения
		if self.direction.x != 0:
			self.last_direction.x = self.direction.x
		elif self.direction.y != 0:
			self.last_direction.y = self.direction.y
		
		if self.direction.length_squared() > 0:
			self.direction.normalize_ip()
			self.velocity = self.direction * self.speed
			self.current_animation = self.move_sprites
			self.animation_speed = 0.15
		else:
			self.current_animation = self.idle_sprites
			self.animation_speed = 0.5
			self.velocity *= 0.6
			if self.velocity.length_squared() < 1:
				self.velocity = Vector2(0, 0)
		
		# Обработка анимации
		if self.current_animation != self.previous_animation:
			self.current_sprite_index = 0
			self.previous_animation = self.current_animation
		
		self.animation_timer += dt
		if self.animation_timer >= self.animation_speed:
			self.animation_timer %= self.animation_speed
			self.current_sprite_index = (self.current_sprite_index + 1) % len(self.current_animation)
		
		current_sprite = self.current_animation[self.current_sprite_index]
		if self.last_direction.x < 0:
			self.sprite = pygame.transform.flip(current_sprite, True, False)
		else:
			self.sprite = current_sprite
		
		self.position += self.velocity * dt
		self.rect.center = self.position
		if self.active_weapon:
			self.active_weapon.update(dt, game_state)
	
	def draw(self, surface, camera: Camera):
		"""Отрисовка игрока"""
		super().draw(surface, camera)
		if not self.is_dying and self.active_weapon:
			num_dots, dot_sprite = self.active_weapon.get_cooldown_dots()
			# Отрисовка точек на экране
			if num_dots > 0 and dot_sprite:
				dot_width = dot_sprite.get_width()
				dot_height = dot_sprite.get_height()
				spacing = 2
				# Расчет ширины всех точек
				total_dots_width = (num_dots * dot_width) + ((num_dots - 1) * spacing)
				# Расчет координат для отрисовки
				world_x = self.position.x
				world_y_top = self.position.y - (self.sprite.get_height() / 2)
				# Расчет масштаба
				zoom = camera.zoom
				# Расчет координат центра экрана
				cam_x, cam_y = camera.camera.topleft
				screen_center_x = (world_x - cam_x) * zoom
				screen_top_y = (world_y_top - cam_y) * zoom
				start_x = screen_center_x - (total_dots_width // 2)
				y_pos = screen_top_y - dot_height - 20
				# Отрисовка точек
				for i in range(num_dots):
					dot_x = start_x + i * (dot_width + spacing)
					surface.blit(dot_sprite, (int(dot_x), int(y_pos)))
		# Отрисовка оружия
		if not self.is_dying:
			if self.active_weapon:
				self.active_weapon.draw(surface, camera)
