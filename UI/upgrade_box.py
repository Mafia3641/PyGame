import pygame
import os

def wrap_text(text, font, max_width):
    lines = []
    words = text.split(' ')
    current_line = ""
    for word in words:
        test_line_no_space = current_line + word
        if font.size(test_line_no_space)[0] <= max_width:
            current_line += word + " "
        else:
            if not current_line:
                lines.append(word)
                current_line = ""
                continue

            lines.append(current_line.strip())
            current_line = word + " "

    lines.append(current_line.strip())
    lines = [line for line in lines if line]
    return lines

class UpgradeBox:
    def __init__(self, upgrade_data, position, size=(250, 750)):
        self.data = upgrade_data
        self.position = position
        self.size = size
        self.rect = pygame.Rect(position, size)
        self.padding = 25

        self.background = None
        self.icon = None
        self.title_font = None
        self.desc_font = None
        self.stats_font = None
        
        self.title_surfs = []
        self.title_rects = []
        self.desc_surfs = []
        self.desc_rects = []
        self.stats_surfs = []
        self.stats_rects = []
        self.icon_surf = None
        self.original_icon_surf = None
        self.icon_draw_rect = None
        
        self._load_resources()
        self._prepare_layout()

    def _load_resources(self):
        try:
            bg_path = "Sprites/Upgrades/Upgrade_sheets/window.png"
            self.background = pygame.image.load(bg_path).convert_alpha()
            self.background = pygame.transform.scale(self.background, self.size)
        except (pygame.error, FileNotFoundError) as e:
            self.background = pygame.Surface(self.size)
            self.background.fill((50, 50, 70))
            pygame.draw.rect(self.background, (200, 200, 220), self.background.get_rect(), 3)

        try:
            icon_path = self.data.get('icon')
            if icon_path:
                self.original_icon_surf = pygame.image.load(icon_path).convert_alpha()
                self.icon_surf = None
            else:
                self.original_icon_surf = None
        except (pygame.error, FileNotFoundError):
            self.original_icon_surf = None
            self.icon_surf = None

        try:
            self.title_font = pygame.font.Font(None, 30)
            self.desc_font = pygame.font.Font(None, 22)
            self.stats_font = pygame.font.Font(None, 24)
        except pygame.error as e:
             self.title_font = pygame.font.SysFont('arial', 28)
             self.desc_font = pygame.font.SysFont('arial', 20)
             self.stats_font = pygame.font.SysFont('arial', 22)

    def _prepare_layout(self):
        useful_rect = self.rect.inflate(-self.padding * 2, -self.padding * 2)
        content_width = useful_rect.width
        
        icon_section_height = useful_rect.height * 0.30
        text_section_height = useful_rect.height * 0.50
        stats_section_height = useful_rect.height * 0.20
        
        icon_section_rect = pygame.Rect(useful_rect.left, useful_rect.top,
                                      content_width, icon_section_height)
        text_section_rect = pygame.Rect(useful_rect.left, icon_section_rect.bottom,
                                      content_width, text_section_height)
        stats_section_rect = pygame.Rect(useful_rect.left, text_section_rect.bottom,
                                       content_width, stats_section_height)
                                       
        current_y = 0
        text_color = (255, 255, 255)

        if self.original_icon_surf:
            max_w = icon_section_rect.width
            max_h = icon_section_rect.height
            icon_w, icon_h = self.original_icon_surf.get_size()

            target_scale = 4.0

            potential_w = int(icon_w * target_scale)
            potential_h = int(icon_h * target_scale)

            scale_to_fit = 1.0
            if icon_w > 0 and icon_h > 0:
                 scale_to_fit = min(max_w / icon_w, max_h / icon_h)

            final_scale = min(target_scale, scale_to_fit)

            fit_w, fit_h = int(icon_w * final_scale), int(icon_h * final_scale)

            new_w, new_h = fit_w // 2, fit_h // 2

            if (new_w, new_h) != (icon_w, icon_h):
                 self.icon_surf = pygame.transform.smoothscale(self.original_icon_surf, (new_w, new_h))
            else:
                self.icon_surf = self.original_icon_surf.copy()

            if self.icon_surf:
                self.icon_draw_rect = self.icon_surf.get_rect(centerx=icon_section_rect.centerx,
                                                             centery=icon_section_rect.centery - 24)
            else:
                self.icon_draw_rect = None
        else:
            self.icon_surf = None
            self.icon_draw_rect = None

        current_y = text_section_rect.top

        self.title_surfs = []
        self.title_rects = []
        self.desc_surfs = []
        self.desc_rects = []
        available_text_height = text_section_rect.height

        if self.title_font and self.data.get('title'):
            title_lines = wrap_text(self.data['title'], self.title_font, content_width)
            title_line_height = self.title_font.get_linesize()
            for line in title_lines:
                if available_text_height - title_line_height < 0: break
                surf = self.title_font.render(line, True, text_color)
                rect = surf.get_rect(centerx=text_section_rect.centerx, top=current_y)
                self.title_surfs.append(surf)
                self.title_rects.append(rect)
                current_y += title_line_height
                available_text_height -= title_line_height
            current_y += 5
            available_text_height -= 5

        if self.desc_font and self.data.get('description'):
            desc_lines = wrap_text(self.data['description'], self.desc_font, content_width)
            desc_line_height = self.desc_font.get_linesize()
            for line in desc_lines:
                if available_text_height - desc_line_height < 0: break
                surf = self.desc_font.render(line, True, text_color)
                rect = surf.get_rect(centerx=text_section_rect.centerx, top=current_y)
                self.desc_surfs.append(surf)
                self.desc_rects.append(rect)
                current_y += desc_line_height
                available_text_height -= desc_line_height

        self.stats_surfs = []
        self.stats_rects = []
        stats_messages = self.data.get('stats_message', [])
        stats_color = (200, 255, 200)
        current_stat_y = stats_section_rect.top + 5
        stat_line_height = 0

        if self.stats_font and stats_messages:
            stat_line_height = self.stats_font.get_linesize()
            max_stat_y = stats_section_rect.bottom - 5

            for message in stats_messages:
                if current_stat_y + stat_line_height > max_stat_y:
                    break

                surf = self.stats_font.render(message, True, stats_color)
                rect = surf.get_rect(centerx=stats_section_rect.centerx, top=current_stat_y)
                self.stats_surfs.append(surf)
                self.stats_rects.append(rect)
                current_stat_y += stat_line_height
        
    def draw(self, surface):
        if self.background:
            surface.blit(self.background, self.position)

        pygame.draw.rect(surface, (255, 255, 255), self.rect, 1)

        abs_x, abs_y = self.position

        if self.icon_surf and self.icon_draw_rect:
            surface.blit(self.icon_surf, (abs_x + self.icon_draw_rect.x - self.rect.x,
                                          abs_y + self.icon_draw_rect.y - self.rect.y))

        for i, surf in enumerate(self.title_surfs):
             rect = self.title_rects[i]
             surface.blit(surf, (abs_x + rect.x - self.rect.x, abs_y + rect.y - self.rect.y))

        for i, surf in enumerate(self.desc_surfs):
             rect = self.desc_rects[i]
             surface.blit(surf, (abs_x + rect.x - self.rect.x, abs_y + rect.y - self.rect.y))

        for i, surf in enumerate(self.stats_surfs):
            rect = self.stats_rects[i]
            surface.blit(surf, (abs_x + rect.x - self.rect.x, abs_y + rect.y - self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                return self.data
        return None