from setuptools import find_packages, setup

package_name = 'py_action'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='david',
    maintainer_email='smithd22@oregonstate.edu',
    description='Action tutorial',
    license='Apache License 2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'server = py_action.fibonacci_action_server:main',
            'client = py_action.fibonacci_action_client:main',
        ],
    },
)
