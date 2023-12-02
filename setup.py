import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "pySWATPlus",
    packages = ['pySWATPlus'],   # Chose the same as "name"
    version = "0.0.7",
    author = "Joan Saló",
    author_email = "jsalo@icra.cat",
    description = "Running and calibrating default or custom SWAT+ projects with Python",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    license = 'GPL-3.0',
    url = "https://github.com/icra/pySWATPlus",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires = ">=3.6"
)