from setuptools import setup

setup(
    py_modules = [],
    install_requires=[
        'Flask',
        'pytest',
        'Flask-Testing',
        'pydevd_pycharm',
        'environs',
        'PyYAML==5.4.1',
        'pika==1.1.0',
    ]
)
