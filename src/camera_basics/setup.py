from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'camera_basics'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test', 'test.*']),
    data_files=[
        ('share/ament_index/resource_index/packages', [os.path.join('resource', package_name)]),
        (os.path.join('share', package_name), ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    extras_require={'test': ['pytest']},
    zip_safe=True,
    maintainer='Robin Nagpal',
    maintainer_email='robinnagpal.tiet@gmail.com',
    description='How a camera turns a scene into pictures, and pictures back into points.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            # The walkthrough is meant to be read as much as run.
            'camera_walkthrough = camera_basics.camera:main',
            'camera_publisher = camera_basics.camera_publisher:main',
        ],
    },
)
