import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Point, Polygon, LineString
import numpy as np

# ---------------- Environment ----------------
boundary_coords = [(-20, 15), (20, 15), (20, -15), (-20, -15)]
obstacle_coords = [(-8.052, -6.720), (4.576, 7.9333), (1.408, 8.3533), (-11.0, -5.040)]

EPS = 1e-3          # numeric tolerance
DEBUG = True       # set True for step-by-step logs


# ---------------- Robot (Tangent Bug) ----------------
class Robot:
    def __init__(self, position, detection_radius, goal, robot_radius, obstacle_coords):
        self.position = np.array(position, dtype=float)
        self.goal = np.array(goal, dtype=float)
        self.detection_radius = float(detection_radius)
        self.robot_radius = float(robot_radius)

        # Clearance obstacle (inflated by robot radius)
        raw_poly = Polygon(obstacle_coords).buffer(0)
        self.clearance_poly = raw_poly.buffer(self.robot_radius)

        # Boundary to trace
        self.boundary = LineString(self.clearance_poly.exterior.coords)
        self.boundary_len = self.boundary.length

        # State
        self.state = "motion_to_goal"
        self.path = [self.position.copy()]

        # Tangent Bug bookkeeping
        self.following_direction = None
        self.current_s = 0
        self.hit_point = None
        self.leave_point = None

        # Visualization markers
        self.hit_points = []
        self.leave_points = []
        self.tangent_points = []

    def _segment_hits_clearance(self, p0, p1):
        seg = LineString([tuple(p0), tuple(p1)])
        return seg.intersects(self.clearance_poly)

    def _s_to_xy(self, s):
        return np.array(self.boundary.interpolate(s).coords[0])

    def _project_to_boundary(self, xy):
        s = self.boundary.project(Point(xy))
        return s, self._s_to_xy(s)

    def _get_distance_to_goal(self, point):
        return np.linalg.norm(point - self.goal)

    def _can_reach_goal_directly(self, from_point=None):
        """Check if we can reach goal directly from given point"""
        if from_point is None:
            from_point = self.position
        return not self._segment_hits_clearance(from_point, self.goal)

    def _find_tangent_points(self):
        """Find left and right tangent points from current position"""
        current_point = Point(self.position)
        
        # Sample points along boundary within detection range
        tangent_candidates = []
        for s in np.linspace(0, self.boundary_len, 200):
            boundary_point = self._s_to_xy(s)
            if np.linalg.norm(boundary_point - self.position) <= self.detection_radius:
                # Check if line from robot to boundary point is clear
                if not self._segment_hits_clearance(self.position, boundary_point):
                    tangent_candidates.append((s, boundary_point))
        
        if not tangent_candidates:
            return None, None
        
        # Find leftmost and rightmost tangent points relative to goal direction
        goal_dir = self.goal - self.position
        goal_dir = goal_dir / np.linalg.norm(goal_dir)
        
        left_tangent = None
        right_tangent = None
        min_left_angle = float('inf')
        min_right_angle = float('inf')
        
        for s, point in tangent_candidates:
            to_point = point - self.position
            to_point = to_point / np.linalg.norm(to_point)
            
            # Calculate angle relative to goal direction
            cross_product = np.cross(goal_dir, to_point)
            dot_product = np.dot(goal_dir, to_point)
            angle = np.arctan2(cross_product, dot_product)
            
            if cross_product > 0:  # Left side
                if angle < min_left_angle:
                    min_left_angle = angle
                    left_tangent = (s, point)
            else:  # Right side
                if angle < min_right_angle:
                    min_right_angle = angle
                    right_tangent = (s, point)
        
        return left_tangent, right_tangent

    def _choose_best_direction(self, left_tangent, right_tangent):
        """Choose the tangent point that gives shortest path to goal"""
        if left_tangent is None and right_tangent is None:
            # If no tangents, choose direction that minimizes distance to goal
            current_s = self.boundary.project(Point(self.position))
            
            # Test both directions
            test_s_cw = (current_s + 1.0) % self.boundary_len
            test_point_cw = self._s_to_xy(test_s_cw)
            dist_cw = self._get_distance_to_goal(test_point_cw)
            
            test_s_ccw = (current_s - 1.0) % self.boundary_len
            test_point_ccw = self._s_to_xy(test_s_ccw)
            dist_ccw = self._get_distance_to_goal(test_point_ccw)
            
            return 1 if dist_cw < dist_ccw else -1
        
        elif left_tangent is None:
            return 1  # Right tangent only
        elif right_tangent is None:
            return -1  # Left tangent only
        else:
            # Choose the tangent that gives shorter path to goal
            _, left_point = left_tangent
            _, right_point = right_tangent
            
            dist_left = self._get_distance_to_goal(left_point)
            dist_right = self._get_distance_to_goal(right_point)
            
            return -1 if dist_left < dist_right else 1

    def move(self, step_size=0.5):
        if DEBUG:
            print(f"Step {len(self.path)}: State={self.state}, Position={self.position}")

        if self.state == "motion_to_goal":
            v = self.goal - self.position
            d = np.linalg.norm(v)
            
            # Check if goal is reached
            if d <= EPS:
                self.position = self.goal.copy()
                self.path.append(self.position.copy())
                if DEBUG: print("Reached goal.")
                return False

            direction = v / d
            next_pos = self.position + direction * min(step_size, d)

            # Check if we hit an obstacle
            if self._segment_hits_clearance(self.position, next_pos):
                # Find hit point on boundary
                self.current_s, hit_xy = self._project_to_boundary(self.position)
                self.hit_point = hit_xy
                self.hit_points.append(hit_xy.copy())
                
                # Move to hit point
                self.position = hit_xy
                self.path.append(self.position.copy())
                
                # Find tangent points and choose best direction
                left_tangent, right_tangent = self._find_tangent_points()
                self.following_direction = self._choose_best_direction(left_tangent, right_tangent)
                self.following_direction = -1
                
                self.state = "boundary_following"
                
                if DEBUG: 
                    print(f"Hit obstacle at {hit_xy}. Switching to boundary following.")
                    dir_name = "left (counterclockwise)" if self.following_direction == -1 else "right (clockwise)"
                    print(f"Following direction: {dir_name}")
            else:
                self.position = next_pos
                self.path.append(self.position.copy())
                
            return True

        elif self.state == "boundary_following":
            # Move along boundary in chosen direction
            self.current_s = (self.current_s + self.following_direction * step_size) % self.boundary_len
            next_pos = self._s_to_xy(self.current_s)
            
            # Update position
            self.position = next_pos
            self.path.append(self.position.copy())
            
            # Check if we can leave boundary (direct path to goal is clear)
            if self._can_reach_goal_directly():
                self.leave_points.append(self.position.copy())
                self.state = "motion_to_goal"
                if DEBUG: 
                    print(f"Leaving boundary at {self.position}. Returning to motion_to_goal.")
            
            return True

        return False


