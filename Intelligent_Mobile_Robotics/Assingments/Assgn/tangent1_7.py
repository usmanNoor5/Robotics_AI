# tb_collage_sequential_auto.py
# Tangent-Bug on obstacles1..7 in a 3x3 sequential "movie" collage.
# Uses Bdry.txt (if present) to fix the same plot boundary on all panels.

import os, numpy as np, matplotlib.pyplot as plt, matplotlib.patches as patches
from matplotlib.lines import Line2D
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union

# ---- Tunables ----
EPS = 1e-5
ROBOT_RADIUS = 0.5
DETECTION_RADIUS = 2.0
STEP_SIZE = 1.5         # 0.8 for more precision, 1.2 for a faster "movie"
MAX_STEPS = 30000
ANIM_STRIDE = 3
PAUSE_SEC = 0.004

# Boundary sliding
BOUND_STEP   = 0.30      # arclength step when sliding along boundary (m)
BOUND_TOL    = 1e-3
START_IGNORE = 1e-6      # ignore intersections exactly at the segment start

# ---------- I/O ----------
def load_polys(filename):
    polys = []
    with open(filename, "r") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    i = 0
    while i < len(lines):
        n = int(lines[i]); i += 1
        pts = []
        for _ in range(n):
            x, y = map(float, lines[i].split()); i += 1
            pts.append((x, y))
        polys.append(Polygon(pts).buffer(0))   # clean up
    return polys

def load_boundary(filename="Bdry.txt"):
    if not os.path.exists(filename):
        return None
    polys = load_polys(filename)
    return polys[0] if polys else None

def auto_bounds(polys, margin_ratio=0.10):
    xs, ys = [], []
    for p in polys:
        x0, y0, x1, y1 = p.bounds
        xs += [x0, x1]; ys += [y0, y1]
    if not xs: return (-25, 25, -20, 20)
    xmin, xmax = min(xs), max(xs); ymin, ymax = min(ys), max(ys)
    dx = max(xmax - xmin, 10); dy = max(ymax - ymin, 10)
    mx, my = dx * margin_ratio, dy * margin_ratio
    return (xmin - mx, xmax + mx, ymin - my, ymax + my)

# ---------- UI helpers ----------
def get_point_on_axis(ax, prompt, clearance_polys, workspace=None):
    """Click point; reject if inside clearance or outside workspace (if provided)."""
    while True:
        note = ax.annotate(prompt, xy=(0.02, 0.98), xycoords='axes fraction',
                           va='top', ha='left', fontsize=9,
                           bbox=dict(boxstyle="round,pad=0.3", fc="w", ec="k", alpha=0.85))
        plt.draw()
        clicks = plt.ginput(1, timeout=0)
        note.remove()
        if not clicks:
            raise RuntimeError("Click cancelled.")
        pt = tuple(clicks[0]); P = Point(pt)
        if any(P.within(poly) for poly in clearance_polys):
            warn = ax.annotate("Inside obstacle — click again", xy=(0.02, 0.85),
                               xycoords='axes fraction', va='top', ha='left', fontsize=9,
                               bbox=dict(boxstyle="round,pad=0.3", fc="#fee", ec="#c33", alpha=0.9), color="#900")
            plt.pause(0.9); warn.remove(); continue
        if workspace is not None and (not P.within(workspace)):
            warn = ax.annotate("Outside boundary — click inside Bdry", xy=(0.02, 0.85),
                               xycoords='axes fraction', va='top', ha='left', fontsize=9,
                               bbox=dict(boxstyle="round,pad=0.3", fc="#eef", ec="#33c", alpha=0.9), color="#003")
            plt.pause(0.9); warn.remove(); continue
        return pt

def highlight_axes(axes, active_idx):
    for j, ax in enumerate(axes):
        if not ax.get_visible(): continue
        for sp in ax.spines.values():
            if j == active_idx:
                sp.set_linewidth(2.5); sp.set_edgecolor("#1f77b4")
            else:
                sp.set_linewidth(1.0); sp.set_edgecolor("black")

