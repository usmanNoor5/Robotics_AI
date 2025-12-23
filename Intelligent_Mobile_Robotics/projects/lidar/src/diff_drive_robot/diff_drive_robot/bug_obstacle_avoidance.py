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


# side_choice = "left"


class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__("obstacle_avoid")
        self.get_logger().info("obstacle_avoidance")

        self.msgs = Twist()

        # declare and initialize cmd_vel publisher
        self.cmd_vel_pub = self.create_publisher(
            msg_type=Twist, topic="/cmd_vel", qos_profile=10
        )
        self.get_logger().info("Initialized /cmd_vel Publisher")

        # declare and initialize callback group
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

        # declare and initialize odom subscriber
        self.odom_sub_qos = QoSProfile(
            depth=10,
            history=HistoryPolicy.KEEP_LAST,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            liveliness=LivelinessPolicy.AUTOMATIC,
        )
        self.odom_sub = self.create_subscription(
            msg_type=Odometry,
            topic="/odom",
            callback=self.odom_callback,
            qos_profile=self.odom_sub_qos,
            callback_group=self.callback_group,
        )
        self.get_logger().info("Initialized /odom Subscriber")

        # declare and initialize control timer callback
        # self.control_timer = self.create_timer(
        #     timer_period_sec=0.200,
        #     callback=self.control_callback,
        #     callback_group=self.callback_group,
        # )
        self.get_logger().info("Initialized Control Timer")

        self.get_logger().info("Obstacle Avoidance Initialized !")

    # class destructor
    def __del__(self):
        return None
    robot_radius = 0.50   # 0.5 m = 50 cm
    
    side_threshold_min = robot_radius + 0.05   # 0.55 m → at least a 5 cm gap from wall
    side_threshold_max = robot_radius + 0.10   # 0.60 m → at most 10 cm gap from wall

    # for front collision avoidance
    front_threshold = robot_radius + 0.40      # 0.90 m → turn if obstacle within 90 cm
    pi = 3.141592654
    pi_inv = 0.318309886
    ignore_iterations = 5
    # process variables
    wall_found = False
    side_chosen = "left"
    lin_vel_zero = 0.000
    lin_vel_slow = 0.500
    lin_vel_fast = 0.500
    ang_vel_zero = 0.000
    ang_vel_slow = 0.050
    ang_vel_fast = 1.500
    ang_vel_mult = 0.0

    # scan subscriber variables
    scan_info_done = False
    scan_angle_min = 0.0
    scan_angle_max = 0.0
    scan_angle_inc = 0.0
    scan_range_min = 0.0
    scan_range_max = 0.0
    scan_right_range = 0.0
    scan_front_range = 0.0
    scan_left_range = 0.0
    scan_angle_range = 0
    scan_ranges_size = 0
    scan_right_index = 0
    scan_front_index = 0
    scan_left_index = 0
    scan_sides_angle_range = 15  # degs
    scan_front_angle_range = 15  # degs
    scan_right_range_from_index = 0
    scan_right_range_to_index = 0
    scan_front_range_from_index = 0
    scan_front_range_to_index = 0
    scan_left_range_from_index = 0
    scan_left_range_to_index = 0

    # odom subscriber variables
    odom_info_done = False
    odom_initial_x = 0.0
    odom_initial_y = 0.0
    odom_initial_yaw = 0.0
    odom_curr_x = 0.0
    odom_curr_y = 0.0
    odom_curr_yaw = 0.0
    odom_prev_x = 0.0
    odom_prev_y = 0.0
    odom_prev_yaw = 0.0
    odom_distance = 0.0
    odom_lin_vel = 0.0
    odom_ang_vel = 0.0
    angles = dict()

    def take_action(self, regions: dict):
        self.get_logger().info("~~~~~ Start take 1 ~~~~")

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
            linear_x = linear_max
            angula_z = angular_min
        elif (
            regions["front"] < max_dist_alw
            and regions["fleft"] > max_dist_alw
            and regions["fright"] > max_dist_alw
        ):
            state_discription = "case2: front"
            linear_x = linear_min
            angula_z = angular_max
        elif (
            regions["front"] > max_dist_alw
            and regions["fleft"] > max_dist_alw
            and regions["fright"] < max_dist_alw
        ):
            state_discription = "case3 : fright"
            linear_x = linear_min
            angula_z = angular_max
        elif (
            regions["front"] > max_dist_alw
            and regions["fleft"] < max_dist_alw
            and regions["fright"] > max_dist_alw
        ):
            state_discription = "case3 : fleft"
            linear_x = linear_min
            angula_z = -1*angular_max
        elif (
            regions["front"] < max_dist_alw
            and regions["fleft"] > max_dist_alw
            and regions["fright"] < max_dist_alw
        ):
            state_discription = "case5 : front and fright"
            linear_x = linear_min
            angula_z = angular_max
        elif (
            regions["front"] < max_dist_alw
            and regions["fleft"] < max_dist_alw
            and regions["fright"] > max_dist_alw
        ):
            state_discription = "case6 : front and fleft"
            linear_x = linear_min
            angula_z = -1*angular_max
        elif (
            regions["front"] < max_dist_alw
            and regions["fleft"] < max_dist_alw
            and regions["fright"] < max_dist_alw
        ):
            state_discription = "case7 : fleft and fright and front"
            linear_x = linear_min
            angula_z = angular_max
        elif (
            regions["front"] > max_dist_alw
            and regions["fleft"] < max_dist_alw
            and regions["fright"] < max_dist_alw
        ):
            state_discription = "case8 : fleft and fright"
            linear_x = linear_max
            angula_z = angular_min

        else:
            state_discription = "UNKNOWN CASE"

        self.get_logger().info(f"State: {state_discription}")
        self.msgs.linear.x = linear_x
        self.msgs.angular.z = angula_z

        self.cmd_vel_pub.publish(self.msgs)

    def odom_callback(self, odom_msg):
        if (self.odom_info_done):
            # do this step continuously
            # get current odometry values
            self.odom_curr_x = odom_msg.pose.pose.position.x
            self.odom_curr_y = odom_msg.pose.pose.position.y
            angles = self.euler_from_quaternion(odom_msg.pose.pose.orientation.x,
                                                odom_msg.pose.pose.orientation.y,
                                                odom_msg.pose.pose.orientation.z,
                                                odom_msg.pose.pose.orientation.w)
            self.odom_curr_yaw = angles["yaw_deg"]
            # calculate distance based on current and previous odometry values
            self.odom_distance += self.calculate_distance(self.odom_prev_x,
                                                          self.odom_prev_y,
                                                          self.odom_curr_x,
                                                          self.odom_curr_y)
            # set previous odometry values to current odometry values
            self.odom_prev_x = self.odom_curr_x
            self.odom_prev_y = self.odom_curr_y
            self.odom_prev_yaw = self.odom_curr_yaw
        else:
            self.get_logger().info("~~~~~ Start Odom Info ~~~~")

            # do this step only once
            # get initial odometry values
            self.odom_initial_x = odom_msg.pose.pose.position.x
            self.odom_initial_y = odom_msg.pose.pose.position.y
            angles = self.euler_from_quaternion(odom_msg.pose.pose.orientation.x,
                                                odom_msg.pose.pose.orientation.y,
                                                odom_msg.pose.pose.orientation.z,
                                                odom_msg.pose.pose.orientation.w)
            self.odom_initial_yaw = angles["yaw_deg"]
            # set previous odometry values to initial odometry values
            self.odom_prev_x = self.odom_initial_x
            self.odom_prev_y = self.odom_initial_y
            self.odom_prev_yaw = self.odom_initial_yaw
            # set flag to true so this step will not be done again
            self.odom_info_done = True
            # print odom details
            self.get_logger().info("~~~~~ Start Odom Info ~~~~")
            self.get_logger().info("odom_initial_x: %+0.3f" % (self.odom_initial_x))
            self.get_logger().info("odom_initial_y: %+0.3f" % (self.odom_initial_y))
            self.get_logger().info("odom_initial_yaw: %+0.3f" % (self.odom_initial_yaw))
            self.get_logger().info("~~~~~ End Odom Info ~~~~")
        return None
    def euler_from_quaternion(self, quat_x, quat_y, quat_z, quat_w):
        # function to convert quaternions to euler angles

        # calculate roll
        sinr_cosp = 2 * (quat_w * quat_x + quat_y * quat_z)
        cosr_cosp = 1 - 2 * (quat_x * quat_x + quat_y * quat_y)
        roll_rad = math.atan2(sinr_cosp, cosr_cosp)
        roll_deg = (roll_rad * 180 * self.pi_inv)

        # calculate pitch
        sinp = 2 * (quat_w * quat_y - quat_z * quat_x)
        pitch_rad = math.asin(sinp)
        pitch_deg = (pitch_rad * 180 * self.pi_inv)

        # calculate yaw
        siny_cosp = 2 * (quat_w * quat_z + quat_x * quat_y)
        cosy_cosp = 1 - 2 * (quat_y * quat_y + quat_z * quat_z)
        yaw_rad = math.atan2(siny_cosp, cosy_cosp)
        yaw_deg = (yaw_rad * 180 * self.pi_inv)

        # store the angle values in a dict
        angles = dict()
        angles["roll_rad"] = roll_rad
        angles["roll_deg"] = roll_deg
        angles["pitch_rad"] = pitch_rad
        angles["pitch_deg"] = pitch_deg
        angles["yaw_rad"] = yaw_rad
        angles["yaw_deg"] = yaw_deg

        # return the angle values
        return angles
    def calculate_distance(self, prev_x, prev_y, curr_x, curr_y):
        # function to calculate euclidean distance in 2d plane

        #calculate distance
        distance = ((((curr_x - prev_x) ** 2.0) +
                     ((curr_y - prev_y) ** 2.0)) ** 0.50)

        #return the distance value
        return distance

    def scan_callback(self, scan_msg: LaserScan):
        

        if self.scan_info_done:
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

        else:
            
    #         # do this step only once
    #         # get the min and max angles
    #         self.scan_angle_min = scan_msg.angle_min
    #         self.scan_angle_max = scan_msg.angle_max
    #         # get the min and max range values
    #         self.scan_range_min = scan_msg.range_min
    #         self.scan_range_max = scan_msg.range_max
    #         # get the size of the ranges array
    #         self.scan_ranges_size = len(scan_msg.ranges)
    #         # get the total scan angle range
    #         self.scan_angle_range = int(
    #             (abs(self.scan_angle_min) + abs(self.scan_angle_max))
    #             * (180.0 / self.pi)
    #         )
    #         # get the angle increments per scan ray
    #         self.scan_angle_inc = self.scan_angle_range / self.scan_ranges_size
    #         # calculate the front, right and left scan ray indexes
    #         self.scan_front_index = self.scan_ranges_size / 2
    #         self.scan_right_index = (
    #             self.scan_front_index - int(90.0 / self.scan_angle_inc) - 1
    #         )
    #         self.scan_left_index = (
    #             self.scan_front_index + int(90.0 / self.scan_angle_inc) + 1
    #         )
    #         # calculate the front scan ray ranges
    #         self.scan_front_range_from_index = self.scan_front_index - int(
    #             self.scan_front_angle_range / self.scan_angle_inc
    #         )
    #         self.scan_front_range_to_index = self.scan_front_index + int(
    #             self.scan_front_angle_range / self.scan_angle_inc
    #         )
    #         # calculate right and left scan ray ranges
    #         if self.scan_angle_range > 180:
    #             self.scan_right_range_from_index = self.scan_right_index - int(
    #                 self.scan_sides_angle_range / self.scan_angle_inc
    #             )
    #             self.scan_right_range_to_index = self.scan_right_index + int(
    #                 self.scan_sides_angle_range / self.scan_angle_inc
    #             )
    #             self.scan_left_range_from_index = self.scan_left_index - int(
    #                 self.scan_sides_angle_range / self.scan_angle_inc
    #             )
    #             self.scan_left_range_to_index = self.scan_left_index + int(
    #                 self.scan_sides_angle_range / self.scan_angle_inc
    #             )
    #         else:
    #             self.scan_right_range_from_index = self.scan_right_index
    #             self.scan_right_range_to_index = self.scan_right_index + int(
    #                 self.scan_sides_angle_range / self.scan_angle_inc
    #             )
    #             self.scan_left_range_from_index = self.scan_left_index - int(
    #                 self.scan_sides_angle_range / self.scan_angle_inc
    #             )
    #             self.scan_left_range_to_index = self.scan_left_index
    #         # set flag to true so this step will not be done again
            self.scan_info_done = True
    #         # print scan details
    #         self.get_logger().info("~~~~~ Start Scan Info ~~~~")
    #         self.get_logger().info("scan_angle_min: %+0.3f" % (self.scan_angle_min))
    #         self.get_logger().info("scan_angle_max: %+0.3f" % (self.scan_angle_max))
    #         self.get_logger().info("scan_range_min: %+0.3f" % (self.scan_range_min))
    #         self.get_logger().info("scan_range_max: %+0.3f" % (self.scan_range_max))
    #         self.get_logger().info("scan_angle_range: %d" % (self.scan_angle_range))
    #         self.get_logger().info("scan_ranges_size: %d" % (self.scan_ranges_size))
    #         self.get_logger().info("scan_angle_inc: %+0.3f" % (self.scan_angle_inc))
    #         self.get_logger().info("scan_right_index: %d" % (self.scan_right_index))
    #         self.get_logger().info("scan_front_index: %d" % (self.scan_front_index))
    #         self.get_logger().info("scan_left_index: %d" % (self.scan_left_index))
    #         self.get_logger().info("scan_right_range_index:")
    #         self.get_logger().info(
    #             "from: %d ~~~> to: %d"
    #             % (self.scan_right_range_from_index, self.scan_right_range_to_index)
    #         )
    #         self.get_logger().info("scan_front_range_index:")
    #         self.get_logger().info(
    #             "from: %d ~~~> to: %d"
    #             % (self.scan_front_range_from_index, self.scan_front_range_to_index)
    #         )
    #         self.get_logger().info("scan_left_range_index:")
    #         self.get_logger().info(
    #             "from: %d ~~~> to: %d"
    #             % (self.scan_left_range_from_index, self.scan_left_range_to_index)
    #         )
    #         self.get_logger().info("~~~~~ End Scan Info ~~~~")
        return None


def main(args=None):

    # initialize ROS2 node
    rclpy.init(args=args)

    # create an instance of the wall follower class
    wall_follower = ObstacleAvoidance()
    
    # create a multithreaded executor
    executor = MultiThreadedExecutor(num_threads=4)
    
    # add the wall follower node to the executor
    executor.add_node(wall_follower)

    try:
        # spin the executor to handle callbacks
        executor.spin()
    except Exception as e:
        wall_follower.get_logger().error(f"Exception in executor: {e}")
        
    # finally:
    #     # indicate wall follower node termination
    #     wall_follower.get_logger().info("Terminating Wall Follower ...")
    #     # stop the robot
    #     # wall_follower.twist_cmd.linear.x = wall_follower.lin_vel_zero
    #     # wall_follower.twist_cmd.angular.z = wall_follower.ang_vel_zero
    #     # publish the twist command
    #     # wall_follower.publish_twist_cmd()
    #     wall_follower.get_logger().info("Wall Follower Terminated !")
    
    # shutdown the executor when spin completes
    executor.shutdown()
    
    # destroy the wall follower node
    wall_follower.destroy_node()

    # shutdown ROS2 node when spin completes
    rclpy.shutdown()

    return None


if __name__ == "__main__":
    main()

# End of Code
