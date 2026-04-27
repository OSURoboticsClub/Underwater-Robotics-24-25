from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    return LaunchDescription([
        DeclareLaunchArgument('lateral_mod', default_value='0.75'),
        DeclareLaunchArgument('yaw_mod', default_value='0.75'),
        DeclareLaunchArgument('vertical_mod', default_value='0.75'),
        DeclareLaunchArgument('pitch_roll_mod', default_value='0.75'),
        DeclareLaunchArgument('allow_rolling', default_value='True'),
        Node(
            package='rov_ctrl_sys',
            executable='joy_to_motor',
            name='joy_to_motor',
            output='log',
            parameters=[{
                'lateral_mod': LaunchConfiguration('lateral_mod'),
                'yaw_mod': LaunchConfiguration('yaw_mod'),
                'vertical_mod': LaunchConfiguration('vertical_mod'),
                'pitch_roll_mod': LaunchConfiguration('pitch_roll_mod'),
                'allow_rolling': LaunchConfiguration('allow_rolling'),
            }],
#             ros_arguments=['--log-level', 'debug'],
        ),
        Node(
            package='rov_ctrl_sys',
            executable='joy_to_servo',
            name='joy_to_servo',
            output='log',
#             ros_arguments=['--log-level', 'debug'],
        ),
        Node(
            package='joy',
            executable='joy_node',
            name='gamepad',
        ),
    ])
