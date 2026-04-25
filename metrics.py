# metrics.py
import pygame

class Metrics:
    def __init__(self):
        self.total_cars_exited = 0
        self.max_queue_length = 0
        self.total_wait_time = 0
        self.elapsed = 0.0
        
        # Accident stats
        self.total_accidents = 0
        self.total_fatalities = 0
        self.active_accidents = 0
        
    def update(self, dt, vehicle_manager, accident_manager=None):
        self.elapsed += dt
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
        # Background — taller if we have accident stats
        panel_h = 140 if self.total_accidents > 0 else 110
        bg_rect = pygame.Rect(5, 75, 280, panel_h)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 120), bg_surf.get_rect(), border_radius=8)
        pygame.draw.rect(bg_surf, (255, 255, 255, 100), bg_surf.get_rect(), 2, border_radius=8)
        surface.blit(bg_surf, bg_rect.topleft)
        
        # Text
        hrs = int(self.elapsed // 3600)
        mins = int((self.elapsed % 3600) // 60)
        secs = self.elapsed % 60
        if hrs > 0:
            time_str = f"Time: {hrs}h {mins}m {secs:.1f}s"
        elif mins > 0:
            time_str = f"Time: {mins}m {secs:.1f}s"
        else:
            time_str = f"Time: {secs:.1f}s"
            
        lines = [
            (time_str, (255, 255, 255)),
            (f"Max Queue: {self.max_queue_length}", (255, 255, 255))
        ]
        
        if self.total_accidents > 0:
            lines.append((f"Accidents: {self.total_accidents}  Deaths: {self.total_fatalities}", (255, 120, 120)))
            if self.active_accidents > 0:
                lines.append((f"Active Accidents: {self.active_accidents}", (255, 80, 80)))
        
        y = 85
        for line_text, color in lines:
            txt = font.render(line_text, True, color)
            surface.blit(txt, (15, y))
            y += 25
