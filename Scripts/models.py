import pygame
from pygame.math import Vector2
from utils import load_sprite
from constants import SPEED, BASE_DAMAGE
from weapon import MeleeWeapon, RangeWeapon
from game_object import GameObject
from weapon_stats import WEAPON_STATS


class Player(GameObject):
	
	def __init__(self, position: tuple):
		self.direction = Vector2(0, 0)
		self.speed = SPEED
		self.damage = BASE_DAMAGE
		self.max_hp = 100 # Add max HP
		self.hp = self.max_hp # Start with full HP
		
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
		self.death_sprites = [
			load_sprite('Player/Player_Die/player_die_1'),
			load_sprite('Player/Player_Die/player_die_2'),
			load_sprite('Player/Player_Die/player_die_3'),
		]
		self.last_direction = Vector2(1, 0)
		self.current_sprite_index = 0
		self.current_animation = self.idle_sprites
		self.previous_animation = self.current_animation
		self.animation_speed = 0.5
		self.animation_timer = 0
		self.is_dying = False
		self.death_frame_index = 0
		self.death_timer = 0.0
		self.death_frame_duration = 0.4 # Increased from 0.2 for slower animation

		super().__init__(position, self.idle_sprites[0], Vector2(0))

		self.active_weapon = None
		self.pickup_weapon('starter_sword')
	
	def pickup_weapon(self, weapon_name: str):
		if weapon_name not in WEAPON_STATS:
			raise ValueError(f"Unknown weapon requested: {weapon_name}")

		stats = WEAPON_STATS[weapon_name]
		weapon_type = stats.get('type')
		
		# Common args for both types
		common_args = {
			'owner': self,
			'offset': Vector2(stats['offset']) # Convert list to Vector2
		}

		if weapon_type == 'melee':
			# Generate attack sprite list from pattern
			attack_sprites = [
				stats['attack_sprite_pattern'].format(i) 
				for i in range(1, stats['attack_sprite_count'] + 1)
			]
			
			# Specific args for MeleeWeapon
			melee_args = {
				'idle_sprite_name': stats['idle_sprite_name'],
				'attack_sprite_names': attack_sprites,
				'damage': stats['damage'],
				'attack_range': stats['attack_range'],
				'cooldown': stats['cooldown'],
				'repulsion': stats['repulsion'],
				'frame_duration': stats['frame_duration']
			}
			self.active_weapon = MeleeWeapon(**common_args, **melee_args)
			
		elif weapon_type == 'range':
			# Specific args for RangeWeapon
			range_args = {
			    'weapon_idle_sprite': stats['weapon_idle_sprite'], # Key corrected in stats file
				'projectile_speed': stats['projectile_speed'],
				'projectile_sprite_name': stats['projectile_sprite_name'],
				'damage': stats['damage'],
				'cooldown': stats['cooldown'],
				'accuracy': stats['accuracy'],
				'repulsion': stats['repulsion']
			}
			self.active_weapon = RangeWeapon(**common_args, **range_args)
			
		else:
			raise ValueError(f"Unknown weapon type '{weapon_type}' in stats for {weapon_name}")
	
	def take_damage(self, amount):
		"""Reduces player HP and handles death."""
		if self.hp > 0 and not self.is_dying: # Only take damage if alive and not already dying
			self.hp -= amount
			print(f"Player took {amount} damage, HP left: {self.hp}") # Debug
			if self.hp <= 0:
				self.hp = 0 # Prevent negative HP
				# --- Trigger Death Sequence --- 
				print("Player Death Sequence Started!") # Debug
				self.is_dying = True
				self.death_frame_index = 0
				self.death_timer = 0.0
				# Set initial death sprite immediately
				if self.death_sprites:
					self.sprite = self.death_sprites[0]
					self.rect.size = self.sprite.get_size()
				# -----------------------------
				# Remove old game over logic:
				# print("Player Died!") 
				# pygame.quit()
				# sys.exit() 

	def update(self, camera=None, dt=0):
		# --- Handle Death Animation First --- 
		if self.is_dying:
			self.velocity = Vector2(0, 0) # Stop movement
			
			self.death_timer += dt
			target_frame_index = int(self.death_timer // self.death_frame_duration)
			current_frame_index = min(target_frame_index, len(self.death_sprites) - 1)
			
			# --- DEBUG PRINTS --- 
			print(f"Death Update: dt={dt:.4f}, timer={self.death_timer:.4f}, target_idx={target_frame_index}, current_idx={current_frame_index}, stored_idx={self.death_frame_index}")
			# ------------------
			
			# Update sprite only if the frame index has changed
			if current_frame_index != self.death_frame_index:
				# --- DEBUG PRINT --- 
				print(f"  >>> Updating death frame index from {self.death_frame_index} to {current_frame_index}")
				# -------------------
				self.death_frame_index = current_frame_index
				self.sprite = self.death_sprites[self.death_frame_index]
				self.rect.size = self.sprite.get_size() # Update rect size for new sprite
				
			# Update rect position (even if stopped)
			self.rect.center = (int(self.position.x), int(self.position.y))
			
			# Add a condition to check if animation cycle is complete (optional)
			# if target_frame_index >= len(self.death_sprites):
			#    print("Death animation cycle finished")
				
			return # Skip normal update
		# ----------------------------------
		
		# --- Normal Update Logic (if not dying) --- 
		# Input handling
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
		