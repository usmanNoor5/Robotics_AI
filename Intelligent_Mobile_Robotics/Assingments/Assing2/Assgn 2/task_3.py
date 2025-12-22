#!/usr/bin/env python3
"""
pf_tangentbug_compact_fixed.py
Potential Field + Bounce + Tangent-Bug wall-following (fixed).
This is the revised full script — replaces your original file.
"""
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, LineString
from collections import deque
import random
import sys

# ----------------------------
# Parameters (tweakable)
# ----------------------------
KP = 8.0
ETA = 5.0
INFLUENCE = 0.9
AREA_WIDTH = 14.0
STEP_SIZE = 0.05

BOUNCE_ATTEMPTS = 6           # try a couple more attempts
BOUNCE_MAG = 0.035
BOUNCE_STEPS = 6
BOUNCE_MICRO_SCALE = 0.6
BOUNCE_PERP_WEIGHT = 0.3     # weight for perpendicular component when combining with outward nudge

WALL_FOLLOW_MAX_STEPS = 3000
OUTWARD_OFFSET = 0.06          # push just outside boundary
MIN_STEP_FACTOR = 0.12
STEP_SHRINK_STEPS = 10

OSC_HISTORY = 6
PROGRESS_WINDOW = 6
PROGRESS_EPS = 1e-3

FORCE_ARROW_SCALE = 0.3

# ----------------------------
# Environments (polygons)
# (kept identical to your original)
# ----------------------------
A = [(3,2),(3.5,2),(3.5,7),(3,7)]
B = [(6.5,2),(7,2),(7,7),(6.5,7)]
C = [(3,2),(7,2),(7,2.5),(3,2.5)]
env301_polygons = [Polygon(A), Polygon(B), Polygon(C)]
env301_start = [5,1]
env301_goal  = [5,9]

R1 = [(2,2),(5,2),(5,3.8),(2,3.8)]
R2 = [(4.2,4.2),(7.2,4.2),(7.2,6),(4.2,6)]
R3 = [(8.2,1.5),(9.2,1.5),(9.2,8.5),(8.2,8.5)]
R4 = [(7.8,8.5),(9.8,8.5),(9.8,9.1),(7.8,9.1)]
env302_polygons = [Polygon(R1), Polygon(R2), Polygon(R3), Polygon(R4)]
env302_start = [1,1]
env302_goal  = [9.5,9.5]

C_top    = [(2,8),(10,8),(10,9),(2,9)]
C_left   = [(2,2),(3,2),(3,9),(2,9)]
C_bottom = [(2,2),(10,2),(10,3),(2,3)]
Pocket   = [(5,4),(7,4),(7,6),(5,6)]
Guide_low  = [(9.5,1),(11,1),(11,2.2),(9.5,2.2)]
Guide_high = [(9.5,9),(11,9),(11,10.2),(9.5,10.2)]
env303_polygons = [Polygon(C_top), Polygon(C_left), Polygon(C_bottom),
                   Polygon(Pocket), Polygon(Guide_low), Polygon(Guide_high)]
env303_start = [1.2,1.2]
env303_goal  = [11,10.5]

ENVIRONMENTS = {
    1: {"polygons": env301_polygons, "start": env301_start, "goal": env301_goal},
    2: {"polygons": env302_polygons, "start": env302_start, "goal": env302_goal},
    3: {"polygons": env303_polygons, "start": env303_start, "goal": env303_goal},
}

# ----------------------------
# Helpers / utilities
# ----------------------------
def log(s):
    print(f"[LOG] {s}")

def attractive_potential(x, y, goal):
    return 0.5 * KP * np.hypot(x - goal[0], y - goal[1])**2

def repulsive_potential(x, y, polygons):
    p = Point(x,y)
    min_d = float('inf')
    for poly in polygons:
        d = poly.exterior.distance(p)
        min_d = min(min_d, d)
    if min_d < 1e-6:
        min_d = 1e-6
    if min_d <= INFLUENCE:
        return 0.5 * ETA * (1.0/min_d - 1.0/INFLUENCE)**2
    return 0.0

def total_potential(x, y, goal, polygons):
    return attractive_potential(x, y, goal) + repulsive_potential(x, y, polygons)

