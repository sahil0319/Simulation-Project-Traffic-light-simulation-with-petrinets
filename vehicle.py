import pygame
import random
import math
import os

# Vehicle Types and Colors
# We now map these to asset folders
VEHICLE_TYPES = {
    "Compact":   {"folder": "Compact", "length": 40, "speed": 180},
    "Sedan":     {"folder": "Sedan",   "length": 45, "speed": 160},
    "Truck":     {"folder": "Truck",   "length": 60, "speed": 120},
    "Sport":     {"folder": "Sport",   "length": 42, "speed": 220},
    "Coupe":     {"folder": "Coupe",   "length": 42, "speed": 200},
    "VIP":     {"folder": "Sport",   "length": 45, "speed": 170, "priority": True}, # Use Sport for VIP
    "Ambulance": {"folder": "Truck",   "length": 55, "speed": 230, "priority": True} # Emergency Vehicle
}

# Cache for loaded images
SPRITE_CACHE = {}

def load_sprites():
    if SPRITE_CACHE:
        return
    
    base_path = "assets"
    colors = ["blue", "green", "red", "gray", "cream", "white", "black", "yellow"]
    
    for type_name, specs in VEHICLE_TYPES.items():
        folder = specs.get("folder")
        if not folder: continue
        
        path = os.path.join(base_path, folder)
        if not os.path.exists(path):
            continue
            
        SPRITE_CACHE[type_name] = {}
        
        # Try to find images
        for f in os.listdir(path):
            if f.endswith(".png"):
                # assume format: type_color.png
                # e.g. sedan_blue.png
                # Extract color
                parts = f.split('_')
                if len(parts) > 1:
                    color = parts[1].replace(".png", "")
                    img = pygame.image.load(os.path.join(path, f)).convert_alpha()
                    
                    # Assume original sprites are facing UP (or adjust here)
                    # We will resize them to standard width/length (~20x40)
                    # Adjust scale based on specs
                    
                    # Rotate 180 if original assets are facing DOWN? 
                    # Usually top-down assets face DOWN or UP.
                    # We'll rotate them to point UP (0 degrees) as canonical.
                    # Let's assume they face DOWN by default if they are from common packs.
                    # But if they face UP, we keep as is.
                    # We'll assume UP for now.
                    
                    # Resize
                    w, h = img.get_size()
                    # Aspect ratio
                    target_w = 24
                    target_h = specs["length"]
                    img = pygame.transform.scale(img, (target_w, target_h))
                    
                    SPRITE_CACHE[type_name][color] = img

