from setuptools import setup, find_packages


setup(
    name='votronic-read',
    version='0.1.0',
    description='read displayport of Votronic MP430 Duo Digital Solar Regulator',
    long_description=open("README.md").read(),
    url='',
    author='Daniel Hiepler',
    author_email='d-votronic@coderdu.de',
    license='unlicense',
    keywords='solar serial json',
    py_modules=['votronic'],
    install_requires=[
        'click',
        'pyserial-asyncio'
    ],
    #packages=find_packages(exclude=['tests*']),
    entry_points={
        'console_scripts': [
            'votronic=votronic.cat:read_votronic',
        ]
    }
)