def calc_force(x, y, goal, polygons):
    eps = 1e-3
    du_dx = (total_potential(x+eps, y, goal, polygons) - total_potential(x-eps, y, goal, polygons)) / (2*eps)
    du_dy = (total_potential(x, y+eps, goal, polygons) - total_potential(x, y-eps, goal, polygons)) / (2*eps)
    return -np.array([du_dx, du_dy])

# line intersection: allow touches (tangential) as safe; only treat crossing / interior intersection as blocking
def line_intersects_any_polygon(p1, p2, polygons):
    seg = LineString([tuple(p1), tuple(p2)])
    for poly in polygons:
        if seg.crosses(poly) or poly.contains(seg) or (seg.intersects(poly) and not seg.touches(poly)):
            return True
    return False

def project_out_of_obstacles(pos, polygons):
    p = Point(pos[0], pos[1])
    for poly in polygons:
        if poly.contains(p):
            bp = poly.exterior.interpolate(poly.exterior.project(p))
            bp_arr = np.array(bp.coords[0])
            direction = pos - bp_arr
            n = np.linalg.norm(direction)
            if n < 1e-8:
                direction = np.random.randn(2)
                n = np.linalg.norm(direction)
            return bp_arr + (direction / n) * OUTWARD_OFFSET
        d = poly.exterior.distance(p)
        if d < 0.02:
            bp = poly.exterior.interpolate(poly.exterior.project(p))
            bp_arr = np.array(bp.coords[0])
            direction = pos - bp_arr
            n = np.linalg.norm(direction)
            if n < 1e-8:
                direction = np.random.randn(2)
                n = np.linalg.norm(direction)
            return bp_arr + (direction / n) * OUTWARD_OFFSET
    return pos

def clamp_outside_polygons(candidate, polygons, margin=0.05):
    """If candidate lies inside any polygon (or too close), project it just outside the nearest boundary."""
    p = Point(candidate[0], candidate[1])
    for poly in polygons:
        if poly.contains(p) or poly.exterior.distance(p) < margin:
            bp = np.array(poly.exterior.interpolate(poly.exterior.project(p)).coords[0])
            # outward vector
            outward = candidate - bp
            n = np.linalg.norm(outward)
            if n < 1e-8:
                centroid = np.array(poly.centroid.coords[0])
                outward = bp - centroid
                n = np.linalg.norm(outward)
                if n < 1e-8:
                    outward = np.array([1.0,0.0])
                    n = 1.0
            return bp + (outward / n) * (margin + OUTWARD_OFFSET)
    return candidate

def shrink_and_try(pos, delta, polygons):
    for frac in np.linspace(1.0, MIN_STEPFactor if False else 1.0, 1):  # keep semantic but fallback
        pass
    # original functionality below (rewritten to be robust)
    for frac in np.linspace(1.0, MIN_STEP_FACTOR, STEP_SHRINK_STEPS):
        cand = pos + delta * frac
        if (not line_intersects_any_polygon(pos, cand, polygons)) and (not any(poly.contains(Point(cand[0], cand[1])) for poly in polygons)):
            cand = project_out_of_obstacles(cand, polygons)
            if not any(poly.contains(Point(cand[0], cand[1])) for poly in polygons):
                return cand, True
    return pos, False

def safe_step(pos, delta, polygons):
    """Attempt to move safely: direct, shrunk, or snapped outside."""
    candidate = pos + delta
    if (not line_intersects_any_polygon(pos, candidate, polygons)) and (not any(poly.contains(Point(candidate[0], candidate[1])) for poly in polygons)):
        return candidate
    cand, ok = shrink_and_try(pos, delta, polygons)
    if ok:
        return cand
    # fallback: project to nearest boundary + outward (robust check)
    best_bp, best_poly = None, None
    best_d = float('inf')
    for poly in polygons:
        bp = np.array(poly.exterior.interpolate(poly.exterior.project(Point(pos[0], pos[1]))).coords[0])
        d = np.linalg.norm(bp - pos)
        if d < best_d:
            best_d = d
            best_bp = bp
            best_poly = poly
    if best_bp is None:
        return pos
    exterior = best_poly.exterior
    s = exterior.project(Point(pos[0], pos[1]))
    p_on = np.array(exterior.interpolate(s).coords[0])
    ahead = np.array(exterior.interpolate((s + 1e-3) % exterior.length).coords[0])
    tangent = ahead - p_on
    tnorm = np.linalg.norm(tangent)
    if tnorm < 1e-8:
        tangent = np.random.randn(2); tnorm = np.linalg.norm(tangent)
    tangent_u = tangent / tnorm
    normal = np.array([-tangent_u[1], tangent_u[0]])
    centroid = np.array(best_poly.centroid.coords[0])
    if np.dot(normal, p_on - centroid) < 0:
        normal = -normal
    outside = p_on + normal * (OUTWARD_OFFSET + 0.02)
    if not any(poly.contains(Point(outside[0], outside[1])) for poly in polygons) and (not line_intersects_any_polygon(pos, outside, polygons)):
        return outside
    # last-resort: small jitter outwards
    jitter = p_on + normal * (OUTWARD_OFFSET + 0.04)
    if not any(poly.contains(Point(jitter[0], jitter[1])) for poly in polygons) and (not line_intersects_any_polygon(pos, jitter, polygons)):
        return jitter
    return pos

