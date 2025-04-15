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
		enemy.position += direction * self.speed * dt
		enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))


class Enemy(GameObject):
	"""
	Базовый класс врагов.
	При обновлении враг делегирует логику движения классу NPC_Logic.
	Метод attack является шаблонным – пока выводит сообщение, но должен запускать анимацию атаки
	и проверять коллизию с игроком.
	"""
	
	def __init__(self, position, sprite, damage=10, speed=100, attack_range=50, target=None):
		# Инициализируем базовый объект
		super().__init__(position, sprite, Vector2(0, 0))
		self.damage = damage
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


class Monkey(Enemy):
	"""
	Пример конкретного типа врага – Monkey.
	Можно задать другие параметры скорости, урона, диапазона атаки.
	"""
	
	def __init__(self, position, target):
		# Загружаем спрайт для врага, например используя утилиту load_sprite
		sprite = load_sprite("monkey_enemy", with_alpha=True)
		# Инициализируем базовый класс с индивидуальными параметрами для Monkey
		super().__init__(position, sprite, damage=5, speed=120, attack_range=40, target=target)
