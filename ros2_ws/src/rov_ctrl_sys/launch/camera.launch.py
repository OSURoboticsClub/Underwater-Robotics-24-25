from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    params_dir = PathJoinSubstitution([FindPackageShare('rov_ctrl_sys'), 'config'])

    return LaunchDescription([
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='camera',
            output='log',
            parameters=[
                PathJoinSubstitution([params_dir, 'camera.yaml']),
                PathJoinSubstitution([params_dir, 'camera_shared.yaml']),
            ],
#             ros_arguments=['--params-file', PathJoinSubstitution([params_dir, 'camera.yaml'])],
        ),
    ])
