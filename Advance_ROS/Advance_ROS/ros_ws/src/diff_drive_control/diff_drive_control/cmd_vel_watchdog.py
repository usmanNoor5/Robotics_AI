import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class CmdVelWatchdog(Node):
    """
    Publishes zero cmd_vel at a fixed rate whenever no other node is
    publishing on cmd_vel.  This keeps the diff-drive plugin's PID
    actively holding the robot at rest instead of coasting freely.

    When the APF controller (or any other controller) is running, it
    shows up in the publisher list and the watchdog goes silent so it
    does not interfere with control commands.
    """

    def __init__(self):
        super().__init__('cmd_vel_watchdog')
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)
        # 10 Hz is fast enough to keep the robot held without flooding
        self.create_timer(0.1, self.watchdog_loop)
        self.get_logger().info('cmd_vel watchdog running — robot will hold position when idle.')

    def watchdog_loop(self):
        # Get all publishers on /cmd_vel except ourselves
        pub_info = self.get_publishers_info_by_topic('/cmd_vel')
        external = [p for p in pub_info if p.node_name != self.get_name()]
        if not external:
            self.publisher_.publish(Twist())   # all-zero = hold still


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelWatchdog()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
