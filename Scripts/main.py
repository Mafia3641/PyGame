import sys
import os

# Добавляем корневую директорию проекта в sys.path
dir_scripts = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(dir_scripts, '..'))
if project_root not in sys.path:
	sys.path.append(project_root)

# Импортируем класс GameController из файла controller.py
from Scripts.controller import GameController

if __name__ == '__main__':
	"""Запуск игры"""
	controller = GameController()
	controller.run()

