from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'ros_basics'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test', 'test.*']),
    data_files=[
        ('share/ament_index/resource_index/packages', [os.path.join('resource', package_name)]),
        (os.path.join('share', package_name), ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),
    ],
    install_requires=['setuptools'],
    extras_require={'test': ['pytest']},
    zip_safe=True,
    maintainer='Robin Nagpal',
    maintainer_email='robinnagpal.tiet@gmail.com',
    description='One small program for each thing ROS is used for.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'basics_node = ros_basics.nodes:main',
            'basics_publisher = ros_basics.publisher:main',
            'basics_subscriber = ros_basics.subscriber:main',
            'basics_parameters = ros_basics.parameters:main',
            'basics_service_server = ros_basics.service_server:main',
            'basics_service_client = ros_basics.service_client:main',
            'basics_action_server = ros_basics.action_server:main',
            'basics_action_client = ros_basics.action_client:main',
            'basics_frames = ros_basics.frames:main',
        ],
    },
)
