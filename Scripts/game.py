import pygame
import sys
from utils import load_sprite
from models import Player
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from camera import Camera
from enemy import Slime
from weapon import RangeWeapon, MeleeWeapon

class Game:
    def __init__(self):
        self._init_pygame()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.background = load_sprite("grass", False)
        self.background_width = self.background.get_width()
        self.background_height = self.background.get_height()
        self.scaled_background = None # Cache for scaled background
        self.last_camera_zoom = None  # To detect zoom changes
    
        self.player = Player(position=(400, 300))
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.enemies = []
        self.player.game_enemies = self.enemies
        self.clock = pygame.time.Clock()

    def main_loop(self):
        self._spawn_enemy(enemy_type='Slime', position=(420, 350))
        self._spawn_enemy(enemy_type='Slime', position=(450, 350))
        self.player.pickup_weapon('starter_sword')
        while True:
            dt = self.clock.tick(FPS) / 1000
            self._handle_events()
            self._process_game_logic(dt)
            self._draw()
        
            

    def _init_pygame(self):
        pygame.init()
        pygame.display.set_caption("Terra")

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # ЛКМ
                if self.player.active_weapon:
                    self.player.active_weapon.attack(self.player.position, self.player.direction, self.enemies)
        
        
    def _process_game_logic(self, dt):
        self.player.update(self.camera, dt)
        self.enemies = [enemy for enemy in self.enemies if not enemy.should_be_removed]
        for enemy in self.enemies:
            enemy.update(dt)
        self.player.active_weapon.update(dt, self.enemies)
    
    def _spawn_enemy(self, enemy_type: str, position: tuple):
        if enemy_type.lower() == 'slime':
            enemy = Slime(position, target=self.player)
            self.enemies.append(enemy)
            print("Slime created")
    
    
    def _draw_background(self):
        """
        Draws the background tiles, scaled and positioned correctly according to the camera zoom.
        Calculates the visible world area and draws only the necessary tiles.
        """
        self.screen.fill((0, 0, 0)) # Clear screen
        
        zoom = self.camera.zoom
        # --- Check if background needs rescaling --- 
        if zoom != self.last_camera_zoom or self.scaled_background is None:
            scaled_bg_width = int(self.background_width * zoom)
            scaled_bg_height = int(self.background_height * zoom)
            if scaled_bg_width > 0 and scaled_bg_height > 0:
                print(f"Rescaling background for zoom: {zoom}") # Debug print
                self.scaled_background = pygame.transform.scale(self.background, (scaled_bg_width, scaled_bg_height))
                self.last_camera_zoom = zoom
            else:
                # Handle invalid scale size (e.g., zoom too small)
                self.scaled_background = None 
        # -----------------------------------------

        if self.scaled_background is None: # If scaling failed or zoom is 0
            return # Don't draw background

        inv_zoom = 1.0 / zoom
        
        # Calculate the visible world area
        world_view_width = self.camera.width * inv_zoom
        world_view_height = self.camera.height * inv_zoom
        world_view_left = self.camera.camera.x
        world_view_top = self.camera.camera.y
        world_view_rect = pygame.Rect(world_view_left, world_view_top, world_view_width, world_view_height)

        # Use the cached scaled background dimensions
        scaled_bg_width = self.scaled_background.get_width()
        scaled_bg_height = self.scaled_background.get_height()

        # Calculate the range of tiles needed
        start_col = int(world_view_left // self.background_width)
        end_col = int((world_view_left + world_view_width) // self.background_width) + 1
        start_row = int(world_view_top // self.background_height)
        end_row = int((world_view_top + world_view_height) // self.background_height) + 1

        # Draw the necessary tiles
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                # World position of the top-left corner of the tile
                tile_world_x = col * self.background_width
                tile_world_y = row * self.background_height
                
                # Screen position calculation (similar to camera.apply)
                screen_x = (tile_world_x - world_view_left) * zoom
                screen_y = (tile_world_y - world_view_top) * zoom
                
                self.screen.blit(self.scaled_background, (int(screen_x), int(screen_y)))

    def _draw(self):
        # Отрисовываем фон каждый кадр: всего 9 тайлов, что даст эффект бесконечного мира,
        # при этом игрок всегда оказывается по центру экрана.
        self._draw_background()
        # Отрисовываем игрока с учетом смещения камеры
        render_objects = [self.player] + self.enemies
        if isinstance(self.player.active_weapon, RangeWeapon):
            render_objects += self.player.active_weapon.projectiles
        render_objects.sort(key=lambda obj: obj.position.y)
        
        for obj in render_objects:
            # Draw object and its potential health bar (handled in GameObject.draw)
            obj.draw(self.screen, self.camera)
        
        # Draw weapon separately (also handles its own health bar if it had one)
        self.player.active_weapon.draw(self.screen, self.camera)
        
        # --- Draw Player HUD (Health Bar) --- 
        self._draw_player_hud()
        # -----------------------------------
        
        pygame.display.update()

    def _draw_player_hud(self):
        """Draws the player's health bar in the top-left corner."""
        BAR_WIDTH = 200
        BAR_HEIGHT = 20
        BAR_X = 10
        BAR_Y = 10
        
        if self.player.max_hp <= 0: return # Avoid division by zero if max_hp is invalid
        
        hp_ratio = max(0, self.player.hp / self.player.max_hp)
        
        bg_color = (128, 0, 0) # Dark Red
        fg_color = (0, 200, 0) # Green
        border_color = (255, 255, 255) # White border
        
        bg_rect = pygame.Rect(BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT)
        
        fg_rect_width = int(BAR_WIDTH * hp_ratio)
        fg_rect = pygame.Rect(BAR_X, BAR_Y, fg_rect_width, BAR_HEIGHT)
        
        # Draw background
        pygame.draw.rect(self.screen, bg_color, bg_rect)
        # Draw foreground
        pygame.draw.rect(self.screen, fg_color, fg_rect)
        # Draw border
        pygame.draw.rect(self.screen, border_color, bg_rect, 2) # Border thickness 2