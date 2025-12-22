#!/usr/bin/env python3
"""
Full script: Potential Field navigation + PSO tuner with live PSO visualization

Save as: pf_pso_visual_full.py
Dependencies:
  - numpy
  - matplotlib
  - shapely
"""

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from collections import deque
import time
import sys

# ----------------------------
# Default Parameters (will be tuned by PSO)
# ----------------------------
KP = 10.0
ETA = 5.0
INFLUENCE = 0.9
AREA_WIDTH = 14.0
OSCILLATIONS_DETECTION_LENGTH = 5
STEP_SIZE = 0.05

# ----------------------------
# GRID 1 (Environment 101)
# ----------------------------
A1 = [(2, 2), (4, 2), (4, 4), (2, 4)]
A2 = [(6, 0), (7.5, 0), (7.5, 3), (6, 3)]
A3 = [(3, 6), (5, 6), (4, 9)]
A4 = [(8, 5), (9, 6), (9, 7), (7.5, 7.5), (7, 6)]
grid1_polygons = [Polygon(A1), Polygon(A2), Polygon(A3), Polygon(A4)]

grid1_start = [0.5, 0.5]
grid1_goal = [9.5, 8.5]

# ----------------------------
# GRID 2 (Environment 102)
# ----------------------------
B1 = [(1,1),(4,1),(4,2.5),(3.2,3.2),(2.5,2.6),(1.8,3.4),(1,2.8)]
B2 = [(5.5,0.5),(7.8,0.5),(7.8,2.2),(7.2,3.1),(6.4,2.6),(5.5,3.2)]
B3 = [(2.2,5.2),(3.8,5),(4.6,6.3),(4.2,7.6),(3.1,8.2),(2.1,7.4),(1.7,6.1)]
B4 = [(7,5),(9.2,5.4),(9.5,6.6),(8.9,7.8),(7.7,8.1),(6.8,7.3),(6.6,6)]
B5 = [(5,3.8),(6.1,4),(6.3,4.7),(5.6,5.2),(4.7,4.9),(4.5,4.2)]
grid2_polygons = [Polygon(B1), Polygon(B2), Polygon(B3), Polygon(B4), Polygon(B5)]

grid2_start = [-1, -1]
grid2_goal = [11, 9]

# ----------------------------
# GRID 3 (Environment 103)
# ----------------------------
C1 = [(1,1),(2.8,0.8),(3.6,1.6),(3.2,2.7),(2.1,3.2),(1.2,2.6),(0.8,1.8)]
C2 = [(4.5,0.5),(6.5,0.5),(7.1,1.3),(6.8,2.2),(5.7,2.8),(4.7,2.1),(4.3,1.3)]
C3 = [(8.2,0.8),(9.8,0.8),(10.4,2),(9.7,3.1),(8.6,3.4),(7.9,2.4)]
C4 = [(2.5,4.5),(3.8,4.2),(4.6,4.8),(4.9,6),(4.1,7),(2.9,7.6),(1.8,7),(1.6,5.8)]
C5 = [(6,4),(7.8,4.1),(8.7,4.9),(8.9,6.2),(8,7.3),(6.9,7.8),(5.8,7.1),(5.5,5.8),(5.6,4.7)]
C6 = [(9.2,4.8),(11.6,5.1),(11.8,6.3),(11.1,7.4),(10,8.1),(8.9,7.9),(8.3,6.8),(8.8,5.5)]
C7 = [(4.6,3.2),(5.3,3.3),(5.7,3.8),(5.5,4.3),(4.9,4.5),(4.4,4.1),(4.3,3.6)]
grid3_polygons = [Polygon(C1), Polygon(C2), Polygon(C3), Polygon(C4), Polygon(C5), Polygon(C6), Polygon(C7)]

grid3_start = [0, 0]
grid3_goal = [12, 9.5]

ENVIRONMENTS = {
    1: {"polygons": grid1_polygons, "start": grid1_start, "goal": grid1_goal},
    2: {"polygons": grid2_polygons, "start": grid2_start, "goal": grid2_goal},
    3: {"polygons": grid3_polygons, "start": grid3_start, "goal": grid3_goal},
}

# ----------------------------
# Potential Functions (param-driven)
# ----------------------------
def attractive_potential(x, y, goal, kp):
    return 0.5 * kp * np.hypot(x - goal[0], y - goal[1])**2

