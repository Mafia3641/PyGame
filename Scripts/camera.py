import pygame
from pygame.math import Vector2 # Import Vector2


class Camera:
	def __init__(self, width, height, zoom=2.0):
		self.width = width
		self.height = height
		self.zoom = zoom
		self.camera = pygame.rect.Rect(0, 0, width, height)
	
	def apply(self, entity):
		# Calculate screen coordinates based on world coordinates, camera position, and zoom
		screen_x = (entity.rect.x - self.camera.x) * self.zoom
		screen_y = (entity.rect.y - self.camera.y) * self.zoom
		# Calculate screen size based on world size and zoom
		screen_w = entity.rect.width * self.zoom
		screen_h = entity.rect.height * self.zoom
		# Return a new Rect representing the entity's position and size on the screen
		# Use int() for pixel coordinates
		return pygame.Rect(int(screen_x), int(screen_y), int(screen_w), int(screen_h))
	
	def update(self, target):
		# Calculate the world coordinates for the top-left corner of the view
		# ensuring the target's center appears in the middle of the screen after zooming.
		# Use floating-point division for accuracy.
		x = target.rect.centerx - (self.width / 2.0) / self.zoom
		y = target.rect.centery - (self.height / 2.0) / self.zoom
		
		# Update the camera's position (top-left corner in world coordinates)
		self.camera.x = x
		self.camera.y = y
		# The camera rect's width/height are not strictly needed for the current apply logic,
		# so we leave them representing the screen dimensions for now.

	def screen_to_world(self, screen_pos):
		"""Converts screen coordinates (e.g., mouse position) to world coordinates."""
		# Get screen position as a Vector2
		screen_vec = Vector2(screen_pos)
		# Reverse the zoom scaling
		world_offset_x = screen_vec.x / self.zoom
		world_offset_y = screen_vec.y / self.zoom
		# Add the camera's world position (top-left)
		world_x = self.camera.x + world_offset_x
		world_y = self.camera.y + world_offset_y
		return Vector2(world_x, world_y)