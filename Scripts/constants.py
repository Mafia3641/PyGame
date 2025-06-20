from pygame.math import Vector2

ACCELERATION = 0.25
WINDOW_WIDTH = 1920*0.7
WINDOW_HEIGHT = 1080*0.7
SPEED = 250
FPS = 240
BASE_DAMAGE = 60
UP = Vector2(0, -1)

PLAY_BUTTON_POSITION = (WINDOW_WIDTH/2-50, WINDOW_HEIGHT/2)
SETTINGS_BUTTON_POSITION = (20, 20)
EXIT_BUTTON_POSITION = (20, 100)

INITIAL_XP_TO_LEVEL_UP = 100
XP_LEVEL_MULTIPLIER = 1.5
SLIME_XP_REWARD = 20

WAVE_INTRO_FADE_DURATION = 1.0
WAVE_INTRO_HOLD_DURATION = 2.0
WAVE_INTRO_MAX_FONT_SIZE = 120
WAVE_INTRO_MIN_FONT_SIZE = 20
WAVE_INSCRIPTION_POSITION = (864, 243)

INITIAL_SPAWN_COOLDOWN = 1.0
SPAWN_RADIUS_MIN = 250
SPAWN_RADIUS_MAX = 400

SLIME_MAX_LEVEL = 5
SLIME_BASE_HP = 50
SLIME_BASE_DAMAGE = 5
SLIME_HP_INCREASE_PER_LEVEL = 0.20
SLIME_DAMAGE_INCREASE_PER_LEVEL = 0.10

GAME_OVER_ANIM_DURATION = 1.5
GAME_OVER_MAX_FONT_SIZE = 150
GAME_OVER_MIN_FONT_SIZE = 50
GAME_OVER_START_ALPHA = 0
GAME_OVER_END_ALPHA = 255

NEW_GAME_BUTTON_DELAY = 5.0
ACTION_NEW_GAME = 'new_game'

UPGRADE_CARD_SIZE = (250, 750)
UPGRADE_CARD_Y_POS = 150
UPGRADE_CARD_SPACING = 50

BASE_PLAYER_HP = 100
BASE_MAX_MANA = 50

BASE_HP_BAR_WIDTH = 200
BASE_MANA_BAR_WIDTH = 180
MAX_HP_BAR_WIDTH = 400
MAX_MANA_BAR_WIDTH = 360