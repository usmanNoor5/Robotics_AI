#! /usr/bin/python3
# imports
# rclpy imports
import rclpy  # rclpy
from rclpy.node import Node  # base node
from rclpy.qos import QoSProfile  # qos profile
from rclpy.qos import (
    HistoryPolicy,
    ReliabilityPolicy,  # qos policies
    DurabilityPolicy,
    LivelinessPolicy,
)  # qos policies
from rclpy.executors import MultiThreadedExecutor  # multithreaded executor
from rclpy.callback_groups import ReentrantCallbackGroup  # reentrant callback group

# ros2 interfaces
from geometry_msgs.msg import Twist  # twist message
from nav_msgs.msg import Odometry  # odometry message
from sensor_msgs.msg import LaserScan  # laser scan message

# standard imports
import math


class WallFollower(Node):
    def __init__(self):
        super().__init__("wallfollower")
        self.get_logger().info("Wall_Follower")

        self.twist_msgs= Twist()
        self.cmd_vel_pub = self.create_publisher(
            msg_type=Twist, topic="/cmd_vel", qos_profile=10
        )
        self.get_logger().info("Initialized /cmd_vel Publisher")


        self.callback_group = ReentrantCallbackGroup()
        # declare and initialize scan subscriber
        self.scan_sub_qos = QoSProfile(
            depth=10,
            history=HistoryPolicy.KEEP_LAST,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            liveliness=LivelinessPolicy.AUTOMATIC,
        )
        self.scan_sub = self.create_subscription(
            msg_type=LaserScan,
            topic="/scan",
            callback=self.scan_callback,
            qos_profile=self.scan_sub_qos,
            callback_group=self.callback_group,
        )
        self.get_logger().info("Initialized /scan Subscriber")

        self.angular_max= 3.0
        self.angular_min= 0.0
        self.linear_min= 0.0
        self.linear_max= 2.5

        self.state= 0

        self.state_dict= {
            0:'find the wall',
            1:'turn left',
            2:'follow the wall',
        }


        self.timer = self.create_timer(0.05, self.control)






    def scan_callback(self, scan_msg: LaserScan):
        
        ranges = scan_msg.ranges
        n = len(ranges)
        step = n // 5  # divide into 5 chunks

        region = {
            "right":  min(ranges[0:step] or [float('inf')]),
            "fright": min(ranges[step:2*step] or [float('inf')]),
            "front":  min(ranges[2*step:3*step] or [float('inf')]),
            "fleft":  min(ranges[3*step:4*step] or [float('inf')]),
            "left":   min(ranges[4*step:] or [float('inf')]),
        }
        # self.get_logger().info("~~~~~ Start laser 1 ~~~~")
        # region = {
        #     "right": min(min(scan_msg.ranges[0:143]), 6),
        #     "fright": min(min(scan_msg.ranges[144:287]), 6),
        #     "front": min(min(scan_msg.ranges[288:431]), 6),
        #     "fleft": min(min(scan_msg.ranges[432:575]), 6),
        #     "left": min(min(scan_msg.ranges[576:713]), 6)
        # }
        # self.get_logger().info("~~~~~ Start laser 2 ~~~~")

        self.take_action(regions=region)


    def change_state(self,state:int):
        if state != self.state:
            self.get_logger().info(f"Wall follower: {state}:{self.state_dict[state]}")
            self.state=state


    def take_action(self, regions: dict):
        # self.get_logger().info("~~~~~ Start take 1 ~~~~")

        linear_x = 0
        angula_z = 0

        angular_max=5.0
        linear_max=3.5
        angular_min=0.0
        linear_min=0.0

        state_discription = ""
        max_dist_alw = 1.5
        if (
            regions["front"] > max_dist_alw
            and regions["fleft"] > max_dist_alw
            and regions["fright"] > max_dist_alw
        ):
            state_discription = "case1 : do nothing"
            self.change_state(0)
        elif (

            regions["front"] < max_dist_alw
            and regions["fleft"] > max_dist_alw
            and regions["fright"] > max_dist_alw
        ):
            state_discription = "case2: front"
            self.change_state(1)

        elif (
            regions["front"] > max_dist_alw
            and regions["fleft"] > max_dist_alw
            and regions["fright"] < max_dist_alw
        ):
            state_discription = "case3 : fright"
            self.change_state(2)

        elif (
            regions["front"] > max_dist_alw
            and regions["fleft"] < max_dist_alw
            and regions["fright"] > max_dist_alw
        ):
            state_discription = "case3 : fleft"

            self.change_state(0)

        elif (
            regions["front"] < max_dist_alw
            and regions["fleft"] > max_dist_alw
            and regions["fright"] < max_dist_alw
        ):
            state_discription = "case5 : front and fright"
            self.change_state(1)

        elif (
            regions["front"] < max_dist_alw
            and regions["fleft"] < max_dist_alw
            and regions["fright"] > max_dist_alw
        ):
            state_discription = "case6 : front and fleft"
            self.change_state(1)

        elif (
            regions["front"] < max_dist_alw
            and regions["fleft"] < max_dist_alw
            and regions["fright"] < max_dist_alw
        ):
            state_discription = "case7 : fleft and fright and front"
            self.change_state(1)

        elif (
            regions["front"] > max_dist_alw
            and regions["fleft"] < max_dist_alw
            and regions["fright"] < max_dist_alw
        ):
            state_discription = "case8 : fleft and fright"
            self.change_state(0)


        else:
            state_discription = "UNKNOWN CASE"

        # self.get_logger().info(f"State: {state_discription}")

    def find_wall(self):
        self.twist_msgs.angular.z= -1*2.0
        self.twist_msgs.linear.x= 1.0
        # return(self.twist_msgs)
    def turn_left(self):
        self.twist_msgs.angular.z=self.angular_max
        self.twist_msgs.linear.x=0.0
        # return(self.twist_msgs)
    
    def follow_wall(self):
        self.twist_msgs.angular.z=0.0
        self.twist_msgs.linear.x=self.linear_max
        # return(self.twist_msgs)

    def control(self):
        if self.state==0:
            self.find_wall()

        elif self.state==1:
            self.turn_left()
        elif self.state==2:
            self.follow_wall()

        else:
            self.get_logger().info("Unknown State")

        self.cmd_vel_pub.publish(self.twist_msgs)

    def destroy(self):
        self.get_logger().info("Destroying node resources...")
        if self.timer is not None:
            self.timer.cancel()

        self.twist_msgs.angular.z= self.angular_min
        self.twist_msgs.linear.x= self.linear_min
        self.cmd_vel_pub.publish(self.twist_msgs)
        if self.cmd_vel_pub is not None:
            self.destroy_publisher(self.cmd_vel_pub)
        # Destroy other resources (subscribers, clients, etc.) here
        self.destroy_node()


            
def main(args=None):
    rclpy.init(args=args)
    node = WallFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy()   # <-- call custom destroy
        rclpy.shutdown()
   

if __name__ == '__main__':
    main()




