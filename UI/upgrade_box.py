import pygame
import os

# Helper function for text wrapping
def wrap_text(text, font, max_width):
    lines = []
    words = text.split(' ')
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        # Check width
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            # Add the completed line (strip trailing space)
            lines.append(current_line.strip())
            # Start new line with the current word
            current_line = word + " "
    lines.append(current_line.strip()) # Add the last line
    return lines

class UpgradeBox:
    def __init__(self, upgrade_data, position, size=(250, 400)):
        self.data = upgrade_data
        self.position = position
        self.size = size
        self.rect = pygame.Rect(position, size)

        # --- Load Resources (Handle potential errors) --- #
        self.background = None
        self.icon = None
        self.title_font = None
        self.desc_font = None
        self.stats_font = None
        
        self.title_surf = None
        self.desc_surfs = [] # List of surfaces for wrapped lines
        self.stats_surf = None
        self.icon_rect = None

        try:
            bg_path = "Sprites/Upgrades/Upgrade_sheets/window.png"
            self.background = pygame.image.load(bg_path).convert_alpha()
            self.background = pygame.transform.scale(self.background, self.size)
        except (pygame.error, FileNotFoundError) as e:
            # Create fallback background
            self.background = pygame.Surface(self.size)
            self.background.fill((50, 50, 70)) # Dark greyish blue
            pygame.draw.rect(self.background, (200, 200, 220), self.background.get_rect(), 3) # Border

        try:
            icon_path = self.data.get('icon', '')
            if icon_path and os.path.exists(icon_path):
                self.icon = pygame.image.load(icon_path).convert_alpha()
                # Scale icon (e.g., to 1/3 of card width)
                icon_width = self.size[0] // 3
                aspect_ratio = self.icon.get_height() / self.icon.get_width()
                icon_height = int(icon_width * aspect_ratio)
                self.icon = pygame.transform.smoothscale(self.icon, (icon_width, icon_height))
            else:
                 # print(f"Warning: Icon not found or path missing for {self.data.get('title', 'Upgrade')}: {icon_path}") # Commented out original warning too
                 pass # Keep the structure
        except pygame.error as e:
            # print(f"Error loading icon ({icon_path}): {e}")
            self.icon = None

        # --- Fonts (Consider using a global font manager later) --- #
        try:
            self.title_font = pygame.font.Font(None, 30) # Example size
            self.desc_font = pygame.font.Font(None, 22)  # Smaller for description
            self.stats_font = pygame.font.Font(None, 24) # Example size
        except pygame.error as e:
             # print(f"Error loading fonts for UpgradeBox: {e}")
             # Use system fallback
             self.title_font = pygame.font.SysFont('arial', 28)
             self.desc_font = pygame.font.SysFont('arial', 20)
             self.stats_font = pygame.font.SysFont('arial', 22)
        # -------------------------------------------------------- #

        self._render_text() # Prepare text surfaces

    def _render_text(self):
        padding = 15 # Padding inside the card
        content_width = self.size[0] - 2 * padding
        current_y = padding
        text_color = (255, 255, 255) # White text

        # --- Title --- #
        if self.title_font and self.data.get('title'):
            self.title_surf = self.title_font.render(self.data['title'], True, text_color)
            self.title_rect = self.title_surf.get_rect(midtop=(self.size[0] // 2, current_y))
            current_y = self.title_rect.bottom + 10 # Spacing
        
        # --- Icon --- #
        if self.icon:
            self.icon_rect = self.icon.get_rect(centerx=self.size[0] // 2, top=current_y)
            current_y = self.icon_rect.bottom + 10 # Spacing
        else:
             # Add space even if icon fails to load
             current_y += self.size[0] // 3 + 10 

        # --- Description --- #
        self.desc_surfs = []
        desc_start_y = current_y
        if self.desc_font and self.data.get('description'):
            wrapped_lines = wrap_text(self.data['description'], self.desc_font, content_width)
            line_height = self.desc_font.get_linesize()
            for line in wrapped_lines:
                surf = self.desc_font.render(line, True, text_color)
                rect = surf.get_rect(topleft=(padding, current_y))
                self.desc_surfs.append((surf, rect))
                current_y += line_height
            current_y += 5 # Spacing after description block
        else:
             current_y += 50 # Placeholder space if no description

        # --- Stats --- # 
        stats_text = ""
        stats_data = self.data.get('stats', {})
        if stats_data:
            stat_lines = []
            for stat, value in stats_data.items():
                prefix = "+" if value >= 0 else ""
                # Handle percentage vs flat based on stat name? (Simple for now)
                if "mult" in stat or "percent" in stat:
                    stat_lines.append(f"{stat.replace('_', ' ').title()}: {prefix}{value*100:.0f}%")
                else:
                    stat_lines.append(f"{stat.replace('_', ' ').title()}: {prefix}{value}")
            stats_text = " | ".join(stat_lines)
        
        if self.stats_font and stats_text:
            self.stats_surf = self.stats_font.render(stats_text, True, (200, 255, 200)) # Light Green
            # Position stats near the bottom
            self.stats_rect = self.stats_surf.get_rect(centerx=self.size[0] // 2, 
                                                       bottom=self.size[1] - padding)
        
    def draw(self, surface):
        # Draw background
        if self.background:
            surface.blit(self.background, self.position)

        # Get absolute position for drawing elements inside the box
        abs_x, abs_y = self.position

        # Draw Title
        if self.title_surf:
            surface.blit(self.title_surf, (abs_x + self.title_rect.x, abs_y + self.title_rect.y))

        # Draw Icon
        if self.icon:
            surface.blit(self.icon, (abs_x + self.icon_rect.x, abs_y + self.icon_rect.y))
            
        # Draw Description Lines
        for surf, rect in self.desc_surfs:
            surface.blit(surf, (abs_x + rect.x, abs_y + rect.y))

        # Draw Stats
        if self.stats_surf:
             surface.blit(self.stats_surf, (abs_x + self.stats_rect.x, abs_y + self.stats_rect.y))

    # Placeholder for click handling later
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                # print(f"Clicked on Upgrade: {self.data.get('title')}") # Debug
                return self.data # Return the upgrade data when clicked
        return None 