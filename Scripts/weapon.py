import pygame
from pygame.math import Vector2
import math # Import math module
from game_object import GameObject
from utils import load_sprite
import random
# Import constants for screen dimensions
from constants import WINDOW_WIDTH, WINDOW_HEIGHT 

class Weapon:
    def __init__(self, owner, offset: Vector2, stats: dict):
        self.owner = owner
        self.offset = Vector2(offset)
        self.stats = stats # Store the weapon stats dictionary
        self.sprite = None
        self.rect = pygame.Rect(0,0,0,0)
        self.angle = 0
        self.world_position = owner.position + offset # Initial world position
        self.cooldown_timer = 0.0
        self.last_direction = Vector2(1, 0) # Default direction
        
        # Cooldown Indicator
        self.cooldown_dots = 0
        self.dot_sprite = None
        self._load_dot_sprite()

    def _load_dot_sprite(self):
        try:
            # --- Use original dot sprite --- #
            # dot_path = "UI/ui_sprites/pause_button.png" # Temp path
            dot_path = "UI/ui_sprites/dot.png" # Original path
            # ----------------------------- #
            self.dot_sprite = pygame.image.load(dot_path).convert_alpha()
            # print(f"DEBUG: Loaded sprite for dots: {dot_path}") # Remove debug print
        except pygame.error as e:
            print(f"Warning: Could not load sprite for dots ({dot_path}): {e}")
            self.dot_sprite = None
        except FileNotFoundError:
            print(f"Warning: Sprite file for dots not found: {dot_path}")
            self.dot_sprite = None

    def update_position(self):
        if not self.sprite: return # Should not happen if called from update check, but safer
        
        # Anchor the weapon to the owner's visual rect center
        anchor_pos = Vector2(self.owner.rect.center)
        
        # --- Adjust offset based on owner direction --- 
        base_offset = self.offset
        flip_horizontal = self.owner.last_direction.x < 0
        adjusted_offset = Vector2(-base_offset.x, base_offset.y) if flip_horizontal else base_offset
        # --------------------------------------------
        
        # Apply the adjusted offset to the anchor position
        target_weapon_center = anchor_pos + adjusted_offset
        
        # Get the weapon sprite's rect (to know its size)
        # Re-fetch the *original* sprite's rect for size, center it later
        self.rect = self.sprite.get_rect()
        
        # Set the weapon rect's center to the calculated target position
        self.rect.center = target_weapon_center

    def update(self, dt, game_state):
        # Update cooldown timer
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer < 0:
                self.cooldown_timer = 0

        # --- Update Cooldown Dots --- #
        total_cooldown = self.stats.get('cooldown', 0.0)
        calculated_dots = 0 # Default to 0
        if total_cooldown <= 0 or self.cooldown_timer <= 0:
            calculated_dots = 0
        else:
            elapsed_time = total_cooldown - self.cooldown_timer
            quarter_cooldown = total_cooldown / 4.0
            
            if elapsed_time >= 3 * quarter_cooldown:
                calculated_dots = 0 # Ready (don't show 4th dot)
            elif elapsed_time >= 2 * quarter_cooldown:
                calculated_dots = 3
            elif elapsed_time >= 1 * quarter_cooldown:
                calculated_dots = 2
            else:
                calculated_dots = 1
                
        self.cooldown_dots = calculated_dots # Assign calculated value
        # --- Debug Print --- #
        if self.cooldown_timer > 0: # Only print during active cooldown
            print(f"  Weapon Cooldown - Timer: {self.cooldown_timer:.2f}/{total_cooldown:.2f}, Elapsed: {elapsed_time:.2f}, Dots: {self.cooldown_dots}")
        # ------------------- #
        # -------------------------- #

        # Align weapon position and orientation with owner
        # Determine facing direction (based on mouse or owner direction)
        if hasattr(self.owner, 'last_direction'):
            self.last_direction = self.owner.last_direction.copy()
        
        # Update position based on owner and offset
        self.world_position = self.owner.position + self.offset.rotate(self.angle) # Apply rotation to offset if needed
        
        # Update sprite orientation (subclasses might override)
        if self.sprite:
            # Basic horizontal flip based on owner's last direction
            if self.last_direction.x < 0:
                self.oriented_sprite = pygame.transform.flip(self.sprite, True, False)
            else:
                self.oriented_sprite = self.sprite
                
        # Ensure the weapon sprite is valid before trying to update position
        if self.sprite:
            self.update_position()

    def draw(self, surface, camera):
        if camera:
            # Create a temporary rect for camera.apply, as Weapon doesn't inherit GameObject's rect handling
            # Use self.rect which is updated in update_position
            temp_obj_for_apply = pygame.sprite.Sprite() # Dummy sprite object
            temp_obj_for_apply.rect = self.rect # Use the weapon's calculated world rect
            temp_obj_for_apply.image = self.sprite # Needed if camera.apply expects an image
            
            screen_rect = camera.apply(temp_obj_for_apply)

            # Check if the object is roughly on screen
            if screen_rect.colliderect(surface.get_rect()):
                # Scale the sprite
                w = max(1, int(screen_rect.width))
                h = max(1, int(screen_rect.height))
                if self.sprite and w > 0 and h > 0: # Ensure sprite exists and size is valid
                    # Scale the sprite first
                    scaled_sprite = pygame.transform.scale(self.sprite, (w, h))
                    
                    # --- Flip based on owner's direction --- 
                    flip_horizontal = self.owner.last_direction.x < 0
                    final_sprite = pygame.transform.flip(scaled_sprite, flip_horizontal, False) if flip_horizontal else scaled_sprite
                    # ------------------------------------
                    
                    # Blit the final (scaled and potentially flipped) sprite
                    surface.blit(final_sprite, screen_rect.topleft)
        else:
            # Fallback if no camera (shouldn't happen with current game structure)
            if self.sprite:
                # --- Flip based on owner's direction (non-camera case) ---
                flip_horizontal = self.owner.last_direction.x < 0
                final_sprite = pygame.transform.flip(self.sprite, flip_horizontal, False) if flip_horizontal else self.sprite
                # ------------------------------------------------------
                surface.blit(final_sprite, self.rect.topleft)

    def get_cooldown_dots(self):
        """Returns the number of dots to display and the dot sprite."""
        return self.cooldown_dots, self.dot_sprite

    # Modify attack to accept target world position
    def attack(self, target_pos: Vector2, game_state):
        """Base attack method. Should be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement the attack method")


class MeleeWeapon(Weapon):
    def __init__(
        self,
        owner,
        offset: Vector2,
        stats: dict, # Use stats dict
        idle_sprite_name: str,
        attack_sprite_names: list[str],
        frame_duration: float = 0.1
    ):
        super().__init__(owner, offset, stats) # Pass stats to base
        # спрайты
        self.idle_sprite    = load_sprite(idle_sprite_name, with_alpha=True)
        self.attack_sprites = [load_sprite(n, with_alpha=True) for n in attack_sprite_names]
        # текущее состояние анимации
        self.sprite         = self.idle_sprite
        self.attacking      = False
        self.frame_index    = 0
        self.timer          = 0.0
        self.frame_duration = frame_duration
        self.cooldown_timer = 0.0 # Add cooldown timer
        self.attack_arc_rad = math.radians(self.stats.get('attack_arc', 360)) # Get arc from stats, default to 360
        self.half_arc_rad = self.attack_arc_rad / 2
    
    # Override attack method for directional arc
    def attack(self, target_pos: Vector2, game_state):
        # Start attack only if not already attacking and cooldown is ready
        if not self.attacking and self.cooldown_timer <= 0:
            self.attacking = True
            self.frame_index = 0
            self.timer = 0.0
            self.hit_enemies_this_attack = set() # Track hits per attack swing
            
            # Set first attack frame immediately
            self.sprite = self.attack_sprites[0]
            self.update_position() # Position weapon for the first frame
            
            print("Melee Attack Started") # Debug
            
            # --- Directional Hit Check --- 
            owner_pos = self.owner.position
            attack_direction = (target_pos - owner_pos)
            # Handle case where target_pos is exactly owner_pos (use owner's facing direction)
            if attack_direction.length_squared() == 0: 
                attack_direction = self.owner.last_direction.copy()
            attack_direction.normalize_ip()
            
            # Get attack range from stats
            attack_range_sq = self.stats.get('range', 50) ** 2 

            for enemy in game_state.enemies: # Access enemies via game_state
                if not enemy.alive: continue # Skip dead enemies
                
                enemy_vector = enemy.position - owner_pos
                distance_sq = enemy_vector.length_squared()
                
                # 1. Check Range
                if distance_sq <= attack_range_sq and distance_sq > 0:
                    # 2. Check Angle
                    enemy_direction = enemy_vector.normalize()
                    # Use dot product for angle check (more efficient than acos)
                    # dot_product = attack_direction.dot(enemy_direction)
                    # angle_rad = math.acos(max(-1.0, min(1.0, dot_product))) # Clamp dot product for safety
                    
                    # Alternative: Use angle_to for signed angle
                    angle_degrees = attack_direction.angle_to(enemy_direction)
                    
                    # Check if the angle is within the arc
                    if abs(angle_degrees) <= self.stats.get('attack_arc', 90) / 2:
                        if enemy not in self.hit_enemies_this_attack:
                            print(f"Hit enemy {id(enemy)} within arc") # Debug
                            enemy.take_damage(self.stats.get('damage', 10)) # Get damage from stats
                            self.hit_enemies_this_attack.add(enemy) # Mark as hit
                            
                            # Apply Knockback & Stun (get values from stats)
                            knockback_strength = self.stats.get('knockback', 100)
                            stun_duration = self.stats.get('stun_duration', 0.1)
                            
                            if knockback_strength > 0 and enemy.alive: # Only apply if alive
                                push_direction = enemy_direction # We already have this normalized
                                knockback_speed = knockback_strength * 3 # Adjust multiplier as needed
                                knockback_duration = 0.15 # Keep knockback brief
                                
                                enemy.knockback_velocity = push_direction * knockback_speed
                                enemy.knockback_timer = knockback_duration
                                # Apply stun slightly longer than knockback potentially
                                enemy.stun_timer = max(enemy.stun_timer, stun_duration) 
                                # Recovery prevents immediate re-engagement
                                enemy.knockback_recovery_timer = max(enemy.knockback_recovery_timer, knockback_duration + 0.3)
            # --- Start Cooldown --- #
            self.cooldown_timer = self.stats.get('cooldown', 0.5) # Start cooldown immediately
            # ---------------------- #
            # ----------------------------

    def update(self, dt, game_state):
        # --- Call Base Class Update First --- #
        # This handles cooldown timer decrement and dot calculation
        super().update(dt, game_state)
        # ---------------------------------- #
        
        # Update position based on current sprite first
        if self.sprite:
            self.update_position()
        
        if self.attacking:
            self.timer += dt
            if self.timer >= self.frame_duration:
                self.timer -= self.frame_duration
                self.frame_index += 1
                if self.frame_index < len(self.attack_sprites):
                    # Advance animation frame
                    self.sprite = self.attack_sprites[self.frame_index]
                else:
                    # Animation finished
                    print("Melee Attack Finished - Starting Cooldown") # Debug
                    self.attacking = False
                    self.sprite    = self.idle_sprite
                    # Cooldown timer is now set/decremented by base class
                    # self.cooldown_timer = self.stats.get('cooldown', 0.5) 
                    return
            
            # NO continuous collision check during animation needed for this instant arc attack

        else: # Not attacking
             # Ensure sprite is idle
            self.sprite = self.idle_sprite
             # Cooldown timer decrement is handled by base class
             # if self.cooldown_timer > 0:
             #     self.cooldown_timer -= dt


class RangeWeapon(Weapon):
    def __init__(
        self,
        owner,
        offset: Vector2,
        stats: dict, # Use stats dict
        weapon_idle_sprite: str, # Keep sprite names separate for now
        projectile_sprite_name: str,
    ):
        super().__init__(owner, offset, stats) # Pass stats to base
        # Access stats via self.stats['key']
        self.projectile_sprite_name = projectile_sprite_name
        self.weapon_idle_sprite     = weapon_idle_sprite # Might need this for display
        self.sprite = load_sprite(self.weapon_idle_sprite, with_alpha=True) # Load weapon sprite
        self.projectiles: list[Projectile] = []

    # Modify attack to accept target world position and game_state
    def attack(self, target_pos: Vector2, game_state):
        if self.cooldown_timer <= 0.0: # Check base class cooldown_timer
            # Calculate direction from owner to target
            direction = (target_pos - self.owner.position)
            if direction.length_squared() > 0: # Avoid normalizing zero vector
                direction.normalize_ip()
            else: # If target is on owner, use owner's facing direction
                direction = self.owner.last_direction.copy().normalize()
                
            # Apply accuracy spread (if defined in stats)
            accuracy_angle = self.stats.get('accuracy', 0) # Default to 0 spread
            if accuracy_angle > 0:
                spread_radians = math.radians((random.random() - 0.5) * accuracy_angle)
                direction.rotate_ip_rad(spread_radians)
            
            # Calculate spawn position (owner center + offset)
            spawn_pos = self.owner.rect.center + self.offset 
            
            # Get projectile stats from weapon stats
            proj_speed = self.stats.get('projectile_speed', 300)
            proj_damage = self.stats.get('damage', 5)
            proj_knockback = self.stats.get('knockback', 50)
            proj_stun = self.stats.get('stun_duration', 0.1)
            
            proj = Projectile(
                position=spawn_pos, 
                direction=direction, 
                speed=proj_speed, 
                sprite_name=self.projectile_sprite_name, 
                damage=proj_damage, 
                knockback=proj_knockback, # Pass knockback
                stun=proj_stun # Pass stun
            )
            game_state.projectiles.append(proj) # Add to game_state's list
            self.cooldown_timer = self.stats.get('cooldown', 1.0) # Set base class cooldown_timer

    def update(self, dt, game_state):
        super().update(dt, game_state) # Call base update for position and cooldown dot calculation
        # Cooldown timer decrement is now handled by the base class update
        # if self.timer > 0:
        #     self.timer -= dt
            
        # Projectile updates are now handled by the main game loop via game_state.projectiles
        # We no longer store/update projectiles within the RangeWeapon itself
        # (This simplifies weapon switching and centralizes projectile management)
        # for proj in self.projectiles[:]: 
        #    ...


class Projectile(GameObject):
    def __init__(self, position, direction: Vector2, speed: float, sprite_name: str, damage:float, knockback:float, stun:float):
        # Load the sprite
        sprite = load_sprite(sprite_name, with_alpha=True)
        # Calculate initial velocity
        velocity = direction.normalize() * speed
        super().__init__(position, sprite, velocity)
        self.damage = damage
        self.knockback = knockback
        self.stun = stun
        # Add a lifetime or range limit if desired
        self.lifetime = 5.0 # seconds

    def update(self, dt, game_state):
        # Move the projectile
        self.position += self.velocity * dt
        self.rect.center = self.position
        
        # Decrease lifetime
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.should_be_removed = True # Mark for removal
            return

        # Collision check with enemies
        for enemy in game_state.enemies:
            if not enemy.alive: continue
            
            if self.rect.colliderect(enemy.rect):
                print(f"Projectile hit enemy {id(enemy)}") # Debug
                enemy.take_damage(self.damage)
                self.should_be_removed = True # Mark projectile for removal
                
                # Apply Knockback & Stun
                if self.knockback > 0 and enemy.alive:
                    push_direction = (enemy.position - self.position).normalize() # Push away from impact point
                    if push_direction.length_squared() == 0: # Avoid zero vector if hit dead center
                        push_direction = (enemy.position - game_state.player.position).normalize()
                        if push_direction.length_squared() == 0: push_direction = Vector2(1,0) # Ultimate fallback
                    
                    knockback_speed = self.knockback * 3 # Adjust multiplier
                    knockback_duration = 0.15
                    
                    enemy.knockback_velocity = push_direction * knockback_speed
                    enemy.knockback_timer = knockback_duration
                    enemy.stun_timer = max(enemy.stun_timer, self.stun)
                    enemy.knockback_recovery_timer = max(enemy.knockback_recovery_timer, knockback_duration + 0.3)

                return # Projectile hits one enemy and is removed