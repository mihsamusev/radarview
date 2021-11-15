from distutils.core import setup
from setuptools import find_packages

setup(
    name="radarview",
    packages=find_packages(),
    version="0.0.1",
    license="MIT",
    description="Python project to extract and preview tracks from SmartMicro radar",
    author="Mihhail Samusev",
    url="https://github.com/radarview",
    install_requires = open("requirements.txt", "r").readlines(), 
    keywords=["radar", "traffic"]
)