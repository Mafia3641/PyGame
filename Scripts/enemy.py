import pygame
from pygame.math import Vector2
import math
from game_object import GameObject
from utils import load_sprite
from constants import SLIME_XP_REWARD, SLIME_BASE_HP, SLIME_BASE_DAMAGE
import random


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
		# --- Stun & Recovery Checks (Return if active) --- 
		if enemy.stun_timer > 0:
			enemy.stun_timer -= dt
			return 
		if enemy.knockback_recovery_timer > 0:
			enemy.knockback_recovery_timer -= dt
			# Apply reduced speed movement logic (as before)
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
		# -----------------------------------------------

		# --- Normal AI Logic --- 
		target_center = self.target.position
		enemy_center = enemy.position
		direction = target_center - enemy_center
		distance = direction.length()
		
		# 1. Check: Waiting during cooldown while player is in range?
		if enemy.attack_cooldown_timer > 0 and distance < self.attack_range:
			enemy.velocity = Vector2(0, 0) # Stay put
			# Don't return yet, let Enemy.update decrement the timer
			# Update rect based on stopped position
			enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))
			return # Skip attack/move checks
			
		# 2. Check: Initiate Attack (very close and cooldown ready)?
		if distance < (0.5 * self.attack_range) and enemy.attack_cooldown_timer <= 0 and not enemy.is_attacking:
			enemy.attack()  # Start wind-up (handled in Enemy/Slime update)
			enemy.velocity = Vector2(0, 0) # Stop moving now
			# Update rect based on stopped position
			enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))
			return # Let wind-up logic take over
		
		# 3. Action: Move towards player (if not waiting or attacking)
		if distance != 0: # Avoid normalization of zero vector
			direction.normalize_ip()
			enemy.velocity = direction
			enemy.position += direction * self.speed * dt
		else:
			enemy.velocity = Vector2(0, 0) # Already at target (or decided not to move)

		# Update rect based on final position for this frame
		enemy.rect.center = (int(enemy.position.x), int(enemy.position.y))


class Enemy(GameObject):
	"""
	Базовый класс врагов.
	При обновлении враг делегирует логику движения классу NPC_Logic.
	Метод attack является шаблонным – пока выводит сообщение, но должен запускать анимацию атаки
	и проверять коллизию с игроком.
	"""
	
	def __init__(self, position, sprite, damage=10, speed=100, hp=100, attack_range=50, target=None, xp_reward=0):
		# Инициализируем базовый объект
		super().__init__(position, sprite, Vector2(0, 0))
		self.damage = damage
		self.hp = hp
		self.max_hp = hp # Store max HP
		self.xp_reward = xp_reward # XP granted on death
		self.alive = True
		self.should_be_removed = False
		self.npc_logic = NPCLogic(target, speed, attack_range)
		
		self.attack_cooldown = 1.0 # Duration of cooldown
		self.attack_anim_duration = 0.5 # Duration of wind-up animation
		
		# State variables
		self.attack_cooldown_timer = 2.0 # Start with initial delay
		self.attack_windup_timer = 0.0
		self.is_attacking = False # Tracks wind-up phase
		
		self.stun_timer = 0.0 
		self.knockback_recovery_timer = 0.0
		self.knockback_velocity = Vector2(0, 0)
		self.knockback_timer = 0.0
		
	
	def update(self, dt):
		# --- Knockback Check (Return if active) --- 
		if self.knockback_timer > 0:
			self.position += self.knockback_velocity * dt
			self.rect.center = (int(self.position.x), int(self.position.y))
			self.knockback_timer -= dt
			if self.knockback_timer <= 0:
				self.knockback_velocity = Vector2(0, 0)
			return # Skip other updates while being knocked back
		# -----------------------
		
		# --- Attack Wind-up Logic (Return if active) --- 
		if self.is_attacking:
			self.velocity = Vector2(0, 0) # Stop moving during wind-up
			self.attack_windup_timer -= dt
			# Add logic here to switch to attack animation if needed
			
			if self.attack_windup_timer <= 0:
				# Wind-up finished, try to deal damage
				self.is_attacking = False # End attack state
				if self.npc_logic and self.npc_logic.target:
					target_pos = self.npc_logic.target.position
					if self.position.distance_to(target_pos) < self.npc_logic.attack_range:
						# print(f"Enemy dealt {self.damage} damage to player!") # Debug
						self.npc_logic.target.take_damage(self.damage)
						
				# Start cooldown regardless of hitting
				self.attack_cooldown_timer = self.attack_cooldown
			# Update rect based on potentially stopped position
			self.rect.center = (int(self.position.x), int(self.position.y))
			return # Finished attack logic for this frame
		# -------------------------
		
		# --- Normal Update (if not knockback/attacking) --- 
		# Decrement attack cooldown timer *first*
		if self.attack_cooldown_timer > 0:
			self.attack_cooldown_timer -= dt
			
		# Run standard NPC logic (handles movement, stun/recovery checks, triggering attack)
		if self.npc_logic and self.npc_logic.target:
			self.npc_logic.update(self, dt)
			
		# Update rect based on position potentially changed by NPCLogic
		self.rect.center = (int(self.position.x), int(self.position.y))

	def attack(self):
		# Called by NPCLogic when in range and cooldown ready
		if not self.is_attacking: # Should always be true if called by NPCLogic due to cooldown check
			# print("Enemy starts attack wind-up!") # Debug
			self.is_attacking = True
			self.attack_windup_timer = self.attack_anim_duration
			# Animation switching logic can be added here or in update based on is_attacking
	
	def take_damage(self, damage):
		if self.alive:
			self.hp -= damage
			if self.hp <= 0:
				self.alive = False
				self.die()
	
	def die(self):
		raise NotImplementedError("Override die() in subclass")

	def apply_knockback(self, direction: Vector2, strength: float, stun_duration: float):
		"""Applies knockback and stun to the enemy."""
		if not self.alive: return

		# Normalize direction
		if direction.length_squared() > 0:
			push_direction = direction.normalize()
		else: # Fallback if direction is zero
			push_direction = Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()

		knockback_speed = strength * 100 # Adjust multiplier as needed
		knockback_duration = 0.2 # How long the push lasts

		# Apply the knockback values
		self.knockback_velocity = push_direction * knockback_speed
		self.knockback_timer = knockback_duration
		self.stun_timer = max(self.stun_timer, stun_duration)
		# A recovery timer to prevent instant re-engagement
		self.knockback_recovery_timer = max(self.knockback_recovery_timer, knockback_duration + 0.1)


