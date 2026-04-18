import os
from launch import LaunchDescription
from launch_ros.actions import Node
import launch_ros.descriptions
from launch.substitutions import Command
from launch.substitutions import PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.actions import OpaqueFunction
from launch.actions import SetEnvironmentVariable
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    xacro_path = 'nav2_mobile_robot.xacro'

    pkg_nav2_mobile_robot = get_package_share_directory('nav2_mobile_robot')

    robot_description = PathJoinSubstitution([
        pkg_nav2_mobile_robot,
        xacro_path
    ])

    maze_world = os.path.join(pkg_nav2_mobile_robot, 'world', 'maze.sdf')

    ign_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=[os.path.join(pkg_nav2_mobile_robot)])

    ignition_gazebo_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            ])
        ]),
        launch_arguments=[('gz_args', [' -r -v 4 ' + maze_world])])

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(Command(['xacro ', robot_description]), value_type=str),
            'use_sim_time': True
        }]
    )

    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen')

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'nav2_mobile_robot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1',
        ],
        output='screen')

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['lidar@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
                '/lidar/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked',
                '/odom/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
                'cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
                '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model',
                '/model/diff_drive/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry',
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],                
        output='screen',
        remappings=[
            ('/model/diff_drive/odometry', '/odom'),
            ('/odom/tf', '/tf'),
        ])

    ld = LaunchDescription()
    ld.add_action( ign_resource_path )
    ld.add_action( ignition_gazebo_node )
    ld.add_action( robot_state_publisher_node )
    ld.add_action( spawn_robot )
    ld.add_action( rviz2_node )
    ld.add_action( bridge )

    return ld
