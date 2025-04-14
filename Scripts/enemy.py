import pygame
from pygame.math import Vector2
import math
from models import GameObject
from utils import load_sprite


class NPCLogic:
	"""
	Логика действий врагов.
	Враг перемещается к центру игрока (target). Если расстояние меньше attack_range,
	вызывается метод attack у врага.
	"""
	
	def __init__(self, target, speed=100, attack_range=50):
		self.target = target  # объект игрока, за которым идет преследование
		self.speed = speed  # скорость преследования (пикселей/сек)
		self.attack_range = attack_range  # дистанция для атаки (пикселей)
	
	def update(self, enemy, dt):
		"""
		Обновление логики врага:
		- Вычисляет направление от врага к игроку и перемещает врага.
		- Если расстояние до игрока меньше или равно attack_range, запускает атаку.
		"""
		# Вычисляем вектор направления к цели
		direction = self.target.position - enemy.position
		distance = direction.length()
		if distance > 0:
			direction = direction.normalize()
		else:
			direction = Vector2(0, 0)
		
		# Перемещаем врага к игроку с учетом скорости и delta time
		enemy.position += direction * self.speed * dt
		enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))
		
		# Если враг достаточно близко к игроку – атакуем
		if distance <= self.attack_range:
			enemy.attack()


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
		self.damage = damage  # урон, который враг может нанести
		# Создаем объект логики NPC с передачей ссылки на игрока (target)
		self.npc_logic = NPCLogic(target, speed, attack_range)
	
	def update(self, dt):
		"""
		Обновление врага – вызываем логику NPC, если цель (игрок) задана.
		"""
		if self.npc_logic and self.npc_logic.target:
			self.npc_logic.update(self, dt)
	
	def attack(self):
		"""
		Шаблон метода атаки.
		Здесь должна запускаться анимация атаки,
		а также проверяться коллизия анимации с моделью игрока для нанесения урона.
		"""
		print("Enemy is attacking! (damage: {})".format(self.damage))
	# В дальнейшем здесь можно добавить активацию анимации и проверку пересечения с игроком.


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
