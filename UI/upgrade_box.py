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
        self.stats_surfs = [] # Store multiple surfaces for each line
        self.stats_rects = [] # Store multiple rects
        self.icon_surf = None # Store potentially scaled icon
        self.original_icon_surf = None # Store the original loaded icon
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
            icon_path = self.data.get('icon')
            if icon_path:
                self.original_icon_surf = pygame.image.load(icon_path).convert_alpha() # Load into original
                self.icon_surf = None # Reset scaled surface
            else:
                self.original_icon_surf = None
        except (pygame.error, FileNotFoundError):
            self.original_icon_surf = None
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
        # Give even more space to the icon
        icon_section_height = useful_rect.height * 0.30 
        text_section_height = useful_rect.height * 0.50 
        stats_section_height = useful_rect.height * 0.20
        
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
        if self.original_icon_surf: # Check original surface
            # Restore logic to scale uniformly while fitting the section
            max_w = icon_section_rect.width
            max_h = icon_section_rect.height
            icon_w, icon_h = self.original_icon_surf.get_size() # Get size from original

            # --- MODIFIED SCALING LOGIC ---
            # Target scale factor (double the original size)
            target_scale = 4.0 # Reduce target scale, likely not the limiting factor now

            # Calculate potential new dimensions
            potential_w = int(icon_w * target_scale)
            potential_h = int(icon_h * target_scale)

            # Calculate scale factor needed to fit within the section
            scale_to_fit = 1.0
            if icon_w > 0 and icon_h > 0:
                 scale_to_fit = min(max_w / icon_w, max_h / icon_h)

            # Use the smaller of the target scale or the scale needed to fit
            final_scale = min(target_scale, scale_to_fit)

            # Calculate dimensions based on fitting the section
            fit_w, fit_h = int(icon_w * final_scale), int(icon_h * final_scale)

            # Explicitly halve the dimensions to make icon smaller
            new_w, new_h = fit_w // 2, fit_h // 2
            # --- END MODIFIED SCALING LOGIC ---

            # Use smoothscale for potentially better quality
            if (new_w, new_h) != (icon_w, icon_h):
                 # Ensure scaling is applied to the *original* loaded surface if it exists
                 # (We store the original in self.icon before modification)
                 # Scale from the original surface into self.icon_surf
                 self.icon_surf = pygame.transform.smoothscale(self.original_icon_surf, (new_w, new_h))
            else:
                # If no scaling needed, just use the original surface
                self.icon_surf = self.original_icon_surf.copy() # Use a copy to avoid modifying original

            # Center the scaled icon within the icon section
            if self.icon_surf:
                # Center horizontally, but move up vertically by 24 pixels
                self.icon_draw_rect = self.icon_surf.get_rect(centerx=icon_section_rect.centerx, 
                                                             centery=icon_section_rect.centery - 24)
            else: # Should not happen if original_icon_surf existed, but for safety
                self.icon_draw_rect = None
        else:
            self.icon_surf = None # Ensure scaled surf is None if original doesn't exist
            self.icon_draw_rect = None # Ensure it's None if no icon

        # --- Section 2: Title & Description (Middle 40%) --- #
        # Restore original text positioning logic
        current_y = text_section_rect.top 

        self.title_surfs = []
        self.title_rects = []
        self.desc_surfs = []
        self.desc_rects = []
        # Restore available height calculation
        available_text_height = text_section_rect.height

        # Title
        if self.title_font and self.data.get('title'):
            title_lines = wrap_text(self.data['title'], self.title_font, content_width)
            title_line_height = self.title_font.get_linesize()
            for line in title_lines:
                # Restore check against available height
                if available_text_height - title_line_height < 0: break 
                surf = self.title_font.render(line, True, text_color)
                # Restore centering
                rect = surf.get_rect(centerx=text_section_rect.centerx, top=current_y)
                self.title_surfs.append(surf)
                self.title_rects.append(rect)
                current_y += title_line_height
                # Restore decrementing available height
                available_text_height -= title_line_height
            current_y += 5 # Spacing after title
            available_text_height -= 5 # Restore decrementing available height for spacing

        # Description
        if self.desc_font and self.data.get('description'):
            desc_lines = wrap_text(self.data['description'], self.desc_font, content_width)
            desc_line_height = self.desc_font.get_linesize()
            for line in desc_lines:
                # Restore check against available height
                if available_text_height - desc_line_height < 0: break
                surf = self.desc_font.render(line, True, text_color)
                # Restore centering
                rect = surf.get_rect(centerx=text_section_rect.centerx, top=current_y)
                self.desc_surfs.append(surf)
                self.desc_rects.append(rect)
                current_y += desc_line_height
                # Restore decrementing available height
                available_text_height -= desc_line_height

        # --- Section 3: Stats (Bottom 20%) --- #
        self.stats_surfs = [] # Store multiple surfaces for each line
        self.stats_rects = [] # Store multiple rects
        stats_messages = self.data.get('stats_message', [])
        stats_color = (200, 255, 200)
        current_stat_y = stats_section_rect.top + 5 # Start 5px below section top
        stat_line_height = 0

        if self.stats_font and stats_messages:
            stat_line_height = self.stats_font.get_linesize()
            max_stat_y = stats_section_rect.bottom - 5 # Limit 5px above section bottom

            for message in stats_messages:
                if current_stat_y + stat_line_height > max_stat_y:
                    break # Stop if no more space

                surf = self.stats_font.render(message, True, stats_color)
                # Center each stat line horizontally within the stats section
                rect = surf.get_rect(centerx=stats_section_rect.centerx, top=current_stat_y)
                self.stats_surfs.append(surf)
                self.stats_rects.append(rect)
                current_stat_y += stat_line_height
        
    def draw(self, surface):
        # Draw background
        if self.background:
            surface.blit(self.background, self.position)

        # --- DEBUG: Draw white border around the main rect --- #
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 1) # White color, 1px thickness
        # --- END DEBUG --- #

        # The rects calculated in _prepare_layout are already in absolute screen coords relative to box origin
        # We just need to offset them by the box's actual position on the screen
        abs_x, abs_y = self.position # Restore original offset calculation

        # Draw Icon
        if self.icon_surf and self.icon_draw_rect:
            # Restore original blitting with offset
            surface.blit(self.icon_surf, (abs_x + self.icon_draw_rect.x - self.rect.x, 
                                          abs_y + self.icon_draw_rect.y - self.rect.y))

        # Draw Title Lines
        for i, surf in enumerate(self.title_surfs):
             rect = self.title_rects[i]
             # Restore original blitting with offset
             surface.blit(surf, (abs_x + rect.x - self.rect.x, abs_y + rect.y - self.rect.y))

        # Draw Description Lines
        for i, surf in enumerate(self.desc_surfs):
             rect = self.desc_rects[i]
             # Restore original blitting with offset
             surface.blit(surf, (abs_x + rect.x - self.rect.x, abs_y + rect.y - self.rect.y))

        # Draw Stats
        # Draw Stat Lines
        for i, surf in enumerate(self.stats_surfs):
            rect = self.stats_rects[i]
            # Use original blitting with offset for each line
            surface.blit(surf, (abs_x + rect.x - self.rect.x, abs_y + rect.y - self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                return self.data 
        return None 