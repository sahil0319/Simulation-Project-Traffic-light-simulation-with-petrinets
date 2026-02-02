# pedestrian.py

import pygame
import random

class Pedestrian:
    def __init__(self, start_idx, end_idx, waypoints, road_info):
        self.waypoints = waypoints
        self.current_target_idx = 0
        self.x, self.y = waypoints[0]
        self.speed = random.uniform(20, 40) # Pixels per second
        self.radius = 6
        self.color = (200, 200, 255)
        self.waiting = False
        
        # We need to know which light controls my crossing
        # Simplified: if my path crosses a road, I check that road's light
        # For now, we'll assume waypoints are [start, curb_stop, end_of_cross, final]
        # This is a bit complex without a graph, so we'll do simple state machine
        self.state = "walking_to_curb" 
    
    def move(self, dt, light_states, road_info):
        if self.current_target_idx >= len(self.waypoints):
            return # Arrived
        
        target = self.waypoints[self.current_target_idx]
        dx = target[0] - self.x
        dy = target[1] - self.y
        dist = (dx**2 + dy**2)**0.5
        
        if dist < 5:
            self.current_target_idx += 1
            if self.current_target_idx >= len(self.waypoints):
                return
            target = self.waypoints[self.current_target_idx]
            dx = target[0] - self.x
            dy = target[1] - self.y
            dist = (dx**2 + dy**2)**0.5

        # Check crossing logic
        # If we are at the curb (say index 1), check light
        if self.current_target_idx == 1: # Assuming index 1 is the point BEFORE crossing
            # Determine which light to check
            # This requires 'road_info' to map waypoints to lights.
            # Simplified: we just stop if we are "waiting"
            pass 

        # Normalize and move
        if dist > 0:
            nx = dx / dist
            ny = dy / dist
            self.x += nx * self.speed * dt
            self.y += ny * self.speed * dt

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)


class PedestrianManager:
    def __init__(self, road_info):
        self.pedestrians = []
        self.road_info = road_info
        self.spawn_timer = 0
        
        # Define some simple paths (corners)
        # 0: NW, 1: NE, 2: SE, 3: SW
        # Paths: NW->NE (Top crossing), NE->SE (Right crossing), etc.
        # We need actual coordinates from main.py's geometry.
        # For now, we'll wait for main.py integration to get real coords.
        self.paths = [] 

    def update(self, dt, light_states):
        pass # To be implemented once geometry is passed

    def draw(self, surface):
        for p in self.pedestrians:
            p.draw(surface)
