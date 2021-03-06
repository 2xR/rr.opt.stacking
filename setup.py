from setuptools import setup, find_packages
import pkgutil

import sys
import os

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, "src")
sys.path.insert(0, src)

with open("README.rst", "rt") as readme_file:
    readme = readme_file.read()

setup(
    name="rr.opt.stacking",
    version=pkgutil.get_data("rr.opt.stacking", "VERSION").decode("utf-8").strip(),
    description="Stacking Problem solvers.",
    long_description=readme,
    url="https://github.com/2xR/rr.opt.stacking",
    author="Rui Jorge Rei",
    author_email="rui.jorge.rei@googlemail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Operating System :: OS Independent",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"": ["LICENSE", "VERSION"]},
    install_requires=[
        "future~=0.15.2",
        # "rr.opt.mcts.basic",  # uncomment when pushed to PyPI
    ],
)
