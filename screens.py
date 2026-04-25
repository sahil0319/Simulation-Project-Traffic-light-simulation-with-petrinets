# screens.py

import pygame
import math
import io
import statistics
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
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

# Matplotlib dark style params applied once
MPL_RC = {
    "figure.facecolor": "#191919",
    "axes.facecolor": "#23232a",
    "axes.edgecolor": "#444",
    "axes.labelcolor": "#ccc",
    "text.color": "#ddd",
    "xtick.color": "#999",
    "ytick.color": "#999",
    "grid.color": "#333",
    "grid.alpha": 0.5,
    "font.size": 11,
}


def _c01(rgb):
    """Convert 0-255 RGB tuple to 0-1 for matplotlib."""
    return tuple(c / 255.0 for c in rgb)


def _fig_to_surface(fig):
    """Render a matplotlib Figure to a pygame.Surface."""
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    raw = canvas.buffer_rgba()
    size = canvas.get_width_height()
    surf = pygame.image.frombuffer(raw, size, "RGBA")
    plt.close(fig)
    return surf


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
        surface.blit(self.btn_font.render(text, True, tc),
                     self.btn_font.render(text, True, tc).get_rect(center=rect.center))


class StatsScreen:
    """Statistics dashboard using matplotlib for charts."""

    def __init__(self, screen_w, screen_h, font_path):
        self.w = screen_w
        self.h = screen_h
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
        self._cached_surface = None
        self._cached_tracker_id = None
        # Chart width in inches for matplotlib (screen_w - margins)
        self._chart_w_inches = (screen_w - 80) / 100.0

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
        tid = id(tracker)
        if self._cached_surface is None or self._cached_tracker_id != tid:
            # Show loading screen immediately so it doesn't look frozen
            surface.fill(BG)
            loading_txt = self.title_font.render("Generating Charts & Statistics...", True, WHITE)
            surface.blit(loading_txt, loading_txt.get_rect(center=(self.w // 2, self.h // 2)))
            hint_txt = self.small_font.render("Please wait a moment...", True, DARK_GRAY)
            surface.blit(hint_txt, hint_txt.get_rect(center=(self.w // 2, self.h // 2 + 40)))
            pygame.display.flip()
            
            self._cached_surface = self._render_full(tracker)
            self._cached_tracker_id = tid

        cs = self._cached_surface
        self.max_scroll = max(0, cs.get_height() - self.h + 100)
        surface.fill(BG)
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

    # ---- Full content render (called once per tracker) ----

    def _render_full(self, tracker):
        """Build the entire scrollable content surface."""
        v = tracker.get_vehicle_stats()
        vip = tracker.get_vip_stats()
        acc = tracker.get_accident_stats()
        ped = tracker.get_pedestrian_stats()

        # Collect all sections as (surface, x_offset) or None
        parts = []

        # Title
        parts.append(self._render_title("Simulation Statistics"))

        # Overview
        parts.append(self._render_section("Overview", ACCENT))
        parts.append(self._render_kv([
            ("Duration", f"{tracker.duration:.1f}s"),
            ("Game Mode", tracker.game_mode or "N/A"),
            ("Total Vehicles", str(v["total"])),
            ("Total Pedestrians", str(ped["total"])),
            ("VIP Events", str(vip["total"])),
            ("Accidents", str(acc["total"])),
            ("Fatalities", str(acc["total_fatalities"])),
        ]))

        # Vehicle Stats
        parts.append(self._render_section("Vehicle Spawns", GREEN_ACC))
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
        parts.append(self._render_kv(items))

        if v["type_freq"]:
            parts.append(self._mpl_bar_h("Vehicle Type Distribution", v["type_freq"], GREEN_ACC))
        if v["dir_freq"]:
            parts.append(self._mpl_bar_h("Vehicle Direction Distribution", v["dir_freq"], ACCENT))

        # Wait time by rate
        wait_dict = tracker.get_avg_wait_time_by_rate()
        if wait_dict:
            fmt = {f"{int(r)} ppm": val for r, val in wait_dict.items()}
            if fmt:
                parts.append(self._mpl_bar_v("Avg Wait Time (sec) by Ped Rate", fmt, ACCENT))

        # Vehicle IAT histogram
        v_iats = tracker._inter_arrival_times(tracker.vehicle_spawns)
        if len(v_iats) > 3:
            parts.append(self._mpl_histogram("Vehicle Inter-Arrival Times (sec)", v_iats, GREEN_ACC))

        # Driving Behavior
        parts.append(self._render_section("Driving Behavior", ACCENT2))
        pg = v["preferred_gap_stats"]
        sg = v["stop_line_gap_stats"]
        parts.append(self._render_kv([
            ("Following Gap Dist.", "Normal(mu=12, sig=4) min=5"),
            ("Observed Mean", f"{pg['mean']:.2f}  std={pg['std']:.2f}" if pg["count"] > 0 else "N/A"),
            ("Stop-Line Gap Dist.", "Normal(mu=8, sig=3) min=5"),
            ("Observed Mean", f"{sg['mean']:.2f}  std={sg['std']:.2f}" if sg["count"] > 0 else "N/A"),
        ]))
        gaps = [g["preferred_gap"] for g in tracker.vehicle_gaps]
        if len(gaps) > 3:
            parts.append(self._mpl_histogram("Following Gap Distribution", gaps, ACCENT2))

        # VIP Stats
        parts.append(self._render_section("VIP Convoy Events", ACCENT2))
        vitems = [
            ("Total Events", str(vip["total"])),
            ("Distribution", "Exponential(lam=1/45)"),
            ("Expected Mean", "45.0s"),
        ]
        vi = vip["iat_stats"]
        if vi["count"] > 0:
            vitems.append(("Observed Mean IAT", f"{vi['mean']:.2f}s  std={vi['std']:.2f}"))
        parts.append(self._render_kv(vitems))
        if vip["dir_freq"]:
            parts.append(self._mpl_bar_h("VIP Direction", vip["dir_freq"], ACCENT2))

        # Accident Stats
        parts.append(self._render_section("Accident Events", RED_ACC))
        aitems = [
            ("Total Accidents", str(acc["total"])),
            ("Total Fatalities", str(acc["total_fatalities"])),
            ("Distribution", "Exponential(lam=1/60)"),
            ("Expected Mean", "60.0s"),
        ]
        ai = acc["iat_stats"]
        if ai["count"] > 0:
            aitems.append(("Observed Mean IAT", f"{ai['mean']:.2f}s  std={ai['std']:.2f}"))
        parts.append(self._render_kv(aitems))
        if acc["type_freq"]:
            parts.append(self._mpl_bar_h("Accident Types", acc["type_freq"], RED_ACC))

        acc_per_min = tracker.get_accidents_per_min_by_rate()
        if acc_per_min:
            fmt_acc = {f"{int(r)} ppm": val for r, val in acc_per_min.items()}
            if fmt_acc:
                parts.append(self._mpl_bar_v("Accidents per Minute by Ped Rate", fmt_acc, RED_ACC))

        # Collision Model
        parts.append(self._render_section("Theoretical Collision Model", WHITE))
        parts.append(self._render_kv([
            ("Equation", "Rate = base + (P_hit * λ_c * λ_p * s_c * s_p)"),
            ("P_hit (Base hit prob)", f"{P_HIT}"),
            ("λ_c (Car spawn rate)", f"{LAMBDA_C} cars/min"),
            ("s_c (Car cross time)", f"{S_C} min"),
            ("s_p (Ped cross time)", f"{S_P} min"),
            ("Base Rate", f"{BASELINE_RATE_P_MIN} acc/min"),
        ]))

        # Pedestrian Stats
        parts.append(self._render_section("Pedestrian Events", PED_COLOR))
        pitems = [
            ("Total Spawned", str(ped["total"])),
            ("Spawn Rate", f"{ped['spawn_rate_ppm']:.0f} per minute"),
            ("Distribution", f"Exponential(lam={ped['spawn_rate_ppm']/60:.2f})"),
        ]
        pi = ped["iat_stats"]
        if pi["count"] > 0:
            pitems.append(("Observed Mean IAT", f"{pi['mean']:.2f}s  std={pi['std']:.2f}"))
        parts.append(self._render_kv(pitems))
        if ped["crossing_freq"]:
            parts.append(self._mpl_bar_h("Crossing Location", ped["crossing_freq"], PED_COLOR))

        p_iats = tracker._inter_arrival_times(tracker.pedestrian_spawns)
        if len(p_iats) > 3:
            parts.append(self._mpl_histogram("Pedestrian Inter-Arrival Times (sec)", p_iats, PED_COLOR))

        # Event Timeline
        all_events = []
        for e in tracker.vehicle_spawns:
            all_events.append((e["time"], "Vehicle", GREEN_ACC))
        for e in tracker.vip_spawns:
            all_events.append((e["time"], "VIP", ACCENT2))
        for e in tracker.accident_spawns:
            all_events.append((e["time"], "Accident", RED_ACC))
        if len(all_events) > 2:
            parts.append(self._render_section("Event Timeline", WHITE))
            parts.append(self._mpl_timeline(all_events, tracker.start_time or 0, tracker.duration))

        # Assemble all parts vertically
        total_h = sum(p.get_height() + 8 for p in parts) + 60
        final = pygame.Surface((self.w, total_h))
        final.fill(BG)
        y = 20
        for p in parts:
            x = (self.w - p.get_width()) // 2
            final.blit(p, (x, y))
            y += p.get_height() + 8
        return final

    # ---- Pygame-rendered helpers ----

    def _render_title(self, text):
        s = pygame.Surface((self.w, 60), pygame.SRCALPHA)
        t = self.title_font.render(text, True, WHITE)
        s.blit(t, t.get_rect(center=(self.w // 2, 30)))
        return s

    def _render_section(self, title, color):
        s = pygame.Surface((self.w - 40, 48), pygame.SRCALPHA)
        txt = self.section_font.render(title, True, color)
        s.blit(txt, (10, 5))
        pygame.draw.line(s, color, (10, 42), (self.w - 60, 42), 2)
        return s

    def _render_kv(self, items):
        cw = self.w - 60
        row_h = 34
        ch = len(items) * row_h + 20
        s = pygame.Surface((cw, ch), pygame.SRCALPHA)
        pygame.draw.rect(s, CARD_BG, (0, 0, cw, ch), border_radius=8)
        pygame.draw.rect(s, CARD_BORDER, (0, 0, cw, ch), 1, border_radius=8)
        cy = 12
        for label, value in items:
            s.blit(self.body_font.render(label, True, GRAY), (18, cy))
            s.blit(self.body_font.render(value, True, WHITE), (cw // 2 + 30, cy))
            cy += row_h
        return s

    # ---- Matplotlib chart helpers ----

    def _mpl_bar_h(self, title, freq, color):
        """Horizontal bar chart."""
        with plt.rc_context(MPL_RC):
            sorted_items = sorted(freq.items(), key=lambda kv: kv[1])
            labels = [str(k) for k, _ in sorted_items]
            vals = [v for _, v in sorted_items]
            h = max(1.8, len(labels) * 0.45 + 0.8)
            fig, ax = plt.subplots(figsize=(self._chart_w_inches, h))
            ax.barh(labels, vals, color=_c01(color), edgecolor=_c01(color), linewidth=0.5, height=0.6)
            ax.set_title(title, fontsize=13, pad=8)
            for i, v in enumerate(vals):
                ax.text(v + max(vals) * 0.02, i, str(v), va="center", fontsize=10, color="#ddd")
            ax.set_xlim(0, max(vals) * 1.2 if vals else 1)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout(pad=0.5)
            return _fig_to_surface(fig)

    def _mpl_bar_v(self, title, freq, color):
        """Vertical bar chart."""
        with plt.rc_context(MPL_RC):
            try:
                sorted_items = sorted(freq.items(), key=lambda kv: float(str(kv[0]).replace(' ppm', '')))
            except:
                sorted_items = sorted(freq.items(), key=lambda kv: kv[0])
            labels = [str(k) for k, v in sorted_items]
            vals = [v for k, v in sorted_items]
            fig, ax = plt.subplots(figsize=(self._chart_w_inches, 2.5))
            bars = ax.bar(labels, vals, color=_c01(color), edgecolor=_c01(color), width=0.5)
            ax.set_title(title, fontsize=13, pad=8)
            for bar, v in zip(bars, vals):
                label = f"{v:.2f}" if isinstance(v, float) else str(v)
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        label, ha="center", va="bottom", fontsize=10, color="#ddd")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout(pad=0.5)
            return _fig_to_surface(fig)

    def _mpl_histogram(self, title, values, color):
        """Histogram with mean line and stats annotation."""
        with plt.rc_context(MPL_RC):
            fig, ax = plt.subplots(figsize=(self._chart_w_inches, 2.8))
            ax.hist(values, bins=min(15, max(5, len(values) // 3)),
                    color=_c01(color), edgecolor="#333", alpha=0.85)
            mean_v = statistics.mean(values)
            std_v = statistics.pstdev(values) if len(values) > 1 else 0
            ax.axvline(mean_v, color="#ffff66", linewidth=2, linestyle="--", label=f"mean={mean_v:.2f}")
            ax.set_title(title, fontsize=13, pad=8)
            ax.set_xlabel("Value")
            ax.set_ylabel("Count")
            ax.legend(loc="upper right", fontsize=9)
            stat_txt = f"n={len(values)}  μ={mean_v:.2f}  σ={std_v:.2f}"
            ax.text(0.02, 0.95, stat_txt, transform=ax.transAxes, fontsize=9,
                    va="top", color="#aaa", bbox=dict(boxstyle="round,pad=0.3", facecolor="#222", alpha=0.7))
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout(pad=0.5)
            return _fig_to_surface(fig)

    def _mpl_timeline(self, events, start_time, duration):
        """Scatter-plot timeline of events."""
        with plt.rc_context(MPL_RC):
            fig, ax = plt.subplots(figsize=(self._chart_w_inches, 2.0))
            type_y = {"Vehicle": 1, "VIP": 2, "Accident": 3}
            for evt_time, evt_type, color in events:
                t = evt_time - start_time
                y = type_y.get(evt_type, 1)
                ax.scatter(t, y, color=_c01(color), s=18, zorder=3, alpha=0.8)
            ax.set_yticks([1, 2, 3])
            ax.set_yticklabels(["Vehicle", "VIP", "Accident"])
            ax.set_xlabel("Time (s)")
            ax.set_title("Event Timeline", fontsize=13, pad=8)
            ax.set_xlim(0, max(duration, 1))
            ax.set_ylim(0.5, 3.5)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout(pad=0.5)
            return _fig_to_surface(fig)
