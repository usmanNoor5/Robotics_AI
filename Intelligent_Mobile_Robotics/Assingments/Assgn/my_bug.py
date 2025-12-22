# adaptive_bug.py
# Adaptive Bug with Learning - extends HybridTangentDistBug
# hybrid_bug.py
# Hybrid Tangent-Dist Bug Algorithm

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import random

# ---------
# - Tunables ----------
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
EPS = 1e-5
ROBOT_RADIUS = 0.5
DETECTION_RADIUS = 2.0
STEP_SIZE = 1.0
BOUND_STEP = 0.30
LEAVE_TOL = 0.20
ANIM_STRIDE = 2
PAUSE_SEC = 0.004
MAX_STEPS = 60000

# Hybrid specific parameters
TANGENT_THRESHOLD = 0.9  # Distance threshold to use tangent vs boundary
MIN_OBSTACLE_CURVATURE = 0.5  # When to prefer tangent following

OBST_FILE = "obstacles6.txt"
BDRY_FILE = "Bdry.txt"

class HybridTangentDistBug:
    """
    Hybrid Strategy:
      - Uses tangent following for 'simple' obstacles (low curvature, good tangents)
      - Uses boundary following for complex obstacles (high curvature, no clear tangents)
      - Dynamically switches based on obstacle geometry and sensor data
    """
    def __init__(self, obstacles, start, goal):
        self.start = np.array(start, float)
        self.goal = np.array(goal, float)
        
        # Process obstacles
        self.polys = [p.buffer(0) for p in obstacles]
        self.boundaries = []
        for p in self.polys:
            self.boundaries.append(LineString(p.exterior.coords))
            for r in p.interiors:
                self.boundaries.append(LineString(r.coords))
        self.L = [b.length for b in self.boundaries]
        self.union = unary_union(self.polys) if self.polys else None
        
        # State machine
        self.p = self.start.copy()
        self.path = [self.p.copy()]
        self.state = "to_goal"  # to_goal, tangent_follow, boundary_follow, to_leave
        
        # Events for visualization
        self.hit_events = []
        self.leave_events = []
        self.strategy_changes = []
        
        # Boundary following state
        self.i = None
        self.s = None
        self.dir = +1
        self.loop_dist = 0.0
        self.best_s = None
        self.best_d = np.inf
        
        # Tangent following state
        self.current_tangent = None
        self.tangent_attempts = 0
        self.max_tangent_attempts = 10
        
        # Strategy decision
        self.current_strategy = None

    def _los_clear(self, a, b):
        """Check line-of-sight between points."""
        if self.union is None:
            return True
        seg = LineString([tuple(a), tuple(b)])
        inter = seg.intersection(self.union)
        if inter.is_empty:
            return True
        if inter.geom_type == "Point":
            return np.linalg.norm(np.array(inter.coords[0]) - b) < 1e-8
        return False

    def _first_boundary_hit(self, p0, p1):
        """Find first intersection with any boundary."""
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
                        pts.append(Point(list(g.coords)[0]))
            for pt in pts:
                d_along = seg.project(pt)
                if d_along <= 1e-9:
                    continue
                if best is None or d_along < best_d:
                    best = (i, np.array(pt.coords[0]))
                    best_d = d_along
        return best

    def _s_to_xy(self, s, i):
        return np.array(self.boundaries[i].interpolate(s).coords[0])

    def _calculate_obstacle_curvature(self, i, s, window=0.5):
        """Estimate local curvature of the boundary."""
        b = self.boundaries[i]
        L = self.L[i]
        
        # Sample points around current position
        s1 = (s - window) % L
        s2 = s
        s3 = (s + window) % L
        
        p1 = np.array(b.interpolate(s1).coords[0])
        p2 = np.array(b.interpolate(s2).coords[0])
        p3 = np.array(b.interpolate(s3).coords[0])
        
        # Calculate approximate curvature
        v1 = p2 - p1
        v2 = p3 - p2
        if np.linalg.norm(v1) < EPS or np.linalg.norm(v2) < EPS:
            return 0
            
        # clamp dot for numeric stability
        cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cosang = max(-1.0, min(1.0, cosang))
        angle = np.arccos(cosang)
        curvature = angle / window
        
        return curvature

    def _find_best_tangent(self, i, s):
        """Find the best tangent point toward goal."""
        b = self.boundaries[i]
        L = self.L[i]
        
        best_tangent = None
        best_score = -np.inf
        
        # Sample candidate points along the boundary
        samples = max(10, min(60, int(L)))  # more robust sampling
        for sample_s in np.linspace(0, L, samples):
            candidate = self._s_to_xy(sample_s, i)
            
            # Check if this is a reasonable tangent direction
            if self._los_clear(self.p, candidate) and self._los_clear(candidate, self.goal):
                # Score based on progress toward goal and distance
                goal_dist_reduction = np.linalg.norm(self.p - self.goal) - np.linalg.norm(candidate - self.goal)
                path_length = np.linalg.norm(candidate - self.p)
                score = goal_dist_reduction - 0.5 * path_length  # Prefer shorter detours
                
                if score > best_score:
                    best_score = score
                    best_tangent = (sample_s, candidate)
        
        return best_tangent

    def _choose_strategy(self, i, s):
        """Decide whether to use tangent or boundary following."""
        # Always try tangent first for simple cases
        curvature = self._calculate_obstacle_curvature(i, s)
        
        if curvature < MIN_OBSTACLE_CURVATURE:
            # Low curvature - good candidate for tangent following
            tangent = self._find_best_tangent(i, s)
            if tangent is not None:
                return "tangent", tangent
        
        # Default to boundary following for complex obstacles
        return "boundary", None

    def _start_boundary_follow(self, i, hit_xy):
        """Initialize boundary following."""
        self.i = i
        b = self.boundaries[i]
        L = self.L[i]
        self.s = b.project(Point(hit_xy))
        self.loop_dist = 0.0
        self.best_s = self.s
        self.best_d = np.linalg.norm(hit_xy - self.goal)

        # Choose direction
        s_plus = (self.s + BOUND_STEP) % L
        s_minus = (self.s - BOUND_STEP) % L
        q_plus = np.array(b.interpolate(s_plus).coords[0])
        q_minus = np.array(b.interpolate(s_minus).coords[0])
        f_plus = np.linalg.norm(q_plus - self.goal)
        f_minus = np.linalg.norm(q_minus - self.goal)
        self.dir = +1 if f_plus <= f_minus else -1

    def step(self):
        if self.state == "to_goal":
            # Move straight toward goal
            v = self.goal - self.p
            d = np.linalg.norm(v)
            if d <= EPS:
                self.p = self.goal.copy()
                self.path.append(self.p.copy())
                return False
                
            nxt = self.p + (v / d) * min(STEP_SIZE, d)

            hit = self._first_boundary_hit(self.p, nxt)
            if hit is not None:
                i, hit_xy = hit
                self.p = hit_xy
                self.path.append(self.p.copy())
                self.hit_events.append((len(self.path)-1, self.p.copy()))
                
                # Choose strategy based on obstacle geometry
                strategy, tangent_info = self._choose_strategy(i, self.boundaries[i].project(Point(hit_xy)))
                self.current_strategy = strategy
                self.strategy_changes.append((len(self.path)-1, strategy))
                
                if strategy == "tangent":
                    self.state = "tangent_follow"
                    self.i = i
                    self.s = self.boundaries[i].project(Point(hit_xy))
                    self.current_tangent = tangent_info
                    self.tangent_attempts = 0
                else:
                    self.state = "boundary_follow"
                    self._start_boundary_follow(i, hit_xy)
            else:
                self.p = nxt
                self.path.append(self.p.copy())
            return True

        elif self.state == "tangent_follow":
            # Follow tangent toward goal
            self.tangent_attempts += 1
            
            if self.current_tangent is None or self.tangent_attempts > self.max_tangent_attempts:
                # Fall back to boundary following
                self.state = "boundary_follow"
                self._start_boundary_follow(self.i, self.p)
                return True
                
            target_s, target_xy = self.current_tangent
            
            # Move toward tangent point
            v = target_xy - self.p
            d = np.linalg.norm(v)
            if d <= EPS:
                # Reached tangent point, check if we can go to goal
                if self._los_clear(self.p, self.goal):
                    self.leave_events.append((len(self.path)-1, self.p.copy()))
                    self.state = "to_goal"
                else:
                    # Find new tangent or switch to boundary
                    new_strategy, new_tangent = self._choose_strategy(self.i, self.s)
                    if new_strategy == "tangent" and new_tangent is not None:
                        self.current_tangent = new_tangent
                        self.tangent_attempts = 0
                    else:
                        self.state = "boundary_follow"
                        self._start_boundary_follow(self.i, self.p)
            else:
                nxt = self.p + (v / d) * min(STEP_SIZE, d)
                
                # Check if we hit another boundary
                hit = self._first_boundary_hit(self.p, nxt)
                if hit is not None:
                    # Tangent path blocked, switch to boundary following
                    i, hit_xy = hit
                    self.state = "boundary_follow"
                    self._start_boundary_follow(i, hit_xy)
                    self.p = hit_xy
                else:
                    self.p = nxt
                    
                self.path.append(self.p.copy())
                
                # Update arc position
                if self.i is not None:
                    self.s = self.boundaries[self.i].project(Point(self.p))
                
            return True

        elif self.state == "boundary_follow":
            i = self.i
            b = self.boundaries[i]
            L = self.L[i]
            
            # Check if we can leave to goal
            if self._los_clear(self.p, self.goal):
                self.leave_events.append((len(self.path)-1, self.p.copy()))
                self.state = "to_goal"
                return True

            # Check if we should try tangent following again
            if self.loop_dist % 2.0 < BOUND_STEP:  # Periodically check
                strategy, tangent_info = self._choose_strategy(i, self.s)
                if strategy == "tangent" and tangent_info is not None:
                    self.state = "tangent_follow"
                    self.current_tangent = tangent_info
                    self.tangent_attempts = 0
                    self.strategy_changes.append((len(self.path)-1, "tangent"))
                    return True

            # Continue boundary following
            self.s = (self.s + self.dir * BOUND_STEP) % L
            self.p = self._s_to_xy(self.s, i)
            self.path.append(self.p.copy())
            self.loop_dist += BOUND_STEP

            # Update best point
            d = np.linalg.norm(self.p - self.goal)
            if d < self.best_d - 1e-12:
                self.best_d = d
                self.best_s = self.s

            # Check for full loop
            if self.loop_dist >= L - 0.5 * BOUND_STEP:
                self.state = "to_leave"
                
            return True

        elif self.state == "to_leave":
            i = self.i
            b = self.boundaries[i]
            L = self.L[i]
            
            # Move to best leave point
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

