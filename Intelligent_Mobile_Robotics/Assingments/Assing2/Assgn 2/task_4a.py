# task_4a_FINAL_FIXED.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import os
import math

# ---------------------------
# Scene / dataset (your CSV)
# ---------------------------
env_obstacles_raw = [
    # Environment 1
    {"env":1, "id":"B0","cx":0,"cy":0,"r":10,"isBoundary":True},
    {"env":1, "id":"O1","cx":0,"cy":4,"r":3.5,"isBoundary":False},
    {"env":1, "id":"O2","cx":0,"cy":-4,"r":3.5,"isBoundary":False},
    # Environment 2
    {"env":2, "id":"B0","cx":0,"cy":0,"r":10,"isBoundary":True},
    {"env":2, "id":"O1","cx":0,"cy":5,"r":2,"isBoundary":False},
    {"env":2, "id":"O2","cx":-4,"cy":1,"r":2,"isBoundary":False},
    {"env":2, "id":"O3","cx":4,"cy":1,"r":2,"isBoundary":False},
    # Environment 3
    {"env":3, "id":"B0","cx":0,"cy":0,"r":10,"isBoundary":True},
    {"env":3, "id":"O1","cx":0,"cy":5,"r":1.5,"isBoundary":False},
    {"env":3, "id":"O2","cx":3,"cy":1,"r":2,"isBoundary":False},
    {"env":3, "id":"O3","cx":-4,"cy":-2,"r":1,"isBoundary":False},
    {"env":3, "id":"O4","cx":2,"cy":-4,"r":2,"isBoundary":False},
    {"env":3, "id":"O5","cx":-1,"cy":-6,"r":2,"isBoundary":False},
]

start_goal = {
    1: {"start": np.array([-8.0, 0.0]), "goal": np.array([8.0, 0.0])},
    2: {"start": np.array([0.0, 0.0]), "goal": np.array([0.0, 9.0])},
    3: {"start": np.array([-6.8, -6.8]), "goal": np.array([6.8, 6.8])},
}

# ---------------------------
# Helpers: build environment
# ---------------------------
def build_env(env_id):
    obs = [o for o in env_obstacles_raw if o["env"] == env_id]
    boundary = None
    obstacles = []
    for o in obs:
        if o["isBoundary"]:
            boundary = {"c": np.array([o["cx"], o["cy"]], dtype=float), "r": float(o["r"]), "id": o["id"]}
        else:
            obstacles.append({"c": np.array([o["cx"], o["cy"]], dtype=float), "r": float(o["r"]), "id": o["id"]})
    return boundary, obstacles

# ---------------------------
# REVISED Navigation Function - FIXED CORE ISSUES
# ---------------------------
def gamma(q, q_goal):
    """Distance to goal squared - CORRECT"""
    d = q - q_goal
    val = float(d.dot(d))
    grad = 2.0 * d
    return val, grad

def beta_obstacle(q, c, r):
    """Obstacle function - positive outside, negative inside"""
    d = q - c
    dist = np.linalg.norm(d)
    if dist > 1e-12:
        grad = d / dist
    else:
        grad = np.array([1.0, 0.0])  # Arbitrary direction away
    return dist - r, grad

def beta_boundary(q, c, r):
    """Boundary function - positive inside, negative outside"""
    d = q - c
    dist = np.linalg.norm(d)
    if dist > 1e-12:
        grad = -d / dist  # Points inward
    else:
        grad = -np.array([1.0, 0.0])
    return r - dist, grad

def beta_total_and_grad(q, obstacles, boundary, safety_margin=0.09):
    """Product of all beta functions - FIXED IMPLEMENTATION"""
    betas = []
    grads = []
    
    # Internal obstacles with safety margin
    for ob in obstacles:
        b, g = beta_obstacle(q, ob["c"], ob["r"] + safety_margin)
        betas.append(b)
        grads.append(g)
    
    # Boundary with safety margin
    if boundary is not None:
        b0, g0 = beta_boundary(q, boundary["c"], boundary["r"] - safety_margin)
        betas.append(b0)
        grads.append(g0)
    
    if len(betas) == 0:
        return 1.0, np.zeros(2)
    
    # CRITICAL FIX: Handle near-collision cases properly
    min_beta = min(betas)
    if min_beta < 0.1:  # Too close to obstacle
        # Strong repulsion from the most critical obstacle
        critical_idx = np.argmin(betas)
        beta_val = betas[critical_idx]
        grad_beta = grads[critical_idx]
        # Scale by inverse distance for strong repulsion
        repulsion = 1.0 / (abs(beta_val) + 0.01)
        return beta_val, repulsion * grad_beta
    
    # Normal case: product of betas
    beta_prod = 1.0
    for b in betas:
        beta_prod *= b
    
    # Gradient of product using product rule
    grad_beta = np.zeros(2)
    for i in range(len(betas)):
        partial_prod = 1.0
        for j in range(len(betas)):
            if i != j:
                partial_prod *= betas[j]
        grad_beta += partial_prod * grads[i]
    
    return beta_prod, grad_beta

