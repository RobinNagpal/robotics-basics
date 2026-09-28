from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'camera_one_box'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test', 'test.*']),
    data_files=[
        ('share/ament_index/resource_index/packages', [os.path.join('resource', package_name)]),
        (os.path.join('share', package_name), ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.xacro')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.sdf')),
        (os.path.join('share', package_name, 'worlds', 'textures'), glob('worlds/textures/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    extras_require={'test': ['pytest']},
    zip_safe=True,
    maintainer='Robin Nagpal',
    maintainer_email='robinnagpal.tiet@gmail.com',
    description='A depth camera in Gazebo finds one box on a table and measures it.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'box_locator = camera_one_box.box_locator:main',
            'show_pixels = camera_one_box.show_pixels:main',
            'save_snapshot = camera_one_box.save_snapshot:main',
        ],
    },
)
