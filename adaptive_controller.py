# adaptive_controller.py
from petri_net import PetriNet

class AdaptiveController:
    def __init__(self, poles, approach_pole_map):
        self.net = PetriNet()
        self.poles = poles
        self.approach_pole_map = approach_pole_map
        self.active_direction = None # Currently Green direction
        self.next_direction = None   # Direction transitioning to Green
        
        # --- Petri Net Structure: Decoupled Lanes ---
        # For each direction (N, E, S, W), we need:
        # 1. P_Green: Active Green state.
        # 2. P_Yellow: Active Yellow state (transitioning to Red).
        # 3. P_RedYellow: Active Red+Yellow state (transitioning to Green).
        
        self.places = {}
        self.transitions = {}
        
        for d in ["N", "E", "S", "W"]:
            # Places
            p_green = self.net.add_place(f"P_{d}_Green", 0)
            p_yellow = self.net.add_place(f"P_{d}_Yellow", 0)
            p_red_yellow = self.net.add_place(f"P_{d}_RedYellow", 0)
            
            self.places[d] = {
                "green": p_green,
                "yellow": p_yellow,
                "red_yellow": p_red_yellow
            }
            
            # Transitions
            
            # 1. End Green -> Start Yellow
            t_end_green = self.net.add_transition(f"T_{d}_EndGreen", min_time=5) # Adaptive time
            t_end_green.add_input(p_green)
            t_end_green.add_output(p_yellow)
            
            # 2. End Yellow -> Red (Consumes token)
            t_end_yellow = self.net.add_transition(f"T_{d}_EndYellow", min_time=3.0) 
            t_end_yellow.add_input(p_yellow)
            # Output is nothing (token consumed, light becomes Red)
            
            # 3. End RedYellow -> Green
            t_end_ry = self.net.add_transition(f"T_{d}_EndRY", min_time=3.0) 
            t_end_ry.add_input(p_red_yellow)
            t_end_ry.add_output(p_green)
            
            self.transitions[d] = {
                "t_end_green": t_end_green,
                "t_end_yellow": t_end_yellow,
                "t_end_ry": t_end_ry
            }
            
    def update(self, dt, vehicle_manager):
        # 1. Update Petri Net
        fired = self.net.update(dt)
        if fired:
            self.apply_states()
        
        # 2. Scheduler & Overlap Logic
        # Scan current states
        green_dir = None
        yellow_dir = None
        ry_dir = None
        
        for d in ["N", "E", "S", "W"]:
            if self.places[d]["green"].tokens > 0:
                green_dir = d
            if self.places[d]["yellow"].tokens > 0:
                yellow_dir = d
            if self.places[d]["red_yellow"].tokens > 0:
                ry_dir = d
        
        # Update active direction tracker
        if green_dir:
            self.active_direction = green_dir
            
        # Case A: Transition Overlap
        # If we are in Yellow phase, and NO RedYellow phase is active, initiate the next phase.
        # We also ensure NO Green is active (e.g. from a race condition or manual override).
        if yellow_dir and not ry_dir and not green_dir:
            exclude_list = [yellow_dir]
            best_dir = self.select_next_phase(vehicle_manager, exclude=exclude_list)
            
            if best_dir:
                # Start Red-Yellow for next direction
                p_ry = self.places[best_dir]["red_yellow"]
                p_ry.add_token(1, current_time=self.net.current_time)
                
                # Setup Green duration for future
                q_len, max_wait = vehicle_manager.get_lane_info(best_dir)
                t_green = self.transitions[best_dir]["t_end_green"]
                t_green.min_time = min(5 + q_len * 1.0, 15)
                
                self.apply_states()
        
        # Case B: Bootstrap / All Red / Recovery
        # If system is empty (no Green, no Yellow, no RY), pick a lane.
        elif not green_dir and not yellow_dir and not ry_dir:
             best_dir = self.select_next_phase(vehicle_manager, exclude=[])
             if best_dir:
                 self.places[best_dir]["red_yellow"].add_token(1, current_time=self.net.current_time)
                 
                 q_len, max_wait = vehicle_manager.get_lane_info(best_dir)
                 t_green = self.transitions[best_dir]["t_end_green"]
                 t_green.min_time = min(5 + q_len * 1.0, 15)
                 
                 self.apply_states()

    def select_next_phase(self, vehicle_manager, exclude=[]):
        """Standard scheduler: Queue Length > Wait Time."""
        candidates = []
        for d in ["N", "E", "S", "W"]:
            if d in exclude: continue
            
            q_len, max_wait = vehicle_manager.get_lane_info(d)
            if q_len > 0:
                candidates.append({
                    "dir": d,
                    "len": q_len,
                    "wait": max_wait
                })
        
        if not candidates:
            return None
            
        # Sort by Length (Desc), then Wait Time (Desc)
        candidates.sort(key=lambda x: (x["len"], x["wait"]), reverse=True)
        return candidates[0]["dir"]
        
    def force_phase(self, direction):
        """Bootstrap or Manual Override."""
        # Clear all tokens
        for d in self.places:
            self.places[d]["green"].tokens = 0
            self.places[d]["yellow"].tokens = 0
            self.places[d]["red_yellow"].tokens = 0
            
        # Set target to Green
        p = self.places[direction]["red_yellow"]
        p.tokens = 0
        p.add_token(1, current_time=self.net.current_time)

        self.active_direction = direction
        self.next_direction = None
        
        self.apply_states()

    def step_manual(self):
        # Force current Green -> Yellow immediately
        # Or force next phase? Manual is tricky with dynamic logic.
        # Let's just force the Petri Net to step whatever is enabled.
        fired = self.net.force_step()
        if fired:
            self.apply_states()
        return fired

    def advance_time(self, dt):
        self.net.current_time += dt

    def apply_states(self):
        # Default all to Red
        for pole in self.poles:
            pole["state"] = "red"
            
        # Check places
        for d in ["N", "E", "S", "W"]:
            state = "red"
            if self.places[d]["green"].tokens > 0:
                state = "green"
            elif self.places[d]["yellow"].tokens > 0:
                state = "yellow"
            elif self.places[d]["red_yellow"].tokens > 0:
                state = "red_yellow"
            
            if state != "red":
                self.set_pole(d, state)
                
    def set_pole(self, direction, state):
        idx = self.approach_pole_map.get(direction)
        if idx is not None:
            self.poles[idx]["state"] = state