def phi_and_grad(q, q_goal, obstacles, boundary, K):
    """Navigation function - COMPLETELY REVISED"""
    gamma_val, grad_gamma = gamma(q, q_goal)
    beta_val, grad_beta = beta_total_and_grad(q, obstacles, boundary)
    
    # CRITICAL FIX: Handle near-obstacle cases
    if beta_val < 0.05:  # Too close to obstacle
        # Pure obstacle avoidance - ignore goal
        phi = -beta_val  # Make it positive for minimization
        grad_phi = -grad_beta
        return phi, grad_phi, gamma_val, beta_val
    
    # Normal navigation function case
    denominator = (gamma_val**K + beta_val)**(1/K)
    
    if denominator < 1e-12:
        # Fallback to direct goal attraction
        phi = gamma_val
        grad_phi = grad_gamma
    else:
        phi = gamma_val / denominator
        
        # CORRECT gradient computation
        term1 = grad_gamma / denominator
        term2 = (gamma_val / (K * denominator**(K + 1))) * grad_beta
        grad_phi = term1 - term2
    
    return float(phi), grad_phi, gamma_val, beta_val

# ---------------------------
# SIMULATION - MAJOR IMPROVEMENTS
# ---------------------------
def simulate(env_id,
             K=2.0,  # Lower K values work better
             alpha=0.02,  # Larger step size
             tol=0.1,
             max_iters=5000,  # Reduced iterations
             safety_margin=0.3):
    
    boundary, obstacles = build_env(env_id)
    q = start_goal[env_id]["start"].astype(float).copy()
    q_goal = start_goal[env_id]["goal"].astype(float).copy()
    traj = [q.copy()]
    reached = False
    collided = False
    collision_ob = None
    
    print(f"\n--- Sim Env {env_id} | K={K} alpha={alpha} ---")
    print(f"Start: {q}, Goal: {q_goal}")
    
    for it in range(max_iters):
        current_dist = np.linalg.norm(q - q_goal)
        
        # Progress reporting
        if it % 500 == 0:
            print(f"it={it}, dist_to_goal={current_dist:.4f}")
        
        # Check if reached goal
        if current_dist < tol:
            print(f"SUCCESS: Reached goal at iteration {it}")
            reached = True
            break
        
        # Compute navigation function
        phi_val, grad_phi, gamma_val, beta_val = phi_and_grad(q, q_goal, obstacles, boundary, K)
        grad_norm = np.linalg.norm(grad_phi)
        
        # CRITICAL: If gradient is too small, use direct goal direction
        if grad_norm < 1e-8:
            goal_dir = (q_goal - q) / (current_dist + 1e-12)
            grad_phi = goal_dir
            grad_norm = 1.0
        
        # Normalize gradient for consistent step size
        step_direction = grad_phi / grad_norm
        
        # Adaptive step size based on environment
        adaptive_alpha = alpha
        
        # Reduce step size near obstacles
        min_obstacle_dist = float('inf')
        for ob in obstacles:
            dist_to_ob = np.linalg.norm(q - ob["c"]) - ob["r"]
            min_obstacle_dist = min(min_obstacle_dist, dist_to_ob)
        
        if min_obstacle_dist < 1.0:
            adaptive_alpha = alpha * 0.5
        if min_obstacle_dist < 0.5:
            adaptive_alpha = alpha * 0.2
        
        # Take step
        q_new = q - adaptive_alpha * step_direction
        
        # Collision check
        collision_detected = False
        for ob in obstacles:
            if np.linalg.norm(q_new - ob["c"]) < ob["r"] + 0.05:  # Small margin
                collision_detected = True
                collision_ob = ob["id"]
                break
        
        if collision_detected:
            print(f"COLLISION with {collision_ob} at iteration {it}")
            collided = True
            break
        
        q = q_new
        traj.append(q.copy())
    
    if not reached and not collided:
        final_dist = np.linalg.norm(q - q_goal)
        print(f"MAX ITERS: Final distance: {final_dist:.4f}")
    
    return np.array(traj), reached, collided, it, collision_ob

