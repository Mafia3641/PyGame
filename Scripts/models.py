import pygame
from pygame.math import Vector2
from utils import load_sprite
from constants import SPEED

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
		blit_position = self.position - Vector2(self.radius)

		blit_position = Vector2(
			self.position.x - self.sprite.get_width() / 2,
			self.position.y - self.sprite.get_height()
		)

		if camera:
			blit_position -= Vector2(camera.camera.topleft)
		surface.blit(self.sprite, blit_position)
	
	def move(self):
		self.position = self.position + self.velocity

		self.rect.x = self.position.x - self.radius
		self.rect.y = self.position.y - self.radius

		self.rect.x = self.position.x - self.sprite.get_width() / 2
		self.rect.y = self.position.y - self.sprite.get_height()

	
	def collides_with(self, other_object):
		distance = self.position.distance_to(other_object.position)
		return distance < self.radius + other_object.radius


class Player(GameObject):
	
	def __init__(self, position: tuple):
		self.direction = Vector2(0, 0)
		self.speed = SPEED
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
		self.last_direction = Vector2(1, 0)
		self.current_sprite_index = 0
		self.current_animation = self.idle_sprites
		self.previous_animation = self.current_animation
		self.animation_speed = 0.5
		self.animation_timer = 0

		super().__init__(position, self.idle_sprites[0], Vector2(0))

	def update(self, camera=None, dt=0):
		keys = pygame.key.get_pressed()
		self.direction.x = keys[pygame.K_d] - keys[pygame.K_a]
		self.direction.y = keys[pygame.K_s] - keys[pygame.K_w]

		# Обновляем направление
		if self.direction.x != 0:
			self.last_direction.x = self.direction.x

		# Физика движения
		if self.direction.length() > 0:
			self.direction = self.direction.normalize()
			self.velocity = self.direction * self.speed * dt
			self.current_animation = self.move_sprites
			self.animation_speed = 0.15  # Быстрая анимация при беге
		else:
			self.current_animation = self.idle_sprites
			self.animation_speed = 0.5  # Медленная анимация при покое
			self.velocity *= 0.8
			if self.velocity.length() < 0.1:
				self.velocity = Vector2(0, 0)

		if self.current_animation != self.previous_animation:
			self.current_sprite_index = 0
			self.previous_animation = self.current_animation

		# Обновляем анимацию (без сброса таймера каждый кадр!)
		self.animation_timer += dt
		if self.animation_timer >= self.animation_speed:
			self.animation_timer = 0
			self.current_sprite_index = (self.current_sprite_index + 1) % len(self.current_animation)


		# Применяем спрайт с учетом направления
		current_sprite = self.current_animation[self.current_sprite_index]
		if self.last_direction.x < 0:
			self.sprite = pygame.transform.flip(current_sprite, True, False)
		else:
			self.sprite = current_sprite

		# Обновляем позицию
		self.position += self.velocity

		self.rect.x = self.position.x - self.sprite.get_width() / 2
		self.rect.y = self.position.y - self.sprite.get_height()

		if camera:
			camera.update(self)