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
    display_node = Node(
        package='rov_ctrl_sys',
        executable='window',
        name='display',
        output='log',
        remappings=[
            ('image_raw','image_uncompressed'),
        ],
        arguments=[
            '--ros-args',
            '--log-level', 'display:=DEBUG',
        ],
    )

    return LaunchDescription([
        display_node,
        Node(
            package='rov_ctrl_sys',
            executable='keyboard_to_servo',
            name='keyboard_to_servo',
            output='log',
            arguments=[
                '--ros-args',
                '--log-level', 'display:=DEBUG',
            ],
        ),
        Node(
            package='image_transport',
            executable='republish',
            name='camera_uncompressor',
            remappings=[
                ('in/compressed', '/rov/image_raw/compressed'),
                ('out', '/ground/image_uncompressed'),
            ],
            arguments=[
                'compressed', 'raw', 
            ],
            output='log'
        ),
#         Node(
#             package='rov_ctrl_sys',
#             executable='keyboard_to_servo',
#             name='keyboard_to_servo',
#             output='log',
#         ),
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
