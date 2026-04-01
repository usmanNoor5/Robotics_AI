#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math


class UTurnBox(Node):
    def __init__(self):
        super().__init__('u_turn_box', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)
        ])

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # Speeds
        self.linear_speed = 0.5
        self.angular_speed = 0.5

        # Durations (seconds)
        self.forward_time = 4.0      # along the box side
        self.side_time = 3.0         # across the box width
        self.turn_time = (math.pi / 2) / self.angular_speed  # 90-degree turn

        # U-turn sequence: (linear_x, angular_z, duration, label)
        self.steps = [
            (self.linear_speed, 0.0, self.forward_time, 'Moving forward (side 1)'),
            (0.0, self.angular_speed, self.turn_time,   'Turning left 90 degrees'),
            (self.linear_speed, 0.0, self.side_time,    'Moving forward (across box)'),
            (0.0, self.angular_speed, self.turn_time,   'Turning left 90 degrees'),
            (self.linear_speed, 0.0, self.forward_time, 'Moving forward (side 2)'),
        ]
        self.current_step = 0
        self.step_start_time = None

        # Publish cmd_vel at 20 Hz
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.get_logger().info('Waiting for simulation time...')

    def timer_callback(self):
        now = self.get_clock().now()

        # Wait until sim time is active (non-zero)
        if now.nanoseconds == 0:
            return

        # All steps done -> stop and shutdown
        if self.current_step >= len(self.steps):
            self.publish_twist(0.0, 0.0)
            self.get_logger().info('U-turn complete!')
            self.timer.cancel()
            raise SystemExit

        lin, ang, duration, label = self.steps[self.current_step]

        # Start new step
        if self.step_start_time is None:
            self.step_start_time = now
            self.get_logger().info(f'Step {self.current_step + 1}/{len(self.steps)}: {label}')

        elapsed = (now - self.step_start_time).nanoseconds / 1e9

        if elapsed < duration:
            self.publish_twist(lin, ang)
        else:
            # Brief stop between steps for stability
            self.publish_twist(0.0, 0.0)
            self.current_step += 1
            self.step_start_time = None

    def publish_twist(self, linear_x, angular_z):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = UTurnBox()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
