class AutonomousController:
    def __init__(self, poles, approach_pole_map):
        self.poles = poles
        self.approach_pole = approach_pole_map
        
        self.AUTO_ORDER = ["N", "E", "S", "W"]
        self.T_GREEN = 5.0
        self.T_SWITCH = 3.0
        
        self.auto_idx = 0
        self.auto_phase = "green"  # "green" or "switch"
        self.auto_timer = self.T_GREEN

    def set_all_red(self):
        for p in self.poles:
            p["state"] = "red"

    def set_approach_state(self, approach, state):
        self.poles[self.approach_pole[approach]]["state"] = state

    def apply_states(self):
        """
        Applies states based on auto_idx + auto_phase.
        In 'green': current approach is green, all others red.
        In 'switch': current is yellow, next is red+yellow, others red.
        """
        curr = self.AUTO_ORDER[self.auto_idx]
        nxt = self.AUTO_ORDER[(self.auto_idx + 1) % len(self.AUTO_ORDER)]

        self.set_all_red()

        if self.auto_phase == "green":
            self.set_approach_state(curr, "green")
        else:  # "switch"
            self.set_approach_state(curr, "yellow")
            self.set_approach_state(nxt, "red_yellow")

    def update(self, dt):
        """
        Call every frame in autonomas mode.
        dt = seconds since last frame.
        """
        self.auto_timer -= dt
        if self.auto_timer > 0:
            return

        # phase ended -> advance
        if self.auto_phase == "green":
            self.auto_phase = "switch"
            self.auto_timer = self.T_SWITCH
        else:
            # switch finished -> next approach gets green
            self.auto_phase = "green"
            self.auto_idx = (self.auto_idx + 1) % len(self.AUTO_ORDER)
            self.auto_timer = self.T_GREEN
