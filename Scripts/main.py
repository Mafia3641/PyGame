import pygame
import sys
import os

dir_scripts = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(dir_scripts, '..'))
if project_root not in sys.path:
	sys.path.append(project_root)

from Scripts.controller import GameController

if __name__ == '__main__':
	controller = GameController()
	controller.run()