class Slime(Enemy):
	"""
	Пример конкретного типа врага – Monkey.
	Можно задать другие параметры скорости, урона, диапазона атаки.
	"""
	
	def __init__(self, position, target, hp=SLIME_BASE_HP, damage=SLIME_BASE_DAMAGE):
		# Загружаем спрайт для врага, например используя утилиту load_sprite
		sprite = load_sprite("Enemies/Slime/Slime_idle/slime_idle_1", with_alpha=True)
		# Инициализируем базовый класс с параметрами, включая переданные hp и damage
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
		
		# --- Grant XP to Player Immediately --- #
		try:
			if self.npc_logic and self.npc_logic.target and not self.npc_logic.target.is_dying:
				xp_to_grant = self.xp_reward * self.npc_logic.target.xp_multiplier
				self.npc_logic.target.gain_xp(xp_to_grant)
				self.npc_logic.target.restore_mana(10) # Restore 10 mana
				# print(f"DEBUG: Granted {self.xp_reward} XP from Slime {id(self)} in die() method.") # Debug print
		except AttributeError:
			# print(f"Warning: Could not grant XP from Slime {id(self)}. Target or npc_logic missing?")
			pass # Silently ignore if target missing
		# ------------------------------------ #
		
	def update(self, dt):
		# --- Knockback Check (Return if active) --- 
		if self.knockback_timer > 0:
			self.position += self.knockback_velocity * dt
			self.rect.center = (int(self.position.x), int(self.position.y))
			self.knockback_timer -= dt
			if self.knockback_timer <= 0:
				self.knockback_velocity = Vector2(0, 0)
			# Force idle animation during knockback? 
			# self.sprite = self.slime_idle_sprites[0] 
			# self.rect.size = self.sprite.get_size()
			return
		# -----------------------
		
		# --- Dying Check (Return if active) --- 
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
			return # Skip normal logic if dying
		
		# --- Attack Wind-up Logic (Return if active) --- 
		if self.is_attacking:
			self.velocity = Vector2(0, 0) # Stop moving
			self.attack_windup_timer -= dt
			# Set attack animation
			# Assuming attack animation exists and mirrors wind-up duration
			# This part needs specific slime attack sprites
			# self.current_slime_animation = self.slime_attack_sprites 
			self.current_slime_animation = self.slime_idle_sprites # Placeholder: use idle during windup
			self.animation_timer += dt # Still animate during windup
			if self.animation_timer >= self.animation_speed: # Use normal anim speed
				self.animation_timer = 0
				self.current_sprite_index = (self.current_sprite_index + 1) % len(self.current_slime_animation)
				self.sprite = self.current_slime_animation[self.current_sprite_index]
				# Flip if needed
				if self.last_direction.x < 0:
					self.sprite = pygame.transform.flip(self.sprite, True, False)
				self.rect.size = self.sprite.get_size()
			
			if self.attack_windup_timer <= 0:
				# Wind-up finished, try to deal damage
				self.is_attacking = False
				if self.npc_logic and self.npc_logic.target:
					target_pos = self.npc_logic.target.position
					if self.position.distance_to(target_pos) < self.npc_logic.attack_range:
						# print(f"Slime dealt {self.damage} damage to player!") # Debug
						self.npc_logic.target.take_damage(self.damage)
				# Start cooldown
				self.attack_cooldown_timer = self.attack_cooldown
			# Update rect based on potentially stopped position
			self.rect.center = (int(self.position.x), int(self.position.y))
			return # Finished attack logic for this frame
				
			# Ensure rect is updated even if windup continues
			self.rect.center = (int(self.position.x), int(self.position.y))
			return # Still winding up
		# -------------------------
		
		# --- Normal Slime Update (if not knockback/dying/attacking) --- 
		# Decrement attack cooldown timer *first*
		if self.attack_cooldown_timer > 0:
			self.attack_cooldown_timer -= dt
			
		# Run NPC logic (handles movement/waiting/attack initiation)
		if self.npc_logic and self.npc_logic.target:
			self.npc_logic.update(self, dt)
			
		# === Animation logic based on velocity from NPCLogic ===
		if self.velocity.length_squared() > 0:
			self.current_slime_animation = self.slime_move_sprites
			self.last_direction = self.velocity.normalize()
		else:
			self.current_slime_animation = self.slime_idle_sprites
			
		# Update animation frame
		self.animation_timer += dt
		if self.animation_timer >= self.animation_speed:
			self.animation_timer = 0
			self.current_sprite_index = (self.current_sprite_index + 1) % len(self.current_slime_animation)
			self.sprite = self.current_slime_animation[self.current_sprite_index]
			# Flip if needed
			if self.last_direction.x < 0:
				self.sprite = pygame.transform.flip(self.sprite, True, False)
			# Update rect size
			self.rect.width = self.sprite.get_width()
			self.rect.height = self.sprite.get_height()
			
		# === Update rect position based on final position ===
		self.rect.center = (int(self.position.x), int(self.position.y))

