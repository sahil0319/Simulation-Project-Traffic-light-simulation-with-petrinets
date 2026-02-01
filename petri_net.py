import time

class Place:
    def __init__(self, name, tokens=0):
        self.name = name
        self.tokens = tokens

    def add_token(self, count=1):
        self.tokens += count

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
        self.min_time = min_time  # Minimum time signals must stay in state
        self.max_time = max_time  # Maximum time before forced transition (not always strictly enforced depending on logic)
        self.inputs = {}  # Map Place -> token count needed
        self.outputs = {} # Map Place -> token count produced
        self.last_fired_time = 0

    def add_input(self, place, weight=1):
        self.inputs[place] = weight

    def add_output(self, place, weight=1):
        self.outputs[place] = weight

    def can_fire(self, current_time=None):
        # Check token requirements
        for place, weight in self.inputs.items():
            if place.tokens < weight:
                return False
        
        # Check timing if applicable
        if current_time is not None:
            time_since_last = current_time - self.last_fired_time
            if time_since_last < self.min_time:
                return False
        
        return True

    def fire(self, current_time=None):
        if not self.can_fire(current_time):
            return False

        # Consume tokens
        for place, weight in self.inputs.items():
            place.remove_token(weight)

        # Produce tokens
        for place, weight in self.outputs.items():
            place.add_token(weight)
        
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
        p = Place(name, tokens)
        self.places[name] = p
        return p

    def add_transition(self, name, min_time=0, max_time=float('inf')):
        t = Transition(name, min_time, max_time)
        self.transitions.append(t)
        return t

    def update(self, dt):
        self.current_time += dt
        # Naive simulation: try to fire any transition that is ready
        # In a strict Petri Net, this might be non-deterministic or need a specific scheduler.
        # For a traffic light, we usually want a deterministic sequence or priority.
        
        fired_any = False
        # We iterate a copy or index to avoid issues if list changes (though it shouldn't here)
        for t in self.transitions:
            if t.can_fire(self.current_time):
                t.fire(self.current_time)
                fired_any = True
                # In some models, we might only fire one transition per step.
                # For this traffic controller, sequential firing is often expected.
                # If we return here, we fire one per update.
        return fired_any

    def get_token_count(self, place_name):
        if place_name in self.places:
            return self.places[place_name].tokens
        return 0
