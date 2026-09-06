from setuptools import find_packages, setup

package_name = 'farmng_bridge'

setup(
    name=package_name,
    version='0.0.1',
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
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='min',
    maintainer_email='liminphd@gmail.com',
    description='ROS 2 bridge for Farm-ng native motion estimation and global pose.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'farmng_bridge = farmng_bridge.farmng_bridge_node:main',
        ],
    },
)
