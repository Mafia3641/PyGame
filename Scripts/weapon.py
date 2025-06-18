import pygame
from pygame.math import Vector2
import math
from game_object import GameObject
from utils import load_sprite
import random
from weapon_stats import WEAPON_STATS
from math import atan2, degrees
from constants import WINDOW_WIDTH, WINDOW_HEIGHT

class Weapon:
    def __init__(self, owner, offset: Vector2, stats: dict):
        self.owner = owner
        self.offset = Vector2(offset)
        self.stats = stats
        self.sprite = None
        self.rect = pygame.Rect(0,0,0,0)
        self.angle = 0
        self.world_position = owner.position + offset
        self.cooldown_timer = 0.0
        self.last_direction = Vector2(1, 0)
        
        self.cooldown_dots = 0
        self.dot_sprite = None
        self._load_dot_sprite()

    def _load_dot_sprite(self):
        try:
            dot_path = "UI/ui_sprites/dot.png"
            self.dot_sprite = pygame.image.load(dot_path).convert_alpha()
        except pygame.error as e:
            self.dot_sprite = None
        except FileNotFoundError:
            self.dot_sprite = None

    def update_position(self):
        if not self.sprite: return
        
        anchor_pos = Vector2(self.owner.rect.center)
        
        base_offset = self.offset
        flip_horizontal = self.owner.last_direction.x < 0
        adjusted_offset = Vector2(-base_offset.x, base_offset.y) if flip_horizontal else base_offset
        
        target_weapon_center = anchor_pos + adjusted_offset
        
        self.rect = self.sprite.get_rect()
        
        self.rect.center = target_weapon_center

    def update(self, dt, game_state):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer < 0:
                self.cooldown_timer = 0

        total_cooldown = self.stats.get('cooldown', 0.0)
        calculated_dots = 0
        if total_cooldown <= 0 or self.cooldown_timer <= 0:
            calculated_dots = 0
        else:
            elapsed_time = total_cooldown - self.cooldown_timer
            quarter_cooldown = total_cooldown / 4.0
            
            if elapsed_time >= 3 * quarter_cooldown:
                calculated_dots = 0
            elif elapsed_time >= 2 * quarter_cooldown:
                calculated_dots = 3
            elif elapsed_time >= 1 * quarter_cooldown:
                calculated_dots = 2
            else:
                calculated_dots = 1
                
        self.cooldown_dots = calculated_dots

        if hasattr(self.owner, 'last_direction'):
            self.last_direction = self.owner.last_direction.copy()
        
        self.world_position = self.owner.position + self.offset.rotate(self.angle)
        
        if self.sprite:
            if self.last_direction.x < 0:
                self.oriented_sprite = pygame.transform.flip(self.sprite, True, False)
            else:
                self.oriented_sprite = self.sprite
                
        if self.sprite:
            self.update_position()

    def draw(self, surface, camera):
        if not self.sprite: return

        flip_horizontal = self.owner.last_direction.x < 0
        
        current_sprite = self.sprite
        
        final_sprite = pygame.transform.flip(current_sprite, flip_horizontal, False)

        temp_obj_for_apply = pygame.sprite.Sprite()
        temp_obj_for_apply.rect = self.rect
        temp_obj_for_apply.image = final_sprite

        screen_rect = camera.apply(temp_obj_for_apply)

        surface.blit(final_sprite, screen_rect.topleft)

    def get_cooldown_dots(self):
        
        return self.cooldown_dots, self.dot_sprite

    def attack(self, target_pos: Vector2, game_state):
        
        raise NotImplementedError("Subclasses must implement the attack method")


