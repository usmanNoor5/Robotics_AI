import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Circle
import os
import math

# ======================================================
# 3D ENVIRONMENT DATA
# ======================================================

env_obstacles_raw = [
    # Environment 5
    {"env":5,"id":"B0","cx":0,"cy":0,"cz":0,"r":10,"isBoundary":True},
    {"env":5,"id":"O1","cx":-5,"cy":-3,"cz":0,"r":2.8,"isBoundary":False},
    {"env":5,"id":"O2","cx":0,"cy":0.5,"cz":0.8,"r":2.4,"isBoundary":False},
    {"env":5,"id":"O3","cx":5,"cy":3,"cz":0,"r":2.6,"isBoundary":False},
    {"env":5,"id":"O4","cx":1.5,"cy":-1,"cz":0.8,"r":1.6,"isBoundary":False},

    # Environment 6
    {"env":6,"id":"B0","cx":0,"cy":0,"cz":0,"r":10,"isBoundary":True},
    {"env":6,"id":"O1","cx":0,"cy":5,"cz":0,"r":2.2,"isBoundary":False},
    {"env":6,"id":"O2","cx":-4,"cy":1,"cz":0,"r":2.2,"isBoundary":False},
    {"env":6,"id":"O3","cx":4,"cy":1,"cz":0,"r":2.2,"isBoundary":False},
    {"env":6,"id":"O4","cx":0,"cy":0,"cz":4.5,"r":2.0,"isBoundary":False},

    # Environment 7
    {"env":7,"id":"B0","cx":0,"cy":0,"cz":0,"r":10,"isBoundary":True},
    {"env":7,"id":"O1","cx":0,"cy":5,"cz":0,"r":2.0,"isBoundary":False},
    {"env":7,"id":"O2","cx":-4,"cy":1,"cz":0,"r":2.0,"isBoundary":False},
    {"env":7,"id":"O3","cx":4,"cy":1,"cz":0,"r":2.0,"isBoundary":False},
    {"env":7,"id":"O4","cx":0,"cy":0,"cz":5,"r":2.0,"isBoundary":False},
    {"env":7,"id":"O5","cx":0,"cy":0,"cz":-5,"r":2.0,"isBoundary":False},
]

start_goal = {
    5: {"start": np.array([-9.0,-1.0,-1.0]), "goal": np.array([9.0,1.0,1.0])},
    6: {"start": np.array([-7.5,0.0,-7.5]), "goal": np.array([7.5,0.0,7.5])},
    7: {"start": np.array([0.0,0.0,-8.0]), "goal": np.array([0.0,0.0,8.0])},
}

# ======================================================
# ENV BUILDER
# ======================================================

def build_env(env_id):
    obs = [o for o in env_obstacles_raw if o["env"] == env_id]
    boundary = None
    obstacles = []

    for o in obs:
        c = np.array([o["cx"], o["cy"], o["cz"]], dtype=float)
        if o["isBoundary"]:
            boundary = {"c": c, "r": float(o["r"]), "id": o["id"]}
        else:
            obstacles.append({"c": c, "r": float(o["r"]), "id": o["id"]})

    return boundary, obstacles

# ======================================================
# 3D Navigation Function
# ======================================================

def gamma(q, q_goal):
    d = q - q_goal
    return float(d.dot(d)), 2.0 * d

def beta_obstacle(q, c, r):
    d = q - c
    dist = np.linalg.norm(d)
    grad = d / (dist + 1e-12)
    return dist - r, grad

def beta_boundary(q, c, r):
    d = q - c
    dist = np.linalg.norm(d)
    grad = -d / (dist + 1e-12)
    return r - dist, grad

