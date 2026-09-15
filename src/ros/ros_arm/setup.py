from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'ros_arm'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test', 'test.*']),
    data_files=[
        ('share/ament_index/resource_index/packages', [os.path.join('resource', package_name)]),
        (os.path.join('share', package_name), ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
    ],
    install_requires=['setuptools'],
    extras_require={'test': ['pytest']},
    zip_safe=True,
    maintainer='Robin Nagpal',
    maintainer_email='robinnagpal.tiet@gmail.com',
    description='The simplest arm: two joints, moved by publishing joint positions.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'arm_mover = ros_arm.arm_mover:main',
            'distance_sensor = ros_arm.distance_sensor:main',
        ],
    },
)
