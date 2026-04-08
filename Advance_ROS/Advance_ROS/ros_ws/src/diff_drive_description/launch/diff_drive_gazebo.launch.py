import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue

def declare_args(context, *args, **kwargs):
    # Initializes the robot_type parameter passed via command line [cite: 323, 327]
    robot_type_arg = DeclareLaunchArgument(
        'robot_type',
        default_value='',
        description='Type of robot model to load (base, with_lidar, with_control)'
    )
    return [robot_type_arg]

def launch_setup(context, *args, **kwargs):
    # Process the robot_type parameter [cite: 353, 355]
    robot_type_value = context.perform_substitution(LaunchConfiguration('robot_type'))
    package_name = 'diff_drive_description'

    # Map the argument to the correct xacro file [cite: 372, 374, 376]
    if robot_type_value == 'base':
        xacro_file = 'my_robot.urdf.xacro'
    elif robot_type_value == 'with_lidar':
        xacro_file = 'my_robot_with_lidar.urdf.xacro'
    elif robot_type_value == 'with_control':
        xacro_file = 'my_robot_with_lidar_control.urdf.xacro'
    else:
        raise ValueError(f'Unknown robot type: {robot_type_value}') # [cite: 384]

    # Path to the robot description file [cite: 390, 392]
    robot_description_path = os.path.join(
        get_package_share_directory(package_name),
        'urdf',
        xacro_file
    )

    # 1. Robot State Publisher Node [cite: 412, 413]
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(Command(['xacro ', robot_description_path]), value_type=str)
        }]
    )

    # 2. Ignition Gazebo Node (World Setup) [cite: 850, 889]
    ignition_gazebo_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py' # [cite: 893]
            ])
        ]),
        launch_arguments=[('gz_args', [' -r -v 4 empty.sdf'])] # [cite: 894]
    )

    # 3. Spawn Node (Injects the robot into the simulation) [cite: 850, 859]
    spawn_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'diff_drive', # [cite: 861]
            '-x', '0', '-y', '0', '-z', '0.1', # [cite: 865, 867, 868]
            '-topic', '/robot_description' # [cite: 873]
        ],
        output='screen'
    )

    # 4. ROS 2-Gazebo Bridge (Maps internal Gazebo topics to ROS 2) [cite: 824, 903]
    # Configuration varies based on whether sensors or control are active [cite: 905, 911]
    if robot_type_value == 'with_lidar':
        bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                'lidar@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan', # [cite: 909]
                '/lidar/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked' # [cite: 910]
            ],
            output='screen'
        )
    elif robot_type_value == 'with_control':
        bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                'lidar@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan', # [cite: 924]
                '/lidar/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked', # [cite: 925]
                'cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist', # ROS->Gazebo only
                '/model/diff_drive/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry' # [cite: 926]
            ],
            output='screen'
        )
    watchdog_node = Node(
        package='diff_drive_control',
        executable='cmd_vel_watchdog',
        name='cmd_vel_watchdog',
        output='screen',
    )

    if robot_type_value == 'with_control':
        return [robot_state_publisher_node, spawn_node, ignition_gazebo_node, bridge, watchdog_node]
    elif robot_type_value != 'base':
        return [robot_state_publisher_node, spawn_node, ignition_gazebo_node, bridge]
    else:
        return [robot_state_publisher_node, spawn_node, ignition_gazebo_node]

    # # Define the return list of nodes [cite: 935, 936]
    # nodes = [robot_state_publisher_node, ignition_gazebo_node, spawn_node]
    # if bridge:
    #     nodes.append(bridge)
    
    # return nodes

def generate_launch_description():
    # Entry point of the launch file using OpaqueFunction for dynamic setup [cite: 471, 474]
    return LaunchDescription([
        OpaqueFunction(function=declare_args), # [cite: 482]
        OpaqueFunction(function=launch_setup)  # [cite: 482]
    ])