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
    """Manages VIP vehicle with police escort."""
    
    def __init__(self, approach, road_info, geometry):
        self.approach = approach
        self.road_info = road_info
        self.geometry = geometry
        
        self.vip = VIPVehicle(approach, road_info)
        self.escorts = []
        self.blockers = []
        
        self.active = True
        self.state = "approaching"  # approaching, crossing, passed
        
        # Create escort vehicles
        self._create_escorts()
        self._create_blockers()
    
    def _create_escorts(self):
        """Create police escorts around VIP."""
        # Front escort
        front = PoliceVehicle(self.vip.x, self.vip.y, self.approach, self.road_info, "escort")
        
        # Rear escort
        rear = PoliceVehicle(self.vip.x, self.vip.y, self.approach, self.road_info, "escort")
        
        self.escorts = [front, rear]
    
    def _create_blockers(self):
        """Create police blockers at perpendicular roads."""
        cx = self.geometry["cx"]
        cy = self.geometry["cy"]
        road_w = self.geometry["road_width"]
        cross_s = self.geometry["cross_size"]
        
        # Block perpendicular traffic - position blockers closer to intersection
        if self.approach in ["N", "S"]:
            # Block E and W approaches
            blocker_w = PoliceVehicle(
                cx - cross_s // 2 - 60, cy + road_w // 4,
                "E", self.road_info, "blocker"
            )
            blocker_e = PoliceVehicle(
                cx + cross_s // 2 + 60, cy - road_w // 4,
                "W", self.road_info, "blocker"
            )
            self.blockers = [blocker_w, blocker_e]
        else:
            # Block N and S approaches
            blocker_n = PoliceVehicle(
                cx - road_w // 4, cy - cross_s // 2 - 60,
                "S", self.road_info, "blocker"
            )
            blocker_s = PoliceVehicle(
                cx + road_w // 4, cy + cross_s // 2 + 60,
                "N", self.road_info, "blocker"
            )
            self.blockers = [blocker_n, blocker_s]
    
    def get_escort_offsets(self):
        """Get position offsets for front and rear escorts based on approach."""
        front_offset = (0, 0)
        rear_offset = (0, 0)
        spacing = 80  # Increased from 70 for visual clarity
        
        if self.approach == "N":  # Moving down
            front_offset = (0, -spacing)
            rear_offset = (0, spacing)
        elif self.approach == "S":  # Moving up
            front_offset = (0, spacing)
            rear_offset = (0, -spacing)
        elif self.approach == "E":  # Moving left
            front_offset = (spacing, 0)
            rear_offset = (-spacing, 0)
        elif self.approach == "W":  # Moving right
            front_offset = (-spacing, 0)
            rear_offset = (spacing, 0)
        
        return front_offset, rear_offset
    
    def update(self, dt):
        if not self.active:
            return
        
        # Move VIP
        self.vip.move(dt)
        
        # Update escorts to follow VIP smoothly
        front_offset, rear_offset = self.get_escort_offsets()
        
        if len(self.escorts) >= 2:
            self.escorts[0].move_with_vip(self.vip.x, self.vip.y, 
                                          front_offset[0], front_offset[1], dt)
            self.escorts[1].move_with_vip(self.vip.x, self.vip.y,
                                          rear_offset[0], rear_offset[1], dt)
        
        # Update blockers (stationary)
        for blocker in self.blockers:
            blocker.update(dt)
        
        # Check if VIP has exited
        if not self.vip.active:
            self.active = False
    
    def draw(self, surface):
        # Draw blockers first (they're stationary)
        for blocker in self.blockers:
            blocker.draw(surface)
        
        # Draw escorts
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
        return {
            "x": self.vip.x,
            "y": self.vip.y,
            "approach": self.approach,
            "active": self.active
        }


class PoliceManager:
    """Manages all police vehicles and VIP convoys."""
    
    def __init__(self, road_info, geometry):
        self.road_info = road_info
        self.geometry = geometry
        self.convoys = []
        self.vip_spawn_timer = random.uniform(15, 30)  # First VIP after 15-30 seconds
        self.vip_active = False
        
    def set_geometry(self, cx, cy, road_width, cross_size):
        self.geometry = {
            "cx": cx,
            "cy": cy,
            "road_width": road_width,
            "cross_size": cross_size
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
            self.vip_spawn_timer = random.uniform(30, 55)  # Next VIP in 30-55 seconds
        
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
    
    def is_vip_active(self):
        return self.vip_active
    
    def get_blocked_directions(self):
        """Get directions that should have RED lights (perpendicular to VIP)."""
        blocked = set()
        for convoy in self.convoys:
            blocked.update(convoy.get_blocked_directions())
        return list(blocked)
    
    def get_spawn_blocked_directions(self):
        """Get ALL directions blocked for spawning during VIP passage."""
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
