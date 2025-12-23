# Bumperbot ROS2 Humble Tutorial - Tasks 1, 2, and 3

This README provides step-by-step instructions for completing three progressive tasks using the `bumperbot` ROS2 package on Ubuntu 22.04 with ROS2 Humble. The tasks cover basic square movement, localization-based navigation, and full SLAM with navigation.

**Important Note**: In **every new terminal**, always source the workspace first:

```bash
. ~/bumperbot_ws/install/setup.bash
```
(Assume your workspace is at ~/bumperbot_ws. Adjust the path if different.)
Prerequisites

Install Ubuntu 22.04 LTS.
Install ROS2 Humble (official guide: https://docs.ros.org/en/humble/Installation.html).
Place the bumperbot packages in ~/bumperbot_ws/src.
After any code modifications, rebuild the workspace:

```bash
cd ~/bumperbot_ws
colcon build
. install/setup.bash
```
## Task 1 — Basic Square Movement (No Localization / SLAM) ▶️

**Goal:** Make the robot move in a square using a simple controller.

**Steps:**

1. Edit `bumperbot_bringup/launch/simulated_robot.launch.py` (name may vary) and comment out SLAM and localization-related launch descriptions so only the basic simulation and controller run.

2. Build and source the workspace:

```bash
cd ~/bumperbot_ws
colcon build
. install/setup.bash
```

3. Run the simulation and controller in separate terminals (source the workspace in each terminal):

Terminal 1
```bash
ros2 launch bumperbot_bringup simulated_robot.launch.py
```

Terminal 2
```bash
ros2 run bumperbot_controller control.py
```

You should see the robot move in a square in Gazebo.

## Task 2 — Navigation with Known Map (Localization Only) 🗺️

**Goal:** Enable navigation using a pre-existing map and localization (AMCL). Use RViz's **2D Nav Goal** to set goals.

**Key steps:**

1. In `bumperbot_bringup/launch/simulated_robot.launch.py`, enable the localization section and keep SLAM disabled.

2. In `bumperbot_localization/launch/global_localization.launch.py`:
   - Copy the `lifecycle_nodes` list, remove `amcl` from the copy, and comment out the original `nav2_amcl` include (per the tutorial steps).

3. In `bumperbot_localization/launch/navigation.launch.py`, change references of `nav2_params` to `nav2_params_copy` where instructed.

4. Build the workspace:

```bash
cd ~/bumperbot_ws
colcon build
. install/setup.bash
```

5. Run the required nodes in separate terminals (source the workspace in each):

Terminal 1
```bash
ros2 launch bumperbot_bringup simulated_robot.launch.py world_name:=small_house use_slam:=false
```

Terminal 2
```bash
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map odom
```

Terminal 3
```bash
ros2 launch bumperbot_localization navigation.launch.py
```

Open RViz (if not launched), then use the **2D Nav Goal** tool to send navigation goals to the robot.

## Task 3 — Full SLAM + Navigation 🧭

**Goal:** Run online SLAM so the robot builds the map and navigates simultaneously.

**Steps:**

1. In `bumperbot_bringup/launch/simulated_robot.launch.py`, enable both SLAM and localization (uncomment relevant sections).

2. In `bumperbot_localization/launch/navigation.launch.py`, revert `nav2_params_copy` back to `nav2_params` and re-enable any previously commented lifecycle nodes (including AMCL).

3. Build the workspace:

```bash
cd ~/bumperbot_ws
colcon build
. install/setup.bash
```

4. Run the simulation and navigation launch files in separate terminals:

Terminal 1
```bash
ros2 launch bumperbot_bringup simulated_robot.launch.py world_name:=small_house use_slam:=true
```

Terminal 2
```bash
ros2 launch bumperbot_localization navigation.launch.py
```

In RViz you should see the map being built in real-time — use **2D Nav Goal** to send goals while SLAM and navigation run.


## Summary

**Task 1:** Open-loop square movement.

**Task 2:** Navigation on a static known map.

**Task 3:** Full autonomous SLAM + navigation.

Enjoy your bumperbot experiments!

Final Reminder: Always run 
```bash 
. ~/bumperbot_ws/install/setup.bash in every new terminal.
```
