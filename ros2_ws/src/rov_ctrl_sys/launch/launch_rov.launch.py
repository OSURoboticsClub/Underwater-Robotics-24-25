from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    launch_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'launch'])

    return LaunchDescription([
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'rov_movement.launch.py']),
            launch_arguments={
                    'lateral_mod': '1.0',
                    'yaw_mod': '1.0',
                    'vertical_mod': '1.0',
                    'pitch_roll_mod': '1.0',
            }.items()
        ),
    ])
