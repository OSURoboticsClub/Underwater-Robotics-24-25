from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, GroupAction
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import PushRosNamespace
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    launch_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'launch'])

    return LaunchDescription([
        GroupAction([
            PushRosNamespace('rov'),
            IncludeLaunchDescription(
                PathJoinSubstitution([launch_dir, 'motor_control.launch.py']),
                launch_arguments={
                    'port': '/dev/esp1',
                }.items()
            ),
            IncludeLaunchDescription(
                PathJoinSubstitution([launch_dir, 'servo_control.launch.py']),
                launch_arguments={
                    'port': '/dev/esp2',
                }.items()
            ),
            IncludeLaunchDescription(
                PathJoinSubstitution([launch_dir, 'camera.launch.py']),
            ),
        ]),
    ])