# ---------------------------
# Visualization (unchanged)
# ---------------------------
def plot_heatmap_and_traj(env_id, traj, K, savepath=None, grid_N=150):
    boundary, obstacles = build_env(env_id)
    q_goal = start_goal[env_id]["goal"]
    q_start = start_goal[env_id]["start"]
    
    if boundary is not None:
        cx, cy = boundary["c"]
        R = boundary["r"]
        lim = R + 0.5
    else:
        lim = 12.0
    
    xs = np.linspace(-lim, lim, grid_N)
    ys = np.linspace(-lim, lim, grid_N)
    X, Y = np.meshgrid(xs, ys)
    phi_grid = np.zeros_like(X)
    
    for i in range(grid_N):
        for j in range(grid_N):
            q = np.array([X[i,j], Y[i,j]])
            val, _, _, _ = phi_and_grad(q, q_goal, obstacles, boundary, K)
            phi_grid[i,j] = val
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot heatmap
    cf = ax.contourf(X, Y, phi_grid, levels=50, alpha=0.6)
    fig.colorbar(cf, ax=ax, label='phi(q)')
    
    # Plot obstacles
    for ob in obstacles:
        circ = Circle(tuple(ob["c"]), ob["r"], fill=True, color='red', alpha=0.7)
        ax.add_patch(circ)
        ax.text(ob["c"][0], ob["c"][1], ob["id"], ha='center', va='center', 
                fontweight='bold', color='white')
    
    if boundary is not None:
        b = Circle(tuple(boundary["c"]), boundary["r"], fill=False, 
                   linewidth=3, color='black')
        ax.add_patch(b)
    
    # Plot trajectory
    if len(traj) > 1:
        ax.plot(traj[:,0], traj[:,1], 'b-', linewidth=2, label='trajectory')
        ax.plot(traj[:,0], traj[:,1], 'go', markersize=2, alpha=0.6)
    
    ax.plot(q_start[0], q_start[1], 'go', markersize=10, label='start', 
            markeredgecolor='black')
    ax.plot(q_goal[0], q_goal[1], 'r*', markersize=15, label='goal', 
            markeredgecolor='black')
    
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect('equal')
    status = "SUCCESS" if len(traj) > 0 and np.linalg.norm(traj[-1] - q_goal) < 0.1 else "FAILED"
    ax.set_title(f"Env {env_id} - {status} (K={K}, Steps={len(traj)})")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if savepath:
        os.makedirs(os.path.dirname(savepath), exist_ok=True)
        plt.savefig(savepath, dpi=150, bbox_inches='tight')
        print(f"Saved: {savepath}")
    plt.show()

# ---------------------------
# RUN EXPERIMENTS WITH OPTIMIZED PARAMETERS
# ---------------------------
if __name__ == "__main__":
    out_dir = "./nav_outputs_fixed_v2"
    os.makedirs(out_dir, exist_ok=True)

    # OPTIMIZED PARAMETERS - Lower K values work much better
    settings = {
        1: {"K": 1.5, "alpha": 0.03},   # Simple environment
        2: {"K": 2.0, "alpha": 0.02},   # Medium complexity  
        3: {"K": 2.5, "alpha": 0.015}   # Complex environment
    }

    results = {}
    
    for env_id in [1, 2, 3]:
        s = settings[env_id]
        traj, reached, collided, iters, collision_ob = simulate(
            env_id, K=s["K"], alpha=s["alpha"], max_iters=5000)
        
        status = "SUCCESS" if reached else "COLLISION" if collided else "STUCK"
        final_dist = np.linalg.norm(traj[-1] - start_goal[env_id]['goal']) if len(traj) > 0 else float('inf')
        print(f"Env {env_id}: {status}, iters={iters}, final_dist={final_dist:.4f}")
        
        fname = os.path.join(out_dir, f"env{env_id}_K{s['K']}_FIXED.png")
        plot_heatmap_and_traj(env_id, traj, s["K"], savepath=fname)
        results[env_id] = {"status": status, "traj": traj, "reached": reached}
    
    print("\n" + "="*50)
    print("FINAL RESULTS")
    print("="*50)
    for env_id in [1, 2, 3]:
        status = results[env_id]["status"]
        final_dist = np.linalg.norm(results[env_id]["traj"][-1] - start_goal[env_id]['goal'])
        print(f"Environment {env_id}: {status} (distance: {final_dist:.4f})")