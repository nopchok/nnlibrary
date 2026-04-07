import setuptools

import os

thelibFolder = os.path.dirname(os.path.realpath(__file__))
requirementPath = thelibFolder + '/requirements.txt'
install_requires = []

if os.path.isfile(requirementPath):
    with open(requirementPath) as f:
        install_requires = f.read().splitlines()

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nnlibrary",
    version="0.0.1",
    author="nnlibrary",
    author_email="c.noppawawt@gmail.com",
    description="nnlibrary",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nopchok/nnlibrary",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=install_requires
)
