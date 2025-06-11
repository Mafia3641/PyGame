from pygame.math import Vector2

ACCELERATION = 0.25
WINDOW_WIDTH = 1920*0.7
WINDOW_HEIGHT = 1080*0.7
SPEED = 250
FPS = 240
BASE_DAMAGE = 60
UP = Vector2(0, -1)

# --- UI Constants ---
PLAY_BUTTON_POSITION = (WINDOW_WIDTH/2-50, WINDOW_HEIGHT/2)  # Approx center for 1728x972
SETTINGS_BUTTON_POSITION = (20, 20) # Left, aligned with play
EXIT_BUTTON_POSITION = (20, 100) # Top-right

# --- Leveling Constants ---
INITIAL_XP_TO_LEVEL_UP = 100
XP_LEVEL_MULTIPLIER = 1.5 # XP needed increases by 50% each level
SLIME_XP_REWARD = 20

# --- Wave Announcement Constants ---
WAVE_INTRO_FADE_DURATION = 1.0  # Seconds for fade in/out
WAVE_INTRO_HOLD_DURATION = 2.0  # Seconds to hold text
WAVE_INTRO_MAX_FONT_SIZE = 120 # Max font size during animation
WAVE_INTRO_MIN_FONT_SIZE = 20  # Starting/Ending font size
WAVE_INSCRIPTION_POSITION = (864, 243) # Center X, 1/4 down Y for 1728x972 screen

# --- Spawner Constants ---
INITIAL_SPAWN_COOLDOWN = 1.0  # Seconds between spawns
SPAWN_RADIUS_MIN = 250      # Min pixels from player to spawn
SPAWN_RADIUS_MAX = 400      # Max pixels from player to spawn

# --- Enemy Scaling Constants ---
SLIME_MAX_LEVEL = 5
SLIME_BASE_HP = 50
SLIME_BASE_DAMAGE = 5
SLIME_HP_INCREASE_PER_LEVEL = 0.20  # 20% increase
SLIME_DAMAGE_INCREASE_PER_LEVEL = 0.10 # 10% increase

# --- Game Over Animation Constants ---
GAME_OVER_ANIM_DURATION = 1.5 # Seconds for fade-in animation
GAME_OVER_MAX_FONT_SIZE = 150
GAME_OVER_MIN_FONT_SIZE = 50
GAME_OVER_START_ALPHA = 0   # Fully transparent
GAME_OVER_END_ALPHA = 255 # Fully opaque

# --- New Game Button Constants ---
NEW_GAME_BUTTON_DELAY = 5.0 # Seconds after death before button appears
ACTION_NEW_GAME = 'new_game' # Action string for controller

# --- Upgrade UI Constants ---
UPGRADE_CARD_SIZE = (250, 750)
UPGRADE_CARD_Y_POS = 150 # Vertical position on screen
UPGRADE_CARD_SPACING = 50 # Horizontal space between cards

# --- Player Base Stats ---
BASE_PLAYER_HP = 100
BASE_MAX_MANA = 50

# --- HUD Bar Constants ---
BASE_HP_BAR_WIDTH = 200
BASE_MANA_BAR_WIDTH = 180
MAX_HP_BAR_WIDTH = 400  # Max visual width for the HP bar
MAX_MANA_BAR_WIDTH = 360 # Max visual width for the Mana bar