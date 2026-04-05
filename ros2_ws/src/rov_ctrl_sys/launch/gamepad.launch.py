from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    return LaunchDescription([
        DeclareLaunchArgument('lateral_mod', default_value='1.0'),
        DeclareLaunchArgument('yaw_mod', default_value='1.0'),
        DeclareLaunchArgument('vertical_mod', default_value='1.0'),
        DeclareLaunchArgument('pitch_roll_mod', default_value='1.0'),
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
            }],
            arguments=[
                '--ros-args',
                '--log-level', 'joy_to_motor:=DEBUG',
            ],
        ),
#         Node(
#             package='rov_ctrl_sys',
#             executable='joy_to_servo',
#             name='joy_to_servo',
#             output='log',
#         ),
        Node(
            package='joy',
            executable='joy_node',
            name='gamepad',
        ),
    ])
