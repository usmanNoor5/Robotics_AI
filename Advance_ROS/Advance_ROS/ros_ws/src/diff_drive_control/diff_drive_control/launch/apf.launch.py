from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():

    apf_conf = PathJoinSubstitution(
        [get_package_share_directory("diff_drive_control"), "config", "apf.yaml"]
    )

    return LaunchDescription(
        [
            Node(
                package="diff_drive_control",
                executable="apf_controller",
                name="apf_controller",
                output="screen",
                parameters=[apf_conf],
            )
        ]
    )
