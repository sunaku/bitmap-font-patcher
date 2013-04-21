from setuptools import setup

setup(
    name='bitmap-font-patcher',
    version='alpha',
    description='Patches bitmap fonts for powerline',
    scripts=[
        'fontpatcher.py',
    ],
    keywords='',
    install_requires=[
        'bdflib',
        'pil',
        'fontforge',
    ],
)
