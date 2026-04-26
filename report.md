# Simulation Report — Probabilistic & Statistical Models

This document catalogs every probability distribution, stochastic process, and statistical metric implemented in the Petri Net Traffic Light Simulation. Implementation details and citations to the actual codebase are included for each model.

---

## 1. Stochastic Processes & Probability Distributions

### 1.1 Distribution Reference Table

| Component | Variable | Distribution | Parameters | Source File |
|---|---|---|---|---|
| Vehicle Spawn Interval | `spawn_timer` | Uniform | U(1.2, 3.0) seconds | `vehicle.py` |
| Vehicle Type Selection | `type_name` | Discrete Uniform | Equal probability over {Sedan, SUV, Hatchback, Truck, Pickup, Van, SportsCar, MiniVan} | `vehicle.py` |
| Ambulance Spawn | `is_ambulance` | Bernoulli | p = 0.10 | `vehicle.py` |
| Vehicle Direction | `direction` | Discrete Uniform | Equal probability over {N, S, E, W} (excluding blocked) | `vehicle.py` |
| Vehicle Following Gap | `preferred_gap` | Truncated Normal | N(μ=12, σ=4), min=5 | `vehicle.py` |
| Stop Line Gap | `stop_line_gap` | Truncated Normal | N(μ=8, σ=3), min=5 | `vehicle.py` |
| Pedestrian Spawn Interval | `spawn_timer` | Exponential | λ = spawn_rate_ppm / 60 | `pedestrian.py` |
| Pedestrian Walking Speed | `speed` | Uniform | U(35, 55) px/s | `pedestrian.py` |
| Pedestrian Crossing Location | `crossing` | Discrete Uniform | Equal over {North, South, East, West} | `pedestrian.py` |
| Pedestrian Direction | `direction` | Discrete Uniform | {positive, negative} | `pedestrian.py` |
| Accident Inter-Arrival | `spawn_timer` | Exponential | λ = rate_per_sec (dynamic, see §2.1) | `accident.py` |
| Collision Type | `collision_type` | Discrete | P(car_ped) ∝ λ_p; P(car_car) ∝ remaining | `accident.py` |
| Fatalities per Accident | `num_victims` | Discrete Uniform | car_car: U{1,3}; car_ped: 1 | `accident.py` |
| VIP Spawn Interval | `vip_spawn_timer` | Exponential | λ = 1/45 (mean 45s) | `police.py` |
| VIP Direction | `approach` | Discrete Uniform | Equal over {N, S, E, W} | `police.py` |

---

## 2. Core Mathematical Models

### 2.1 Accident Rate — Queuing-Theoretic Collision Model

Accidents are generated as a **non-homogeneous Poisson process** whose rate dynamically adapts to the pedestrian spawn rate. The model computes expected simultaneous occupancy given car and pedestrian throughput.

**Equation:**
```
R(λ_p) = R_base + P_hit × λ_c × λ_p × s_c × s_p
```

