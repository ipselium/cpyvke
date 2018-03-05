from setuptools import setup, find_packages

import sys


if sys.version_info < (2,7):
    raise NotImplementedError(
        "Sorry, you need at least Python 2.7 to use cpyvke.")

VERSION = '1.0'

__doc__ = """\
A Curses PYthon Variable and Kernel Explorer
"""


setup(
    name='cpyvke',
    version=VERSION,
    url='https://github.com/ipselium/cpyvke',
    author='Cyril Desjouy',
    author_email='ipselium@free.fr',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'kd5 = cpyvke.kd5:main',
            'cpyvke = cpyvke.cpyvke:main',
            'cpyvke-launch-ipython = cpyvke.launch:main',
        ],
    },
    install_requires=["jupyter_client", "ipykernel", "psutil", "numpy", "matplotlib"],
    license='BSD',
    description='A Kernel and variable explorer in Curses',
    long_description=__doc__,
    classifiers=[
        'Development Status :: Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
    ]
)
