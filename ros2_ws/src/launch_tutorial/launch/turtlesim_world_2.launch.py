from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='sim',
            parameters=[PathJoinSubstitution([
                FindPackageShare('launch_tutorial'), 'config', 'turtlesim.yaml'])
            ],
        ),
    ])
