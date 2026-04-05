from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    SetEnvironmentVariable,
    EmitEvent,
    ExecuteProcess,
    LogInfo,
    RegisterEventHandler,
    TimerAction
)
from launch.conditions import IfCondition
from launch.event_handlers import (
    OnExecutionComplete,
    OnProcessExit,
    OnProcessIO,
    OnProcessStart,
    OnShutdown
)
from launch.events import Shutdown
from launch.substitutions import (
    EnvironmentVariable,
    FindExecutable,
    LaunchConfiguration,
    LocalSubstitution,
    PathJoinSubstitution,
    PythonExpression
)
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

def generate_launch_description():
    video_device = LaunchConfiguration('video_device')
    pixel_format = LaunchConfiguration('pixel_format')

    display_node = Node(
        package='rov_ctrl_sys',
        executable='window',
        name='display',
        output='log',
        arguments=[
            '--ros-args',
            '--log-level', 'display:=DEBUG',
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('video_device', default_value=video_device),
        DeclareLaunchArgument('pixel_format', default_value=pixel_format),
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='camera',
            output='log',
            parameters=[{
                'video_device': LaunchConfiguration('video_device'),
                'pixel_format': LaunchConfiguration('pixel_format'),
            }],
        ),
        display_node,
        RegisterEventHandler(
            OnProcessExit(
                target_action=display_node,
                on_exit=[
                    LogInfo(msg=('User closed the display window')),
                    EmitEvent(event=Shutdown(
                        reason='Display closed'))
                ]
            )
        ),
        RegisterEventHandler(
            OnShutdown(
                on_shutdown=[LogInfo(
                    msg=['Launch was asked to shutdown: ', LocalSubstitution('event.reason')]
                )]
            )
        ),
    ])