# Visualization and main function would be similar to your original code
# but with additional plotting for strategy changes
class AdaptiveBugWithLearning(HybridTangentDistBug):
    """
    Adds reinforcement learning to strategy selection:
    - Learns which strategy works best in different situations
    - Adapts based on success/failure of previous choices
    - Uses feature-based situation assessment
    """
    
    def __init__(self, obstacles, start, goal):
        super().__init__(obstacles, start, goal)
        
        # Learning parameters
        self.strategy_weights = {
            'tangent': 1.0,
            'boundary': 1.0
        }
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.success_history = []
        self.situation_memory = {}  # Cache successful strategies for situations
        
        # Feature tracking
        self.current_features = None
        self.last_strategy = None
        self.last_situation = None

        # For plotting bookkeeping
        self._plotted_strategy_idx = 0

    # Override choose strategy to use learning module
    def _choose_strategy(self, i, s):
        return self._choose_strategy_with_learning(i, s)

    def _extract_situation_features(self, i, s):
        """Extract features describing the current situation."""
        b = self.boundaries[i]
        L = self.L[i]
        
        features = {}
        
        # 1. Local curvature
        features['curvature'] = self._calculate_obstacle_curvature(i, s)
        
        # 2. Distance to goal
        current_pos = self._s_to_xy(s, i)
        features['distance_to_goal'] = np.linalg.norm(current_pos - self.goal)
        
        # 3. Obstacle size
        features['obstacle_size'] = L
        
        # 4. Visibility of goal
        features['goal_visible'] = self._los_clear(current_pos, self.goal)
        
        # 5. Number of visible tangents
        visible_tangents = 0
        samples = max(6, min(30, int(L/2) if L/2 >= 1 else 6))
        for sample_s in np.linspace(0, L, samples):
            candidate = self._s_to_xy(sample_s, i)
            if self._los_clear(current_pos, candidate) and self._los_clear(candidate, self.goal):
                visible_tangents += 1
        features['visible_tangents'] = visible_tangents
        
        # 6. Progress made (reduction in distance to goal since hitting obstacle)
        if hasattr(self, 'hit_distance') and self.hit_distance > EPS:
            features['progress_ratio'] = (self.hit_distance - features['distance_to_goal']) / max(self.hit_distance, EPS)
        else:
            features['progress_ratio'] = 0.0
            
        return features

    def _quantize_features(self, features):
        """Convert continuous features to discrete state representation."""
        state = []
        
        # Curvature: low, medium, high
        if features['curvature'] < 0.2:
            state.append('curv_low')
        elif features['curvature'] < 0.5:
            state.append('curv_med')
        else:
            state.append('curv_high')
            
        # Distance to goal: near, medium, far
        dist = features['distance_to_goal']
        if dist < 3.0:
            state.append('dist_near')
        elif dist < 8.0:
            state.append('dist_med')
        else:
            state.append('dist_far')
            
        # Obstacle size: small, medium, large
        size = features['obstacle_size']
        if size < 10.0:
            state.append('size_small')
        elif size < 25.0:
            state.append('size_med')
        else:
            state.append('size_large')
            
        # Goal visibility
        state.append('goal_vis' if features['goal_visible'] else 'goal_hid')
        
        # Tangents availability
        if features['visible_tangents'] == 0:
            state.append('tangents_none')
        elif features['visible_tangents'] < 3:
            state.append('tangents_few')
        else:
            state.append('tangents_many')
            
        return tuple(state)

    def _choose_strategy_with_learning(self, i, s):
        """Use learned weights to choose strategy."""
        features = self._extract_situation_features(i, s)
        state = self._quantize_features(features)
        
        # Store for learning later
        self.current_features = features
        self.last_situation = state
        
        # Check memory for this situation
        if state in self.situation_memory:
            best_strategy = self.situation_memory[state]
            tangent_info = self._find_best_tangent(i, s) if best_strategy == "tangent" else None
            # record last strategy for learning
            self.last_strategy = best_strategy
            return best_strategy, tangent_info
        
        # Use softmax selection based on weights
        strategies = ['tangent', 'boundary']
        weights = [self.strategy_weights[strat] for strat in strategies]
        
        # Add some exploration
        if random.random() < 0.2:  # 20% exploration
            chosen_idx = random.randint(0, len(strategies)-1)
        else:
            # Softmax selection
            exp_weights = np.exp(weights - np.max(weights))  # numeric stability
            probs = exp_weights / np.sum(exp_weights)
            chosen_idx = np.random.choice(len(strategies), p=probs)
            
        chosen_strategy = strategies[chosen_idx]
        self.last_strategy = chosen_strategy
        
        tangent_info = self._find_best_tangent(i, s) if chosen_strategy == "tangent" else None
        
        return chosen_strategy, tangent_info

    def _evaluate_strategy_success(self, strategy):
        """Evaluate how successful the current strategy was."""
        if not hasattr(self, 'hit_distance') or self.hit_distance < EPS:
            return 0.5  # Neutral if we don't have reference
            
        current_distance = np.linalg.norm(self.p - self.goal)
        
        # Success based on progress toward goal
        progress = (self.hit_distance - current_distance) / max(self.hit_distance, EPS)
        
        # Penalize for time spent (normalize by path length)
        time_penalty = 0.005 * len(self.path) / max(1, len(self.path))
        
        # Reward for actually reaching goal
        goal_bonus = 1.0 if current_distance < EPS else 0.0
        
        # normalize into [0,1]
        success_score = progress - time_penalty + goal_bonus
        success_score = max(0.0, min(1.0, success_score))
        self.success_history.append(success_score)
        return success_score

    def _update_strategy_weights(self, strategy, success_score):
        """Update strategy weights based on success."""
        # Update the chosen strategy
        self.strategy_weights[strategy] += self.learning_rate * success_score
        
        # Slight decay for other strategies
        for other_strategy in list(self.strategy_weights.keys()):
            if other_strategy != strategy:
                self.strategy_weights[other_strategy] *= self.discount_factor
                
        # Normalize weights to prevent explosion
        total = sum(self.strategy_weights.values())
        if total <= 0:
            # reset
            for s in self.strategy_weights:
                self.strategy_weights[s] = 1.0
            total = sum(self.strategy_weights.values())
        for s in self.strategy_weights:
            self.strategy_weights[s] /= total

    def _record_successful_strategy(self, state, strategy, success_score):
        """Remember successful strategies for specific situations."""
        if success_score > 0.7:  # Only remember clearly successful strategies
            self.situation_memory[state] = strategy
        elif state in self.situation_memory and success_score < 0.3:
            # Remove from memory if strategy performed poorly
            del self.situation_memory[state]

    # Override the step method to add learning
    def step(self):
        # If we are moving to goal and haven't hit anything yet, set hit_distance baseline
        if self.state == "to_goal" and len(self.hit_events) == 0:
            self.hit_distance = np.linalg.norm(self.p - self.goal)
            
        # Call parent step
        prev_state = self.state
        result = super().step()
        
        # If we just hit an obstacle, ensure hit_distance is set to baseline for that encounter
        if prev_state == "to_goal" and len(self.hit_events) > 0 and hasattr(self, 'hit_distance'):
            # ensure it's set at first hit (already set above)
            pass
        
        # Learning updates if we had chosen a strategy recently
        if self.last_strategy and self.current_features:
            # Evaluate strategy success
            success_score = self._evaluate_strategy_success(self.last_strategy)
            
            # Update weights
            self._update_strategy_weights(self.last_strategy, success_score)
            
            # Update situation memory
            if self.last_situation:
                self._record_successful_strategy(
                    self.last_situation, 
                    self.last_strategy, 
                    success_score
                )
            
            # Reset for next decision
            self.last_strategy = None
            self.last_situation = None
            self.current_features = None
            
        return result

    def get_learning_stats(self):
        """Return learning statistics for analysis."""
        return {
            'strategy_weights': self.strategy_weights.copy(),
            'memory_size': len(self.situation_memory),
            'success_history': self.success_history.copy()
        }

