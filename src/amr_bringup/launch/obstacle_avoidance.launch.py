import os
import yaml
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    hardware_interface = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("amr_firmware"),
            "launch",
            "hardware_interface.launch.py"
        ),
    )
    
    controller = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("amr_controller"),
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
            get_package_share_directory("amr_controller"),
            "launch",
            "joystick_teleop.launch.py"
        ),
        launch_arguments={
            "use_sim_time": "False"
        }.items()
    )

    
    # ✅ YAML file path
    rplidar_params = os.path.join(
        get_package_share_directory("amr_bringup"),
        "config",
        "rplidar_a1.yaml"
    )

    # ✅ Correct Node definition
    rplidar_node = Node(
    package="rplidar_ros",
    executable="rplidar_composition",
    name="rplidar_node",
    output="screen",
    parameters=[{
            'serial_port': '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0',
            'frame_id': 'laser_link',
            'angle_compensate': True,
            'scan_mode': 'Standard',
        }]
    )
#   {
#      'serial_port': '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0',
#      'frame_id': 'laser_link',
#      'angle_compensate': True,
#      'scan_mode': 'Standard'
#         }

    avoid_obstacles_node = Node(
        package="amr_utils",
        executable="avoid_obstacles.py"    
    )
  
    return LaunchDescription([
        hardware_interface,
        controller,
        joystick,
        rplidar_node,
        avoid_obstacles_node
    ])