# main.py

import pygame
from sys import exit
from adaptive_controller import AdaptiveController
from vehicle import VehicleManager
from pedestrian import PedestrianManager, Pedestrian
from police import PoliceManager
from accident import AccidentManager
from game_modes import AutomaticMode, ManualSurvivalMode, ScenarioChallengeMode
from metrics import Metrics
from stats_tracker import StatsTracker
from screens import MenuScreen, StatsScreen

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
start_N = (cx - road_width // 4, -60)
start_S = (cx + road_width // 4, H + 60)
start_E = (W + 60, cy - road_width // 4) 
start_W = (-60, cy + road_width // 4)

stop_y_N = intersection.top - 20
stop_y_S = intersection.bottom + 20
stop_x_W = intersection.left - 20
stop_x_E = intersection.right + 20

road_info = {
    "starts": {"N": start_N, "S": start_S, "E": start_E, "W": start_W},
    "stop_lines": {"N": stop_y_N, "S": stop_y_S, "E": stop_x_E, "W": stop_x_W}
}

# --- Traffic Poles ---
poles = [
    {"name": "NW", "pos": (intersection.left - 35, intersection.top - 80), "state": "red"},
    {"name": "NE", "pos": (intersection.right + 35, intersection.top - 80), "state": "red"},
    {"name": "SW", "pos": (intersection.left - 35, intersection.bottom + 20), "state": "red"},
    {"name": "SE", "pos": (intersection.right + 35, intersection.bottom + 20), "state": "red"},
]
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

# --- Screens ---
menu_screen = MenuScreen(W, H, FONT_PATH)
stats_screen = StatsScreen(W, H, FONT_PATH)
last_tracker = None  # Stats from last run

# --- State ---
STATE_MENU = "menu"
STATE_GAME = "game"
STATE_STATS = "stats"
app_state = STATE_MENU

# --- Game variables (initialized per-run) ---
vehicle_manager = None
pedestrian_manager = None
police_manager = None
accident_manager = None
controller = None
metrics = None
modes = None
current_mode_idx = 0
selected_pole = None
slider_dragging = False
tracker = None

# --- Pedestrian Spawn Rate Slider ---
slider_x = 20
slider_y = H - 40
slider_w = 200
slider_h = 10
slider_min = 0
slider_max = 120


def init_game():
    """Initialize all game objects for a new simulation run."""
    global vehicle_manager, pedestrian_manager, police_manager, accident_manager
    global controller, metrics, modes, current_mode_idx, selected_pole, slider_dragging
    global tracker

    tracker = StatsTracker()
    tracker.start()

    vehicle_manager = VehicleManager(road_info, stats_tracker=tracker)
    pedestrian_manager = PedestrianManager(road_info, geometry, stats_tracker=tracker)
    police_manager = PoliceManager(road_info, geometry, stats_tracker=tracker)
    accident_manager = AccidentManager(road_info, geometry, stats_tracker=tracker)
    controller = AdaptiveController(poles, approach_map)
    controller.apply_states()
    metrics = Metrics()

    modes = [
        AutomaticMode(controller, vehicle_manager, pedestrian_manager),
        ManualSurvivalMode(controller, vehicle_manager, pedestrian_manager),
        ScenarioChallengeMode(controller, vehicle_manager, pedestrian_manager)
    ]
    current_mode_idx = 0
    selected_pole = None
    slider_dragging = False


def end_game():
    """Save stats and return to menu."""
    global last_tracker, app_state
    if tracker:
        if 'vehicle_manager' in globals() and vehicle_manager:
            vehicle_manager.flush_wait_times()
        tracker.stop()
        tracker.game_mode = modes[current_mode_idx].name if modes else "N/A"
        tracker.max_queue_length = metrics.max_queue_length if metrics else 0
        tracker.pedestrian_spawn_rate = pedestrian_manager.spawn_rate_ppm if pedestrian_manager else 30
        last_tracker = tracker
        menu_screen.stats_enabled = True
    app_state = STATE_MENU


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

def draw_key_button(x, y, label, w=36, h=36, active=False):
    """Draw a single keyboard-style button."""
    bg = (80, 80, 80) if not active else (100, 200, 255)
    border = (140, 140, 140) if not active else (150, 230, 255)
    text_col = (220, 220, 220) if not active else (20, 20, 20)
    # Shadow
    pygame.draw.rect(screen, (30, 30, 30), (x + 2, y + 2, w, h), border_radius=5)
    # Body
    pygame.draw.rect(screen, bg, (x, y, w, h), border_radius=5)
    # Border
    pygame.draw.rect(screen, border, (x, y, w, h), 2, border_radius=5)
    # Label
    small_font = pygame.font.Font(FONT_PATH, 22)
    lbl_surf = small_font.render(label, True, text_col)
    lbl_rect = lbl_surf.get_rect(center=(x + w // 2, y + h // 2))
    screen.blit(lbl_surf, lbl_rect)


def draw_controls_overlay():
    """Draw WASD + Space overlay and Shift+</> hint in the bottom-right."""
    # --- Panel background ---
    panel_w, panel_h = 180, 140
    panel_x = W - panel_w - 15
    panel_y = H - panel_h - 45
    overlay_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    overlay_surf.fill((25, 25, 25, 180))
    screen.blit(overlay_surf, (panel_x, panel_y))
    pygame.draw.rect(screen, (100, 200, 255), (panel_x, panel_y, panel_w, panel_h), 1, border_radius=6)

    # Title
    tiny_font = pygame.font.Font(FONT_PATH, 18)
    title = tiny_font.render("Controls", True, (100, 200, 255))
    screen.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 4))

    # WASD layout
    key_size = 28
    gap = 3
    # Center the WASD cluster in the panel
    cluster_w = key_size * 3 + gap * 2
    bx = panel_x + (panel_w - cluster_w) // 2 - 30
    by = panel_y + 24

    # Which key corresponds to which pole movement is active
    draw_key_button(bx + key_size + gap, by, "W", key_size, key_size)  # W top-center
    draw_key_button(bx, by + key_size + gap, "A", key_size, key_size)  # A left
    draw_key_button(bx + key_size + gap, by + key_size + gap, "S", key_size, key_size)  # S center
    draw_key_button(bx + (key_size + gap) * 2, by + key_size + gap, "D", key_size, key_size)  # D right

    # Space bar
    space_w = key_size * 3 + gap * 2
    space_y = by + (key_size + gap) * 2
    draw_key_button(bx, space_y, "SPACE", space_w, key_size)

    # Labels on the right side of WASD cluster
    hint_font = pygame.font.Font(FONT_PATH, 16)
    hint_x = bx + cluster_w + 12
    nav_hint = hint_font.render("Select", True, (160, 160, 160))
    screen.blit(nav_hint, (hint_x, by + key_size // 2))
    space_hint = hint_font.render("Toggle", True, (160, 160, 160))
    screen.blit(space_hint, (hint_x, space_y + 4))

    # Shift + < / > hint for pedestrian rate
    rate_y = space_y + key_size + 8
    shift_hint = hint_font.render("Shift+</>  Ped Rate", True, (160, 160, 160))
    screen.blit(shift_hint, (panel_x + 10, rate_y))


def draw_ui():
    mode_name = modes[current_mode_idx].name
    lbl = ui_font.render(f"Mode: {mode_name} (M=switch, V=VIP, A=Accident)", True, WHITE)
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

    # --- Controls overlay (Manual Survival mode only) ---
    if modes[current_mode_idx].name == "Manual Survival":
        draw_controls_overlay()

    # ESC hint
    esc_txt = ui_font.render("[ESC] Back to Menu", True, (100, 100, 100))
    screen.blit(esc_txt, (W - 240, H - 30))


# --- Main Loop ---
running = True
while running:
    dt = clock.tick(60) / 1000.0
    
    # =========================================================
    #  MENU STATE
    # =========================================================
    if app_state == STATE_MENU:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                break
            result = menu_screen.handle_event(event)
            if result == "play":
                init_game()
                app_state = STATE_GAME
            elif result == "stats":
                stats_screen.scroll_y = 0
                app_state = STATE_STATS

        if app_state == STATE_MENU:
            menu_screen.draw(screen, dt)
            pygame.display.flip()

    # =========================================================
    #  STATS STATE
    # =========================================================
    elif app_state == STATE_STATS:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            result = stats_screen.handle_event(event)
            if result == "menu":
                app_state = STATE_MENU

        if app_state == STATE_STATS and last_tracker:
            stats_screen.draw(screen, last_tracker)
            pygame.display.flip()

    # =========================================================
    #  GAME STATE
    # =========================================================
    elif app_state == STATE_GAME:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                end_game()
                running = False
                break
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    end_game()
                    continue

                if event.key == pygame.K_m:
                    current_mode_idx = (current_mode_idx + 1) % len(modes)
                    metrics = Metrics()
                
                if event.key == pygame.K_v:
                    police_manager.spawn_vip_convoy()
                
                if event.key == pygame.K_a:
                    accident_manager.trigger_accident(vehicle_manager, pedestrian_manager)
                
                # Shift+> and Shift+< to adjust pedestrian spawn rate
                if event.key == pygame.K_PERIOD and (event.mod & pygame.KMOD_SHIFT):
                    new_rate = min(slider_max, pedestrian_manager.spawn_rate_ppm + 15)
                    pedestrian_manager.spawn_rate_ppm = new_rate
                    if tracker:
                        vehicle_manager.flush_wait_times()
                        tracker.record_ped_rate_change(new_rate)
                elif event.key == pygame.K_COMMA and (event.mod & pygame.KMOD_SHIFT):
                    new_rate = max(slider_min, pedestrian_manager.spawn_rate_ppm - 15)
                    pedestrian_manager.spawn_rate_ppm = new_rate
                    if tracker:
                        vehicle_manager.flush_wait_times()
                        tracker.record_ped_rate_change(new_rate)
                
                new_selection = modes[current_mode_idx].handle_input(event, selected_pole)
                if new_selection is not None:
                    selected_pole = new_selection

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
                if slider_dragging and tracker:
                    vehicle_manager.flush_wait_times()
                    tracker.record_ped_rate_change(pedestrian_manager.spawn_rate_ppm)
                slider_dragging = False
            
            if event.type == pygame.MOUSEMOTION and slider_dragging:
                mx = event.pos[0]
                frac = max(0, min(1, (mx - slider_x) / slider_w))
                raw_val = slider_min + frac * (slider_max - slider_min)
                # Snap to increments of 15
                snapped_val = round(raw_val / 15.0) * 15
                pedestrian_manager.spawn_rate_ppm = max(slider_min, min(slider_max, snapped_val))

        if app_state != STATE_GAME:
            continue

        # Update
        current_mode = modes[current_mode_idx]
        
        police_manager.update(dt)
        accident_manager.update(dt, vehicle_manager, pedestrian_manager)
        
        blocked_dirs = police_manager.get_blocked_directions()
        spawn_blocked = police_manager.get_spawn_blocked_directions()
        vehicle_manager.set_blocked_directions(spawn_blocked if spawn_blocked else blocked_dirs)
        
        vehicle_manager.set_vip_info(police_manager.get_vip_info())
        vehicle_manager.set_blocker_rects(police_manager.get_blocker_rects())
        vehicle_manager.set_accident_blockers(accident_manager.get_blocker_rects())
        
        current_mode.update(dt, police_manager, accident_manager)
        
        light_states = current_mode.get_light_states()
        pedestrian_manager.update(dt, light_states, police_manager.is_vip_active(), vehicle_manager.vehicles)
        
        metrics.update(vehicle_manager, accident_manager)
        
        # Draw
        screen.fill(BG)
        draw_sidewalk()
        
        pygame.draw.rect(screen, ROAD, vertical_road)
        pygame.draw.rect(screen, ROAD, horizontal_road)
        pygame.draw.rect(screen, (45, 45, 45), intersection)
        
        # --- Road Markings ---
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
        accident_manager.draw(screen)

        for i, p in enumerate(poles):
            draw_light(p["pos"][0], p["pos"][1], p["state"])
            if selected_pole == i:
                 pygame.draw.rect(screen, WHITE, (p["pos"][0]-20, p["pos"][1]-20, 40, 110), 2)

        draw_ui()
        metrics.draw(screen, ui_font)

        pygame.display.flip()

pygame.quit()
