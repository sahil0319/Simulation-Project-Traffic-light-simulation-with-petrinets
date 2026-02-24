# pedestrian.py

import pygame
import random
import math

# Pedestrian colors for variety
PEDESTRIAN_COLORS = [
    (255, 200, 150),  # Light skin
    (210, 160, 120),  # Medium skin
    (150, 100, 70),   # Dark skin
    (255, 220, 180),  # Pale
]

SHIRT_COLORS = [
    (255, 100, 100),  # Red
    (100, 150, 255),  # Blue
    (100, 255, 100),  # Green
    (255, 255, 100),  # Yellow
    (200, 100, 255),  # Purple
    (255, 150, 50),   # Orange
    (255, 255, 255),  # White
]

class Pedestrian:
    def __init__(self, crossing_type, direction, geometry):
        """
        crossing_type: "horizontal_top", "horizontal_bottom", "vertical_left", "vertical_right"
        direction: "positive" or "negative"
        geometry: dict with cx, cy, road_width, cross_size
        """
        self.crossing_type = crossing_type
        self.direction = direction
        self.geometry = geometry
        
        cx = geometry["cx"]
        cy = geometry["cy"]
        road_w = geometry["road_width"]
        cross_s = geometry["cross_size"]
        
        # Waypoints: [spawn, curb_wait, cross_end, destination]
        # Pedestrian spawns on sidewalk, walks to curb, waits for safe signal,
        # then crosses the full road, and walks onto the opposite sidewalk.
        
        sidewalk_offset = 45  # Distance from road edge to spawn on sidewalk
        curb_margin = 5       # Stop just before the road edge
        
        crosswalk_offset = 40  # Crosswalk distance from intersection edge
        
        if crossing_type == "horizontal_top":  # Crosses top of vertical road (NW <-> NE)
            y_cross = cy - cross_s // 2 - crosswalk_offset
            if direction == "positive":  # West to East
                self.waypoints = [
                    (cx - road_w // 2 - sidewalk_offset, y_cross),   # Spawn on NW sidewalk
                    (cx - road_w // 2 - curb_margin, y_cross),       # Wait at west curb
                    (cx + road_w // 2 + curb_margin, y_cross),       # Reach east curb
                    (cx + road_w // 2 + sidewalk_offset, y_cross),   # Walk onto NE sidewalk
                ]
            else:  # East to West
                self.waypoints = [
                    (cx + road_w // 2 + sidewalk_offset, y_cross),
                    (cx + road_w // 2 + curb_margin, y_cross),
                    (cx - road_w // 2 - curb_margin, y_cross),
                    (cx - road_w // 2 - sidewalk_offset, y_cross),
                ]
            self.check_directions = ["N", "S"]  # Check vertical traffic lights
            self.crossing_axis = "horizontal"
            self.road_min = cx - road_w // 2
            self.road_max = cx + road_w // 2
            self.cross_y = y_cross
            self.cross_x = None
            
        elif crossing_type == "horizontal_bottom":  # SW <-> SE
            y_cross = cy + cross_s // 2 + crosswalk_offset
            if direction == "positive":
                self.waypoints = [
                    (cx - road_w // 2 - sidewalk_offset, y_cross),
                    (cx - road_w // 2 - curb_margin, y_cross),
                    (cx + road_w // 2 + curb_margin, y_cross),
                    (cx + road_w // 2 + sidewalk_offset, y_cross),
                ]
            else:
                self.waypoints = [
                    (cx + road_w // 2 + sidewalk_offset, y_cross),
                    (cx + road_w // 2 + curb_margin, y_cross),
                    (cx - road_w // 2 - curb_margin, y_cross),
                    (cx - road_w // 2 - sidewalk_offset, y_cross),
                ]
            self.check_directions = ["N", "S"]
            self.crossing_axis = "horizontal"
            self.road_min = cx - road_w // 2
            self.road_max = cx + road_w // 2
            self.cross_y = y_cross
            self.cross_x = None
            
        elif crossing_type == "vertical_left":  # NW <-> SW
            x_cross = cx - cross_s // 2 - crosswalk_offset
            if direction == "positive":  # North to South
                self.waypoints = [
                    (x_cross, cy - road_w // 2 - sidewalk_offset),
                    (x_cross, cy - road_w // 2 - curb_margin),
                    (x_cross, cy + road_w // 2 + curb_margin),
                    (x_cross, cy + road_w // 2 + sidewalk_offset),
                ]
            else:
                self.waypoints = [
                    (x_cross, cy + road_w // 2 + sidewalk_offset),
                    (x_cross, cy + road_w // 2 + curb_margin),
                    (x_cross, cy - road_w // 2 - curb_margin),
                    (x_cross, cy - road_w // 2 - sidewalk_offset),
                ]
            self.check_directions = ["E", "W"]
            self.crossing_axis = "vertical"
            self.road_min = cy - road_w // 2
            self.road_max = cy + road_w // 2
            self.cross_x = x_cross
            self.cross_y = None
            
        elif crossing_type == "vertical_right":  # NE <-> SE
            x_cross = cx + cross_s // 2 + crosswalk_offset
            if direction == "positive":
                self.waypoints = [
                    (x_cross, cy - road_w // 2 - sidewalk_offset),
                    (x_cross, cy - road_w // 2 - curb_margin),
                    (x_cross, cy + road_w // 2 + curb_margin),
                    (x_cross, cy + road_w // 2 + sidewalk_offset),
                ]
            else:
                self.waypoints = [
                    (x_cross, cy + road_w // 2 + sidewalk_offset),
                    (x_cross, cy + road_w // 2 + curb_margin),
                    (x_cross, cy - road_w // 2 - curb_margin),
                    (x_cross, cy - road_w // 2 - sidewalk_offset),
                ]
            self.check_directions = ["E", "W"]
            self.crossing_axis = "vertical"
            self.road_min = cy - road_w // 2
            self.road_max = cy + road_w // 2
            self.cross_x = x_cross
            self.cross_y = None
        
        self.current_target_idx = 0
        self.x, self.y = self.waypoints[0]
        self.speed = random.uniform(35, 55)
        self.crossing_speed = self.speed * 1.3  # Walk faster while crossing
        self.radius = 6
        
        # Visual attributes
        self.skin_color = random.choice(PEDESTRIAN_COLORS)
        self.shirt_color = random.choice(SHIRT_COLORS)
        
        self.waiting = False
        self.crossing = False   # True when actively on the road
        self.wait_time = 0
        self.animation_offset = random.uniform(0, math.pi * 2)
        self.finished = False
        
    def is_on_road(self):
        """Check if pedestrian is currently on the road surface."""
        if self.crossing_axis == "horizontal":
            return self.road_min - 5 < self.x < self.road_max + 5
        else:
            return self.road_min - 5 < self.y < self.road_max + 5
    
    def can_cross(self, light_states, vip_active=False, vehicles=None):
        """Check if pedestrian can safely cross based on traffic lights and nearby vehicles."""
        if vip_active:
            return False  # Never cross during VIP passage
            
        # Pedestrian can cross when the perpendicular traffic has red/yellow
        for d in self.check_directions:
            state = light_states.get(d, "red")
            if state == "green":
                return False  # Traffic is flowing in our crosswalk direction
        
        # Check if any vehicle is currently in or very close to our crosswalk
        if vehicles:
            crosswalk_rect = self.get_crosswalk_rect()
            # Expand the check area slightly for safety
            safety_rect = crosswalk_rect.inflate(20, 20)
            for v in vehicles:
                if safety_rect.colliderect(v.rect) and v.speed > 10:
                    return False  # Vehicle is in/near crosswalk and moving
        
        return True
    
    def get_crosswalk_rect(self):
        """Return the rectangle area of this pedestrian's crosswalk for vehicle detection."""
        if self.crossing_axis == "horizontal":
            return pygame.Rect(self.road_min, self.cross_y - 20, 
                             self.road_max - self.road_min, 40)
        else:
            return pygame.Rect(self.cross_x - 20, self.road_min,
                             40, self.road_max - self.road_min)
    
    def move(self, dt, light_states, vip_active=False, vehicles=None):
        if self.finished:
            return
            
        if self.current_target_idx >= len(self.waypoints):
            self.finished = True
            self.crossing = False
            return
        
        target = self.waypoints[self.current_target_idx]
        dx = target[0] - self.x
        dy = target[1] - self.y
        dist = (dx**2 + dy**2)**0.5
        
        # === PHASE 1: Walking to curb (waypoint 0 -> 1) ===
        # Just walk normally, no checks needed
        
        # === PHASE 2: At curb, wait for safe crossing (at waypoint 1) ===
        if self.current_target_idx == 1 and dist < 8:
            if not self.can_cross(light_states, vip_active, vehicles):
                self.waiting = True
                self.wait_time += dt
                return
            else:
                self.waiting = False
                self.crossing = True  # Start crossing!
        
        # === PHASE 3: Crossing the road (waypoint 1 -> 2) ===
        # Once crossing, NEVER stop. Commit to crossing.
        # Use faster speed while on road.
        
        # === PHASE 4: Reached other side (waypoint 2 -> 3) ===
        # Walk onto sidewalk and finish
        
        # Reached waypoint, advance to next
        if dist < 5:
            self.current_target_idx += 1
            if self.current_target_idx >= len(self.waypoints):
                self.finished = True
                self.crossing = False
                return
            target = self.waypoints[self.current_target_idx]
            dx = target[0] - self.x
            dy = target[1] - self.y
            dist = (dx**2 + dy**2)**0.5
            
            # Check if we just finished crossing (reached waypoint 2)
            if self.current_target_idx >= 3:
                self.crossing = False
        
        # Move towards target
        if dist > 0:
            nx = dx / dist
            ny = dy / dist
            
            # Use faster speed while crossing the road
            current_speed = self.crossing_speed if self.crossing else self.speed
            
            self.x += nx * current_speed * dt
            self.y += ny * current_speed * dt
            self.animation_offset += dt * 10

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        
        # Walking animation - slight bob
        bob = math.sin(self.animation_offset) * 1.5 if not self.waiting else 0
        
        # Body (shirt)
        body_rect = pygame.Rect(x - 4, y - 2 + bob, 8, 10)
        pygame.draw.ellipse(surface, self.shirt_color, body_rect)
        
        # Head
        pygame.draw.circle(surface, self.skin_color, (x, int(y - 6 + bob)), 5)
        
        # Waiting indicator (small pulsing circle above head)
        if self.waiting:
            pulse = abs(math.sin(pygame.time.get_ticks() / 300)) * 0.5 + 0.5
            wait_color = (int(255 * pulse), int(100 * pulse), int(100 * pulse))
            pygame.draw.circle(surface, wait_color, (x, int(y - 15)), 3)


class PedestrianManager:
    def __init__(self, road_info, geometry=None):
        self.pedestrians = []
        self.road_info = road_info
        self.spawn_timer = random.uniform(2, 4)
        
        # Default geometry (will be set from main.py)
        self.geometry = geometry or {
            "cx": 500,
            "cy": 350,
            "road_width": 220,
            "cross_size": 260
        }
        
        # Crossing types available
        self.crossing_types = [
            "horizontal_top",
            "horizontal_bottom", 
            "vertical_left",
            "vertical_right"
        ]
        
    def set_geometry(self, cx, cy, road_width, cross_size):
        """Set intersection geometry from main.py."""
        self.geometry = {
            "cx": cx,
            "cy": cy,
            "road_width": road_width,
            "cross_size": cross_size
        }

    def get_active_crosswalks(self):
        """Return crosswalk rects where pedestrians are currently crossing.
        Used by vehicles to know where to stop."""
        crosswalks = []
        for p in self.pedestrians:
            if p.crossing and p.is_on_road():
                crosswalks.append({
                    "rect": p.get_crosswalk_rect(),
                    "axis": p.crossing_axis,
                    "pos": (p.x, p.y)
                })
        return crosswalks

    def update(self, dt, light_states, vip_active=False, all_vehicles=None):
        # Spawn new pedestrians
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_pedestrian()
            self.spawn_timer = random.uniform(3, 7)
        
        # Flatten vehicle dict to list for collision checks
        vehicles = []
        if all_vehicles:
            for direction_vehicles in all_vehicles.values():
                vehicles.extend(direction_vehicles)
        
        # Update existing pedestrians with vehicle awareness
        for p in self.pedestrians:
            p.move(dt, light_states, vip_active, vehicles)
        
        # Remove finished pedestrians
        self.pedestrians = [p for p in self.pedestrians if not p.finished]
    
    def spawn_pedestrian(self):
        crossing = random.choice(self.crossing_types)
        direction = random.choice(["positive", "negative"])
        
        new_ped = Pedestrian(crossing, direction, self.geometry)
        self.pedestrians.append(new_ped)

    def draw(self, surface):
        for p in self.pedestrians:
            p.draw(surface)
    
    def get_waiting_count(self):
        """Return number of pedestrians waiting at crossings."""
        return sum(1 for p in self.pedestrians if p.waiting)
