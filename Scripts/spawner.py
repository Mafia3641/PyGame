import pygame
import random
import math
from pygame.math import Vector2

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
	sys.path.append(project_root)

from Scripts.enemy import Slime
from Scripts.constants import (INITIAL_SPAWN_COOLDOWN, SPAWN_RADIUS_MIN, SPAWN_RADIUS_MAX,
                             SLIME_MAX_LEVEL, SLIME_BASE_HP, SLIME_BASE_DAMAGE,
                             SLIME_HP_INCREASE_PER_LEVEL, SLIME_DAMAGE_INCREASE_PER_LEVEL)

class Spawner:
    def __init__(self, player_ref, game_state_ref):
        self.player = player_ref
        self.game_state = game_state_ref
        self.spawn_timer = INITIAL_SPAWN_COOLDOWN
        self.current_enemy_level = 1
        self.active = True

    def _calculate_stats(self, level):
        
        if level <= 1:
            return SLIME_BASE_HP, SLIME_BASE_DAMAGE
        
        level_multiplier = level - 1
        hp = SLIME_BASE_HP * (1 + SLIME_HP_INCREASE_PER_LEVEL * level_multiplier)
        damage = SLIME_BASE_DAMAGE * (1 + SLIME_DAMAGE_INCREASE_PER_LEVEL * level_multiplier)
        
        return int(hp), int(damage)

    def update(self, dt):
        if not self.active:
            return

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = INITIAL_SPAWN_COOLDOWN
            self._spawn_enemy()

    def _spawn_enemy(self):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(SPAWN_RADIUS_MIN, SPAWN_RADIUS_MAX)
        offset = Vector2(radius, 0).rotate(math.degrees(angle))
        spawn_pos = self.player.position + offset

        current_hp, current_damage = self._calculate_stats(self.current_enemy_level)
        

        try:
            enemy = Slime(
                position=spawn_pos,
                target=self.player,
                hp=current_hp,
                damage=current_damage
            )
            self.game_state.enemies.append(enemy)
        except TypeError as e:
             pass
        except Exception as e:
            pass


    def next_wave(self):
        self.current_enemy_level += 1
        if self.current_enemy_level > SLIME_MAX_LEVEL:
            self.active = False
            
    def is_active(self):
        return self.active