# ----------------------------
# Local minima detection
# ----------------------------
def detect_osc(prev_positions):
    if len(prev_positions) < OSC_HISTORY:
        return False
    return len(set(prev_positions)) <= 2

def detect_no_progress(prev_dists):
    if len(prev_dists) < PROGRESS_WINDOW:
        return False
    recent = list(prev_dists)[-PROGRESS_WINDOW:]
    return (max(recent) - min(recent)) < PROGRESS_EPS

# ----------------------------
# Bounce escape (reworked)
# ----------------------------
def try_bounce_escape(pos, goal, polygons):
    """
    Prefer outward normal nudges away from the nearest polygon; only accept
    candidates that are safe (segment-check + not-in-polygon). Fall back to
    perpendicular micro nudges if outward can't be applied.
    """
    pos = np.array(pos, dtype=float)
    # find nearest polygon (for reliable outward normal)
    nearest_poly = None; min_d = float('inf')
    for poly in polygons:
        d = poly.exterior.distance(Point(pos[0], pos[1]))
        if d < min_d:
            min_d = d; nearest_poly = poly

    for att in range(BOUNCE_ATTEMPTS):
        # base force-perp
        f = calc_force(pos[0], pos[1], goal, polygons)
        if np.linalg.norm(f) < 1e-8:
            perp = np.random.randn(2); perp /= (np.linalg.norm(perp)+1e-9)
        else:
            perp = np.array([-f[1], f[0]])
            n = np.linalg.norm(perp)
            if n < 1e-8:
                perp = np.random.randn(2); n = np.linalg.norm(perp)
            perp = perp / (n + 1e-9)

        # compute outward normal from nearest polygon
        if nearest_poly is not None:
            p_on = np.array(nearest_poly.exterior.interpolate(nearest_poly.exterior.project(Point(pos[0], pos[1]))).coords[0])
            centroid = np.array(nearest_poly.centroid.coords[0])
            outward = p_on - centroid
            if np.linalg.norm(outward) < 1e-8:
                outward = np.random.randn(2)
            outward_u = outward / (np.linalg.norm(outward) + 1e-9)
        else:
            outward_u = perp

        sign = 1 if (att % 2 == 0) else -1
        # combine outward nudge with a small perpendicular component to help escape tangential traps
        delta = outward_u * BOUNCE_MAG * sign + perp * (BOUNCE_MAG * BOUNCE_PERP_WEIGHT * (1 if att % 2 == 0 else -1))

        # safety: segment must not cross polygon and endpoint outside
        if line_intersects_any_polygon(pos, pos + delta, polygons):
            # try pure perpendicular smaller nudge (if segment is blocked)
            small_delta = perp * (BOUNCE_MAG * 0.6 * (1 if att % 2 == 0 else -1))
            if line_intersects_any_polygon(pos, pos + small_delta, polygons):
                continue
            delta = small_delta

        cand = safe_step(pos, delta, polygons)
        cand = project_out_of_obstacles(cand, polygons)
        if any(poly.contains(Point(cand[0], cand[1])) for poly in polygons):
            continue

        dist_before = np.linalg.norm(pos - goal)
        trial = cand.copy()
        success = False
        for _ in range(BOUNCE_STEPS):
            ff = calc_force(trial[0], trial[1], goal, polygons)
            fn = np.linalg.norm(ff)
            if fn < 1e-8:
                dirv = np.random.randn(2); dirv /= (np.linalg.norm(dirv)+1e-9)
            else:
                dirv = ff / fn
            micro_delta = dirv * STEP_SIZE * BOUNCE_MICRO_SCALE
            # ensure micro step is safe
            if line_intersects_any_polygon(trial, trial + micro_delta, polygons):
                break
            micro = safe_step(trial, micro_delta, polygons)
            micro = project_out_of_obstacles(micro, polygons)
            if any(poly.contains(Point(micro[0], micro[1])) for poly in polygons):
                break
            trial = micro
            if np.linalg.norm(trial - goal) < dist_before - 0.06:
                success = True
                break
        if success:
            log(f"Bounce success on attempt {att+1}")
            return trial, True
    return pos, False

