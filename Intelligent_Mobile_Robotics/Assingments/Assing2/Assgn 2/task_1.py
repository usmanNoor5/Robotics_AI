import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from collections import deque

# ----------------------------
# Parameters
# ----------------------------

KP = 10.0
ETA = 5.0
INFLUENCE = 0.9
AREA_WIDTH = 14.0
OSCILLATIONS_DETECTION_LENGTH = 5
STEP_SIZE = 0.05

# # ----------------------------
# # Define Obstacles (Polygons)
# # ----------------------------

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
# ------------``----------------
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

# ----------------------------
# Dictionary for easy selection
# ----------------------------
ENVIRONMENTS = {
    1: {"polygons": grid1_polygons, "start": grid1_start, "goal": grid1_goal},
    2: {"polygons": grid2_polygons, "start": grid2_start, "goal": grid2_goal},
    3: {"polygons": grid3_polygons, "start": grid3_start, "goal": grid3_goal},
}

# ----------------------------
# Potential Functions
# ----------------------------
def attractive_potential(x, y, goal):
    return 0.5 * KP * np.hypot(x - goal[0], y - goal[1])**2

def repulsive_potential(x, y, polygons):
    min_d = float('inf')
    for poly in polygons:
        d = poly.exterior.distance(Point(x, y))
        if d < min_d:
            min_d = d
    if min_d < 1e-6:
        min_d = 1e-6
    if min_d <= INFLUENCE:
        return 0.5 * ETA * (1.0/min_d - 1.0/INFLUENCE)**2
    else:
        return 0.0

def total_potential(x, y, goal, polygons):
    return attractive_potential(x, y, goal) + repulsive_potential(x, y, polygons)

def calc_force(x, y, goal, polygons):
    eps = 1e-3
    du_dx = (total_potential(x + eps, y, goal, polygons) - total_potential(x - eps, y, goal, polygons)) / (2 * eps)
    du_dy = (total_potential(x, y + eps, goal, polygons) - total_potential(x, y - eps, goal, polygons)) / (2 * eps)
    return -np.array([du_dx, du_dy])

# ----------------------------
# Live Visualization
# ----------------------------
def potential_field_live(start, goal, polygons, step_size=STEP_SIZE, max_iters=2000):
    pos = np.array(start, dtype=float)
    path = [pos.copy()]
    prev_positions = deque()

    # Precompute potential field
    x_vals = np.linspace(0, AREA_WIDTH, 80)
    y_vals = np.linspace(0, AREA_WIDTH, 80)
    X, Y = np.meshgrid(x_vals, y_vals)
    Z = np.zeros_like(X)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            Z[i, j] = total_potential(X[i, j], Y[i, j], goal, polygons)

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
    ax.set_xlim(0, AREA_WIDTH)
    ax.set_ylim(0, AREA_WIDTH)
    ax.set_title("Real-Time Potential Field Navigation")
    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.grid(True)

    for i in range(max_iters):
        f = calc_force(pos[0], pos[1], goal, polygons)
        norm = np.linalg.norm(f)
        if norm < 1e-5:
            f += np.random.randn(2) * 0.1
            norm = np.linalg.norm(f)
        f /= norm
        pos += step_size * f
        path.append(pos.copy())

        prev_positions.append((round(pos[0], 2), round(pos[1], 2)))
        if len(prev_positions) > OSCILLATIONS_DETECTION_LENGTH:
            prev_positions.popleft()
            if len(set(prev_positions)) < len(prev_positions):
                pos += np.random.uniform(-0.2, 0.2, 2)

        # ✅ FIXED: use list values for set_data()
        robot_dot.set_data([pos[0]], [pos[1]])
        path_line.set_data(np.array(path)[:, 0], np.array(path)[:, 1])

        # Update arrow showing current force
        force_arrow.remove()
        force_arrow = ax.arrow(pos[0], pos[1], 0.3*f[0], 0.3*f[1], head_width=0.15, fc='cyan', ec='cyan')

        plt.pause(0.01)

        if np.linalg.norm(pos - goal) < 0.2:
            print("✅ Goal reached!")
            break

    plt.ioff()
    plt.show()

# ----------------------------
# Run Simulation
# ----------------------------
if __name__ == '__main__':
    print("Select Environment:")
    print("1 → Grid 1 (Environment 101)")
    print("2 → Grid 2 (Environment 102)")
    print("3 → Grid 3 (Environment 103)")

    choice = int(input("Enter grid number (1–3): "))

    # Load corresponding grid data
    env = ENVIRONMENTS.get(choice, ENVIRONMENTS[1])  # default = Grid 1
    polygons = env["polygons"]
    start = env["start"]
    goal = env["goal"]

    print(f"\n✅ Loaded Grid {choice}")
    print(f"Obstacles: {len(polygons)}")
    print(f"Start: {start}")
    print(f"Goal: {goal}")

    # Run potential field simulation
    potential_field_live(start, goal, polygons)
