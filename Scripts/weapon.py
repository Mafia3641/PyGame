import pygame
from pygame.math import Vector2
from game_object import GameObject
from utils import load_sprite
import random
# Import constants for screen dimensions
from constants import WINDOW_WIDTH, WINDOW_HEIGHT 

class Weapon:
    def __init__(self, owner, offset: Vector2):
        self.owner = owner
        self.offset = Vector2(offset)
        self.sprite = None
        self.rect = pygame.Rect(0,0,0,0)

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

    def update(self, dt, enemies: list = None):
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


class MeleeWeapon(Weapon):
    def __init__(
        self,
        owner,
        offset: Vector2,
        idle_sprite_name: str,
        attack_sprite_names: list[str],
        damage: float,
        attack_range: float,
        cooldown: float,
        repulsion: float,
        frame_duration: float = 0.1
    ):
        super().__init__(owner, offset)
        # базовые характеристики
        self.damage         = damage
        self.attack_range   = attack_range
        self.cooldown       = cooldown
        self.repulsion      = repulsion
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
    
    def attack(self, player_pos, direction, enemies):
        # Start attack only if not already attacking and cooldown is ready
        if not self.attacking and self.cooldown_timer <= 0:
            self.attacking = True
            self.frame_index = 0
            self.timer = 0.0
            # self.hit_enemies_this_attack = set() # No longer needed
            
            # Set first attack frame immediately
            self.sprite = self.attack_sprites[0]
            self.update_position() # Position weapon for the first frame collision check
            
            print("Melee Attack Started - Checking Hits Now") # Debug
            # --- Check for hits only at the start of the attack --- 
            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):
                    print(f"Hit enemy {id(enemy)} at start of attack") # Debug
                    enemy.take_damage(self.damage)
                    # Apply knockback velocity
                    push_direction = (enemy.position - self.owner.position).normalize()
                    knockback_speed = 400 
                    knockback_duration = 0.25
                    enemy.knockback_velocity = push_direction * knockback_speed
                    enemy.knockback_timer = knockback_duration
                    enemy.stun_timer = knockback_duration 
                    enemy.knockback_recovery_timer = knockback_duration + 0.5
            # -------------------------------------------------------

    def update(self, dt, enemies: list = None):
        # Update position based on current sprite first (applies adjusted offset)
        # This needs to happen regardless of attacking state
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
                    # Position update happens at start of next update call
                else:
                    # Animation finished
                    print("Melee Attack Finished - Starting Cooldown") # Debug
                    self.attacking = False
                    self.sprite    = self.idle_sprite
                    self.cooldown_timer = self.cooldown # Start cooldown NOW
                    # Position update for idle sprite happens at start of next update call
                    return
            
            # --- REMOVED collision check loop from here --- 
            # Collision check now only happens in attack() method

        else: # Not attacking
             # Ensure sprite is idle (might be redundant but safe)
            self.sprite = self.idle_sprite
             # Decrement cooldown timer if active
            if self.cooldown_timer > 0:
                self.cooldown_timer -= dt
            # Position update for idle sprite happens at start of next update call


class RangeWeapon(Weapon):
    def __init__(
        self,
        owner,
        offset: Vector2,
        weapon_ilde_sprite,
        projectile_speed: float,
        projectile_sprite_name: str,
        damage: float,
        cooldown: float,
        accuracy: float,
        repulsion: float
    ):
        super().__init__(owner, offset)
        self.projectile_speed      = projectile_speed
        self.projectile_sprite_name= projectile_sprite_name
        self.weapon_idle_sprite    = weapon_ilde_sprite
        self.damage                = damage
        self.cooldown              = cooldown
        self.accuracy              = accuracy  # угол разброса
        self.repulsion             = repulsion
        self.timer                 = 0.0
        self.projectiles: list[Projectile] = []

    def shoot(self, direction: Vector2):
        if self.timer <= 0.0:
            # небольшое варьирование направления по точности
            spread = (Vector2(direction).rotate((random.random() - 0.5)*self.accuracy))
            pos = self.owner.position + self.offset
            proj = Projectile(pos, spread, self.projectile_speed, self.projectile_sprite_name, self.damage, self.repulsion)
            self.projectiles.append(proj)
            self.timer = self.cooldown

    def update(self, dt, enemies: list = None):
        super().update(dt)
        if self.timer > 0:
            self.timer -= dt
            
        # --- Define projectile cleanup distance --- 
        # Use screen dimensions (consider maybe 1.5 times the larger dimension)
        max_dist_sq = (max(WINDOW_WIDTH, WINDOW_HEIGHT) * 1.5) ** 2
        player_pos = self.owner.position
        # -----------------------------------------

        for proj in self.projectiles[:]: # Iterate over a copy for safe removal
            proj.update(dt)
            removed = False # Flag to check if removed by collision

            # --- Cleanup based on distance from player --- 
            if (proj.position - player_pos).length_squared() > max_dist_sq:
                self.projectiles.remove(proj)
                continue # Skip collision check if removed
            # -------------------------------------------

            # Collision check with enemies
            if enemies:
                for enemy in enemies:
                    if proj.rect.colliderect(enemy.rect):
                        enemy.take_damage(proj.damage)
                        # --- Apply knockback velocity --- 
                        push_direction = (enemy.position - self.owner.position).normalize()
                        knockback_speed = 400
                        knockback_duration = 0.25
                        enemy.knockback_velocity = push_direction * knockback_speed
                        enemy.knockback_timer = knockback_duration
                        enemy.stun_timer = knockback_duration # Prevent AI during knockback
                        enemy.knockback_recovery_timer = knockback_duration + 0.5 # Slow move after knockback
                        # --------------------------------
                        self.projectiles.remove(proj)
                        removed = True
                        break # Stop checking enemies for this projectile
            # No need to check distance again if removed by collision
            # if removed:
            #     continue


class Projectile(GameObject):
    def __init__(self, position, direction: Vector2, speed: float, sprite_name: str, damage:float, repulsion:float):
        sprite   = load_sprite(sprite_name, with_alpha=True)
        velocity = direction.normalize() * speed
        super().__init__(position, sprite, velocity)
        self.damage    = damage
        self.repulsion = repulsion

    def update(self, dt):
        self.position += self.velocity * dt
        self.rect.x = self.position.x - self.sprite.get_width()/2
        self.rect.y = self.position.y - self.sprite.get_height()