from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch.conditions import UnlessCondition, IfCondition

def generate_launch_description():
    params_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'config'])

    return LaunchDescription([
        DeclareLaunchArgument('allow_rolling', default_value='True'),

        DeclareLaunchArgument('lateral_mod', default_value='0.75'),
        DeclareLaunchArgument('vertical_mod', default_value='0.75'),
        DeclareLaunchArgument('turn_mod', default_value='0.75'),
        DeclareLaunchArgument('pitch_roll_mod', default_value='0.75'),

        DeclareLaunchArgument('lateral_cap', default_value='0.75'),
        DeclareLaunchArgument('vertical_cap', default_value='0.75'),
        Node(
            package='rov_ctrl_sys',
            executable='joy_to_motor',
            name='joy_to_motor',
            output='log',
            parameters=[{
                'lateral_cap': LaunchConfiguration('lateral_cap'),
                'vertical_cap': LaunchConfiguration('vertical_cap'),
                'allow_rolling': LaunchConfiguration('allow_rolling'),
            }],
#             ros_arguments=['--log-level', 'debug'],
            ros_arguments=['--params-file', PathJoinSubstitution([params_dir, 'motors.yaml'])],
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