class MeleeWeapon(Weapon):
    def __init__(
        self,
        owner,
        offset: Vector2,
        stats: dict,
        idle_sprite_name: str,
        attack_sprite_names: list[str],
        frame_duration: float = 0.1
    ):
        super().__init__(owner, offset, stats)
        self.idle_sprite    = load_sprite(idle_sprite_name, with_alpha=True)
        self.attack_sprites = [load_sprite(n, with_alpha=True) for n in attack_sprite_names]
        
        scale = self.stats.get('scale', 1)
        if scale != 1:
            w, h = self.idle_sprite.get_size()
            self.idle_sprite = pygame.transform.scale(self.idle_sprite, (int(w * scale), int(h * scale)))
            self.attack_sprites = [pygame.transform.scale(s, (int(s.get_width() * scale), int(s.get_height() * scale))) for s in self.attack_sprites]

        self.sprite         = self.idle_sprite
        self.attacking      = False
        self.frame_index    = 0
        self.timer          = 0.0
        self.frame_duration = frame_duration
        self.cooldown_timer = 0.0
        self.attack_arc_rad = math.radians(self.stats.get('attack_arc', 360))
        self.half_arc_rad = self.attack_arc_rad / 2
        self.current_attack_direction = Vector2(1, 0)
    
    def update_position(self):
        if not self.sprite: return
        
        anchor_pos = Vector2(self.owner.rect.center)
        
        base_offset = self.offset
        flip_horizontal = self.owner.last_direction.x < 0

        if flip_horizontal:
            adjusted_offset = Vector2(-base_offset.x + 20, base_offset.y)
        else:
            adjusted_offset = Vector2(base_offset.x - 2, base_offset.y)
        
        target_weapon_center = anchor_pos + adjusted_offset
        
        self.rect = self.sprite.get_rect()
        
        self.rect.center = target_weapon_center

    def attack(self, target_pos: Vector2, game_state):
        if not self.attacking and self.cooldown_timer <= 0:
            self.attacking = True
            self.frame_index = 0
            self.timer = 0.0
            self.hit_enemies_this_attack = set()
            
            self.sprite = self.attack_sprites[0]
            self.update_position()
            
            owner_pos = self.owner.position
            direction = target_pos - owner_pos
            if direction.length_squared() > 0:
                 self.current_attack_direction = direction.normalize()
            else:
                 self.current_attack_direction = self.owner.last_direction.copy().normalize()
                 if self.current_attack_direction.length_squared() == 0:
                     self.current_attack_direction = Vector2(1, 0)

            
            self.cooldown_timer = self.stats.get('cooldown', 0.5)

    def update(self, dt, game_state):
        super().update(dt, game_state)
        
        if self.sprite:
            self.update_position()
        
        if self.attacking:
            self.timer += dt
            if self.timer >= self.frame_duration:
                self.timer %= self.frame_duration
                self.frame_index += 1
                if self.frame_index >= len(self.attack_sprites):
                    self.attacking = False
                    self.frame_index = 0
                    self.sprite = self.idle_sprite
                    return
                else:
                    self.sprite = self.attack_sprites[self.frame_index]
            
            if self.frame_index < 3:
                owner_pos = self.owner.position
                attack_range_sq = self.stats.get('range', 50) ** 2
                attack_direction = self.current_attack_direction
                if attack_direction.length_squared() == 0: attack_direction = Vector2(1,0)
                
                for enemy in game_state.enemies:
                    if enemy not in self.hit_enemies_this_attack:
                        if not enemy.alive:
                            continue
                        enemy_vec = enemy.position - owner_pos
                        if enemy_vec.length_squared() < attack_range_sq:
                            if attack_direction.length() > 0 and enemy_vec.length() > 0:
                                angle_between = attack_direction.angle_to(enemy_vec)
                                if abs(angle_between) <= math.degrees(self.half_arc_rad):
                                    enemy.take_damage(self.stats.get('damage', 0))
                                    enemy.apply_knockback(attack_direction, self.stats.get('repulsion', 0), 0.1)
                                    self.hit_enemies_this_attack.add(enemy)

        else:
            self.sprite = self.idle_sprite
            self.update_position()