# ----------------------------
# Tangent-Bug style wall-following (outside) - strengthened checks
# ----------------------------
def wall_following(start_pos, polygons, goal):
    """
    Find nearest polygon, follow its exterior from outside, check LOS to goal and escape when clear.
    This version aggressively enforces staying outside and checks for segment intersections.
    """
    pos = np.array(start_pos, dtype=float)
    p_pt = Point(pos[0], pos[1])
    nearest_poly = None
    min_d = float('inf')
    for poly in polygons:
        d = poly.exterior.distance(p_pt)
        if d < min_d:
            min_d = d
            nearest_poly = poly
    if nearest_poly is None:
        return pos, False

    exterior = nearest_poly.exterior
    perim = exterior.length
    s = exterior.project(Point(pos[0], pos[1]))
    proj_pt = np.array(exterior.interpolate(s).coords[0])
    centroid = np.array(nearest_poly.centroid.coords[0])
    outward_vec = proj_pt - centroid
    if np.linalg.norm(outward_vec) < 1e-8:
        outward_vec = np.array([1.0,0.0])
    outward_u = outward_vec / np.linalg.norm(outward_vec)
    # ensure starting just outside and segment from start->outside is safe
    start_out = proj_pt + outward_u * (OUTWARD_OFFSET + 0.01)
    if not line_intersects_any_polygon(pos, start_out, polygons):
        pos = start_out.copy()

    # Choose direction by comparing small forward/back samples (toward goal)
    small = max(0.02, STEP_SIZE*0.8)
    p_f = np.array(exterior.interpolate((s + small) % perim).coords[0])
    p_b = np.array(exterior.interpolate((s - small) % perim).coords[0])
    d_f = np.linalg.norm(p_f - goal); d_b = np.linalg.norm(p_b - goal)
    direction = 1 if d_f < d_b else -1

    last_samples = deque(maxlen=6)
    best_dist = np.linalg.norm(pos - goal)
    stuck_counter = 0

    def los_clear(a, b):
        # use the same conservative rule as PF
        return not line_intersects_any_polygon(a, b, polygons)

    advance = STEP_SIZE * 0.9
    for step in range(WALL_FOLLOW_MAX_STEPS):
        s = (s + direction * advance) % perim
        boundary_pt = np.array(exterior.interpolate(s).coords[0])

        # compute tangent and outward normal robustly
        ahead = np.array(exterior.interpolate((s + 1e-3) % perim).coords[0])
        tangent = ahead - boundary_pt
        tn = np.linalg.norm(tangent)
        if tn < 1e-8:
            tangent = np.random.randn(2); tn = np.linalg.norm(tangent)
        tangent_u = tangent / tn
        normal = np.array([-tangent_u[1], tangent_u[0]])
        if np.dot(normal, boundary_pt - centroid) < 0:
            normal = -normal

        # candidate just outside + a little forward so the robot follows boundary
        candidate_out = boundary_pt + normal * (OUTWARD_OFFSET + 0.01)
        if any(poly.contains(Point(candidate_out[0], candidate_out[1])) for poly in polygons):
            # push further out until outside or give up and flip direction
            candidate_out = boundary_pt + normal * (OUTWARD_OFFSET + 0.04)
            if any(poly.contains(Point(candidate_out[0], candidate_out[1])) for poly in polygons):
                # try flipping normal (rare)
                candidate_out = boundary_pt - normal * (OUTWARD_OFFSET + 0.04)
                if any(poly.contains(Point(candidate_out[0], candidate_out[1])) for poly in polygons):
                    direction *= -1
                    continue

        desired = candidate_out + tangent_u * (advance * 0.7)

        delta = desired - pos
        dnorm = np.linalg.norm(delta)
        maxstep = STEP_SIZE * 1.5
        if dnorm > maxstep:
            delta = delta / dnorm * maxstep

        # if stepping from pos->pos+delta would cross a polygon, reduce step or flip direction
        if line_intersects_any_polygon(pos, pos + delta, polygons):
            # try smaller forward-only along tangent
            small_desired = candidate_out + tangent_u * (advance * 0.3)
            small_delta = small_desired - pos
            if not line_intersects_any_polygon(pos, pos + small_delta, polygons) and not any(poly.contains(Point((pos+small_delta)[0], (pos+small_delta)[1])) for poly in polygons):
                new_pos = safe_step(pos, small_delta, polygons)
            else:
                # flip direction to attempt other way around obstacle
                direction *= -1
                stuck_counter += 1
                if stuck_counter > 6:
                    # push further outside a bit and continue
                    pos = candidate_out + normal * 0.03
                    stuck_counter = 0
                continue
        else:
            new_pos = safe_step(pos, delta, polygons)

        new_pos = project_out_of_obstacles(new_pos, polygons)
        if any(poly.contains(Point(new_pos[0], new_pos[1])) for poly in polygons):
            # really shouldn't happen — step outward forcibly and continue
            new_pos = boundary_pt + normal * (OUTWARD_OFFSET + 0.06) + tangent_u * (advance * 0.1)
            if any(poly.contains(Point(new_pos[0], new_pos[1])) for poly in polygons):
                direction *= -1
                continue

        dist_now = np.linalg.norm(new_pos - goal)
        if dist_now < best_dist:
            best_dist = dist_now

        key = (round(boundary_pt[0],3), round(boundary_pt[1],3))
        last_samples.append(key)
        if len(last_samples) == last_samples.maxlen:
            uniq = len(set(last_samples))
            if uniq <= 2:
                stuck_counter += 1
            else:
                stuck_counter = max(0, stuck_counter-1)

        if stuck_counter >= 6:
            direction *= -1
            stuck_counter = 0
            s = (s + direction * (advance * 4.0)) % perim
            pos = new_pos.copy()
            continue

        pos = new_pos.copy()

        # Escape: LOS must be clear and PF should point roughly outward
        if los_clear(pos, goal):
            f = calc_force(pos[0], pos[1], goal, polygons)
            fn = np.linalg.norm(f)
            if fn < 1e-8:
                continue
            f_unit = f / fn
            out_dir = pos - centroid
            if np.linalg.norm(out_dir) < 1e-8:
                continue
            out_unit = out_dir / np.linalg.norm(out_dir)
            if np.dot(f_unit, out_unit) > 0.15 and dist_now <= best_dist * 1.02:
                log("WF: LOS clear and PF outward → escaping to PF")
                return pos, True
    log("WALL FOLLOW failed (max steps)")
    return pos, False

