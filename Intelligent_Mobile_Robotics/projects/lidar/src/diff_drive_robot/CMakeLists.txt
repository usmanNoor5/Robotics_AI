cmake_minimum_required(VERSION 3.8)
project(diff_drive_robot)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(tf2 REQUIRED)

# Install launch files, URDF, configs, etc.
install(
  DIRECTORY launch urdf config worlds rviz
  DESTINATION share/${PROJECT_NAME}
)

# Install Python modules (packages)
ament_python_install_package(${PROJECT_NAME})

# Install standalone Python scripts
install(PROGRAMS
  ${PROJECT_NAME}/bug.py
  ${PROJECT_NAME}/dist.py
  ${PROJECT_NAME}/location.py
  ${PROJECT_NAME}/bug_test.py
  ${PROJECT_NAME}/bug_obstacle_avoidance.py
  ${PROJECT_NAME}/go_to_point.py
  ${PROJECT_NAME}/wall_follower.py
  ${PROJECT_NAME}/obstacle.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
