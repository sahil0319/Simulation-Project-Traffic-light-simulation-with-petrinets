# accident.py

import pygame
import random
import math
import os
from petri_net import PetriNet
from vehicle import VEHICLE_TYPES, SPRITE_CACHE, load_sprites
from pedestrian import PEDESTRIAN_COLORS, SHIRT_COLORS


# --- Accident lifecycle phases ---
PHASE_COLLISION = "collision"             # Animated collision in progress
PHASE_CRASHED = "crashed"                 # Wreck on road, waiting for dispatch
PHASE_AMBULANCE_DISPATCHED = "ambulance_dispatched"
PHASE_LOADING = "loading"
PHASE_CLEARING = "clearing"
PHASE_DONE = "done"

# --- Constants ---
# Theoretical collision model constants
P_HIT = 0.20             # Base probability of crash given simultaneous occupancy
S_C = 0.036              # Car crossing time (minutes)
S_P = 0.081              # Ped crossing time (minutes)
LAMBDA_C = 28.5          # Average car spawn rate (cars/min)
BASELINE_RATE_P_MIN = 1.0 # 1 accident per min without peds
COLLISION_DURATION = 0.9          # Animation time for collision
DISPATCH_DELAY = 1.5
LOADING_DURATION = 4.0
CLEARING_DURATION = 2.5


# =========================================================================
#  Visual helper classes
# =========================================================================

