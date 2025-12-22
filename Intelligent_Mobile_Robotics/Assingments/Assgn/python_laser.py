import os
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from matplotlib.patches import Circle
from matplotlib.widgets import Button
import time


def load_obstacles_from_file(filename):
    """Read polygon obstacles from file, skipping blank lines."""
    obstacles = []
    with open(filename, "r") as f:
        lines = [line.strip() for line in f if line.strip()]  # remove blanks

    i = 0
    while i < len(lines):
        n = int(lines[i])  # number of vertices
        i += 1
        coords = []
        for _ in range(n):
            x, y = map(float, lines[i].split())
            coords.append((x, y))
            i += 1
        obstacles.append(Polygon(coords))
    return obstacles


class TangentBugLaserSimulator:
    def __init__(self, obstacles, robot_radius=0.5, num_rays=36, max_range=2.0, safe_distance=0.5):
        self.obstacles = obstacles
        self.robot_radius = robot_radius
        self.num_rays = num_rays
        self.max_range = max_range
        self.safe_distance = safe_distance

        # Start, goal, and preview
        self.start = None
        self.goal = None
        self.current_pos = None
        self.preview_circle = None
        self.goal_line = None
        self.robot_circle = None
        self.sensor_artists = []
        self.is_moving = False
        self.path_history = []

        # Tangent-Bug states
        self.state = "to_goal"  # 'to_goal', 'boundary_follow'
        self.follow_direction = None  # Will be determined dynamically
        self.hit_point = None
        self.leave_point = None
        self.min_distance_to_goal = float('inf')
        self.m_point = None
        self.m_point_history = []

        # Setup plot
        self.fig, self.ax = plt.subplots()
        plt.subplots_adjust(bottom=0.2)
        self.ax.set_aspect("equal")
        self.ax.grid(True, linestyle="--", alpha=0.5)

        # Auto-fit plot limits from obstacles
        all_x = [x for poly in obstacles for x, _ in poly.exterior.coords]
        all_y = [y for poly in obstacles for _, y in poly.exterior.coords]
        self.ax.set_xlim(min(all_x) - 2, max(all_x) + 2)
        self.ax.set_ylim(min(all_y) - 2, max(all_y) + 2)

        # Draw obstacles
        for obs in obstacles:
            xs, ys = obs.exterior.xy
            self.ax.fill(xs, ys, alpha=0.5, fc="gray", ec="black")

        # Buttons
        ax_start = plt.axes([0.2, 0.05, 0.2, 0.075])
        ax_reset = plt.axes([0.6, 0.05, 0.2, 0.075])
        self.start_button = Button(ax_start, "Start Moving")
        self.reset_button = Button(ax_reset, "Reset")
        self.start_button.on_clicked(self.start_moving)
        self.reset_button.on_clicked(self.reset)

        # Connect events
        self.cid_click = self.fig.canvas.mpl_connect("button_press_event", self.onclick)
        self.cid_move = self.fig.canvas.mpl_connect("motion_notify_event", self.onmove)

        plt.title("Tangent-Bug Laser Simulator - Click to set Start and Goal")
        plt.show()

    def simulate_sensor(self, robot):
        """Simulate laser sensor and return intersection points with obstacles"""
        angles = np.linspace(0, 2*np.pi, self.num_rays, endpoint=False)
        sensor_points = []
        sensor_distances = []

        for angle in angles:
            ray_end = robot + self.max_range * np.array([np.cos(angle), np.sin(angle)])
            ray = LineString([robot, ray_end])

            closest_pt = None
            closest_dist = self.max_range

            for obs in self.obstacles:
                inter = ray.intersection(obs.boundary)
                if not inter.is_empty:
                    if inter.geom_type == "Point":
                        d = Point(robot).distance(inter)
                        if d < closest_dist:
                            closest_dist = d
                            closest_pt = inter
                    elif inter.geom_type == "MultiPoint":
                        for pt in inter.geoms:
                            d = Point(robot).distance(pt)
                            if d < closest_dist:
                                closest_dist = d
                                closest_pt = pt

            if closest_pt is not None:
                sensor_points.append(closest_pt)
                sensor_distances.append(closest_dist)
            else:
                sensor_points.append(Point(ray_end))
                sensor_distances.append(self.max_range)

        return sensor_points, angles, sensor_distances

    def update_sensor_display(self, robot_pos):
        """Update the sensor rays display"""
        # Clear previous sensor display
        for artist in self.sensor_artists:
            artist.remove()
        self.sensor_artists = []
        
        # Get new sensor readings
        sensor_points, angles, sensor_distances = self.simulate_sensor(robot_pos)
        
        # Draw new sensor rays
        for i, pt in enumerate(sensor_points):
            if sensor_distances[i] < self.max_range:
                # Hit obstacle - red ray
                ray_line, = self.ax.plot([robot_pos[0], pt.x], [robot_pos[1], pt.y], 
                                       "r-", linewidth=1.0, alpha=0.7)
                hit_pt, = self.ax.plot(pt.x, pt.y, "ro", markersize=2)
            else:
                # No obstacle - green ray
                ray_line, = self.ax.plot([robot_pos[0], pt.x], [robot_pos[1], pt.y], 
                                       "g-", linewidth=0.5, alpha=0.3)
                hit_pt, = self.ax.plot(pt.x, pt.y, "go", markersize=1)
            
            self.sensor_artists.extend([ray_line, hit_pt])
            
        return sensor_points, angles, sensor_distances

    def onmove(self, event):
        if self.start is None and event.inaxes == self.ax:
            if self.preview_circle:
                self.preview_circle.remove()
            self.preview_circle = Circle((event.xdata, event.ydata),
                                         radius=self.robot_radius,
                                         edgecolor="blue", facecolor="none", linestyle="--")
            self.ax.add_patch(self.preview_circle)
            self.fig.canvas.draw_idle()

    def onclick(self, event):
        if event.inaxes != self.ax or self.is_moving:
            return

        if self.start is None:
            self.start = np.array([event.xdata, event.ydata])
            self.current_pos = self.start.copy()
            self.robot_circle = Circle(self.start, radius=self.robot_radius, 
                                     edgecolor="blue", facecolor="lightblue", 
                                     alpha=0.6, label="Start")
            self.ax.add_patch(self.robot_circle)
            self.ax.legend()
            if self.preview_circle:
                self.preview_circle.remove()
            self.fig.canvas.draw_idle()
            print(f"Start set at {self.start}")

        elif self.goal is None:
            self.goal = np.array([event.xdata, event.ydata])
            self.ax.plot(self.goal[0], self.goal[1], "ro", markersize=8, label="Goal")
            self.ax.legend()

            self.goal_line, = self.ax.plot([self.start[0], self.goal[0]],
                                           [self.start[1], self.goal[1]],
                                           "m-", linewidth=1.5, label="Start→Goal")

            # Show initial sensor readings
            self.update_sensor_display(self.start)
            self.fig.canvas.draw_idle()
            print(f"Goal set at {self.goal}")

    def start_moving(self, event):
        if self.start is None or self.goal is None or self.is_moving:
            return
            
        self.is_moving = True
        self.start_button.label.set_text("Moving...")
        plt.pause(0.1)
        
        # Run tangent-bug algorithm
        self.tangent_bug_algorithm()
        
        self.is_moving = False
        self.start_button.label.set_text("Start Moving")

    def find_m_point(self, sensor_points):
        """Find the point on obstacle boundary closest to goal (M-point)"""
        if not sensor_points:
            return None
            
        min_distance = float('inf')
        m_point = None
        
        for pt in sensor_points:
            if hasattr(pt, 'x') and hasattr(pt, 'y'):
                distance = np.linalg.norm([pt.x - self.goal[0], pt.y - self.goal[1]])
                if distance < min_distance:
                    min_distance = distance
                    m_point = np.array([pt.x, pt.y])
        
        return m_point

    def choose_optimal_direction(self, pos, sensor_points, closest_angle):
        """Choose optimal direction (left or right) to reach M-point"""
        if self.m_point is None:
            return 1  # Default to left if no M-point
            
        # Calculate angles for left and right directions
        left_angle = closest_angle + np.pi/2
        right_angle = closest_angle - np.pi/2
        
        # Calculate vectors
        left_vector = np.array([np.cos(left_angle), np.sin(left_angle)])
        right_vector = np.array([np.cos(right_angle), np.sin(right_angle)])
        
        # Vector to M-point
        to_m = self.m_point - pos
        if np.linalg.norm(to_m) > 0:
            to_m = to_m / np.linalg.norm(to_m)
        
        # Calculate which direction aligns better with M-point
        left_alignment = np.dot(left_vector, to_m)
        right_alignment = np.dot(right_vector, to_m)
        
        # Choose direction that better aligns with M-point
        if left_alignment > right_alignment:
            return 1  # Left
        else:
            return -1  # Right

    def tangent_bug_algorithm(self):
        """Proper Tangent-Bug algorithm with dynamic direction selection"""
        pos = self.current_pos.copy()
        step_size = 0.08
        max_iterations = 5000
        iteration = 0
        
        # Store path history for visualization
        self.path_history = [pos.copy()]
        self.m_point_history = []
        
        while iteration < max_iterations:
            iteration += 1
            
            # Check if we reached the goal
            distance_to_goal = np.linalg.norm(pos - self.goal)
            if distance_to_goal < self.robot_radius + 0.1:
                print("Goal reached!")
                break
            
            # Get sensor readings
            sensor_points, angles, sensor_distances = self.update_sensor_display(pos)
            
            if self.state == "to_goal":
                # Move directly toward goal
                goal_dir = self.goal - pos
                if np.linalg.norm(goal_dir) > 0:
                    goal_dir = goal_dir / np.linalg.norm(goal_dir)
                
                # Check if path to goal is blocked
                min_obstacle_distance = min(sensor_distances)
                
                if min_obstacle_distance < self.robot_radius + self.safe_distance:
                    # Switch to boundary following
                    self.state = "boundary_follow"
                    self.hit_point = pos.copy()
                    self.min_distance_to_goal = distance_to_goal
                    
                    # Find initial M-point and choose optimal direction
                    self.m_point = self.find_m_point(sensor_points)
                    if self.m_point is not None:
                        self.m_point_history.append(self.m_point.copy())
                    
                    # Find closest obstacle angle to determine direction
                    min_dist_idx = np.argmin(sensor_distances)
                    closest_angle = angles[min_dist_idx]
                    
                    # Choose optimal direction dynamically
                    self.follow_direction = self.choose_optimal_direction(pos, sensor_points, closest_angle)
                    
                    direction_str = "LEFT" if self.follow_direction == 1 else "RIGHT"
                    print(f"Switching to boundary following. Direction: {direction_str}")
                    print(f"M-point at {self.m_point}")
                else:
                    # Continue toward goal
                    new_pos = pos + step_size * goal_dir
                    if self.is_position_safe(new_pos):
                        pos = new_pos
                    else:
                        self.state = "boundary_follow"
                        self.hit_point = pos.copy()
                        self.min_distance_to_goal = distance_to_goal
                        self.m_point = self.find_m_point(sensor_points)
                        min_dist_idx = np.argmin(sensor_distances)
                        closest_angle = angles[min_dist_idx]
                        self.follow_direction = self.choose_optimal_direction(pos, sensor_points, closest_angle)
                        
            elif self.state == "boundary_follow":
                # Update M-point continuously
                new_m_point = self.find_m_point(sensor_points)
                if new_m_point is not None:
                    new_m_distance = np.linalg.norm(new_m_point - self.goal)
                    if self.m_point is None or new_m_distance < np.linalg.norm(self.m_point - self.goal):
                        self.m_point = new_m_point
                        self.m_point_history.append(self.m_point.copy())
                        print(f"Updated M-point to {self.m_point}, distance to goal: {new_m_distance:.2f}")
                
                # Update minimum distance to goal
                current_distance = np.linalg.norm(pos - self.goal)
                if current_distance < self.min_distance_to_goal:
                    self.min_distance_to_goal = current_distance
                
                # Get wall following direction
                follow_vector = self.calculate_wall_follow_direction(pos, sensor_points, angles, sensor_distances)
                
                if follow_vector is not None:
                    new_pos = pos + step_size * follow_vector
                    
                    if self.is_position_safe(new_pos):
                        pos = new_pos
                    else:
                        # If stuck, try perpendicular direction
                        perpendicular_angle = np.arctan2(follow_vector[1], follow_vector[0]) + np.pi/2
                        perpendicular_vector = np.array([np.cos(perpendicular_angle), np.sin(perpendicular_angle)])
                        new_pos = pos + (step_size * 0.5) * perpendicular_vector
                        if self.is_position_safe(new_pos):
                            pos = new_pos
                
                # Check leave condition: reached M-point and direct path is clear
                if (self.m_point is not None and 
                    np.linalg.norm(pos - self.m_point) < step_size * 3 and
                    self.is_direct_path_clear(pos)):
                    
                    self.state = "to_goal"
                    print("Leaving boundary following - reached M-point with clear path to goal")
            
            # Update robot position
            self.current_pos = pos.copy()
            self.path_history.append(pos.copy())
            
            # Update visualization
            self.robot_circle.center = pos
            
            # Visualize M-point
            if self.m_point is not None:
                if hasattr(self, 'm_point_plot'):
                    self.m_point_plot.set_data([self.m_point[0]], [self.m_point[1]])
                else:
                    self.m_point_plot, = self.ax.plot([self.m_point[0]], [self.m_point[1]], 
                                                    'ys', markersize=8, markeredgecolor='black', 
                                                    label='M-point')
                    self.ax.legend()
            
            # Draw path
            if len(self.path_history) > 1:
                path_x = [p[0] for p in self.path_history]
                path_y = [p[1] for p in self.path_history]
                if hasattr(self, 'path_line'):
                    self.path_line.set_data(path_x, path_y)
                else:
                    self.path_line, = self.ax.plot(path_x, path_y, 'b-', linewidth=2, alpha=0.7, label='Path')
                    self.ax.legend()
            
            self.fig.canvas.draw_idle()
            plt.pause(0.01)
        
        if iteration >= max_iterations:
            print("Maximum iterations reached")

    def calculate_wall_follow_direction(self, pos, sensor_points, angles, sensor_distances):
        """Calculate wall following direction based on chosen direction"""
        # Find the closest obstacle point
        min_distance = float('inf')
        closest_angle = 0
        
        for i, dist in enumerate(sensor_distances):
            if dist < min_distance:
                min_distance = dist
                closest_angle = angles[i]
        
        # Calculate follow direction based on chosen side
        if self.follow_direction == 1:  # Left
            follow_angle = closest_angle + np.pi/2
        else:  # Right
            follow_angle = closest_angle - np.pi/2
        
        follow_vector = np.array([np.cos(follow_angle), np.sin(follow_angle)])
        
        # Add component toward M-point if available
        if self.m_point is not None:
            to_m = self.m_point - pos
            if np.linalg.norm(to_m) > 0:
                to_m = to_m / np.linalg.norm(to_m)
                # Blend: 80% wall following, 20% toward M-point
                blended = 0.8 * follow_vector + 0.2 * to_m
                if np.linalg.norm(blended) > 0:
                    follow_vector = blended / np.linalg.norm(blended)
        
        # Maintain safe distance from wall
        desired_distance = self.robot_radius + self.safe_distance + 0.1
        if min_distance < desired_distance - 0.1:
            # Too close, move away
            away_angle = closest_angle
            away_vector = np.array([np.cos(away_angle), np.sin(away_angle)])
            follow_vector = 0.7 * follow_vector + 0.3 * away_vector
        elif min_distance > desired_distance + 0.2:
            # Too far, move toward wall slightly
            toward_angle = closest_angle + np.pi
            toward_vector = np.array([np.cos(toward_angle), np.sin(toward_angle)])
            follow_vector = 0.9 * follow_vector + 0.1 * toward_vector
        
        # Normalize
        if np.linalg.norm(follow_vector) > 0:
            follow_vector = follow_vector / np.linalg.norm(follow_vector)
        
        return follow_vector

    def is_direct_path_clear(self, pos):
        """Check if direct path to goal is clear of obstacles"""
        path_to_goal = LineString([pos, self.goal])
        
        for obs in self.obstacles:
            buffered_obs = obs.buffer(self.robot_radius + self.safe_distance)
            if path_to_goal.intersects(buffered_obs):
                return False
        return True

    def is_position_safe(self, pos):
        """Check if a position is safe (not inside any obstacle)"""
        robot_point = Point(pos)
        expanded_obstacles = [obs.buffer(self.robot_radius + self.safe_distance) for obs in self.obstacles]
        
        for obs in expanded_obstacles:
            if robot_point.within(obs):
                return False
        return True

    def reset(self, event):
        print("Resetting simulation...")
        self.is_moving = False
        self.start_button.label.set_text("Start Moving")
        
        # Clear all dynamic elements
        if self.robot_circle:
            self.robot_circle.remove()
            self.robot_circle = None
        if self.goal_line:
            self.goal_line.remove()
            self.goal_line = None
        for art in self.sensor_artists:
            art.remove()
        self.sensor_artists = []
        if hasattr(self, 'path_line'):
            self.path_line.remove()
            del self.path_line
        if hasattr(self, 'm_point_plot'):
            self.m_point_plot.remove()
            del self.m_point_plot
        
        # Reset state
        self.state = "to_goal"
        self.follow_direction = None
        self.hit_point = None
        self.leave_point = None
        self.min_distance_to_goal = float('inf')
        self.m_point = None
        self.m_point_history = []
        
        self.start = None
        self.goal = None
        self.current_pos = None
        self.path_history = []
        
        self.fig.canvas.draw_idle()
        plt.title("Tangent-Bug Laser Simulator - Click to set Start and Goal")


# ---- Example run ----
if __name__ == "__main__":
    # Build path to obstacles file in the same folder
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(base_dir, "obstacles4.txt")

    obstacles = load_obstacles_from_file(filename)
    TangentBugLaserSimulator(obstacles)