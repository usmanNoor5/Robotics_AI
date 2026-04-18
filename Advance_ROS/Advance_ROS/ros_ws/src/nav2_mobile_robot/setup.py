from setuptools import find_packages, setup

package_name = 'nav2_mobile_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name, ['urdf/nav2_mobile_robot.xacro']),
        ('share/' + package_name, ['urdf/nav2_mobile_robot_macro.xacro']),
        ('share/' + package_name, ['launch/display.launch.py']),
        ('share/' + package_name, ['launch/slam.launch.py']),
        ('share/' + package_name, ['launch/localization.launch.py']),
        ('share/' + package_name, ['launch/navigation.launch.py']),
        ('share/' + package_name + '/config', ['config/slam.yaml']),
        ('share/' + package_name + '/config', ['config/amcl.yaml']),
        ('share/' + package_name + '/config', ['config/nav.yaml']),
        ('share/' + package_name + '/world', ['world/maze.sdf']),
        ('share/' + package_name + '/map', ['map/maze.pgm']),
        ('share/' + package_name + '/map', ['map/maze.yaml']),
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
