from setuptools import setup, find_packages

required_installs = ["wheel", "lscsoft-glue", "python-ligo-lw", "lalsuite"]

setup(
    name="spiir",
    version="0.0.1",
    packages=find_packages(),
    install_requires=required_installs,
    description="A Python package for the SPIIR search pipeline",
    author="Daniel Tang",
    author_email="daniel.tang@uwa.edu.au",
)
