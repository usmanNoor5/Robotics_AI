#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math


def yaw_from_quaternion(q):
    """Convert quaternion to yaw"""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class SquareOdom(Node):
    def __init__(self):
        super().__init__('square_odom')

        self.cmd_pub = self.create_publisher(
            Twist,
            '/bumperbot_controller/cmd_vel_unstamped',
            10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            '/bumperbot_controller/odom',
            self.odom_callback,
            10
        )

        self.timer = self.create_timer(0.05, self.control_loop)

        # Robot state
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        # State machine
        self.state = 'FORWARD'
        self.step = 0

        self.start_x = None
        self.start_y = None
        self.start_yaw = None

        self.get_logger().info("Square odom node started")

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.yaw = yaw_from_quaternion(msg.pose.pose.orientation)

    def distance_traveled(self):
        return math.sqrt(
            (self.x - self.start_x) ** 2 +
            (self.y - self.start_y) ** 2
        )

    def angle_turned(self):
        diff = self.yaw - self.start_yaw
        return math.atan2(math.sin(diff), math.cos(diff))

    def stop_robot(self):
        self.cmd_pub.publish(Twist())

    def control_loop(self):
        cmd = Twist()

        if self.step >= 4:
            self.stop_robot()
            self.get_logger().info("✅ Square completed")
            rclpy.shutdown()
            return

        # ---------- MOVE FORWARD 1 METER ----------
        if self.state == 'FORWARD':
            if self.start_x is None:
                self.start_x = self.x
                self.start_y = self.y
                self.get_logger().info(f"➡️ Forward {self.step+1}")

            if self.distance_traveled() < 1.0:
                cmd.linear.x = 0.2
            else:
                self.stop_robot()
                self.state = 'TURN'
                self.start_yaw = self.yaw
                self.start_x = None
                self.start_y = None

        # ---------- TURN 90 DEG ----------
        elif self.state == 'TURN':
            if abs(self.angle_turned()) < math.pi / 2:
                cmd.angular.z = 0.5
            else:
                self.stop_robot()
                self.state = 'FORWARD'
                self.start_yaw = None
                self.step += 1

        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = SquareOdom()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
