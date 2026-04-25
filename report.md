# Simulation Report — Probabilistic & Statistical Models

This document catalogs every probability distribution, stochastic process, and statistical metric implemented in the Petri Net Traffic Light Simulation.

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

Accidents are generated as a **non-homogeneous Poisson process** whose rate dynamically adapts to the pedestrian spawn rate.

**Equation:**

```
R(λ_p) = R_base + P_hit × λ_c × λ_p × s_c × s_p
```

Where:

| Symbol | Description | Value |
|---|---|---|
| R(λ_p) | Accident rate (accidents/min) | Dynamic |
| R_base | Baseline accident rate (no pedestrians) | 1.0 acc/min |
| P_hit | Probability of crash given simultaneous intersection occupancy | 0.20 |
| λ_c | Average vehicle arrival rate | 28.5 cars/min |
| λ_p | Current pedestrian spawn rate | 0–120 peds/min |
| s_c | Average car intersection crossing time | 0.036 min (~2.2s) |
| s_p | Average pedestrian crossing time | 0.081 min (~4.9s) |

**Interpretation:** The model is derived from queuing theory. The term `λ_c × λ_p × s_c × s_p` computes the expected number of simultaneous car-pedestrian occupancy events per minute. `P_hit` scales this to a collision probability.

**Example rate calculations:**

| λ_p (ppm) | R(λ_p) (acc/min) | Mean inter-arrival (sec) |
|---|---|---|
| 0 | 1.000 | 60.0 |
| 30 | 1.497 | 40.1 |
| 60 | 1.994 | 30.1 |
| 90 | 2.491 | 24.1 |
| 120 | 2.988 | 20.1 |

### 2.2 Vehicle Spawn Process

Vehicles are spawned using a **renewal process** with Uniform inter-arrival times.

```
T_spawn ~ Uniform(1.2, 3.0)
```

Expected spawn rate:

```
E[T] = (1.2 + 3.0) / 2 = 2.1 sec
λ_vehicles ≈ 60 / 2.1 ≈ 28.57 vehicles/min
```

At each spawn event:
- Direction ~ DiscreteUniform({N, S, E, W} \ blocked_dirs)
- P(ambulance) = 0.10 (Bernoulli trial)
- If not ambulance: type ~ DiscreteUniform({Sedan, SUV, Hatchback, ...})

### 2.3 Pedestrian Spawn Process

Pedestrians are spawned using a **Poisson process** (exponential inter-arrivals):

```
T_spawn ~ Exponential(λ = rate_ppm / 60)
```

Where `rate_ppm` cycles through: **0, 15, 30, 45, 60, 75, 90, 105, 120** ppm.

| Rate (ppm) | λ (per sec) | E[inter-arrival] (sec) |
|---|---|---|
| 0 | 0 | ∞ (disabled) |
| 15 | 0.25 | 4.00 |
| 30 | 0.50 | 2.00 |
| 45 | 0.75 | 1.33 |
| 60 | 1.00 | 1.00 |
| 90 | 1.50 | 0.67 |
| 120 | 2.00 | 0.50 |

### 2.4 VIP Spawn Process

VIP convoys are spawned as a **Poisson process**:

```
T_vip ~ Exponential(λ = 1/45)
E[T_vip] = 45 seconds
```

---

## 3. Vehicle Physics Model

### 3.1 Following Distance

Each vehicle has randomized gap preferences:

```
preferred_gap ~ max(5, N(μ=12, σ=4))   // gap to vehicle ahead
stop_line_gap ~ max(5, N(μ=8,  σ=3))   // gap to stop line
```

### 3.2 Speed Control (Car-Following)

| Condition | Target Speed |
|---|---|
| No vehicle ahead | max_speed |
| dist < preferred_gap | 0 (hard brake) |
| dist < 60 | 0.8 × ahead.speed |
| dist < 100 | 1.0 × ahead.speed |
| Overlapping (dist < 0) | 0 (emergency stop) |

Acceleration/deceleration:

