from setuptools import find_packages, setup

package_name = 'diff_bot_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pavan',
    maintainer_email='pavankumarangajala09@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'simple_publisher = diff_bot_py.simple_publisher:main',
            'simple_subscriber = diff_bot_py.simple_subscriber:main',
            'simple_parameter = diff_bot_py.simple_parameter:main',
            'simple_turtlesim_kinematics = diff_bot_py.simple_turtlesim_kinematics:main', 
            'simple_tf_kinematics = diff_bot_py.simple_tf_kinematics:main',
            'simple_service_server = diff_bot_py.simple_service_server:main',
        ],
    },
)