**Implementation Citation** ([accident.py:L1061-L1068](file:///Users/mahdisahil/Desktop/simulation/sim_project/accident.py#L1061-L1068)):
```python
# Recalculate dynamic accident rate based on queuing model
lambda_p = self._ped_manager.spawn_rate_ppm if self._ped_manager else 0
# Accident rate per minute = baseline + (p_hit * lambda_c * lambda_p * s_c * s_p)
rate_per_min = BASELINE_RATE_P_MIN + (P_HIT * LAMBDA_C * lambda_p * S_C * S_P)
# Convert to rate per second for expovariate
rate_per_sec = rate_per_min / 60.0

self.spawn_timer += random.expovariate(rate_per_sec)
```


### 2.2 Vehicle Spawn Process

Vehicles are spawned using a **renewal process** with Uniform inter-arrival times. 

**Equation:**
```
T_spawn ~ Uniform(1.2, 3.0)
```

**Implementation Citation** ([vehicle.py:L502](file:///Users/mahdisahil/Desktop/simulation/sim_project/vehicle.py#L502)):
```python
self.spawn_timer += random.uniform(1.2, 3.0)
```

At each spawn event:
- `is_ambulance` ~ Bernoulli(0.1)
- `type_name` ~ DiscreteUniform(types \ ambulance)

**Implementation Citation** ([vehicle.py:L498-L499](file:///Users/mahdisahil/Desktop/simulation/sim_project/vehicle.py#L498-L499)):
```python
# 10% chance for ambulance
is_ambulance = random.random() < 0.1
```


### 2.3 Pedestrian Spawn Process

Pedestrians are spawned using a **Poisson process** (exponential inter-arrivals).

**Equation:**
```
T_spawn ~ Exponential(λ = rate_ppm / 60)
```

**Implementation Citation** ([pedestrian.py:L366](file:///Users/mahdisahil/Desktop/simulation/sim_project/pedestrian.py#L366)):
```python
self.spawn_timer = random.expovariate(self.spawn_rate_ppm / 60.0)
```


### 2.4 VIP Spawn Process

VIP convoys are spawned as a **Poisson process**.

**Equation:**
```
T_vip ~ Exponential(λ = 1/45)
E[T_vip] = 45 seconds
```

**Implementation Citation** ([police.py:L813](file:///Users/mahdisahil/Desktop/simulation/sim_project/police.py#L813)):
```python
self.vip_spawn_timer = random.expovariate(1.0 / 45.0)  # Average 45s between spawns
```

---

## 3. Vehicle Physics Model

### 3.1 Following Distance

Each vehicle has randomized gap preferences to simulate natural spacing variance:

**Equation:**
```
preferred_gap ~ max(5, N(μ=12, σ=4))
stop_line_gap ~ max(5, N(μ=8,  σ=3))
```

**Implementation Citation** ([vehicle.py:L97-L99](file:///Users/mahdisahil/Desktop/simulation/sim_project/vehicle.py#L97-L99)):
```python
# Randomized gap preferences for natural spacing
self.preferred_gap = max(5, random.normalvariate(12, 4))  # Gap to car ahead
self.stop_line_gap = max(5, random.normalvariate(8, 3))   # Gap to stop line
```


### 3.2 Speed Control (Car-Following)

Vehicles calculate a `target_speed` based on the gap to the vehicle ahead, then accelerate or decelerate to match it.

**Implementation Citation** ([vehicle.py:L268-L272](file:///Users/mahdisahil/Desktop/simulation/sim_project/vehicle.py#L268-L272)):
```python
if target_speed > self.speed:
    self.speed += 200 * dt  # Acceleration
elif target_speed < self.speed:
    self.speed -= 400 * dt  # Deceleration

self.speed = max(0, min(self.speed, self.max_speed * 1.2))
```

---

## 4. Petri Net Controller Model

### 4.1 German All-Red Interlock

The scheduler enforces a strict safety invariant where the next direction's RedYellow only begins **after** all Places across all directions are empty (the all-red state).

**Equation:**
```
∀t: |{d : P_d_Green.tokens > 0}| ≤ 1
```

**Implementation Citation** ([adaptive_controller.py:L90-L94](file:///Users/mahdisahil/Desktop/simulation/sim_project/adaptive_controller.py#L90-L94)):
```python
# All-Red Interlock: schedule the next phase ONLY when every single
# place in the net is empty (all directions are Red).  This guarantees
# no two directions can ever have Green (or Green+Yellow) at the same time.
if not green_dir and not yellow_dir and not ry_dir:
    exclude = getattr(self, "_pending_schedule_exclude", [])
    best_dir = self.select_next_phase(vehicle_manager, exclude=exclude)
```


### 4.2 Green Duration (Adaptive)

Green light duration dynamically adapts to the queue length for the selected direction.

**Equation:**
```
T_EndGreen.min_time = min(5 + queue_length × 1.0, 15)
```

**Implementation Citation** ([adaptive_controller.py:L103-L105](file:///Users/mahdisahil/Desktop/simulation/sim_project/adaptive_controller.py#L103-L105)):
```python
q_len, max_wait = vehicle_manager.get_lane_info(best_dir)
t_green = self.transitions[best_dir]["t_end_green"]
t_green.min_time = min(5 + q_len * 1.0, 15)
```

---

## 5. Computed Statistics & Metrics

### 5.1 Average Wait Time by Pedestrian Rate

To prevent bias from initial transient conditions, data is filtered using a Warm-Up Period Deletion.

**Equation:**
```
AvgWait(r) = (1/|W_r|) × Σ wait_time_i    for all vehicles recorded at rate r (excluding warm-up)
```

**Implementation Citation** ([stats_tracker.py:L68-L76](file:///Users/mahdisahil/Desktop/simulation/sim_project/stats_tracker.py#L68-L76)):
```python
def _in_warmup(self):
    """Return True if we are in the warm-up window of the current rate interval."""
    if not self.warmup_enabled:
        return False
    if self.current_ped_rate_start is None:
        return False
    elapsed = self.sim_time - self.current_ped_rate_start
    return elapsed < self.WARMUP_DURATION
```


### 5.2 Inter-Arrival Time (IAT) Analysis

For any event stream `E = {e₁, e₂, ..., eₙ}`:

```
IAT_i = t_{i+1} − t_i
μ_IAT = (1/n) × Σ IAT_i
σ_IAT = √[(1/n) × Σ(IAT_i − μ_IAT)²]
```

**Implementation Citation** ([stats_tracker.py:L177-L182](file:///Users/mahdisahil/Desktop/simulation/sim_project/stats_tracker.py#L177-L182)):
```python
def _inter_arrival_times(self, events):
    """Compute inter-arrival times from a list of events with 'time' key."""
    if len(events) < 2:
        return []
    times = sorted(e["time"] for e in events)
    return [times[i + 1] - times[i] for i in range(len(times) - 1)]
```

---

## 6. Simulation Configuration

### 6.1 Auto-Cycling Parameters

| Parameter | Value |
|---|---|
| Rate Steps | 0, 15, 30, 45, 60, 75, 90, 105, 120 ppm |
| Duration per Step | 600 simulation seconds (10 minutes) |
| Clean Sweep | Wipes vehicles, pedestrians, accidents between steps |
| Warm-up Deletion | Ignores stats for the first 60 seconds of a step |

### 6.2 Speed Multipliers

| Key | Multiplier |
|---|---|
| 1 | 1× |
| 2 | 2× |
| 3 | 4× |
| 4 | 8× |
| 5 | 16× |
| 6 | 32× |
| 7 | 64× |

### 6.3 Accident Scene Timing

| Phase | Duration |
|---|---|
| Collision Animation | 0.9s |
| Dispatch Delay | 1.5s |
| Loading (ambulance at scene) | 4.0s |
| Clearing (fade out) | 2.5s |
| **Total** | **8.9s** |
