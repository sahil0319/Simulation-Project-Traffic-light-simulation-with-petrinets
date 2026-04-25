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
        geometry: dict with cx, cy, road_width, cross_size, screen_width, screen_height
        """
        self.crossing_type = crossing_type
        self.direction = direction
        self.geometry = geometry
        
        cx = geometry["cx"]
        cy = geometry["cy"]
        road_w = geometry["road_width"]
        cross_s = geometry["cross_size"]
        screen_w = geometry.get("screen_width", 1000)
        screen_h = geometry.get("screen_height", 700)
        
        # Waypoints: [spawn_edge, sidewalk_approach, curb_wait, cross_end, sidewalk_exit, dest_edge]
        # Pedestrian spawns at screen edge, walks along sidewalk to crosswalk,
        # waits for safe signal, crosses, then walks to opposite screen edge.
        
        curb_margin = 5       # Stop just before the road edge
        crosswalk_offset = 40  # Crosswalk distance from intersection edge
        sidewalk_offset = 45   # Distance from road edge on the sidewalk side
        edge_margin = -50      # Spawn slightly off screen
        
        if crossing_type == "horizontal_top":  # Crosses top of vertical road (NW <-> NE)
            y_cross = cy - cross_s // 2 - crosswalk_offset
            if direction == "positive":  # West to East
                self.waypoints = [
                    (edge_margin, y_cross),                                 # Spawn at left screen edge
                    (cx - road_w // 2 - sidewalk_offset, y_cross),          # Walk along sidewalk
                    (cx - road_w // 2 - curb_margin, y_cross),              # Wait at west curb
                    (cx + road_w // 2 + curb_margin, y_cross),              # Reach east curb
                    (cx + road_w // 2 + sidewalk_offset, y_cross),          # Walk onto NE sidewalk
                    (screen_w + abs(edge_margin), y_cross),                 # Walk to right screen edge
                ]
            else:  # East to West
                self.waypoints = [
                    (screen_w + abs(edge_margin), y_cross),
                    (cx + road_w // 2 + sidewalk_offset, y_cross),
                    (cx + road_w // 2 + curb_margin, y_cross),
                    (cx - road_w // 2 - curb_margin, y_cross),
                    (cx - road_w // 2 - sidewalk_offset, y_cross),
                    (edge_margin, y_cross),
                ]
            self.check_directions = ["N", "S"]  # Check vertical traffic lights
            self.crossing_axis = "horizontal"
            self.road_min = cx - road_w // 2
            self.road_max = cx + road_w // 2
            self.cross_y = y_cross
            self.cross_x = None
            self.curb_waypoint_idx = 2  # Index of curb wait waypoint
            
        elif crossing_type == "horizontal_bottom":  # SW <-> SE
            y_cross = cy + cross_s // 2 + crosswalk_offset
            if direction == "positive":
                self.waypoints = [
                    (edge_margin, y_cross),
                    (cx - road_w // 2 - sidewalk_offset, y_cross),
                    (cx - road_w // 2 - curb_margin, y_cross),
                    (cx + road_w // 2 + curb_margin, y_cross),
                    (cx + road_w // 2 + sidewalk_offset, y_cross),
                    (screen_w + abs(edge_margin), y_cross),
                ]
            else:
                self.waypoints = [
                    (screen_w + abs(edge_margin), y_cross),
                    (cx + road_w // 2 + sidewalk_offset, y_cross),
                    (cx + road_w // 2 + curb_margin, y_cross),
                    (cx - road_w // 2 - curb_margin, y_cross),
                    (cx - road_w // 2 - sidewalk_offset, y_cross),
                    (edge_margin, y_cross),
                ]
            self.check_directions = ["N", "S"]
            self.crossing_axis = "horizontal"
            self.road_min = cx - road_w // 2
            self.road_max = cx + road_w // 2
            self.cross_y = y_cross
            self.cross_x = None
            self.curb_waypoint_idx = 2
            
        elif crossing_type == "vertical_left":  # NW <-> SW
            x_cross = cx - cross_s // 2 - crosswalk_offset
            if direction == "positive":  # North to South
                self.waypoints = [
                    (x_cross, edge_margin),
                    (x_cross, cy - road_w // 2 - sidewalk_offset),
                    (x_cross, cy - road_w // 2 - curb_margin),
                    (x_cross, cy + road_w // 2 + curb_margin),
                    (x_cross, cy + road_w // 2 + sidewalk_offset),
                    (x_cross, screen_h + abs(edge_margin)),
                ]
            else:
                self.waypoints = [
                    (x_cross, screen_h + abs(edge_margin)),
                    (x_cross, cy + road_w // 2 + sidewalk_offset),
                    (x_cross, cy + road_w // 2 + curb_margin),
                    (x_cross, cy - road_w // 2 - curb_margin),
                    (x_cross, cy - road_w // 2 - sidewalk_offset),
                    (x_cross, edge_margin),
                ]
            self.check_directions = ["E", "W"]
            self.crossing_axis = "vertical"
            self.road_min = cy - road_w // 2
            self.road_max = cy + road_w // 2
            self.cross_x = x_cross
            self.cross_y = None
            self.curb_waypoint_idx = 2
            
        elif crossing_type == "vertical_right":  # NE <-> SE
            x_cross = cx + cross_s // 2 + crosswalk_offset
            if direction == "positive":
                self.waypoints = [
                    (x_cross, edge_margin),
                    (x_cross, cy - road_w // 2 - sidewalk_offset),
                    (x_cross, cy - road_w // 2 - curb_margin),
                    (x_cross, cy + road_w // 2 + curb_margin),
                    (x_cross, cy + road_w // 2 + sidewalk_offset),
                    (x_cross, screen_h + abs(edge_margin)),
                ]
            else:
                self.waypoints = [
                    (x_cross, screen_h + abs(edge_margin)),
                    (x_cross, cy + road_w // 2 + sidewalk_offset),
                    (x_cross, cy + road_w // 2 + curb_margin),
                    (x_cross, cy - road_w // 2 - curb_margin),
                    (x_cross, cy - road_w // 2 - sidewalk_offset),
                    (x_cross, edge_margin),
                ]
            self.check_directions = ["E", "W"]
            self.crossing_axis = "vertical"
            self.road_min = cy - road_w // 2
            self.road_max = cy + road_w // 2
            self.cross_x = x_cross
            self.cross_y = None
            self.curb_waypoint_idx = 2
        
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
    
    def _get_vehicle_avoidance(self, vehicles):
        """Calculate lateral avoidance vector to walk around stopped/slow vehicles."""
        if not vehicles or not self.crossing:
            return 0, 0
        
        avoidance_x = 0
        avoidance_y = 0
        ped_rect = pygame.Rect(self.x - 8, self.y - 8, 16, 16)
        
        for v in vehicles:
            # Only avoid vehicles that are near our path
            dx = self.x - v.x
            dy = self.y - v.y
            dist_sq = dx * dx + dy * dy
            
            # Avoidance radius — react within 40 pixels
            avoidance_radius = 40
            if dist_sq > avoidance_radius * avoidance_radius:
                continue
            if dist_sq < 1:
                dist_sq = 1
            
            dist = math.sqrt(dist_sq)
            
            # Repulsion force inversely proportional to distance
            # Push perpendicular to our crossing direction
            strength = (avoidance_radius - dist) / avoidance_radius * 60
            
            if self.crossing_axis == "horizontal":
                # We're moving horizontally; dodge vertically
                if dy == 0:
                    dy = random.choice([-1, 1])
                avoidance_y += (dy / abs(dy)) * strength
            else:
                # We're moving vertically; dodge horizontally
                if dx == 0:
                    dx = random.choice([-1, 1])
                avoidance_x += (dx / abs(dx)) * strength
        
        return avoidance_x, avoidance_y
    
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
        
        # === PHASE: Walking to curb (waypoints 0 -> curb_waypoint_idx) ===
        # Just walk normally, no checks needed
        
        # === PHASE: At curb, wait for safe crossing ===
        if self.current_target_idx == self.curb_waypoint_idx and dist < 8:
            if not self.can_cross(light_states, vip_active, vehicles):
                self.waiting = True
                self.wait_time += dt
                return
            else:
                self.waiting = False
                self.crossing = True  # Start crossing!
        
        # === PHASE: Crossing the road ===
        # Once crossing, NEVER stop. Commit to crossing.
        # Use faster speed while on road.
        
        # === PHASE: Reached other side ===
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
            
            # Check if we just finished crossing (reached post-cross sidewalk waypoint)
            if self.current_target_idx >= self.curb_waypoint_idx + 2:
                self.crossing = False
        
        # Move towards target
        if dist > 0:
            nx = dx / dist
            ny = dy / dist
            
            # Use faster speed while crossing the road
            current_speed = self.crossing_speed if self.crossing else self.speed
            step = current_speed * dt
            
            if step >= dist:
                # Snap to waypoint to avoid high-speed oscillation
                self.x = target[0]
                self.y = target[1]
            else:
                move_x = nx * step
                move_y = ny * step
                
                # Add vehicle avoidance if crossing
                if self.crossing and vehicles:
                    avoid_x, avoid_y = self._get_vehicle_avoidance(vehicles)
                    move_x += avoid_x * dt
                    move_y += avoid_y * dt
                
                self.x += move_x
                self.y += move_y
                
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
    def __init__(self, road_info, geometry=None, stats_tracker=None):
        self.pedestrians = []
        self.road_info = road_info
        self.spawn_rate_ppm = 30  # Persons per minute (default)
        self.stats_tracker = stats_tracker
        
        # Use exponential distribution for spawn timer
        if self.spawn_rate_ppm > 0:
            self.spawn_timer = random.expovariate(self.spawn_rate_ppm / 60.0)
        else:
            self.spawn_timer = float('inf')
        
        # Default geometry (will be set from main.py)
        self.geometry = geometry or {
            "cx": 500,
            "cy": 350,
            "road_width": 220,
            "cross_size": 260,
            "screen_width": 1000,
            "screen_height": 700
        }
        
        # Crossing types available
        self.crossing_types = [
            "horizontal_top",
            "horizontal_bottom", 
            "vertical_left",
            "vertical_right"
        ]
        
    def set_geometry(self, cx, cy, road_width, cross_size, screen_width=1000, screen_height=700):
        """Set intersection geometry from main.py."""
        self.geometry = {
            "cx": cx,
            "cy": cy,
            "road_width": road_width,
            "cross_size": cross_size,
            "screen_width": screen_width,
            "screen_height": screen_height
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
        # Handle case where rate changed from 0 to > 0
        if self.spawn_timer == float('inf') and self.spawn_rate_ppm > 0:
            self.spawn_timer = random.expovariate(self.spawn_rate_ppm / 60.0)
            
        # Spawn new pedestrians
        self.spawn_timer -= dt
        while self.spawn_timer <= 0 and self.spawn_rate_ppm > 0:
            self.spawn_pedestrian()
            self.spawn_timer += random.expovariate(self.spawn_rate_ppm / 60.0)
            
        if self.spawn_rate_ppm == 0:
            self.spawn_timer = float('inf')
        
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

        if self.stats_tracker:
            self.stats_tracker.record_pedestrian_spawn(crossing, direction)

    def draw(self, surface):
        for p in self.pedestrians:
            p.draw(surface)
    
    def get_waiting_count(self):
        """Return number of pedestrians waiting at crossings."""
        return sum(1 for p in self.pedestrians if p.waiting)
