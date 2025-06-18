import pygame
from pygame.math import Vector2
import math
from game_object import GameObject
from utils import load_sprite
from constants import SLIME_XP_REWARD, SLIME_BASE_HP, SLIME_BASE_DAMAGE
import random
class NPCLogic:
	
	def __init__(self, target, speed=100, attack_range=50):
		self.target = target
		self.speed = speed
		self.attack_range = attack_range
	def update(self, enemy, dt):
		if enemy.stun_timer > 0:
			enemy.stun_timer -= dt
			return
		if enemy.knockback_recovery_timer > 0:
			enemy.knockback_recovery_timer -= dt
			target_center = self.target.position
			enemy_center = enemy.position
			direction = target_center - enemy_center
			distance = direction.length()
			if distance < 0.5 * self.attack_range:
				enemy.velocity = Vector2(0, 0)
				return
			if distance != 0:
				direction.normalize_ip()
			enemy.velocity = direction
			enemy.position += direction * (self.speed * 0.5) * dt
			enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))
			return
		target_center = self.target.position
		enemy_center = enemy.position
		direction = target_center - enemy_center
		distance = direction.length()
		if enemy.attack_cooldown_timer > 0 and distance < self.attack_range:
			enemy.velocity = Vector2(0, 0)
			enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))
			return
		if distance < (0.5 * self.attack_range) and enemy.attack_cooldown_timer <= 0 and not enemy.is_attacking:
			enemy.attack()
			enemy.velocity = Vector2(0, 0)
			enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))
			return
		if distance != 0:
			direction.normalize_ip()
			enemy.velocity = direction
			enemy.position += direction * self.speed * dt
		else:
			enemy.velocity = Vector2(0, 0)
		enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))
class Enemy(GameObject):
	
	def __init__(self, position, sprite, damage=10, speed=100, hp=100, attack_range=50, target=None, xp_reward=0):
		super().__init__(position, sprite, Vector2(0, 0))
		self.damage = damage
		self.hp = hp
		self.max_hp = hp
		self.xp_reward = xp_reward
		self.alive = True
		self.should_be_removed = False
		self.npc_logic = NPCLogic(target, speed, attack_range)
		self.attack_cooldown = 1.0
		self.attack_anim_duration = 0.5
		self.attack_cooldown_timer = 2.0
		self.attack_windup_timer = 0.0
		self.is_attacking = False
		self.stun_timer = 0.0
		self.knockback_recovery_timer = 0.0
		self.knockback_velocity = Vector2(0, 0)
		self.knockback_timer = 0.0
	def update(self, dt):
		if self.knockback_timer > 0:
			self.position += self.knockback_velocity * dt
			self.rect.center = (int(self.position.x), int(self.position.y))
			self.knockback_timer -= dt
			if self.knockback_timer <= 0:
				self.knockback_velocity = Vector2(0, 0)
			return
		if self.is_attacking:
			self.velocity = Vector2(0, 0)
			self.attack_windup_timer -= dt
			if self.attack_windup_timer <= 0:
				self.is_attacking = False
				if self.npc_logic and self.npc_logic.target:
					target_pos = self.npc_logic.target.position
					if self.position.distance_to(target_pos) < self.npc_logic.attack_range:
						self.npc_logic.target.take_damage(self.damage)
				self.attack_cooldown_timer = self.attack_cooldown
			self.rect.center = (int(self.position.x), int(self.position.y))
			return
		if self.attack_cooldown_timer > 0:
			self.attack_cooldown_timer -= dt
		if self.npc_logic and self.npc_logic.target:
			self.npc_logic.update(self, dt)
		self.rect.center = (int(self.position.x), int(self.position.y))
	def attack(self):
		if not self.is_attacking:
			self.is_attacking = True
			self.attack_windup_timer = self.attack_anim_duration
	def take_damage(self, damage):
		if self.alive:
			self.hp -= damage
			if self.hp <= 0:
				self.alive = False
				self.die()
	def die(self):
		raise NotImplementedError("Override die() in subclass")
	def apply_knockback(self, direction: Vector2, strength: float, stun_duration: float):
		
		if not self.alive: return
		if direction.length_squared() > 0:
			push_direction = direction.normalize()
		else:
			push_direction = Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
		knockback_speed = strength * 100
		knockback_duration = 0.2
		self.knockback_velocity = push_direction * knockback_speed
		self.knockback_timer = knockback_duration
		self.stun_timer = max(self.stun_timer, stun_duration)
		self.knockback_recovery_timer = max(self.knockback_recovery_timer, knockback_duration + 0.1)