def repulsive_potential(x, y, polygons, eta, influence):
    min_d = float('inf')
    p = Point(x, y)
    for poly in polygons:
        d = poly.exterior.distance(p)
        if d < min_d:
            min_d = d
    if min_d < 1e-6:
        min_d = 1e-6
    if min_d <= influence:
        return 0.5 * eta * (1.0/min_d - 1.0/influence)**2
    else:
        return 0.0

def total_potential(x, y, goal, polygons, kp, eta, influence):
    return attractive_potential(x, y, goal, kp) + repulsive_potential(x, y, polygons, eta, influence)

def calc_force(x, y, goal, polygons, kp, eta, influence):
    eps = 1e-3
    du_dx = (total_potential(x + eps, y, goal, polygons, kp, eta, influence) - total_potential(x - eps, y, goal, polygons, kp, eta, influence)) / (2 * eps)
    du_dy = (total_potential(x, y + eps, goal, polygons, kp, eta, influence) - total_potential(x, y - eps, goal, polygons, kp, eta, influence)) / (2 * eps)
    return -np.array([du_dx, du_dy])

# ----------------------------
# Non-visual simulation used by PSO for fitness evaluation
# ----------------------------
def simulate_pf(start, goal, polygons, params, max_iters=2000, collision_threshold=0.15):
    """
    Run a quick, non-visual simulation using the provided params dict:
    params = {'kp':..., 'eta':..., 'influence':..., 'step':...}
    Returns (success_bool, path_length, final_dist_to_goal, collision_count)
    """
    kp = params['kp']
    eta = params['eta']
    influence = params['influence']
    step = params['step']

    pos = np.array(start, dtype=float)
    path_len = 0.0
    prev_positions = deque(maxlen=OSCILLATIONS_DETECTION_LENGTH)
    collision_count = 0
    reached = False

    for i in range(max_iters):
        f = calc_force(pos[0], pos[1], goal, polygons, kp, eta, influence)
        norm = np.linalg.norm(f)
        if norm < 1e-6:
            # small jitter to escape flat gradient
            f = np.random.randn(2) * 0.01
            norm = np.linalg.norm(f)
        f /= norm
        pos_new = pos + step * f
        path_len += np.linalg.norm(pos_new - pos)
        pos = pos_new

        # detect collision (penetration) approx - if closer than threshold to any polygon exterior
        p = Point(pos[0], pos[1])
        for poly in polygons:
            d = poly.exterior.distance(p)
            if d < collision_threshold:
                collision_count += 1
                # push away a bit
                pos += (step * f) * -0.5
                break

        prev_positions.append((round(pos[0], 3), round(pos[1], 3)))
        if len(prev_positions) == OSCILLATIONS_DETECTION_LENGTH and len(set(prev_positions)) < len(prev_positions):
            # small random nudge to try escape oscillation
            pos += np.random.uniform(-0.05, 0.05, 2)

        if np.linalg.norm(pos - goal) < 0.2:
            reached = True
            break

    final_dist = np.linalg.norm(pos - goal)
    return reached, path_len, final_dist, collision_count

# ----------------------------
# Fitness function construction
# ----------------------------
def fitness_for_params(start, goal, polygons, params):
    # Run a few short trials with small random seeds to get robust estimate
    trials = 3
    scores = []
    for t in range(trials):
        reached, path_len, final_dist, collision_count = simulate_pf(
            start, goal, polygons, params, max_iters=1500, collision_threshold=0.12
        )
        # Lower fitness is better:
        # base = final distance (if not reached) + small penalty for path length + strong penalty for collisions and failed reach
        score = final_dist + 0.002 * path_len + 1.0 * collision_count
        if not reached:
            score += 5.0  # big penalty for not reaching
        scores.append(score)
    return float(np.mean(scores))

