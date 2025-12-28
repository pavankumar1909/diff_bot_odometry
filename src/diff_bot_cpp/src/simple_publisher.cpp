#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <chrono>


using namespace std::chrono_literals;

class SimplePublisher : public rclcpp::Node
{
  public:

     SimplePublisher(): Node("simple_publisher")
     {
       publisher_ = this->create_publisher<std_msgs::msg::String>("topic", 10);
       timer_ = this->create_wall_timer(
         std::chrono::seconds(1),
         std::bind(&SimplePublisher::timerCallback, this)
        
        );
    }
      
     private:
        unsigned int counter_;
        
        rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
        rclcpp::TimerBase::SharedPtr timer_;
         
        void timerCallback()
        {
        auto message = std_msgs::msg::String();
        message.data = "Hello, ROS2!";
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
        publisher_->publish(message);
        }
};

int main (int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<SimplePublisher>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}