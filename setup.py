
from setuptools import setup, find_packages
import sys, os
from iaas.core import VERSION

setup(
    name='iaas',
    version=VERSION,
    description="IaaS",
    long_description="IaaS",
    classifiers=[],
    keywords='',
    author='Christo De Lange',
    author_email='christo_de_lange@homedepot.com',
    url='',
    license='GPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    test_suite='nose.collector',
    install_requires=[
        ### Required to build documentation
        # "Sphinx >= 1.0",
        ### Required for testing
        # "nose",
        # "coverage",
        ### Required to function
        'cement',
        'Jinja2',
        'pystache',
        'tabulate',
        'pyYaml',
        'requests',
        ],
    setup_requires=[],
    entry_points={
        'console_scripts': [
            'iaas = iaas.cli.main:main'
        ]
    },
    namespace_packages=[],
    )