```
if speed < target: speed += 200 × dt
if speed > target: speed -= 400 × dt
speed ∈ [0, max_speed × 1.2]
```

### 3.3 Wait Time Accumulation

```
if speed < 5.0 px/s:
    wait_time += dt
```

Wait time is recorded per-vehicle when the vehicle exits the screen, tagged with the current pedestrian rate.

---

## 4. Petri Net Controller Model

### 4.1 State Machine (per direction)

```
Places:   P_Green, P_Yellow, P_RedYellow    (tokens ∈ {0, 1})
Transitions:
  T_EndGreen    : P_Green    → P_Yellow       (min_time: adaptive 5–15s)
  T_EndYellow   : P_Yellow   → ∅ (consumed)   (min_time: 3.0s)
  T_EndRedYellow: P_RedYellow → P_Green       (min_time: 3.0s)
```

### 4.2 German All-Red Interlock

The scheduler enforces a strict safety invariant:

```
∀t: |{d : P_d_Green.tokens > 0}| ≤ 1
```

The next direction's RedYellow only begins **after** all Places across all directions are empty (all-red state).

### 4.3 Green Duration (Adaptive)

```
T_EndGreen.min_time = min(5 + queue_length × 1.0, 15)
```

---

## 5. Computed Statistics & Metrics

### 5.1 Summary Metrics

| Metric | Formula |
|---|---|
| Duration | `end_time − start_time` |
| Total Vehicles | count of vehicle_spawns |
| Ambulance % | `ambulances / total × 100` |
| Total Fatalities | Σ victims per accident |

### 5.2 Inter-Arrival Time (IAT) Analysis

For any event stream E = {e₁, e₂, ..., eₙ}:

```
IAT_i = t_{i+1} − t_i    for i = 1, ..., n-1

μ_IAT = (1/n) × Σ IAT_i
σ_IAT = √[(1/n) × Σ(IAT_i − μ_IAT)²]
```

Computed for: vehicles, pedestrians, accidents, VIPs.

### 5.3 Average Wait Time by Pedestrian Rate

```
AvgWait(r) = (1/|W_r|) × Σ wait_time_i    for all vehicles recorded at rate r
```

Only reported when cumulative time at rate `r` ≥ 60 seconds.

### 5.4 Accidents per Minute by Pedestrian Rate

```
AccPerMin(r) = count(accidents at rate r) / (duration_at_rate_r / 60)
```

Only reported when cumulative time at rate `r` ≥ 60 seconds.

### 5.5 Frequency Distributions

- **Vehicle Type Distribution**: count per type (Sedan, SUV, Truck, ...)
- **Vehicle Direction Distribution**: count per direction (N, S, E, W)
- **Crossing Location Distribution**: count per crosswalk (North, South, East, West)
- **Collision Type Distribution**: count per type (car_car, car_pedestrian)

---

## 6. Simulation Configuration

### 6.1 Auto-Cycling Parameters

| Parameter | Value |
|---|---|
| Rate Steps | 0, 15, 30, 45, 60, 75, 90, 105, 120 ppm |
| Duration per Step | 600 simulation seconds (10 minutes) |
| Clean Sweep (optional) | Wipes vehicles, pedestrians, accidents between steps |

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

---

## 7. Charts Generated

The statistics screen (`screens.py`) generates the following matplotlib visualizations:

1. **Vehicle Type Distribution** — Horizontal bar chart
2. **Vehicle Direction Distribution** — Horizontal bar chart
3. **Avg Wait Time by Ped Rate** — Vertical bar chart
4. **Vehicle IAT Histogram** — Histogram with mean line and μ/σ annotation
5. **Accident Type Distribution** — Horizontal bar chart
6. **Accidents per Minute by Ped Rate** — Vertical bar chart
7. **Pedestrian Crossing Location** — Horizontal bar chart
8. **Pedestrian IAT Histogram** — Histogram with mean line and μ/σ annotation
9. **Event Timeline** — Scatter plot of all events over simulation time
