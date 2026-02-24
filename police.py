# police.py

import pygame
import random
import math


class PoliceVehicle:
    """Police vehicle that can block roads and escort VIPs."""
    
    def __init__(self, x, y, approach, road_info, role="escort"):
        """
        role: "escort" (moves with VIP), "blocker" (stationary road block)
        """
        self.x = x
        self.y = y
        self.approach = approach
        self.road_info = road_info
        self.role = role
        
        self.width = 22
        self.length = 46
        self.max_speed = 200
        self.speed = 0
        
        # Visual
        self.base_color = (20, 40, 100)        # Dark navy blue
        self.highlight_color = (40, 70, 140)    # Lighter navy for panels
        self.stripe_color = (220, 220, 220)     # White stripe
        self.windshield_color = (60, 80, 120)   # Tinted glass
        self.wheel_color = (25, 25, 25)         # Black wheels
        self.bumper_color = (150, 150, 160)     # Chrome bumper
        
        # State
        self.active = True
        self.blocking = False
        
        self.rect = pygame.Rect(0, 0, self.width, self.length)
        self.update_rect()
        
        # Pre-render the police car surface (facing UP as canonical direction)
        self._render_surface()
    
    def _render_surface(self):
        """Pre-render a detailed police car facing UP."""
        w, h = self.width, self.length
        self.base_surface = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        s = self.base_surface
        ox, oy = 2, 2  # offset for anti-alias padding
        
        # --- Body ---
        body_rect = pygame.Rect(ox, oy, w, h)
        pygame.draw.rect(s, self.base_color, body_rect, border_radius=6)
        
        # --- Hood (front = top when facing up) ---
        hood_rect = pygame.Rect(ox + 2, oy + 1, w - 4, 10)
        pygame.draw.rect(s, self.highlight_color, hood_rect, border_radius=4)
        
        # --- Trunk (rear = bottom) ---
        trunk_rect = pygame.Rect(ox + 2, oy + h - 10, w - 4, 9)
        pygame.draw.rect(s, self.highlight_color, trunk_rect, border_radius=4)
        
        # --- Windshield (front) ---
        ws_rect = pygame.Rect(ox + 4, oy + 10, w - 8, 7)
        pygame.draw.rect(s, self.windshield_color, ws_rect, border_radius=2)
        
        # --- Rear window ---
        rw_rect = pygame.Rect(ox + 4, oy + h - 17, w - 8, 6)
        pygame.draw.rect(s, self.windshield_color, rw_rect, border_radius=2)
        
        # --- White side stripe (runs along the middle of the car) ---
        stripe_y = oy + h // 2 - 2
        pygame.draw.rect(s, self.stripe_color, pygame.Rect(ox + 1, stripe_y, w - 2, 4))
        
        # --- Door lines ---
        door_color = (15, 35, 85)
        # Left door
        pygame.draw.line(s, door_color, (ox + 1, oy + 18), (ox + 1, oy + h - 18), 1)
        # Right door
        pygame.draw.line(s, door_color, (ox + w - 2, oy + 18), (ox + w - 2, oy + h - 18), 1)
        
        # --- Wheels (4 dark rectangles at corners) ---
        ww, wh = 4, 7
        # Front-left
        pygame.draw.rect(s, self.wheel_color, pygame.Rect(ox - 1, oy + 5, ww, wh), border_radius=2)
        # Front-right
        pygame.draw.rect(s, self.wheel_color, pygame.Rect(ox + w - 3, oy + 5, ww, wh), border_radius=2)
        # Rear-left
        pygame.draw.rect(s, self.wheel_color, pygame.Rect(ox - 1, oy + h - 12, ww, wh), border_radius=2)
        # Rear-right
        pygame.draw.rect(s, self.wheel_color, pygame.Rect(ox + w - 3, oy + h - 12, ww, wh), border_radius=2)
        
        # --- Chrome bumpers ---
        pygame.draw.line(s, self.bumper_color, (ox + 3, oy + 1), (ox + w - 4, oy + 1), 2)
        pygame.draw.line(s, self.bumper_color, (ox + 3, oy + h - 1), (ox + w - 4, oy + h - 1), 2)
        
        # --- Light bar housing (white bar on roof, near front) ---
        lb_y = oy + 7
        lb_rect = pygame.Rect(ox + 3, lb_y, w - 6, 5)
        pygame.draw.rect(s, (200, 200, 210), lb_rect, border_radius=2)
        
        # Light bar circles will be drawn dynamically (flashing), store positions
        self._lb_left = (ox + 6, lb_y + 2)
        self._lb_right = (ox + w - 7, lb_y + 2)
    
    def update_rect(self):
        if self.approach in ["N", "S"]:
            self.rect.size = (self.width + 4, self.length + 4)
        else:
            self.rect.size = (self.length + 4, self.width + 4)
        self.rect.center = (self.x, self.y)
    
    def move_with_vip(self, vip_x, vip_y, offset_x, offset_y, dt):
        """Follow VIP with given offset using smooth lerp."""
        target_x = vip_x + offset_x
        target_y = vip_y + offset_y
        
        # Smooth follow with lerp
        lerp_speed = 6.0
        dx = target_x - self.x
        dy = target_y - self.y
        
        self.x += dx * lerp_speed * dt
        self.y += dy * lerp_speed * dt
        
        self.update_rect()
    
    def update(self, dt):
        # Blockers are stationary, just exist
        pass
    
    def draw(self, surface):
        # Determine rotation based on approach
        rotation = 0
        if self.approach == "N":    # Moving down -> face down
            rotation = 180
        elif self.approach == "S":  # Moving up -> face up (canonical)
            rotation = 0
        elif self.approach == "E":  # Moving left -> face left
            rotation = 90
        elif self.approach == "W":  # Moving right -> face right
            rotation = -90
        
        # Rotate the base surface
        rotated = pygame.transform.rotate(self.base_surface, rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)
        
        # --- Flashing light bar (drawn on top after blit) ---
        flash_phase = int(pygame.time.get_ticks() / 120) % 4
        
        if self.approach in ["N", "S"]:
            # Vertical orientation
            if self.approach == "N":
                # Front is bottom
                l1_pos = (int(self.x - 5), int(self.y + self.length // 2 - 12))
                l2_pos = (int(self.x + 5), int(self.y + self.length // 2 - 12))
            else:
                # Front is top
                l1_pos = (int(self.x - 5), int(self.y - self.length // 2 + 10))
                l2_pos = (int(self.x + 5), int(self.y - self.length // 2 + 10))
        else:
            # Horizontal orientation
            if self.approach == "E":
                # Front is left
                l1_pos = (int(self.x - self.length // 2 + 10), int(self.y - 5))
                l2_pos = (int(self.x - self.length // 2 + 10), int(self.y + 5))
            else:
                # Front is right
                l1_pos = (int(self.x + self.length // 2 - 12), int(self.y - 5))
                l2_pos = (int(self.x + self.length // 2 - 12), int(self.y + 5))
        
        # Alternating red/blue with glow effect
        if flash_phase < 2:
            c1 = (255, 30, 30) if flash_phase == 0 else (180, 0, 0)
            c2 = (0, 60, 160)
        else:
            c1 = (120, 0, 0)
            c2 = (30, 100, 255) if flash_phase == 2 else (0, 60, 200)
        
        # Glow
        glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*c1[:3], 60), (8, 8), 8)
        surface.blit(glow_surf, (l1_pos[0] - 8, l1_pos[1] - 8))
        glow_surf2 = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf2, (*c2[:3], 60), (8, 8), 8)
        surface.blit(glow_surf2, (l2_pos[0] - 8, l2_pos[1] - 8))
        
        # Solid light circles
        pygame.draw.circle(surface, c1, l1_pos, 4)
        pygame.draw.circle(surface, c2, l2_pos, 4)
        
        # "POLICE" text for blockers
        if self.role == "blocker":
            font = pygame.font.Font(None, 13)
            police_text = font.render("POLICE", True, (255, 255, 255))
            text_rect = police_text.get_rect(center=(int(self.x), int(self.y)))
            # Dark background behind text
            bg_rect = text_rect.inflate(4, 2)
            bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, 140))
            surface.blit(bg_surf, bg_rect)
            surface.blit(police_text, text_rect)


class VIPVehicle:
    """VIP limousine with waving flag on top."""
    
    def __init__(self, approach, road_info):
        self.approach = approach
        self.road_info = road_info
        
        self.width = 24
        self.length = 60  # Elongated limo
        self.max_speed = 150
        self.speed = self.max_speed
        
        # Position
        start_x, start_y = road_info["starts"][approach]
        self.x = start_x
        self.y = start_y
        
        # Visual
        self.body_color = (15, 15, 18)          # Glossy black
        self.trim_color = (190, 160, 50)        # Gold trim
        self.chrome_color = (170, 170, 180)     # Chrome accents
        self.window_color = (25, 30, 40)        # Very dark tinted windows
        self.wheel_color = (20, 20, 20)         # Black wheels
        self.flag_wave = 0
        
        # State
        self.active = True
        self.passed_intersection = False
        
        self.rect = pygame.Rect(0, 0, self.width, self.length)
        self.update_rect()
        
        # Pre-render the limo surface (facing UP)
        self._render_surface()
    
    def _render_surface(self):
        """Pre-render a detailed VIP limo facing UP."""
        w, h = self.width, self.length
        self.base_surface = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
        s = self.base_surface
        ox, oy = 3, 3
        
        # --- Main body ---
        body_rect = pygame.Rect(ox, oy, w, h)
        pygame.draw.rect(s, self.body_color, body_rect, border_radius=7)
        
        # --- Gold pinstripe border ---
        pygame.draw.rect(s, self.trim_color, body_rect, 2, border_radius=7)
        
        # --- Inner body highlight (subtle gloss) ---
        gloss_rect = pygame.Rect(ox + 3, oy + 2, w - 6, h - 4)
        gloss_surf = pygame.Surface(gloss_rect.size, pygame.SRCALPHA)
        gloss_surf.fill((255, 255, 255, 12))
        s.blit(gloss_surf, gloss_rect)
        
        # --- Hood (front) ---
        hood_rect = pygame.Rect(ox + 2, oy + 1, w - 4, 12)
        pygame.draw.rect(s, (25, 25, 30), hood_rect, border_radius=5)
        # Hood ornament line
        pygame.draw.line(s, self.trim_color, (ox + w // 2, oy + 2), (ox + w // 2, oy + 10), 1)
        
        # --- Trunk (rear) ---
        trunk_rect = pygame.Rect(ox + 2, oy + h - 12, w - 4, 11)
        pygame.draw.rect(s, (25, 25, 30), trunk_rect, border_radius=5)
        
        # --- Front windshield ---
        ws_rect = pygame.Rect(ox + 4, oy + 12, w - 8, 7)
        pygame.draw.rect(s, self.window_color, ws_rect, border_radius=2)
        pygame.draw.rect(s, (60, 60, 70), ws_rect, 1, border_radius=2)  # window frame
        
        # --- Three window sections (limo style) ---
        win_start_y = oy + 20
        win_h = 7
        win_gap = 3
        for i in range(3):
            wy = win_start_y + i * (win_h + win_gap)
            win_rect = pygame.Rect(ox + 3, wy, w - 6, win_h)
            pygame.draw.rect(s, self.window_color, win_rect, border_radius=2)
            pygame.draw.rect(s, (50, 50, 60), win_rect, 1, border_radius=2)
        
        # --- Rear window ---
        rw_rect = pygame.Rect(ox + 4, oy + h - 18, w - 8, 6)
        pygame.draw.rect(s, self.window_color, rw_rect, border_radius=2)
        pygame.draw.rect(s, (60, 60, 70), rw_rect, 1, border_radius=2)
        
        # --- Chrome bumper accents ---
        pygame.draw.line(s, self.chrome_color, (ox + 4, oy + 1), (ox + w - 5, oy + 1), 2)
        pygame.draw.line(s, self.chrome_color, (ox + 4, oy + h - 1), (ox + w - 5, oy + h - 1), 2)
        
        # --- Chrome side trim lines ---
        pygame.draw.line(s, (100, 100, 110), (ox + 1, oy + 15), (ox + 1, oy + h - 15), 1)
        pygame.draw.line(s, (100, 100, 110), (ox + w - 2, oy + 15), (ox + w - 2, oy + h - 15), 1)
        
        # --- Wheels (4 dark rounded rects at corners) ---
        ww, wh = 4, 8
        # Front-left
        pygame.draw.rect(s, self.wheel_color, pygame.Rect(ox - 1, oy + 6, ww, wh), border_radius=2)
        # Front-right
        pygame.draw.rect(s, self.wheel_color, pygame.Rect(ox + w - 3, oy + 6, ww, wh), border_radius=2)
        # Rear-left
        pygame.draw.rect(s, self.wheel_color, pygame.Rect(ox - 1, oy + h - 14, ww, wh), border_radius=2)
        # Rear-right
        pygame.draw.rect(s, self.wheel_color, pygame.Rect(ox + w - 3, oy + h - 14, ww, wh), border_radius=2)
        
        # --- Headlights (small yellow dots at front) ---
        pygame.draw.circle(s, (255, 240, 150), (ox + 5, oy + 3), 2)
        pygame.draw.circle(s, (255, 240, 150), (ox + w - 6, oy + 3), 2)
        
        # --- Taillights (small red dots at rear) ---
        pygame.draw.circle(s, (200, 30, 30), (ox + 5, oy + h - 3), 2)
        pygame.draw.circle(s, (200, 30, 30), (ox + w - 6, oy + h - 3), 2)
    
    def update_rect(self):
        if self.approach in ["N", "S"]:
            self.rect.size = (self.width + 6, self.length + 6)
        else:
            self.rect.size = (self.length + 6, self.width + 6)
        self.rect.center = (self.x, self.y)
    
    def move(self, dt):
        """Move VIP vehicle - always moving, ignores lights."""
        self.flag_wave += dt * 8  # Animate flag
        
        move_dist = self.speed * dt
        
        if self.approach == "N":
            self.y += move_dist
        elif self.approach == "S":
            self.y -= move_dist
        elif self.approach == "E":
            self.x -= move_dist
        elif self.approach == "W":
            self.x += move_dist
        
        self.update_rect()
        
        # Check if passed through and exited
        if self.approach == "N" and self.y > 800:
            self.active = False
        elif self.approach == "S" and self.y < -100:
            self.active = False
        elif self.approach == "E" and self.x < -100:
            self.active = False
        elif self.approach == "W" and self.x > 1100:
            self.active = False
    
    def draw(self, surface):
        # Determine rotation
        rotation = 0
        if self.approach == "N":
            rotation = 180
        elif self.approach == "S":
            rotation = 0
        elif self.approach == "E":
            rotation = 90
        elif self.approach == "W":
            rotation = -90
        
        # Rotate and blit the pre-rendered limo
        rotated = pygame.transform.rotate(self.base_surface, rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)
        
        # --- Waving flag on hood ---
        self._draw_flag(surface)
        
        # --- Gold "VIP" badge ---
        self._draw_vip_badge(surface)
    
    def _draw_flag(self, surface):
        """Draw animated waving flag on top of car."""
        # Flag pole position (front of car)
        if self.approach == "N":
            pole_x = self.x
            pole_y = self.y + self.length // 2 - 8
            flag_dir = 1  # flag extends right
        elif self.approach == "S":
            pole_x = self.x
            pole_y = self.y - self.length // 2 + 8
            flag_dir = 1
        elif self.approach == "E":
            pole_x = self.x - self.length // 2 + 8
            pole_y = self.y
            flag_dir = 1
        else:  # W
            pole_x = self.x + self.length // 2 - 8
            pole_y = self.y
            flag_dir = -1
        
        # Flag pole (going upward from car)
        pole_height = 22
        pole_top_x = pole_x
        pole_top_y = pole_y - pole_height
        pygame.draw.line(surface, (120, 100, 50), 
                        (int(pole_x), int(pole_y)), 
                        (int(pole_top_x), int(pole_top_y)), 2)
        
        # Waving flag with sine wave
        flag_width = 18
        flag_height = 10
        wave_amp = 2.5
        
        # Build flag polygon
        top_points = []
        bottom_points = []
        num_segments = 6
        for i in range(num_segments + 1):
            t = i / num_segments
            wave = math.sin(self.flag_wave + t * math.pi * 2.5) * wave_amp * t
            fx = pole_top_x + t * flag_width * flag_dir
            top_points.append((fx + wave, pole_top_y + 1))
            bottom_points.append((fx + wave, pole_top_y + 1 + flag_height))
        
        flag_points = top_points + list(reversed(bottom_points))
        
        if len(flag_points) >= 3:
            # Green flag with red circle (Bangladesh flag style)
            pygame.draw.polygon(surface, (0, 106, 78), 
                              [(int(p[0]), int(p[1])) for p in flag_points])
            
            # Red circle in center
            center_fx = pole_top_x + flag_width * flag_dir * 0.45
            center_fy = pole_top_y + 1 + flag_height // 2
            pygame.draw.circle(surface, (244, 42, 65), 
                             (int(center_fx), int(center_fy)), 3)
    
    def _draw_vip_badge(self, surface):
        """Draw a small gold VIP indicator near the car."""
        font = pygame.font.Font(None, 14)
        vip_text = font.render("VIP", True, (255, 215, 0))
        
        # Position badge above the car
        if self.approach in ["N", "S"]:
            tx = self.x - 8
            ty = self.y - self.length // 2 - 16
        else:
            tx = self.x - self.length // 2 - 5
            ty = self.y - 16
        
        text_rect = vip_text.get_rect(topleft=(int(tx), int(ty)))
        
        # Small dark background
        bg_rect = text_rect.inflate(6, 4)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (20, 20, 20, 180), bg_surf.get_rect(), border_radius=3)
        pygame.draw.rect(bg_surf, (190, 160, 50, 200), bg_surf.get_rect(), 1, border_radius=3)
        surface.blit(bg_surf, bg_rect)
        surface.blit(vip_text, text_rect)


class VIPConvoy:
    """Manages VIP vehicle with police escort.
    Phase 1: Blockers drive in from screen edges to block perpendicular roads.
    Phase 2: After blockers are in position, VIP + escorts appear and drive through.
    """
    
    def __init__(self, approach, road_info, geometry):
        self.approach = approach
        self.road_info = road_info
        self.geometry = geometry
        
        # Phase management
        self.phase = 1  # 1 = blockers deploying, 2 = VIP moving
        self.phase_timer = 0
        self.blocker_deploy_time = 3.0  # Seconds before VIP appears
        
        # VIP and escorts created later in phase 2
        self.vip = None
        self.escorts = []
        self.blockers = []
        
        self.active = True
        
        # Create blockers that drive in from screen edges
        self._create_blockers_from_edges()
    
    def _create_escorts(self):
        """Create police escorts around VIP."""
        front = PoliceVehicle(self.vip.x, self.vip.y, self.approach, self.road_info, "escort")
        rear = PoliceVehicle(self.vip.x, self.vip.y, self.approach, self.road_info, "escort")
        self.escorts = [front, rear]
    
    def _create_blockers_from_edges(self):
        """Create police blockers that spawn at screen edges and drive to blocking positions."""
        cx = self.geometry["cx"]
        cy = self.geometry["cy"]
        road_w = self.geometry["road_width"]
        cross_s = self.geometry["cross_size"]
        screen_w = self.geometry.get("screen_width", 1000)
        screen_h = self.geometry.get("screen_height", 700)
        
        if self.approach in ["N", "S"]:
            # Convoy is vertical. Block E and W approaches.
            # Use the ambulance (outer) lane for each approach direction
            # W ambulance lane: cy + road_w/4 + 35
            # E ambulance lane: cy - road_w/4 - 35
            
            b1_start_x = -60
            b1_target_x = cx - cross_s // 2 - 60
            b1_y = cy + road_w // 4 + 35  # W ambulance lane (bottom/outer)
            blocker_w = PoliceVehicle(
                b1_start_x, b1_y,
                "W", self.road_info, "blocker"
            )
            blocker_w._target_x = b1_target_x
            blocker_w._target_y = b1_y
            blocker_w._deploying = True
            blocker_w.speed = 200
            
            b2_start_x = screen_w + 60
            b2_target_x = cx + cross_s // 2 + 60
            b2_y = cy - road_w // 4 - 35  # E ambulance lane (top/outer)
            blocker_e = PoliceVehicle(
                b2_start_x, b2_y,
                "E", self.road_info, "blocker"
            )
            blocker_e._target_x = b2_target_x
            blocker_e._target_y = b2_y
            blocker_e._deploying = True
            blocker_e.speed = 200
            
            self.blockers = [blocker_w, blocker_e]
        else:
            # Convoy is horizontal. Block N and S approaches.
            # N ambulance lane: cx - road_w/4 - 35
            # S ambulance lane: cx + road_w/4 + 35
            
            b1_start_y = -60
            b1_target_y = cy - cross_s // 2 - 60
            b1_x = cx - road_w // 4 - 35  # N ambulance lane (left/outer)
            blocker_n = PoliceVehicle(
                b1_x, b1_start_y,
                "N", self.road_info, "blocker"
            )
            blocker_n._target_x = b1_x
            blocker_n._target_y = b1_target_y
            blocker_n._deploying = True
            blocker_n.speed = 200
            
            b2_start_y = screen_h + 60
            b2_target_y = cy + cross_s // 2 + 60
            b2_x = cx + road_w // 4 + 35  # S ambulance lane (right/outer)
            blocker_s = PoliceVehicle(
                b2_x, b2_start_y,
                "S", self.road_info, "blocker"
            )
            blocker_s._target_x = b2_x
            blocker_s._target_y = b2_target_y
            blocker_s._deploying = True
            blocker_s.speed = 200
            
            self.blockers = [blocker_n, blocker_s]
    
    def _blockers_in_position(self):
        """Check if all blockers have reached their target positions."""
        for b in self.blockers:
            if getattr(b, '_deploying', False):
                dx = b._target_x - b.x
                dy = b._target_y - b.y
                if (dx * dx + dy * dy) > 100:  # > 10px away
                    return False
        return True
    
    def _compute_turn_path(self, blocker, idx):
        """Compute waypoints for a blocker to drive into the intersection and turn
        to follow the convoy direction. Returns list of (x, y, approach_at_waypoint).
        The approach is set to the NEXT movement direction so the car visually
        rotates before driving forward."""
        cx = self.geometry["cx"]
        cy = self.geometry["cy"]
        road_w = self.geometry["road_width"]
        
        # Offset each blocker into a different sub-lane so they don't overlap
        # Sub-lane offset: ~20px apart, centered on the VIP's lane
        lane_spread = 20
        sub_offset = -lane_spread // 2 + idx * lane_spread  # idx 0 → -10, idx 1 → +10
        
        if self.approach == "N":  # VIP going down
            target_x = cx - road_w // 4 + sub_offset
            # wp1: drive forward to the turn point, then ROTATE to face down
            wp1 = (target_x, blocker.y, "N")
            # wp2: drive downward a good distance to catch up
            wp2 = (target_x, blocker.y + 250, "N")
            return [wp1, wp2]
        
        elif self.approach == "S":  # VIP going up
            target_x = cx + road_w // 4 + sub_offset
            wp1 = (target_x, blocker.y, "S")
            wp2 = (target_x, blocker.y - 250, "S")
            return [wp1, wp2]
        
        elif self.approach == "E":  # VIP going left
            target_y = cy - road_w // 4 + sub_offset
            wp1 = (blocker.x, target_y, "E")
            wp2 = (blocker.x - 250, target_y, "E")
            return [wp1, wp2]
        
        elif self.approach == "W":  # VIP going right
            target_y = cy + road_w // 4 + sub_offset
            wp1 = (blocker.x, target_y, "W")
            wp2 = (blocker.x + 250, target_y, "W")
            return [wp1, wp2]
        
        return []
    
    def get_escort_offsets(self):
        """Get position offsets for front and rear escorts based on approach."""
        front_offset = (0, 0)
        rear_offset = (0, 0)
        spacing = 80
        
        if self.approach == "N":
            front_offset = (0, -spacing)
            rear_offset = (0, spacing)
        elif self.approach == "S":
            front_offset = (0, spacing)
            rear_offset = (0, -spacing)
        elif self.approach == "E":
            front_offset = (spacing, 0)
            rear_offset = (-spacing, 0)
        elif self.approach == "W":
            front_offset = (-spacing, 0)
            rear_offset = (spacing, 0)
        
        return front_offset, rear_offset
    
    def update(self, dt):
        if not self.active:
            return
        
        if self.phase == 1:
            # Phase 1: Drive blockers to their positions
            self.phase_timer += dt
            
            for b in self.blockers:
                if getattr(b, '_deploying', False):
                    dx = b._target_x - b.x
                    dy = b._target_y - b.y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist > 5:
                        nx = dx / dist
                        ny = dy / dist
                        b.x += nx * b.speed * dt
                        b.y += ny * b.speed * dt
                        b.update_rect()
                    else:
                        b.x = b._target_x
                        b.y = b._target_y
                        b._deploying = False
                        b.update_rect()
            
            # Transition to phase 2 when blockers are in place or timer expires
            if self._blockers_in_position() or self.phase_timer >= self.blocker_deploy_time:
                self.phase = 2
                # Now spawn VIP and escorts
                self.vip = VIPVehicle(self.approach, self.road_info)
                self._create_escorts()
        
        elif self.phase == 2:
            # Phase 2: VIP is moving through
            self.vip.move(dt)
            
            front_offset, rear_offset = self.get_escort_offsets()
            if len(self.escorts) >= 2:
                self.escorts[0].move_with_vip(self.vip.x, self.vip.y,
                                              front_offset[0], front_offset[1], dt)
                self.escorts[1].move_with_vip(self.vip.x, self.vip.y,
                                              rear_offset[0], rear_offset[1], dt)
            
            if not self.vip.active:
                self.active = False
                
            # Check if VIP has passed the center to trigger phase 3
            cx, cy = self.geometry["cx"], self.geometry["cy"]
            vip_passed_center = False
            if self.approach == "N" and self.vip.y > cy + 40:
                vip_passed_center = True
            elif self.approach == "S" and self.vip.y < cy - 40:
                vip_passed_center = True
            elif self.approach == "E" and self.vip.x < cx - 40:
                vip_passed_center = True
            elif self.approach == "W" and self.vip.x > cx + 40:
                vip_passed_center = True
                
            if vip_passed_center:
                self.phase = 3
                for i, b in enumerate(self.blockers):
                    b.role = "escort"
                    b.blocking = False
                    b.speed = 150  # Match VIP speed from the start
                    b._turn_waypoints = self._compute_turn_path(b, i)
                    b._turn_wp_idx = 0
                    b._done_turning = False
        
        elif self.phase == 3:
            # Phase 3: Blockers turn through intersection then drive straight out
            self.vip.move(dt)
            
            front_offset, rear_offset = self.get_escort_offsets()
            if len(self.escorts) >= 2:
                self.escorts[0].move_with_vip(self.vip.x, self.vip.y,
                                              front_offset[0], front_offset[1], dt)
                self.escorts[1].move_with_vip(self.vip.x, self.vip.y,
                                              rear_offset[0], rear_offset[1], dt)
            
            for b in self.blockers:
                if not b._done_turning:
                    # Follow turn waypoints sequentially
                    if b._turn_wp_idx < len(b._turn_waypoints):
                        wp_x, wp_y, wp_approach = b._turn_waypoints[b._turn_wp_idx]
                        dx = wp_x - b.x
                        dy = wp_y - b.y
                        dist = math.sqrt(dx * dx + dy * dy)
                        if dist < 10:
                            # Reached this waypoint — update facing direction
                            b.approach = wp_approach
                            b.update_rect()
                            b._turn_wp_idx += 1
                        else:
                            nx = dx / dist
                            ny = dy / dist
                            b.x += nx * b.speed * dt
                            b.y += ny * b.speed * dt
                            b.update_rect()
                    else:
                        b._done_turning = True
                        b.approach = self.approach
                        b.speed = 150  # Match VIP speed so they don't collide
                        b.update_rect()
                else:
                    # Done turning — just drive straight at VIP speed
                    if self.approach == "N":   b.y += b.speed * dt
                    elif self.approach == "S": b.y -= b.speed * dt
                    elif self.approach == "E": b.x -= b.speed * dt
                    elif self.approach == "W": b.x += b.speed * dt
                    b.update_rect()
            
            if not self.vip.active:
                self.active = False
        
        # Update blockers if not in phase 3 (phase 3 updates them manually)
        if self.phase != 3:
            for blocker in self.blockers:
                blocker.update(dt)
    
    def get_blocker_rects(self):
        """Return rects of stationary blockers so vehicles can stop for them."""
        rects = []
        for b in self.blockers:
            if b.role == "blocker" and not getattr(b, '_deploying', False):
                rects.append(b.rect)
        return rects
    
    def draw(self, surface):
        # Draw blockers first
        for blocker in self.blockers:
            blocker.draw(surface)

        # Draw VIP + escorts in phases where they exist (phase 2 and 3)
        if self.vip:
            for escort in self.escorts:
                escort.draw(surface)
            # Draw VIP on top
            self.vip.draw(surface)

    
    def get_blocked_directions(self):
        """Return list of directions that should have RED lights (perpendicular to VIP)."""
        if self.approach in ["N", "S"]:
            return ["E", "W"]
        else:
            return ["N", "S"]
    
    def get_all_blocked_spawn_directions(self):
        """Return ALL directions — no cars should spawn anywhere during VIP."""
        return ["N", "S", "E", "W"]
    
    def get_vip_info(self):
        """Return VIP position and approach for lane clearing."""
        if self.vip:
            return {
                "x": self.vip.x,
                "y": self.vip.y,
                "approach": self.approach,
                "active": self.active
            }
        return {"x": 0, "y": 0, "approach": self.approach, "active": self.active}
    
    def get_arrow_info(self):
        """Return info for flashing directional arrow."""
        # Arrow shows which direction the convoy is coming FROM and going TO
        direction_map = {
            "N": {"from": "top", "to": "bottom"},
            "S": {"from": "bottom", "to": "top"},
            "E": {"from": "right", "to": "left"},
            "W": {"from": "left", "to": "right"},
        }
        return direction_map.get(self.approach, {"from": "top", "to": "bottom"})


class PoliceManager:
    """Manages all police vehicles and VIP convoys."""
    
    def __init__(self, road_info, geometry):
        self.road_info = road_info
        self.geometry = geometry
        self.convoys = []
        self.vip_spawn_timer = random.expovariate(1.0 / 45.0)  # Average 45s between spawns
        self.vip_active = False
        
    def set_geometry(self, cx, cy, road_width, cross_size, screen_width=1000, screen_height=700):
        self.geometry = {
            "cx": cx,
            "cy": cy,
            "road_width": road_width,
            "cross_size": cross_size,
            "screen_width": screen_width,
            "screen_height": screen_height
        }
    
    def spawn_vip_convoy(self, approach=None):
        """Spawn a VIP convoy from given or random direction."""
        if self.vip_active:
            return  # Only one VIP at a time
        
        if approach is None:
            approach = random.choice(["N", "S", "E", "W"])
        
        convoy = VIPConvoy(approach, self.road_info, self.geometry)
        self.convoys.append(convoy)
        self.vip_active = True
    
    def update(self, dt):
        # Timer for random VIP spawns
        self.vip_spawn_timer -= dt
        if self.vip_spawn_timer <= 0 and not self.vip_active:
            self.spawn_vip_convoy()
            self.vip_spawn_timer = random.expovariate(1.0 / 45.0)  # Next VIP in ~45s average
        
        # Update convoys
        for convoy in self.convoys:
            convoy.update(dt)
        
        # Remove inactive convoys
        active_convoys = [c for c in self.convoys if c.active]
        if len(active_convoys) < len(self.convoys):
            self.vip_active = False
        self.convoys = active_convoys
    
    def draw(self, surface):
        for convoy in self.convoys:
            convoy.draw(surface)
        
        # Draw flashing directional arrows for active VIP convoys
        if self.vip_active and self.convoys:
            self._draw_vip_arrow(surface, self.convoys[0])
    
    def _draw_vip_arrow(self, surface, convoy):
        """Draw a flashing arrow at intersection center pointing in convoy travel direction."""
        approach = convoy.approach
        
        # Flash at ~3Hz
        flash = (pygame.time.get_ticks() // 160) % 2 == 0
        if not flash:
            return
        
        cx = self.geometry["cx"]
        cy = self.geometry["cy"]
        
        arrow_color = (255, 200, 0)  # Bright yellow
        glow_color = (255, 200, 0, 80)
        
        # Arrow centered at intersection, pointing in TRAVEL direction
        ax, ay = cx, cy
        s = 35  # arrow size
        hw = 22  # arrowhead half-width
        bw = 10  # body half-width
        
        if approach == "N":  # Traveling downward
            points = [
                (ax, ay + s),           # tip (bottom)
                (ax - hw, ay + s - 20), # left wing
                (ax - bw, ay + s - 20), # left neck
                (ax - bw, ay - s),      # top-left
                (ax + bw, ay - s),      # top-right
                (ax + bw, ay + s - 20), # right neck
                (ax + hw, ay + s - 20), # right wing
            ]
        elif approach == "S":  # Traveling upward
            points = [
                (ax, ay - s),
                (ax - hw, ay - s + 20),
                (ax - bw, ay - s + 20),
                (ax - bw, ay + s),
                (ax + bw, ay + s),
                (ax + bw, ay - s + 20),
                (ax + hw, ay - s + 20),
            ]
        elif approach == "E":  # Traveling leftward
            points = [
                (ax - s, ay),
                (ax - s + 20, ay - hw),
                (ax - s + 20, ay - bw),
                (ax + s, ay - bw),
                (ax + s, ay + bw),
                (ax - s + 20, ay + bw),
                (ax - s + 20, ay + hw),
            ]
        elif approach == "W":  # Traveling rightward
            points = [
                (ax + s, ay),
                (ax + s - 20, ay - hw),
                (ax + s - 20, ay - bw),
                (ax - s, ay - bw),
                (ax - s, ay + bw),
                (ax + s - 20, ay + bw),
                (ax + s - 20, ay + hw),
            ]
        else:
            return
        
        # Glow effect
        glow_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, glow_color, (50, 50), 45)
        surface.blit(glow_surf, (ax - 50, ay - 50))
        
        # Arrow polygon
        pygame.draw.polygon(surface, arrow_color, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        
        # Label above or below the arrow
        font = pygame.font.Font(None, 20)
        label = font.render("VIP CONVOY", True, (255, 255, 0))
        if approach in ["N", "W"]:
            label_rect = label.get_rect(center=(ax, ay - s - 18))
        else:
            label_rect = label.get_rect(center=(ax, ay + s + 18))
        bg_rect = label_rect.inflate(8, 4)
        bg = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        surface.blit(bg, bg_rect)
        surface.blit(label, label_rect)
    
    def is_vip_active(self):
        return self.vip_active
    
    def get_blocked_directions(self):
        """Get directions that should have RED lights (perpendicular to VIP)."""
        blocked = set()
        for convoy in self.convoys:
            blocked.update(convoy.get_blocked_directions())
        return list(blocked)
    
    def get_spawn_blocked_directions(self):
        """Get ALL directions blocked for spawning during VIP passage.
        This blocks ALL traffic including ambulances."""
        if self.vip_active:
            return ["N", "S", "E", "W"]
        return []
    
    def get_vip_info(self):
        """Get VIP position info for lane clearing."""
        if self.convoys:
            return self.convoys[0].get_vip_info()
        return None
    
    def get_vip_direction(self):
        """Get the direction the VIP is traveling (for traffic preemption)."""
        if self.convoys:
            return self.convoys[0].approach
        return None
    
    def get_blocker_rects(self):
        """Return all stationary blocker rects for vehicle collision avoidance."""
        rects = []
        for convoy in self.convoys:
            rects.extend(convoy.get_blocker_rects())
        return rects
    
    def get_arrow_info(self):
        """Get arrow info for external rendering if needed."""
        if self.convoys:
            return self.convoys[0].get_arrow_info()
        return None