class AccidentVictim:
    """Victim body lying on the road — same visual style as Pedestrian."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = random.uniform(0, 360)
        self.skin_color = random.choice(PEDESTRIAN_COLORS)
        self.shirt_color = random.choice(SHIRT_COLORS)
        self.pants_color = random.choice([
            (50, 50, 80), (70, 60, 50), (30, 30, 30),
            (80, 80, 100), (60, 40, 30)
        ])
        self.blood_radius = random.uniform(10, 16)
        self.blood_alpha = 200
        self.loaded = False
        self.arm_angle = random.uniform(-30, 30)
        self.leg_spread = random.uniform(4, 10)
        # for animation: victim slides / flies from impact
        self.start_x = x
        self.start_y = y
        self.target_x = x + random.uniform(-20, 20)
        self.target_y = y + random.uniform(-20, 20)
        self.visible = False  # only visible after collision completes

    def set_impact_trajectory(self, impact_x, impact_y, fly_dist=30):
        """Set the victim to fly away from impact point."""
        angle = random.uniform(0, math.pi * 2)
        self.start_x = impact_x
        self.start_y = impact_y
        self.target_x = impact_x + math.cos(angle) * fly_dist
        self.target_y = impact_y + math.sin(angle) * fly_dist

    def animate_collision(self, t):
        """Lerp the victim position during collision animation. t in [0,1]."""
        if t < 0.5:
            # Before impact — victim not visible
            self.visible = False
            return
        # After impact — victim flies out
        self.visible = True
        tt = (t - 0.5) / 0.5  # 0->1 over second half
        ease = 1 - (1 - tt) ** 2  # ease out
        self.x = self.start_x + (self.target_x - self.start_x) * ease
        self.y = self.start_y + (self.target_y - self.start_y) * ease

    def draw(self, surface, fade_alpha=255):
        if self.loaded or not self.visible:
            return

        a = int(min(255, fade_alpha))

        # Blood pool
        blood_surf = pygame.Surface((int(self.blood_radius * 3), int(self.blood_radius * 3)), pygame.SRCALPHA)
        bcx = int(self.blood_radius * 1.5)
        bcy = int(self.blood_radius * 1.5)
        ba = int(min(self.blood_alpha, fade_alpha))
        pygame.draw.circle(blood_surf, (120, 5, 5, ba), (bcx, bcy), int(self.blood_radius))
        for _ in range(3):
            sx = bcx + random.randint(-6, 6)
            sy = bcy + random.randint(-6, 6)
            pygame.draw.circle(blood_surf, (140, 8, 8, max(0, ba - 40)), (sx, sy), random.randint(2, 5))
        surface.blit(blood_surf, (int(self.x - self.blood_radius * 1.5),
                                   int(self.y - self.blood_radius * 1.5)))
        if fade_alpha < 30:
            return

        body_surf = pygame.Surface((36, 24), pygame.SRCALPHA)
        bx, by = 18, 12
        leg_w, leg_h = 3, 10
        pygame.draw.rect(body_surf, (*self.pants_color, a),
                         (bx - int(self.leg_spread) - 1, by + 2, leg_w, leg_h), border_radius=1)
        pygame.draw.rect(body_surf, (*self.pants_color, a),
                         (bx + int(self.leg_spread) - 2, by + 1, leg_w, leg_h), border_radius=1)
        pygame.draw.circle(body_surf, (30, 30, 30, a),
                           (bx - int(self.leg_spread), by + leg_h + 2), 2)
        pygame.draw.circle(body_surf, (30, 30, 30, a),
                           (bx + int(self.leg_spread) - 1, by + leg_h + 1), 2)
        torso_rect = pygame.Rect(bx - 5, by - 4, 10, 12)
        pygame.draw.ellipse(body_surf, (*self.shirt_color, a), torso_rect)
        arm_len = 8
        la_ex = bx - 5 - int(math.cos(math.radians(self.arm_angle)) * arm_len)
        la_ey = by + int(math.sin(math.radians(self.arm_angle)) * arm_len)
        pygame.draw.line(body_surf, (*self.skin_color, a), (bx - 5, by), (la_ex, la_ey), 2)
        ra_ex = bx + 5 + int(math.cos(math.radians(-self.arm_angle)) * arm_len)
        ra_ey = by + int(math.sin(math.radians(-self.arm_angle)) * arm_len)
        pygame.draw.line(body_surf, (*self.skin_color, a), (bx + 5, by), (ra_ex, ra_ey), 2)
        pygame.draw.circle(body_surf, (*self.skin_color, a), (bx, by - 8), 5)

        rotated = pygame.transform.rotate(body_surf, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


class GlassShard:
    """Glass debris piece from crash."""

    def __init__(self, x, y):
        self.x = x + random.uniform(-30, 30)
        self.y = y + random.uniform(-30, 30)
        self.size = random.uniform(1.5, 4)
        self.color = random.choice([
            (200, 220, 255), (180, 200, 240), (220, 240, 255),
            (160, 190, 220), (230, 250, 255)
        ])
        self.shimmer_offset = random.uniform(0, math.pi * 2)

    def draw(self, surface, alpha, time_offset=0):
        a = min(255, alpha)
        shimmer = abs(math.sin(time_offset * 2 + self.shimmer_offset))
        c = (min(255, self.color[0] + int(shimmer * 30)),
             min(255, self.color[1] + int(shimmer * 20)),
             min(255, self.color[2] + int(shimmer * 10)), a)
        s = int(self.size)
        if s < 1: return
        shard_surf = pygame.Surface((s * 3, s * 3), pygame.SRCALPHA)
        cx, cy = s * 3 // 2, s * 3 // 2
        pts = [(cx, cy - s), (cx + s, cy), (cx, cy + s - 1), (cx - s + 1, cy)]
        pygame.draw.polygon(shard_surf, c, pts)
        surface.blit(shard_surf, (int(self.x - s * 1.5), int(self.y - s * 1.5)))


class SkidMark:
    """Tire skid mark on road."""

    def __init__(self, start_x, start_y, direction, length=None):
        self.start_x = start_x
        self.start_y = start_y
        self.direction = direction
        self.length = length or random.uniform(40, 90)
        self.width = random.uniform(2, 4)
        self.curve = random.uniform(-15, 15)

    def draw(self, surface, alpha):
        a = min(200, alpha)
        color = (20, 20, 20, a)
        skid_surf = pygame.Surface((int(self.length + 20), int(abs(self.curve) + self.width + 10)), pygame.SRCALPHA)
        points = []
        for i in range(9):
            t = i / 8
            sx = int(t * self.length + 5)
            sy = int(5 + math.sin(t * math.pi) * self.curve)
            points.append((sx, sy))
        if len(points) >= 2:
            pygame.draw.lines(skid_surf, color, False, points, int(self.width))
        angle = 90 if self.direction in ["N", "S"] else 0
        rotated = pygame.transform.rotate(skid_surf, angle)
        rect = rotated.get_rect(center=(int(self.start_x), int(self.start_y)))
        surface.blit(rotated, rect)


class FireParticle:
    """Animated fire/smoke particle."""

    def __init__(self, x, y):
        self.x = x + random.uniform(-8, 8)
        self.y = y + random.uniform(-8, 8)
        self.life = random.uniform(0.3, 0.8)
        self.max_life = self.life
        self.size = random.uniform(3, 7)
        self.drift_x = random.uniform(-15, 15)
        self.drift_y = random.uniform(-40, -15)
        self.is_smoke = random.random() < 0.3

    def update(self, dt):
        self.life -= dt
        self.x += self.drift_x * dt
        self.y += self.drift_y * dt

    def draw(self, surface):
        if self.life <= 0: return
        t = self.life / self.max_life
        size = int(self.size * t)
        if size < 1: return
        if self.is_smoke:
            color = (80, 80, 80, int(80 * t))
        else:
            color = (int(255 * min(1, t + 0.3)), int(180 * t), 0, int(200 * t))
        ps = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(ps, color, (size + 1, size + 1), size)
        surface.blit(ps, (int(self.x - size - 1), int(self.y - size - 1)))

    @property
    def alive(self):
        return self.life > 0


# =========================================================================
#  Animated collision sprite — a car or pedestrian moving during collision
# =========================================================================

class CollisionSprite:
    """A vehicle or pedestrian sprite animated during the collision phase."""

    def __init__(self, sprite_type, start_x, start_y, end_x, end_y, direction,
                 vehicle_image=None, post_crash_angle=0):
        """
        sprite_type: 'vehicle' or 'pedestrian'
        start → end  = path it travels before impact
        post_crash_angle: angle the car rotates to after impact
        """
        self.sprite_type = sprite_type
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.x = start_x
        self.y = start_y
        self.direction = direction

        # Current drawing angle (starts aligned to road, rotates on impact)
        self.road_angle = {"N": 180, "S": 0, "E": 90, "W": -90}.get(direction, 0)
        self.current_angle = self.road_angle
        self.post_crash_angle = post_crash_angle

        # Vehicle sprite
        self.vehicle_image = vehicle_image  # pre-rotated by caller? No, raw UP-facing
        self.vehicle_length = 45
        self.vehicle_width = 24

        # Pedestrian visual   (only used if sprite_type == 'pedestrian')
        self.skin_color = random.choice(PEDESTRIAN_COLORS)
        self.shirt_color = random.choice(SHIRT_COLORS)

        # Impact flash
        self.impacted = False

    def animate(self, t):
        """t in [0, 1] — progress of collision animation."""
        impact_t = 0.55  # moment of impact

        if t < impact_t:
            # Approach phase — accelerate toward impact point
            frac = t / impact_t
            ease = frac ** 1.5  # accelerating
            self.x = self.start_x + (self.end_x - self.start_x) * ease
            self.y = self.start_y + (self.end_y - self.start_y) * ease
            self.current_angle = self.road_angle
            self.impacted = False
        else:
            # Post-impact — slide past slightly and spin
            self.impacted = True
            post_frac = (t - impact_t) / (1.0 - impact_t)
            ease = 1 - (1 - post_frac) ** 3  # ease out (decelerate)
            # Slide a little past impact point
            overshoot = 15
            if self.direction == "N":
                self.x = self.end_x + random.uniform(-2, 2)
                self.y = self.end_y + overshoot * ease
            elif self.direction == "S":
                self.x = self.end_x + random.uniform(-2, 2)
                self.y = self.end_y - overshoot * ease
            elif self.direction == "E":
                self.x = self.end_x - overshoot * ease
                self.y = self.end_y + random.uniform(-2, 2)
            elif self.direction == "W":
                self.x = self.end_x + overshoot * ease
                self.y = self.end_y + random.uniform(-2, 2)

            # Rotate from road angle toward post-crash angle
            self.current_angle = self.road_angle + (self.post_crash_angle - self.road_angle) * ease

    def draw(self, surface):
        if self.sprite_type == "vehicle":
            self._draw_vehicle(surface)
        else:
            self._draw_pedestrian(surface)

    def _draw_vehicle(self, surface):
        if self.vehicle_image:
            rotated = pygame.transform.rotate(self.vehicle_image, self.current_angle)
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated, rect)
        else:
            # Fallback rectangle
            car_surf = pygame.Surface((self.vehicle_width + 4, self.vehicle_length + 4), pygame.SRCALPHA)
            pygame.draw.rect(car_surf, (150, 50, 50), (2, 2, self.vehicle_width, self.vehicle_length), border_radius=4)
            pygame.draw.rect(car_surf, (60, 80, 130), (5, 10, self.vehicle_width - 6, 7), border_radius=2)
            rotated = pygame.transform.rotate(car_surf, self.current_angle)
            rect = rotated.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated, rect)

    def _draw_pedestrian(self, surface):
        x, y = int(self.x), int(self.y)
        # Same as Pedestrian.draw() — body + head
        body_rect = pygame.Rect(x - 4, y - 2, 8, 10)
        pygame.draw.ellipse(surface, self.shirt_color, body_rect)
        pygame.draw.circle(surface, self.skin_color, (x, y - 6), 5)


# =========================================================================
#  Damaged vehicle for wreck scene (uses real sprites)
# =========================================================================

class CrashedVehicle:
    """A wrecked vehicle using actual car sprites with damage overlay."""

    def __init__(self, x, y, direction, vehicle_image=None, crash_angle=None):
        load_sprites()
        self.x = x
        self.y = y
        self.direction = direction
        self.crash_angle = crash_angle if crash_angle is not None else random.uniform(-50, 50)

        if vehicle_image:
            self.original_image = vehicle_image
        else:
            normal_types = [k for k in VEHICLE_TYPES.keys() if k not in ("Ambulance", "VIP")]
            type_name = random.choice(normal_types)
            available = list(SPRITE_CACHE.get(type_name, {}).keys())
            if available:
                self.original_image = SPRITE_CACHE[type_name][random.choice(available)]
            else:
                self.original_image = None

        self.damaged_image = self._create_damaged_sprite()

    def _create_damaged_sprite(self):
        if self.original_image:
            base = self.original_image.copy()
            w, h = base.get_size()
            dmg = pygame.Surface((w, h), pygame.SRCALPHA)
            for _ in range(random.randint(3, 6)):
                sx = random.randint(2, max(3, w - 3))
                sy = random.randint(2, max(3, h - 3))
                ex = max(0, min(w - 1, sx + random.randint(-8, 8)))
                ey = max(0, min(h - 1, sy + random.randint(-8, 8)))
                pygame.draw.line(dmg, (20, 20, 20, 150), (sx, sy), (ex, ey), 2)
            crack_cx, crack_cy = w // 2, h // 3
            for _ in range(4):
                ang = random.uniform(0, math.pi * 2)
                ex = int(crack_cx + math.cos(ang) * random.randint(3, 8))
                ey = int(crack_cy + math.sin(ang) * random.randint(3, 6))
                pygame.draw.line(dmg, (200, 200, 200, 180),
                                 (crack_cx, crack_cy), (max(0, min(w-1, ex)), max(0, min(h-1, ey))), 1)
            dark = pygame.Surface((w, h), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 40))
            base.blit(dark, (0, 0))
            for _ in range(random.randint(1, 3)):
                pygame.draw.circle(dmg, (30, 30, 30, 80),
                                   (random.randint(3, max(4, w-4)), random.randint(3, max(4, h-4))),
                                   random.randint(2, 5))
            base.blit(dmg, (0, 0))
            return base
        else:
            cw, ch = 24, 45
            surf = pygame.Surface((cw + 4, ch + 4), pygame.SRCALPHA)
            clr = random.choice([(180,50,50),(50,50,180),(80,80,80),(200,180,50)])
            pygame.draw.rect(surf, clr, (2, 2, cw, ch), border_radius=4)
            for _ in range(3):
                sx, sy = random.randint(4, cw), random.randint(4, ch)
                pygame.draw.line(surf, (30,30,30), (sx,sy),
                                 (sx+random.randint(-5,5), sy+random.randint(-5,5)), 2)
            return surf

    def draw(self, surface, fade_alpha=255):
        if not self.damaged_image: return
        a = min(255, fade_alpha)
        rot_base = {"N": 180, "S": 0, "E": 90, "W": -90}.get(self.direction, 0)
        total = rot_base + self.crash_angle
        rotated = pygame.transform.rotate(self.damaged_image, total)
        if a < 255:
            rotated.set_alpha(a)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


# =========================================================================
#  Ambulance
# =========================================================================

class AccidentAmbulance:
    """Ambulance using Truck sprite base with red cross."""

    def __init__(self, target_x, target_y, approach, road_info, geometry):
        load_sprites()
        self.approach = approach
        self.road_info = road_info
        self.geometry = geometry
        self.target_x = target_x
        self.target_y = target_y
        self.width = 24
        self.length = 55
        self.max_speed = 250
        self.speed = self.max_speed

        # Build sprite
        truck_colors = list(SPRITE_CACHE.get("Truck", {}).keys())
        if truck_colors:
            preferred = [c for c in truck_colors if c in ("cream", "white")]
            color = preferred[0] if preferred else truck_colors[0]
            base_img = SPRITE_CACHE["Truck"][color]
            self.original_image = pygame.transform.scale(base_img, (self.width, self.length))
            self._apply_markings()
        else:
            self.original_image = None

        cx = geometry["cx"]
        cy = geometry["cy"]
        road_w = geometry["road_width"]
        sw = geometry.get("screen_width", 1000)
        sh = geometry.get("screen_height", 700)

        if approach == "N":
            self.x, self.y = cx - road_w // 4 - 35, -60
        elif approach == "S":
            self.x, self.y = cx + road_w // 4 + 35, sh + 60
        elif approach == "E":
            self.x, self.y = sw + 60, cy - road_w // 4 - 35
        elif approach == "W":
            self.x, self.y = -60, cy + road_w // 4 + 35

        self.state = "driving_to"
        self.at_scene_timer = 0
        self.active = True
        self.rect = pygame.Rect(0, 0, self.width, self.length)
        self._update_rect()

    def _apply_markings(self):
        if not self.original_image: return
        img = self.original_image.copy()
        w, h = img.get_size()
        cx_i, cy_i = w // 2, h // 3
        pygame.draw.rect(img, (220, 40, 40), (cx_i - 2, cy_i - 6, 4, 12))
        pygame.draw.rect(img, (220, 40, 40), (cx_i - 6, cy_i - 2, 12, 4))
        pygame.draw.rect(img, (200, 30, 30), (1, h // 2 - 2, w - 2, 4))
        self.original_image = img

    def _update_rect(self):
        if self.approach in ["N", "S"]:
            self.rect.size = (self.width, self.length)
        else:
            self.rect.size = (self.length, self.width)
        self.rect.center = (int(self.x), int(self.y))

    def update(self, dt):
        if not self.active: return
        if self.state == "driving_to":
            dist = math.hypot(self.x - self.target_x, self.y - self.target_y)
            if dist < 40:
                self.state = "at_scene"
                self.speed = 0; self.at_scene_timer = 0; return
            self.speed = max(30, self.max_speed * min(1, dist / 120))
            
            step = self.speed * dt
            if step >= dist - 35:
                # Snap to scene to prevent high-speed overshoot oscillation
                self.x = self.target_x
                self.y = self.target_y
                self.state = "at_scene"
                self.speed = 0; self.at_scene_timer = 0; return
            else:
                nx = (self.target_x - self.x) / dist
                ny = (self.target_y - self.y) / dist
                self.x += nx * step
                self.y += ny * step
        elif self.state == "at_scene":
            self.at_scene_timer += dt
            if self.at_scene_timer >= LOADING_DURATION:
                self.state = "driving_away"; self.speed = self.max_speed
        elif self.state == "driving_away":
            sw = self.geometry.get("screen_width", 1000)
            sh = self.geometry.get("screen_height", 700)
            if self.approach == "N": self.y += self.speed * dt
            elif self.approach == "S": self.y -= self.speed * dt
            elif self.approach == "E": self.x -= self.speed * dt
            elif self.approach == "W": self.x += self.speed * dt
            if self.x < -100 or self.x > sw + 100 or self.y < -100 or self.y > sh + 100:
                self.active = False
        self._update_rect()

    def draw(self, surface):
        if not self.active: return
        rot = {"N": 180, "S": 0, "E": 90, "W": -90}.get(self.approach, 0)
        if self.original_image:
            r = pygame.transform.rotate(self.original_image, rot)
            surface.blit(r, r.get_rect(center=(int(self.x), int(self.y))))
        else:
            w, h = self.width, self.length
            s = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
            pygame.draw.rect(s, (240, 240, 245), (2, 2, w, h), border_radius=6)
            pygame.draw.rect(s, (220, 40, 40), (3, h // 2 - 1, w - 2, 4))
            cx_i = w // 2 + 2; cy_i = h // 3 + 2
            pygame.draw.rect(s, (220, 40, 40), (cx_i - 2, cy_i - 6, 4, 12))
            pygame.draw.rect(s, (220, 40, 40), (cx_i - 6, cy_i - 2, 12, 4))
            r = pygame.transform.rotate(s, rot)
            surface.blit(r, r.get_rect(center=(int(self.x), int(self.y))))

        # Siren lights
        phase = int(pygame.time.get_ticks() / 100) % 4
        if self.approach in ["N", "S"]:
            off = self.length // 2 - 10
            ly = int(self.y + off) if self.approach == "N" else int(self.y - off)
            l1, l2 = (int(self.x - 6), ly), (int(self.x + 6), ly)
        else:
            off = self.length // 2 - 10
            lx = int(self.x - off) if self.approach == "E" else int(self.x + off)
            l1, l2 = (lx, int(self.y - 6)), (lx, int(self.y + 6))
        c1 = (255, 30, 30) if phase < 2 else (120, 0, 0)
        c2 = (30, 100, 255) if phase >= 2 else (0, 60, 160)
        for pos, c in [(l1, c1), (l2, c2)]:
            gs = pygame.Surface((22, 22), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*c[:3], 70), (11, 11), 11)
            surface.blit(gs, (pos[0] - 11, pos[1] - 11))
            pygame.draw.circle(surface, c, pos, 5)

        if self.state == "driving_to":
            f = pygame.font.Font(None, 14)
            lbl = f.render("AMBULANCE", True, (255, 255, 255))
            lr = lbl.get_rect(center=(int(self.x), int(self.y - self.length // 2 - 12)))
            bg = pygame.Surface(lr.inflate(6, 4).size, pygame.SRCALPHA); bg.fill((180, 30, 30, 180))
            surface.blit(bg, lr.inflate(6, 4)); surface.blit(lbl, lr)


# =========================================================================
#  Main Accident class — now with animated collision
# =========================================================================

def _pick_vehicle_sprite():
    """Pick a random vehicle sprite image (UP-facing) from the cache."""
    load_sprites()
    normal = [k for k in VEHICLE_TYPES.keys() if k not in ("Ambulance", "VIP")]
    random.shuffle(normal)
    for tn in normal:
        colors = list(SPRITE_CACHE.get(tn, {}).keys())
        if colors:
            return SPRITE_CACHE[tn][random.choice(colors)], tn
    return None, None


class Accident:
    """A car accident with animated collision, then wreck scene + ambulance response.

    collision_type:
        'car_car'        — two vehicles crash into each other
        'car_pedestrian' — a vehicle hits a crossing pedestrian
    """

    def __init__(self, accident_id, road_info, geometry,
                 collision_type="car_car",
                 real_vehicles=None, real_pedestrian=None):
        self.id = accident_id
        self.road_info = road_info
        self.geometry = geometry
        self.collision_type = collision_type

        cx = geometry["cx"]
        cy = geometry["cy"]
        road_w = geometry["road_width"]
        cross_s = geometry["cross_size"]
        sw = geometry.get("screen_width", 1000)
        sh = geometry.get("screen_height", 700)

        # Determine crash location and directions
        self.direction = random.choice(["N", "S", "E", "W"])

        if self.direction == "N":
            self.x = cx - road_w // 4 + random.randint(-10, 10)
            self.y = random.randint(100, cy - cross_s // 2 - 80)
        elif self.direction == "S":
            self.x = cx + road_w // 4 + random.randint(-10, 10)
            self.y = random.randint(cy + cross_s // 2 + 80, sh - 100)
        elif self.direction == "E":
            self.x = random.randint(cx + cross_s // 2 + 80, sw - 100)
            self.y = cy - road_w // 4 + random.randint(-10, 10)
        elif self.direction == "W":
            self.x = random.randint(100, cx - cross_s // 2 - 80)
            self.y = cy + road_w // 4 + random.randint(-10, 10)

        # Use real vehicle positions if provided
        if real_vehicles and len(real_vehicles) >= 1:
            v0 = real_vehicles[0]
            self.x = int(v0.x)
            self.y = int(v0.y)
            self.direction = v0.approach
        if real_pedestrian:
            self.x = int(real_pedestrian.x)
            self.y = int(real_pedestrian.y)

        # Phase
        self.phase = PHASE_COLLISION
        self.phase_timer = 0
        self.total_time = 0

        # --- Build collision animation sprites ---
        self.collision_sprites = []
        approach_dist = 100  # how far back to start

        if collision_type == "car_car":
            # Two cars approaching from opposite-ish directions
            dir1 = self.direction
            dir2_map = {"N": "S", "S": "N", "E": "W", "W": "E"}
            dir2 = dir2_map[dir1]

            img1, _ = _pick_vehicle_sprite()
            img2, _ = _pick_vehicle_sprite()

            # Use real vehicle sprites if available
            if real_vehicles and len(real_vehicles) >= 1 and real_vehicles[0].original_image:
                img1 = real_vehicles[0].original_image
                dir1 = real_vehicles[0].approach
            if real_vehicles and len(real_vehicles) >= 2 and real_vehicles[1].original_image:
                img2 = real_vehicles[1].original_image
                dir2 = real_vehicles[1].approach

            # Compute start positions (actual positions if available, else offset)
            if real_vehicles and len(real_vehicles) >= 1:
                s1x, s1y = real_vehicles[0].x, real_vehicles[0].y
            else:
                s1x, s1y = self.x, self.y
                if dir1 == "N": s1y -= approach_dist
                elif dir1 == "S": s1y += approach_dist
                elif dir1 == "E": s1x += approach_dist
                elif dir1 == "W": s1x -= approach_dist
                
            if real_vehicles and len(real_vehicles) >= 2:
                s2x, s2y = real_vehicles[1].x, real_vehicles[1].y
            else:
                s2x, s2y = self.x, self.y
                if dir2 == "N": s2y -= approach_dist
                elif dir2 == "S": s2y += approach_dist
                elif dir2 == "E": s2x += approach_dist
                elif dir2 == "W": s2x -= approach_dist
            # Post-crash angles
            pc1 = random.uniform(-40, 40)
            pc2 = random.uniform(-40, 40)

            cs1 = CollisionSprite("vehicle", s1x, s1y, self.x - 8, self.y - 8, dir1,
                                  vehicle_image=img1,
                                  post_crash_angle={"N":180,"S":0,"E":90,"W":-90}[dir1] + pc1)
            cs2 = CollisionSprite("vehicle", s2x, s2y, self.x + 8, self.y + 8, dir2,
                                  vehicle_image=img2,
                                  post_crash_angle={"N":180,"S":0,"E":90,"W":-90}[dir2] + pc2)
            self.collision_sprites = [cs1, cs2]
            self._crash_angles = [pc1, pc2]
            self._crash_images = [img1, img2]

        elif collision_type == "car_pedestrian":
            img1, _ = _pick_vehicle_sprite()
            if real_vehicles and len(real_vehicles) >= 1 and real_vehicles[0].original_image:
                img1 = real_vehicles[0].original_image
                dir1 = real_vehicles[0].approach
            else:
                dir1 = self.direction

            if real_vehicles and len(real_vehicles) >= 1:
                s1x, s1y = real_vehicles[0].x, real_vehicles[0].y
            else:
                s1x, s1y = self.x, self.y
                if dir1 == "N": s1y -= approach_dist
                elif dir1 == "S": s1y += approach_dist
                elif dir1 == "E": s1x += approach_dist
                elif dir1 == "W": s1x -= approach_dist

            pc1 = random.uniform(-25, 25)
            cs_car = CollisionSprite("vehicle", s1x, s1y, self.x, self.y, dir1,
                                     vehicle_image=img1,
                                     post_crash_angle={"N":180,"S":0,"E":90,"W":-90}[dir1] + pc1)
            # Pedestrian standing at impact
            ped_skin = real_pedestrian.skin_color if real_pedestrian else random.choice(PEDESTRIAN_COLORS)
            ped_shirt = real_pedestrian.shirt_color if real_pedestrian else random.choice(SHIRT_COLORS)
            cs_ped = CollisionSprite("pedestrian", self.x, self.y, self.x, self.y, dir1)
            cs_ped.skin_color = ped_skin
            cs_ped.shirt_color = ped_shirt
            self.collision_sprites = [cs_car, cs_ped]
            self._crash_angles = [pc1]
            self._crash_images = [img1]

        # Impact flash timer
        self._impact_flash = 0

        # --- These are created AFTER collision animation completes ---
        self.crashed_vehicles = []
        self.victims = []
        self.glass_shards = []
        self.skid_marks = []
        self.fire_particles = []
        self.fire_spawn_timer = 0
        self.cones = []
        self.ambulance = None
        self.fade_alpha = 255
        self.num_victims = 0

        block_size = 75
        self.blocker_rect = pygame.Rect(self.x - block_size // 2, self.y - block_size // 2,
                                        block_size, block_size)
        self.active = True
        self._wreck_created = False

    def _create_wreck_scene(self):
        """Build the static wreck scene elements after collision animation ends."""
        self._wreck_created = True

        if self.collision_type == "car_car":
            for i, cs in enumerate(self.collision_sprites):
                angle = self._crash_angles[i] if i < len(self._crash_angles) else random.uniform(-40, 40)
                img = self._crash_images[i] if i < len(self._crash_images) else None
                cv = CrashedVehicle(cs.x, cs.y, cs.direction,
                                    vehicle_image=img, crash_angle=angle)
                self.crashed_vehicles.append(cv)
            self.num_victims = random.randint(1, 3)
        elif self.collision_type == "car_pedestrian":
            cs_car = self.collision_sprites[0]
            img = self._crash_images[0] if self._crash_images else None
            angle = self._crash_angles[0] if self._crash_angles else random.uniform(-25, 25)
            cv = CrashedVehicle(cs_car.x, cs_car.y, cs_car.direction,
                                vehicle_image=img, crash_angle=angle)
            self.crashed_vehicles.append(cv)
            self.num_victims = 1

        # Victims
        for _ in range(self.num_victims):
            v = AccidentVictim(self.x + random.uniform(-25, 25), self.y + random.uniform(-25, 25))
            v.set_impact_trajectory(self.x, self.y, random.uniform(15, 35))
            v.visible = True
            self.victims.append(v)

        # Glass
        for _ in range(random.randint(6, 15)):
            self.glass_shards.append(GlassShard(self.x, self.y))

        # Skid marks
        for _ in range(random.randint(1, 3)):
            off = random.uniform(-15, 15)
            if self.direction in ["N", "S"]:
                sx = self.x + off
                sy = self.y + (random.uniform(-60, -30) if self.direction == "N" else random.uniform(30, 60))
            else:
                sx = self.x + (random.uniform(-60, -30) if self.direction == "W" else random.uniform(30, 60))
                sy = self.y + off
            self.skid_marks.append(SkidMark(sx, sy, self.direction))

        # Hazard cones
        cone_spread = 55
        if self.direction in ["N", "S"]:
            for dy in [-cone_spread, -cone_spread // 2, cone_spread // 2, cone_spread]:
                self.cones.append((self.x + random.uniform(-8, 8), self.y + dy))
        else:
            for dx in [-cone_spread, -cone_spread // 2, cone_spread // 2, cone_spread]:
                self.cones.append((self.x + dx, self.y + random.uniform(-8, 8)))

    def _best_ambulance_approach(self):
        cx, cy = self.geometry["cx"], self.geometry["cy"]
        if self.direction in ["N", "S"]:
            return "N" if self.y < cy else "S"
        return "W" if self.x < cx else "E"

    def update(self, dt):
        if not self.active: return
        self.total_time += dt
        self.phase_timer += dt

        if self.phase == PHASE_COLLISION:
            t = min(1.0, self.phase_timer / COLLISION_DURATION)
            for cs in self.collision_sprites:
                cs.animate(t)
            # Animate victims during collision
            for v in self.victims:
                v.animate_collision(t)
            # Impact flash
            if t >= 0.5:
                self._impact_flash = max(0, 1.0 - (t - 0.5) / 0.3)
            if self.phase_timer >= COLLISION_DURATION:
                # Transition to CRASHED — build wreck scene
                if not self._wreck_created:
                    self._create_wreck_scene()
                self.phase = PHASE_CRASHED
                self.phase_timer = 0

        elif self.phase == PHASE_CRASHED:
            # Fire particles
            self.fire_spawn_timer -= dt
            if self.fire_spawn_timer <= 0:
                self.fire_particles.append(FireParticle(self.x, self.y))
                self.fire_spawn_timer = random.uniform(0.05, 0.15)
            for p in self.fire_particles: p.update(dt)
            self.fire_particles = [p for p in self.fire_particles if p.alive]

            if self.phase_timer >= DISPATCH_DELAY:
                self.phase = PHASE_AMBULANCE_DISPATCHED; self.phase_timer = 0
                self.ambulance = AccidentAmbulance(self.x, self.y, self._best_ambulance_approach(),
                                                    self.road_info, self.geometry)

        elif self.phase == PHASE_AMBULANCE_DISPATCHED:
            self.fire_spawn_timer -= dt
            if self.fire_spawn_timer <= 0:
                self.fire_particles.append(FireParticle(self.x, self.y))
                self.fire_spawn_timer = random.uniform(0.05, 0.15)
            for p in self.fire_particles: p.update(dt)
            self.fire_particles = [p for p in self.fire_particles if p.alive]
            if self.ambulance:
                self.ambulance.update(dt)
                if self.ambulance.state == "at_scene":
                    self.phase = PHASE_LOADING; self.phase_timer = 0

        elif self.phase == PHASE_LOADING:
            self.fire_spawn_timer -= dt
            if self.fire_spawn_timer <= 0:
                self.fire_particles.append(FireParticle(self.x, self.y))
                self.fire_spawn_timer = random.uniform(0.08, 0.2)
            for p in self.fire_particles: p.update(dt)
            self.fire_particles = [p for p in self.fire_particles if p.alive]
            if self.ambulance:
                self.ambulance.update(dt)
                prog = self.phase_timer / LOADING_DURATION
                to_load = int(prog * self.num_victims)
                for i in range(min(to_load, len(self.victims))):
                    self.victims[i].loaded = True
                if self.ambulance.state == "driving_away":
                    for v in self.victims: v.loaded = True
                    self.phase = PHASE_CLEARING; self.phase_timer = 0

        elif self.phase == PHASE_CLEARING:
            if self.ambulance: self.ambulance.update(dt)
            for p in self.fire_particles: p.update(dt)
            self.fire_particles = [p for p in self.fire_particles if p.alive]
            self.fade_alpha = max(0, int(255 * (1.0 - self.phase_timer / CLEARING_DURATION)))
            if self.phase_timer >= CLEARING_DURATION:
                self.phase = PHASE_DONE; self.active = False

    def get_blocker_rect(self):
        if self.phase in [PHASE_COLLISION, PHASE_CRASHED, PHASE_AMBULANCE_DISPATCHED, PHASE_LOADING]:
            return self.blocker_rect
        return None

    def get_blocked_direction(self):
        if self.phase in [PHASE_COLLISION, PHASE_CRASHED, PHASE_AMBULANCE_DISPATCHED, PHASE_LOADING]:
            return self.direction
        return None

    def draw(self, surface):
        if not self.active: return
        alpha = self.fade_alpha

        # ---- COLLISION ANIMATION PHASE ----
        if self.phase == PHASE_COLLISION:
            for cs in self.collision_sprites:
                cs.draw(surface)
            # Impact flash
            if self._impact_flash > 0:
                flash_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                fa = int(200 * self._impact_flash)
                pygame.draw.circle(flash_surf, (255, 255, 200, fa), (30, 30), int(30 * self._impact_flash))
                surface.blit(flash_surf, (int(self.x - 30), int(self.y - 30)))
                # Spark particles
                for _ in range(3):
                    sx = self.x + random.uniform(-15, 15)
                    sy = self.y + random.uniform(-15, 15)
                    pygame.draw.circle(surface, (255, 200, 50), (int(sx), int(sy)), random.randint(1, 3))
            return

        # ---- POST-COLLISION WRECK SCENE ----

        # Skid marks (under everything)
        for skid in self.skid_marks:
            skid.draw(surface, alpha)

        # Police tape
        if self.phase != PHASE_CLEARING or alpha > 100:
            tape_a = min(alpha, 200)
            trect = self.blocker_rect.inflate(20, 20)
            ts = pygame.Surface(trect.size, pygame.SRCALPHA)
            sw = 8
            for x in range(0, trect.width, sw * 2):
                c = (255, 200, 0, tape_a) if (x // sw) % 2 == 0 else (30, 30, 30, tape_a)
                pygame.draw.rect(ts, c, (x, 0, sw, 3))
                pygame.draw.rect(ts, c, (x, trect.height - 3, sw, 3))
            for y in range(0, trect.height, sw * 2):
                c = (255, 200, 0, tape_a) if (y // sw) % 2 == 0 else (30, 30, 30, tape_a)
                pygame.draw.rect(ts, c, (0, y, 3, sw))
                pygame.draw.rect(ts, c, (trect.width - 3, y, 3, sw))
            surface.blit(ts, trect.topleft)

        # Glass
        for sh in self.glass_shards:
            sh.draw(surface, alpha, self.total_time)

        # Crashed vehicles
        for cv in self.crashed_vehicles:
            cv.draw(surface, alpha)

        # Victims
        for v in self.victims:
            v.draw(surface, alpha)

        # Fire
        for p in self.fire_particles:
            p.draw(surface)

        # Cones
        for cx_c, cy_c in self.cones:
            self._draw_cone(surface, cx_c, cy_c, alpha)

        # Ambulance
        if self.ambulance and self.ambulance.active:
            self.ambulance.draw(surface)

        # Warning text
        if self.phase in [PHASE_CRASHED, PHASE_AMBULANCE_DISPATCHED]:
            if (pygame.time.get_ticks() // 300) % 2 == 0:
                f = pygame.font.Font(None, 22)
                txt = f.render("!! ACCIDENT !!", True, (255, 60, 60))
                tr = txt.get_rect(center=(int(self.x), int(self.y - 55)))
                bg = pygame.Surface(tr.inflate(12, 6).size, pygame.SRCALPHA)
                pygame.draw.rect(bg, (0, 0, 0, 200), bg.get_rect(), border_radius=4)
                pygame.draw.rect(bg, (255, 60, 60, 200), bg.get_rect(), 2, border_radius=4)
                surface.blit(bg, tr.inflate(12, 6)); surface.blit(txt, tr)

        if self.phase == PHASE_LOADING:
            dots = "." * (int(self.phase_timer * 2) % 4)
            f = pygame.font.Font(None, 18)
            txt = f.render(f"Loading bodies{dots}", True, (255, 200, 100))
            tr = txt.get_rect(center=(int(self.x), int(self.y - 55)))
            bg = pygame.Surface(tr.inflate(8, 4).size, pygame.SRCALPHA); bg.fill((0, 0, 0, 160))
            surface.blit(bg, tr.inflate(8, 4)); surface.blit(txt, tr)

        if self.phase != PHASE_DONE and self.num_victims > 0:
            f = pygame.font.Font(None, 16)
            ct = f.render(f"{self.num_victims} dead", True, (255, 80, 80))
            cr = ct.get_rect(center=(int(self.x), int(self.y + 55)))
            bg = pygame.Surface(cr.inflate(8, 4).size, pygame.SRCALPHA)
            bg.fill((0, 0, 0, min(160, alpha)))
            surface.blit(bg, cr.inflate(8, 4))
            if alpha > 50: surface.blit(ct, cr)

    def _draw_cone(self, surface, x, y, alpha):
        a = min(255, alpha)
        cs = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.rect(cs, (40, 40, 40, a), (2, 10, 10, 3), border_radius=1)
        pygame.draw.polygon(cs, (255, 140, 0, a), [(7, 0), (3, 10), (11, 10)])
        pygame.draw.line(cs, (255, 255, 255, a), (5, 4), (9, 4), 2)
        pygame.draw.line(cs, (255, 255, 255, a), (4, 7), (10, 7), 1)
        surface.blit(cs, (int(x - 7), int(y - 7)))


# =========================================================================
#  AccidentManager — scans for real vehicles/pedestrians to crash
# =========================================================================

class AccidentManager:
    """Manages accident events. Can grab real vehicles/pedestrians for realistic crashes."""

    def __init__(self, road_info, geometry, stats_tracker=None):
        self.road_info = road_info
        self.geometry = geometry
        self.accidents = []
        self.next_id = 0
        self.spawn_timer = random.expovariate(BASELINE_RATE_P_MIN / 60.0)
        self.total_accidents = 0
        self.total_fatalities = 0
        self.active_accident_count = 0
        self.stats_tracker = stats_tracker

    def trigger_accident(self, vehicle_manager=None, pedestrian_manager=None):
        """Trigger an accident, optionally grabbing real entities from the simulation."""
        collision_type = "car_car"
        real_vehicles = []
        real_pedestrian = None

        # --- Try to find real candidates ---
        if vehicle_manager and pedestrian_manager:
            # Option 1: car hits crossing pedestrian
            crossing_peds = [p for p in pedestrian_manager.pedestrians if p.crossing and p.is_on_road()]
            if crossing_peds:
                ped = random.choice(crossing_peds)
                # Find a vehicle near this pedestrian
                all_v = [v for lane in vehicle_manager.vehicles.values() for v in lane]
                near_vehicles = [v for v in all_v if math.hypot(v.x - ped.x, v.y - ped.y) < 500
                                 and not v.is_ambulance]
                if near_vehicles:
                    chosen_v = min(near_vehicles, key=lambda v: math.hypot(v.x - ped.x, v.y - ped.y))
                    collision_type = "car_pedestrian"
                    real_vehicles = [chosen_v]
                    real_pedestrian = ped
                    # Remove from simulation
                    for d, lane in vehicle_manager.vehicles.items():
                        if chosen_v in lane:
                            lane.remove(chosen_v); break
                    pedestrian_manager.pedestrians.remove(ped)

        # Option 2: two cars crash
        if collision_type == "car_car" and vehicle_manager:
            all_v = [v for lane in vehicle_manager.vehicles.values() for v in lane
                     if not v.is_ambulance and not v.is_vip]
            if len(all_v) >= 2:
                # Pick two vehicles, preferring ones near each other or near intersection
                cx = self.geometry["cx"]
                cy = self.geometry["cy"]
                # Sort by distance to intersection center
                all_v.sort(key=lambda v: math.hypot(v.x - cx, v.y - cy))
                v1 = all_v[0]
                # Find another from a different direction if possible
                v2 = None
                for v in all_v[1:]:
                    if v.approach != v1.approach:
                        v2 = v; break
                if not v2 and len(all_v) >= 2:
                    v2 = all_v[1]
                if v2:
                    real_vehicles = [v1, v2]
                    for rv in real_vehicles:
                        for d, lane in vehicle_manager.vehicles.items():
                            if rv in lane:
                                lane.remove(rv); break

        accident = Accident(self.next_id, self.road_info, self.geometry,
                            collision_type=collision_type,
                            real_vehicles=real_vehicles,
                            real_pedestrian=real_pedestrian)
        accident._spawn_ped_rate = pedestrian_manager.spawn_rate_ppm if pedestrian_manager else 0
        self.accidents.append(accident)
        self.next_id += 1
        self.total_accidents += 1
        # Fatalities added after wreck scene creates victims (deferred)
        accident._fatalities_counted = False

    def update(self, dt, vehicle_manager=None, pedestrian_manager=None):
        self.spawn_timer -= dt
        self._ped_manager = pedestrian_manager  # keep ref for spawn rate
        while self.spawn_timer <= 0:
            active = sum(1 for a in self.accidents if a.active)
            if active < 5:
                self.trigger_accident(vehicle_manager, pedestrian_manager)
            
            # Recalculate dynamic accident rate based on queuing model
            lambda_p = self._ped_manager.spawn_rate_ppm if self._ped_manager else 0
            # Accident rate per minute = baseline + (p_hit * lambda_c * lambda_p * s_c * s_p)
            rate_per_min = BASELINE_RATE_P_MIN + (P_HIT * LAMBDA_C * lambda_p * S_C * S_P)
            # Convert to rate per second for expovariate
            rate_per_sec = rate_per_min / 60.0
            
            self.spawn_timer += random.expovariate(rate_per_sec)

        for accident in self.accidents:
            accident.update(dt)
            # Count fatalities once the wreck scene has been created
            if not accident._fatalities_counted and accident.num_victims > 0:
                self.total_fatalities += accident.num_victims
                accident._fatalities_counted = True
                if self.stats_tracker:
                    ped_rate = getattr(accident, '_spawn_ped_rate', 0)
                    self.stats_tracker.record_accident(
                        accident.collision_type, accident.direction,
                        accident.num_victims, ped_spawn_rate=ped_rate
                    )

        self.accidents = [a for a in self.accidents if a.active]
        self.active_accident_count = len(self.accidents)

    def get_blocker_rects(self):
        return [r for a in self.accidents for r in [a.get_blocker_rect()] if r]

    def get_blocked_directions(self):
        return list({a.get_blocked_direction() for a in self.accidents if a.get_blocked_direction()})

    def draw(self, surface):
        for a in self.accidents:
            a.draw(surface)
