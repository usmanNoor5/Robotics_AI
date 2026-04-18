from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    slam_conf_file = PathJoinSubstitution([
        get_package_share_directory('nav2_mobile_robot'),
        'config', 'slam.yaml'
    ])

    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_use_sim_time_argument = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation/Gazebo clock')

    start_async_slam_toolbox_node = Node(
        parameters=[
            slam_conf_file,
            {'use_sim_time': use_sim_time}
        ],
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen')

    ld = LaunchDescription()
    ld.add_action(declare_use_sim_time_argument)
    ld.add_action(start_async_slam_toolbox_node)

    return ld
                            