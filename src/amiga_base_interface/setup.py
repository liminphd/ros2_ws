from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'amiga_base_interface'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        (
            'share/' + package_name,
            ['package.xml'],
        ),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py'),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='min',
    maintainer_email='liminphd@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'udp_motion_receiver = amiga_base_interface.udp_motion_receiver:main',
            'udp_motor_receiver = amiga_base_interface.udp_motor_receiver:main',
            'wheel_odometry = amiga_base_interface.wheel_odometry:main',
        ],
    },
)
