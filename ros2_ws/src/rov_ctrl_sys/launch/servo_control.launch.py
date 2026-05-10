from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    port = LaunchConfiguration('port')

    return LaunchDescription([
        DeclareLaunchArgument('port', default_value=port),
        Node(
            package='rov_ctrl_sys',
            executable='motor_controller',
            name='servo_controller',
            output='log',  # still logs to ros log
            parameters=[{
                'port': LaunchConfiguration('port'),
            }],
            remappings=[
                ('motor_command','/ground/servo_command'),
                ('motor_feedback','servo_feedback'),
            ],
#             ros_arguments=['--log-level', 'debug'],
        ),
    ])
