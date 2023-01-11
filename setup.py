"""Setup file for mkgendocs"""

from setuptools import setup

setup(
    name='mkgendocs',
    version='0.9.2',
    packages=['mkgendocs'],
    url='https://github.com/davidenunes/mkgendocs',
    description='mkgendocs is a Python tool to automate the generation of documentation from docstrings in markdown',
    include_package_data=True,
    install_requires=[
        "six",
        "pyyaml",
        "astor",
        "mako"
    ],
    classifiers=[
        'Environment :: Console',
        'Operating System :: OS Independent',
        "Programming Language :: Python",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        'Programming Language :: Python :: 3 :: Only',
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        'Topic :: Documentation',
        'Topic :: Text Processing'
    ],
    entry_points="""
        [console_scripts]
        gendocs=mkgendocs.gendocs:main
    """
)
