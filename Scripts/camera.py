import pygame
from pygame.math import Vector2
class Camera:
	def __init__(self, width, height, zoom=2.0):
		self.width = width
		self.height = height
		self.zoom = zoom
		self.camera = pygame.rect.Rect(0, 0, width, height)
	def apply(self, entity):
		screen_x = (entity.rect.x - self.camera.x) * self.zoom
		screen_y = (entity.rect.y - self.camera.y) * self.zoom
		screen_w = entity.rect.width * self.zoom
		screen_h = entity.rect.height * self.zoom
		return pygame.Rect(int(screen_x), int(screen_y), int(screen_w), int(screen_h))
	def update(self, target):
		x = target.rect.centerx - (self.width / 2.0) / self.zoom
		y = target.rect.centery - (self.height / 2.0) / self.zoom
		self.camera.x = x
		self.camera.y = y
	def screen_to_world(self, screen_pos):
		
		screen_vec = Vector2(screen_pos)
		world_offset_x = screen_vec.x / self.zoom
		world_offset_y = screen_vec.y / self.zoom
		world_x = self.camera.x + world_offset_x
		world_y = self.camera.y + world_offset_y
		return Vector2(world_x, world_y)