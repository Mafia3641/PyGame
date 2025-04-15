import pygame
import sys
from utils import load_sprite
from models import Player
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from camera import Camera
from enemy import Monkey

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
        
        self.clock = pygame.time.Clock()

    def main_loop(self):
        self._spawn_enemy(enemy_type='monkey', position=(450, 350))
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

    def _process_game_logic(self, dt):
        self.player.update(self.camera, dt)
        for enemy in self.enemies:
            enemy.update(dt)
    
    def _spawn_enemy(self, enemy_type: str, position: tuple):
        enemy = Monkey(position, target=self.player)
        self.enemies.append(enemy)
        print("Enemy created")
    
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
        render_objects.sort(key=lambda obj: obj.rect.centery)
        
        for obj in render_objects:
            obj.draw(self.screen, self.camera)
        
        pygame.display.update()