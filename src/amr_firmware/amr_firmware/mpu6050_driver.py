#!/usr/bin/env python3
import rclpy
import smbus
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu

# -------- I2C Addresses --------
MPU_ADDR = 0x68
MAG_ADDR = 0x0D

# -------- MPU6050 Registers --------
PWR_MGMT = 0x6B
CONFIG   = 0x1A
ACCEL_XOUT = 0x3B
GYRO_XOUT  = 0x43

# -------- QMC5883L Registers --------
QMC_DATA_X    = 0x00
QMC_CONF_1    = 0x09
QMC_CONF_2    = 0x0A
QMC_SET_RESET = 0x0B


class IMUNode(Node):

    def __init__(self):
        super().__init__("imu_driver")

        self.bus = smbus.SMBus(1)
        self.init_mpu6050()
        self.init_qmc5883l()

        self.pub = self.create_publisher(
            Imu, "/imu/out", qos_profile_sensor_data
        )

        self.msg = Imu()
        self.msg.header.frame_id = "base_link"

        self.timer = self.create_timer(0.01, self.timer_cb)

    # -------- Initialization --------
    def init_mpu6050(self):
        self.bus.write_byte_data(MPU_ADDR, PWR_MGMT, 0x00)   # Wake up
        self.bus.write_byte_data(MPU_ADDR, CONFIG, 0x00)

    def init_qmc5883l(self):
        self.bus.write_byte_data(MAG_ADDR, QMC_SET_RESET, 0x01)
        self.bus.write_byte_data(MAG_ADDR, QMC_CONF_1, 0x1D)  # Continuous, 200Hz
        self.bus.write_byte_data(MAG_ADDR, QMC_CONF_2, 0x40)

    # -------- Timer --------
    def timer_cb(self):

        ax = self.read_word(MPU_ADDR, ACCEL_XOUT) / 16384.0
        ay = self.read_word(MPU_ADDR, ACCEL_XOUT + 2) / 16384.0
        az = self.read_word(MPU_ADDR, ACCEL_XOUT + 4) / 16384.0

        gx = self.read_word(MPU_ADDR, GYRO_XOUT) / 131.0
        gy = self.read_word(MPU_ADDR, GYRO_XOUT + 2) / 131.0
        gz = self.read_word(MPU_ADDR, GYRO_XOUT + 4) / 131.0

        self.msg.linear_acceleration.x = ax * 9.81
        self.msg.linear_acceleration.y = ay * 9.81
        self.msg.linear_acceleration.z = az * 9.81

        self.msg.angular_velocity.x = gx * 0.0174533
        self.msg.angular_velocity.y = gy * 0.0174533
        self.msg.angular_velocity.z = gz * 0.0174533

        self.msg.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(self.msg)

    # -------- I2C Helper --------
    def read_word(self, addr, reg):
        high = self.bus.read_byte_data(addr, reg)
        low  = self.bus.read_byte_data(addr, reg + 1)
        val = (high << 8) | low
        return val - 65536 if val > 32767 else val


def main():
    rclpy.init()
    node = IMUNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
