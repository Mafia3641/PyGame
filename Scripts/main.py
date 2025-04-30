import pygame
import sys
import os

# --- Path Setup --- #
# Get the absolute path of the directory containing this script (Scripts/)
dir_scripts = os.path.dirname(__file__)
# Get the absolute path of the project root (one level up from Scripts/)
project_root = os.path.abspath(os.path.join(dir_scripts, '..'))
# Add the project root to the Python path
if project_root not in sys.path:
	sys.path.append(project_root)

# --- Imports --- #
# We only need to import the controller here
from Scripts.controller import GameController 

# --- Main Execution --- #
if __name__ == '__main__':
	controller = GameController()
	controller.run()

