from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    lateral_mod = LaunchConfiguration('lateral_mod')
    yaw_mod = LaunchConfiguration('yaw_mod')
    vertical_mod = LaunchConfiguration('vertical_mod')
    pitch_roll_mod = LaunchConfiguration('pitch_roll_mod')
    return LaunchDescription([
        DeclareLaunchArgument('lateral_mod', default_value=lateral_mod),
        DeclareLaunchArgument('yaw_mod', default_value=yaw_mod),
        DeclareLaunchArgument('vertical_mod', default_value=vertical_mod),
        DeclareLaunchArgument('pitch_roll_mod', default_value=pitch_roll_mod),
        Node(
            package='rov_ctrl_sys',
            executable='joy_to_motor',
            name='joy_to_motor',
            parameters=[{
                'lateral_mod': LaunchConfiguration('lateral_mod'),
                'yaw_mod': LaunchConfiguration('yaw_mod'),
                'vertical_mod': LaunchConfiguration('vertical_mod'),
                'pitch_roll_mod': LaunchConfiguration('pitch_roll_mod'),
            }]
        ),
        Node(
            package='joy',
            executable='joy_node',
            name='controller',
        ),
    ])
