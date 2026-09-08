from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'arm_transforms'

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
    description='Position, frames and transforms, worked through on a two-joint robot arm.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            # The numbered steps are meant to be read and run in order.
            'arm_step1_positions = arm_transforms.step1_positions:main',
            'arm_step2_frames = arm_transforms.step2_frames:main',
            'arm_step3_chain = arm_transforms.step3_chain:main',
            'arm_step4_broadcast = arm_transforms.step4_broadcast:main',
            'arm_step5_lookup = arm_transforms.step5_lookup:main',
        ],
    },
)