# ----------------------------
# Visual Particle Swarm Optimization (PSO)
# ----------------------------
def run_pso(env_polygons, start, goal, n_particles=20, n_iter=30, seed=0):
    rng = np.random.RandomState(seed)
    # Search bounds for kp, eta, influence, step
    bounds = {
        'kp': (0.5, 40.0),
        'eta': (0.1, 40.0),
        'influence': (0.2, 3.0),
        'step': (0.02, 0.25)
    }

    dims = ['kp', 'eta', 'influence', 'step']
    dim_idx = {d:i for i,d in enumerate(dims)}

    # initialize particles positions and velocities
    pos = np.zeros((n_particles, len(dims)))
    vel = np.zeros_like(pos)
    pbest = np.zeros_like(pos)
    pbest_scores = np.full(n_particles, np.inf)

    for i, d in enumerate(dims):
        lo, hi = bounds[d]
        pos[:, i] = rng.uniform(lo, hi, size=n_particles)
        vel[:, i] = rng.uniform(-abs(hi-lo)*0.1, abs(hi-lo)*0.1, size=n_particles)
    gbest = None
    gbest_score = np.inf

    w = 0.72   # inertia
    c1 = 1.4   # cognitive
    c2 = 1.4   # social

    # Visualization: KP vs ETA scatter + fitness history
    plt.ion()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax_particles, ax_history = axes
    ax_particles.set_title("PSO: KP vs ETA (particles)")
    ax_particles.set_xlabel("KP")
    ax_particles.set_ylabel("ETA")
    ax_particles.grid(True)
    kp_min, kp_max = bounds['kp']
    eta_min, eta_max = bounds['eta']
    ax_particles.set_xlim(kp_min, kp_max)
    ax_particles.set_ylim(eta_min, eta_max)

    particle_scatter = ax_particles.scatter(pos[:,0], pos[:,1], s=50, c='tab:blue', label='particles')
    pbest_scatter = ax_particles.scatter(pbest[:,0], pbest[:,1], s=20, c='tab:green', label='pbest')
    gbest_plot, = ax_particles.plot([], [], 'r*', markersize=15, label='gbest')
    ax_particles.legend(loc='upper right')

    ax_history.set_title("Best fitness over iterations")
    ax_history.set_xlabel("Iteration")
    ax_history.set_ylabel("Best fitness")
    ax_history.grid(True)
    history_x = []
    history_y = []
    best_so_far = np.inf

    print("→ PSO start (visual)...")
    t0 = time.time()

    for it in range(n_iter):
        # Evaluate fitness for each particle
        for i in range(n_particles):
            candidate = {'kp': pos[i,0], 'eta': pos[i,1], 'influence': pos[i,2], 'step': pos[i,3]}
            score = fitness_for_params(start, goal, env_polygons, candidate)

            # update personal best
            if score < pbest_scores[i]:
                pbest_scores[i] = score
                pbest[i] = pos[i].copy()

            # update global best
            if score < gbest_score:
                gbest_score = score
                gbest = pos[i].copy()

        # PSO velocity & position update
        for i in range(n_particles):
            r1 = rng.rand(len(dims))
            r2 = rng.rand(len(dims))
            vel[i] = w*vel[i] + c1*r1*(pbest[i]-pos[i]) + c2*r2*(gbest-pos[i])
            pos[i] = pos[i] + vel[i]
            # clamp
            for k, d in enumerate(dims):
                lo, hi = bounds[d]
                if pos[i,k] < lo:
                    pos[i,k] = lo; vel[i,k] = 0
                if pos[i,k] > hi:
                    pos[i,k] = hi; vel[i,k] = 0

        # Update visualization
        particle_scatter.set_offsets(pos[:, :2])
        pbest_scatter.set_offsets(pbest[:, :2])
        if gbest is not None:
            gbest_plot.set_data([gbest[0]], [gbest[1]])
        # history
        if gbest_score < best_so_far:
            best_so_far = gbest_score
        history_x.append(it+1)
        history_y.append(best_so_far)
        ax_history.clear()
        ax_history.plot(history_x, history_y, '-o')
        ax_history.set_title("Best fitness over iterations")
        ax_history.set_xlabel("Iteration")
        ax_history.set_ylabel("Best fitness")
        ax_history.grid(True)

        ax_particles.set_title(f"PSO: KP vs ETA (iter {it+1}/{n_iter}) — best={best_so_far:.4f}")
        plt.pause(0.01)

        if (it+1) % 5 == 0:
            print(f"   iter {it+1}/{n_iter} — best score = {best_so_far:.4f}")

    print(f"→ PSO done in {time.time()-t0:.1f}s. Best score {best_so_far:.4f}")
    plt.ioff()
    plt.show()

    best_params = {'kp': float(gbest[0]), 'eta': float(gbest[1]), 'influence': float(gbest[2]), 'step': float(gbest[3])}
    return best_params, best_so_far

