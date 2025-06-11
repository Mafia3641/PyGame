import pygame
from pygame.math import Vector2
import math # Import math module
from game_object import GameObject
from utils import load_sprite
import random
from weapon_stats import WEAPON_STATS
from math import atan2, degrees
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
            # print(f"Warning: Could not load sprite for dots ({dot_path}): {e}")
            self.dot_sprite = None
        except FileNotFoundError:
            # print(f"Warning: Sprite file for dots not found: {dot_path}")
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
        # if self.cooldown_timer > 0: # Only print during active cooldown
            # print(f"  Weapon Cooldown - Timer: {self.cooldown_timer:.2f}/{total_cooldown:.2f}, Elapsed: {elapsed_time:.2f}, Dots: {self.cooldown_dots}")
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
        if not self.sprite: return

        # Flip based on owner's direction
        flip_horizontal = self.owner.last_direction.x < 0
        
        # Correctly get the final sprite to be drawn (could be from an animation)
        # For base weapon, it's just the one sprite. For subclasses, this might be different.
        current_sprite = self.sprite
        
        final_sprite = pygame.transform.flip(current_sprite, flip_horizontal, False)

        # Create a dummy object for camera application
        temp_obj_for_apply = pygame.sprite.Sprite()
        temp_obj_for_apply.rect = self.rect # World rect
        temp_obj_for_apply.image = final_sprite # The sprite to be drawn

        screen_rect = camera.apply(temp_obj_for_apply)

        # Blit the final, correctly oriented sprite
        surface.blit(final_sprite, screen_rect.topleft)

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
        
        # Get scale from stats, default to 1 if not present
        scale = self.stats.get('scale', 1)
        if scale != 1:
            # Scale idle sprite
            w, h = self.idle_sprite.get_size()
            self.idle_sprite = pygame.transform.scale(self.idle_sprite, (int(w * scale), int(h * scale)))
            # Scale attack sprites
            self.attack_sprites = [pygame.transform.scale(s, (int(s.get_width() * scale), int(s.get_height() * scale))) for s in self.attack_sprites]

        # текущее состояние анимации
        self.sprite         = self.idle_sprite
        self.attacking      = False
        self.frame_index    = 0
        self.timer          = 0.0
        self.frame_duration = frame_duration
        self.cooldown_timer = 0.0 # Add cooldown timer
        self.attack_arc_rad = math.radians(self.stats.get('attack_arc', 360)) # Get arc from stats, default to 360
        self.half_arc_rad = self.attack_arc_rad / 2
        self.current_attack_direction = Vector2(1, 0) # Store direction of the current swing
    
    def update_position(self):
        if not self.sprite: return # Should not happen if called from update check, but safer
        
        # Anchor the weapon to the owner's visual rect center
        anchor_pos = Vector2(self.owner.rect.center)
        
        # --- Adjust offset based on owner direction --- 
        base_offset = self.offset
        flip_horizontal = self.owner.last_direction.x < 0

        if flip_horizontal:
            # When looking left, move 20px to the right from the mirrored position
            adjusted_offset = Vector2(-base_offset.x + 20, base_offset.y)
        else:
            # When looking right, move 2px to the left from the standard position
            adjusted_offset = Vector2(base_offset.x - 2, base_offset.y)
        # --------------------------------------------
        
        # Apply the adjusted offset to the anchor position
        target_weapon_center = anchor_pos + adjusted_offset
        
        # Get the weapon sprite's rect (to know its size)
        # Re-fetch the *original* sprite's rect for size, center it later
        self.rect = self.sprite.get_rect()
        
        # Set the weapon rect's center to the calculated target position
        self.rect.center = target_weapon_center

    # Override attack method for directional arc
    def attack(self, target_pos: Vector2, game_state):
        # Start attack only if not already attacking and cooldown is ready
        if not self.attacking and self.cooldown_timer <= 0:
            self.attacking = True
            self.frame_index = 0
            self.timer = 0.0
            self.hit_enemies_this_attack = set() # Reset hit set for THIS swing
            
            # Set first attack frame immediately
            self.sprite = self.attack_sprites[0]
            self.update_position() # Position weapon for the first frame
            
            # Calculate and store attack direction for this swing
            owner_pos = self.owner.position
            direction = target_pos - owner_pos
            if direction.length_squared() > 0:
                 self.current_attack_direction = direction.normalize()
            else: # Target is on player, use player facing as fallback
                 self.current_attack_direction = self.owner.last_direction.copy().normalize()
                 # Ensure fallback isn't zero vector
                 if self.current_attack_direction.length_squared() == 0:
                     self.current_attack_direction = Vector2(1, 0)

            # print("Melee Attack Started") # Debug
            
            # --- Start Cooldown --- #
            self.cooldown_timer = self.stats.get('cooldown', 0.5) # Start cooldown immediately

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
            # Check if it's time to advance frame
            if self.timer >= self.frame_duration:
                self.timer %= self.frame_duration
                self.frame_index += 1
                # Check if animation finished
                if self.frame_index >= len(self.attack_sprites):
                    self.attacking = False
                    self.frame_index = 0
                    self.sprite = self.idle_sprite # Return to idle
                    # Cooldown is already running from attack()
                    return # End update for this frame after animation finishes
                else:
                    self.sprite = self.attack_sprites[self.frame_index]
            
            # --- Hit Detection DURING First 3 Frames of Animation --- #
            if self.frame_index < 3: # Only check for hits during frames 0, 1, 2
                owner_pos = self.owner.position
                attack_range_sq = self.stats.get('range', 50) ** 2 
                attack_direction = self.current_attack_direction
                if attack_direction.length_squared() == 0: attack_direction = Vector2(1,0) # Fallback just in case
                
                for enemy in game_state.enemies: 
                    if enemy not in self.hit_enemies_this_attack: # Hit each enemy only once per swing
                        if not enemy.alive:
                            continue
                        enemy_vec = enemy.position - owner_pos
                        if enemy_vec.length_squared() < attack_range_sq:
                            # --- Arc-based Hit Detection --- #
                            if attack_direction.length() > 0 and enemy_vec.length() > 0:
                                angle_between = attack_direction.angle_to(enemy_vec)
                                if abs(angle_between) <= math.degrees(self.half_arc_rad):
                                    # print(f"  Enemy {enemy} hit within arc.") # Debug
                                    enemy.take_damage(self.stats.get('damage', 0))
                                    enemy.apply_knockback(attack_direction, self.stats.get('repulsion', 0), 0.1) # Repulsion is knockback strength
                                    self.hit_enemies_this_attack.add(enemy)
                            # ----------------------------- #

        else: # Not attacking, sprite should be idle
            self.sprite = self.idle_sprite
            self.update_position()


