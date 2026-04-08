import glob

from setuptools import find_packages, setup

package_name = 'diff_drive_description'
from glob import glob
import os
setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    # [cite: 499, 500, 501, 502, 503, 504, 743]
    data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (os.path.join('share', 'diff_drive_description', 'launch'),
     glob('launch/*.launch.py')),
    (os.path.join('share', package_name, 'urdf'),
     glob('urdf/*')),
    ('share/' + package_name, ['urdf/my_robot.urdf.xacro']),
    ('share/' + package_name, ['urdf/my_robot_with_lidar.urdf.xacro']),
    ('share/' + package_name, ['launch/display.launch.py']),
    # ('share/' + package_name, ['launch/diff_drive_gazebo.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='usman',
    maintainer_email='musmannoor2004@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
