import pygame

class Metrics:
    def __init__(self):
        self.total_cars_exited = 0
        self.max_queue_length = 0
        self.total_wait_time = 0
        self.start_time = pygame.time.get_ticks()
        
    def update(self, vehicle_manager):
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

    def draw(self, surface, font):
        # Draw overlay
        # Background
        bg_rect = pygame.Rect(10, 80, 220, 110)
        pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), bg_rect, 2, border_radius=8)
        
        # Text
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000.0
        
        lines = [
            f"Time: {elapsed:.1f}s",
            f"Max Queue: {self.max_queue_length}",
            f"Total Throughput: {self.total_cars_exited or 0}",
            # f"Avg Speed: {0}"
        ]
        
        y = 90
        for line in lines:
            txt = font.render(line, True, (255, 255, 255))
            surface.blit(txt, (20, y))
            y += 25
