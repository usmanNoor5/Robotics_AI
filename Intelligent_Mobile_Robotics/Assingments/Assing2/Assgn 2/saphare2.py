import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ----------------------------
# Environment 201 - Data Setup
# ----------------------------

# Obstacles
obstacle_data = {
    "Environment_ID": [201, 201, 201, 201],
    "Dim": ["3D", "3D", "3D", "3D"],
    "Obstacle_ID": ["S1", "S2", "S3", "S4"],
    "Type": ["sphere", "sphere", "sphere", "sphere"],
    "CenterX": [4, 7, 6, 2],
    "CenterY": [4, 7, 2, 8],
    "CenterZ": [4, 2, 6, 3],
    "Radius": [2, 1.5, 1, 1]
}

# Start and goal positions
env_data = {
    "Environment_ID": [201],
    "Dim": ["3D"],
    "StartX": [0],
    "StartY": [0],
    "StartZ": [0],
    "GoalX": [8],
    "GoalY": [9],
    "GoalZ": [7]
}

# Convert to DataFrames
obstacles = pd.DataFrame(obstacle_data)
env = pd.DataFrame(env_data)

# ----------------------------
# 3D Visualization
# ----------------------------

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

# Plot start and goal
ax.scatter(env["StartX"], env["StartY"], env["StartZ"], color='green', s=100, label='Start')
ax.scatter(env["GoalX"], env["GoalY"], env["GoalZ"], color='red', s=100, label='Goal')

# Plot spherical obstacles
u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
for _, row in obstacles.iterrows():
    x = row["Radius"] * np.cos(u) * np.sin(v) + row["CenterX"]
    y = row["Radius"] * np.sin(u) * np.sin(v) + row["CenterY"]
    z = row["Radius"] * np.cos(v) + row["CenterZ"]
    ax.plot_surface(x, y, z, color='gray', alpha=0.4, linewidth=0)

# Set plot limits and labels
ax.set_xlim(-1, 10)
ax.set_ylim(-1, 10)
ax.set_zlim(-1, 10)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("3D Environment 201 with Spherical Obstacles")

ax.legend()
plt.show()
