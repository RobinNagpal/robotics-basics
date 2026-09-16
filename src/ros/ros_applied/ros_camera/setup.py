from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'ros_camera'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test', 'test.*']),
    data_files=[
        ('share/ament_index/resource_index/packages', [os.path.join('resource', package_name)]),
        (os.path.join('share', package_name), ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    extras_require={'test': ['pytest']},
    zip_safe=True,
    maintainer='Robin Nagpal',
    maintainer_email='robinnagpal.tiet@gmail.com',
    description='The two simplest camera programs: one publishes pictures, one receives them.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'camera_publisher = ros_camera.camera_publisher:main',
            'camera_subscriber = ros_camera.camera_subscriber:main',
        ],
    },
)
