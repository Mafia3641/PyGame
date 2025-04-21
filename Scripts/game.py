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
        Отрисовка 3x3 тайлов с корректным смещением относительно камеры.
        Мы вычисляем offset по оси x и y на основе позиции камеры и размеров тайла.
        """
        # Очищаем экран
        self.screen.fill((0, 0, 0))
        # Вычисляем смещение: остаток от деления координат камеры на размеры фонового тайла.
        offset_x = - (self.camera.camera.x % self.background_width)
        offset_y = - (self.camera.camera.y % self.background_height)
        # Отрисовываем 3x3 сетку (9 тайлов)
        for i in range(-1, 3):
            for j in range(-1, 3):
                pos_x = i * self.background_width + offset_x
                pos_y = j * self.background_height + offset_y
                self.screen.blit(self.background, (pos_x, pos_y))

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
            obj.draw(self.screen, self.camera)
        
        self.player.active_weapon.draw(self.screen, self.camera)
        
        pygame.display.update()