class RangeWeapon(Weapon):
    def __init__(
        self,
        owner,
        offset: Vector2,
        stats: dict,
        weapon_idle_sprite: str,
        projectile_sprite_name: str,
    ):
        super().__init__(owner, offset, stats)
        self.idle_sprite = load_sprite(weapon_idle_sprite, with_alpha=True)
        
        scale = self.stats.get('scale', 1)
        if scale != 1:
            w, h = self.idle_sprite.get_size()
            self.idle_sprite = pygame.transform.scale(self.idle_sprite, (w * scale, h * scale))
            
        self.sprite = self.idle_sprite
        self.projectile_sprite_name = projectile_sprite_name
        self.angle = 0
        self.facing_left = False

    def update_position(self):
        if not self.sprite: return

        anchor_pos = Vector2(self.owner.rect.center)
        
        adjusted_offset = self.offset.copy()
        if self.owner.last_direction.x < 0:
            adjusted_offset.x -= 17
        
        weapon_pos = anchor_pos + adjusted_offset
        
        self.rect = self.idle_sprite.get_rect(center=weapon_pos)

    def attack(self, target_pos: Vector2, game_state):
        if self.cooldown_timer > 0:
            return

        mana_cost = self.stats.get('mana_cost', 0)
        if mana_cost > 0:
            if hasattr(self.owner, 'consume_mana'):
                if not self.owner.consume_mana(mana_cost):
                    return

        owner_pos = self.owner.position
        direction = target_pos - owner_pos
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = Vector2(1, 0)

        accuracy_degrees = self.stats.get('accuracy', 0)
        if accuracy_degrees > 0:
            spread = random.uniform(-accuracy_degrees, accuracy_degrees)
            direction.rotate_ip(spread)
        
        projectile_speed = self.stats.get('projectile_speed', 300)
        damage = self.stats.get('damage', 5)
        knockback = self.stats.get('repulsion', 0)
        stun = self.stats.get('stun', 0.1)

        projectile = Projectile(
            position=self.rect.center,
            direction=direction,
            speed=projectile_speed,
            sprite_name=self.projectile_sprite_name,
            damage=damage,
            knockback=knockback,
            stun=stun
        )
        game_state.projectiles.append(projectile)

        self.cooldown_timer = self.stats.get('cooldown', 0.5)

    def update(self, dt, game_state):
        super().update(dt, game_state)
        
        mouse_world_pos = game_state.get_mouse_world_pos()
        direction = mouse_world_pos - (self.owner.position + self.offset)
        if direction.length_squared() > 0:
            self.angle = direction.angle_to(Vector2(1,0))
            self.facing_left = mouse_world_pos.x < self.owner.position.x

        self.update_position()

    def draw(self, surface, camera):
        if not self.idle_sprite: return

        weapon_world_pos = Vector2(self.rect.center)
        
        sprite_to_rotate = self.idle_sprite
        
        if self.facing_left:
            sprite_to_rotate = pygame.transform.flip(self.idle_sprite, True, False)
            draw_angle = self.angle + 180 if self.angle > 0 else self.angle - 180
        else:
            draw_angle = self.angle
        
        rotated_sprite = pygame.transform.rotate(sprite_to_rotate, draw_angle)
        
        rotated_rect = rotated_sprite.get_rect(center=weapon_world_pos)
        
        temp_obj_for_apply = pygame.sprite.Sprite()
        temp_obj_for_apply.rect = rotated_rect
        temp_obj_for_apply.image = rotated_sprite
        
        screen_rect = camera.apply(temp_obj_for_apply)
        
        surface.blit(rotated_sprite, screen_rect.topleft)

class Projectile(GameObject):
    def __init__(self, position, direction: Vector2, speed: float, sprite_name: str, damage: float, knockback: float, stun: float):
        sprite_path = f"Weapons/RangeWeapons/bullet1"
        sprite = load_sprite(sprite_path, with_alpha=True)
        
        angle = degrees(atan2(-direction.y, direction.x))
        rotated_sprite = pygame.transform.rotate(sprite, angle)

        super().__init__(position, rotated_sprite, direction * speed)
        self.rect = self.sprite.get_rect(center=self.position)
        self.damage = damage
        self.knockback = knockback
        self.stun = stun
        self.lifetime = 5
        self.is_dead = False

    def update(self, dt, game_state):
        for enemy in game_state.enemies:
            if not enemy.alive:
                continue
            if self.rect.colliderect(enemy.rect):
                enemy.take_damage(self.damage)
                enemy.apply_knockback(self.velocity.normalize(), self.knockback, self.stun)
                self.is_dead = True
                return

        self.position += self.velocity * dt
        self.rect.center = self.position

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_dead = True
            return

class Pistol(RangeWeapon):
    def __init__(self, owner, offset: Vector2 = Vector2(15, 10)):
        stats = WEAPON_STATS['pistol']
        idle_sprite_name = "Weapons/RangeWeapons/Pistol/pistol_idle_1"
        projectile_sprite_name = "Weapons/RangeWeapons/bullet1"

        stats['projectile_sprite_name'] = projectile_sprite_name

        super().__init__(
            owner=owner,
            offset=offset,
            stats=stats,
            weapon_idle_sprite=idle_sprite_name,
            projectile_sprite_name=projectile_sprite_name
        )

    def attack(self, target_pos: Vector2, game_state):
        super().attack(target_pos, game_state)

        owner_pos = self.owner.position
        direction = (target_pos - owner_pos).normalize() if (target_pos - owner_pos).length_squared() > 0 else self.owner.last_direction

        range_sq = self.stats.get('close_quarters_range', 0) ** 2
        half_arc_rad = math.radians(self.stats.get('close_quarters_arc', 0) / 2)

        if range_sq == 0 or half_arc_rad == 0:
            return

        for enemy in game_state.enemies:
            if not enemy.alive:
                continue

            enemy_vec = enemy.position - owner_pos
            if enemy_vec.length_squared() < range_sq:
                if direction.length() > 0 and enemy_vec.length() > 0:
                    angle_to_enemy = direction.angle_to(enemy_vec.normalize())
                    if abs(math.radians(angle_to_enemy)) < half_arc_rad:
                        enemy.take_damage(self.stats.get('damage', 0))
                        enemy.apply_knockback(direction, self.stats.get('repulsion', 0), 0.1)
