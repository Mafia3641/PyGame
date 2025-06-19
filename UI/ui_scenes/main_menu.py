import pygame
import sys
from UI.button import Button
import os
from Scripts.constants import PLAY_BUTTON_POSITION, SETTINGS_BUTTON_POSITION, EXIT_BUTTON_POSITION, WINDOW_WIDTH, WINDOW_HEIGHT

ACTION_START_GAME = 'start_game'
ACTION_OPEN_SETTINGS = 'open_settings'
ACTION_EXIT = 'exit'

try:
    import cv2
    import numpy
    OPENCV_AVAILABLE = True
except ImportError:
    print("Warning: OpenCV library (cv2) not found. Video background disabled. Install with 'pip install opencv-python'")
    OPENCV_AVAILABLE = False


class MainMenu:
    """Класс для управления главным меню игры"""
    def __init__(self):
        self.background_color = (255, 255, 255)
        self.buttons = []
        self._setup_buttons()

        self.video_capture = None
        self.current_frame_surface = None

        if OPENCV_AVAILABLE:
            try:
                video_path = "Videos/background_1.mp4"
                self.video_capture = cv2.VideoCapture(video_path)
                if not self.video_capture.isOpened():
                    print(f"Error: Could not open video file: {video_path}")
                    self.video_capture = None
                else:
                    pass

            except Exception as e:
                print(f"Error initializing video capture: {e}")
                self.video_capture = None

    def set_audio_manager(self, audio_manager):
        """Установка менеджера звука"""
        self.audio_manager = audio_manager

    def _setup_buttons(self):
        """Настройка кнопок меню"""
        def start_game_callback():
            return ACTION_START_GAME
        
        def open_settings_callback():
            return ACTION_OPEN_SETTINGS

        def exit_callback():
            return ACTION_EXIT
        
        # Масштаб кнопок
        button_scale = 2.0

        # Загрузка спрайтов для кнопок
        start_unpressed = "UI/ui_sprites/play_button_unpressed.png"
        start_pressed = "UI/ui_sprites/play_button_pressed.png"
        settings_unpressed = "UI/ui_sprites/settings_button_unpressed.png"
        settings_pressed = "UI/ui_sprites/settings_button_pressed.png"
        exit_unpressed = "UI/ui_sprites/close_button_unpressed.png"
        exit_pressed = "UI/ui_sprites/close_button_pressed.png"

        # Создание кнопок
        try:
            self.start_button = Button(
                PLAY_BUTTON_POSITION[0], PLAY_BUTTON_POSITION[1],
                start_unpressed, start_pressed, start_game_callback,
                scale=button_scale
            )
            self.settings_button = Button(
                SETTINGS_BUTTON_POSITION[0], SETTINGS_BUTTON_POSITION[1],
                settings_unpressed, settings_pressed, open_settings_callback,
                scale=button_scale
            )
            self.exit_button = Button(
                EXIT_BUTTON_POSITION[0], EXIT_BUTTON_POSITION[1],
                exit_unpressed, exit_pressed, exit_callback,
                scale=button_scale
            )
        except pygame.error as e:
            sys.exit(1)
        except FileNotFoundError as e:
             sys.exit(1)

        self.buttons.extend([self.start_button, self.settings_button, self.exit_button])

    def handle_events(self, events):
        """Обработка событий"""
        action_taken = None
        for event in events:
            # Обработка событий для каждой кнопки
            for button in self.buttons:
                action = button.handle_event(event)
                if action:
                    action_taken = action
                    break
            if action_taken:
                break
        return action_taken

    def update(self, dt):
        """Обновление состояния меню"""
        if self.video_capture:
            # Чтение кадра из видео
            success, frame = self.video_capture.read()

            # Если кадр не прочитан, то сбрасываем кадр на начало и пытаемся прочитать его снова
            if not success:
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                success, frame = self.video_capture.read()

            try:
                # Если кадр прочитан, то масштабируем его и преобразуем в RGB
                if success:
                    frame_h, frame_w = frame.shape[:2]
                    window_w, window_h = int(WINDOW_WIDTH), int(WINDOW_HEIGHT)
                    
                    scale_w = window_w / frame_w
                    scale_h = window_h / frame_h
                    scale_factor = min(scale_w, scale_h)

                    new_w = int(frame_w * scale_factor)
                    new_h = int(frame_h * scale_factor)
                    scaled_frame = cv2.resize(frame, (new_w, new_h))


                    frame_rgb = cv2.cvtColor(scaled_frame, cv2.COLOR_BGR2RGB)
                    rotated_frame = numpy.rot90(frame_rgb)
                    flipped_frame = numpy.flipud(rotated_frame)
                    self.current_frame_surface = pygame.surfarray.make_surface(flipped_frame)
                else:
                    self.current_frame_surface = None
                    self.video_capture.release()
                    self.video_capture = None

            except Exception as e:
                print(f"Error processing video frame: {e}")
                self.current_frame_surface = None
                if self.video_capture:
                    self.video_capture.release()

    def draw(self, surface):
        """Отрисовка меню"""
        if self.current_frame_surface:
            frame_rect = self.current_frame_surface.get_rect()
            screen_rect = surface.get_rect()
            top_left_x = (screen_rect.width - frame_rect.width) // 2
            top_left_y = (screen_rect.height - frame_rect.height) // 2
            surface.blit(self.current_frame_surface, (top_left_x, top_left_y))
        else:
            surface.fill((30, 30, 50))

        # Отрисовка кнопок
        for button in self.buttons:
            button.draw(surface)