from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    launch_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'launch'])

    return LaunchDescription([
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'gamepad.launch.py']),
        ),
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'display.launch.py']),
        ),
    ])
