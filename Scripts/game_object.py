import pygame
from pygame.math import Vector2

class GameObject:
	def __init__(self, position: tuple, sprite, velocity: Vector2):
		self.position = Vector2(position)
		self.sprite = sprite
		self.radius = sprite.get_width() / 2
		self.velocity = Vector2(velocity)
		self.rect = pygame.Rect(
			self.position.x - sprite.get_width() / 2,
			self.position.y - sprite.get_height(),
			self.sprite.get_width(),
			self.sprite.get_height()
		)
	
	def draw(self, surface, camera=None):
		blit_position = Vector2(
			self.position.x - self.sprite.get_width() / 2,
			self.position.y - self.sprite.get_height()
		)
		
		if camera:
			blit_position -= Vector2(camera.camera.topleft)
		surface.blit(self.sprite, blit_position)
	
	def move(self):
		self.position = self.position + self.velocity
		
		self.rect.x = self.position.x - self.sprite.get_width() / 2
		self.rect.y = self.position.y - self.sprite.get_height()
	
	def collides_with(self, other_object):
		distance = self.position.distance_to(other_object.position)
		return distance < self.radius + other_object.radius

