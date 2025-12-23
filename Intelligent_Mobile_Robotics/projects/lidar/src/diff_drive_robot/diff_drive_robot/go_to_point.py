#! /usr/bin/python3
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
from geometry_msgs.msg import Twist, Point # twist message
from nav_msgs.msg import Odometry  # odometry message
from sensor_msgs.msg import LaserScan  # laser scan message
from tf_transformations import euler_from_quaternion

# standard imports
import math

class GoToPoint(Node):
    def __init__(self):
        super().__init__("go_to_point")
        self.get_logger().info("Go To Point")


        self.twist_msgs =Twist()
        self.declare_parameter("GPointx", 8)   
        self.declare_parameter("GPointy", 0) 
        self.point_x = self.get_parameter("GPointx").get_parameter_value().integer_value
        self.point_y = self.get_parameter("GPointy").get_parameter_value().integer_value

        self.cmd_vel_pub = self.create_publisher(
            msg_type=Twist, topic="/cmd_vel", qos_profile=10
        )
        self.get_logger().info("Initialized /cmd_vel Publisher")

        self.angular_max= 0.6
        self.angular_min= 0.0
        self.linear_min= 0.0
        self.linear_max= 1.0

        self.state= 0

        self.curr_point= Point()

        self.desired_point= Point()
        self.desired_point.x= self.point_x
        self.desired_point.y= self.point_y
        self.desired_point.z= 0
        self.odom_curr_yaw=0

        self.yaw_precision= math.pi/90
        self.precision= 0.3


        self.callback_group = ReentrantCallbackGroup()

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

        self.timer = self.create_timer(0.05, self.control)

    def odom_callback(self,odom_msg:Odometry):
        self.curr_point=  odom_msg.pose.pose.position
        quarentine=[odom_msg.pose.pose.orientation.x,
                                                odom_msg.pose.pose.orientation.y,
                                                odom_msg.pose.pose.orientation.z,
                                                odom_msg.pose.pose.orientation.w]

        angles = euler_from_quaternion(quarentine)
        self.odom_curr_yaw=angles[2]
        



    def fix_yaw(self,posi:Point):
        desired_yaw= math.atan2(posi.y-self.curr_point.y,posi.x-self.curr_point.x)
        err=desired_yaw-self.odom_curr_yaw

        if math.fabs(err)>self.yaw_precision:
            self.twist_msgs.angular.z= self.angular_max if err >0 else -1*self.angular_max

        self.cmd_vel_pub.publish(self.twist_msgs)

        if math.fabs(err)<=self.yaw_precision:
            self.get_logger().info(f"Yaw error {err}")
            self.change_state(1)

    def change_state(self,state:int):
        self.state= state
        self.get_logger().info(f" state changed {state}")

    def go_straight_ahead(self,posi:Point):
        desired_yaw= math.atan2(posi.y-self.curr_point.y,posi.x-self.curr_point.x)
        err_yaw=desired_yaw-self.odom_curr_yaw

        err_pos = math.sqrt(
    pow(posi.y - self.curr_point.y, 2) +
    pow(posi.x - self.curr_point.x, 2)
)


        if err_pos>self.precision:
            self.twist_msgs.angular.z=self.angular_min
            self.twist_msgs.linear.x=self.linear_max
            self.cmd_vel_pub.publish(self.twist_msgs)

        else:
            self.get_logger().info(f"Position error {err_pos}")
            self.change_state(2)

        if math.fabs(err_yaw)<=self.yaw_precision:
            self.get_logger().info(f"Yaw error {err_yaw}")
            self.change_state(0)

    def done(self):
        self.twist_msgs.angular.z =self.angular_min
        self.twist_msgs.linear.x =self.linear_min
        self.cmd_vel_pub.publish(self.twist_msgs)

    def control(self):
        if self.state == 0:
            self.fix_yaw(self.desired_point)

        elif self.state==1:
            self.go_straight_ahead(self.desired_point)
        
        elif self.state==2:
            self.done()
        else:
            self.get_logger().info(f"Unknown State")
    
    def destroy(self):
        self.get_logger().info("Destroying node resources...")
        if self.timer is not None:
            self.timer.cancel()

        self.twist_msgs.angular.z= self.angular_min
        self.twist_msgs.linear.x= self.angular_min
        self.cmd_vel_pub.publish(self.twist_msgs)
        if self.cmd_vel_pub is not None:
            self.destroy_publisher(self.cmd_vel_pub)
        # Destroy other resources (subscribers, clients, etc.) here
        self.destroy_node()



def main(args=None):
    rclpy.init(args=args)
    node = GoToPoint()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy()   # <-- call custom destroy
        rclpy.shutdown()
   

if __name__ == '__main__':
    main()



        




            

        


        

        


         