# ---------------- Simulation / Plot ----------------
start = (-15, -10)
goal = (15, 10)

robot = Robot(
    position=start,
    detection_radius=5.0,  # Increased detection radius for better tangent finding
    goal=goal,
    robot_radius=0.5,
    obstacle_coords=obstacle_coords
)

fig, ax = plt.subplots(figsize=(12, 9))
ax.set_aspect('equal', adjustable='box')
ax.set_xlim(-25, 25)
ax.set_ylim(-20, 20)

# World boundary
ax.add_patch(plt.Polygon(boundary_coords, closed=True, fill=False, edgecolor='k', lw=2))

# Raw obstacle
ax.add_patch(plt.Polygon(obstacle_coords, closed=True, fill=True, fc='gray', alpha=0.6, edgecolor='black'))

# Clearance boundary (dashed red)
ax.plot(*robot.clearance_poly.exterior.xy, 'r--', lw=1, alpha=0.6, label="Clearance boundary")

# Start & Goal
ax.plot(start[0], start[1], 'go', markersize=10, label='Start')
ax.plot(goal[0], goal[1], 'ro', markersize=10, label='Goal')

# Robot marker
robot_patch = patches.Circle(robot.position, robot.robot_radius, fc='blue', ec='black', alpha=0.6)
ax.add_patch(robot_patch)

# Detection radius
detection_circle = patches.Circle(robot.position, robot.detection_radius, fill=False, ec='orange', linestyle='--', alpha=0.5)
ax.add_patch(detection_circle)

# Path trace
trace_x, trace_y = zip(*robot.path)
trace_line, = ax.plot(trace_x, trace_y, 'b-', linewidth=2, alpha=0.7, label='Path')

plt.legend()
plt.ion()
plt.show()

MAX_STEPS = 1000
steps = 0
while steps < MAX_STEPS and robot.move(step_size=0.5):
    robot_patch.center = robot.position
    detection_circle.center = robot.position
    
    trace_x, trace_y = zip(*robot.path)
    trace_line.set_data(trace_x, trace_y)

    # Draw debug markers
    for pt in robot.hit_points:
        ax.plot(pt[0], pt[1], 'yo', markersize=8, label="Hit" if len(robot.hit_points) == 1 else "")

    for pt in robot.leave_points:
        ax.plot(pt[0], pt[1], 'mo', markersize=8, label="Leave" if len(robot.leave_points) == 1 else "")

    plt.title(f"Tangent Bug Algorithm - Step {steps}, State: {robot.state}")
    plt.pause(0.01)
    steps += 1

plt.ioff()
plt.title(f"Tangent Bug Algorithm - Final Path ({steps} steps)")
plt.show()

print(f"Simulation completed in {steps} steps")
print(f"Path length: {len(robot.path)} points")
print(f"Final state: {robot.state}")