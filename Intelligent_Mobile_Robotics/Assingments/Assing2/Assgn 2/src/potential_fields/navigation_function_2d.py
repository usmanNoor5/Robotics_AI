"""
navigation_function_2d.py

Rimon–Koditschek navigation function implementation (analytic φ and ∇φ),
with RK4 integration and adaptive step-size controller. Designed to work with
your main script (run_task4a) which expects a NavigationFunction2D class and
a phi(q, goal, obstacles, boundary) function for visualization.

Save as: src/potential_fields/navigation_function_2d.py
"""

import numpy as np

# Default tuning knobs (can be overridden in constructor)
DEFAULT_EPSILON = 0.03   # small bias to break exact symmetry
DEFAULT_ALPHA = 2.5      # exponent applied to b_old -> b_old^ALPHA


def _to_tuple_obstacles(obstacles):
    """Normalize obstacles to list of (ox, oy, r). Accept tuples or objects with .center/.radius."""
    out = []
    if obstacles is None:
        return out
    for ob in obstacles:
        if isinstance(ob, tuple) or isinstance(ob, list):
            if len(ob) >= 3:
                out.append((float(ob[0]), float(ob[1]), float(ob[2])))
            else:
                raise ValueError("Obstacle tuples must be (x,y,r)")
        else:
            # try object-like
            c = getattr(ob, 'center', None)
            r = getattr(ob, 'radius', None)
            if c is None or r is None:
                raise ValueError("Obstacle must be (x,y,r) or object with .center and .radius")
            out.append((float(c[0]), float(c[1]), float(r)))
    return out


def _to_tuple_boundary(boundary):
    """Normalize boundary to (cx, cy, R) either from tuple or object with .center/.radius."""
    if boundary is None:
        return None
    if isinstance(boundary, tuple) or isinstance(boundary, list):
        if len(boundary) >= 3:
            return (float(boundary[0]), float(boundary[1]), float(boundary[2]))
        else:
            raise ValueError("Boundary must be (cx,cy,R)")
    else:
        c = getattr(boundary, 'center', None)
        r = getattr(boundary, 'radius', None)
        if c is None or r is None:
            raise ValueError("Boundary must be (cx,cy,R) or object with .center and .radius")
        return (float(c[0]), float(c[1]), float(r))


