import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
import numpy as np
from nav_msgs.msg import Odometry
import math
from tf_transformations import euler_from_quaternion


class APF_controller(Node):
    def __init__(self):
        super().__init__('artificial_potential_field_controller')

        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        self.robot_pose_subscriber = self.create_subscription(
            Odometry,
            '/model/diff_drive/odometry',
            self.robot_pose_callback,
            100
        )
        self.lidar_subscriber = self.create_subscription(
            LaserScan,
            'lidar',
            self.lidar_callback,
            10
        )

        self.goal = None
        self.lidar_data = None

        # Declare parameters
        self.declare_parameter('max_linear_vel', 0.3)
        self.declare_parameter('goal', [0.0, 0.0])
        self.declare_parameter('kp', 0.5)
        self.declare_parameter('eta', 1.0)
        self.declare_parameter('repulsion_radius', 1.5)
        self.declare_parameter('emergency_stop_dist', 0.25)
        self.declare_parameter('goal_tolerance', 0.15)
        self.declare_parameter('max_angular_vel', 1.0)
        self.declare_parameter('angular_gain', 1.5)
        self.declare_parameter('local_minima_timeout', 5.0)

        self.kp = self.get_parameter('kp').value
        self.eta = self.get_parameter('eta').value
        self.repulsion_radius = self.get_parameter('repulsion_radius').value
        self.max_linear_vel = self.get_parameter('max_linear_vel').value
        self.max_angular_vel = self.get_parameter('max_angular_vel').value
        self.goal = np.array(self.get_parameter('goal').value)
        self.emergency_stop_dist = self.get_parameter('emergency_stop_dist').value
        self.goal_tolerance = self.get_parameter('goal_tolerance').value
        self.angular_gain = self.get_parameter('angular_gain').value
        self.local_minima_timeout = self.get_parameter('local_minima_timeout').value

        self.get_logger().info(f'Goal: {self.goal}')
        self.add_on_set_parameters_callback(self.parameter_callback)

        self.robot_pose_ready = False
        self.robot_orientation = 0.0
        self.robot_position = np.array([0.0, 0.0])

        # Velocity smoothing — limits acceleration between steps
        self.prev_linear_vel = 0.0
        self.prev_angular_vel = 0.0
        self.linear_accel_limit = 0.15    # m/s per step (at 20 Hz = 3 m/s^2, reaches 0.6 in ~0.2s)
        self.angular_accel_limit = 0.6    # rad/s per step

        # Local minima detection state
        self.last_significant_move_time = None
        self.last_check_position = None
        self.local_minima_escape_active = False
        self.escape_start_time = None
        self.escape_duration = 2.5        # seconds to spin out of minima

        self.goal_reached = False

        # 20 Hz is more than sufficient and reduces log spam / jitter
        self.ctrl_loop_timer = self.create_timer(0.05, self.control_loop)

    # ------------------------------------------------------------------ #
    #  Callbacks                                                           #
    # ------------------------------------------------------------------ #

    def robot_pose_callback(self, msg):
        self.robot_position = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y
        ])
        _, _, self.robot_orientation = euler_from_quaternion([
            msg.pose.pose.orientation.x,
            msg.pose.pose.orientation.y,
            msg.pose.pose.orientation.z,
            msg.pose.pose.orientation.w
        ])
        self.robot_pose_ready = True

    def lidar_callback(self, msg):
        self.lidar_data = msg

    # ------------------------------------------------------------------ #
    #  Potential field forces                                              #
    # ------------------------------------------------------------------ #

    def attractive_potential(self):
        """Pull toward goal (world frame)."""
        if self.goal is None:
            return np.array([0.0, 0.0])
        return self.kp * (self.goal - self.robot_position)

    def repulsive_potential(self):
        """
        Push away from obstacles.

        Bug fixed: lidar ranges/angles are in the robot-LOCAL frame.
        The obstacle angle must be rotated by robot_orientation before
        computing the world-frame repulsion direction.
        """
        if self.lidar_data is None:
            return np.array([0.0, 0.0])

        force = np.array([0.0, 0.0])
        angle_min = self.lidar_data.angle_min
        angle_increment = self.lidar_data.angle_increment

        for i, distance in enumerate(self.lidar_data.ranges):
            if not math.isfinite(distance) or distance <= 0.0:
                continue
            if distance < self.repulsion_radius:
                # Obstacle angle in robot-local frame
                angle_local = angle_min + i * angle_increment
                # Transform to world frame
                angle_world = angle_local + self.robot_orientation
                # Unit vector FROM obstacle TOWARD robot (world frame)
                dir_x = -math.cos(angle_world)
                dir_y = -math.sin(angle_world)
                # Classic APF repulsive magnitude
                magnitude = (
                    self.eta
                    * (1.0 / distance - 1.0 / self.repulsion_radius)
                    * (1.0 / (distance ** 2))
                )
                force[0] += magnitude * dir_x
                force[1] += magnitude * dir_y

        return force

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def get_min_obstacle_distance(self):
        if self.lidar_data is None:
            return float('inf')
        finite_ranges = [
            r for r in self.lidar_data.ranges
            if math.isfinite(r) and r > 0.0
        ]
        return min(finite_ranges) if finite_ranges else float('inf')

    def check_local_minima(self):
        """Return True if the robot appears stuck (hasn't moved meaningfully)."""
        now = self.get_clock().now().nanoseconds * 1e-9

        if self.last_check_position is None:
            self.last_check_position = self.robot_position.copy()
            self.last_significant_move_time = now
            return False

        if np.linalg.norm(self.robot_position - self.last_check_position) > 0.05:
            self.last_check_position = self.robot_position.copy()
            self.last_significant_move_time = now
            return False

        if (self.last_significant_move_time is not None
                and (now - self.last_significant_move_time) > self.local_minima_timeout):
            # Reset so the timer starts fresh after detection
            self.last_significant_move_time = now
            self.last_check_position = self.robot_position.copy()
            return True

        return False

    def _publish_stop(self):
        stop = Twist()
        self.publisher_.publish(stop)
        self.prev_linear_vel = 0.0
        self.prev_angular_vel = 0.0

    # ------------------------------------------------------------------ #
    #  Control loop                                                        #
    # ------------------------------------------------------------------ #

    def control_loop(self):
        if self.goal is None or not self.robot_pose_ready:
            return

        if self.goal_reached:
            return

        target_dist = float(np.linalg.norm(self.goal - self.robot_position))

        # ---- Goal reached -------------------------------------------- #
        if target_dist < self.goal_tolerance:
            self.goal_reached = True
            self.get_logger().info('Goal reached!')
            self._publish_stop()
            return

        min_dist = self.get_min_obstacle_distance()

        # ---- Emergency stop ------------------------------------------ #
        if min_dist < self.emergency_stop_dist:
            self.get_logger().warn(
                f'Emergency stop! Obstacle at {min_dist:.2f} m'
            )
            cmd = Twist()
            cmd.linear.x = -0.05   # slow reverse to back away
            self.publisher_.publish(cmd)
            self.prev_linear_vel = cmd.linear.x
            self.prev_angular_vel = 0.0
            return

        # ---- Local minima detection & escape ------------------------- #
        if self.check_local_minima():
            self.get_logger().warn('Local minima detected! Escaping...')
            self.local_minima_escape_active = True
            self.escape_start_time = self.get_clock().now().nanoseconds * 1e-9

        if self.local_minima_escape_active:
            now = self.get_clock().now().nanoseconds * 1e-9
            if (now - self.escape_start_time) < self.escape_duration:
                cmd = Twist()
                cmd.angular.z = 0.6
                cmd.linear.x = 0.05
                self.publisher_.publish(cmd)
                return
            self.local_minima_escape_active = False

        # ---- APF force computation ----------------------------------- #
        attractive = self.attractive_potential()
        repulsive = self.repulsive_potential()
        resultant = attractive + repulsive

        force_magnitude = float(np.linalg.norm(resultant))
        if force_magnitude < 1e-6:
            self._publish_stop()
            return

        # ---- Desired heading & angular error ------------------------- #
        desired_angle = math.atan2(resultant[1], resultant[0])
        angular_error = math.atan2(
            math.sin(desired_angle - self.robot_orientation),
            math.cos(desired_angle - self.robot_orientation)
        )

        # ---- Linear velocity ----------------------------------------- #
        # cos(error): gentle reduction — at 17° still 95%, at 60° still 50%
        # clamp to 0 so robot never drives backwards due to this factor alone
        angle_factor = max(0.0, math.cos(angular_error))
        # Reduce speed near obstacles
        obs_factor = min(1.0, min_dist / self.repulsion_radius) if min_dist < self.repulsion_radius else 1.0
        desired_linear = (
            min(force_magnitude * self.max_linear_vel, self.max_linear_vel)
            * angle_factor
            * obs_factor
        )

        # ---- Angular velocity ---------------------------------------- #
        desired_angular = float(
            max(-self.max_angular_vel, min(self.max_angular_vel, self.angular_gain * angular_error))
        )

        # ---- Smooth with acceleration limits ------------------------- #
        linear_vel = self.prev_linear_vel + float(np.clip(
            desired_linear - self.prev_linear_vel,
            -self.linear_accel_limit,
            self.linear_accel_limit
        ))
        angular_vel = self.prev_angular_vel + float(np.clip(
            desired_angular - self.prev_angular_vel,
            -self.angular_accel_limit,
            self.angular_accel_limit
        ))

        self.prev_linear_vel = linear_vel
        self.prev_angular_vel = angular_vel

        # ---- Publish ------------------------------------------------- #
        cmd = Twist()
        cmd.linear.x = linear_vel
        cmd.angular.z = angular_vel
        self.publisher_.publish(cmd)

        self.get_logger().info(
            f'goal_dist={target_dist:.2f} obs={min_dist:.2f} '
            f'lin={linear_vel:.3f} ang={angular_vel:.3f} '
            f'ang_err={math.degrees(angular_error):.1f}°'
        )

    # ------------------------------------------------------------------ #
    #  Parameter callback                                                  #
    # ------------------------------------------------------------------ #

    def parameter_callback(self, params):
        from rcl_interfaces.msg import SetParametersResult
        for param in params:
            if param.name == 'kp':
                self.kp = param.value
            elif param.name == 'eta':
                self.eta = param.value
            elif param.name == 'repulsion_radius':
                self.repulsion_radius = param.value
            elif param.name == 'max_linear_vel':
                self.max_linear_vel = param.value
            elif param.name == 'goal':
                self.goal = np.array(param.value)
                self.goal_reached = False
            elif param.name == 'emergency_stop_dist':
                self.emergency_stop_dist = param.value
            elif param.name == 'goal_tolerance':
                self.goal_tolerance = param.value
            elif param.name == 'angular_gain':
                self.angular_gain = param.value
            elif param.name == 'max_angular_vel':
                self.max_angular_vel = param.value
            elif param.name == 'local_minima_timeout':
                self.local_minima_timeout = param.value
        return SetParametersResult(successful=True)


def main(args=None):
    rclpy.init(args=args)
    controller = APF_controller()
    rclpy.spin(controller)
    controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
