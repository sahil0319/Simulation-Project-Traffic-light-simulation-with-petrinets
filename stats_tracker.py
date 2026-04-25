# stats_tracker.py

import time
import statistics


class StatsTracker:
    """Records all random events during a simulation run for statistical analysis."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.game_mode = ""

        # Vehicle events: list of dicts
        self.vehicle_spawns = []        # {time, type, direction, is_ambulance}
        self.vehicle_gaps = []          # {preferred_gap, stop_line_gap}
        self.vehicle_wait_times = []    # {wait_time, ped_rate}

        # VIP events
        self.vip_spawns = []            # {time, direction}

        # Accident events
        self.accident_spawns = []       # {time, collision_type, direction, fatalities}

        # Pedestrian events
        self.pedestrian_spawns = []     # {time, crossing_type, direction}
        
        # Pedestrian rate intervals
        self.ped_rate_intervals = []    # {rate_ppm, start_time, end_time, duration}
        self.current_ped_rate_start = None
        self.current_ped_rate = 30

        # Simulation metrics snapshot
        self.max_queue_length = 0
        self.total_cars_exited = 0
        self.pedestrian_spawn_rate = 30  # default ppm

    def start(self):
        self.start_time = time.time()
        self.current_ped_rate_start = self.start_time

    def stop(self):
        self.end_time = time.time()
        self.record_ped_rate_change(self.current_ped_rate) # Close final interval

    @property
    def duration(self):
        if self.start_time is None:
            return 0
        end = self.end_time or time.time()
        return end - self.start_time

    # --- Recording methods ---

    def record_vehicle_spawn(self, vehicle_type, direction, is_ambulance):
        self.vehicle_spawns.append({
            "time": time.time(),
            "type": vehicle_type,
            "direction": direction,
            "is_ambulance": is_ambulance,
        })

    def record_vehicle_gaps(self, preferred_gap, stop_line_gap):
        self.vehicle_gaps.append({
            "preferred_gap": preferred_gap,
            "stop_line_gap": stop_line_gap,
        })

    def record_vehicle_wait(self, wait_time, ped_rate):
        self.vehicle_wait_times.append({
            "wait_time": wait_time,
            "ped_rate": ped_rate
        })

    def record_vip_spawn(self, direction):
        self.vip_spawns.append({
            "time": time.time(),
            "direction": direction,
        })

    def record_accident(self, collision_type, direction, fatalities=0, ped_spawn_rate=0):
        self.accident_spawns.append({
            "time": time.time(),
            "collision_type": collision_type,
            "direction": direction,
            "fatalities": fatalities,
            "ped_spawn_rate": ped_spawn_rate,
        })

    def record_ped_rate_change(self, new_rate):
        """Close the current rate interval and start a new one."""
        now = time.time()
        if self.current_ped_rate_start is not None:
            self.ped_rate_intervals.append({
                "rate_ppm": self.current_ped_rate,
                "start_time": self.current_ped_rate_start,
                "end_time": now,
                "duration": now - self.current_ped_rate_start
            })
        self.current_ped_rate = new_rate
        self.current_ped_rate_start = now

    def _get_rate_durations(self):
        rate_durations = {}
        for interval in self.ped_rate_intervals:
            r = interval["rate_ppm"]
            rate_durations[r] = rate_durations.get(r, 0) + interval["duration"]
        return rate_durations

    def get_accidents_per_min_by_rate(self):
        """Return {rate_ppm: accidents_per_minute} based on time spent at each rate."""
        rate_durations = self._get_rate_durations()
            
        # Count accidents per rate
        rate_accidents = {r: 0 for r in rate_durations}
        for a in self.accident_spawns:
            rate = a.get("ped_spawn_rate", 0)
            if rate in rate_accidents:
                rate_accidents[rate] += 1
            else:
                rate_accidents[rate] = 1 # Fallback
                rate_durations[rate] = rate_durations.get(rate, 0.001)

        # Compute accidents per minute
        acc_per_min = {}
        for r, dur in rate_durations.items():
            if dur >= 60: # Only show stats if run for at least 60 cumulative seconds
                mins = dur / 60.0
                acc_per_min[r] = round(rate_accidents[r] / mins, 2)
                
        return acc_per_min

    def get_avg_wait_time_by_rate(self):
        """Return {rate_ppm: avg_wait_time_sec} for vehicles."""
        rate_durations = self._get_rate_durations()
        buckets = {}
        for w in self.vehicle_wait_times:
            r = w["ped_rate"]
            if r not in buckets:
                buckets[r] = []
            buckets[r].append(w["wait_time"])
            
        avg_waits = {}
        for r, times in buckets.items():
            dur = rate_durations.get(r, 0)
            if dur >= 60 and len(times) > 0: # Only show stats if run for at least 60 seconds
                avg_waits[r] = sum(times) / len(times)
        return avg_waits

    def record_pedestrian_spawn(self, crossing_type, direction):
        self.pedestrian_spawns.append({
            "time": time.time(),
            "crossing_type": crossing_type,
            "direction": direction,
        })

    # --- Computed statistics ---

    def _inter_arrival_times(self, events):
        """Compute inter-arrival times from a list of events with 'time' key."""
        if len(events) < 2:
            return []
        times = sorted(e["time"] for e in events)
        return [times[i + 1] - times[i] for i in range(len(times) - 1)]

    def _dist_stats(self, values):
        """Return dict of mean, std, min, max for a list of floats."""
        if not values:
            return {"mean": 0, "std": 0, "min": 0, "max": 0, "count": 0}
        return {
            "mean": statistics.mean(values),
            "std": statistics.pstdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "count": len(values),
        }

    def _frequency(self, events, key):
        """Return frequency dict for a given key in events."""
        freq = {}
        for e in events:
            val = e.get(key, "unknown")
            freq[val] = freq.get(val, 0) + 1
        return freq

    def get_vehicle_stats(self):
        total = len(self.vehicle_spawns)
        ambulances = sum(1 for v in self.vehicle_spawns if v["is_ambulance"])
        normal = total - ambulances
        type_freq = self._frequency(
            [v for v in self.vehicle_spawns if not v["is_ambulance"]], "type"
        )
        dir_freq = self._frequency(self.vehicle_spawns, "direction")
        iat = self._inter_arrival_times(self.vehicle_spawns)
        iat_stats = self._dist_stats(iat)

        # Gap stats
        pref_gaps = [g["preferred_gap"] for g in self.vehicle_gaps]
        stop_gaps = [g["stop_line_gap"] for g in self.vehicle_gaps]
        pref_stats = self._dist_stats(pref_gaps)
        stop_stats = self._dist_stats(stop_gaps)

        return {
            "total": total,
            "normal": normal,
            "ambulances": ambulances,
            "ambulance_pct": (ambulances / total * 100) if total > 0 else 0,
            "type_freq": type_freq,
            "dir_freq": dir_freq,
            "iat_stats": iat_stats,
            "preferred_gap_stats": pref_stats,
            "stop_line_gap_stats": stop_stats,
        }

    def get_vip_stats(self):
        total = len(self.vip_spawns)
        dir_freq = self._frequency(self.vip_spawns, "direction")
        iat = self._inter_arrival_times(self.vip_spawns)
        iat_stats = self._dist_stats(iat)
        return {
            "total": total,
            "dir_freq": dir_freq,
            "iat_stats": iat_stats,
        }

    def get_accident_stats(self):
        total = len(self.accident_spawns)
        type_freq = self._frequency(self.accident_spawns, "collision_type")
        dir_freq = self._frequency(self.accident_spawns, "direction")
        total_fatalities = sum(a.get("fatalities", 0) for a in self.accident_spawns)
        iat = self._inter_arrival_times(self.accident_spawns)
        iat_stats = self._dist_stats(iat)
        return {
            "total": total,
            "type_freq": type_freq,
            "dir_freq": dir_freq,
            "total_fatalities": total_fatalities,
            "iat_stats": iat_stats,
        }

    def get_pedestrian_stats(self):
        total = len(self.pedestrian_spawns)
        crossing_freq = self._frequency(self.pedestrian_spawns, "crossing_type")
        dir_freq = self._frequency(self.pedestrian_spawns, "direction")
        iat = self._inter_arrival_times(self.pedestrian_spawns)
        iat_stats = self._dist_stats(iat)
        return {
            "total": total,
            "crossing_freq": crossing_freq,
            "dir_freq": dir_freq,
            "iat_stats": iat_stats,
            "spawn_rate_ppm": self.pedestrian_spawn_rate,
        }

    def has_data(self):
        """Return True if any events were recorded."""
        return (len(self.vehicle_spawns) > 0 or
                len(self.vip_spawns) > 0 or
                len(self.accident_spawns) > 0 or
                len(self.pedestrian_spawns) > 0)
