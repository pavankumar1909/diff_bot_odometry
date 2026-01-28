import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    gazebo = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("diff_bot_description"),
            "launch",
            "gazebo.launch.py"
        ),
    )
    
    controller = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("diff_bot_controller"),
            "launch",
            "controller.launch.py"
        ),
        launch_arguments={
            "use_simple_controller": "False",
            "use_python": "False"
        }.items(),
    )
    
    joystick = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("diff_bot_controller"),
            "launch",
            "joystick_teleop.launch.py"
        ),
        launch_arguments={
            "use_sim_time": "True"
        }.items()
    )

    # teleop_keyboard = Node(
    #     package="teleop_twist_keyboard",
    #     executable="teleop_twist_keyboard",
    #     name="teleop_twist_keyboard",
    #     output="screen",
    #     prefix="xterm -e",     # IMPORTANT: opens a terminal for keyboard input
    #     parameters=[{
    #         "use_sim_time": True
    #     }],
    #     remappings=[
    #         ("/cmd_vel", "/diff_bot_controller/cmd_vel")
    #     ]
    # )
    
    return LaunchDescription([
        gazebo,
        controller,
        joystick
        #teleop_keyboard
    ])