import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from shapely.geometry import Point, Polygon as ShapelyPolygon

# ----------------------------
# Parameters
# ----------------------------
KP = 3.0        # Attractive gain
ETA = 100.0     # Repulsive gain
INFLUENCE = 1.5 # Influence range for obstacles
STEP_SIZE = 0.05
MAX_ITERS = 3000
GOAL_THRESHOLD = 0.2

# ----------------------------
# Obstacles (Your Polygons)
# ----------------------------
A1 = [(2,2),(4,2),(4,4),(2,4)]
A2 = [(6,0),(7.5,0),(7.5,3),(6,3)]
A3 = [(3,6),(5,6),(4,9)]
A4 = [(8,5),(9,6),(9,7),(7.5,7.5),(7,6)]
obstacles = [A1, A2, A3, A4]

# Convert to shapely polygons
obstacle_polygons = [ShapelyPolygon(o) for o in obstacles]

# ----------------------------
# Goal and Start
# ----------------------------
start = np.array([0.5, 0.5])
goal = np.array([9.0, 9.0])

# ----------------------------
# Potential Field Functions
# ----------------------------
def attractive_force(x, goal):
    """Linear attractive force toward goal"""
    return -KP * (x - goal)

def repulsive_force(x, obstacles):
    """Repulsive force from polygons"""
    total_f = np.zeros(2)
    for poly in obstacles:
        d = poly.exterior.distance(Point(x))
        if d < INFLUENCE:
            # Direction away from closest point on polygon
            nearest = np.array(poly.exterior.interpolate(poly.exterior.project(Point(x))).coords[0])
            dir_vec = (x - nearest)
            if np.linalg.norm(dir_vec) != 0:
                dir_vec /= np.linalg.norm(dir_vec)
            f = ETA * (1.0/d - 1.0/INFLUENCE) / (d**2) * dir_vec
            total_f += f
    return total_f

# ----------------------------
# Simulation
# ----------------------------
pos = start.copy()
path = [pos.copy()]

for _ in range(MAX_ITERS):
    fatt = attractive_force(pos, goal)
    frep = repulsive_force(pos, obstacle_polygons)
    ftotal = fatt + frep

    # Normalize force and take step
    if np.linalg.norm(ftotal) > 1e-5:
        ftotal /= np.linalg.norm(ftotal)
    pos += STEP_SIZE * ftotal
    path.append(pos.copy())

    # Stop if close to goal
    if np.linalg.norm(pos - goal) < GOAL_THRESHOLD:
        print("Goal reached!")
        break

path = np.array(path)

# ----------------------------
# Plot Results
# ----------------------------
fig, ax = plt.subplots(figsize=(7,7))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.set_title("Potential Field Path Planning")
ax.grid(True)

# Draw polygons
for i, poly in enumerate(obstacles, 1):
    patch = Polygon(poly, closed=True, fill=True, edgecolor='black', facecolor='red', alpha=0.4)
    ax.add_patch(patch)
    x = np.mean([p[0] for p in poly])
    y = np.mean([p[1] for p in poly])
    ax.text(x, y, f"A{i}", ha='center', va='center', fontsize=10, color='black')

# Plot path
ax.plot(start[0], start[1], 'go', markersize=8, label='Start')
ax.plot(goal[0], goal[1], 'b*', markersize=12, label='Goal')
ax.plot(path[:,0], path[:,1], 'k-', linewidth=1.5, label='Path')

ax.legend()
plt.show()
