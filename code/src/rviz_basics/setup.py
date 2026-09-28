from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'rviz_basics'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test', 'test.*']),
    data_files=[
        # Registers the package with the ament index so ros2 / RViz can find it.
        ('share/ament_index/resource_index/packages', [os.path.join('resource', package_name)]),
        (os.path.join('share', package_name), ['package.xml']),
        # Non-Python assets have to be listed here or they will not land in
        # install/ and FindPackageShare will not resolve them at launch time.
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    # colcon only selects its pytest runner when it can see a test dependency on
    # pytest; without this `colcon test` silently falls back to unittest and
    # collects nothing. (The older `tests_require=` spelling no longer works —
    # setuptools 72 removed it.)
    extras_require={'test': ['pytest']},
    zip_safe=True,
    maintainer='Robin Nagpal',
    maintainer_email='robinnagpal.tiet@gmail.com',
    description=(
        'Minimal ROS 2 + RViz2 example: a TF frame orbiting the origin '
        'with a marker attached to it.'
    ),
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            # Add one line per node: '<executable> = <package>.<module>:main'
            'marker_publisher = rviz_basics.marker_publisher:main',
        ],
    },
)
