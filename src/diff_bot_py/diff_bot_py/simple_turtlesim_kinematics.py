import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
import math

class TurtlesimKinematics(Node):
    def __init__(self):
        super().__init__('simple_turtlesim_kinematics')
        self.turtle1_pose_subscriber = self.create_subscription(Pose, '/turtle1/pose', self.turtle1_pose_callback, 10)
        self.turtle2_pose_subscriber = self.create_subscription(Pose, '/turtle2/pose', self.turtle2_pose_callback, 10)

        self.last_turtle1_pose = Pose()
        self.last_turtle2_pose = Pose()
       # self.get_logger().info('Simple Turtlesim Kinematics Node has been started.')

    def turtle1_pose_callback(self, msg):
        self.last_turtle1_pose = msg
      #  self.get_logger().info(f'Turtle1 Pose - x: {msg.x}, y: {msg.y}, theta: {msg.theta}')    

    def turtle2_pose_callback(self, msg):
        self.last_turtle2_pose = msg
        Tx=self.last_turtle2_pose.x - self.last_turtle1_pose.x
        Ty=self.last_turtle2_pose.y - self.last_turtle1_pose.y

        theta_rad = self.last_turtle2_pose.theta - self.last_turtle1_pose.theta
        theta_deg = 180 * theta_rad / 3.14
        self.get_logger().info("""\n
                      Translation Vector turtle1 -> turtle2\n
                      Tx: %f\n
                      Ty: %f\n
                      Rotation Matrix turtle1 -> turtle2\n 
                      theta (rad): %f\n
                      theta (deg): %f\n
                      |R11   R12|:  |%f %f|\n
                      |R21   R22|   |%f %f|\n""" %
                      (
                        Tx, Ty, theta_rad, theta_deg,
                        math.cos(theta_rad), -math.sin(theta_rad),
                        math.sin(theta_rad), math.cos(theta_rad)
                      )
                    )

       # self.get_logger().info(f'Translation Vector turtle1 -> turtle2 - Tx: {Tx}, Ty: {Ty}')


def main():
    rclpy.init()
    node = TurtlesimKinematics()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
