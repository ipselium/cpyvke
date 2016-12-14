from setuptools import setup
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
    packages=['cpyvke'],
    entry_points="""
    [console_scripts]
    cpyvke = cpyvke.cpyvke:main
    kd5 = cpyvke.kd5:main
    """,
    install_requires=["jupyter_client"],
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
