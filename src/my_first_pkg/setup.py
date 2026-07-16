from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'my_first_pkg'

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
    maintainer_email='min@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'publisher = my_first_pkg.publisher:main',
            'subscriber = my_first_pkg.subscriber:main',
            'add_two_ints_server = my_first_pkg.add_two_ints_server:main',
            'add_two_ints_client = my_first_pkg.add_two_ints_client:main',
            'move_robot_action_server = my_first_pkg.move_robot_action_server:main',
            'move_robot_action_client = my_first_pkg.move_robot_action_client:main',
            'parameter_demo = my_first_pkg.parameter_demo:main',
        ],
    },
)