class NavigationFunction2D:
    def __init__(self,
                 K: float = 2.0,
                 step_size: float = 0.05,
                 max_iterations: int = 2000,
                 goal_threshold: float = 0.1,
                 epsilon: float = DEFAULT_EPSILON,
                 alpha: float = DEFAULT_ALPHA,
                 verbose: bool = False):
        """
        K: navigation function parameter
        step_size: initial dt for adaptive RK4 stepping
        max_iterations: safety cap
        goal_threshold: distance to goal to terminate
        epsilon: small bias added to obstacle betas to break symmetry
        alpha: exponent applied to the product b -> b^alpha (strengthen obstacles)
        verbose: if True, print backtracking/debug info
        """
        self.K = float(K)
        self.dt_init = float(step_size)
        self.max_iterations = int(max_iterations)
        self.goal_threshold = float(goal_threshold)
        self.EPSILON = float(epsilon)
        self.ALPHA = float(alpha)
        self.verbose = bool(verbose)

    # --------------------------------
    # β functions (RK-admissible) + gradients
    # --------------------------------
    def _beta_list_and_grad(self, q, obstacles, boundary, eps=1e-12):
        """
        Returns beta_vals, grad_betas using:
          beta0 (boundary) = 1 - ||q-c||^2 / R^2, grad = -2*(q-c)/R^2
          bi (obstacle)  = 1 - r^2 / ||q - o||^2 + EPSILON, grad = 2*r^2*(q-o)/||q-o||^4
        EPSILON has zero gradient (pure scalar shift).
        """
        q = np.asarray(q, dtype=float)
        beta_vals = []
        grad_betas = []

        boundary_t = _to_tuple_boundary(boundary)
        if boundary_t is None:
            # If no boundary provided, create a huge boundary to avoid negative beta0
            boundary_t = (0.0, 0.0, 1e6)

        cx, cy, R = boundary_t
        c = np.array([cx, cy], dtype=float)
        d2 = np.sum((q - c)**2)
        beta0 = 1.0 - (d2 / (R**2))
        grad_beta0 = -2.0 * (q - c) / (R**2)
        beta_vals.append(beta0)
        grad_betas.append(grad_beta0)

        obs_list = _to_tuple_obstacles(obstacles)
        for (ox, oy, r) in obs_list:
            o = np.array([ox, oy], dtype=float)
            vec = q - o
            d2o = np.sum(vec**2)
            if d2o < eps:
                # near center, avoid division-by-zero: nudge a tiny bit
                d2o = eps
                vec = vec + 1e-6
            # RK-admissible obstacle beta with small epsilon bias
            bi = 1.0 - (r**2) / d2o + self.EPSILON
            grad_bi = 2.0 * (r**2) * vec / (d2o**2)
            beta_vals.append(bi)
            grad_betas.append(grad_bi)

        return beta_vals, grad_betas

    def _beta_product_and_grad(self, q, obstacles, boundary, eps=1e-12):
        """
        Compute raw product b_old = prod beta_i and grad_b_old = sum (prod_except_i * grad_beta_i)
        Then apply exponent ALPHA:
            b = b_old ** ALPHA
            grad_b = ALPHA * (b_old ** (ALPHA - 1)) * grad_b_old
        """
        beta_vals, grad_betas = self._beta_list_and_grad(q, obstacles, boundary, eps=eps)
        n = len(beta_vals)
        b_old = 1.0
        for bi in beta_vals:
            b_old *= bi

        # prefix/suffix trick for grad
        prefix = np.ones(n, dtype=float)
        suffix = np.ones(n, dtype=float)
        for i in range(1, n):
            prefix[i] = prefix[i-1] * beta_vals[i-1]
        for i in range(n-2, -1, -1):
            suffix[i] = suffix[i+1] * beta_vals[i+1]

        grad_b_old = np.zeros(2, dtype=float)
        for j in range(n):
            prod_except_j = prefix[j] * suffix[j]
            grad_b_old += prod_except_j * grad_betas[j]

        # clamp b_old to be positive for stability
        if b_old <= 0:
            b_old = max(b_old, 1e-16)

        b = b_old ** self.ALPHA
        grad_b = self.ALPHA * (b_old ** (self.ALPHA - 1.0)) * grad_b_old
        return b, grad_b

    # --------------------------------
    # γ (g) and ∇g
    # --------------------------------
    def _gamma(self, q, q_goal):
        q = np.asarray(q, dtype=float)
        q_goal = np.asarray(q_goal, dtype=float)
        g = np.sum((q - q_goal)**2)
        grad_g = 2.0 * (q - q_goal)
        return g, grad_g

    # --------------------------------
    # φ and ∇φ analytic
    # --------------------------------
    def phi_and_gradient(self, q, q_goal, obstacles, boundary, clamp_D=1e-14):
        """
        φ(q) = g / (g^K + b)^{1/K}
        Returns (phi_val (scalar), grad_phi (2-vector))
        """
        q = np.asarray(q, dtype=float)
        g, grad_g = self._gamma(q, q_goal)
        b, grad_b = self._beta_product_and_grad(q, obstacles, boundary)

        D = (g**self.K) + b
        if D <= clamp_D:
            D = clamp_D

        one_over_K = 1.0 / self.K
        D_pow = D ** one_over_K
        # term inside derivative
        K_term = self.K * (g**(self.K - 1)) * grad_g
        term_inside = K_term + grad_b
        D_pow_minus = D ** (one_over_K - 1.0)

        numerator = (grad_g * D) - (g * one_over_K * D_pow_minus * term_inside)
        denom = D ** (2.0 * one_over_K)
        # protect against tiny denom
        if np.all(np.abs(denom) < 1e-30):
            grad_phi = np.zeros_like(numerator)
        else:
            grad_phi = numerator / denom

        phi_val = g / D_pow
        return float(phi_val), grad_phi

    def phi(self, q, q_goal, obstacles, boundary):
        """Public φ(q) (scalar) used by plotting code."""
        return float(self.phi_and_gradient(q, q_goal, obstacles, boundary)[0])

    # --------------------------------
    # Vector field and RK4
    # --------------------------------
    def _qdot(self, q, q_goal, obstacles, boundary):
        _, grad = self.phi_and_gradient(q, q_goal, obstacles, boundary)
        return -grad

    def _rk4_step(self, q, dt, q_goal, obstacles, boundary):
        k1 = self._qdot(q, q_goal, obstacles, boundary)
        k2 = self._qdot(q + 0.5 * dt * k1, q_goal, obstacles, boundary)
        k3 = self._qdot(q + 0.5 * dt * k2, q_goal, obstacles, boundary)
        k4 = self._qdot(q + dt * k3, q_goal, obstacles, boundary)
        return q + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)

    # --------------------------------
    # Collision / boundary helpers
    # --------------------------------
    @staticmethod
    def _is_in_collision(q, obstacles, margin=1e-9):
        q = np.asarray(q, dtype=float)
        obs_list = _to_tuple_obstacles(obstacles)
        for (ox, oy, r) in obs_list:
            if np.linalg.norm(q - np.array([ox, oy])) <= r + margin:
                return True
        return False

    @staticmethod
    def _is_outside_boundary(q, boundary, margin=1e-9):
        q = np.asarray(q, dtype=float)
        b = _to_tuple_boundary(boundary)
        if b is None:
            return False
        cx, cy, R = b
        return np.linalg.norm(q - np.array([cx, cy])) >= R - margin

    # --------------------------------
    # Adaptive backtracking step (Armijo-like)
    # --------------------------------
    def _adaptive_rk4_step(self, q, q_goal, obstacles, boundary,
                          dt_init=None, min_dt=1e-6, rho=0.5, c=1e-4, max_backtrack=25):
        if dt_init is None:
            dt_init = self.dt_init
        phi_q, grad = self.phi_and_gradient(q, q_goal, obstacles, boundary)
        grad_norm_sq = float(np.dot(grad, grad))
        if grad_norm_sq < 1e-16:
            return q.copy(), 0.0, False, "tiny_gradient"

        dt = float(dt_init)
        for trial in range(max_backtrack):
            if dt < min_dt:
                return q.copy(), dt, False, "dt_below_min"
            q_new = self._rk4_step(q, dt, q_goal, obstacles, boundary)
            # safety
            if self._is_in_collision(q_new, obstacles):
                if self.verbose:
                    print(f"[backtrack] collision at dt={dt:.3e}, reducing")
                dt *= rho
                continue
            if self._is_outside_boundary(q_new, boundary):
                if self.verbose:
                    print(f"[backtrack] outside boundary at dt={dt:.3e}, reducing")
                dt *= rho
                continue
            phi_new, _ = self.phi_and_gradient(q_new, q_goal, obstacles, boundary)
            if phi_new <= phi_q - c * dt * grad_norm_sq:
                return q_new, dt, True, "accepted"
            else:
                if self.verbose:
                    print(f"[backtrack] armijo failed (phi_new={phi_new:.6e} > phi_q - c*dt*||grad||^2), dt={dt:.3e} -> reducing")
                dt *= rho
                continue
        return q.copy(), dt, False, "backtrack_failed"

    # --------------------------------
    # Path planner API (used by your main script)
    # --------------------------------
    def plan_path(self, start, goal, obstacles, boundary):
        """
        Plan path from start to goal avoiding circular obstacles and within boundary.
        Returns (path (ndarray Nx2), success (bool), info (dict)).
        """
        q = np.array(start, dtype=float)
        q_goal = np.array(goal, dtype=float)
        path = [q.copy()]

        dt_init = float(self.dt_init)

        for it in range(self.max_iterations):
            # check goal
            if np.linalg.norm(q - q_goal) < self.goal_threshold:
                info = {
                    'iterations': it,
                    'final_distance': float(np.linalg.norm(q - q_goal)),
                    'path_length': len(path),
                    'reason': 'reached_goal'
                }
                return np.array(path), True, info

            phi_q, grad = self.phi_and_gradient(q, q_goal, obstacles, boundary)
            grad_norm = np.linalg.norm(grad)
            if grad_norm < 1e-12:
                info = {
                    'iterations': it,
                    'final_distance': float(np.linalg.norm(q - q_goal)),
                    'path_length': len(path),
                    'reason': 'tiny_gradient_stuck'
                }
                return np.array(path), False, info

            q_new, dt_used, ok, reason = self._adaptive_rk4_step(q, q_goal, obstacles, boundary,
                                                                 dt_init=dt_init, min_dt=1e-8, rho=0.5, c=1e-4, max_backtrack=30)
            if not ok:
                # try tiny Euler fallback once
                if reason in ("dt_below_min", "backtrack_failed"):
                    tiny = 1e-6
                    q_fallback = q + tiny * self._qdot(q, q_goal, obstacles, boundary)
                    if (not self._is_in_collision(q_fallback, obstacles)) and (not self._is_outside_boundary(q_fallback, boundary)):
                        q = q_fallback
                        path.append(q.copy())
                        continue
                    info = {
                        'iterations': it,
                        'final_distance': float(np.linalg.norm(q - q_goal)),
                        'path_length': len(path),
                        'reason': f'step_failed:{reason}'
                    }
                    return np.array(path), False, info
                else:
                    info = {
                        'iterations': it,
                        'final_distance': float(np.linalg.norm(q - q_goal)),
                        'path_length': len(path),
                        'reason': f'step_failed:{reason}'
                    }
                    return np.array(path), False, info

            q = q_new
            path.append(q.copy())

            # adapt dt_init heuristic
            if dt_used >= dt_init * 0.999:
                dt_init = min(dt_init * 1.2, 0.5)
            else:
                dt_init = max(dt_used, 1e-8)

            # safety checks
            if self._is_in_collision(q, obstacles):
                info = {
                    'iterations': it,
                    'final_distance': float(np.linalg.norm(q - q_goal)),
                    'path_length': len(path),
                    'reason': 'collision_after_step'
                }
                return np.array(path), False, info
            if self._is_outside_boundary(q, boundary):
                info = {
                    'iterations': it,
                    'final_distance': float(np.linalg.norm(q - q_goal)),
                    'path_length': len(path),
                    'reason': 'outside_boundary_after_step'
                }
                return np.array(path), False, info

        info = {
            'iterations': self.max_iterations,
            'final_distance': float(np.linalg.norm(q - q_goal)),
            'path_length': len(path),
            'reason': 'max_iterations_reached'
        }
        return np.array(path), False, info