# ----------------------------
# Main live loop
# ----------------------------
def potential_field_live(start, goal, polygons, max_iters=8000, visualize=True):
    pos = np.array(start, dtype=float)
    pos = project_out_of_obstacles(pos, polygons)
    path = [pos.copy()]

    prev_positions = deque(maxlen=OSC_HISTORY)
    prev_distances = deque(maxlen=PROGRESS_WINDOW+2)

    if visualize:
        xs = np.linspace(0, AREA_WIDTH, 160); ys = np.linspace(0, AREA_WIDTH, 160)
        X, Y = np.meshgrid(xs, ys)
        Z = np.zeros_like(X)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                Z[i,j] = total_potential(X[i,j], Y[i,j], goal, polygons)
        plt.ion()
        fig, ax = plt.subplots(figsize=(8,8))
        contour = ax.contourf(X, Y, Z, levels=100, cmap='plasma', alpha=0.8)
        fig.colorbar(contour)
        for poly in polygons:
            x, y = poly.exterior.xy
            ax.fill(x, y, color='red', alpha=0.5)
        ax.plot(goal[0], goal[1], "b*", markersize=12)
        ax.plot(start[0], start[1], "go", markersize=8)
        robot_dot, = ax.plot([], [], "ko", markersize=6)
        path_line, = ax.plot([], [], "k-", linewidth=2)
        force_arrow = ax.arrow(pos[0], pos[1], 0, 0, head_width=0.12, fc='cyan', ec='cyan')
        ax.set_xlim(0, AREA_WIDTH); ax.set_ylim(0, AREA_WIDTH); ax.grid(True)
    else:
        robot_dot = path_line = force_arrow = None

    for it in range(max_iters):
        f_raw = calc_force(pos[0], pos[1], goal, polygons)
        f_norm = np.linalg.norm(f_raw)
        if f_norm < 1e-8:
            step_dir = np.random.randn(2); step_dir /= (np.linalg.norm(step_dir)+1e-9)
        else:
            step_dir = f_raw / f_norm

        dist = np.linalg.norm(pos - goal)
        log(f"PF step {it}: pos={pos}, dist={dist:.3f}, f_norm={f_norm:.3f}")

        prev_positions.append((round(pos[0],2), round(pos[1],2)))
        prev_distances.append(dist)

        oscillation = detect_osc(prev_positions)
        no_prog = detect_no_progress(prev_distances)

        if oscillation or no_prog:
            why = "oscillation" if oscillation else "no-progress"
            log(f"LOCAL MINIMA detected ({why}) — trying bounce")
            pos_after_bounce, escaped = try_bounce_escape(pos, goal, polygons)
            if escaped:
                pos = project_out_of_obstacles(pos_after_bounce, polygons)
                pos = clamp_outside_polygons(pos, polygons)
                path.append(pos.copy())
                prev_positions.clear(); prev_distances.clear()
                log("Escaped LM via bounce → resuming PF")
                if visualize:
                    robot_dot.set_data([pos[0]], [pos[1]]); path_line.set_data(np.array(path)[:,0], np.array(path)[:,1]); plt.pause(0.01)
                continue
            # bounce failed → WF
            log("Bounce failed → switching to WALL FOLLOW")
            pos_after_wf, wf_escaped = wall_following(pos, polygons, goal)
            pos = project_out_of_obstacles(pos_after_wf, polygons)
            pos = clamp_outside_polygons(pos, polygons)
            path.append(pos.copy())
            prev_positions.clear(); prev_distances.clear()
            if wf_escaped:
                log("Escaped LM via WALL FOLLOW → resume PF")
            else:
                log("WF failed → small relocation")
                pos = safe_step(pos, np.random.uniform(-0.12,0.12,2), polygons)
                pos = project_out_of_obstacles(pos, polygons)
            if visualize:
                robot_dot.set_data([pos[0]], [pos[1]]); path_line.set_data(np.array(path)[:,0], np.array(path)[:,1]); plt.pause(0.01)
            continue

        # normal PF step
        delta = STEP_SIZE * step_dir
        next_pos = pos + delta
        next_pos = clamp_outside_polygons(next_pos, polygons, margin=0.05)
        if line_intersects_any_polygon(pos, next_pos, polygons):
            next_pos, ok = shrink_and_try(pos, delta, polygons)
            if not ok:
                next_pos = safe_step(pos, np.random.uniform(-OUTWARD_OFFSET, OUTWARD_OFFSET, 2), polygons)
        pos = project_out_of_obstacles(next_pos, polygons)
        path.append(pos.copy())

        # viz update
        if visualize:
            robot_dot.set_data([pos[0]], [pos[1]])
            path_line.set_data(np.array(path)[:,0], np.array(path)[:,1])
            try:
                force_arrow.remove()
            except Exception:
                pass
            f_for_arrow = calc_force(pos[0], pos[1], goal, polygons)
            fn_arrow = np.linalg.norm(f_for_arrow)
            if fn_arrow > 0:
                f_display = (f_for_arrow / fn_arrow) * FORCE_ARROW_SCALE
            else:
                f_display = np.array([0.0,0.0])
            force_arrow = ax.arrow(pos[0], pos[1], f_display[0], f_display[1], head_width=0.12, fc='cyan', ec='cyan')
            plt.pause(0.01)

        if np.linalg.norm(pos - goal) < 0.25:
            log("GOAL REACHED")
            break

    if visualize:
        plt.ioff(); plt.show()
    return path

# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    random.seed(42); np.random.seed(42)
    print("Select Environment:")
    print("1 -> Env 301")
    print("2 -> Env 302")
    print("3 -> Env 303")
    try:
        ch = int(input("Enter number: ").strip())
    except Exception:
        ch = 1
    env = ENVIRONMENTS.get(ch, ENVIRONMENTS[1])
    potential_field_live(env["start"], env["goal"], env["polygons"])
