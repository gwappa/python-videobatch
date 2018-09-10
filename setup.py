import setuptools
from videobatch import VERSION_STR

setuptools.setup(
    name='videobatch',
    version=VERSION_STR,
    description='a toolkit for frame-by-frame conversion of videos in batch',
    url='https://github.com/gwappa/python-videobatch',
    author='Keisuke Sehara',
    author_email='keisuke.sehara@gmail.com',
    license='MIT',
    install_requires=[
        'numpy>=1.3',
        'scipy>=0.7',
        'matplotlib>=2.0',
        'sk-video>=1.1'
        ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        ],
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': ['videobatch=videobatch']
    }
)