class Slime(Enemy):
	
	def __init__(self, position, target, hp=SLIME_BASE_HP, damage=SLIME_BASE_DAMAGE):
		sprite = load_sprite("Enemies/Slime/Slime_idle/slime_idle_1", with_alpha=True)
		super().__init__(position, sprite,
					 damage=damage,
					 speed=120,
					 hp=hp,
					 attack_range=30,
					 target=target,
					 xp_reward=SLIME_XP_REWARD)
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
		try:
			if self.npc_logic and self.npc_logic.target and not self.npc_logic.target.is_dying:
				xp_to_grant = self.xp_reward * self.npc_logic.target.xp_multiplier
				self.npc_logic.target.gain_xp(xp_to_grant)
				self.npc_logic.target.restore_mana(10)
		except AttributeError:
			pass
	def update(self, dt):
		if self.knockback_timer > 0:
			self.position += self.knockback_velocity * dt
			self.rect.center = (int(self.position.x), int(self.position.y))
			self.knockback_timer -= dt
			if self.knockback_timer <= 0:
				self.knockback_velocity = Vector2(0, 0)
			return
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
			return
		if self.is_attacking:
			self.velocity = Vector2(0, 0)
			self.attack_windup_timer -= dt
			self.current_slime_animation = self.slime_idle_sprites
			self.animation_timer += dt
			if self.animation_timer >= self.animation_speed:
				self.animation_timer = 0
				self.current_sprite_index = (self.current_sprite_index + 1) % len(self.current_slime_animation)
				self.sprite = self.current_slime_animation[self.current_sprite_index]
				if self.last_direction.x < 0:
					self.sprite = pygame.transform.flip(self.sprite, True, False)
				self.rect.size = self.sprite.get_size()
			if self.attack_windup_timer <= 0:
				self.is_attacking = False
				if self.npc_logic and self.npc_logic.target:
					target_pos = self.npc_logic.target.position
					if self.position.distance_to(target_pos) < self.npc_logic.attack_range:
						self.npc_logic.target.take_damage(self.damage)
				self.attack_cooldown_timer = self.attack_cooldown
			self.rect.center = (int(self.position.x), int(self.position.y))
			return
			self.rect.center = (int(self.position.x), int(self.position.y))
			return
		if self.attack_cooldown_timer > 0:
			self.attack_cooldown_timer -= dt
		if self.npc_logic and self.npc_logic.target:
			self.npc_logic.update(self, dt)
		if self.velocity.length_squared() > 0:
			self.current_slime_animation = self.slime_move_sprites
			self.last_direction = self.velocity.normalize()
		else:
			self.current_slime_animation = self.slime_idle_sprites
		self.animation_timer += dt
		if self.animation_timer >= self.animation_speed:
			self.animation_timer = 0
			self.current_sprite_index = (self.current_sprite_index + 1) % len(self.current_slime_animation)
			self.sprite = self.current_slime_animation[self.current_sprite_index]
			if self.last_direction.x < 0:
				self.sprite = pygame.transform.flip(self.sprite, True, False)
			self.rect.width = self.sprite.get_width()
			self.rect.height = self.sprite.get_height()
		self.rect.center = (int(self.position.x), int(self.position.y))
