import pygame
from pygame.math import Vector2
from utils import load_sprite
from constants import SPEED, UP

class GameObject:
	def __init__(self, position: tuple, sprite, velocity: Vector2):
		self.position = Vector2(position)
		self.sprite = sprite
		self.radius = sprite.get_width() / 2
		self.velocity = Vector2(velocity)
		self.rect = pygame.Rect(
			self.position.x - self.radius,
			self.position.y - self.radius,
			self.sprite.get_width(),
			self.sprite.get_height()
		)
	
	def draw(self, surface, camera=None):
		blit_position = self.position - Vector2(self.radius)
		if camera:
			blit_position -= Vector2(camera.camera.topleft)
		surface.blit(self.sprite, blit_position)
	
	def move(self):
		self.position = self.position + self.velocity
		self.rect.x = self.position.x - self.radius
		self.rect.y = self.position.y - self.radius
	
	def collides_with(self, other_object):
		distance = self.position.distance_to(other_object.position)
		return distance < self.radius + other_object.radius


class Player(GameObject):
	
	def __init__(self, position: tuple):
		self.direction = Vector2(0, 0)
		self.speed = SPEED
		super().__init__(position, load_sprite('hero_v1'), Vector2(0))
	
	def update(self, camera=None, dt=0):
		keys = pygame.key.get_pressed()
		# Обрабатываем пережвижение персонажа
		self.direction.x = keys[pygame.K_d] - keys[pygame.K_a]
		self.direction.y = keys[pygame.K_s] - keys[pygame.K_w]

		if self.direction.length() > 0:
			self.direction = self.direction.normalize()
			self.velocity = self.direction * self.speed * dt
		if self.velocity.length() > self.speed:
			self.velocity = self.velocity.normalize() * self.speed
		if self.direction.length() == 0:
			self.velocity *= 0.8
			if self.velocity.length() < 0.1:  # Полная остановка при малой скорости
				self.velocity = Vector2(0, 0)
		self.position += self.velocity
		self.rect.x = self.position.x - self.radius
		self.rect.y = self.position.y - self.radius
		
		if camera:
			camera.update(self)

