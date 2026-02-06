#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from enum import Enum
import math

from sensor_msgs.msg import LaserScan
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import ColorRGBA
from geometry_msgs.msg import Twist


class State(Enum):
    FREE = 0
    WARNING = 1
    DANGER = 2


class ZoneObstacleAvoidance(Node):

    def __init__(self):
        super().__init__('zone_obstacle_avoidance')

        # ---------------- Parameters ----------------
        self.declare_parameter('warning_distance', 0.6)
        self.declare_parameter('danger_distance', 0.25)
        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('zones_topic', '/zones')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')

        self.warning_distance = self.get_parameter('warning_distance').value
        self.danger_distance = self.get_parameter('danger_distance').value
        self.scan_topic = self.get_parameter('scan_topic').value
        self.zones_topic = self.get_parameter('zones_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value

        # ---------------- ROS interfaces ----------------
        self.scan_sub = self.create_subscription(
            LaserScan, self.scan_topic, self.laser_callback, 10
        )

        self.zones_pub = self.create_publisher(
            MarkerArray, self.zones_topic, 10
        )

        self.cmd_vel_pub = self.create_publisher(
            Twist, self.cmd_vel_topic, 10
        )

        # ---------------- State ----------------
        self.zone_states = [State.FREE] * 6
        self.is_first_msg = True

        # ---------------- Visualization ----------------
        self.zones = MarkerArray()
        self.create_zone_markers()

        self.get_logger().info("6-zone obstacle avoidance with motion logic started")

    # =================================================
    # Visualization
    # =================================================
    def create_zone_markers(self):
        for zone in range(6):
            warn = Marker()
            warn.id = zone
            warn.type = Marker.CYLINDER
            warn.action = Marker.ADD
            warn.scale.x = self.warning_distance * 2
            warn.scale.y = self.warning_distance * 2
            warn.scale.z = 0.01
            warn.pose.position.z = 0.01
            warn.color = ColorRGBA(0.0, 1.0, 0.0, 0.3)
            self.set_zone_orientation(warn, zone)

            danger = Marker()
            danger.id = zone + 6
            danger.type = Marker.CYLINDER
            danger.action = Marker.ADD
            danger.scale.x = self.danger_distance * 2
            danger.scale.y = self.danger_distance * 2
            danger.scale.z = 0.01
            danger.pose.position.z = 0.02
            danger.color = ColorRGBA(1.0, 0.0, 0.0, 0.0)
            self.set_zone_orientation(danger, zone)

            self.zones.markers.extend([warn, danger])

    def set_zone_orientation(self, marker, zone_index):
        yaw = math.radians(zone_index * 60)
        marker.pose.orientation.z = math.sin(yaw / 2)
        marker.pose.orientation.w = math.cos(yaw / 2)

    # =================================================
    # Zone detection
    # =================================================
    def compute_zone_states(self, msg: LaserScan):
        self.zone_states = [State.FREE] * 6

        for i, r in enumerate(msg.ranges):
            if math.isinf(r):
                continue

            angle = msg.angle_min + i * msg.angle_increment
            angle_deg = math.degrees(angle)

            if angle_deg > 180:
                angle_deg -= 360
            if angle_deg < -180:
                angle_deg += 360

            if -30 <= angle_deg < 30:
                zone = 0
            elif 30 <= angle_deg < 90:
                zone = 1
            elif 90 <= angle_deg < 150:
                zone = 2
            elif angle_deg >= 150 or angle_deg < -150:
                zone = 3
            elif -150 <= angle_deg < -90:
                zone = 4
            elif -90 <= angle_deg < -30:
                zone = 5
            else:
                continue

            if r <= self.danger_distance:
                self.zone_states[zone] = State.DANGER
            elif r <= self.warning_distance:
                if self.zone_states[zone] != State.DANGER:
                    self.zone_states[zone] = State.WARNING

    def update_zone_colors(self):
        for i, state in enumerate(self.zone_states):
            warn = self.zones.markers[i]
            danger = self.zones.markers[i + 6]

            if state == State.FREE:
                warn.color = ColorRGBA(0.0, 1.0, 0.0, 0.3)
                danger.color = ColorRGBA(1.0, 0.0, 0.0, 0.0)
            elif state == State.WARNING:
                warn.color = ColorRGBA(1.0, 1.0, 0.0, 0.8)
                danger.color = ColorRGBA(1.0, 0.0, 0.0, 0.0)
            elif state == State.DANGER:
                warn.color = ColorRGBA(1.0, 1.0, 0.0, 0.8)
                danger.color = ColorRGBA(1.0, 0.0, 0.0, 1.0)

    # =================================================
    # Motion logic
    # =================================================
    def compute_cmd_vel(self):
        twist = Twist()

        front = self.zone_states[0]
        front_left = self.zone_states[2]
        front_right = self.zone_states[1]

        if front == State.DANGER:
            twist.linear.x = 0.0
            # turn toward freer side
            if front_left.value < front_right.value:
                twist.angular.z = 0.8
            else:
                twist.angular.z = -0.8

        elif front == State.WARNING:
            twist.linear.x = 0.12
            if front_left.value < front_right.value:
                twist.angular.z = 0.4
            else:
                twist.angular.z = -0.4

        elif front_left == State.DANGER:
            twist.linear.x = 0.1
            twist.angular.z = -0.6

        elif front_right == State.DANGER:
            twist.linear.x = 0.1
            twist.angular.z = 0.6

        else:
            twist.linear.x = 0.25
            twist.angular.z = 0.0

        return twist

    # =================================================
    # Callback
    # =================================================
    def laser_callback(self, msg: LaserScan):
        self.compute_zone_states(msg)
        self.update_zone_colors()

        cmd = self.compute_cmd_vel()
        self.cmd_vel_pub.publish(cmd)

        if self.is_first_msg:
            for m in self.zones.markers:
                m.header.frame_id = msg.header.frame_id
            self.is_first_msg = False

        self.zones_pub.publish(self.zones)


# =====================================================
def main():
    rclpy.init()
    node = ZoneObstacleAvoidance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
