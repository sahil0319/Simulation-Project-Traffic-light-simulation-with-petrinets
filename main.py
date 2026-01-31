import pygame
from sys import exit
from autonomous_controller import AutonomousController

pygame.init()
# --- Font (use your .ttf path here) ---
FONT_PATH = "font/Pixeltype.ttf"   # <-- change this to your font file path
ui_font = pygame.font.Font(FONT_PATH, 30)


# --- Window ---
W, H = 1000, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Intersection Layout (Step 2)")
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


def draw_sidewalk():
    # Sidewalks (simple footpaths around the roads)
    pad = 25  # sidewalk thickness

    # Top-left
    pygame.draw.rect(screen, SIDEWALK, pygame.Rect(0, 0, cx - road_width//2 - pad, cy - road_width//2 - pad))
    # Top-right
    pygame.draw.rect(screen, SIDEWALK, pygame.Rect(cx + road_width//2 + pad, 0, W, cy - road_width//2 - pad))
    # Bottom-left
    pygame.draw.rect(screen, SIDEWALK, pygame.Rect(0, cy + road_width//2 + pad, cx - road_width//2 - pad, H))
    # Bottom-right
    pygame.draw.rect(screen, SIDEWALK, pygame.Rect(cx + road_width//2 + pad, cy + road_width//2 + pad, W, H))


# --- Intersection geometry ---
cx, cy = W // 2, H // 2
road_width = 220
cross_size = 260  # size of the central intersection box

# Road rectangles (plus shape)
vertical_road = pygame.Rect(cx - road_width // 2, 0, road_width, H)
horizontal_road = pygame.Rect(0, cy - road_width // 2, W, road_width)

# Central intersection box
intersection = pygame.Rect(cx - cross_size // 2, cy - cross_size // 2, cross_size, cross_size)


# --- Traffic poles (each has its own state) ---
light_states = ["red", "red_yellow", "green", "yellow"]

selected_pole = None

poles = [
    {"name": "NW", "pos": (intersection.left - 35, intersection.top - 80), "state": "red"},
    {"name": "NE", "pos": (intersection.right + 35, intersection.top - 80), "state": "red"},
    {"name": "SW", "pos": (intersection.left - 35, intersection.bottom + 20), "state": "red"},
    {"name": "SE", "pos": (intersection.right + 35, intersection.bottom + 20), "state": "red"},
]
name_to_index = {pole["name"]: i for i, pole in enumerate(poles)}

# Map your 4 drawn poles to 4 approaches (clockwise)
# You can change this mapping later if you move pole positions.
approach_pole = {
    "N": name_to_index["NW"],
    "E": name_to_index["NE"],
    "S": name_to_index["SE"],
    "W": name_to_index["SW"],
}


def move_selection_wasd(curr_idx, key):
    if curr_idx is None:
        return curr_idx
    name = poles[curr_idx]["name"]
    
    if key == pygame.K_w:
        if name == "SE": return name_to_index["NE"]
        if name == "SW": return name_to_index["NW"]
        return curr_idx
    if key == pygame.K_s:  # go south
        if name == "NW": return name_to_index["SW"]
        if name == "NE": return name_to_index["SE"]
        return curr_idx  # already bottom row

    if key == pygame.K_a:  # go west
        if name == "NE": return name_to_index["NW"]
        if name == "SE": return name_to_index["SW"]
        return curr_idx  # already left column

    if key == pygame.K_d:  # go east
        if name == "NW": return name_to_index["NE"]
        if name == "SW": return name_to_index["SE"]
        return curr_idx  # already right column

    return curr_idx
    
    
    
def pole_hitbox(pole):
    x, y = pole["pos"]
    # clickable area around the traffic pole
    return pygame.Rect(x - 20, y - 20, 40, 110)

# Stop line positions (near the intersection edges)
stop_line_thickness = 8
stop_line_len = road_width - 40

stop_N = pygame.Rect(cx - stop_line_len // 2, intersection.top - 20, stop_line_len, stop_line_thickness)
stop_S = pygame.Rect(cx - stop_line_len // 2, intersection.bottom + 12, stop_line_len, stop_line_thickness)
stop_W = pygame.Rect(intersection.left - 20, cy - stop_line_len // 2, stop_line_thickness, stop_line_len)
stop_E = pygame.Rect(intersection.right + 12, cy - stop_line_len // 2, stop_line_thickness, stop_line_len)

# Crosswalks (simple zebra stripes)
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

# Traffic light drawing (placeholder circles)
def draw_light(x, y, state="red"):
    # pole + box
    pygame.draw.rect(screen, (40, 40, 40), (x - 12, y - 12, 24, 60), border_radius=6)
    pygame.draw.rect(screen, (35, 35, 35), (x - 3, y + 48, 6, 40))

    # lights
    
    off = (70, 70, 70)
    r = 7
    
    red_on = state in ("red", "red_yellow")
    yellow_on = state in ("yellow", "red_yellow")
    green_on = state == "green"

    # top/mid/bottom circles
    pygame.draw.circle(screen, RED if red_on else off, (x, y), r)
    pygame.draw.circle(screen, YELLOW if yellow_on else off, (x, y + 18), r)
    pygame.draw.circle(screen, GREEN if green_on else off, (x, y + 36), r)

# Center lane lines (optional)
def draw_lane_lines():
    # vertical lane divider
    pygame.draw.line(screen, LANE, (cx, 0), (cx, H), 2)
    # horizontal lane divider
    pygame.draw.line(screen, LANE, (0, cy), (W, cy), 2)
    
def draw_compass(top_right_x, top_right_y, radius=40):
    """
    Draws a simple compass at the top-right corner.
    (top_right_x, top_right_y) is the top-right anchor point.
    """
    # center of compass
    cx_c = top_right_x - radius - 10
    cy_c = top_right_y + radius + 10

    # circle
    pygame.draw.circle(screen, (200, 200, 200), (cx_c, cy_c), radius, 2)

    # cross lines
    pygame.draw.line(screen, (200, 200, 200), (cx_c, cy_c - radius + 6), (cx_c, cy_c + radius - 6), 2)
    pygame.draw.line(screen, (200, 200, 200), (cx_c - radius + 6, cy_c), (cx_c + radius - 6, cy_c), 2)

    # direction labels
    font_c = pygame.font.SysFont(None, 22)
    n = font_c.render("N", True, (230, 230, 230))
    s = font_c.render("S", True, (230, 230, 230))
    e = font_c.render("E", True, (230, 230, 230))
    w = font_c.render("W", True, (230, 230, 230))

    screen.blit(n, (cx_c - n.get_width() // 2, cy_c - radius - 18))
    screen.blit(s, (cx_c - s.get_width() // 2, cy_c + radius + 2))
    screen.blit(e, (cx_c + radius + 6, cy_c - e.get_height() // 2))
    screen.blit(w, (cx_c - radius - w.get_width() - 6, cy_c - w.get_height() // 2))


mode = {"autonomas": 0, "play": 1}
curr_mode = mode["autonomas"]

# ---------------- AUTONOMOUS CONTROLLER ----------------
auto_controller = AutonomousController(poles, approach_pole)


# --- Toggle button (top-left) ---
toggle_rect = pygame.Rect(20, 20, 170, 42)

def mode_name(curr_mode_value):
    # reverse lookup: 0 -> autonomas, 1 -> play
    for k, v in mode.items():
        if v == curr_mode_value:
            return k
    return "unknown"

def draw_toggle_button():
    # hover effect
    mx, my = pygame.mouse.get_pos()
    hover = toggle_rect.collidepoint(mx, my)

    bg = (70, 70, 70) if not hover else (95, 95, 95)
    border = (230, 230, 230)

    pygame.draw.rect(screen, bg, toggle_rect, border_radius=10)
    pygame.draw.rect(screen, border, toggle_rect, 2, border_radius=10)

    label = f"Mode: {mode_name(curr_mode)}"
    text_surf = ui_font.render(label, False, (240, 240, 240))
    screen.blit(
        text_surf,
        (toggle_rect.x + 12, toggle_rect.y + (toggle_rect.height - text_surf.get_height()) // 2)
    )



# --- Main loop ---
running = True




while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            exit()

        # Click to select a pole
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            selected_pole = None

            # toggle button click
            if toggle_rect.collidepoint(event.pos):
                curr_mode = mode["play"] if curr_mode == mode["autonomas"] else mode["autonomas"]

            # select poles only in play mode
            if curr_mode == mode["play"]:
                for i, pole in enumerate(poles):
                    if pole_hitbox(pole).collidepoint(mx, my):
                        selected_pole = i
                        break

        
        # if a traffic pole is selected, navigate others with wasd
      
                
        # SPACE changes only the selected pole
        if event.type == pygame.KEYDOWN and curr_mode == mode["play"]:
            if selected_pole is not None and event.key in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
                selected_pole = move_selection_wasd(selected_pole, event.key)

            if event.key == pygame.K_ESCAPE:
                selected_pole = None

            if event.key == pygame.K_SPACE and selected_pole is not None:
                cur = poles[selected_pole]["state"]
                nxt = light_states[(light_states.index(cur) + 1) % len(light_states)]
                poles[selected_pole]["state"] = nxt

            

    

    screen.fill(BG)
    
    draw_sidewalk()
    # draw toggle button
    draw_toggle_button()
    


    # draw compass
    draw_compass(W - 10, 10, radius=40)

    # Draw roads
    pygame.draw.rect(screen, ROAD, vertical_road)
    pygame.draw.rect(screen, ROAD, horizontal_road)

    # Draw intersection box (slightly darker)
    pygame.draw.rect(screen, (45, 45, 45), intersection)

    # Lane lines (optional helper)
    draw_lane_lines()

    # Stop lines
    pygame.draw.rect(screen, WHITE, stop_N)
    pygame.draw.rect(screen, WHITE, stop_S)
    pygame.draw.rect(screen, WHITE, stop_W)
    pygame.draw.rect(screen, WHITE, stop_E)

    # Crosswalks (one across NS road, one across EW road)
    # Across NS road => horizontal stripes above and below intersection
    draw_crosswalk_horizontal(intersection.top - 55, cx - road_width // 2 + 20, cx + road_width // 2 - 20)
    draw_crosswalk_horizontal(intersection.bottom + 25, cx - road_width // 2 + 20, cx + road_width // 2 - 20)

    # Across EW road => vertical stripes left and right of intersection
    draw_crosswalk_vertical(intersection.left - 55, cy - road_width // 2 + 20, cy + road_width // 2 - 20)
    draw_crosswalk_vertical(intersection.right + 25, cy - road_width // 2 + 20, cy + road_width // 2 - 20)

    # Traffic lights (4 corners near intersection)
    for i, pole in enumerate(poles):
        x, y = pole["pos"]
        draw_light(x,y, pole["state"])
        
        if selected_pole == i:
            pygame.draw.rect(screen, WHITE, pole_hitbox(pole), 2, border_radius=6)
       

    # # Small instruction text
    # font = pygame.font.SysFont(None, 28)
    # txt = font.render("Step 2: Intersection drawing only | Press SPACE to change light color", True, (220, 220, 220))
    # screen.blit(txt, (20, 20))

    pygame.display.flip()
    dt = clock.tick(60) / 1000.0
    # If autonomas mode: controller decides light states (no manual editing)
    if curr_mode == mode["autonomas"]:
        selected_pole = None  # disable manual selection in autonomous mode
        auto_controller.update(dt)
        auto_controller.apply_states()



pygame.quit()
