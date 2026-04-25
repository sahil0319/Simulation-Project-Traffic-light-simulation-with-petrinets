# screens.py

import pygame
import math
from accident import P_HIT, S_C, S_P, LAMBDA_C, BASELINE_RATE_P_MIN

# --- Colors ---
BG = (25, 25, 25)
CARD_BG = (35, 35, 40)
CARD_BORDER = (60, 60, 70)
ACCENT = (100, 200, 255)
ACCENT2 = (255, 180, 60)
GREEN_ACC = (80, 220, 130)
RED_ACC = (255, 90, 90)
WHITE = (230, 230, 230)
GRAY = (140, 140, 140)
DARK_GRAY = (80, 80, 80)
BTN_BG = (45, 50, 60)
BTN_HOVER = (60, 70, 90)
BTN_DISABLED = (35, 35, 38)
PED_COLOR = (200, 160, 255)


class MenuScreen:
    """Main menu with Play and Statistics buttons."""

    def __init__(self, screen_w, screen_h, font_path):
        self.w = screen_w
        self.h = screen_h
        self.title_font = pygame.font.Font(font_path, 60)
        self.sub_font = pygame.font.Font(font_path, 30)
        self.btn_font = pygame.font.Font(font_path, 36)
        self.small_font = pygame.font.Font(font_path, 22)
        bw, bh = 340, 70
        cx = screen_w // 2
        self.btn_play = pygame.Rect(cx - bw // 2, 320, bw, bh)
        self.btn_stats = pygame.Rect(cx - bw // 2, 420, bw, bh)
        self.hover_play = False
        self.hover_stats = False
        self.stats_enabled = False
        self.anim_t = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_play = self.btn_play.collidepoint(event.pos)
            self.hover_stats = self.btn_stats.collidepoint(event.pos) and self.stats_enabled
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_play.collidepoint(event.pos):
                return "play"
            if self.btn_stats.collidepoint(event.pos) and self.stats_enabled:
                return "stats"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 or event.key == pygame.K_RETURN:
                return "play"
            if event.key == pygame.K_2 and self.stats_enabled:
                return "stats"
        return None

    def draw(self, surface, dt):
        self.anim_t += dt
        surface.fill(BG)
        for i in range(6):
            angle = self.anim_t * 0.3 + i * math.pi / 3
            radius = 180 + math.sin(self.anim_t * 0.5 + i) * 30
            cx = self.w // 2 + int(math.cos(angle) * radius)
            cy = self.h // 2 + int(math.sin(angle) * radius) - 40
            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
            alpha = int(25 + 15 * math.sin(self.anim_t * 2 + i))
            color = ACCENT if i % 2 == 0 else ACCENT2
            pygame.draw.circle(glow, (*color, alpha), (30, 30), 28)
            surface.blit(glow, (cx - 30, cy - 30))
        title = self.title_font.render("Petri Net Traffic Sim", True, WHITE)
        surface.blit(title, title.get_rect(center=(self.w // 2, 160)))
        sub = self.sub_font.render("Traffic Light Controller Simulation", True, GRAY)
        surface.blit(sub, sub.get_rect(center=(self.w // 2, 220)))
        pygame.draw.line(surface, ACCENT, (self.w // 2 - 100, 250), (self.w // 2 + 100, 250), 2)
        self._draw_btn(surface, self.btn_play, "Start Simulation", self.hover_play, True, ACCENT)
        sc = ACCENT2 if self.stats_enabled else DARK_GRAY
        self._draw_btn(surface, self.btn_stats, "View Statistics", self.hover_stats, self.stats_enabled, sc)
        if not self.stats_enabled:
            h = self.small_font.render("(Run a simulation first)", True, DARK_GRAY)
            surface.blit(h, h.get_rect(center=(self.w // 2, self.btn_stats.bottom + 25)))
        k = self.small_font.render("[1] Play    [2] Stats    [ESC] Quit", True, DARK_GRAY)
        surface.blit(k, k.get_rect(center=(self.w // 2, self.h - 40)))

    def _draw_btn(self, surface, rect, text, hover, enabled, accent):
        bg = BTN_HOVER if hover else (BTN_BG if enabled else BTN_DISABLED)
        pygame.draw.rect(surface, bg, rect, border_radius=12)
        bc = accent if (enabled and hover) else (CARD_BORDER if enabled else (40, 40, 42))
        pygame.draw.rect(surface, bc, rect, 2, border_radius=12)
        tc = WHITE if enabled else DARK_GRAY
        surface.blit(self.btn_font.render(text, True, tc), self.btn_font.render(text, True, tc).get_rect(center=rect.center))


class StatsScreen:
    """Statistics dashboard with larger fonts and histogram graphs."""

    def __init__(self, screen_w, screen_h, font_path):
        self.w = screen_w
        self.h = screen_h
        # Use clean system font for statistics readability
        clean = pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", 1)  # test availability
        clean_name = "Arial" if pygame.font.match_font("arial") else None
        self.title_font = pygame.font.SysFont(clean_name, 38, bold=True)
        self.section_font = pygame.font.SysFont(clean_name, 28, bold=True)
        self.label_font = pygame.font.SysFont(clean_name, 22)
        self.value_font = pygame.font.SysFont(clean_name, 24, bold=True)
        self.body_font = pygame.font.SysFont(clean_name, 21)
        self.small_font = pygame.font.SysFont(clean_name, 18)
        self.btn_font = pygame.font.SysFont(clean_name, 22, bold=True)
        self.btn_back = pygame.Rect(20, 20, 200, 50)
        self.hover_back = False
        self.scroll_y = 0
        self.max_scroll = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover_back = self.btn_back.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_back.collidepoint(event.pos):
                return "menu"
            if event.button == 4:
                self.scroll_y = min(0, self.scroll_y + 50)
            elif event.button == 5:
                self.scroll_y = max(-self.max_scroll, self.scroll_y - 50)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return "menu"
            if event.key == pygame.K_UP:
                self.scroll_y = min(0, self.scroll_y + 70)
            if event.key == pygame.K_DOWN:
                self.scroll_y = max(-self.max_scroll, self.scroll_y - 70)
        return None

    def draw(self, surface, tracker):
        surface.fill(BG)
        v = tracker.get_vehicle_stats()
        vip = tracker.get_vip_stats()
        acc = tracker.get_accident_stats()
        ped = tracker.get_pedestrian_stats()

        # Estimate content height
        content_h = 5000
        cs = pygame.Surface((self.w, content_h), pygame.SRCALPHA)
        y = 20

        # Title
        t = self.title_font.render("Simulation Statistics", True, WHITE)
        cs.blit(t, t.get_rect(center=(self.w // 2, y + 25)))
        y += 70

        # ===== OVERVIEW =====
        y = self._section(cs, y, "Overview", ACCENT)
        y = self._kv(cs, y, [
            ("Duration", f"{tracker.duration:.1f}s"),
            ("Game Mode", tracker.game_mode or "N/A"),
            ("Total Vehicles", str(v["total"])),
            ("Total Pedestrians", str(ped["total"])),
            ("VIP Events", str(vip["total"])),
            ("Accidents", str(acc["total"])),
            ("Fatalities", str(acc["total_fatalities"])),
        ])

        # ===== VEHICLE STATS =====
        y = self._section(cs, y + 15, "Vehicle Spawns", GREEN_ACC)
        items = [
            ("Total Spawned", str(v["total"])),
            ("Normal Vehicles", str(v["normal"])),
            ("Ambulances", f"{v['ambulances']} ({v['ambulance_pct']:.1f}%)"),
            ("Ambulance Dist.", "Bernoulli(p=0.10)"),
            ("Spawn Interval Dist.", "Uniform(1.2, 3.0) sec"),
        ]
        iat = v["iat_stats"]
        if iat["count"] > 0:
            items.append(("Observed Mean IAT", f"{iat['mean']:.2f}s  std={iat['std']:.2f}"))
        y = self._kv(cs, y, items)

        if v["type_freq"]:
            y = self._bars_horizontal(cs, y, "Vehicle Type Distribution", v["type_freq"], GREEN_ACC)
        if v["dir_freq"]:
            y = self._bars_horizontal(cs, y, "Vehicle Direction Distribution", v["dir_freq"], ACCENT)

        # Vehicle Wait Time vs Pedestrian Rate correlation
        wait_times_dict = tracker.get_avg_wait_time_by_rate()
        formatted_waits = {f"{int(rate)} ppm": val for rate, val in wait_times_dict.items() if val > 0}
        if formatted_waits:
            y = self._bars_vertical(cs, y, "Avg Wait Time (sec) by Ped Rate", formatted_waits, ACCENT, is_float=True)
        else:
            warn = self.small_font.render("* Run simulation at a specific rate for 60 cumulative seconds to see Avg Wait Time data.", True, (255, 150, 150))
            cs.blit(warn, (self.m + 10, y + 10))
            y += 35

        # IAT histogram for vehicles
        v_iats = tracker._inter_arrival_times(tracker.vehicle_spawns)
        if len(v_iats) > 3:
            y = self._histogram(cs, y, "Vehicle Inter-Arrival Times (sec)", v_iats, GREEN_ACC)

        # ===== DRIVING BEHAVIOR =====
        y = self._section(cs, y + 15, "Driving Behavior", ACCENT2)
        pg = v["preferred_gap_stats"]
        sg = v["stop_line_gap_stats"]
        y = self._kv(cs, y, [
            ("Following Gap Dist.", "Normal(mu=12, sig=4) min=5"),
            ("Observed Mean", f"{pg['mean']:.2f}  std={pg['std']:.2f}" if pg["count"] > 0 else "N/A"),
            ("Stop-Line Gap Dist.", "Normal(mu=8, sig=3) min=5"),
            ("Observed Mean", f"{sg['mean']:.2f}  std={sg['std']:.2f}" if sg["count"] > 0 else "N/A"),
        ])
        # Gap histogram
        gaps = [g["preferred_gap"] for g in tracker.vehicle_gaps]
        if len(gaps) > 3:
            y = self._histogram(cs, y, "Following Gap Distribution", gaps, ACCENT2)

        # ===== VIP STATS =====
        y = self._section(cs, y + 15, "VIP Convoy Events", ACCENT2)
        items = [
            ("Total Events", str(vip["total"])),
            ("Distribution", "Exponential(lam=1/45)"),
            ("Expected Mean", "45.0s"),
        ]
        vi = vip["iat_stats"]
        if vi["count"] > 0:
            items.append(("Observed Mean IAT", f"{vi['mean']:.2f}s  std={vi['std']:.2f}"))
        y = self._kv(cs, y, items)
        if vip["dir_freq"]:
            y = self._bars_horizontal(cs, y, "VIP Direction", vip["dir_freq"], ACCENT2)

        # ===== ACCIDENT STATS =====
        y = self._section(cs, y + 15, "Accident Events", RED_ACC)
        items = [
            ("Total Accidents", str(acc["total"])),
            ("Total Fatalities", str(acc["total_fatalities"])),
            ("Distribution", "Exponential(lam=1/60)"),
            ("Expected Mean", "60.0s"),
        ]
        ai = acc["iat_stats"]
        if ai["count"] > 0:
            items.append(("Observed Mean IAT", f"{ai['mean']:.2f}s  std={ai['std']:.2f}"))
        y = self._kv(cs, y, items)
        if acc["type_freq"]:
            y = self._bars_horizontal(cs, y, "Accident Types", acc["type_freq"], RED_ACC)

        # Accident vs Pedestrian Rate correlation
        acc_per_min_dict = tracker.get_accidents_per_min_by_rate()
        formatted_acc = {f"{int(rate)} ppm": val for rate, val in acc_per_min_dict.items() if val > 0}
        if formatted_acc:
            y = self._bars_vertical(cs, y, "Accidents per Minute by Ped Rate", formatted_acc, RED_ACC)
        else:
            warn = self.small_font.render("* Run simulation at a specific rate for 60 cumulative seconds to see Accident per Min data.", True, (255, 150, 150))
            cs.blit(warn, (self.m + 10, y + 10))
            y += 35
                
        # ===== COLLISION MODEL MATH =====
        y = self._section(cs, y + 15, "Theoretical Collision Model", WHITE)
        y = self._kv(cs, y, [
            ("Equation", "Rate = base + (P_hit * λ_c * λ_p * s_c * s_p)"),
            ("P_hit (Base hit prob)", f"{P_HIT}"),
            ("λ_c (Car spawn rate)", f"{LAMBDA_C} cars/min"),
            ("s_c (Car cross time)", f"{S_C} min"),
            ("s_p (Ped cross time)", f"{S_P} min"),
            ("Base Rate", f"{BASELINE_RATE_P_MIN} acc/min"),
        ])

        # ===== PEDESTRIAN STATS =====
        y = self._section(cs, y + 15, "Pedestrian Events", PED_COLOR)
        items = [
            ("Total Spawned", str(ped["total"])),
            ("Spawn Rate", f"{ped['spawn_rate_ppm']:.0f} per minute"),
            ("Distribution", f"Exponential(lam={ped['spawn_rate_ppm']/60:.2f})"),
        ]
        pi = ped["iat_stats"]
        if pi["count"] > 0:
            items.append(("Observed Mean IAT", f"{pi['mean']:.2f}s  std={pi['std']:.2f}"))
        y = self._kv(cs, y, items)
        if ped["crossing_freq"]:
            y = self._bars_horizontal(cs, y, "Crossing Location", ped["crossing_freq"], PED_COLOR)

        # Pedestrian IAT histogram
        p_iats = tracker._inter_arrival_times(tracker.pedestrian_spawns)
        if len(p_iats) > 3:
            y = self._histogram(cs, y, "Pedestrian Inter-Arrival Times (sec)", p_iats, PED_COLOR)

        # ===== EVENT TIMELINE =====
        all_events = []
        for e in tracker.vehicle_spawns:
            all_events.append((e["time"], "Vehicle", GREEN_ACC))
        for e in tracker.vip_spawns:
            all_events.append((e["time"], "VIP", ACCENT2))
        for e in tracker.accident_spawns:
            all_events.append((e["time"], "Accident", RED_ACC))
        if len(all_events) > 2:
            y = self._section(cs, y + 15, "Event Timeline", WHITE)
            y = self._timeline(cs, y, all_events, tracker.start_time or 0, tracker.duration)

        y += 40
        self.max_scroll = max(0, y - self.h + 150)
        surface.blit(cs, (0, self.scroll_y))

        # Fixed back button
        bg = BTN_HOVER if self.hover_back else BTN_BG
        pygame.draw.rect(surface, bg, self.btn_back, border_radius=8)
        pygame.draw.rect(surface, ACCENT, self.btn_back, 2, border_radius=8)
        bt = self.btn_font.render("<- Back", True, WHITE)
        surface.blit(bt, bt.get_rect(center=self.btn_back.center))

        if self.max_scroll > 0:
            hint = self.small_font.render("Scroll or Arrow Keys", True, DARK_GRAY)
            surface.blit(hint, hint.get_rect(center=(self.w // 2, self.h - 15)))

    # ---- helpers ----

    def _section(self, surf, y, title, color):
        txt = self.section_font.render(title, True, color)
        surf.blit(txt, (30, y))
        pygame.draw.line(surf, color, (30, y + 38), (self.w - 30, y + 38), 2)
        return y + 50

    def _kv(self, surf, y, items):
        x0 = 30
        cw = self.w - 60
        row_h = 34
        ch = len(items) * row_h + 20
        pygame.draw.rect(surf, CARD_BG, (x0, y, cw, ch), border_radius=8)
        pygame.draw.rect(surf, CARD_BORDER, (x0, y, cw, ch), 1, border_radius=8)
        cy = y + 12
        for label, value in items:
            surf.blit(self.body_font.render(label, True, GRAY), (x0 + 18, cy))
            surf.blit(self.body_font.render(value, True, WHITE), (x0 + cw // 2 + 30, cy))
            cy += row_h
        return y + ch + 12

    def _bars_horizontal(self, surf, y, title, freq, color):
        x0 = 30
        cw = self.w - 80
        surf.blit(self.body_font.render(title, True, WHITE), (x0 + 10, y))
        y += 32
        mx = max(freq.values()) if freq else 1
        bar_h = 28
        gap = 8
        ch = len(freq) * (bar_h + gap) + 20
        pygame.draw.rect(surf, CARD_BG, (x0, y, cw, ch), border_radius=8)
        pygame.draw.rect(surf, CARD_BORDER, (x0, y, cw, ch), 1, border_radius=8)
        by = y + 10
        lw = 160
        baw = cw - lw - 90
        for key, cnt in sorted(freq.items(), key=lambda kv: -kv[1]):
            surf.blit(self.body_font.render(str(key), True, GRAY), (x0 + 15, by + 2))
            bw = int((cnt / mx) * baw) if mx > 0 else 0
            pygame.draw.rect(surf, color, (x0 + lw, by, max(6, bw), bar_h), border_radius=5)
            surf.blit(self.body_font.render(str(cnt), True, WHITE), (x0 + lw + bw + 10, by + 2))
            by += bar_h + gap
        return y + ch + 12

    def _bars_vertical(self, surf, y, title, freq, color, is_float=False):
        x0 = 30
        cw = self.w - 80
        surf.blit(self.body_font.render(title, True, WHITE), (x0 + 10, y))
        y += 32
        
        # Vertical bar chart layout
        chart_h = 160
        total_h = chart_h + 50
        pygame.draw.rect(surf, CARD_BG, (x0, y, cw, total_h), border_radius=8)
        pygame.draw.rect(surf, CARD_BORDER, (x0, y, cw, total_h), 1, border_radius=8)
        
        if not freq:
            return y + total_h + 12
            
        mx = max(freq.values()) if freq else 1
        num_bars = len(freq)
        pad_x = 40
        area_w = cw - (pad_x * 2)
        bar_w = min(60, max(15, (area_w // num_bars) - 10))
        
        ax_y_bot = y + chart_h - 10
        
        # Sort by key if it's numeric-like, else by value
        try:
            sorted_items = sorted(freq.items(), key=lambda kv: float(str(kv[0]).replace(' ppm', '')))
        except:
            sorted_items = sorted(freq.items(), key=lambda kv: -kv[1])
            
        spacing = area_w / max(1, num_bars)
        
        for i, (key, cnt) in enumerate(sorted_items):
            bx = x0 + pad_x + int(i * spacing) + int((spacing - bar_w) / 2)
            bh = int((cnt / mx) * (chart_h - 40)) if mx > 0 else 0
            
            # Draw bar
            pygame.draw.rect(surf, color, (bx, ax_y_bot - bh, bar_w, max(4, bh)), border_radius=4)
            
            # Draw value on top
            val_txt = f"{cnt:.1f}" if is_float else str(cnt)
            val_surf = self.small_font.render(val_txt, True, WHITE)
            surf.blit(val_surf, (bx + bar_w//2 - val_surf.get_width()//2, ax_y_bot - bh - 20))
            
            # Draw label below
            lbl_txt = str(key)
            if len(lbl_txt) > 8:
                lbl_txt = lbl_txt.replace("car_pedestrian", "Car/Ped")
                if len(lbl_txt) > 8:
                    lbl_txt = lbl_txt[:6] + ".."
            lbl_surf = self.small_font.render(lbl_txt, True, GRAY)
            surf.blit(lbl_surf, (bx + bar_w//2 - lbl_surf.get_width()//2, ax_y_bot + 5))
            
        return y + total_h + 12

    def _histogram(self, surf, y, title, values, color, num_bins=12):
        """Draw a histogram of raw values."""
        x0 = 30
        cw = self.w - 80
        chart_h = 160
        surf.blit(self.body_font.render(title, True, WHITE), (x0 + 10, y))
        y += 32
        total_h = chart_h + 50
        pygame.draw.rect(surf, CARD_BG, (x0, y, cw, total_h), border_radius=8)
        pygame.draw.rect(surf, CARD_BORDER, (x0, y, cw, total_h), 1, border_radius=8)

        if not values:
            return y + total_h + 12

        lo, hi = min(values), max(values)
        if hi == lo:
            hi = lo + 1
        bin_w_val = (hi - lo) / num_bins
        bins = [0] * num_bins
        for v in values:
            idx = min(int((v - lo) / bin_w_val), num_bins - 1)
            bins[idx] += 1
        mx = max(bins) if bins else 1

        pad_l = 50
        pad_r = 20
        pad_t = 15
        pad_b = 35
        area_w = cw - pad_l - pad_r
        area_h = chart_h - pad_t
        bar_w = max(4, area_w // num_bins - 2)

        # Y axis
        ax_x = x0 + pad_l
        ax_y_top = y + pad_t
        ax_y_bot = y + pad_t + area_h
        pygame.draw.line(surf, GRAY, (ax_x, ax_y_top), (ax_x, ax_y_bot), 1)
        pygame.draw.line(surf, GRAY, (ax_x, ax_y_bot), (ax_x + area_w, ax_y_bot), 1)

        # Y ticks
        for i in range(5):
            tick_y = ax_y_bot - int(i / 4 * area_h)
            pygame.draw.line(surf, (50, 50, 55), (ax_x, tick_y), (ax_x + area_w, tick_y), 1)
            lbl = self.small_font.render(str(int(mx * i / 4)), True, DARK_GRAY)
            surf.blit(lbl, (ax_x - lbl.get_width() - 5, tick_y - 8))

        # Bars
        for i, cnt in enumerate(bins):
            bh = int((cnt / mx) * area_h) if mx > 0 else 0
            bx = ax_x + int(i * area_w / num_bins) + 1
            by_bar = ax_y_bot - bh
            r = pygame.Rect(bx, by_bar, bar_w, bh)
            pygame.draw.rect(surf, color, r, border_radius=2)
            # Lighter top
            if bh > 4:
                pygame.draw.rect(surf, tuple(min(255, c + 40) for c in color),
                                 (bx, by_bar, bar_w, 3), border_radius=2)

        # X labels (lo and hi)
        surf.blit(self.small_font.render(f"{lo:.1f}", True, DARK_GRAY), (ax_x, ax_y_bot + 5))
        hi_lbl = self.small_font.render(f"{hi:.1f}", True, DARK_GRAY)
        surf.blit(hi_lbl, (ax_x + area_w - hi_lbl.get_width(), ax_y_bot + 5))
        mid_lbl = self.small_font.render(f"{(lo+hi)/2:.1f}", True, DARK_GRAY)
        surf.blit(mid_lbl, (ax_x + area_w // 2 - mid_lbl.get_width() // 2, ax_y_bot + 5))

        # Stats annotation
        import statistics
        mean_v = statistics.mean(values)
        std_v = statistics.pstdev(values) if len(values) > 1 else 0
        stat_txt = f"n={len(values)}  mean={mean_v:.2f}  std={std_v:.2f}"
        st = self.small_font.render(stat_txt, True, GRAY)
        surf.blit(st, (ax_x + 10, y + chart_h + 15))

        # Mean line
        mean_x = ax_x + int((mean_v - lo) / (hi - lo) * area_w)
        if ax_x < mean_x < ax_x + area_w:
            pygame.draw.line(surf, (255, 255, 100), (mean_x, ax_y_top), (mean_x, ax_y_bot), 2)
            ml = self.small_font.render("mean", True, (255, 255, 100))
            surf.blit(ml, (mean_x + 3, ax_y_top))

        return y + total_h + 15

    def _timeline(self, surf, y, events, start_time, duration):
        """Draw a timeline scatter plot of events."""
        x0 = 30
        cw = self.w - 80
        ch = 130
        pygame.draw.rect(surf, CARD_BG, (x0, y, cw, ch), border_radius=8)
        pygame.draw.rect(surf, CARD_BORDER, (x0, y, cw, ch), 1, border_radius=8)

        pad_l, pad_r = 20, 20
        area_w = cw - pad_l - pad_r
        ax_y = y + ch - 35
        ax_x = x0 + pad_l

        # Axis
        pygame.draw.line(surf, GRAY, (ax_x, ax_y), (ax_x + area_w, ax_y), 1)

        # X labels
        if duration > 0:
            for i in range(5):
                t_val = duration * i / 4
                tx = ax_x + int(i / 4 * area_w)
                pygame.draw.line(surf, DARK_GRAY, (tx, ax_y), (tx, ax_y + 5), 1)
                surf.blit(self.small_font.render(f"{t_val:.0f}s", True, DARK_GRAY), (tx - 10, ax_y + 8))

        # Plot dots by type at different y levels
        type_rows = {"Vehicle": 0, "VIP": 1, "Accident": 2}
        row_h = 22
        for evt_time, evt_type, color in events:
            if duration <= 0:
                continue
            t_offset = evt_time - start_time
            ex = ax_x + int((t_offset / duration) * area_w)
            ex = max(ax_x, min(ax_x + area_w, ex))
            row = type_rows.get(evt_type, 0)
            ey = y + 15 + row * row_h
            pygame.draw.circle(surf, color, (ex, ey + 6), 4)

        # Legend
        lx = ax_x + 5
        for name, row in type_rows.items():
            colors = {0: GREEN_ACC, 1: ACCENT2, 2: RED_ACC}
            ly = y + 15 + row * row_h
            pygame.draw.circle(surf, colors[row], (lx - 12, ly + 6), 4)

        # Legend labels on right
        ly = y + 12
        for name, c in [("Vehicle", GREEN_ACC), ("VIP", ACCENT2), ("Accident", RED_ACC)]:
            surf.blit(self.small_font.render(name, True, c), (x0 + cw - 110, ly))
            ly += row_h

        return y + ch + 15
