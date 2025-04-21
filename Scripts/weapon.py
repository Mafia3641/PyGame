import pygame
from pygame.math import Vector2
from game_object import GameObject
from utils import load_sprite
import random

class Weapon:
    def __init__(self, owner, offset: Vector2):
        self.owner = owner
        self.offset = Vector2(offset)
        self.sprite = None
        self.rect = pygame.Rect(0,0,0,0)

    def update_position(self):
        pos = self.owner.position + self.offset
        self.rect = self.sprite.get_rect()
        self.rect.x = pos.x - self.sprite.get_width() / 2
        self.rect.y = pos.y - self.sprite.get_height()

    def update(self, dt, enemies: list = None):
        self.update_position()

    def draw(self, surface, camera):
        draw_pos = Vector2(self.rect.topleft)
        if camera:
            draw_pos -= Vector2(camera.camera.topleft)
        surface.blit(self.sprite, draw_pos)


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
    
    def attack(self, player_pos, direction, enemies):
        if not self.attacking:
            self.attacking = True
            self.frame_index = 0
            self.timer = 0.0
            
            # Пример проверки попадания
            for enemy in enemies:
                if player_pos.distance_to(enemy.position) <= self.attack_range:
                    enemy.hp -= self.damage
                    print(f"[Melee] Hit enemy for {self.damage} HP")

    def update(self, dt, enemies: list = None):
        super().update(dt)
        if self.attacking:
            self.timer += dt
            if self.timer >= self.frame_duration:
                self.timer -= self.frame_duration
                self.frame_index += 1
                if self.frame_index < len(self.attack_sprites):
                    self.sprite = self.attack_sprites[self.frame_index]
                else:
                    # анимация кончилась
                    self.attacking = False
                    self.sprite    = self.idle_sprite
                    return

            # проверяем попадание по врагам
            if enemies:
                for enemy in enemies:
                    if self.rect.colliderect(enemy.rect):
                        enemy.take_damage(self.damage)
                        # при желании — отталкиваем:
                        push = (enemy.position - self.owner.position).normalize() * self.repulsion
                        enemy.position += push

        else:
            self.sprite = self.idle_sprite


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
        for proj in self.projectiles[:]:
            proj.update(dt)
            # коллизия
            if enemies:
                for enemy in enemies:
                    if proj.rect.colliderect(enemy.rect):
                        enemy.take_damage(proj.damage)
                        push = (enemy.position - self.owner.position).normalize() * proj.repulsion
                        enemy.position += push
                        self.projectiles.remove(proj)
                        break


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