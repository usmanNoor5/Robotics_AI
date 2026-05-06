# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Source

```bash
# Source ROS2 first (Humble/Iron)
source /opt/ros/<distro>/setup.bash

# Build entire workspace
colcon build

# Build a single package
colcon build --packages-select <package_name>

# Source the workspace after building
source install/setup.bash
```

Always run `source install/setup.bash` after building before launching nodes.

## Running the Stack

This workspace is structured as a progressive learning path — each stage builds on the previous.

### Stage 1 — Basic robot in Gazebo (`my_robot_description` + `my_robot_bringup`)
```bash
ros2 launch my_robot_bringup my_robot.launch.xml
python3 src/my_robot_bringup/scripts/u_turn_box.py   # run while Gazebo is up
```

### Stage 2 — Robot with lidar and odometry (`diff_drive_description`)
```bash
# robot_type options: base | with_lidar | with_control
ros2 launch diff_drive_description diff_drive_gazebo.launch.py robot_type:=with_control
```

### Stage 3 — APF autonomous controller (`diff_drive_control`)
Requires Gazebo already running with `robot_type:=with_control`.
```bash
ros2 launch diff_drive_control apf.launch.py
ros2 param set /apf_controller goal "[5.0, 3.0]"   # change goal at runtime
```

### Stage 4 — Full Nav2 stack (`nav2_mobile_robot`)
Each command runs in a separate terminal:
```bash
ros2 launch nav2_mobile_robot display.launch.py       # Gazebo + RViz + bridges
ros2 launch nav2_mobile_robot slam.launch.py          # SLAM mapping (OR localization, not both)
ros2 launch nav2_mobile_robot localization.launch.py  # AMCL on pre-built map/maze.yaml
ros2 launch nav2_mobile_robot navigation.launch.py    # Nav2 planning + control
```

## Architecture

### Package Roles

| Package | Type | Role |
|---|---|---|
| `my_robot_description` | ament_cmake | First-gen URDF assets only (no lidar, no sensors) |
| `my_robot_bringup` | ament_cmake | Launch `my_robot` into Gazebo + bridge config + u_turn demo script |
| `diff_drive_description` | ament_python | Evolved URDF with 3 robot variants (`base`, `with_lidar`, `with_control`) |
| `diff_drive_control` | ament_python | APF controller node + cmd_vel watchdog node |
| `nav2_mobile_robot` | ament_python | Full Nav2 stack in a maze world (SLAM, AMCL, DWB, behavior trees) |

### Key Topics

| Topic | Type | Flow |
|---|---|---|
| `cmd_vel` | `geometry_msgs/Twist` | ROS → Gazebo |
| `lidar` | `sensor_msgs/LaserScan` | Gazebo → ROS |
| `/model/diff_drive/odometry` | `nav_msgs/Odometry` | Gazebo → ROS (APF uses this) |
| `/odom` | `nav_msgs/Odometry` | Gazebo → ROS (Nav2 uses this) |
| `/tf`, `/clock`, `/joint_states` | — | Bridged via `ros_gz_bridge` |

### APF Controller (`diff_drive_control`)

The `apf_controller` node implements Artificial Potential Fields:
- **Attractive force**: pulls toward `goal` param with gain `kp`
- **Repulsive force**: pushes away from obstacles within `repulsion_radius` using LiDAR; angles are transformed from robot-local to world frame
- **Emergency stop**: reverses slowly (`linear.x = -0.05`) when obstacle is within `emergency_stop_dist`
- **Local minima escape**: if the robot hasn't moved >0.05m in `local_minima_timeout` seconds, spins at `angular.z=0.6` for 2.5s
- **Velocity smoothing**: acceleration-limited steps (linear: 0.15 m/s/step, angular: 0.6 rad/s/step)
- All params in `diff_drive_control/config/apf.yaml`; live-tunable via `ros2 param set`

The `cmd_vel_watchdog` node publishes zero-velocity at 10 Hz when the APF controller is inactive, preventing the robot from drifting.

### Nav2 Stack (`nav2_mobile_robot`)

- **World**: `world/maze.sdf`
- **Pre-built map**: `map/maze.pgm` + `map/maze.yaml` (0.05 m/pixel, origin at −10,−10.1)
- **SLAM**: `slam_toolbox` async, Ceres solver, scan on `/lidar`
- **Localization**: AMCL (`DifferentialMotionModel`, 500–2000 particles, initial pose at origin)
- **Local planner**: DWB at 20 Hz, max 0.26 m/s linear / 1.0 rad/s angular
- **Global planner**: NavFn (Dijkstra)
- **Costmaps**: local 25×25m rolling window, global with static + obstacle layers; inflation radius 0.35m local / 0.55m global

All Nav2 nodes run with `use_sim_time=True` and are managed by `nav2_lifecycle_manager`.

### Gazebo Bridge Pattern

Bridges are declared per `robot_type` in `diff_drive_description/launch/diff_drive_gazebo.launch.py`. The `with_control` variant adds `cmd_vel` (ROS→Gz) and `/model/diff_drive/odometry` (Gz→ROS). The `nav2_mobile_robot` bridge config also includes `/odom/tf` → `/tf` and `/clock`.

## Robot Physical Parameters

- Body: 0.6 × 0.4 × 0.2 m, mass 5 kg
- Wheels: radius 0.1 m, separation 0.5 m
- Lidar: 640 samples/scan, ±80° horizontal FOV, 0.1–10 m range, 10 Hz, mounted 0.2 m above `base_link` on `lidar_link`
- Drive wheel friction: µ=1.5; caster friction: µ=0.01

## Notes

- `my_robot_bringup/scripts/u_turn_box.py` is not registered as an entry point — run with `python3` directly, not via `ros2 run`.
- `my_robot_description` and `diff_drive_description` are two separate generations of the same robot. Prefer `diff_drive_description` for any sensor or navigation work.
- SLAM and localization launches are mutually exclusive — do not run both at the same time.
