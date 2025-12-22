# tb_obstacle8_point.py
# Tangent-Bug for Obstacle 8 — point robot (R=0), sensor range = 2.
# Uses Bdry.txt only for the plot frame and click validation.

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union

# ---------- Tunables ----------
EPS = 1e-5
ROBOT_RADIUS     = 0.0       # point robot per assignment
DETECTION_RADIUS = 2.0
STEP_SIZE        = 1.0
BOUND_STEP       = 0.30      # arclength increment when sliding
LEAVE_TOL        = 0.20
ANIM_STRIDE      = 2
PAUSE_SEC        = 0.004
MAX_STEPS        = 60000

OBST_FILE = "obstacles4.txt"
BDRY_FILE = "Bdry.txt"

# ---------- I/O ----------
def load_polys(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError(filename)
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
        polys.append(Polygon(pts).buffer(0))  # buffer(0) cleans rings
    return polys

def load_boundary(filename):
    if not os.path.exists(filename):
        return None
    polys = load_polys(filename)
    return polys[0] if polys else None

# ---------- Click helper ----------
def get_point_on_axis(ax, prompt, obstacles, workspace=None):
    """Reprompt if inside any obstacle or outside the workspace boundary."""
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
        if any(P.within(poly) for poly in obstacles):
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

# ---------- Tangent-Bug (point robot) with robust sliding ----------
class TangentBugPoint:
    """
    States:
      • 'to_goal' : move straight toward the goal until the segment hits a boundary
      • 'slide'   : stick to that boundary in a fixed direction; record nearest-to-goal point
      • 'to_leave': (after one full loop) move along boundary to the recorded best-leave point
    We leave early if the goal becomes visible while sliding.
    """
    def __init__(self, obstacles, start, goal):
        self.start = np.array(start, float)
        self.goal  = np.array(goal,  float)

        # Point robot => no inflation; just clean polygons
        self.polys = [p.buffer(0) for p in obstacles]
        # Build list of boundary curves: exteriors + all holes
        self.boundaries = []
        for p in self.polys:
            self.boundaries.append(LineString(p.exterior.coords))
            for r in p.interiors:
                self.boundaries.append(LineString(r.coords))
        self.L = [b.length for b in self.boundaries]
        self.union = unary_union(self.polys) if self.polys else None

        # State
        self.p = self.start.copy()
        self.path = [self.p.copy()]
        self.state = "to_goal"

        self.hit_events = []
        self.leave_events = []

        # slide state
        self.i = None           # boundary index
        self.s = None           # current arclength on boundary i
        self.dir = +1           # sliding direction (+1/-1)
        self.loop_dist = 0.0    # distance traveled along this boundary
        self.best_s = None      # arclength of nearest-to-goal point seen this loop
        self.best_d = np.inf

    # ----- geometry helpers -----
    def _los_clear(self, a, b):
        """Line-of-sight between a and b ignoring mere touching at b."""
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

    def _first_boundary_hit(self, p0, p1):
        """Return (i, hit_xy) for the closest intersection of segment p0->p1 with any boundary curve."""
        seg = LineString([tuple(p0), tuple(p1)])
        best = None
        best_d = None
        for i, b in enumerate(self.boundaries):
            inter = seg.intersection(b)
            if inter.is_empty:
                continue
            pts = []
            if inter.geom_type == "Point":
                pts = [inter]
            elif inter.geom_type in ("MultiPoint", "GeometryCollection", "LineString", "MultiLineString"):
                for g in getattr(inter, "geoms", [inter]):
                    if g.geom_type == "Point":
                        pts.append(g)
                    elif g.geom_type == "LineString":
                        # overlapping segment — take its start point
                        pts.append(Point(list(g.coords)[0]))
            for pt in pts:
                d_along = seg.project(pt)
                if d_along <= 1e-9:
                    continue
                if best is None or d_along < best_d:
                    best = (i, np.array(pt.coords[0])); best_d = d_along
        return best  # or None

    def _s_to_xy(self, s, i):
        return np.array(self.boundaries[i].interpolate(s).coords[0])

    # ----- slide helpers -----
    def _start_slide(self, i, hit_xy):
        """Initialize sliding on boundary i from hit point."""
        self.i = i
        b = self.boundaries[i]; L = self.L[i]
        self.s = b.project(Point(hit_xy))
        self.loop_dist = 0.0
        self.best_s = self.s
        self.best_d = np.linalg.norm(hit_xy - self.goal)

        # choose initial direction that immediately reduces heuristic
        s_plus  = (self.s + BOUND_STEP) % L
        s_minus = (self.s - BOUND_STEP) % L
        q_plus  = np.array(b.interpolate(s_plus ).coords[0])
        q_minus = np.array(b.interpolate(s_minus).coords[0])
        f_plus  = np.linalg.norm(q_plus  - self.goal)
        f_minus = np.linalg.norm(q_minus - self.goal)
        self.dir = +1 if f_plus <= f_minus else -1

        self.state = "slide"

    # ----- one step -----
    def step(self, step_size=STEP_SIZE):
        if self.state == "to_goal":
            # straight toward goal; if we hit, start sliding that boundary
            v = self.goal - self.p
            d = np.linalg.norm(v)
            if d <= EPS:
                self.p = self.goal.copy()
                self.path.append(self.p.copy())
                return False
            nxt = self.p + (v / d) * min(step_size, d)

            hit = self._first_boundary_hit(self.p, nxt)
            if hit is not None:
                i, hit_xy = hit
                self.p = hit_xy
                self.path.append(self.p.copy())
                self.hit_events.append((len(self.path)-1, self.p.copy()))
                self._start_slide(i, hit_xy)
            else:
                self.p = nxt
                self.path.append(self.p.copy())
            return True

        elif self.state == "slide":
            i = self.i; b = self.boundaries[i]; L = self.L[i]
            # leave immediately if goal is visible
            if self._los_clear(self.p, self.goal):
                self.leave_events.append((len(self.path)-1, self.p.copy()))
                self.state = "to_goal"
                return True

            # advance along boundary with fixed orientation
            self.s = (self.s + self.dir * BOUND_STEP) % L
            self.p = self._s_to_xy(self.s, i)
            self.path.append(self.p.copy())
            self.loop_dist += BOUND_STEP

            # update nearest-to-goal seen on this boundary
            d = np.linalg.norm(self.p - self.goal)
            if d < self.best_d - 1e-12:
                self.best_d = d; self.best_s = self.s

            # finished one full loop? go to best leave point first
            if self.loop_dist >= L - 0.5 * BOUND_STEP:
                self.state = "to_leave"
            return True

        elif self.state == "to_leave":
            i = self.i; b = self.boundaries[i]; L = self.L[i]
            # shortest-way along boundary from current s to best_s
            fwd = (self.best_s - self.s) % L
            bwd = (self.s - self.best_s) % L
            if fwd <= bwd:
                self.s = (self.s + min(fwd, BOUND_STEP)) % L
            else:
                self.s = (self.s - min(bwd, BOUND_STEP)) % L
            self.p = self._s_to_xy(self.s, i)
            self.path.append(self.p.copy())

            rem = min(fwd, bwd)
            if rem <= LEAVE_TOL:
                self.leave_events.append((len(self.path)-1, self.p.copy()))
                self.state = "to_goal"
            return True

        return False

# ---------- Main ----------
def main():
    obstacles = load_polys(OBST_FILE)
    workspace = load_boundary(BDRY_FILE)  # frame + click guards only

    fig, ax = plt.subplots(figsize=(8, 6.6))
    ax.set_aspect('equal', adjustable='box')
    ax.set_title("Obstacle 8 — Tangent Bug (point robot, sensor = 2)")

    # draw workspace frame from Bdry.txt
    if workspace is not None:
        bx, by = workspace.exterior.xy
        ax.plot(bx, by, color='black', linewidth=2.0)
        x0, y0, x1, y1 = workspace.bounds
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)

    # draw obstacles
    for poly in obstacles:
        ax.add_patch(plt.Polygon(list(poly.exterior.coords), closed=True,
                                 fill=True, fc='lightgray', alpha=0.85,
                                 edgecolor='dimgray', lw=1.0))

    # global legend
    legend_handles = [
        Line2D([], [], marker='o', color='w', markerfacecolor='g', markeredgecolor='g', label='Start'),
        Line2D([], [], marker='o', color='w', markerfacecolor='r', markeredgecolor='r', label='Goal'),
        Line2D([], [], linestyle='--', color='b', label='Path'),
        Line2D([], [], marker='o', color='w', markerfacecolor='y', markeredgecolor='k', label='Hit'),
        Line2D([], [], marker='o', color='w', markerfacecolor='m', markeredgecolor='k', label='Leave'),
    ]
    fig.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(0.98, 0.98),
               frameon=True, fontsize=9, title="Legend")
    plt.tight_layout(rect=[0, 0, 0.95, 0.95]); plt.pause(0.1)

    # choose start/goal (inside boundary, outside obstacles)
    start = get_point_on_axis(ax, "Click START", obstacles, workspace)
    goal  = get_point_on_axis(ax, "Click GOAL",  obstacles, workspace)
    ax.plot(start[0], start[1], 'go'); ax.plot(goal[0], goal[1], 'ro')
    plt.pause(0.15)

    # artists
    (line,) = ax.plot([], [], 'b--', lw=1.6)
    circ = patches.Circle(start, 0.10, fc='royalblue', ec='black', alpha=0.9)
    ax.add_patch(circ)

    bot = TangentBugPoint(obstacles, start, goal)

    step = 0
    while step < MAX_STEPS and bot.step(step_size=STEP_SIZE):
        step += 1
        if step % ANIM_STRIDE == 0:
            P = np.array(bot.path)
            line.set_data(P[:, 0], P[:, 1])
            circ.center = (P[-1, 0], P[-1, 1])
            plt.pause(PAUSE_SEC)

    # final frame
    P = np.array(bot.path)
    line.set_data(P[:, 0], P[:, 1])
    circ.center = (P[-1, 0], P[-1, 1])
    fig.suptitle("Done", fontsize=13)
    plt.show()

if __name__ == "__main__":
    main()
