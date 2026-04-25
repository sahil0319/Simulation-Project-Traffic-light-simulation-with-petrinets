import pygame
import math
import time as _time

# ── Palette ──
BG           = (18, 18, 24)
PANEL_BG     = (28, 28, 36)
PANEL_BORDER = (60, 60, 70)
ARC_COLOR    = (100, 100, 120)
ARC_INTER    = (140, 120, 200)
TEXT_DIM     = (140, 140, 155)
TEXT_BRIGHT  = (220, 220, 230)
TRANS_FILL   = (60, 60, 140)
TRANS_BORDER = (100, 100, 200)
SCHED_FILL   = (90, 50, 140)
SCHED_BORDER = (160, 100, 255)
PLACE_EMPTY  = (45, 45, 55)
LEGEND_BG    = (30, 30, 40, 200)

# State colors
C_GREEN      = (40, 210, 80)
C_YELLOW     = (240, 200, 50)
C_REDYELLOW  = (255, 130, 40)
C_RED        = (200, 50, 50)
C_SCHED      = (180, 120, 255)

PLACE_RADIUS   = 30
TOKEN_RADIUS   = 10
TRANSITION_W   = 14
TRANSITION_H   = 38
GLOW_RADIUS    = 44
ANIM_DURATION  = 0.45


# ── Animation particle ──
class _TokenAnim:
    __slots__ = ("path", "color", "t", "duration", "alive")

    def __init__(self, path, color, duration=ANIM_DURATION):
        self.path = path
        self.color = color
        self.t = 0.0
        self.duration = duration
        self.alive = True

    def update(self, dt):
        self.t += dt
        if self.t >= self.duration:
            self.alive = False

    @property
    def pos(self):
        p = min(1.0, self.t / self.duration)
        p = p * p * (3 - 2 * p)

        if len(self.path) == 2:
            s, e = self.path
            return (s[0] + (e[0] - s[0]) * p, s[1] + (e[1] - s[1]) * p)

        total_segs = len(self.path) - 1
        seg_p = p * total_segs
        idx = min(int(seg_p), total_segs - 1)
        local_p = seg_p - idx
        s = self.path[idx]
        e = self.path[idx + 1]
        return (s[0] + (e[0] - s[0]) * local_p, s[1] + (e[1] - s[1]) * local_p)

    def draw(self, surface):
        if not self.alive:
            return
        x, y = self.pos
        ix, iy = int(x), int(y)
        p = min(1.0, self.t / self.duration)
        glow_r = int(18 * (1.0 - abs(p - 0.5) * 2) + 8)
        gs = pygame.Surface((glow_r * 4, glow_r * 4), pygame.SRCALPHA)
        a = int(90 * (1.0 - abs(p - 0.5) * 1.5))
        pygame.draw.circle(gs, (*self.color, max(0, a)), (glow_r * 2, glow_r * 2), glow_r)
        surface.blit(gs, (ix - glow_r * 2, iy - glow_r * 2))
        pygame.draw.circle(surface, self.color, (ix, iy), 7)
        pygame.draw.circle(surface, (255, 255, 255), (ix, iy), 3)


