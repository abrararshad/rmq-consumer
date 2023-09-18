from setuptools import setup

setup(
    py_modules = [],
    install_requires=[
        'Flask',
        'pytest',
        'Flask-Testing',
        'pydevd_pycharm',
        'environs',
        'pika==1.1.0',
    ]
)
