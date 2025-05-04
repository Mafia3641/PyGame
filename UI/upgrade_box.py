import pygame
import os

# Helper function for text wrapping
def wrap_text(text, font, max_width):
    lines = []
    words = text.split(' ')
    current_line = ""
    for word in words:
        # Test line *without* trailing space initially
        test_line_no_space = current_line + word
        # Check if adding the word itself exceeds the width
        if font.size(test_line_no_space)[0] <= max_width:
            # If it fits, update current_line *with* the space for the next iteration
            current_line += word + " "
        else:
            # If adding the word *doesn't* fit:
            # 1. Handle the case where the current line is empty (first word is too long)
            if not current_line:
                # If the first word is too long, add it anyway (it will overflow,
                # but breaking words is complex and might not be desired visually)
                lines.append(word)
                current_line = "" # Reset for next word
                continue # Skip the rest of the loop for this word

            # 2. Add the previous line (without the new word)
            lines.append(current_line.strip())
            # Start the new line with the current word (plus space for next iteration)
            current_line = word + " "

    # Add the last remaining line
    lines.append(current_line.strip())
    # Filter out any potentially empty lines created by the logic
    lines = [line for line in lines if line]
    return lines

class UpgradeBox:
    def __init__(self, upgrade_data, position, size=(250, 750)): # Use taller default size
        self.data = upgrade_data
        self.position = position
        self.size = size
        self.rect = pygame.Rect(position, size)
        self.padding = 25 # Transparent border/padding

        # --- Load Resources --- #
        self.background = None
        self.icon = None
        self.title_font = None
        self.desc_font = None
        self.stats_font = None
        
        # --- Rendered Surfaces & Rects --- #
        self.title_surfs = []
        self.title_rects = []
        self.desc_surfs = []
        self.desc_rects = []
        self.stats_surf = None
        self.stats_rect = None
        self.icon_surf = None # Store potentially scaled icon
        self.icon_draw_rect = None # Rect to draw icon within its section
        
        self._load_resources()
        self._prepare_layout()

    def _load_resources(self):
        # Load Background
        try:
            bg_path = "Sprites/Upgrades/Upgrade_sheets/window.png"
            self.background = pygame.image.load(bg_path).convert_alpha()
            self.background = pygame.transform.scale(self.background, self.size)
        except (pygame.error, FileNotFoundError) as e:
            self.background = pygame.Surface(self.size)
            self.background.fill((50, 50, 70))
            pygame.draw.rect(self.background, (200, 200, 220), self.background.get_rect(), 3)

        # Load Icon
        try:
            icon_path = self.data.get('icon', '')
            if icon_path and os.path.exists(icon_path):
                self.icon_surf = pygame.image.load(icon_path).convert_alpha()
            else:
                 self.icon_surf = None # Explicitly set to None if not found
        except pygame.error as e:
            self.icon_surf = None

        # Load Fonts
        try:
            self.title_font = pygame.font.Font(None, 30) 
            self.desc_font = pygame.font.Font(None, 22)  
            self.stats_font = pygame.font.Font(None, 24) 
        except pygame.error as e:
             self.title_font = pygame.font.SysFont('arial', 28)
             self.desc_font = pygame.font.SysFont('arial', 20)
             self.stats_font = pygame.font.SysFont('arial', 22)

    def _prepare_layout(self):
        # Calculate the useful inner area after padding
        useful_rect = self.rect.inflate(-self.padding * 2, -self.padding * 2)
        content_width = useful_rect.width
        
        # Define section heights based on percentages - ADJUSTED
        icon_section_height = useful_rect.height * 0.40 # Increased from 0.20
        text_section_height = useful_rect.height * 0.40 # Decreased from 0.50
        stats_section_height = useful_rect.height * 0.20 # Decreased from 0.30
        
        # Define section rectangles (relative to useful_rect top-left)
        icon_section_rect = pygame.Rect(useful_rect.left, useful_rect.top, 
                                      content_width, icon_section_height)
        text_section_rect = pygame.Rect(useful_rect.left, icon_section_rect.bottom, 
                                      content_width, text_section_height)
        stats_section_rect = pygame.Rect(useful_rect.left, text_section_rect.bottom, 
                                       content_width, stats_section_height)
                                       
        current_y = 0 # Track y position within each section
        text_color = (255, 255, 255)

        # --- Section 1: Icon (Top 40%) --- #
        if self.icon_surf:
            # Restore logic to scale uniformly while fitting the section
            max_w = icon_section_rect.width
            max_h = icon_section_rect.height
            icon_w, icon_h = self.icon_surf.get_size() # Get original size
            
            # Calculate scale factor to fit within the section (preserves aspect ratio)
            # Avoid division by zero if icon dimensions are somehow 0
            if icon_w > 0 and icon_h > 0:
                scale = min(max_w / icon_w, max_h / icon_h)
            else:
                scale = 1.0 # Default scale if icon dimensions are invalid

            # Apply scaling (upscaling or downscaling)
            new_w, new_h = int(icon_w * scale), int(icon_h * scale)
            
            # Use smoothscale for potentially better quality
            # Only scale if necessary (new dimensions are different)
            if (new_w, new_h) != (icon_w, icon_h):
                 self.icon_surf = pygame.transform.smoothscale(self.icon_surf, (new_w, new_h))
            
            # Center the scaled icon within the icon section
            self.icon_draw_rect = self.icon_surf.get_rect(center=icon_section_rect.center)
        else:
             self.icon_draw_rect = None # Ensure it's None if no icon

        # --- Section 2: Title & Description (Middle 40%) --- #
        current_y = text_section_rect.top # Reset Y for this section
        self.title_surfs = []
        self.title_rects = []
        self.desc_surfs = []
        self.desc_rects = []
        available_text_height = text_section_rect.height

        # Title
        if self.title_font and self.data.get('title'):
            title_lines = wrap_text(self.data['title'], self.title_font, content_width)
            title_line_height = self.title_font.get_linesize()
            for line in title_lines:
                 if available_text_height - title_line_height < 0: break # Stop if no space
                 surf = self.title_font.render(line, True, text_color)
                 rect = surf.get_rect(centerx=text_section_rect.centerx, top=current_y)
                 self.title_surfs.append(surf)
                 self.title_rects.append(rect)
                 current_y += title_line_height
                 available_text_height -= title_line_height
            current_y += 5 # Spacing after title
            available_text_height -= 5

        # Description
        if self.desc_font and self.data.get('description'):
            desc_lines = wrap_text(self.data['description'], self.desc_font, content_width)
            desc_line_height = self.desc_font.get_linesize()
            for line in desc_lines:
                if available_text_height - desc_line_height < 0: break # Stop if no space
                surf = self.desc_font.render(line, True, text_color)
                # Position lines centered within the section
                rect = surf.get_rect(centerx=text_section_rect.centerx, top=current_y)
                self.desc_surfs.append(surf)
                self.desc_rects.append(rect)
                current_y += desc_line_height
                available_text_height -= desc_line_height

        # --- Section 3: Stats (Bottom 20%) --- #
        self.stats_surf = None
        self.stats_rect = None
        stats_text = ""
        stats_data = self.data.get('stats', {})
        if stats_data:
            stat_lines = []
            for stat, value in stats_data.items():
                prefix = "+" if value >= 0 else ""
                if "mult" in stat or "percent" in stat:
                    stat_lines.append(f"{stat.replace('_', ' ').title()}: {prefix}{value*100:.0f}%")
                else:
                    stat_lines.append(f"{stat.replace('_', ' ').title()}: {prefix}{value}")
            stats_text = " | ".join(stat_lines)
        
        if self.stats_font and stats_text:
            self.stats_surf = self.stats_font.render(stats_text, True, (200, 255, 200))
            # Center stats within the stats section rectangle
            self.stats_rect = self.stats_surf.get_rect(center=stats_section_rect.center)
        
    def draw(self, surface):
        # Draw background
        if self.background:
            surface.blit(self.background, self.position)

        # --- DEBUG: Draw white border around the main rect --- #
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 1) # White color, 1px thickness
        # --- END DEBUG --- #

        # Get absolute position for drawing elements inside the box
        # The rects calculated in _prepare_layout are already in absolute screen coords relative to box origin
        # We just need to offset them by the box's actual position on the screen
        abs_x, abs_y = self.position

        # Draw Icon
        if self.icon_surf and self.icon_draw_rect:
            surface.blit(self.icon_surf, (abs_x + self.icon_draw_rect.x - self.rect.x, 
                                          abs_y + self.icon_draw_rect.y - self.rect.y))

        # Draw Title Lines
        for i, surf in enumerate(self.title_surfs):
             rect = self.title_rects[i]
             surface.blit(surf, (abs_x + rect.x - self.rect.x, abs_y + rect.y - self.rect.y))

        # Draw Description Lines
        for i, surf in enumerate(self.desc_surfs):
             rect = self.desc_rects[i]
             surface.blit(surf, (abs_x + rect.x - self.rect.x, abs_y + rect.y - self.rect.y))

        # Draw Stats
        if self.stats_surf and self.stats_rect:
             surface.blit(self.stats_surf, (abs_x + self.stats_rect.x - self.rect.x, 
                                             abs_y + self.stats_rect.y - self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                return self.data 
        return None 