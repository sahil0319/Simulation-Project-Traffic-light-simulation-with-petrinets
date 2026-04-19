# game_modes.py

import pygame

class GameMode:
    def __init__(self, controller, vehicle_manager, pedestrian_manager=None):
        self.controller = controller
        self.vehicle_manager = vehicle_manager
        self.pedestrian_manager = pedestrian_manager
        self.name = "Generic"

    def update(self, dt, police_manager=None):
        pass

    def handle_input(self, event, selected_pole=None):
        pass
    
    def get_light_states(self):
        return {}


class AutomaticMode(GameMode):
    def __init__(self, controller, vehicle_manager, pedestrian_manager=None):
        super().__init__(controller, vehicle_manager, pedestrian_manager)
        self.name = "Automatic"

    def update(self, dt, police_manager=None, accident_manager=None):
        # Check for VIP preemption
        vip_active = police_manager.is_vip_active() if police_manager else False
        blocked_dirs = police_manager.get_blocked_directions() if police_manager else []
        vip_dir = police_manager.get_vip_direction() if police_manager else None
        
        # Combine accident blocked directions
        if accident_manager:
            accident_blocked = accident_manager.get_blocked_directions()
            blocked_dirs = list(set(blocked_dirs + accident_blocked))
        
        # Controller decides everything (with VIP override)
        self.controller.update(dt, self.vehicle_manager, vip_active, blocked_dirs, vip_dir)
        
        # Get active crosswalks for vehicle-pedestrian awareness
        active_crosswalks = []
        if self.pedestrian_manager:
            active_crosswalks = self.pedestrian_manager.get_active_crosswalks()
        
        self.vehicle_manager.update(dt, self.get_light_states(), active_crosswalks)

    def get_light_states(self):
        res = {}
        kp = {v: k for k, v in self.controller.approach_pole_map.items()} # idx -> "N"
        for i, pole in enumerate(self.controller.poles):
            if i in kp:
                res[kp[i]] = pole["state"]
        return res


# game_modes.py

class ManualSurvivalMode(GameMode):
    def __init__(self, controller, vehicle_manager, pedestrian_manager=None):
        super().__init__(controller, vehicle_manager, pedestrian_manager)
        self.name = "Manual Survival"

    def update(self, dt, police_manager=None, accident_manager=None):
        # Check for VIP preemption (forces lights even in manual mode)
        vip_active = police_manager.is_vip_active() if police_manager else False
        blocked_dirs = police_manager.get_blocked_directions() if police_manager else []
        vip_dir = police_manager.get_vip_direction() if police_manager else None
        
        # Combine accident blocked directions
        if accident_manager:
            accident_blocked = accident_manager.get_blocked_directions()
            blocked_dirs = list(set(blocked_dirs + accident_blocked))
        
        if vip_active:
            # VIP overrides manual control
            self.controller.set_vip_preemption(vip_dir, blocked_dirs)
        
        # time passes, but controller does NOT auto-step
        self.controller.advance_time(dt)
        
        active_crosswalks = []
        if self.pedestrian_manager:
            active_crosswalks = self.pedestrian_manager.get_active_crosswalks()
        
        self.vehicle_manager.update(dt, self.get_light_states(), active_crosswalks)

    def handle_input(self, event, selected_pole=None):
        if event.type == pygame.KEYDOWN:
            # SPACE = "try advance the Petri net by one valid transition"
            # (optional) require a selected pole so it feels like "I’m controlling"
            if event.key == pygame.K_SPACE and selected_pole is not None:
                # Map selected pole index back to direction
                # approach_pole_map: {"N": 0, "S": 2, ...}
                direction = None
                for k, v in self.controller.approach_pole_map.items():
                    if v == selected_pole:
                        direction = k
                        break
                
                if direction:
                    # Check if ANY state in this direction is active
                    states = self.controller.places[direction]
                    if any(p.tokens > 0 for p in states.values()):
                         self.controller.step_manual()
                    else:
                         self.controller.force_phase(direction)

            # WASD navigation
            if selected_pole is not None:
                # 0: NW, 1: NE, 2: SW, 3: SE
                if event.key == pygame.K_w: # Up
                    if selected_pole == 2: return 0
                    if selected_pole == 3: return 1
                elif event.key == pygame.K_s: # Down
                    if selected_pole == 0: return 2
                    if selected_pole == 1: return 3
                elif event.key == pygame.K_a: # Left
                    if selected_pole == 1: return 0
                    if selected_pole == 3: return 2
                elif event.key == pygame.K_d: # Right
                    if selected_pole == 0: return 1
                    if selected_pole == 2: return 3

        return selected_pole

    get_light_states = AutomaticMode.get_light_states


class ScenarioChallengeMode(GameMode):
    def __init__(self, controller, vehicle_manager, pedestrian_manager=None):
        super().__init__(controller, vehicle_manager, pedestrian_manager)
        self.name = "Challenge: Rush Hour"
        self.time_elapsed = 0
        
    def update(self, dt, police_manager=None, accident_manager=None):
        self.time_elapsed += dt
        
        # Check for VIP preemption
        vip_active = police_manager.is_vip_active() if police_manager else False
        blocked_dirs = police_manager.get_blocked_directions() if police_manager else []
        vip_dir = police_manager.get_vip_direction() if police_manager else None
        
        # Combine accident blocked directions
        if accident_manager:
            accident_blocked = accident_manager.get_blocked_directions()
            blocked_dirs = list(set(blocked_dirs + accident_blocked))
        
        # Adaptive controller runs (with VIP override)
        self.controller.update(dt, self.vehicle_manager, vip_active, blocked_dirs, vip_dir)
        
        if self.time_elapsed < 30:
            pass
        elif self.time_elapsed < 60:
            if self.vehicle_manager.spawn_timer > 1.0:
                self.vehicle_manager.spawn_timer = 1.0
        else:
             if self.vehicle_manager.spawn_timer > 0.5:
                self.vehicle_manager.spawn_timer = 0.5
                 
        active_crosswalks = []
        if self.pedestrian_manager:
            active_crosswalks = self.pedestrian_manager.get_active_crosswalks()
        
        self.vehicle_manager.update(dt, self.get_light_states(), active_crosswalks)

    get_light_states = AutomaticMode.get_light_states
