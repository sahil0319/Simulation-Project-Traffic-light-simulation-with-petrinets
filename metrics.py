# metrics.py
import pygame

class Metrics:
    def __init__(self):
        self.total_cars_exited = 0
        self.max_queue_length = 0
        self.total_wait_time = 0
        self.start_time = pygame.time.get_ticks()
        
        # Accident stats
        self.total_accidents = 0
        self.total_fatalities = 0
        self.active_accidents = 0
        
    def update(self, vehicle_manager, accident_manager=None):
        # Scan queues
        current_max_q = 0
        for direction, lane in vehicle_manager.vehicles.items():
            if len(lane) > current_max_q:
                current_max_q = len(lane)
            
            # Simple wait time heuristic:
            # If car speed is near 0, add to wait time?
            # Or just track total waiting cars.
            pass
            
        if current_max_q > self.max_queue_length:
            self.max_queue_length = current_max_q
        
        # Update accident stats
        if accident_manager:
            self.total_accidents = accident_manager.total_accidents
            self.total_fatalities = accident_manager.total_fatalities
            self.active_accidents = accident_manager.active_accident_count

    def draw(self, surface, font):
        # Draw overlay
        # Background — taller if we have accident stats
        panel_h = 140 if self.total_accidents > 0 else 110
        bg_rect = pygame.Rect(10, 80, 240, panel_h)
        pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), bg_rect, 2, border_radius=8)
        
        # Text
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0
        
        lines = [
            (f"Time: {elapsed:.1f}s", (255, 255, 255)),
            (f"Max Queue: {self.max_queue_length}", (255, 255, 255)),
            (f"Throughput: {self.total_cars_exited or 0}", (255, 255, 255)),
        ]
        
        if self.total_accidents > 0:
            lines.append((f"Accidents: {self.total_accidents}  Deaths: {self.total_fatalities}", (255, 120, 120)))
            if self.active_accidents > 0:
                lines.append((f"Active Accidents: {self.active_accidents}", (255, 80, 80)))
        
        y = 90
        for line_text, color in lines:
            txt = font.render(line_text, True, color)
            surface.blit(txt, (20, y))
            y += 25
