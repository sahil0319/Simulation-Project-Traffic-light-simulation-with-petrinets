import pygame
from sys import exit
from adaptive_controller import AdaptiveController
from vehicle import VehicleManager
from pedestrian import PedestrianManager, Pedestrian
from game_modes import AutomaticMode, ManualSurvivalMode, ScenarioChallengeMode
from metrics import Metrics

pygame.init()

# --- Font ---
FONT_PATH = "font/Pixeltype.ttf" 
ui_font = pygame.font.Font(FONT_PATH, 30)

# --- Window ---
W, H = 1000, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Petri Net Traffic Controller")
clock = pygame.time.Clock()

# --- Colors ---
BG = (25, 25, 25)
ROAD = (55, 55, 55)
LANE = (120, 120, 120)
WHITE = (230, 230, 230)
YELLOW = (255, 220, 40)
RED = (255, 60, 60)
GREEN = (60, 255, 120)
SIDEWALK = (85, 85, 85)

# --- Intersection geometry ---
cx, cy = W // 2, H // 2
road_width = 220
cross_size = 260 

vertical_road = pygame.Rect(cx - road_width // 2, 0, road_width, H)
horizontal_road = pygame.Rect(0, cy - road_width // 2, W, road_width)
intersection = pygame.Rect(cx - cross_size // 2, cy - cross_size // 2, cross_size, cross_size)

# --- Road Info for Vehicles ---
# N=Southbound (Top->Bottom), S=Northbound (Bottom->Top), E=Westbound (Right->Left), W=Eastbound (Left->Right)
# (Based on standard RHT)
# N Lane: x < cx. S Lane: x > cx.
# W Lane (Eastbound): y > cy. E Lane (Westbound): y < cy.

# Starts
start_N = (cx - road_width // 4, -60)
start_S = (cx + road_width // 4, H + 60)
start_E = (W + 60, cy - road_width // 4) 
start_W = (-60, cy + road_width // 4)

# Stop Lines (Approximate Y or X values)
# N stop Y: intersection top
stop_y_N = intersection.top - 20
stop_y_S = intersection.bottom + 20
stop_x_W = intersection.left - 20
stop_x_E = intersection.right + 20

road_info = {
    "starts": {"N": start_N, "S": start_S, "E": start_E, "W": start_W},
    "stop_lines": {"N": stop_y_N, "S": stop_y_S, "E": stop_x_E, "W": stop_x_W}
}

# --- Traffic Poles ---
# 0: NW, 1: NE, 2: SE, 3: SW
poles = [
    {"name": "NW", "pos": (intersection.left - 35, intersection.top - 80), "state": "red"},
    {"name": "NE", "pos": (intersection.right + 35, intersection.top - 80), "state": "red"},
    {"name": "SW", "pos": (intersection.left - 35, intersection.bottom + 20), "state": "red"},
    {"name": "SE", "pos": (intersection.right + 35, intersection.bottom + 20), "state": "red"},
]
# Map Approach Direction to Pole Index
# N (Southbound) looks at NW pole? Or NE?
# Typically N approaches from top, sees light on FAR RIGHT (SW) or NEAR RIGHT (NW).
# Let's map: 
# N traffic (from top) -> Looks at NW signal (idx 0) 
# E traffic (from right) -> Looks at NE signal (idx 1)
# S traffic (from bottom) -> Looks at SE signal (idx 3)
# W traffic (from left) -> Looks at SW signal (idx 2)
# Wait, this matches the previous code's mapping logic roughly?
# "N": name_to_index["NW"] (0)
# "E": name_to_index["NE"] (1)
# "S": name_to_index["SE"] (3)
# "W": name_to_index["SW"] (2)

approach_map = {"N": 0, "E": 1, "S": 3, "W": 2}

# --- Managers ---
vehicle_manager = VehicleManager(road_info)
pedestrian_manager = PedestrianManager(road_info)
controller = AdaptiveController(poles, approach_map)
metrics = Metrics()

# --- Modes ---
modes = [
    AutomaticMode(controller, vehicle_manager),
    ManualSurvivalMode(controller, vehicle_manager),
    ScenarioChallengeMode(controller, vehicle_manager)
]
current_mode_idx = 0

# --- Selected Pole (Manual Only) ---
selected_pole = None

# --- Drawing Helpers ---
def draw_sidewalk():
    pad = 25
    pygame.draw.rect(screen, SIDEWALK, pygame.Rect(0, 0, cx - road_width//2 - pad, cy - road_width//2 - pad))
    pygame.draw.rect(screen, SIDEWALK, pygame.Rect(cx + road_width//2 + pad, 0, W, cy - road_width//2 - pad))
    pygame.draw.rect(screen, SIDEWALK, pygame.Rect(0, cy + road_width//2 + pad, cx - road_width//2 - pad, H))
    pygame.draw.rect(screen, SIDEWALK, pygame.Rect(cx + road_width//2 + pad, cy + road_width//2 + pad, W, H))

def draw_light(x, y, state="red"):
    pygame.draw.rect(screen, (40, 40, 40), (x - 12, y - 12, 24, 60), border_radius=6)
    r = 7
    red_on = state in ("red", "red_yellow")
    yellow_on = state in ("yellow", "red_yellow")
    green_on = state == "green"
    pygame.draw.circle(screen, RED if red_on else (70,70,70), (x, y), r)
    pygame.draw.circle(screen, YELLOW if yellow_on else (70,70,70), (x, y + 18), r)
    pygame.draw.circle(screen, GREEN if green_on else (70,70,70), (x, y + 36), r)

def draw_crosswalk_horizontal(y, x_start, x_end, stripe_w=10, gap=8):
    x = x_start
    while x < x_end:
        pygame.draw.rect(screen, WHITE, (x, y, stripe_w, 30))
        x += stripe_w + gap

def draw_crosswalk_vertical(x, y_start, y_end, stripe_h=10, gap=8):
    y = y_start
    while y < y_end:
        pygame.draw.rect(screen, WHITE, (x, y, 30, stripe_h))
        y += stripe_h + gap

def draw_ui():
    mode_name = modes[current_mode_idx].name
    lbl = ui_font.render(f"Mode: {mode_name} (Press M to switch)", True, WHITE)
    screen.blit(lbl, (20, 20))
    
    if selected_pole is not None:
        p = poles[selected_pole]
        txt = ui_font.render(f"Selected: {p['name']} ({p['state']})", True, YELLOW)
        screen.blit(txt, (20, 50))

# --- Main Loop ---
running = True
while running:
    dt = clock.tick(60) / 1000.0
    
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            exit()
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                current_mode_idx = (current_mode_idx + 1) % len(modes)
                metrics = Metrics()
            
                metrics = Metrics()
            
            modes[current_mode_idx].handle_input(event, selected_pole)
            
            if event.key == pygame.K_ESCAPE:
                selected_pole = None

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            for i, p in enumerate(poles):
                rect = pygame.Rect(p["pos"][0]-20, p["pos"][1]-20, 40, 110)
                if rect.collidepoint(mx, my):
                    selected_pole = i

    # Update
    current_mode = modes[current_mode_idx]
    current_mode.update(dt)
    metrics.update(vehicle_manager)
    
    # Draw
    screen.fill(BG)
    draw_sidewalk()
    
    # Draw roads
    pygame.draw.rect(screen, ROAD, vertical_road)
    pygame.draw.rect(screen, ROAD, horizontal_road)
    pygame.draw.rect(screen, (45, 45, 45), intersection)
    
    # --- Road Markings ---
    
    # helper for double yellow
    def draw_double_yellow(start_pos, end_pos):
        # We'll expect vertical or horizontal lines
        # Draw two lines 4px apart, centered on the abstract line
        if start_pos[0] == end_pos[0]: # Vertical
            x = start_pos[0]
            pygame.draw.line(screen, YELLOW, (x - 3, start_pos[1]), (x - 3, end_pos[1]), 3)
            pygame.draw.line(screen, YELLOW, (x + 3, start_pos[1]), (x + 3, end_pos[1]), 3)
        else: # Horizontal
            y = start_pos[1]
            pygame.draw.line(screen, YELLOW, (start_pos[0], y - 3), (end_pos[0], y - 3), 3)
            pygame.draw.line(screen, YELLOW, (start_pos[0], y + 3), (end_pos[0], y + 3), 3)

    # helper for dashed white
    def draw_dashed_white(start_pos, end_pos):
        if start_pos[0] == end_pos[0]: # Vertical
            x = start_pos[0]
            for y in range(int(start_pos[1]), int(end_pos[1]), 40):
                pygame.draw.line(screen, WHITE, (x, y), (x, min(y + 20, end_pos[1])), 2)
        else: # Horizontal
            y = start_pos[1]
            for x in range(int(start_pos[0]), int(end_pos[0]), 40):
                pygame.draw.line(screen, WHITE, (x, y), (min(x + 20, end_pos[0]), y), 2)

    # 1. Double Yellow Center Lines
    draw_double_yellow((cx, 0), (cx, cy - cross_size//2)) # Top
    draw_double_yellow((cx, cy + cross_size//2), (cx, H)) # Bottom
    draw_double_yellow((0, cy), (cx - cross_size//2, cy)) # Left
    draw_double_yellow((cx + cross_size//2, cy), (W, cy)) # Right

    # 2. Lane Dividers (Dashed White) - separating Lane 1 (Inner) and Lane 2 (Outer)
    # Road Width 220. Center cx. Half 110. Lanes roughly 55 wide.
    # Divider is at cx +/- 55.
    
    # Vertical Road
    draw_dashed_white((cx - 55, 0), (cx - 55, cy - cross_size//2)) # Top Left (N-bound Incoming)
    draw_dashed_white((cx + 55, 0), (cx + 55, cy - cross_size//2)) # Top Right (N-bound Outgoing)
    
    draw_dashed_white((cx - 55, cy + cross_size//2), (cx - 55, H)) # Bottom Left (S-bound Outgoing)
    draw_dashed_white((cx + 55, cy + cross_size//2), (cx + 55, H)) # Bottom Right (S-bound Incoming)

    # Horizontal Road
    draw_dashed_white((0, cy - 55), (cx - cross_size//2, cy - 55)) # Left Top (W-bound Outgoing)
    draw_dashed_white((0, cy + 55), (cx - cross_size//2, cy + 55)) # Left Bottom (W-bound Incoming)
    
    draw_dashed_white((cx + cross_size//2, cy - 55), (W, cy - 55)) # Right Top (E-bound Incoming)
    draw_dashed_white((cx + cross_size//2, cy + 55), (W, cy + 55)) # Right Bottom (E-bound Outgoing)

    # 3. Shoulder Lines (Solid White) at Road Edges
    # Edges at cx +/- 110
    
    # Vertical
    pygame.draw.line(screen, WHITE, (cx - 110, 0), (cx - 110, cy - cross_size//2), 3) # Top Left Edge
    pygame.draw.line(screen, WHITE, (cx + 110, 0), (cx + 110, cy - cross_size//2), 3) # Top Right Edge
    pygame.draw.line(screen, WHITE, (cx - 110, cy + cross_size//2), (cx - 110, H), 3) # Bottom Left Edge
    pygame.draw.line(screen, WHITE, (cx + 110, cy + cross_size//2), (cx + 110, H), 3) # Bottom Right Edge
    
    # Horizontal
    pygame.draw.line(screen, WHITE, (0, cy - 110), (cx - cross_size//2, cy - 110), 3) # Left Top Edge
    pygame.draw.line(screen, WHITE, (0, cy + 110), (cx - cross_size//2, cy + 110), 3) # Left Bottom Edge
    pygame.draw.line(screen, WHITE, (cx + cross_size//2, cy - 110), (W, cy - 110), 3) # Right Top Edge
    pygame.draw.line(screen, WHITE, (cx + cross_size//2, cy + 110), (W, cy + 110), 3) # Right Bottom Edge
    
    # Crosswalks (Restored stripes)
    draw_crosswalk_horizontal(intersection.top - 55, cx - road_width // 2 + 20, cx + road_width // 2 - 20)
    draw_crosswalk_horizontal(intersection.bottom + 25, cx - road_width // 2 + 20, cx + road_width // 2 - 20)
    draw_crosswalk_vertical(intersection.left - 55, cy - road_width // 2 + 20, cy + road_width // 2 - 20)
    draw_crosswalk_vertical(intersection.right + 25, cy - road_width // 2 + 20, cy + road_width // 2 - 20)

    # Stop lines (Restored relative dimensions)
    stop_len = road_width - 40
    pygame.draw.rect(screen, WHITE, pygame.Rect(cx - stop_len//2, stop_y_N, stop_len, 8))
    pygame.draw.rect(screen, WHITE, pygame.Rect(cx - stop_len//2, stop_y_S, stop_len, 8))
    pygame.draw.rect(screen, WHITE, pygame.Rect(stop_x_W, cy - stop_len//2, 8, stop_len))
    pygame.draw.rect(screen, WHITE, pygame.Rect(stop_x_E, cy - stop_len//2, 8, stop_len))

    # Entities
    vehicle_manager.draw(screen)
    pedestrian_manager.draw(screen)

    # Traffic Lights
    for i, p in enumerate(poles):
        draw_light(p["pos"][0], p["pos"][1], p["state"])
        if selected_pole == i:
             pygame.draw.rect(screen, WHITE, (p["pos"][0]-20, p["pos"][1]-20, 40, 110), 2)

    # UI
    draw_ui()
    metrics.draw(screen, ui_font)

    pygame.display.flip()

pygame.quit()
