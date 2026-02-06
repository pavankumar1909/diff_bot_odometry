#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from enum import Enum
import math
import time

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class State(Enum):
    FREE = 0
    WARNING = 1
    DANGER = 2


class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')

        # Parameters
        self.declare_parameter('warning_distance', 0.6)
        self.declare_parameter('danger_distance', 0.2)
        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')

        self.warning_distance = self.get_parameter('warning_distance').value
        self.danger_distance = self.get_parameter('danger_distance').value
        self.scan_topic = self.get_parameter('scan_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value

        # ROS interfaces
        self.scan_sub = self.create_subscription(
            LaserScan, self.scan_topic, self.laser_callback, 10
        )
        self.cmd_vel_pub = self.create_publisher(
            Twist, self.cmd_vel_topic, 10
        )

        # State
        self.state = State.FREE
        self.prev_state = State.FREE
        self.danger_start_time = None

        self.get_logger().info("Obstacle avoidance node started")

    # -----------------------------------------------------
    # Helper: find free direction using LaserScan
    # -----------------------------------------------------
    def get_free_direction(self, msg: LaserScan):
        left_min = float('inf')
        right_min = float('inf')

        for i, r in enumerate(msg.ranges):
            if math.isinf(r):
                continue

            angle = msg.angle_min + i * msg.angle_increment

            # LEFT: +30° to +90°
            if math.radians(30) < angle < math.radians(90):
                left_min = min(left_min, r)

            # RIGHT: -90° to -30°
            elif -math.radians(90) < angle < -math.radians(30):
                right_min = min(right_min, r)

        if left_min > right_min:
            return "LEFT"
        elif right_min > left_min:
            return "RIGHT"
        else:
            return None

    # -----------------------------------------------------
    # Laser callback
    # -----------------------------------------------------
    def laser_callback(self, msg: LaserScan):
        # --------- State detection ----------
        self.state = State.FREE

        for r in msg.ranges:
            if not math.isinf(r) and r <= self.warning_distance:
                self.state = State.WARNING
                if r <= self.danger_distance:
                    self.state = State.DANGER
                    break

        twist = Twist()

        # --------- State actions ----------
        if self.state == State.FREE:
            twist.linear.x = 0.25
            twist.angular.z = 0.0
            self.danger_start_time = None

        elif self.state == State.WARNING:
            direction = self.get_free_direction(msg)

            twist.linear.x = 0.12
            if direction == "LEFT":
                twist.angular.z = 0.6
            elif direction == "RIGHT":
                twist.angular.z = -0.6
            else:
                twist.angular.z = 0.0

            self.danger_start_time = None

        elif self.state == State.DANGER:
            twist.linear.x = 0.0
            twist.angular.z = 0.0

            if self.danger_start_time is None:
                self.danger_start_time = time.time()
                self.get_logger().warn("DANGER! Stopping for 10 seconds")

            elapsed = time.time() - self.danger_start_time

            if elapsed > 10.0:
                direction = self.get_free_direction(msg)
                if direction == "LEFT":
                    twist.angular.z = 0.8
                elif direction == "RIGHT":
                    twist.angular.z = -0.8

        # --------- Publish ----------
        self.cmd_vel_pub.publish(twist)

        if self.state != self.prev_state:
            self.get_logger().info(
                f"State changed: {self.prev_state.name} → {self.state.name}"
            )
            self.prev_state = self.state


def main():
    rclpy.init()
    node = ObstacleAvoidance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
