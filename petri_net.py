# petri_net.py

import time

class Place:
    def __init__(self, name, tokens=0, current_time=0):
        self.name = name
        self.tokens = tokens
        self.last_arrival_time = current_time

    def add_token(self, count=1, current_time=0):
        self.tokens += count
        if count > 0:
            self.last_arrival_time = current_time

    def remove_token(self, count=1):
        if self.tokens >= count:
            self.tokens -= count
            return True
        return False

    def __repr__(self):
        return f"Place({self.name}, tokens={self.tokens})"


class Transition:
    def __init__(self, name, min_time=0, max_time=float('inf')):
        self.name = name
        self.min_time = min_time  # Minimum duration tokens must stay in input places
        self.max_time = max_time  
        self.inputs = {}  # Map Place -> token count needed
        self.outputs = {} # Map Place -> token count produced
        self.last_fired_time = 0

    def add_input(self, place, weight=1):
        self.inputs[place] = weight

    def add_output(self, place, weight=1):
        self.outputs[place] = weight

    def can_fire(self, current_time=None, ignore_time=False):
        # Check token requirements and timing
        for place, weight in self.inputs.items():
            if place.tokens < weight:
                return False
            
            # Check timing relative to token arrival
            if not ignore_time and current_time is not None:
                duration = current_time - place.last_arrival_time
                if duration < self.min_time:
                    return False
        
        return True

    def fire(self, current_time=0):
         # Note: We don't check can_fire here again to allow 'force' logic if caller checked.
         # But usually caller checks.
        
        # Consume tokens
        for place, weight in self.inputs.items():
            place.remove_token(weight)

        # Produce tokens
        for place, weight in self.outputs.items():
            place.add_token(weight, current_time)
        
        if current_time is not None:
            self.last_fired_time = current_time
            
        return True

    def __repr__(self):
        return f"Transition({self.name})"


class PetriNet:
    def __init__(self):
        self.places = {}
        self.transitions = []
        self.current_time = 0

    def add_place(self, name, tokens=0):
        p = Place(name, tokens, self.current_time)
        self.places[name] = p
        return p

    def add_transition(self, name, min_time=0, max_time=float('inf')):
        t = Transition(name, min_time, max_time)
        self.transitions.append(t)
        return t

    def update(self, dt):
        self.current_time += dt
        fired_any = False
        
        # Greedy firing
        for t in self.transitions:
            if t.can_fire(self.current_time):
                t.fire(self.current_time)
                # Return immediately to avoid cascading multiple phases in one frame 
                # (unless we want that, but for traffic lights we usually want distinct phases)
                # With token timing, cascading is prevented automatically by min_time!
                # But to be safe and consistent with user edits:
                return True 
                
        return False
        
    def force_step(self):
        """Find the first transition that HAS TOKENS (ignoring time) and fire it."""
        for t in self.transitions:
            if t.can_fire(self.current_time, ignore_time=True):
                 t.fire(self.current_time)
                 return True
        return False

    def get_token_count(self, place_name):
        if place_name in self.places:
            return self.places[place_name].tokens
        return 0
