import pygame
from pygame.math import Vector2
import math
from models import GameObject
from utils import load_sprite


class NPCLogic:
	"""
	Логика действий врагов.
	Враг перемещается к центру игрока (target). Если расстояние меньше 0.5 * attack_range от позиции player,
	вызывается метод attack у врага.
	"""
	
	def __init__(self, target, speed=100, attack_range=50):
		self.target = target  # объект игрока, за которым идет преследование
		self.speed = speed  # скорость преследования (пикселей/сек)
		self.attack_range = attack_range  # дистанция для атаки (пикселей)
	
	def update(self, enemy, dt):
		# Центры врага и игрока (self.target)
		target_center = self.target.position
		enemy_center = enemy.position
		
		# Вектор к игроку
		direction = target_center - enemy_center
		distance = direction.length()
		
		# Если враг слишком близко — не двигается и атакует
		if distance < 0.5 * self.attack_range:
			enemy.velocity = Vector2(0, 0)
			enemy.attack()  # Атака, если на расстоянии ближе порога
			return
		
		# Нормализуем вектор и двигаемся к игроку
		if distance != 0:
			direction.normalize_ip()

		enemy.velocity = direction
		enemy.position += direction * self.speed * dt
		enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))


class Enemy(GameObject):
	"""
	Базовый класс врагов.
	При обновлении враг делегирует логику движения классу NPC_Logic.
	Метод attack является шаблонным – пока выводит сообщение, но должен запускать анимацию атаки
	и проверять коллизию с игроком.
	"""
	
	def __init__(self, position, sprite, damage=10, speed=100, hp=100, attack_range=50, target=None):
		# Инициализируем базовый объект
		super().__init__(position, sprite, Vector2(0, 0))
		self.damage = damage
		self.hp = hp
		self.alive = True
		self.should_be_removed = False
		self.npc_logic = NPCLogic(target, speed, attack_range)
		
		self.attack_cooldown = 1.0 # seconds
		self.attack_anim_duration = 0.5
		
	
	def update(self, dt):
		"""
		Обновление врага – вызываем логику NPC, если цель (игрок) задана.
		"""
		if self.npc_logic and self.npc_logic.target:
			self.npc_logic.update(self, dt)
	
	def attack(self):
		print("Enemy is attacking! (damage: {})".format(self.damage))
	
	def take_damage(self, damage):
		if self.alive:
			self.hp -= damage
			if self.hp <= 0:
				self.alive = False
				self.die()
	
	def die(self):
		raise NotImplementedError("Override die() in subclass")


class Slime(Enemy):
	"""
	Пример конкретного типа врага – Monkey.
	Можно задать другие параметры скорости, урона, диапазона атаки.
	"""
	
	def __init__(self, position, target):
		# Загружаем спрайт для врага, например используя утилиту load_sprite
		sprite = load_sprite("Enemies/Slime/Slime_idle/slime_idle_1", with_alpha=True)
		# Инициализируем базовый класс с индивидуальными параметрами для Slime
		super().__init__(position, sprite, damage=5, speed=120, hp=50, attack_range=30, target=target)
		
		self.slime_move_sprites = [
			load_sprite("Enemies/Slime/Slime_run/slime_move_1"),
			load_sprite("Enemies/Slime/Slime_run/slime_move_2"),
			load_sprite("Enemies/Slime/Slime_run/slime_move_3"),
			load_sprite("Enemies/Slime/Slime_run/slime_move_4"),
			load_sprite("Enemies/Slime/Slime_run/slime_move_5"),
			load_sprite("Enemies/Slime/Slime_run/slime_move_6"),
		]
		self.slime_idle_sprites = [
			load_sprite("Enemies/Slime/Slime_idle/slime_idle_1"),
			load_sprite("Enemies/Slime/Slime_idle/slime_idle_2"),
			load_sprite("Enemies/Slime/Slime_idle/slime_idle_3"),
			load_sprite("Enemies/Slime/Slime_idle/slime_idle_4"),
		]
		self.last_direction = Vector2(1, 0)
		self.current_sprite_index = 0
		self.current_slime_animation = self.slime_move_sprites
		self.previous_animation = self.current_slime_animation
		self.animation_speed = 0.2
		self.animation_timer = 0
		
		self.death_sprites = [
			load_sprite("Enemies/Slime/Slime_die/slime_die_1"),
			load_sprite("Enemies/Slime/Slime_die/slime_die_2"),
			load_sprite("Enemies/Slime/Slime_die/slime_die_3"),
			load_sprite("Enemies/Slime/Slime_die/slime_die_4"),
			load_sprite("Enemies/Slime/Slime_die/slime_die_5"),
		]
		self.dying = False
		self.death_timer = 0.0
		self.death_frame_index = 0
		self.death_frame_duration = 0.2
		self.time_since_last_frame = 0.0
		self.removal_delay = 5.0
		
	
	def die(self):
		self.dying = True
		self.death_timer = 0.0
		self.death_frame_index = 0
		self.sprite = self.death_sprites[0]
		
	def update(self, dt):
		if self.dying:
			self.death_timer += dt
			self.time_since_last_frame += dt
			
			if self.death_frame_index < len(self.death_sprites):
				if self.time_since_last_frame >= self.death_frame_duration:
					self.time_since_last_frame = 0
					self.death_frame_index += 1
					if self.death_frame_index < len(self.death_sprites):
						self.sprite = self.death_sprites[self.death_frame_index]
			
			if self.death_timer >= self.removal_delay:
				self.should_be_removed = True
		
		
		else:
			super().update(dt)
			# === Определяем текущую анимацию на основе движения ===
			if self.velocity.length_squared() > 0:
				# Движется
				self.current_slime_animation = self.slime_move_sprites
				self.last_direction = self.velocity.normalize()
			else:
				# Стоит
				self.current_slime_animation = self.slime_idle_sprites
			
			# === Обновление таймера и кадра анимации ===
			self.animation_timer += dt
			if self.animation_timer >= self.animation_speed:
				self.animation_timer = 0
				self.current_sprite_index = (self.current_sprite_index + 1) % len(self.current_slime_animation)
				self.sprite = self.current_slime_animation[self.current_sprite_index]
				
				# Отзеркаливание при движении влево
				if self.last_direction.x < 0:
					self.sprite = pygame.transform.flip(self.sprite, True, False)
			
			# === Обновление позиции спрайта ===
			self.rect.x = self.position.x - self.sprite.get_width() / 2
			self.rect.y = self.position.y - self.sprite.get_height()

