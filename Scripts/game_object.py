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
		if camera:
			# Get the screen rectangle (position and size) from the camera
			screen_rect = camera.apply(self)

			# Check if the object is roughly on screen to avoid unnecessary scaling/blitting
			if screen_rect.colliderect(surface.get_rect()):
				# Scale the sprite to the size determined by the camera's zoom
				# Ensure size dimensions are integers and non-negative
				w = max(1, int(screen_rect.width))
				h = max(1, int(screen_rect.height))
				scaled_sprite = pygame.transform.scale(self.sprite, (w, h))
				
				# Blit the scaled sprite at the screen position determined by the camera
				surface.blit(scaled_sprite, screen_rect.topleft)
				
				# --- Draw Health Bar for objects with hp --- 
				if hasattr(self, 'hp') and hasattr(self, 'max_hp') and self.hp > 0:
					BAR_HEIGHT = 5
					BAR_PADDING = 2 # Space above sprite
					bar_width = screen_rect.width # Make bar as wide as sprite
					hp_ratio = max(0, self.hp / self.max_hp)
					
					bg_color = (128, 0, 0) # Dark Red
					fg_color = (0, 200, 0) # Green
					
					bg_rect_pos_x = screen_rect.left
					bg_rect_pos_y = screen_rect.top - BAR_HEIGHT - BAR_PADDING
					bg_rect = pygame.Rect(bg_rect_pos_x, bg_rect_pos_y, bar_width, BAR_HEIGHT)
					
					fg_rect_width = int(bar_width * hp_ratio)
					fg_rect = pygame.Rect(bg_rect_pos_x, bg_rect_pos_y, fg_rect_width, BAR_HEIGHT)
					
					pygame.draw.rect(surface, bg_color, bg_rect)
					pygame.draw.rect(surface, fg_color, fg_rect)
				# -----------------------------------------
		else:
			# Original drawing logic if no camera is provided
			blit_position = Vector2(
				self.position.x - self.sprite.get_width() / 2,
				self.position.y - self.sprite.get_height()
			)
			surface.blit(self.sprite, blit_position)
			# Health bar not drawn in non-camera case for simplicity
	
	def move(self):
		self.position = self.position + self.velocity
		
		self.rect.x = self.position.x - self.sprite.get_width() / 2
		self.rect.y = self.position.y - self.sprite.get_height()
	
	def collides_with(self, other_object):
		distance = self.position.distance_to(other_object.position)
		return distance < self.radius + other_object.radius

