from pygame.image import load
import os
import pygame

def load_sprite(name, with_alpha=True):
	base_path = os.path.dirname(os.path.abspath(__file__))
	sprite_path = os.path.join(base_path, "..", "Sprites", f"{name}.png")
	sprite_path = os.path.normpath(sprite_path)  # нормализуем путь под ОС
	
	try:
		loaded_sprite = load(sprite_path)
		surface = loaded_sprite.convert_alpha() if with_alpha else loaded_sprite.convert()
		return surface
	except pygame.error:
		# print(f"Ошибка: не удалось найти спрайт по пути: {sprite_path}")
		raise SystemExit(f"Ошибка: не удалось найти спрайт по пути: {sprite_path}")