# ----------------------------
# Live Visualization (uses given params)
# ----------------------------
def potential_field_live(start, goal, polygons, params, area_width=AREA_WIDTH, step_size=None, max_iters=2000):
    pos = np.array(start, dtype=float)
    path = [pos.copy()]
    prev_positions = deque()

    kp = params['kp']
    eta = params['eta']
    influence = params['influence']
    step = params['step'] if step_size is None else step_size

    # Precompute potential field (for background)
    x_vals = np.linspace(0, area_width, 120)
    y_vals = np.linspace(0, area_width, 120)
    X, Y = np.meshgrid(x_vals, y_vals)
    Z = np.zeros_like(X)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            Z[i, j] = total_potential(X[i, j], Y[i, j], goal, polygons, kp, eta, influence)

    plt.ion()
    fig, ax = plt.subplots(figsize=(8, 8))
    contour = ax.contourf(X, Y, Z, levels=100, cmap='plasma', alpha=0.8)
    fig.colorbar(contour, label="Potential Value")

    for poly in polygons:
        x, y = poly.exterior.xy
        ax.fill(x, y, color='red', alpha=0.5)

    ax.plot(goal[0], goal[1], "b*", markersize=12, label="Goal")
    ax.plot(start[0], start[1], "go", markersize=8, label="Start")

    robot_dot, = ax.plot([], [], "ko", markersize=6)
    path_line, = ax.plot([], [], "k-", linewidth=2)
    force_arrow = ax.arrow(pos[0], pos[1], 0, 0, head_width=0.15, fc='cyan', ec='cyan')

    ax.legend()
    ax.set_xlim(0, area_width)
    ax.set_ylim(0, area_width)
    ax.set_title("Real-Time Potential Field Navigation (PSO-tuned params)")
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.grid(True)

    for i in range(max_iters):
        f = calc_force(pos[0], pos[1], goal, polygons, kp, eta, influence)
        norm = np.linalg.norm(f)
        if norm < 1e-5:
            f += np.random.randn(2) * 0.1
            norm = np.linalg.norm(f)
        f /= norm
        pos += step * f
        path.append(pos.copy())

        prev_positions.append((round(pos[0], 2), round(pos[1], 2)))
        if len(prev_positions) > OSCILLATIONS_DETECTION_LENGTH:
            prev_positions.popleft()
            if len(set(prev_positions)) < len(prev_positions):
                pos += np.random.uniform(-0.2, 0.2, 2)

        robot_dot.set_data([pos[0]], [pos[1]])
        path_line.set_data(np.array(path)[:, 0], np.array(path)[:, 1])

        force_arrow.remove()
        force_arrow = ax.arrow(pos[0], pos[1], 0.3*f[0], 0.3*f[1], head_width=0.15, fc='cyan', ec='cyan')

        plt.pause(0.01)

        if np.linalg.norm(pos - goal) < 0.2:
            print("✅ Goal reached!")
            break

    plt.ioff()
    plt.show()

# ----------------------------
# Run Simulation / PSO selection
# ----------------------------
if __name__ == '__main__':
    print("Select Environment:")
    print("1 → Grid 1 (Environment 101)")
    print("2 → Grid 2 (Environment 102)")
    print("3 → Grid 3 (Environment 103)")

    try:
        choice = int(input("Enter grid number (1–3): ").strip())
    except:
        choice = 1

    env = ENVIRONMENTS.get(choice, ENVIRONMENTS[1])
    polygons = env["polygons"]
    start = env["start"]
    goal = env["goal"]

    print(f"\nLoaded Grid {choice}")
    print(f"Obstacles: {len(polygons)}")
    print(f"Start: {start}")
    print(f"Goal: {goal}")

    # Ask whether to run PSO or use defaults
    run_pso_choice = input("Run PSO to tune params before visualizing? (y/n) [y]: ").strip().lower()
    if run_pso_choice == '' or run_pso_choice == 'y':
        best_params, best_score = run_pso(polygons, start, goal, n_particles=20, n_iter=30, seed=42)
        print(f"\nBest params found by PSO: {best_params} (score {best_score:.4f})")
    else:
        best_params = {'kp': KP, 'eta': ETA, 'influence': INFLUENCE, 'step': STEP_SIZE}
        print("Using default params:", best_params)

    # Run visual with best params
    potential_field_live(start, goal, polygons, best_params)
