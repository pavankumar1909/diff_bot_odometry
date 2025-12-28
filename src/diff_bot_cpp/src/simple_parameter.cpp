#include <rclcpp/rclcpp.hpp>
#include <rcl_interfaces/msg/set_parameters_result.hpp>
#include <stdint.h>
#include <string>
#include <vector>

using namespace std;
using std::placeholders::_1;

class SimpleParameterNode : public rclcpp::Node
{
 public:
   SimpleParameterNode():Node("simple_parameter")
   {
        this->declare_parameter<std::int64_t>("simple_int_param", 28);
        this->declare_parameter<std::string>("simple_string_param", "Hello, ROS2 Parameters!");

        param_callback_handle_ = this->add_on_set_parameters_callback(
            std::bind(&SimpleParameterNode::paramchangecallback, this, _1)
        );
   } 
   
   private:
     OnSetParametersCallbackHandle::SharedPtr param_callback_handle_;

     rcl_interfaces::msg::SetParametersResult paramchangecallback(
        const std::vector<rclcpp::Parameter> & parameters)
     {
        
        rcl_interfaces::msg::SetParametersResult result;

        for (const auto & param : parameters)
        {
            if(param.get_name()=="simple_int_param" && param.get_type()== rclcpp::ParameterType::PARAMETER_INTEGER)
            {
               RCLCPP_INFO_STREAM(get_logger(), "Parameter " << param.get_name() << "' has been changed to " << param.as_int() );  
               result.successful = true;
            }
            else if(param.get_name()=="simple_string_param" && param.get_type()== rclcpp::ParameterType::PARAMETER_STRING)
            {
              RCLCPP_INFO_STREAM(get_logger(), "Parameter " << param.get_name() << " has been changed to " << param.as_string());
              result.successful = true;
            }
            
        }

       
        return result;
     }
};


int main(int argc, char ** argv)
{
    rclcpp::init(argc, argv);
    auto node = make_shared<SimpleParameterNode>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}