from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    launch_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'launch'])

    return LaunchDescription([
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'motor_control.launch.py']),
            launch_arguments={
                'port': '/dev/ttyUSB0',
            }.items()
        ),
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'servo_control.launch.py']),
            launch_arguments={
                'port': '/dev/ttyUSB0',
            }.items()
        ),
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'camera.launch.py']),
            launch_arguments={
                    'video_device': '/dev/main_camera',
            }.items()
        ),
    ])