def beta_total_and_grad(q, obstacles, boundary, safety_margin=0.1):
    betas = []
    grads = []

    for ob in obstacles:
        b, g = beta_obstacle(q, ob["c"], ob["r"] + safety_margin)
        betas.append(b)
        grads.append(g)

    b0, g0 = beta_boundary(q, boundary["c"], boundary["r"] - safety_margin)
    betas.append(b0)
    grads.append(g0)

    min_beta = min(betas)
    if min_beta < 0.1:
        idx = np.argmin(betas)
        rep = 1.0 / (abs(betas[idx]) + 0.01)
        return betas[idx], rep * grads[idx]

    # Product
    beta_prod = np.prod(betas)

    # Gradient of product
    grad_beta = np.zeros(3)
    for i in range(len(betas)):
        p = np.prod([betas[j] for j in range(len(betas)) if j != i])
        grad_beta += p * grads[i]

    return beta_prod, grad_beta

def phi_and_grad(q, q_goal, obstacles, boundary, K):
    gamma_val, grad_gamma = gamma(q, q_goal)
    beta_val, grad_beta = beta_total_and_grad(q, obstacles, boundary)

    if beta_val < 0.05:
        return -beta_val, -grad_beta, gamma_val, beta_val

    denom = (gamma_val**K + beta_val)**(1.0 / K)
    phi = gamma_val / denom

    grad_phi = (grad_gamma / denom) - (
        (gamma_val / (K * denom**(K + 1))) * grad_beta
    )

    return phi, grad_phi, gamma_val, beta_val

# ======================================================
# SIMULATION 3D
# ======================================================

def simulate(env_id, K=2.0, alpha=0.03, tol=0.1, max_iters=6000):
    boundary, obstacles = build_env(env_id)
    q = start_goal[env_id]["start"].copy()
    q_goal = start_goal[env_id]["goal"].copy()
    traj = [q.copy()]

    for it in range(max_iters):
        if np.linalg.norm(q - q_goal) < tol:
            print(f"SUCCESS env {env_id} at {it}")
            break

        phi_val, grad_phi, gamma_val, beta_val = phi_and_grad(q, q_goal, obstacles, boundary, K)
        grad_norm = np.linalg.norm(grad_phi)

        if grad_norm < 1e-9:
            grad_phi = (q_goal - q) / (np.linalg.norm(q_goal - q) + 1e-12)

        step = -alpha * grad_phi / (np.linalg.norm(grad_phi) + 1e-12)
        q_new = q + step

        # Collision check
        for ob in obstacles:
            if np.linalg.norm(q_new - ob["c"]) < ob["r"]:
                print("Collision with", ob["id"])
                return np.array(traj), False

        q = q_new
        traj.append(q.copy())

    return np.array(traj), True

# ======================================================
# 3D PLOTS
# ======================================================

def plot_traj_3d(env_id, traj):
    boundary, obstacles = build_env(env_id)
    q_start = start_goal[env_id]["start"]
    q_goal = start_goal[env_id]["goal"]

    fig = plt.figure(figsize=(10,8))
    ax = fig.add_subplot(111, projection='3d')

    # Boundary
    u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
    x = boundary["c"][0] + boundary["r"]*np.cos(u)*np.sin(v)
    y = boundary["c"][1] + boundary["r"]*np.sin(u)*np.sin(v)
    z = boundary["c"][2] + boundary["r"]*np.cos(v)
    ax.plot_wireframe(x, y, z, color="gray", alpha=0.3)

    # Obstacles
    for ob in obstacles:
        u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
        x = ob["c"][0] + ob["r"]*np.cos(u)*np.sin(v)
        y = ob["c"][1] + ob["r"]*np.sin(u)*np.sin(v)
        z = ob["c"][2] + ob["r"]*np.cos(v)
        ax.plot_wireframe(x, y, z, color="red", alpha=0.5)

    # Path
    ax.plot(traj[:,0], traj[:,1], traj[:,2], 'b-', linewidth=2)
    ax.scatter(*q_start, color='green', s=80)
    ax.scatter(*q_goal, color='red', s=80)

    ax.set_title(f"3D Navigation - Env {env_id}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    plt.show()

# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    for env_id in [5,6,7]:
        traj, ok = simulate(env_id, K=2.0, alpha=0.03)
        plot_traj_3d(env_id, traj)