class Vehicle:
    def __init__(self, vehicle_id, approach, road_info, is_ambulance=False):
        # Load sprites if not loaded
        load_sprites()
        
        self.id = vehicle_id
        self.approach = approach  # "N", "S", "E", "W" (where I am coming FROM)
        self.is_ambulance = is_ambulance
        
        if is_ambulance:
            self.type_name = "Ambulance"
        else:
            # exclude Ambulance from random choice
            choices = [k for k in VEHICLE_TYPES.keys() if k != "Ambulance"]
            self.type_name = random.choice(choices)
            
        specs = VEHICLE_TYPES[self.type_name]
        
        self.length = specs["length"]
        self.max_speed = specs["speed"] 
        self.width = 24 # Standard width for sprite
        self.is_vip = specs.get("priority", False)
        
        self.speed = self.max_speed
        self.state = "moving" 
        
        # Pick sprite
        available_colors = list(SPRITE_CACHE.get(self.type_name, {}).keys())
        if available_colors:
            if self.is_ambulance:
                # Try to pick a white or cream truck if available, else random
                if "cream" in available_colors: self.color_name = "cream"
                elif "white" in available_colors: self.color_name = "white"
                else: self.color_name = random.choice(available_colors)
            else:
                self.color_name = random.choice(available_colors)
            self.original_image = SPRITE_CACHE[self.type_name][self.color_name]
        else:
            self.original_image = None
            self.color = (255, 0, 0) # Fallback

        # Initial position
        # Road width 220. Half 110. Center 0.
        # RHT: 
        # N (Southbound): Lane 1 (Normal) near Center. Lane 2 (Emergency) at Far Right (West edge).
        # S (Northbound): Lane 1 (Normal) near Center. Lane 2 (Emergency) at Far Right (East edge).
        # E (Westbound): Lane 1 (Normal) near Center. Lane 2 (Emergency) at Far Right (North edge).
        # W (Eastbound): Lane 1 (Normal) near Center. Lane 2 (Emergency) at Far Right (South edge).
        
        start_x, start_y = road_info["starts"][approach]
        
        # Lane offsets relative to start center
        if approach == "N":
            if self.is_ambulance: self.x = start_x - 35 # Left/Outer (Shoulder)
            else: self.x = start_x + 25 # Right/Inner (Main)
            self.y = start_y
            
        elif approach == "S":
            if self.is_ambulance: self.x = start_x + 35 # Right/Outer (Shoulder)
            else: self.x = start_x - 25 # Left/Inner (Main)
            self.y = start_y
            
        elif approach == "E":
            self.x = start_x
            if self.is_ambulance: self.y = start_y - 35 # Top/Outer
            else: self.y = start_y + 25 # Bottom/Inner
            
        elif approach == "W":
            self.x = start_x
            if self.is_ambulance: self.y = start_y + 35 # Bottom/Outer
            else: self.y = start_y - 25 # Top/Inner
        
        self.rect = pygame.Rect(0, 0, self.width, self.length)
        self.image = self.original_image
        self.update_rect()

    def update_rect(self):
        # Orientation based on approach
        # Assume original image faces UP
        
        rotation = 0
        if self.approach == "N": # From Top (Moving Down) -> Face Down
            rotation = 180
        elif self.approach == "S": # From Bottom (Moving Up) -> Face Up
            rotation = 0
        elif self.approach == "E": # From Right (Moving Left) -> Face Left
            rotation = 90
        elif self.approach == "W": # From Left (Moving Right) -> Face Right
            rotation = -90
            
        if self.original_image:
            self.image = pygame.transform.rotate(self.original_image, rotation)
            self.rect = self.image.get_rect()
        else:
            if self.approach in ["N", "S"]:
                self.rect.size = (self.width, self.length)
            else:
                self.rect.size = (self.length, self.width)
        
        self.rect.center = (self.x, self.y)

    def move(self, dt, vehicle_ahead, stop_line_pos, light_state):
        target_speed = self.max_speed
        
        # Ambulance ignores red lights? Or just stops if blocked?
        # User said "ambulance going in the emergency lane".
        # Emergency lane usually bypasses traffic.
        # So we IGNORE stop lines if we are an ambulance in emergency lane.
        
        dist_to_vehicle = float('inf')
        
        if vehicle_ahead:
            # We only collide with vehicles in OUR lane.
            # vehicle_ahead is passed from manage list.
            # Manager needs to separate lanes!
            # Or we do simple distance check:
            is_same_lane = False
            
            # Simple check: lateral distance
            lat_dist = 0
            if self.approach in ["N", "S"]: lat_dist = abs(self.x - vehicle_ahead.x)
            else: lat_dist = abs(self.y - vehicle_ahead.y)
            
            if lat_dist < 40: # Same lane
                is_same_lane = True
            
            if is_same_lane:
                if self.approach == "N": # Moving Down (+y)
                    # vehicle_ahead.y should be > self.y
                    dist_to_vehicle = vehicle_ahead.y - self.y - (self.length/2 + vehicle_ahead.length/2)
                elif self.approach == "S": # Moving Up (-y)
                    # vehicle_ahead.y should be < self.y
                    dist_to_vehicle = self.y - vehicle_ahead.y - (self.length/2 + vehicle_ahead.length/2)
                elif self.approach == "E": # Moving Left (-x)
                    # vehicle_ahead.x should be < self.x
                    dist_to_vehicle = self.x - vehicle_ahead.x - (self.length/2 + vehicle_ahead.length/2)
                elif self.approach == "W": # Moving Right (+x)
                    # vehicle_ahead.x should be > self.x
                    dist_to_vehicle = vehicle_ahead.x - self.x - (self.length/2 + vehicle_ahead.length/2)
                
                if dist_to_vehicle < 20:
                    target_speed = 0
                elif dist_to_vehicle < 100:
                    target_speed = min(target_speed, vehicle_ahead.speed)

        # Light logic
        # 1. Ambulances ALWAYS ignore lights (Preemption)
        # 2. Normal cars respect light_state (which manager will force to Red if ambulance is near)
        
        if not self.is_ambulance:
            should_stop = False
            dist_to_line = float('inf')
            crossed = False

            if self.approach == "N": 
                dist_to_line = stop_line_pos - self.y
                if self.y > stop_line_pos: crossed = True
            elif self.approach == "S": 
                dist_to_line = self.y - stop_line_pos
                if self.y < stop_line_pos: crossed = True
            elif self.approach == "E": 
                dist_to_line = self.x - stop_line_pos
                if self.x < stop_line_pos: crossed = True
            elif self.approach == "W": 
                dist_to_line = stop_line_pos - self.x
                if self.x > stop_line_pos: crossed = True

            if not crossed and dist_to_line > 0 and dist_to_line < 150:
                if light_state in ["red", "red_yellow", "yellow"]:
                     should_stop = True
            
            if should_stop:
                if dist_to_line < 25:
                    target_speed = 0
                else:
                    target_speed = min(target_speed, (dist_to_line / 120) * self.max_speed)
        
        # Physics
        if self.speed < target_speed:
            self.speed += 200 * dt
        elif self.speed > target_speed:
            self.speed -= 400 * dt
        
        if self.speed < 0: self.speed = 0
        if self.speed > self.max_speed * 1.5: self.speed = self.max_speed * 1.5

        # Move
        move_dist = self.speed * dt
        
        if self.approach == "N": self.y += move_dist
        elif self.approach == "S": self.y -= move_dist
        elif self.approach == "E": self.x -= move_dist
        elif self.approach == "W": self.x += move_dist
            
        self.update_rect()

    def draw(self, surface):
        if self.original_image and self.image:
             surface.blit(self.image, self.rect)
             # Draw separate indicator for ambulance if needed
             if self.is_ambulance:
                 # Blinking light?
                 if (pygame.time.get_ticks() // 200) % 2 == 0:
                     pygame.draw.circle(surface, (255, 50, 50), self.rect.center, 8)
                 else:
                     pygame.draw.circle(surface, (50, 50, 255), self.rect.center, 8)
        else:
            pygame.draw.rect(surface, self.color or (200,200,200), self.rect, border_radius=4)


class VehicleManager:
    def __init__(self, road_info):
        self.vehicles = {
            "N": [], "S": [], "E": [], "W": []
        }
        self.road_info = road_info
        self.spawn_timer = 0.5 # Start fast
        self.next_id = 0

    def update(self, dt, light_states):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            direction = random.choice(["N", "S", "E", "W"])
            
            # 10% chance of Ambulance
            is_ambulance = random.random() < 0.1
            
            self.spawn_vehicle(direction, is_ambulance)
            self.spawn_timer = random.uniform(1.2, 3.0) 

        # Step 1: Detect active Ambulances approaching intersections
        emergency_override = False
        for lane in self.vehicles.values():
            for v in lane:
                if v.is_ambulance:
                    # Check distance to intersection (rough)
                    # Center is (0,0) relative to start if we normalize, but here world coords.
                    # Intersection stops are around (cx-100, cy-100)...
                    # Only override if it's somewhat close or active, not just spawned far away?
                    # Let's say if it exists, SAFETY FIRST -> All stop.
                    emergency_override = True
                    break
            if emergency_override: break

        for direction, lane_vehicles in self.vehicles.items():
            stop_line = self.road_info["stop_lines"][direction]
            
            # If emergency, FORCE RED for normal cars
            if emergency_override:
                light = "red" 
            else:
                light = light_states.get(direction, "red") 
            
            # Filter out distant vehicles
            active_vehicles = []
            for i, vehicle in enumerate(lane_vehicles):
                # Check for vehicle ahead ONLY in same lane
                vehicle_ahead = None
                
                # Check specifically for same-lane predecessor
                # This is O(N^2) worst case but N is small per lane.
                # Since list is ordered by spawn, previous cars are always 'ahead' in array index unless overtaking happens (not here).
                # We just need to find the nearest one in same lane.
                
                # Heuristic: just check the last few? No, linear scan backwards is fine.
                for j in range(i-1, -1, -1):
                    other = lane_vehicles[j]
                    # Check lane alignment
                    lat_dist = 0
                    if direction in ["N", "S"]: lat_dist = abs(vehicle.x - other.x)
                    else: lat_dist = abs(vehicle.y - other.y)
                    
                    if lat_dist < 20: # Same lane
                        vehicle_ahead = other
                        break
                
                vehicle.move(dt, vehicle_ahead, stop_line, light)
                
                # Check bounds (keep if within reasonable area)
                # W=1000, H=700
                if -200 < vehicle.x < 1200 and -200 < vehicle.y < 900:
                    active_vehicles.append(vehicle)
            
            self.vehicles[direction] = active_vehicles

    def spawn_vehicle(self, direction, is_ambulance=False):
        start_x, start_y = self.road_info["starts"][direction]
        target_x, target_y = start_x, start_y
        
        # Consistent offset logic (Must match Vehicle.__init__)
        if direction == "N":
            if is_ambulance: target_x = start_x - 35
            else: target_x = start_x + 25
        elif direction == "S":
            if is_ambulance: target_x = start_x + 35
            else: target_x = start_x - 25
        elif direction == "E":
            if is_ambulance: target_y = start_y - 35
            else: target_y = start_y + 25
        elif direction == "W":
            if is_ambulance: target_y = start_y + 35
            else: target_y = start_y - 25
            
        lane = self.vehicles[direction]
        if lane:
            safe = True
            for last_v in reversed(lane):
                # Lateral check
                lat_dist = 0
                if direction in ["N", "S"]: lat_dist = abs(last_v.x - target_x)
                else: lat_dist = abs(last_v.y - target_y)
                
                if lat_dist < 20: # Same lane collision check
                    long_dist = 0
                    if direction in ["N", "S"]: long_dist = abs(last_v.y - target_y)
                    else: long_dist = abs(last_v.x - target_x)
                    
                    if long_dist < 80:
                        safe = False
                        break
                if not safe: break
            
            if not safe: return

        new_vehicle = Vehicle(self.next_id, direction, self.road_info, is_ambulance)
        self.vehicles[direction].append(new_vehicle)
        self.next_id += 1

    def draw(self, surface):
        for lane in self.vehicles.values():
            for v in lane:
                v.draw(surface)