class RangeWeapon(Weapon):
    def __init__(
        self,
        owner,
        offset: Vector2,
        stats: dict, # Use stats dict
        weapon_idle_sprite: str, # Keep sprite names separate for now
        projectile_sprite_name: str,
    ):
        super().__init__(owner, offset, stats)
        # Load sprites
        self.idle_sprite = load_sprite(weapon_idle_sprite, with_alpha=True)
        self.sprite = self.idle_sprite
        self.projectile_sprite_name = projectile_sprite_name
        self.angle = 0 # For aiming visual

    def update_position(self):
        if not self.sprite: return

        anchor_pos = Vector2(self.owner.rect.center)
        
        # We don't use horizontal flip for ranged aiming, aiming is done with rotation
        target_weapon_center = anchor_pos + self.offset.rotate(-self.angle)
        
        # Use the idle_sprite for the rect calculation to have a consistent size before rotation
        self.rect = self.idle_sprite.get_rect(center=target_weapon_center)

    def attack(self, target_pos: Vector2, game_state):
        if self.cooldown_timer > 0:
            return # Can't attack while on cooldown

        # --- Mana Cost ---
        mana_cost = self.stats.get('mana_cost', 0)
        if mana_cost > 0:
            if hasattr(self.owner, 'consume_mana'):
                if not self.owner.consume_mana(mana_cost):
                    # print("Not enough mana!") # Optional debug message
                    return # Block attack if not enough mana
        # -----------------

        # Calculate direction from owner to target
        owner_pos = self.owner.position
        direction = target_pos - owner_pos
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = Vector2(1, 0) # Fallback if target is on owner

        # --- Accuracy --- #
        accuracy_degrees = self.stats.get('accuracy', 0)
        if accuracy_degrees > 0:
            spread = random.uniform(-accuracy_degrees, accuracy_degrees)
            direction.rotate_ip(spread) # In-place rotation
        # ---------------- #
        
        # Get projectile stats from weapon stats
        projectile_speed = self.stats.get('projectile_speed', 300)
        damage = self.stats.get('damage', 5)
        knockback = self.stats.get('repulsion', 0) # Use 'repulsion' for knockback
        stun = self.stats.get('stun', 0.1)

        # Create the projectile
        projectile = Projectile(
            position=self.rect.center, # Start from the weapon's sprite center
            direction=direction,
            speed=projectile_speed,
            sprite_name=self.projectile_sprite_name,
            damage=damage,
            knockback=knockback,
            stun=stun
        )
        game_state.projectiles.append(projectile)

        # Start cooldown
        self.cooldown_timer = self.stats.get('cooldown', 0.5)

    def update(self, dt, game_state):
        # Base update for cooldown
        super().update(dt, game_state)
        
        # Aim towards mouse
        mouse_world_pos = game_state.get_mouse_world_pos()
        direction = mouse_world_pos - (self.owner.position + self.offset)
        if direction.length_squared() > 0:
             self.angle = -direction.angle_to(Vector2(1,0)) # Negate for pygame's y-down coord system

        # Update position after angle is set
        self.update_position()
        
    def draw(self, surface, camera):
        if not self.idle_sprite: return # Use idle_sprite as the source

        # --- Aiming Rotation --- #
        # Rotate the original idle sprite
        rotated_sprite = pygame.transform.rotate(self.idle_sprite, self.angle)
        
        # Flip based on aim direction (more intuitive for ranged)
        # We check if the angle is pointing to the left side of the screen
        # Angles in pygame: 0 is right, 90 is down, 180 is left, 270 is up
        flip_horizontal = abs(self.angle) > 90

        if flip_horizontal:
            # Flip the original sprite vertically (up/down)
            flipped_orig_sprite = pygame.transform.flip(self.idle_sprite, False, True)
            # Then rotate it. This keeps the "top" of the gun pointing correctly.
            final_sprite = pygame.transform.rotate(flipped_orig_sprite, self.angle)
        else:
            final_sprite = rotated_sprite # Use the already rotated sprite

        # Create a new rect for the rotated sprite to position it correctly
        rotated_rect = final_sprite.get_rect(center=self.rect.center)
        
        # Create a dummy object for camera application
        temp_obj_for_apply = pygame.sprite.Sprite()
        temp_obj_for_apply.rect = rotated_rect # Use the new rotated rect
        temp_obj_for_apply.image = final_sprite
        
        screen_rect = camera.apply(temp_obj_for_apply)
        
        surface.blit(final_sprite, screen_rect.topleft)

