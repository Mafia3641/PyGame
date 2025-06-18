import pygame
import random
from pygame.math import Vector2
from utils import load_sprite
from player import Player
from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    WAVE_INTRO_FADE_DURATION, WAVE_INTRO_HOLD_DURATION, 
    WAVE_INTRO_MAX_FONT_SIZE, WAVE_INTRO_MIN_FONT_SIZE,
    WAVE_INSCRIPTION_POSITION, SLIME_MAX_LEVEL,
    GAME_OVER_ANIM_DURATION, GAME_OVER_MAX_FONT_SIZE,
    GAME_OVER_END_ALPHA,
    NEW_GAME_BUTTON_DELAY, ACTION_NEW_GAME,
    UPGRADE_CARD_SIZE, UPGRADE_CARD_Y_POS, UPGRADE_CARD_SPACING, 
    BASE_PLAYER_HP, BASE_MAX_MANA, 
    BASE_HP_BAR_WIDTH, BASE_MANA_BAR_WIDTH, 
    MAX_HP_BAR_WIDTH, MAX_MANA_BAR_WIDTH
)
from camera import Camera
from UI.button import Button
from Scripts.spawner import Spawner
from UI.upgrade_box import UpgradeBox
from Scripts.game_states import STATE_GO_TO_MENU
from Scripts.upgrades_list import get_upgrade_data, get_all_upgrade_names
from Scripts.upgrades_list import get_upgrade_data, get_all_upgrade_names

class GameState:
    def __init__(self, player, enemies, projectiles, camera):
        self.player = player
        self.enemies = enemies
        self.projectiles = projectiles
        self.camera = camera

    def get_mouse_world_pos(self) -> Vector2:
        mouse_screen_pos = pygame.mouse.get_pos()
        return self.camera.screen_to_world(mouse_screen_pos)

