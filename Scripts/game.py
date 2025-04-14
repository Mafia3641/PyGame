import pygame
import sys
from utils import load_sprite
from models import Player
from constants import WINDOW_WIDTH, WINDOW_HEIGHT
from camera import Camera

class Game:
    def __init__(self):
        self._init_pygame()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.background = load_sprite("grass", False)
        self.background_width = self.background.get_width()
        self.background_height = self.background.get_height()

        self.player = Player(position=(400, 300))
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.clock = pygame.time.Clock()

    def main_loop(self):
        while True:
            self._handle_events()
            self._process_game_logic()
            self._draw()
            self.clock.tick(240)

    def _init_pygame(self):
        pygame.init()
        pygame.display.set_caption("Terra")

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def _process_game_logic(self):
        self.player.update(self.camera)

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
        self.player.draw(self.screen, self.camera)
        pygame.display.update()