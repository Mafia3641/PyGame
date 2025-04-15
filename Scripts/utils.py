from pygame.image import load
import os
def load_sprite(name, with_alpha=True):
	base_path = os.path.dirname(os.path.abspath(__file__))
	sprite_path = os.path.join(base_path, "..", "Sprites", f"{name}.png")
	sprite_path = os.path.normpath(sprite_path)  # нормализуем путь под ОС
	
	try:
		loaded_sprite = load(sprite_path)
		if with_alpha:
			return loaded_sprite.convert_alpha()
		else:
			return loaded_sprite.convert()
	except FileNotFoundError:
		print(f"Ошибка: не удалось найти спрайт по пути: {sprite_path}")
		raise