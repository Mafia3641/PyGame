import pygame


class Camera:
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.camera = pygame.rect.Rect(0, 0, width, height)
	
	def apply(self, entity):
		# Смещаем объекты относительно камеры
		return entity.rect.move(-self.camera.x, -self.camera.y)
	
	def update(self, target):
		# Смещение камеры (игрок всегда посередине)
		x = target.rect.centerx - self.width // 2
		y = target.rect.centery - self.height // 2
		self.camera = pygame.Rect(x, y, self.width, self.height)