# ---------- Tangent-Bug with “best-leave after one lap” ----------
class TangentBugScene:
    """
    free  → if goal not visible: hit first blocker → slide
    slide → move by arclength along that obstacle; track best point (min |q-goal|)
             - leave immediately if goal becomes visible
             - otherwise, after ~one full lap, go to best point and LEAVE (Bug1-style)
    """
    def __init__(self, obstacles, start, goal,
                 robot_radius=ROBOT_RADIUS, detection_radius=DETECTION_RADIUS):
        self.start = np.array(start, float); self.goal = np.array(goal, float)
        self.rr = float(robot_radius); self.dr = float(detection_radius)

        # Inflate obstacles & geometry
        self.raw = obstacles
        self.clearance = [p.buffer(self.rr).buffer(0) for p in self.raw]
        self.union = unary_union(self.clearance) if self.clearance else None
        self.boundaries = [LineString(c.exterior.coords) for c in self.clearance]
        self.L = [b.length for b in self.boundaries]

        # State
        self.p = self.start.copy()
        self.path = [self.p.copy()]
        self.state = "free"            # "free", "slide", "goto_best"
        self.slide_idx = None
        self.s = None
        self.dir = +1
        self.loop_dist = 0.0
        self.best_s = None
        self.best_d = np.inf

        self.hit_events, self.leave_events = [], []
        self._last_p = self.p.copy()

    # ---- geometry helpers ----
    def _los_clear(self, a, b):
        if self.union is None: return True
        seg = LineString([tuple(a), tuple(b)])
        inter = seg.intersection(self.union)
        if inter.is_empty: return True
        if inter.geom_type == "Point":
            return np.linalg.norm(np.array(inter.coords[0]) - b) < 1e-8
        if inter.geom_type.startswith("Multi") or inter.geom_type == "GeometryCollection":
            for g in inter.geoms:
                if g.geom_type == "Point" and np.linalg.norm(np.array(g.coords[0]) - b) < 1e-8:
                    continue
                return False
            return True
        return False

    def _first_blocking_obstacle(self, p, g):
        """Return (idx, s, xy) of FIRST boundary hit along segment p->g."""
        if not self.boundaries:
            return None
        seg = LineString([tuple(p), tuple(g)])
        best = None; best_d = None
        for i, poly in enumerate(self.clearance):
            inter = seg.intersection(poly.boundary)
            if inter.is_empty: continue
            pts = []
            if inter.geom_type == "Point":
                pts = [inter]
            elif inter.geom_type in ("MultiPoint","GeometryCollection","MultiLineString","LineString"):
                for q in getattr(inter, "geoms", [inter]):
                    if q.geom_type == "Point":
                        pts.append(q)
                    elif q.geom_type == "LineString":
                        pts.append(Point(list(q.coords)[0]))
            for pt in pts:
                d = seg.project(pt)
                if d <= START_IGNORE:  # ignore contact at the start point
                    continue
                if best_d is None or d < best_d:
                    s = self.boundaries[i].project(pt)
                    xy = np.array(self.boundaries[i].interpolate(s).coords[0])
                    best = (i, s, xy); best_d = d
        return best

    def _s_to_xy(self, s, i):
        return np.array(self.boundaries[i].interpolate(s).coords[0])

    def _choose_dir(self, i, s):
        """Pick boundary direction that (locally) reduces distance to goal."""
        b = self.boundaries[i]; L = self.L[i]
        s_plus  = (s + BOUND_STEP) % L
        s_minus = (s - BOUND_STEP) % L
        d_plus  = np.linalg.norm(np.array(b.interpolate(s_plus ).coords[0]) - self.goal)
        d_minus = np.linalg.norm(np.array(b.interpolate(s_minus).coords[0]) - self.goal)
        return +1 if d_plus <= d_minus else -1

    # ---- one step ----
    def step(self, step_size=STEP_SIZE):
        if self.state == "free":
            if self._los_clear(self.p, self.goal):
                v = self.goal - self.p
                d = np.linalg.norm(v)
                if d <= EPS:
                    self.p = self.goal.copy(); self.path.append(self.p.copy()); return False
                self.p = self.p + (v / d) * min(step_size, d)
                self.path.append(self.p.copy())
            else:
                blk = self._first_blocking_obstacle(self.p, self.goal)
                if blk is None:
                    v = self.goal - self.p; d = np.linalg.norm(v)
                    if d <= EPS:
                        self.p = self.goal.copy(); self.path.append(self.p.copy()); return False
                    self.p = self.p + (v / d) * min(step_size, d)
                    self.path.append(self.p.copy())
                else:
                    i, s, xy = blk
                    self.p = xy; self.path.append(self.p.copy())
                    self.hit_events.append((len(self.path)-1, self.p.copy()))
                    self.slide_idx = i; self.s = s
                    self.dir = self._choose_dir(i, s)
                    self.loop_dist = 0.0
                    self.best_s = s; self.best_d = np.linalg.norm(self.p - self.goal)
                    self.state = "slide"

        elif self.state == "slide":
            i = self.slide_idx; L = self.L[i]
            # advance along boundary
            self.s = (self.s + self.dir * BOUND_STEP) % L
            self.loop_dist += abs(BOUND_STEP)
            self.p = self._s_to_xy(self.s, i); self.path.append(self.p.copy())

            # track best boundary point to the goal
            d = np.linalg.norm(self.p - self.goal)
            if d < self.best_d - 1e-12:
                self.best_d = d; self.best_s = self.s

            # leave immediately if we can see the goal
            if self._los_clear(self.p, self.goal):
                self.leave_events.append((len(self.path)-1, self.p.copy()))
                self.state = "free"
            # otherwise, after one full lap go to the best point then leave
            elif self.loop_dist >= L - 0.5 * BOUND_STEP:
                self.state = "goto_best"

        else:  # "goto_best" — move along boundary (shortest way) to best_s, then leave
            i = self.slide_idx; L = self.L[i]
            # shortest direction to best_s
            fwd = (self.best_s - self.s) % L
            bwd = (self.s - self.best_s) % L
            if fwd <= bwd:
                self.s = (self.s + min(fwd, BOUND_STEP)) % L
            else:
                self.s = (self.s - min(bwd, BOUND_STEP)) % L
            self.p = self._s_to_xy(self.s, i); self.path.append(self.p.copy())

            # reached best point? leave even if goal still not visible
            if min(fwd, bwd) <= 0.5 * BOUND_STEP:
                self.leave_events.append((len(self.path)-1, self.p.copy()))
                self.state = "free"

        self._last_p = self.p.copy()
        return True

