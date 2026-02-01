from petri_net import PetriNet

class AdaptiveController:
    def __init__(self, poles, approach_pole_map):
        self.net = PetriNet()
        self.poles = poles
        self.approach_pole_map = approach_pole_map
        self.current_phase = "N" # Start with North Green
        
        # Build the Petri Net for 4-way intersection (Simple Cycle)
        # Places: P_N_Green, P_E_Green, P_S_Green, P_W_Green
        # Transitions: T_N_to_E, T_E_to_S, T_S_to_W, T_W_to_N
        
        self.p_n = self.net.add_place("P_N_Green", 1) # Start with token here
        self.p_e = self.net.add_place("P_E_Green", 0)
        self.p_s = self.net.add_place("P_S_Green", 0)
        self.p_w = self.net.add_place("P_W_Green", 0)
        
        # Transitions with min times (green light duration)
        # We start with fixed times, but update() will adjust them adaptively
        self.t_n_e = self.net.add_transition("T_N->E", min_time=5)
        self.t_n_e.add_input(self.p_n)
        self.t_n_e.add_output(self.p_e)
        
        self.t_e_s = self.net.add_transition("T_E->S", min_time=5)
        self.t_e_s.add_input(self.p_e)
        self.t_e_s.add_output(self.p_s)
        
        self.t_s_w = self.net.add_transition("T_S->W", min_time=5)
        self.t_s_w.add_input(self.p_s)
        self.t_s_w.add_output(self.p_w)
        
        self.t_w_n = self.net.add_transition("T_W->N", min_time=5)
        self.t_w_n.add_input(self.p_w)
        self.t_w_n.add_output(self.p_n)

    def update(self, dt, vehicle_manager):
        # Update Petri Net
        fired = self.net.update(dt)
        
        if fired:
            self.apply_states()
            
        # Adaptive Logic: Adjust min_time based on queue length
        # This is a simple implementation: 
        # If current green lane has many cars, extend its time (by not checking 'min_time' but 'dynamic_time')
        # OR: we just blindly update min_time for next round.
        
        # Let's simple-adjust the min_time of the transition OUT of the current state
        # e.g., if N is green (token in P_N), we look at T_N->E min_time.
        
        q_n = len(vehicle_manager.vehicles["N"])
        q_e = len(vehicle_manager.vehicles["E"])
        q_s = len(vehicle_manager.vehicles["S"])
        q_w = len(vehicle_manager.vehicles["W"])
        
        # Base time + 1s per car, max 15s
        self.t_n_e.min_time = min(5 + q_n * 1.0, 15)
        self.t_e_s.min_time = min(5 + q_e * 1.0, 15)
        self.t_s_w.min_time = min(5 + q_s * 1.0, 15)
        self.t_w_n.min_time = min(5 + q_w * 1.0, 15)

    def apply_states(self):
        # Map tokens to physical lights
        # Reset all to RED first
        for pole in self.poles:
            pole["state"] = "red"
            
        # Set GREEN based on tokens
        # Note: In real PN, we might have yellow states. 
        # For simplicity here, we jump Green->Red (Yellow can be added as intermediate places)
        
        if self.p_n.tokens > 0:
            self.set_pole("N", "green")
            self.current_phase = "N"
        if self.p_e.tokens > 0:
            self.set_pole("E", "green")
            self.current_phase = "E"
        if self.p_s.tokens > 0:
            self.set_pole("S", "green")
            self.current_phase = "S"
        if self.p_w.tokens > 0:
            self.set_pole("W", "green")
            self.current_phase = "W"

    def set_pole(self, direction, state):
        idx = self.approach_pole_map.get(direction)
        if idx is not None:
            self.poles[idx]["state"] = state

    def force_phase(self, direction):
        """Manually force the traffic light phase to the given direction."""
        # Clear all tokens
        self.p_n.tokens = 0
        self.p_e.tokens = 0
        self.p_s.tokens = 0
        self.p_w.tokens = 0
        
        # Set token for the target direction
        if direction == "N": self.p_n.add_token()
        elif direction == "E": self.p_e.add_token()
        elif direction == "S": self.p_s.add_token()
        elif direction == "W": self.p_w.add_token()
        
        # Apply immediately
        self.apply_states()
