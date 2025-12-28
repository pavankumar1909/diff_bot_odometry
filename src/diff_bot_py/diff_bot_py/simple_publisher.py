import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SimplePublisher(Node):
    def __init__(self):
        super().__init__('simple_publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)

        self.counter_ = 0
        self.frequency_ = 1.0  # Frequency in Hz
        self.get_logger().info('Publishing at %d Hz' % self.frequency_)
        self.timer = self.create_timer(1.0 / self.frequency_, self.timer_callback)

    def timer_callback(self):
        msg = String()
        msg.data = 'Hello, ROS 2! count:%d' % self.counter_
        self.publisher_.publish(msg)
        self.counter_ += 1
        self.get_logger().info(f'Publishing: "{msg.data}"')



def main():
    rclpy.init()
    simple_publisher = SimplePublisher()
    rclpy.spin(simple_publisher)
    simple_publisher.destroy_node()
    rclpy.shutdown()  

if __name__ == '__main__':
    main()          