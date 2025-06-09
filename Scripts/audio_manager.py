import pygame

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.current_music = None
        self.master_volume = 0.2  # Начальная громкость 20%
        self.game_volume_multiplier = 0.5  # Игровая музыка на 50% тише
        
        # Предзагрузка музыкальных файлов
        self.menu_music = "Audio/main_menu_music.mp3"
        self.game_music = "Audio/in_game_music.mp3"
        
    def play_menu_music(self):
        if self.current_music != self.menu_music:
            pygame.mixer.music.load(self.menu_music)
            pygame.mixer.music.play(-1)  # -1 означает бесконечное повторение
            pygame.mixer.music.set_volume(self.master_volume)
            self.current_music = self.menu_music
            
    def play_game_music(self):
        if self.current_music != self.game_music:
            pygame.mixer.music.load(self.game_music)
            pygame.mixer.music.play(-1)  # -1 означает бесконечное повторение
            pygame.mixer.music.set_volume(self.master_volume * self.game_volume_multiplier)
            self.current_music = self.game_music
            
    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_music = None
        
    def set_volume(self, volume):
        self.master_volume = max(0.0, min(1.0, volume))
        # Применяем множитель громкости для игровой музыки
        if self.current_music == self.game_music:
            pygame.mixer.music.set_volume(self.master_volume * self.game_volume_multiplier)
        else:
            pygame.mixer.music.set_volume(self.master_volume)
        
    def get_volume(self):
        return self.master_volume 