# ── Renderer ──
class PetriNetRenderer:
    def __init__(self, width, height, font_path=None):
        self.w = width
        self.h = height
        fp = font_path

        # Use a clean system font for the Petri net screen (not pixel font)
        try:
            # Try common clean sans-serif fonts
            for name in ["Arial", "Helvetica", "DejaVu Sans", "Verdana", "Segoe UI"]:
                test = pygame.font.match_font(name)
                if test:
                    self.font_title   = pygame.font.Font(test, 28)
                    self.font_section = pygame.font.Font(test, 22)
                    self.font_label   = pygame.font.Font(test, 16)
                    self.font_tiny    = pygame.font.Font(test, 13)
                    break
            else:
                raise ValueError("No system font found")
        except Exception:
            # Fallback to pygame default
            self.font_title   = pygame.font.SysFont(None, 36)
            self.font_section = pygame.font.SysFont(None, 28)
            self.font_label   = pygame.font.SysFont(None, 22)
            self.font_tiny    = pygame.font.SysFont(None, 17)

        self._prev_tokens = {}
        self._prev_active_dir = None
        self._anims: list[_TokenAnim] = []

        # Layout: dynamically centered based on screen size
        cx, cy = self.w // 2, self.h // 2 + 15
        self._center = (cx, cy)

        # Spread panels wider on larger screens
        spread_x = min(350, self.w // 3)
        spread_y = min(240, self.h // 3)

        self._dir_centers = {
            "N": (cx,            cy - spread_y),
            "S": (cx,            cy + spread_y),
            "W": (cx - spread_x, cy),
            "E": (cx + spread_x, cy),
        }

        sp = 55
        self._node_offsets = {
            "ry":       (0, -sp * 2),
            "t_endry":  (0, -sp),
            "green":    (0, 0),
            "t_endg":   (0, sp),
            "yellow":   (0, sp * 2),
            "t_endy":   (0, sp * 3),
        }

    def _abs_pos(self, direction, node_key):
        bx, by = self._dir_centers[direction]
        dx, dy = self._node_offsets[node_key]
        return (bx + dx, by + dy)

    # ── Public ──

    def draw(self, surface, net, active_direction=None):
        surface.fill(BG)

        title = self.font_title.render("Petri Net  —  Traffic Light Controller", True, TEXT_BRIGHT)
        surface.blit(title, title.get_rect(center=(self.w // 2, 30)))
        hint = self.font_tiny.render("[P] Toggle Petri Net View", True, TEXT_DIM)
        surface.blit(hint, hint.get_rect(center=(self.w // 2, 58)))

        if not net:
            msg = self.font_section.render("Adaptive Petri Net Controller not active in this mode.", True, (255, 100, 100))
            surface.blit(msg, msg.get_rect(center=(self.w // 2, self.h // 2)))
            return

        self._detect_changes(net, active_direction)

        self._anims = [a for a in self._anims if a.alive]
        for a in self._anims:
            a.update(1 / 60.0)

        # Draw inter-panel arcs (behind)
        self._draw_inter_arcs(surface)
        # Central scheduler
        self._draw_scheduler(surface, active_direction)
        # Direction panels
        for d, (bx, by) in self._dir_centers.items():
            self._draw_panel(surface, net, d, bx, by, d == active_direction)
        # Animations on top
        for a in self._anims:
            a.draw(surface)
        # Legend
        self._draw_legend(surface)

    # ── Inter-panel arcs ──

    def _draw_inter_arcs(self, surface):
        cx, cy = self._center
        for d in ["N", "S", "E", "W"]:
            t_endy_pos = self._abs_pos(d, "t_endy")
            self._draw_curved_arc(surface, t_endy_pos, (cx, cy), d, "out", ARC_INTER)
            ry_pos = self._abs_pos(d, "ry")
            self._draw_curved_arc(surface, (cx, cy), ry_pos, d, "in", ARC_INTER)

    def _draw_curved_arc(self, surface, start, end, direction, arc_type, color):
        sx, sy = start
        ex, ey = end
        mx = (sx + ex) / 2
        my = (sy + ey) / 2
        offsets = {
            "N": {"out": (35, 0),   "in": (-35, 0)},
            "S": {"out": (-35, 0),  "in": (35, 0)},
            "E": {"out": (0, 35),   "in": (0, -35)},
            "W": {"out": (0, -35),  "in": (0, 35)},
        }
        ox, oy = offsets[direction][arc_type]
        cpx, cpy = mx + ox, my + oy

        points = []
        steps = 18
        for i in range(steps + 1):
            t = i / steps
            t1 = 1 - t
            px = t1*t1*sx + 2*t1*t*cpx + t*t*ex
            py = t1*t1*sy + 2*t1*t*cpy + t*t*ey
            points.append((int(px), int(py)))

        if len(points) >= 2:
            pygame.draw.lines(surface, color, False, points, 1)

        if len(points) >= 2:
            dx = points[-1][0] - points[-2][0]
            dy = points[-1][1] - points[-2][1]
            angle = math.atan2(dy, dx)
            ax, ay = points[-1]
            ax -= int(math.cos(angle) * 12)
            ay -= int(math.sin(angle) * 12)
            a1, a2 = angle + 2.6, angle - 2.6
            l = 6
            pygame.draw.polygon(surface, color, [
                (ax, ay),
                (int(ax + math.cos(a1) * l), int(ay + math.sin(a1) * l)),
                (int(ax + math.cos(a2) * l), int(ay + math.sin(a2) * l)),
            ])

    # ── Central scheduler ──

    def _draw_scheduler(self, surface, active_direction):
        cx, cy = self._center
        pygame.draw.circle(surface, (35, 25, 50), (cx, cy), 34)
        pygame.draw.circle(surface, SCHED_BORDER, (cx, cy), 34, 2)
        pulse = 0.6 + 0.4 * math.sin(_time.time() * 3)
        gs = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*SCHED_FILL, int(40 * pulse)), (45, 45), 40)
        surface.blit(gs, (cx - 45, cy - 45))
        lbl = self.font_tiny.render("Scheduler", True, C_SCHED)
        surface.blit(lbl, lbl.get_rect(center=(cx, cy)))

    # ── State change detection ──

    def _detect_changes(self, net, active_direction):
        cur = {}
        for name, place in net.places.items():
            cur[name] = place.tokens

        if not self._prev_tokens:
            self._prev_tokens = dict(cur)
            self._prev_active_dir = active_direction
            return

        cx, cy = self._center

        for d in ["N", "S", "E", "W"]:
            ry_name = f"P_{d}_RedYellow"
            g_name  = f"P_{d}_Green"
            y_name  = f"P_{d}_Yellow"

            prev_ry = self._prev_tokens.get(ry_name, 0)
            prev_g  = self._prev_tokens.get(g_name, 0)
            prev_y  = self._prev_tokens.get(y_name, 0)
            cur_ry  = cur.get(ry_name, 0)
            cur_g   = cur.get(g_name, 0)
            cur_y   = cur.get(y_name, 0)

            # Intra-panel: RY → Green
            if prev_ry > cur_ry and cur_g > prev_g:
                s = self._abs_pos(d, "ry")
                e = self._abs_pos(d, "green")
                self._anims.append(_TokenAnim([s, e], C_GREEN))

            # Intra-panel: Green → Yellow
            if prev_g > cur_g and cur_y > prev_y:
                s = self._abs_pos(d, "green")
                e = self._abs_pos(d, "yellow")
                self._anims.append(_TokenAnim([s, e], C_YELLOW))

            # Yellow consumed → animate to scheduler
            if prev_y > cur_y and cur_g <= prev_g and cur_ry <= prev_ry:
                s = self._abs_pos(d, "t_endy")
                self._anims.append(_TokenAnim([s, (cx, cy)], C_RED, duration=0.5))

            # Token appeared in RY → animate from scheduler
            if cur_ry > prev_ry and prev_g <= cur_g and prev_y <= cur_y:
                e = self._abs_pos(d, "ry")
                self._anims.append(_TokenAnim([(cx, cy), e], C_SCHED, duration=0.5))

        # Inter-panel handoff
        if active_direction and self._prev_active_dir and active_direction != self._prev_active_dir:
            old_d = self._prev_active_dir
            new_d = active_direction
            old_bottom = self._abs_pos(old_d, "t_endy")
            new_top = self._abs_pos(new_d, "ry")
            self._anims.append(_TokenAnim(
                [old_bottom, (cx, cy), new_top],
                C_SCHED, duration=0.8
            ))

        self._prev_tokens = dict(cur)
        self._prev_active_dir = active_direction

    # ── Panel drawing ──

    def _draw_panel(self, surface, net, direction, bx, by, is_active):
        pw, ph = 210, 400
        rect = pygame.Rect(bx - pw // 2, by - ph // 2 + 10, pw, ph)

        pygame.draw.rect(surface, PANEL_BG, rect, border_radius=12)
        border_c = C_GREEN if is_active else PANEL_BORDER
        pygame.draw.rect(surface, border_c, rect, 2, border_radius=12)

        dir_names = {"N": "North  ▲", "S": "South  ▼", "E": "East  ▶", "W": "West  ◀"}
        lbl = self.font_section.render(dir_names[direction], True, border_c)
        surface.blit(lbl, lbl.get_rect(center=(bx, rect.top + 22)))

        no = self._node_offsets

        p_ry = net.places.get(f"P_{direction}_RedYellow")
        p_g  = net.places.get(f"P_{direction}_Green")
        p_y  = net.places.get(f"P_{direction}_Yellow")

        tok_ry = p_ry.tokens if p_ry else 0
        tok_g  = p_g.tokens if p_g else 0
        tok_y  = p_y.tokens if p_y else 0

        pos = {k: (bx + v[0], by + v[1]) for k, v in no.items()}

        # Intra-panel arcs
        self._draw_arc(surface, pos["ry"], pos["t_endry"])
        self._draw_arc(surface, pos["t_endry"], pos["green"])
        self._draw_arc(surface, pos["green"], pos["t_endg"])
        self._draw_arc(surface, pos["t_endg"], pos["yellow"])
        self._draw_arc(surface, pos["yellow"], pos["t_endy"])

        # Places
        self._draw_place_node(surface, pos["ry"],     "Red-Yellow", C_REDYELLOW, tok_ry)
        self._draw_place_node(surface, pos["green"],  "Green",      C_GREEN,     tok_g)
        self._draw_place_node(surface, pos["yellow"], "Yellow",     C_YELLOW,    tok_y)

        # Transitions
        self._draw_transition_node(surface, pos["t_endry"], "T₁")
        self._draw_transition_node(surface, pos["t_endg"],  "T₂")
        self._draw_transition_node(surface, pos["t_endy"],  "T₃")

        # Current state label
        state = "RED"
        state_col = C_RED
        if tok_g > 0:
            state = "GREEN"; state_col = C_GREEN
        elif tok_y > 0:
            state = "YELLOW"; state_col = C_YELLOW
        elif tok_ry > 0:
            state = "RED-YELLOW"; state_col = C_REDYELLOW

        st = self.font_label.render(f"● {state}", True, state_col)
        surface.blit(st, st.get_rect(center=(bx, rect.bottom - 18)))

    def _draw_place_node(self, surface, pos, name, color, tokens):
        x, y = int(pos[0]), int(pos[1])

        if tokens > 0:
            gs = pygame.Surface((GLOW_RADIUS * 2, GLOW_RADIUS * 2), pygame.SRCALPHA)
            pulse = 0.65 + 0.35 * math.sin(_time.time() * 4)
            alpha = int(55 * pulse)
            pygame.draw.circle(gs, (*color, alpha), (GLOW_RADIUS, GLOW_RADIUS), GLOW_RADIUS)
            surface.blit(gs, (x - GLOW_RADIUS, y - GLOW_RADIUS))

        pygame.draw.circle(surface, PLACE_EMPTY, (x, y), PLACE_RADIUS)
        ring_col = color if tokens > 0 else (75, 75, 85)
        pygame.draw.circle(surface, ring_col, (x, y), PLACE_RADIUS, 3)

        if tokens > 0:
            pygame.draw.circle(surface, color, (x, y), TOKEN_RADIUS)
            pygame.draw.circle(surface, (255, 255, 255), (x, y), 4)

        lbl = self.font_label.render(name, True, TEXT_BRIGHT if tokens > 0 else TEXT_DIM)
        surface.blit(lbl, lbl.get_rect(midleft=(x + PLACE_RADIUS + 8, y)))

    def _draw_transition_node(self, surface, pos, name):
        x, y = int(pos[0]), int(pos[1])
        rect = pygame.Rect(x - TRANSITION_W // 2, y - TRANSITION_H // 2, TRANSITION_W, TRANSITION_H)
        pygame.draw.rect(surface, TRANS_FILL, rect, border_radius=2)
        pygame.draw.rect(surface, TRANS_BORDER, rect, 2, border_radius=2)

        lbl = self.font_label.render(name, True, TEXT_DIM)
        surface.blit(lbl, lbl.get_rect(midright=(x - TRANSITION_W // 2 - 6, y)))

    def _draw_arc(self, surface, start, end):
        pygame.draw.line(surface, ARC_COLOR, (int(start[0]), int(start[1])),
                         (int(end[0]), int(end[1])), 2)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        ex = end[0] - math.cos(angle) * 14
        ey = end[1] - math.sin(angle) * 14
        a1, a2 = angle + 2.6, angle - 2.6
        l = 7
        pygame.draw.polygon(surface, ARC_COLOR, [
            (int(ex), int(ey)),
            (int(ex + math.cos(a1) * l), int(ey + math.sin(a1) * l)),
            (int(ex + math.cos(a2) * l), int(ey + math.sin(a2) * l)),
        ])

    def _draw_legend(self, surface):
        lw, lh = 220, 170
        lx, ly = self.w - lw - 15, self.h - lh - 15
        ls = pygame.Surface((lw, lh), pygame.SRCALPHA)
        ls.fill(LEGEND_BG)
        surface.blit(ls, (lx, ly))
        pygame.draw.rect(surface, PANEL_BORDER, (lx, ly, lw, lh), 1, border_radius=6)

        t = self.font_label.render("Legend", True, TEXT_BRIGHT)
        surface.blit(t, (lx + lw // 2 - t.get_width() // 2, ly + 8))

        items = [
            (C_GREEN,      "Place (active)"),
            ((75,75,85),   "Place (empty)"),
            (TRANS_FILL,   "Transition"),
            (SCHED_FILL,   "Scheduler"),
            (ARC_INTER,    "Inter-panel arc"),
        ]
        for i, (c, label) in enumerate(items):
            yy = ly + 34 + i * 26
            pygame.draw.circle(surface, c, (lx + 18, yy + 5), 6)
            lt = self.font_label.render(label, True, TEXT_DIM)
            surface.blit(lt, (lx + 32, yy - 2))
