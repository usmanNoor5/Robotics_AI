import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# =====================================================
# Parameters
# =====================================================
KP = 5.0        # Attractive potential gain
ETA = 10.0        # Repulsive potential gain
INFLUENCE = 0.5  # Distance of influence
STEP_SIZE = 0.2
MAX_ITERS = 3000

# =====================================================
# Environment Definitions
# =====================================================

ENVIRONMENTS = {
    1: {  # Environment 201
        "id": 201,
        "obstacles": [
            {"center": np.array([4, 4, 4]), "radius": 2},
            {"center": np.array([7, 7, 2]), "radius": 1.5},
            {"center": np.array([6, 2, 6]), "radius": 1},
            {"center": np.array([2, 8, 3]), "radius": 1},
        ],
        "start": np.array([0.0, 0.0, 0.0]),
        "goal": np.array([8.0, 9.0, 7.0]),
    },
    2: {  # Environment 202
        "id": 202,
        "obstacles": [
            {"center": np.array([-6, -6, 0]), "radius": 2.5},
            {"center": np.array([-3, -3, 0]), "radius": 2.2},
            {"center": np.array([0, -1, 1]), "radius": 2},
            {"center": np.array([3, 1, 0]), "radius": 2.4},
            {"center": np.array([6, 4, 0]), "radius": 2.1},
            {"center": np.array([8, 7, 0]), "radius": 2},
            {"center": np.array([-2, 2.5, 1.5]), "radius": 1.8},
            {"center": np.array([4.5, -2.5, -1.2]), "radius": 1.7},
            {"center": np.array([1, 4.5, 2]), "radius": 1.6},
        ],
        "start": np.array([-9.0, -9.0, -1.0]),
        "goal": np.array([9.0, 9.0, 0.0]),
    },
    3: {  # Environment 203
        "id": 203,
        "obstacles": [
            {"center": np.array([-2, -1, 2]), "radius": 2.3},
            {"center": np.array([0, 2, 0]), "radius": 2},
            {"center": np.array([2, -2, -1]), "radius": 2.1},
            {"center": np.array([4, 3, 2]), "radius": 1.7},
            {"center": np.array([6, 1, 4]), "radius": 2},
            {"center": np.array([7, 5, 6]), "radius": 2.1},
            {"center": np.array([-4, 3, -2]), "radius": 1.8},
            {"center": np.array([-6, 1, 2]), "radius": 2},
            {"center": np.array([-5, -3, 0]), "radius": 2.2},
            {"center": np.array([1, -5, 3]), "radius": 1.6},
            {"center": np.array([3, -4, 5]), "radius": 1.8},
            {"center": np.array([5, -2, 6]), "radius": 2},
        ],
        "start": np.array([-9.0, 0.0, -9.0]),
        "goal": np.array([9.0, 9.0, 9.0]),
    },
}

# =====================================================
# Potential Field Functions
# =====================================================
def attractive_potential(q, goal):
    """Attractive potential"""
    return 0.5 * KP * np.linalg.norm(q - goal) ** 2

def repulsive_potential(q, obstacles):
    """Repulsive potential from spherical obstacles"""
    U_rep = 0.0
    for obs in obstacles:
        c, r = obs["center"], obs["radius"]
        d = np.linalg.norm(q - c) - r
        if d <= 0:
            return np.inf  # inside obstacle
        if d <= INFLUENCE:
            U_rep += 0.5 * ETA * ((1.0 / d - 1.0 / INFLUENCE) ** 2)
    return U_rep

def total_potential(q, goal, obstacles):
    return attractive_potential(q, goal) + repulsive_potential(q, obstacles)

def calc_force(q, goal, obstacles):
    """Gradient-based force"""
    eps = 1e-3
    grad = np.zeros(3)
    for i in range(3):
        dq = np.zeros(3)
        dq[i] = eps
        grad[i] = (total_potential(q + dq, goal, obstacles) -
                   total_potential(q - dq, goal, obstacles)) / (2 * eps)
    return -grad

# =====================================================
# Path Simulation
# =====================================================
def apf_3d_path(start, goal, obstacles):
    pos = np.array(start, dtype=float)
    path = [pos.copy()]

    for i in range(MAX_ITERS):
        f = calc_force(pos, goal, obstacles)
        if np.linalg.norm(f) < 1e-6:
            f += np.random.randn(3) * 0.01  # escape flat zones
        f /= np.linalg.norm(f)
        pos += STEP_SIZE * f
        path.append(pos.copy())

        if np.linalg.norm(pos - goal) < 0.3:
            print(f"✅ Goal reached in {i} iterations.")
            break

    return np.array(path)

# =====================================================
# 3D Visualization with Animation
# =====================================================
def visualize_apf_3d(start, goal, obstacles):
    path = apf_3d_path(start, goal, obstacles)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title("3D Artificial Potential Field Navigation")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    # Adjust view based on environment bounds
    all_points = np.array([obs["center"] for obs in obstacles])
    bounds = [np.min(all_points) - 3, np.max(all_points) + 3]
    ax.set_xlim(bounds)
    ax.set_ylim(bounds)
    ax.set_zlim(bounds)

    # Plot start & goal
    ax.scatter(start[0], start[1], start[2], c='green', s=80, label="Start")
    ax.scatter(goal[0], goal[1], goal[2], c='red', s=80, label="Goal")

    # Plot obstacles
    u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
    for obs in obstacles:
        cx, cy, cz = obs["center"]
        r = obs["radius"]
        x = cx + r * np.cos(u) * np.sin(v)
        y = cy + r * np.sin(u) * np.sin(v)
        z = cz + r * np.cos(v)
        ax.plot_surface(x, y, z, color='gray', alpha=0.4, linewidth=0)

    # Path animation
    path_line, = ax.plot([], [], [], 'k-', linewidth=2, label="Path")
    robot_dot, = ax.plot([], [], [], 'bo', markersize=6, label="Robot")

    plt.ion()
    for i in range(0, len(path), 2):
        path_line.set_data(path[:i, 0], path[:i, 1])
        path_line.set_3d_properties(path[:i, 2])
        robot_dot.set_data([path[i, 0]], [path[i, 1]])
        robot_dot.set_3d_properties([path[i, 2]])
        plt.pause(0.01)

    plt.ioff()
    ax.legend()
    plt.show()

# =====================================================
# Main Program
# =====================================================
if __name__ == "__main__":
    print("Select 3D Environment:")
    print("1 → Environment 201")
    print("2 → Environment 202")
    print("3 → Environment 203")
    choice = int(input("Enter choice (1–3): "))

    env = ENVIRONMENTS.get(choice, ENVIRONMENTS[1])
    print(f"\n✅ Loaded Environment {env['id']}")
    print(f"Obstacles: {len(env['obstacles'])}")
    print(f"Start: {env['start']}")
    print(f"Goal: {env['goal']}\n")

    visualize_apf_3d(env["start"], env["goal"], env["obstacles"])
