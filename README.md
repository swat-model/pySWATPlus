# pySWATPlus


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14889319.svg)](https://doi.org/10.5281/zenodo.14889319)
![PyPI - Version](https://img.shields.io/pypi/v/pySWATPlus)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pySWATPlus)
![PyPI - Status](https://img.shields.io/pypi/status/pySWATPlus)

[![flake8](https://github.com/swat-model/pySWATPlus/actions/workflows/linting.yml/badge.svg)](https://github.com/swat-model/pySWATPlus/actions/workflows/linting.yml)
[![mypy](https://github.com/swat-model/pySWATPlus/actions/workflows/typing.yml/badge.svg)](https://github.com/swat-model/pySWATPlus/actions/workflows/typing.yml)
[![pytest](https://github.com/swat-model/pySWATPlus/actions/workflows/testing.yml/badge.svg)](https://github.com/swat-model/pySWATPlus/actions/workflows/testing.yml)
[![codecov](https://codecov.io/gh/debpal/pySWATPlus/graph/badge.svg?token=0XJ89FRID9)](https://codecov.io/gh/debpal/pySWATPlus)

![GitHub last commit](https://img.shields.io/github/last-commit/swat-model/pySWATPlus)
![GitHub commit activity](https://img.shields.io/github/commit-activity/t/swat-model/pySWATPlus)
![GitHub Repo stars](https://img.shields.io/github/stars/swat-model/pySWATPlus)
![GitHub forks](https://img.shields.io/github/forks/swat-model/pySWATPlus)
![GitHub Created At](https://img.shields.io/github/created-at/swat-model/pySWATPlus)

![Read the Docs](https://img.shields.io/readthedocs/pySWATPlus)
![Pepy Total Downloads](https://img.shields.io/pepy/dt/pySWATPLus)
![PyPI - License](https://img.shields.io/pypi/l/pySWATPlus)


## 📦 About

`pySWATPlus` is an open-source Python package developed and maintained by [ICRA](https://icra.cat/).
It provides a programmatic interface to the [SWAT+](https://swat.tamu.edu/software/plus/) model, allowing users to run simulations, modify input files, and streamline custom experimentation through the model’s `TxtInOut` folder.


## ✨ Key Features

- Navigate and read files in the SWAT+ `TxtInOut` folder.
- Modify input parameters and save the updated files.
- Run SWAT+ simulations either in the main `TxtInOut` folder or in a user-specified directory.
- Perform sensitivity analysis on model parameters using the [SALib](https://github.com/SALib/SALib) Python package, with support for parallel computation.



## 📥 Install pySWATPlus

To install from PyPI repository:

```bash
pip install pySWATPlus
```

To install the latest development version from GitHub:

```bash
pip install git+https://github.com/swat-model/pySWATPlus.git
```

To install from source in editable mode within your desired `conda` environment:

```bash
# Activate your Conda environment
conda activate <environment_name>

# Install required tools and clone the repository
pip install build
cd C:\Users\Username\Folder  # Replace with your actual path
git clone https://github.com/swat-model/pySWATPlus.git
cd pySWATPlus

# Build the package
python -m build

# Install in editable mode
pip install --editable .
```

## ✅ Verify Installation

The installation is successful if no error is raised when importing the module using the following command:

```python
import pySWATPlus
```

## 📚 Documentation

For a guide to setting up first SWAT+ project and other functionalities with examples,
refere to the [pySWATPlus documentation](https://pyswatplus.readthedocs.io/en/latest/).



## ⚠️ Legacy Version Notice

Version 1.x includes breaking changes, including the `SWATProblem` and `SWATProblemMultimodel` classes have been removed. Updated tutorials for calibration analysis are coming soon.

- To get the old 0.x version from the PyPI repository:

```bash
pip install pySWATPlus==0.2.20
```

- [Access the source code of the 0.x version](https://github.com/swat-model/pySWATPlus/tree/v0.x)


## 📖 Citation

If you use `pySWATPlus` in your research, please cite it using the following **concept DOI**, which always points to the latest version:

```bibtex
@software{joan_salo_pyswatplus_latest,
  author       = {Joan Saló and
                  Debasish Pal and
                  Oliu Llorente},
  title        = {swat-model/pySWATPlus},
  year         = 2025,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.14889319},
  url          = {https://doi.org/10.5281/zenodo.14889319},
  note         = {This DOI always points to the latest version of pySWATPlus.},
}
```


To cite a specific version:

- Visit the [Zenodo project page](https://doi.org/10.5281/zenodo.14889319).
- Select the specific version you used (e.g., `v1.0.1`).
- Copy the appropriate citation format (BibTeX, APA, etc.).