class Game:
    def __init__(self, starting_weapon_type: str):
        
        self.background = load_sprite("grass", False)
        self.background_width = self.background.get_width()
        self.background_height = self.background.get_height()
        self.scaled_background = None
        self.last_camera_zoom = None
    
        self.player = Player(position=(400, 300), starting_weapon_type=starting_weapon_type)
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.enemies = []
        self.projectiles = []

        self.game_state = GameState(self.player, self.enemies, self.projectiles, self.camera)
        
        self.spawner = Spawner(self.player, self.game_state)

        self.audio_manager = None
        
        self.slider_rect = pygame.Rect(0, 0, 300, 10)
        self.slider_handle_radius = 15
        self.is_dragging = False
        self.volume_font = pygame.font.Font(None, 48)
        self.volume_text = self.volume_font.render("Громкость", True, (255, 255, 255))
        
        self.is_paused = False
        self._setup_pause_button()
        self._setup_resume_button()
        self._setup_pause_overlay_elements()
        
        self.current_wave = 0
        self.is_showing_wave_intro = False
        self.wave_intro_timer = 0.0
        self.wave_intro_stage = 'fade_in'
        self.wave_font = None

        self.is_game_over = False
        self.game_over_font = None
        self.game_over_timer = 0.0
        self.new_game_button_appear_timer = 0.0
        self.new_game_button = None

        self.is_game_won = False

        self.is_showing_upgrades = True
        self.available_upgrade_boxes = []
        self.all_upgrade_names = get_all_upgrade_names() 
        
        self._show_upgrade_selection()

    def _setup_pause_button(self):
        try:
            pause_sprite_path = "UI/ui_sprites/pause_button.png"
            temp_pause_img = pygame.image.load(pause_sprite_path)
            btn_width, btn_height = temp_pause_img.get_size()
            
            pause_x = WINDOW_WIDTH - btn_width - 10
            pause_y = 10
            
            self.pause_button = Button(
                pause_x, 
                pause_y, 
                pause_sprite_path, 
                pause_sprite_path,
                callback=self._toggle_pause
            )
        except pygame.error as e:
            self.pause_button = None
        except FileNotFoundError:
            self.pause_button = None
            
    def _setup_resume_button(self):
        self.resume_button = None
        try:
            resume_unpressed_path = "UI/ui_sprites/resume_button_unpressed.png"
            resume_pressed_path = "UI/ui_sprites/resume_button_pressed.png"
            
            button_text = "RESUME"
            text_font_size = 28
            text_color = (255, 255, 255)
            
            self.resume_button = Button(
                0, 0,
                resume_unpressed_path, 
                resume_pressed_path, 
                callback=self._toggle_pause,
                text=button_text,
                font_size=text_font_size,
                font_color=text_color,
                scale=5.0
            )
        except pygame.error as e:
            pass
        except FileNotFoundError:
            pass
            
    def _toggle_pause(self):
        self.is_paused = not self.is_paused

    def _setup_pause_overlay_elements(self):
        try:
            self.pause_font = pygame.font.Font(None, 74)
        except pygame.error:
            self.pause_font = pygame.font.SysFont('arial', 60)
            
        self.paused_text_surface = self.pause_font.render(
            "PAUSED", True, (255, 255, 255)
        )
        screen_rect = pygame.display.get_surface().get_rect() 
        self.paused_text_rect = self.paused_text_surface.get_rect(
            center=screen_rect.center
        )
        
        overlay_color = (0, 0, 0, 150)
        self.pause_overlay_surface = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        self.pause_overlay_surface.fill(overlay_color)
        
        if self.resume_button:
            button_rect = self.resume_button.rect
            button_x = self.paused_text_rect.centerx - button_rect.width // 2
            button_y = self.paused_text_rect.bottom + 20
            self.resume_button.rect.topleft = (button_x, button_y)

        try:
            exit_unpressed_path = "UI/ui_sprites/close_button_unpressed.png"
            exit_pressed_path = "UI/ui_sprites/close_button_pressed.png"

            self.exit_button = Button(
                0, 0,
                exit_unpressed_path,
                exit_pressed_path,
                callback=self._request_go_to_menu,
                scale=2.0
            )

            screen_rect = pygame.display.get_surface().get_rect()
            button_rect = self.exit_button.rect
            padding = 20
            button_x = screen_rect.width - button_rect.width - padding
            button_y = screen_rect.height - button_rect.height - padding
            self.exit_button.rect.topleft = (button_x, button_y)

        except pygame.error as e:
            print(f"Error loading exit button sprite: {e}")
        except FileNotFoundError:
            print(f"Error: Exit button sprite not found")

        self._center_volume_elements()

    def handle_events(self, events):
        current_button_rect = None
        if self.pause_button and self.pause_button.unpressed_sprite:
            original_sprite = self.pause_button.unpressed_sprite
            original_width, original_height = original_sprite.get_size()
            zoom = self.camera.zoom
            scale_factor = zoom * 2
            scaled_width = max(1, int(original_width * scale_factor))
            scaled_height = max(1, int(original_height * scale_factor))
            padding = 10
            scaled_x = WINDOW_WIDTH - scaled_width - padding
            scaled_y = padding
            self.pause_button.rect.topleft = (scaled_x, scaled_y)
            self.pause_button.rect.size = (scaled_width, scaled_height)
            current_button_rect = self.pause_button.rect
        if self.is_game_over and self.new_game_button:
            for event in events:
                action = self.new_game_button.handle_event(event)
                if action:
                    return action
        if self.is_game_won and self.new_game_button:
            for event in events:
                action = self.new_game_button.handle_event(event)
                if action:
                    return action
                
        if self.is_showing_upgrades:
            for event in events:
                for box in self.available_upgrade_boxes:
                    selected_upgrade_data = box.handle_event(event)
                    if selected_upgrade_data:
                        self._apply_upgrade(selected_upgrade_data)
                        self.is_showing_upgrades = False
                        self.available_upgrade_boxes = []
                        if self.spawner.is_active():
                            self._start_next_wave_intro()
                        return
            
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._toggle_pause()
                    continue

            event_consumed_by_button = False
            if self.pause_button and current_button_rect:
                mouse_over_button = False
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    mouse_over_button = current_button_rect.collidepoint(event.pos)
                
                if mouse_over_button or (event.type == pygame.MOUSEBUTTONUP and self.pause_button.is_pressed):
                    action = self.pause_button.handle_event(event)
                    if action is not None:
                         event_consumed_by_button = True 
                    elif event.type == pygame.MOUSEBUTTONDOWN and mouse_over_button:
                        event_consumed_by_button = True
                        
            if event_consumed_by_button:
                continue

            event_consumed_by_resume_button = False
            if self.is_paused and self.resume_button:
                mouse_over_resume_button = False
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                     mouse_over_resume_button = self.resume_button.rect.collidepoint(event.pos)
                
                if mouse_over_resume_button or (event.type == pygame.MOUSEBUTTONUP and self.resume_button.is_pressed):
                    action = self.resume_button.handle_event(event)
                    if action is not None:
                        event_consumed_by_resume_button = True
                    elif event.type == pygame.MOUSEBUTTONDOWN and mouse_over_resume_button:
                        event_consumed_by_resume_button = True
                        
            if event_consumed_by_resume_button:
                continue

            event_consumed_by_exit_button = False
            if self.is_paused and self.exit_button:
                mouse_over_exit_button = False
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                     mouse_over_exit_button = self.exit_button.rect.collidepoint(event.pos)
                
                if mouse_over_exit_button or (event.type == pygame.MOUSEBUTTONUP and self.exit_button.is_pressed):
                    action = self.exit_button.handle_event(event)
                    if action is not None:
                        return action
                    elif event.type == pygame.MOUSEBUTTONDOWN and mouse_over_exit_button:
                        event_consumed_by_exit_button = True
                        
            if event_consumed_by_exit_button:
                continue

            if not self.is_paused:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.player.handle_input([event], self.camera, self.game_state)

        if self.is_paused and self.audio_manager:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        handle_pos = (
                            self.slider_rect.left + self.audio_manager.get_volume() * self.slider_rect.width,
                            self.slider_rect.centery
                        )
                        handle_rect = pygame.Rect(
                            handle_pos[0] - self.slider_handle_radius,
                            handle_pos[1] - self.slider_handle_radius,
                            self.slider_handle_radius * 2,
                            self.slider_handle_radius * 2
                        )
                        if handle_rect.collidepoint(event.pos):
                            self.is_dragging = True
                            
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.is_dragging = False
                        
                elif event.type == pygame.MOUSEMOTION:
                    if self.is_dragging:
                        rel_x = event.pos[0] - self.slider_rect.left
                        new_volume = max(0.0, min(1.0, rel_x / self.slider_rect.width))
                        self.audio_manager.set_volume(new_volume)
        
    def update(self, dt):
        if self.player.is_dying and not self.is_game_over:
            self.is_game_over = True
            self.game_over_timer = 0.0
        if self.is_game_over:
            self.player.update(dt, self.camera, self.game_state)
            
            if self.game_over_timer < GAME_OVER_ANIM_DURATION:
                self.game_over_timer += dt
            else:
                if self.new_game_button_appear_timer < NEW_GAME_BUTTON_DELAY:
                    self.new_game_button_appear_timer += dt
                
            if self.new_game_button_appear_timer >= NEW_GAME_BUTTON_DELAY and self.new_game_button is None:
                self._setup_new_game_button()
                
            return

        if self.is_game_won:
            if self.new_game_button is None:
                self._setup_new_game_button()
            return

        if self.is_showing_upgrades:
            return

        if self.is_showing_wave_intro:
            self._update_wave_intro(dt)
        
        if self.is_paused:
            return 
        
        self.spawner.update(dt)
        
        self.player.update(dt, self.camera, self.game_state)
        
        self.camera.update(self.player)

        if self.player.is_dying:
            return
        
        for enemy in self.enemies[:]:
            enemy.update(dt)
            if enemy.should_be_removed:
                self.enemies.remove(enemy)

        if self.player.current_level > self.current_wave and self.current_wave <= SLIME_MAX_LEVEL:
             self._end_wave()

        for p in self.projectiles:
            p.update(dt, self.game_state)

        self.projectiles = [p for p in self.projectiles if not getattr(p, 'is_dead', False)]
        self.game_state.projectiles = self.projectiles
        
    def _update_wave_intro(self, dt):
        if not self.is_showing_wave_intro: return
        self.wave_intro_timer += dt
        total_fade_hold_duration = WAVE_INTRO_FADE_DURATION + WAVE_INTRO_HOLD_DURATION
        total_duration = WAVE_INTRO_FADE_DURATION * 2 + WAVE_INTRO_HOLD_DURATION

        if self.wave_intro_stage == 'fade_in':
            if self.wave_intro_timer >= WAVE_INTRO_FADE_DURATION:
                self.wave_intro_stage = 'hold'
        elif self.wave_intro_stage == 'hold':
            if self.wave_intro_timer >= total_fade_hold_duration:
                self.wave_intro_stage = 'fade_out'
        elif self.wave_intro_stage == 'fade_out':
            if self.wave_intro_timer >= total_duration:
                self.is_showing_wave_intro = False

    def _end_wave(self):
        enemies_to_remove = [e for e in self.game_state.enemies if not e.dying]
        for enemy in enemies_to_remove:
            self.game_state.enemies.remove(enemy)
            
        self.spawner.next_wave()
        
        if self.current_wave >= 5:
            self.is_game_won = True
            return

        if self.spawner.is_active():
            self.player.restore_hp()
            
            self._show_upgrade_selection()
        else:
            pass
             
    def _show_upgrade_selection(self):
        self.is_showing_upgrades = True
        self.available_upgrade_boxes = []
        
        selected_names = self._select_upgrades()
        if not selected_names:
            self.is_showing_upgrades = False
            self._start_next_wave_intro()
            return

        num_cards = len(selected_names)
        total_width = num_cards * UPGRADE_CARD_SIZE[0] + (num_cards - 1) * UPGRADE_CARD_SPACING
        start_x = (WINDOW_WIDTH - total_width) // 2

        for i, name in enumerate(selected_names):
            upgrade_data = get_upgrade_data(name)
            if upgrade_data:
                card_x = start_x + i * (UPGRADE_CARD_SIZE[0] + UPGRADE_CARD_SPACING)
                card_y = UPGRADE_CARD_Y_POS
                box = UpgradeBox(upgrade_data, (card_x, card_y), UPGRADE_CARD_SIZE)
                self.available_upgrade_boxes.append(box)
            else:
                pass
                
    def _select_upgrades(self, count=3):
        available_count = len(self.all_upgrade_names)
        select_count = min(count, available_count)
        
        if select_count <= 0:
            return []
            
        try:
            return random.sample(self.all_upgrade_names, select_count)
        except ValueError:
            return random.sample(self.all_upgrade_names, available_count) 
            
    def _apply_upgrade(self, upgrade_data):
        stats_to_apply = upgrade_data.get('stats', {})

        for stat_name, value in stats_to_apply.items():
            if stat_name == 'max_hp_mult':
                self.player.max_hp *= value
                self.player.hp = self.player.max_hp
            elif stat_name == 'max_mana_mult':
                self.player.max_mana *= value
                self.player.current_mana = self.player.max_mana
            elif stat_name == 'speed_mult':
                self.player.speed *= value
            elif stat_name == 'xp_multiplier':
                self.player.xp_multiplier *= value

            elif hasattr(self.player.active_weapon, 'stats'):
                weapon_stats = self.player.active_weapon.stats
                if stat_name == 'damage_mult':
                    if 'damage' in weapon_stats:
                        weapon_stats['damage'] *= value
                elif stat_name == 'attack_cooldown_mult':
                    if 'cooldown' in weapon_stats:
                        weapon_stats['cooldown'] *= value
                else:
                    pass
            else:
                pass
                
    def _start_next_wave_intro(self):
        self.current_wave += 1 
        self.is_showing_wave_intro = True
        self.wave_intro_timer = 0.0
        self.wave_intro_stage = 'fade_in'
    
    def _request_go_to_menu(self):
        return STATE_GO_TO_MENU
    
    def draw(self, surface):
        self._draw_background(surface)
        
        render_objects = [] 
        if not self.player.is_dying:
            render_objects.extend(self.enemies)
            render_objects.extend(self.projectiles)
            render_objects.sort(key=lambda obj: obj.position.y)
        for obj in render_objects:
            obj.draw(surface, self.camera)
            
        self.player.draw(surface, self.camera)
        
        self._draw_player_hud(surface)
        
        if self.pause_button and self.pause_button.unpressed_sprite:
            original_sprite = self.pause_button.unpressed_sprite
            original_width, original_height = original_sprite.get_size()
            zoom = self.camera.zoom
            
            scale_factor = zoom * 2
            scaled_width = max(1, int(original_width * scale_factor))
            scaled_height = max(1, int(original_height * scale_factor))
            
            scaled_sprite = pygame.transform.scale(original_sprite, (scaled_width, scaled_height))
            
            padding = 10
            scaled_x = WINDOW_WIDTH - scaled_width - padding
            scaled_y = padding
            
            surface.blit(scaled_sprite, (scaled_x, scaled_y))
            
        if self.is_paused:
            self._draw_pause_overlay(surface)
        
        if self.is_showing_wave_intro:
            self._draw_wave_intro(surface)
        
        if self.is_game_over:
            self._draw_game_over(surface)
            if self.new_game_button:
                self.new_game_button.draw(surface)
        if self.is_game_won:
            self._draw_win_screen(surface)
            if self.new_game_button:
                self.new_game_button.draw(surface)

        if self.is_showing_upgrades:
            for box in self.available_upgrade_boxes:
                box.draw(surface)

    def _draw_background(self, surface):
        surface.fill((0, 0, 0))
        
        zoom = self.camera.zoom
        if zoom != self.last_camera_zoom or self.scaled_background is None:
            scaled_bg_width = int(self.background_width * zoom)
            scaled_bg_height = int(self.background_height * zoom)
            if scaled_bg_width > 0 and scaled_bg_height > 0:
                self.scaled_background = pygame.transform.scale(self.background, (scaled_bg_width, scaled_bg_height))
                self.last_camera_zoom = zoom
            else:
                self.scaled_background = None 
        if self.scaled_background is None:
            return

        inv_zoom = 1.0 / zoom
        
        world_view_width = self.camera.width * inv_zoom
        world_view_height = self.camera.height * inv_zoom
        world_view_left = self.camera.camera.x
        world_view_top = self.camera.camera.y
        world_view_rect = pygame.Rect(world_view_left, world_view_top, world_view_width, world_view_height)

        scaled_bg_width = self.scaled_background.get_width()
        scaled_bg_height = self.scaled_background.get_height()

        start_col = int(world_view_left // self.background_width)
        end_col = int((world_view_left + world_view_width) // self.background_width) + 1
        start_row = int(world_view_top // self.background_height)
        end_row = int((world_view_top + world_view_height) // self.background_height) + 1

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile_world_x = col * self.background_width
                tile_world_y = row * self.background_height
                
                screen_x = (tile_world_x - world_view_left) * zoom
                screen_y = (tile_world_y - world_view_top) * zoom
                
                surface.blit(self.scaled_background, (int(screen_x), int(screen_y)))

    def _draw_player_hud(self, surface):
        screen_width = surface.get_width()
        
        HP_BAR_HEIGHT = 20
        HP_BAR_X = 10
        HP_BAR_Y = 10
        
        if self.player.max_hp > 0:
            hp_ratio_to_base = self.player.max_hp / BASE_PLAYER_HP
            target_hp_width = BASE_HP_BAR_WIDTH * hp_ratio_to_base
            current_hp_bar_width = min(target_hp_width, MAX_HP_BAR_WIDTH)

            hp_ratio = max(0, self.player.hp / self.player.max_hp)
            
            hp_bg_color = (128, 0, 0)
            hp_fg_color = (0, 200, 0)
            hp_border_color = (255, 255, 255)
            
            hp_bg_rect = pygame.Rect(HP_BAR_X, HP_BAR_Y, int(current_hp_bar_width), HP_BAR_HEIGHT)
            hp_fg_rect_width = int(current_hp_bar_width * hp_ratio)
            hp_fg_rect = pygame.Rect(HP_BAR_X, HP_BAR_Y, hp_fg_rect_width, HP_BAR_HEIGHT)
            
            pygame.draw.rect(surface, hp_bg_color, hp_bg_rect)
            pygame.draw.rect(surface, hp_fg_color, hp_fg_rect)
            pygame.draw.rect(surface, hp_border_color, hp_bg_rect, 2)
        if self.player.max_mana > 0:
            MANA_BAR_HEIGHT = 15
            MANA_BAR_X = HP_BAR_X
            MANA_BAR_Y = HP_BAR_Y + HP_BAR_HEIGHT + 5
            
            mana_ratio_to_base = self.player.max_mana / BASE_MAX_MANA
            target_mana_width = BASE_MANA_BAR_WIDTH * mana_ratio_to_base
            current_mana_bar_width = min(target_mana_width, MAX_MANA_BAR_WIDTH)

            mana_ratio = max(0, self.player.current_mana / self.player.max_mana)
            
            mana_bg_color = (0, 0, 100)
            mana_fg_color = (0, 100, 255)
            mana_border_color = (200, 200, 255)
            
            mana_bg_rect = pygame.Rect(MANA_BAR_X, MANA_BAR_Y, int(current_mana_bar_width), MANA_BAR_HEIGHT)
            mana_fg_rect_width = int(current_mana_bar_width * mana_ratio)
            mana_fg_rect = pygame.Rect(MANA_BAR_X, MANA_BAR_Y, mana_fg_rect_width, MANA_BAR_HEIGHT)
            
            pygame.draw.rect(surface, mana_bg_color, mana_bg_rect)
            pygame.draw.rect(surface, mana_fg_color, mana_fg_rect)
            pygame.draw.rect(surface, mana_border_color, mana_bg_rect, 2)
        XP_BAR_WIDTH = 300
        XP_BAR_HEIGHT = 15
        XP_BAR_X = (screen_width - XP_BAR_WIDTH) // 2
        XP_BAR_Y = 10
        
        if self.player.xp_for_next_level > 0:
            xp_ratio = max(0, self.player.current_xp / self.player.xp_for_next_level)

            xp_bg_color = (50, 50, 50)
            xp_fg_color = (0, 180, 255)
            xp_border_color = (200, 200, 200)
            
            xp_bg_rect = pygame.Rect(XP_BAR_X, XP_BAR_Y, XP_BAR_WIDTH, XP_BAR_HEIGHT)
            xp_fg_rect_width = int(XP_BAR_WIDTH * xp_ratio)
            xp_fg_rect = pygame.Rect(XP_BAR_X, XP_BAR_Y, xp_fg_rect_width, XP_BAR_HEIGHT)
            
            pygame.draw.rect(surface, xp_bg_color, xp_bg_rect)
            pygame.draw.rect(surface, xp_fg_color, xp_fg_rect)
            pygame.draw.rect(surface, xp_border_color, xp_bg_rect, 2)

            try:
                level_font = pygame.font.Font(None, 24)
                level_text = f"Level: {self.player.current_level}"
                level_surf = level_font.render(level_text, True, (255, 255, 255))
                level_rect = level_surf.get_rect(midtop=(xp_bg_rect.centerx, xp_bg_rect.bottom + 5))
                surface.blit(level_surf, level_rect)
            except pygame.error:
                pass

    def _draw_pause_overlay(self, surface):
        surface.blit(self.pause_overlay_surface, (0, 0))
        surface.blit(self.paused_text_surface, self.paused_text_rect)
        
        if self.audio_manager:
            surface.blit(self.volume_text, self.volume_text_rect)
            
            pygame.draw.rect(surface, (100, 100, 100), self.slider_rect)
            
            filled_rect = pygame.Rect(
                self.slider_rect.left,
                self.slider_rect.top,
                self.slider_rect.width * self.audio_manager.get_volume(),
                self.slider_rect.height
            )
            pygame.draw.rect(surface, (200, 200, 200), filled_rect)
            
            handle_pos = (
                self.slider_rect.left + self.audio_manager.get_volume() * self.slider_rect.width,
                self.slider_rect.centery
            )
            pygame.draw.circle(surface, (255, 255, 255), handle_pos, self.slider_handle_radius)
        
        if self.resume_button:
            self.resume_button.draw(surface)
        if self.exit_button:
            self.exit_button.draw(surface)

    def _draw_wave_intro(self, surface):
        current_size = WAVE_INTRO_MIN_FONT_SIZE
        current_alpha = 0
        progress = 0.0
        total_fade_hold_duration = WAVE_INTRO_FADE_DURATION + WAVE_INTRO_HOLD_DURATION
        total_duration = WAVE_INTRO_FADE_DURATION * 2 + WAVE_INTRO_HOLD_DURATION

        if self.wave_intro_stage == 'fade_in':
            progress = min(1.0, self.wave_intro_timer / WAVE_INTRO_FADE_DURATION)
            current_size = int(WAVE_INTRO_MIN_FONT_SIZE + (WAVE_INTRO_MAX_FONT_SIZE - WAVE_INTRO_MIN_FONT_SIZE) * progress)
            current_alpha = int(255 * progress)
        elif self.wave_intro_stage == 'hold':
            current_size = WAVE_INTRO_MAX_FONT_SIZE
            current_alpha = 255
        elif self.wave_intro_stage == 'fade_out':
            fade_out_timer = self.wave_intro_timer - total_fade_hold_duration
            progress = max(0.0, 1.0 - (fade_out_timer / WAVE_INTRO_FADE_DURATION))
            current_size = int(WAVE_INTRO_MIN_FONT_SIZE + (WAVE_INTRO_MAX_FONT_SIZE - WAVE_INTRO_MIN_FONT_SIZE) * progress)
            current_alpha = int(255 * progress)

        current_alpha = max(0, min(255, current_alpha))
        current_size = max(1, current_size)

        try:
            if self.wave_font is None or self.wave_font.get_height() != current_size:
                 self.wave_font = pygame.font.Font(None, current_size) 
            
            wave_text = f"WAVE {self.current_wave}"
            text_surface = self.wave_font.render(wave_text, True, (255, 255, 255))
            text_surface.set_alpha(current_alpha)
            
            text_rect = text_surface.get_rect(center=WAVE_INSCRIPTION_POSITION)
            
            surface.blit(text_surface, text_rect)
        except pygame.error:
            pass
        except AttributeError:
             pass

    def _draw_game_over(self, surface):
        progress = min(1.0, self.game_over_timer / GAME_OVER_ANIM_DURATION)
        
        start_size = GAME_OVER_MAX_FONT_SIZE * 0.8
        start_alpha = GAME_OVER_END_ALPHA * 0.8
        
        current_size = int(start_size + (GAME_OVER_MAX_FONT_SIZE - start_size) * progress)
        current_alpha = int(start_alpha + (GAME_OVER_END_ALPHA - start_alpha) * progress)
        
        current_alpha = max(0, min(255, current_alpha))
        current_size = max(1, current_size)
        
        try:
            if self.game_over_font is None or self.game_over_font.get_height() != current_size:
                self.game_over_font = pygame.font.Font(None, current_size) 
                
            text_surface = self.game_over_font.render("GAME OVER", True, (200, 0, 0))
            text_surface.set_alpha(current_alpha)
            
            screen_rect = surface.get_rect()
            text_rect = text_surface.get_rect(center=screen_rect.center)
            
            surface.blit(text_surface, text_rect)
        except pygame.error:
            pass
        except AttributeError:
            pass

    def _draw_win_screen(self, surface):
        try:
            if self.game_over_font is None:
                self.game_over_font = pygame.font.Font(None, GAME_OVER_MAX_FONT_SIZE) 
                
            text_surface = self.game_over_font.render("WIN!", True, (255, 215, 0))
            
            screen_rect = surface.get_rect()
            text_rect = text_surface.get_rect(center=screen_rect.center)
            
            surface.blit(text_surface, text_rect)
        except pygame.error:
            pass

    def _setup_new_game_button(self):
        try:
            unpressed_path = "UI/ui_sprites/play_button_unpressed.png"
            pressed_path = "UI/ui_sprites/play_button_pressed.png"

            button_scale = 2.0
            
            self.new_game_button = Button(
                0, 0,
                unpressed_path, 
                pressed_path, 
                callback=self._start_new_game,
                scale=button_scale
            )
            
            screen_rect = pygame.display.get_surface().get_rect()
            game_over_text_center_y = screen_rect.centery 
            
            button_rect = self.new_game_button.rect
            button_x = screen_rect.centerx - button_rect.width // 2
            button_y = game_over_text_center_y + (GAME_OVER_MAX_FONT_SIZE // 2) + 50 
            self.new_game_button.rect.topleft = (button_x, button_y)
            
        except pygame.error as e:
            self.new_game_button = None
        except FileNotFoundError as e:
            self.new_game_button = None
            
    def _start_new_game(self):
        print("New Game button clicked!")
        return ACTION_NEW_GAME

    def set_audio_manager(self, audio_manager):
        self.audio_manager = audio_manager

    def _center_volume_elements(self):
        screen_rect = pygame.display.get_surface().get_rect()
        
        self.volume_text_rect = self.volume_text.get_rect(
            centerx=screen_rect.centerx,
            top=self.paused_text_rect.bottom + 50
        )
        
        self.slider_rect.centerx = screen_rect.centerx
        self.slider_rect.top = self.volume_text_rect.bottom + 20
        
        if self.resume_button:
            self.resume_button.rect.centerx = screen_rect.centerx
            self.resume_button.rect.top = self.slider_rect.bottom + 40