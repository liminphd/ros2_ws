from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'robot_sensors'


setup(
    name=package_name,
    version='0.1.0',
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
            os.path.join(
                'share',
                package_name,
                'launch',
            ),
            glob('launch/*.launch.py'),
        ),
        (
            os.path.join(
                'share',
                package_name,
                'config',
            ),
            glob('config/*.yaml'),
        ),
        (
            os.path.join(
                'share',
                package_name,
                'config',
                'velodyne',
            ),
            glob('config/velodyne/*.yaml'),
        ),
        (
            os.path.join(
                'share',
                package_name,
                'config',
                'sbg',
            ),
            glob('config/sbg/*.yaml'),
        ),
        (
            os.path.join(
                'share',
                package_name,
                'config',
                'oak',
            ),
            glob('config/oak/*.yaml'),
        ),
    ],

    install_requires=['setuptools'],
    zip_safe=True,

    maintainer='Min Li',
    maintainer_email='liminphd@gmail.com',

    description='Unified sensor launch and configuration package',

    license='Apache-2.0',

    tests_require=['pytest'],

    entry_points={
        'console_scripts': [],
    },
)