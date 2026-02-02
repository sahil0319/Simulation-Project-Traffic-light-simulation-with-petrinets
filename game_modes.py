# game_modes.py

import pygame

class GameMode:
    def __init__(self, controller, vehicle_manager):
        self.controller = controller
        self.vehicle_manager = vehicle_manager
        self.name = "Generic"

    def update(self, dt):
        pass

    def handle_input(self, event, selected_pole=None):
        pass


class AutomaticMode(GameMode):
    def __init__(self, controller, vehicle_manager):
        super().__init__(controller, vehicle_manager)
        self.name = "Automatic"

    def update(self, dt):
        # Controller decides everything
        self.controller.update(dt, self.vehicle_manager)
        self.vehicle_manager.update(dt, self.get_light_states())

    def get_light_states(self):
        res = {}
        kp = {v: k for k, v in self.controller.approach_pole_map.items()} # idx -> "N"
        for i, pole in enumerate(self.controller.poles):
            if i in kp:
                res[kp[i]] = pole["state"]
        return res


# game_modes.py

class ManualSurvivalMode(GameMode):
    def __init__(self, controller, vehicle_manager):
        super().__init__(controller, vehicle_manager)
        self.name = "Manual Survival"

    def update(self, dt):
        # time passes, but controller does NOT auto-step
        self.controller.advance_time(dt)
        self.vehicle_manager.update(dt, self.get_light_states())

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
    def __init__(self, controller, vehicle_manager):
        super().__init__(controller, vehicle_manager)
        self.name = "Challenge: Rush Hour"
        self.time_elapsed = 0
        
    def update(self, dt):
        self.time_elapsed += dt
        
        # Adaptive controller runs
        self.controller.update(dt, self.vehicle_manager)
        
        if self.time_elapsed < 30:
            pass
        elif self.time_elapsed < 60:
            if self.vehicle_manager.spawn_timer > 1.0:
                self.vehicle_manager.spawn_timer = 1.0
        else:
             if self.vehicle_manager.spawn_timer > 0.5:
                self.vehicle_manager.spawn_timer = 0.5
                 
        self.vehicle_manager.update(dt, self.get_light_states())

    get_light_states = AutomaticMode.get_light_states
