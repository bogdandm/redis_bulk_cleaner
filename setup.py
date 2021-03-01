#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'Click>=7.0',
    'redis>=3.0',
    'tqdm>=4.30.0',
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Bogdan Kalashnikov",
    author_email='bogdan.dm@gmail.com',
    python_requires='>=3.5',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description=" ",
    entry_points={
        'console_scripts': [
            'redis_bulk_cleaner=redis_bulk_cleaner.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='redis_bulk_cleaner',
    name='redis_bulk_cleaner',
    packages=find_packages(include=['redis_bulk_cleaner', 'redis_bulk_cleaner.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/bogdandm/redis_bulk_cleaner',
    version='0.1.5',
    zip_safe=False,
)
