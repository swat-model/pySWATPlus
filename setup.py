import setuptools



setuptools.setup(
    name = "PySWATPlus",
    packages = ['PySWATPlus'],   
    version = "0.0.1",
    license = 'GPL-3.0',
    description = " Running and calibrating default or custom SWAT+ projects with Python",
    author = "Joan Saló",
    author_email = "jsalo@icra.cat",
    url = "https://github.com/icra/pySWATPlus",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL-3.0",
        "Operating System :: OS Independent",
    ],
    package_dir = {"": "src"},
    packages = setuptools.find_packages(where="src"),
    python_requires = ">=3.6"
)