from setuptools import setup

package_name = 'diff_bot_firmware'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Pavan',
    maintainer_email='pavan@example.com',
    description='MPU6050 IMU driver for differential robot firmware',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mpu6050_driver = diff_bot_firmware.mpu6050_driver:main',
            'serial_receiver = diff_bot_firmware.serial_receiver:main',
            'serial_transmitter = diff_bot_firmware.serial_transmitter:main'
        ],
    },
)