def main():
    obstacles = load_polys(OBST_FILE)
    workspace = load_boundary(BDRY_FILE)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect('equal', adjustable='box')
    ax.set_title("Adaptive Hybrid Bug with Learning")

    # Draw environment
    if workspace is not None:
        bx, by = workspace.exterior.xy
        ax.plot(bx, by, color='black', linewidth=2.0)
        x0, y0, x1, y1 = workspace.bounds
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)

    for poly in obstacles:
        ax.add_patch(plt.Polygon(list(poly.exterior.coords), closed=True,
                                 fill=True, fc='lightgray', alpha=0.85,
                                 edgecolor='dimgray', lw=1.0))

    # Enhanced legend
    legend_handles = [
        Line2D([], [], marker='o', color='w', markerfacecolor='g', markeredgecolor='g', label='Start'),
        Line2D([], [], marker='o', color='w', markerfacecolor='r', markeredgecolor='r', label='Goal'),
        Line2D([], [], linestyle='--', color='b', label='Path'),
        Line2D([], [], marker='o', color='w', markerfacecolor='y', markeredgecolor='k', label='Hit'),
        Line2D([], [], marker='o', color='w', markerfacecolor='m', markeredgecolor='k', label='Leave'),
        Line2D([], [], marker='^', color='w', markerfacecolor='orange', markeredgecolor='k', label='Tangent Start'),
        Line2D([], [], marker='s', color='w', markerfacecolor='cyan', markeredgecolor='k', label='Boundary Start'),
    ]
    fig.legend(handles=legend_handles, loc='upper right', frameon=True)

    # Get start and goal
    start = get_point_on_axis(ax, "Click START", obstacles, workspace)
    goal = get_point_on_axis(ax, "Click GOAL", obstacles, workspace)
    ax.plot(start[0], start[1], 'go', markersize=10)
    ax.plot(goal[0], goal[1], 'ro', markersize=10)

    # Initialize adaptive bug
    bot = AdaptiveBugWithLearning(obstacles, start, goal)

    # Visualization setup
    (line,) = ax.plot([], [], 'b--', lw=1.6)
    circ = patches.Circle(start, 0.10, fc='royalblue', ec='black', alpha=0.9)
    ax.add_patch(circ)

    # Strategy change markers lists
    tangent_markers = []
    boundary_markers = []
    hit_markers = []
    leave_markers = []

    # Text box to show learning weights & memory size (dynamic)
    stats_box = ax.text(0.02, 0.02, "", transform=ax.transAxes, fontsize=9,
                        bbox=dict(boxstyle="round,pad=0.4", fc="w", ec="k", alpha=0.9),
                        verticalalignment='bottom')

    # Run simulation
    step = 0
    while step < MAX_STEPS and bot.step():
        step += 1
        
        # Update visualization
        if step % ANIM_STRIDE == 0:
            P = np.array(bot.path)
            line.set_data(P[:, 0], P[:, 1])
            circ.center = (P[-1, 0], P[-1, 1])

            # Plot new hit markers
            for idx, pos in bot.hit_events[len(hit_markers):]:
                if idx < len(P):
                    ph = ax.plot(P[idx,0], P[idx,1], 'yo', markersize=6, alpha=0.9)[0]
                    hit_markers.append(ph)
            # Plot new leave markers
            for idx, pos in bot.leave_events[len(leave_markers):]:
                if idx < len(P):
                    pl = ax.plot(pos[0], pos[1], 'mo', markersize=6, alpha=0.9)[0]
                    leave_markers.append(pl)

            # Plot newly recorded strategy changes (only the ones not yet plotted)
            for sc in bot.strategy_changes[bot._plotted_strategy_idx:]:
                idx, strategy = sc
                if idx < len(P):
                    pos = P[idx]
                    if strategy == "tangent":
                        m = ax.plot(pos[0], pos[1], '^', color='orange', markersize=8, alpha=0.9)[0]
                        tangent_markers.append(m)
                    else:
                        m = ax.plot(pos[0], pos[1], 's', color='cyan', markersize=6, alpha=0.9)[0]
                        boundary_markers.append(m)
            bot._plotted_strategy_idx = len(bot.strategy_changes)

            # Update stats box
            stats = bot.get_learning_stats()
            txt = f"Weights:\n tangent: {stats['strategy_weights']['tangent']:.3f}\n boundary: {stats['strategy_weights']['boundary']:.3f}\nMemory: {stats['memory_size']}\nSteps: {len(bot.path)}"
            stats_box.set_text(txt)

            plt.pause(PAUSE_SEC)

    # Final results
    P = np.array(bot.path)
    line.set_data(P[:, 0], P[:, 1])
    circ.center = (P[-1, 0], P[-1, 1])
    
    # Ensure all remaining markers plotted
    for idx, pos in bot.hit_events[len(hit_markers):]:
        if idx < len(P):
            ax.plot(P[idx,0], P[idx,1], 'yo', markersize=6, alpha=0.9)
    for idx, pos in bot.leave_events[len(leave_markers):]:
        if idx < len(P):
            ax.plot(pos[0], pos[1], 'mo', markersize=6, alpha=0.9)
    for sc in bot.strategy_changes[bot._plotted_strategy_idx:]:
        idx, strategy = sc
        if idx < len(P):
            pos = P[idx]
            if strategy == "tangent":
                ax.plot(pos[0], pos[1], '^', color='orange', markersize=8, alpha=0.9)
            else:
                ax.plot(pos[0], pos[1], 's', color='cyan', markersize=6, alpha=0.9)
    stats = bot.get_learning_stats()
    print(f"Learning Statistics:")
    print(f"Final weights: {stats['strategy_weights']}")
    print(f"Memory size: {stats['memory_size']}")
    print(f"Path length: {len(bot.path)} steps")
    
    fig.suptitle(f"Adaptive Bug Complete - Learned: {stats['memory_size']} situations")
    plt.show()

if __name__ == "__main__":
    main()
