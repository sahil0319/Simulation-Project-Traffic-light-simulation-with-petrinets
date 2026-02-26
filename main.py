# main.py

import pygame
from sys import exit
from adaptive_controller import AdaptiveController
from vehicle import VehicleManager
from pedestrian import PedestrianManager, Pedestrian
from police import PoliceManager
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

# --- Geometry Info for Pedestrians and Police ---
geometry = {
    "cx": cx,
    "cy": cy,
    "road_width": road_width,
    "cross_size": cross_size,
    "screen_width": W,
    "screen_height": H
}

# --- Managers ---
vehicle_manager = VehicleManager(road_info)
pedestrian_manager = PedestrianManager(road_info, geometry)
police_manager = PoliceManager(road_info, geometry)
controller = AdaptiveController(poles, approach_map)
controller.apply_states()
metrics = Metrics()

# --- Modes ---
modes = [
    AutomaticMode(controller, vehicle_manager, pedestrian_manager),
    ManualSurvivalMode(controller, vehicle_manager, pedestrian_manager),
    ScenarioChallengeMode(controller, vehicle_manager, pedestrian_manager)
]
current_mode_idx = 0

# --- Selected Pole (Manual Only) ---
selected_pole = None

# --- Pedestrian Spawn Rate Slider ---
slider_x = 20
slider_y = H - 40
slider_w = 200
slider_h = 10
slider_min = 0    # 0 persons per minute
slider_max = 120  # 120 persons per minute
slider_dragging = False



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
    lbl = ui_font.render(f"Mode: {mode_name} (Press M to switch, V for VIP)", True, WHITE)
    screen.blit(lbl, (20, 20))
    
    if selected_pole is not None:
        p = poles[selected_pole]
        txt = ui_font.render(f"Selected: {p['name']} ({p['state']})", True, YELLOW)
        screen.blit(txt, (20, 50))
    
    # VIP indicator
    if police_manager.is_vip_active():
        vip_txt = ui_font.render("! VIP CONVOY PASSING !", True, (255, 215, 0))
        txt_rect = vip_txt.get_rect(center=(W // 2, 25))
        bg_rect = txt_rect.inflate(20, 10)
        pygame.draw.rect(screen, (50, 50, 50), bg_rect, border_radius=5)
        pygame.draw.rect(screen, (255, 215, 0), bg_rect, 2, border_radius=5)
        screen.blit(vip_txt, txt_rect)
    
    # Pedestrian count
    ped_waiting = pedestrian_manager.get_waiting_count()
    if ped_waiting > 0:
        ped_txt = ui_font.render(f"Pedestrians waiting: {ped_waiting}", True, (200, 200, 255))
        screen.blit(ped_txt, (W - 250, 20))
    
    # --- Pedestrian Spawn Rate Slider ---
    # Background track
    pygame.draw.rect(screen, (60, 60, 60), (slider_x, slider_y, slider_w, slider_h), border_radius=4)
    # Filled portion
    rate = pedestrian_manager.spawn_rate_ppm
    fill_frac = (rate - slider_min) / max(1, slider_max - slider_min)
    fill_w = int(fill_frac * slider_w)
    pygame.draw.rect(screen, (100, 200, 255), (slider_x, slider_y, fill_w, slider_h), border_radius=4)
    # Knob
    knob_x = slider_x + fill_w
    pygame.draw.circle(screen, (255, 255, 255), (knob_x, slider_y + slider_h // 2), 8)
    pygame.draw.circle(screen, (100, 200, 255), (knob_x, slider_y + slider_h // 2), 6)
    # Label
    rate_label = ui_font.render(f"Ped: {rate:.0f}/min", True, (200, 220, 255))
    screen.blit(rate_label, (slider_x + slider_w + 15, slider_y - 8))

def draw_wasd_indicator():
    """Draw WASD + SPACE key indicator in bottom-right corner, highlighting pressed keys."""
    keys = pygame.key.get_pressed()
    
    key_size = 36
    gap = 4
    margin = 60
    
    # Base position (bottom-left)
    base_x = margin
    base_y = H - margin - (2 * key_size + gap + key_size + gap)  # 2 rows of keys + spacebar
    
    # Colors
    dim_bg = (50, 50, 50)
    dim_border = (90, 90, 90)
    dim_text = (120, 120, 120)
    active_bg = (0, 180, 220)
    active_border = (0, 230, 255)
    active_text = (255, 255, 255)
    
    key_layout = [
        # (label, col, row, pygame_key, width)
        ("W", 1, 0, pygame.K_w, key_size),
        ("A", 0, 1, pygame.K_a, key_size),
        ("S", 1, 1, pygame.K_s, key_size),
        ("D", 2, 1, pygame.K_d, key_size),
    ]
    
    for label, col, row, pkey, w in key_layout:
        x = base_x + col * (key_size + gap)
        y = base_y + row * (key_size + gap)
        pressed = keys[pkey]
        
        bg = active_bg if pressed else dim_bg
        border = active_border if pressed else dim_border
        txt_col = active_text if pressed else dim_text
        
        rect = pygame.Rect(x, y, w, key_size)
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2, border_radius=6)
        
        txt = ui_font.render(label, True, txt_col)
        txt_rect = txt.get_rect(center=rect.center)
        screen.blit(txt, txt_rect)
    
    # Spacebar row below WASD
    space_y = base_y + 2 * (key_size + gap)
    space_w = 3 * key_size + 2 * gap
    space_pressed = keys[pygame.K_SPACE]
    
    bg = active_bg if space_pressed else dim_bg
    border = active_border if space_pressed else dim_border
    txt_col = active_text if space_pressed else dim_text
    
    space_rect = pygame.Rect(base_x, space_y, space_w, key_size)
    pygame.draw.rect(screen, bg, space_rect, border_radius=6)
    pygame.draw.rect(screen, border, space_rect, 2, border_radius=6)
    
    space_txt = ui_font.render("SPACE", True, txt_col)
    space_txt_rect = space_txt.get_rect(center=space_rect.center)
    screen.blit(space_txt, space_txt_rect)

# =========================
# 1) MENU UI HELPERS (PASTE ABOVE MAIN LOOP)
# =========================

class Button:
    def __init__(self, rect: pygame.Rect, text: str, font, on_click=None):
        self.rect = rect
        self.text = text
        self.font = font
        self.on_click = on_click
        self.hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        return False

    def draw(self, surf, *, fg=(230, 230, 230)):
        # Simple style (no extra deps)
        bg = (70, 70, 70) if not self.hover else (90, 90, 90)
        border = (160, 160, 160) if not self.hover else (220, 220, 220)
        pygame.draw.rect(surf, bg, self.rect, border_radius=10)
        pygame.draw.rect(surf, border, self.rect, 2, border_radius=10)

        txt = self.font.render(self.text, True, fg)
        txt_rect = txt.get_rect(center=self.rect.center)
        surf.blit(txt, txt_rect)


def draw_dim_overlay(surf, alpha=160):
    overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surf.blit(overlay, (0, 0))



# =========================
# 2) MENU STATE + BUTTONS (PASTE NEAR OTHER GLOBALS, BEFORE MAIN LOOP)
# =========================

GAME_MENU = "menu"
GAME_SETTINGS = "settings"
GAME_RUNNING = "running"

game_state = GAME_MENU

title_font = pygame.font.Font(FONT_PATH, 70)
menu_font = pygame.font.Font(FONT_PATH, 38)

# Background should always be Automatic mode while menu/settings is open
BACKGROUND_MODE_IDX = 0

def set_state(new_state):
    global game_state, current_mode_idx, selected_pole, metrics
    game_state = new_state

    # If they start the game, put them into normal running flow.
    # Keep current_mode_idx as-is if you want, but most games start in Automatic.
    if new_state == GAME_RUNNING:
        # Start game in the normal mode system (you can change this if you want)
        current_mode_idx = BACKGROUND_MODE_IDX
        selected_pole = None
        metrics = Metrics()

def on_start():
    set_state(GAME_RUNNING)

def on_settings():
    set_state(GAME_SETTINGS)

def on_quit():
    pygame.quit()
    exit()

def on_back_to_menu():
    set_state(GAME_MENU)

# Button layout
btn_w, btn_h = 260, 58
btn_x = W // 2 - btn_w // 2
btn_y0 = H // 2 - 40

btn_start = Button(pygame.Rect(btn_x, btn_y0 + 0*(btn_h+14), btn_w, btn_h), "START", menu_font, on_start)
btn_settings = Button(pygame.Rect(btn_x, btn_y0 + 1*(btn_h+14), btn_w, btn_h), "SETTINGS", menu_font, on_settings)
btn_quit = Button(pygame.Rect(btn_x, btn_y0 + 2*(btn_h+14), btn_w, btn_h), "QUIT", menu_font, on_quit)

btn_back = Button(pygame.Rect(20, 20, 160, 50), "BACK", menu_font, on_back_to_menu)

menu_buttons = [btn_start, btn_settings, btn_quit]

# --- Main Loop ---
running = True
while running:
    dt = clock.tick(60) / 1000.0

    # ---------------------------------
    # EVENT HANDLING (REPLACE YOURS)
    # ---------------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            exit()

        # ---------- MENU / SETTINGS input ----------
        if game_state in (GAME_MENU, GAME_SETTINGS):
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC in menu -> quit, ESC in settings -> back to menu
                    if game_state == GAME_MENU:
                        on_quit()
                    else:
                        on_back_to_menu()

                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    # Enter starts game from menu
                    if game_state == GAME_MENU:
                        on_start()

            # Buttons
            if game_state == GAME_MENU:
                for b in menu_buttons:
                    b.handle_event(event)

            if game_state == GAME_SETTINGS:
                btn_back.handle_event(event)

                # Allow slider changing only in Settings screen (same slider logic you already use)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    knob_cx = slider_x + int(((pedestrian_manager.spawn_rate_ppm - slider_min) / max(1, slider_max - slider_min)) * slider_w)
                    if abs(mx - knob_cx) < 15 and abs(my - (slider_y + slider_h // 2)) < 15:
                        slider_dragging = True

                if event.type == pygame.MOUSEBUTTONUP:
                    slider_dragging = False

                if event.type == pygame.MOUSEMOTION and slider_dragging:
                    mx = event.pos[0]
                    frac = max(0, min(1, (mx - slider_x) / slider_w))
                    pedestrian_manager.spawn_rate_ppm = slider_min + frac * (slider_max - slider_min)

            # IMPORTANT: while in menu/settings, DO NOT let gameplay inputs run
            continue

        # ---------- RUNNING (your original inputs, unchanged) ----------
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                current_mode_idx = (current_mode_idx + 1) % len(modes)
                metrics = Metrics()
                if isinstance(modes[current_mode_idx], ManualSurvivalMode):
                    selected_pole = 0
                else:
                    selected_pole = None

            if event.key == pygame.K_v:
                police_manager.spawn_vip_convoy()

            new_selection = modes[current_mode_idx].handle_input(event, selected_pole)
            if new_selection is not None:
                selected_pole = new_selection

            if event.key == pygame.K_ESCAPE:
                selected_pole = None

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            knob_cx = slider_x + int(((pedestrian_manager.spawn_rate_ppm - slider_min) / max(1, slider_max - slider_min)) * slider_w)
            if abs(mx - knob_cx) < 15 and abs(my - (slider_y + slider_h // 2)) < 15:
                slider_dragging = True
            else:
                for i, p in enumerate(poles):
                    rect = pygame.Rect(p["pos"][0]-20, p["pos"][1]-20, 40, 110)
                    if rect.collidepoint(mx, my):
                        selected_pole = i

        if event.type == pygame.MOUSEBUTTONUP:
            slider_dragging = False

        if event.type == pygame.MOUSEMOTION and slider_dragging:
            mx = event.pos[0]
            frac = max(0, min(1, (mx - slider_x) / slider_w))
            pedestrian_manager.spawn_rate_ppm = slider_min + frac * (slider_max - slider_min)

    # Update
      # Background simulation mode while menu/settings is open:
    if game_state in (GAME_MENU, GAME_SETTINGS):
        current_mode = modes[BACKGROUND_MODE_IDX]
    else:
        current_mode = modes[current_mode_idx]

    # Update police/VIP system first (same as your logic)
    police_manager.update(dt)

    blocked_dirs = police_manager.get_blocked_directions()
    spawn_blocked = police_manager.get_spawn_blocked_directions()
    vehicle_manager.set_blocked_directions(spawn_blocked if spawn_blocked else blocked_dirs)

    vehicle_manager.set_vip_info(police_manager.get_vip_info())
    vehicle_manager.set_blocker_rects(police_manager.get_blocker_rects())

    # Update mode (controller + vehicles) (same flow)
    current_mode.update(dt, police_manager)

    # Update pedestrians (same flow)
    light_states = current_mode.get_light_states()
    pedestrian_manager.update(dt, light_states, police_manager.is_vip_active(), vehicle_manager.vehicles)

    # Metrics only when actually playing (optional; doesn’t change simulation logic)
    if game_state == GAME_RUNNING:
        metrics.update(vehicle_manager)

    
    # Draw
    screen.fill(BG)
    draw_sidewalk()

    pygame.draw.rect(screen, ROAD, vertical_road)
    pygame.draw.rect(screen, ROAD, horizontal_road)
    pygame.draw.rect(screen, (45, 45, 45), intersection)

    def draw_double_yellow(start_pos, end_pos):
        if start_pos[0] == end_pos[0]:
            x = start_pos[0]
            pygame.draw.line(screen, YELLOW, (x - 3, start_pos[1]), (x - 3, end_pos[1]), 3)
            pygame.draw.line(screen, YELLOW, (x + 3, start_pos[1]), (x + 3, end_pos[1]), 3)
        else:
            y = start_pos[1]
            pygame.draw.line(screen, YELLOW, (start_pos[0], y - 3), (end_pos[0], y - 3), 3)
            pygame.draw.line(screen, YELLOW, (start_pos[0], y + 3), (end_pos[0], y + 3), 3)

    def draw_dashed_white(start_pos, end_pos):
        if start_pos[0] == end_pos[0]:
            x = start_pos[0]
            for y in range(int(start_pos[1]), int(end_pos[1]), 40):
                pygame.draw.line(screen, WHITE, (x, y), (x, min(y + 20, end_pos[1])), 2)
        else:
            y = start_pos[1]
            for x in range(int(start_pos[0]), int(end_pos[0]), 40):
                pygame.draw.line(screen, WHITE, (x, y), (min(x + 20, end_pos[0]), y), 2)

    draw_double_yellow((cx, 0), (cx, cy - cross_size//2))
    draw_double_yellow((cx, cy + cross_size//2), (cx, H))
    draw_double_yellow((0, cy), (cx - cross_size//2, cy))
    draw_double_yellow((cx + cross_size//2, cy), (W, cy))

    draw_dashed_white((cx - 55, 0), (cx - 55, cy - cross_size//2))
    draw_dashed_white((cx + 55, 0), (cx + 55, cy - cross_size//2))
    draw_dashed_white((cx - 55, cy + cross_size//2), (cx - 55, H))
    draw_dashed_white((cx + 55, cy + cross_size//2), (cx + 55, H))

    draw_dashed_white((0, cy - 55), (cx - cross_size//2, cy - 55))
    draw_dashed_white((0, cy + 55), (cx - cross_size//2, cy + 55))
    draw_dashed_white((cx + cross_size//2, cy - 55), (W, cy - 55))
    draw_dashed_white((cx + cross_size//2, cy + 55), (W, cy + 55))

    pygame.draw.line(screen, WHITE, (cx - 110, 0), (cx - 110, cy - cross_size//2), 3)
    pygame.draw.line(screen, WHITE, (cx + 110, 0), (cx + 110, cy - cross_size//2), 3)
    pygame.draw.line(screen, WHITE, (cx - 110, cy + cross_size//2), (cx - 110, H), 3)
    pygame.draw.line(screen, WHITE, (cx + 110, cy + cross_size//2), (cx + 110, H), 3)

    pygame.draw.line(screen, WHITE, (0, cy - 110), (cx - cross_size//2, cy - 110), 3)
    pygame.draw.line(screen, WHITE, (0, cy + 110), (cx - cross_size//2, cy + 110), 3)
    pygame.draw.line(screen, WHITE, (cx + cross_size//2, cy - 110), (W, cy - 110), 3)
    pygame.draw.line(screen, WHITE, (cx + cross_size//2, cy + 110), (W, cy + 110), 3)

    draw_crosswalk_horizontal(intersection.top - 55, cx - road_width // 2 + 20, cx + road_width // 2 - 20)
    draw_crosswalk_horizontal(intersection.bottom + 25, cx - road_width // 2 + 20, cx + road_width // 2 - 20)
    draw_crosswalk_vertical(intersection.left - 55, cy - road_width // 2 + 20, cy + road_width // 2 - 20)
    draw_crosswalk_vertical(intersection.right + 25, cy - road_width // 2 + 20, cy + road_width // 2 - 20)

    stop_len = road_width - 40
    pygame.draw.rect(screen, WHITE, pygame.Rect(cx - stop_len//2, stop_y_N, stop_len, 8))
    pygame.draw.rect(screen, WHITE, pygame.Rect(cx - stop_len//2, stop_y_S, stop_len, 8))
    pygame.draw.rect(screen, WHITE, pygame.Rect(stop_x_W, cy - stop_len//2, 8, stop_len))
    pygame.draw.rect(screen, WHITE, pygame.Rect(stop_x_E, cy - stop_len//2, 8, stop_len))

    pedestrian_manager.draw(screen)
    vehicle_manager.draw(screen)
    police_manager.draw(screen)

    for i, p in enumerate(poles):
        draw_light(p["pos"][0], p["pos"][1], p["state"])
        if game_state == GAME_RUNNING and selected_pole == i:
            pygame.draw.rect(screen, WHITE, (p["pos"][0]-20, p["pos"][1]-20, 40, 110), 2)

    # Normal UI only during gameplay
    if game_state == GAME_RUNNING:
        draw_ui()
        metrics.draw(screen, ui_font)
        if isinstance(modes[current_mode_idx], ManualSurvivalMode):
            draw_wasd_indicator()

    # -------- MENU OVERLAYS --------
    if game_state == GAME_MENU:
        draw_dim_overlay(screen, alpha=160)

        title = title_font.render("PETRI NET TRAFFIC", True, (240, 240, 240))
        sub = ui_font.render("Menu running on live Automatic simulation", True, (200, 200, 200))

        title_rect = title.get_rect(center=(W//2, H//2 - 170))
        sub_rect = sub.get_rect(center=(W//2, H//2 - 120))
        screen.blit(title, title_rect)
        screen.blit(sub, sub_rect)

        for b in menu_buttons:
            b.draw(screen)

        hint = ui_font.render("ENTER = Start   ESC = Quit", True, (180, 180, 180))
        screen.blit(hint, (W//2 - hint.get_width()//2, H - 60))

    elif game_state == GAME_SETTINGS:
        draw_dim_overlay(screen, alpha=160)

        title = title_font.render("SETTINGS", True, (240, 240, 240))
        title_rect = title.get_rect(center=(W//2, 120))
        screen.blit(title, title_rect)

        # Reuse your slider UI so settings are real (Ped spawn rate)
        # Just draw it here + a label
        info = ui_font.render("Adjust Pedestrian Spawn Rate:", True, (220, 220, 255))
        screen.blit(info, (slider_x, slider_y - 50))

        # Draw slider exactly like draw_ui does, but standalone
        pygame.draw.rect(screen, (60, 60, 60), (slider_x, slider_y, slider_w, slider_h), border_radius=4)
        rate = pedestrian_manager.spawn_rate_ppm
        fill_frac = (rate - slider_min) / max(1, slider_max - slider_min)
        fill_w = int(fill_frac * slider_w)
        pygame.draw.rect(screen, (100, 200, 255), (slider_x, slider_y, fill_w, slider_h), border_radius=4)
        knob_x = slider_x + fill_w
        pygame.draw.circle(screen, (255, 255, 255), (knob_x, slider_y + slider_h // 2), 8)
        pygame.draw.circle(screen, (100, 200, 255), (knob_x, slider_y + slider_h // 2), 6)
        rate_label = ui_font.render(f"Ped: {rate:.0f}/min", True, (200, 220, 255))
        screen.blit(rate_label, (slider_x + slider_w + 15, slider_y - 8))

        btn_back.draw(screen)
        hint = ui_font.render("ESC = Back to Menu", True, (180, 180, 180))
        screen.blit(hint, (20, 80))

    pygame.display.flip()

pygame.quit()
