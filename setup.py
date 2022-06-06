from setuptools import setup, find_packages

setup(
    name="spiir-utils",
    version="0.0.1",
    packages=find_packages(),
    package_dir={"": "src"},
    install_requires=["wheel", "lscsoft-glue", "python-ligo-lw", "lalsuite"],
    description="A Python utilities package for the SPIIR search pipeline",
    author="Daniel Tang",
    author_email="daniel.tang@uwa.edu.au",
)