# ---------- Main ----------
def main():
    files = [f"obstacles{i}.txt" for i in range(1, 7+1)]
    scenes = []
    for fp in files:
        if not os.path.exists(fp): raise FileNotFoundError(fp)
        scenes.append({"name": os.path.basename(fp), "obstacles": load_polys(fp)})

    workspace = load_boundary("Bdry.txt")  # shared frame if provided

    fig, axes = plt.subplots(3, 3, figsize=(14, 10))
    axes = axes.ravel()

    # Draw scenes and set bounds
    for i in range(9):
        ax = axes[i]; ax.set_aspect('equal', adjustable='box')
        if i < len(scenes):
            sc = scenes[i]; ax.set_title(sc["name"])
            for poly in sc["obstacles"]:
                ax.add_patch(plt.Polygon(list(poly.exterior.coords), closed=True,
                                         fill=True, fc='lightgray', alpha=0.85,
                                         edgecolor='dimgray', lw=1.0))
            if workspace is not None:
                bx, by = workspace.exterior.xy
                ax.plot(bx, by, color='black', linewidth=1.8)
                x0, y0, x1, y1 = workspace.bounds
                ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
            else:
                xmin, xmax, ymin, ymax = auto_bounds(sc["obstacles"])
                ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
        else:
            ax.set_visible(False)

    # Global legend (one box)
    legend_handles = [
        Line2D([], [], marker='o', color='w', markerfacecolor='g', markeredgecolor='g', label='Start'),
        Line2D([], [], marker='o', color='w', markerfacecolor='r', markeredgecolor='r', label='Goal'),
        Line2D([], [], linestyle='--', color='b', label='Path'),
        Line2D([], [], marker='o', color='w', markerfacecolor='y', markeredgecolor='k', label='Hit'),
        Line2D([], [], marker='o', color='w', markerfacecolor='m', markeredgecolor='k', label='Leave'),
    ]
    fig.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(0.985, 0.98),
               frameon=True, fontsize=9, title="Legend")
    plt.tight_layout(rect=[0, 0, 0.95, 0.96]); plt.pause(0.1)

    # Sequential movie: pick S/G per panel, then autoplay
    for i, sc in enumerate(scenes):
        ax = axes[i]
        highlight_axes(axes, i)
        fig.suptitle(f"Panel {i+1}/{len(scenes)} — {sc['name']} | Select START then GOAL", fontsize=13)
        plt.draw()

        clearance = [p.buffer(ROBOT_RADIUS).buffer(0) for p in sc["obstacles"]]
        start = get_point_on_axis(ax, "Click START (this panel)", clearance, workspace)
        goal  = get_point_on_axis(ax, "Click GOAL (this panel)",  clearance, workspace)
        ax.plot(start[0], start[1], 'go'); ax.plot(goal[0], goal[1], 'ro'); plt.pause(0.2)

        (line,) = ax.plot([], [], 'b--', lw=1.6)
        circ = patches.Circle(start, ROBOT_RADIUS, fc='royalblue', ec='black', alpha=0.7); ax.add_patch(circ)

        bot = TangentBugScene(sc["obstacles"], start, goal,
                              robot_radius=ROBOT_RADIUS, detection_radius=DETECTION_RADIUS)

        fig.suptitle(f"Panel {i+1}/{len(scenes)} — {sc['name']} | Simulating…", fontsize=13)
        plt.draw()

        step = 0; k_hit = k_leave = 0
        while step < MAX_STEPS and bot.step(step_size=STEP_SIZE):
            step += 1
            while k_hit   < len(bot.hit_events)   and bot.hit_events[k_hit][0]   <= len(bot.path)-1:
                _, pt = bot.hit_events[k_hit];     ax.plot(pt[0], pt[1], 'yo', ms=6); k_hit += 1
            while k_leave < len(bot.leave_events) and bot.leave_events[k_leave][0] <= len(bot.path)-1:
                _, pt = bot.leave_events[k_leave]; ax.plot(pt[0], pt[1], 'mo', ms=6); k_leave += 1

            if step % ANIM_STRIDE == 0:
                P = np.array(bot.path)
                line.set_data(P[:, 0], P[:, 1])
                circ.center = (P[-1, 0], P[-1, 1])
                plt.pause(PAUSE_SEC)

        P = np.array(bot.path)
        line.set_data(P[:, 0], P[:, 1])
        circ.center = (P[-1, 0], P[-1, 1])
        plt.pause(0.8)

    highlight_axes(axes, -1)
    fig.suptitle("All panels done.", fontsize=14)
    plt.show()


if __name__ == "__main__":
    main()
