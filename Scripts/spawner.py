import pygame
import random
import math
from pygame.math import Vector2

# Assuming Slime and constants are accessible (adjust imports if needed based on project structure)
# This might require adding Scripts path if spawner.py is outside Scripts
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
        # print(f"Spawner Initialized: Level {self.current_enemy_level}, Active: {self.active}") # Debug

    def _calculate_stats(self, level):
        """Calculates HP and damage for a given enemy level."""
        # Level 1 uses base stats
        if level <= 1:
            return SLIME_BASE_HP, SLIME_BASE_DAMAGE
        
        # Calculate scaled stats for levels > 1
        level_multiplier = level - 1
        hp = SLIME_BASE_HP * (1 + SLIME_HP_INCREASE_PER_LEVEL * level_multiplier)
        damage = SLIME_BASE_DAMAGE * (1 + SLIME_DAMAGE_INCREASE_PER_LEVEL * level_multiplier)
        
        # Return integer values for HP/damage
        return int(hp), int(damage)

    def update(self, dt):
        if not self.active:
            return

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = INITIAL_SPAWN_COOLDOWN # Reset timer
            self._spawn_enemy()

    def _spawn_enemy(self):
        # Calculate spawn position around the player
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(SPAWN_RADIUS_MIN, SPAWN_RADIUS_MAX)
        offset = Vector2(radius, 0).rotate(math.degrees(angle))
        spawn_pos = self.player.position + offset

        # Calculate stats for the current level
        current_hp, current_damage = self._calculate_stats(self.current_enemy_level)
        
        # print(f"Spawning Slime Level {self.current_enemy_level} at {spawn_pos} (Stats: HP={current_hp}, DMG={current_damage})") # Debug

        # Create the enemy instance (Slime for now)
        # Assumes Slime.__init__ is updated to accept hp and damage
        try:
            enemy = Slime(
                position=spawn_pos, 
                target=self.player,
                hp=current_hp,
                damage=current_damage
                # xp_reward remains constant based on SLIME_XP_REWARD in Slime.__init__
            )
            self.game_state.enemies.append(enemy)
        except TypeError as e:
             # print(f"ERROR: Could not spawn Slime. Does its __init__ accept hp and damage? Error: {e}")
             pass # Fail silently for now?
        except Exception as e:
            # print(f"ERROR: Unexpected error spawning Slime: {e}")
            pass # Fail silently for now?


    def next_wave(self):
        self.current_enemy_level += 1
        # print(f"Spawner progressing to Level {self.current_enemy_level} enemies.") # Debug
        if self.current_enemy_level > SLIME_MAX_LEVEL:
            self.active = False
            # print("Spawner reached max enemy level. Deactivating.") # Debug
            
    def is_active(self):
        return self.active 