class Projectile(GameObject):
    def __init__(self, position, direction: Vector2, speed: float, sprite_name: str, damage: float, knockback: float, stun: float):
        sprite_path = f"Weapons/RangeWeapons/bullet1"
        sprite = load_sprite(sprite_path, with_alpha=True)
        
        # Rotate sprite to match direction
        angle = degrees(atan2(-direction.y, direction.x))
        rotated_sprite = pygame.transform.rotate(sprite, angle)

        super().__init__(position, rotated_sprite, direction * speed)
        self.rect = self.sprite.get_rect(center=self.position) # Ensure rect is centered correctly
        self.damage = damage
        self.knockback = knockback
        self.stun = stun
        self.lifetime = 5  # seconds
        self.is_dead = False # Flag for removal

    def update(self, dt, game_state):
        # Collision check with enemies should happen *before* moving
        # This prevents the projectile from "tunneling" through an enemy on its first frame
        for enemy in game_state.enemies:
            if not enemy.alive:
                continue
            if self.rect.colliderect(enemy.rect):
                enemy.take_damage(self.damage)
                enemy.apply_knockback(self.velocity.normalize(), self.knockback, self.stun)
                self.is_dead = True
                return # A projectile hits only one enemy and disappears

        # Move the projectile if no collision occurred
        self.position += self.velocity * dt
        self.rect.center = self.position

        # Lifetime check
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_dead = True
            return

class Pistol(RangeWeapon):
    def __init__(self, owner, offset: Vector2 = Vector2(15, 10)):
        stats = WEAPON_STATS['pistol']
        idle_sprite_name = "Weapons/RangeWeapons/Pistol/pistol_idle_1"
        projectile_sprite_name = "Weapons/RangeWeapons/bullet1"

        # Correctly get the stats for the projectile from the stats dict
        stats['projectile_sprite_name'] = projectile_sprite_name

        super().__init__(
            owner=owner,
            offset=offset,
            stats=stats,
            weapon_idle_sprite=idle_sprite_name,
            projectile_sprite_name=projectile_sprite_name
        )
        
        # Scale the pistol sprite by 2x
        w, h = self.sprite.get_size()
        self.sprite = pygame.transform.scale(self.sprite, (w * 2, h * 2))

    def attack(self, target_pos: Vector2, game_state):
        # First, perform the standard ranged attack to fire a projectile
        super().attack(target_pos, game_state)

        # Now, add an instantaneous melee-style check for point-blank targets
        owner_pos = self.owner.position
        direction = (target_pos - owner_pos).normalize() if (target_pos - owner_pos).length_squared() > 0 else self.owner.last_direction

        range_sq = self.stats.get('close_quarters_range', 0) ** 2
        half_arc_rad = math.radians(self.stats.get('close_quarters_arc', 0) / 2)

        if range_sq == 0 or half_arc_rad == 0:
            return # Skip if stats are not defined

        for enemy in game_state.enemies:
            if not enemy.alive:
                continue

            enemy_vec = enemy.position - owner_pos
            if enemy_vec.length_squared() < range_sq:
                if direction.length() > 0 and enemy_vec.length() > 0:
                    angle_to_enemy = direction.angle_to(enemy_vec.normalize())
                    if abs(math.radians(angle_to_enemy)) < half_arc_rad:
                        # Apply damage and effects
                        enemy.take_damage(self.stats.get('damage', 0))
                        enemy.apply_knockback(direction, self.stats.get('repulsion', 0), 0.1)
                        # We don't need a "hit_this_attack" set because it's instant
                        # and the projectile is a separate entity.