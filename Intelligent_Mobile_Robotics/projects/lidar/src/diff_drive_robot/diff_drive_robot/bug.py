#!/usr/bin/env python3
import math
import sys
# import roslib; roslib.load_manifest('bugs')
import rclpy
from rclpy.node import Node
import tf_transformations as transform
from tf_transformations import euler_from_quaternion  # ROS2 version

from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry

from location import Location
from dist import Dist
import time

current_location = Location()
current_dists = Dist()

delta = .1
WALL_PADDING = .5

STRAIGHT = 0
LEFT = 1
RIGHT = 2
MSG_STOP = 3


class Bug(Node):
    def __init__(self, left=True, tx=5.0, ty=0.0):
        # self.pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)
        # self.tx = tx
        # self.ty = ty
        super().__init__('bug_node')
        # self.create_timer(0.1, self.wesa)
        self.isleft=left
        # Publisher for velocity commands
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Subscribers
        self.create_subscription(Odometry, '/odom', self.location_callback, 10)
        self.create_subscription(LaserScan, '/scan', self.sensor_callback, 10)

        # Target point
        self.tx = tx
        self.ty = ty
        self.x=0
        self.y=0
        self.yaw=0

        

        # Store last odometry + scan data
        self.current_pose = None
        self.latest_scan = None
    
    def location_callback(self, data: Odometry):
        p = data.pose.pose.position
        q = (
            data.pose.pose.orientation.x,
            data.pose.pose.orientation.y,
            data.pose.pose.orientation.z,
            data.pose.pose.orientation.w
        )
        # Convert quaternion to yaw
        
        (roll,pitch,self.yaw) = euler_from_quaternion(q)  # in [-pi, pi]
        self.x=p.x
        self.y=p.y
        current_location.update_location(p.x, p.y, self.yaw)
        # self.get_logger().info(f"going {self.x},{self.y},{self.yaw}")

        # self.get_logger().info(f"going {p.x},{p.y},{t}")


    def sensor_callback(self, data: LaserScan):
        current_dists.update(data)
        # ranges = data.ranges
        # n = len(ranges)
        # front = min(ranges[n//2 - 10 : n//2 + 10])   # middle of array = 180° = front
        # right  = min(ranges[n//4 - 10 : n//4 + 10])   # 90°
        # left = min(ranges[3*n//4 - 10 : 3*n//4 + 10]) # 270°
        # back  = min(ranges[0:10] + ranges[-10:])     # 0° (start/end of array)

        # self.get_logger().info(f"Front: {front:.2f}, Left: {left:.2f}, Right: {right:.2f}, Back: {back:.2f}")

    def wesa(self):
        self.get_logger().info(f"going {self.x},{self.y},{self.yaw}")


    def go(self, direction):
        cmd = Twist()
        if direction == STRAIGHT:
            cmd.linear.x = 1.0
        elif direction == LEFT:
            cmd.angular.z = 0.8
        elif direction == RIGHT:
            cmd.angular.z = -0.8
        elif direction == MSG_STOP:
            pass
        self.pub.publish(cmd)

    def go_until_obstacle(self):
        # print "Going until destination or obstacle"
        self.get_logger().info("Going until destination or obstacle")
        # self.get_logger().info(f"going {self.x},{self.y},{self.yaw}")
        # self.get_logger().info(f"going {current_location.distance(5.0, 8.0)}")
        # self.get_logger().info(f"going {current_location.current_location()}")

        if current_location.distance(5.0, 0.0) > delta:
            (frontdist, l,r) = current_dists.get()
            self.get_logger().info(f"going {current_location.current_location()}")
            self.get_logger().info(f"going {current_location.facing_point(5.0,0.0)}")

            # self.get_logger().info("in if")

            # rclpy.spin_once(self, timeout_sec=0.01)
            if frontdist <= WALL_PADDING:
                self.get_logger().info("returning True")
                return True

            if current_location.facing_point(5.0,0.0):
                self.go(STRAIGHT)
                self.get_logger().info("going straight")

            elif current_location.faster_left(self.tx, self.ty) and bool(self.isleft):

                self.go(LEFT)
                self.get_logger().info(f"going left{current_location.faster_left(self.tx, self.ty)}")
                
                

            # else:
            #     self.go(RIGHT)
            #     self.get_logger().info("going right")

            time.sleep(0.1)
        self.get_logger().info("returning False")
        return False
        # return True

    def follow_wall(self):
        self.get_logger().info("Following wall")
        while current_dists.get()[0] <= WALL_PADDING:
            self.go(RIGHT)
            time.sleep(0.1)
        while not self.should_leave_wall():
            (front, left,right) = current_dists.get()
            if front <= WALL_PADDING:
                self.go(RIGHT)
            elif WALL_PADDING - .1 <= left <= WALL_PADDING + .1:
                self.go(STRAIGHT)
            elif left > WALL_PADDING + .1:
                self.go(LEFT)
            else:
                self.go(RIGHT)
            time.sleep(0.1)
    def should_leave_wall(self):
        # print "You dolt! You need to subclass bug to know how to leave the wall"
        self.get_logger().info("You dolt! You need to subclass bug to know how to leave the wall")

        sys.exit(1)


class Bug0(Bug):
    def should_leave_wall(self):
        (x, y, t) = current_location.current_location()
        dir_to_go = current_location.global_to_local(current_location.necessary_heading(x, y, self.tx, self.ty))
        at = current_dists.at(dir_to_go)
        if at > 10:
            # print "Leaving wall"
            self.get_logger().info("Leaving wall")

            return True
        return False



def main():
    rclpy.init()
    tx, ty = 5.0, 8.0  # your target
    node = Bug0()
    # node = Bug0(tx, ty)

    try:
        while rclpy.ok():
            
            if node.go_until_obstacle():
            #     node.follow_wall()
                ...
            rclpy.spin_once(node, timeout_sec=0.1)  # <--- non-blocking
            # rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    # node.stop()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()