# pySWATPlus


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14889319.svg)](https://doi.org/10.5281/zenodo.14889319)

![PyPI - Version](https://img.shields.io/pypi/v/pySWATPlus)
![GitHub Release Date](https://img.shields.io/github/release-date/swat-model/pySWATPlus?display_date=published_at)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pySWATPlus)
![PyPI - Status](https://img.shields.io/pypi/status/pySWATPlus)
![PyPI - Format](https://img.shields.io/pypi/format/pySWATPlus)


![GitHub last commit](https://img.shields.io/github/last-commit/swat-model/pySWATPlus)
![GitHub commit activity](https://img.shields.io/github/commit-activity/t/swat-model/pySWATPlus)


[![docs](https://github.com/swat-model/pySWATPlus/actions/workflows/documenting.yml/badge.svg)](https://github.com/swat-model/pySWATPlus/actions/workflows/documenting.yml)
[![flake8](https://github.com/swat-model/pySWATPlus/actions/workflows/linting.yml/badge.svg)](https://github.com/swat-model/pySWATPlus/actions/workflows/linting.yml)
[![mypy](https://github.com/swat-model/pySWATPlus/actions/workflows/typing.yml/badge.svg)](https://github.com/swat-model/pySWATPlus/actions/workflows/typing.yml)
[![pytest](https://github.com/swat-model/pySWATPlus/actions/workflows/testing.yml/badge.svg)](https://github.com/swat-model/pySWATPlus/actions/workflows/testing.yml)
[![pytest](https://github.com/swat-model/pySWATPlus/actions/workflows/building.yml/badge.svg)](https://github.com/swat-model/pySWATPlus/actions/workflows/building.yml)
![Codecov](https://img.shields.io/codecov/c/github/debpal/pySWATPlus)

![GitHub Repo stars](https://img.shields.io/github/stars/swat-model/pySWATPlus)
![GitHub forks](https://img.shields.io/github/forks/swat-model/pySWATPlus)
![GitHub Created At](https://img.shields.io/github/created-at/swat-model/pySWATPlus)

![Pepy Total Downloads](https://img.shields.io/pepy/dt/pySWATPLus)
![PyPI - License](https://img.shields.io/pypi/l/pySWATPlus)


## 📦 About

`pySWATPlus` is an open-source Python package that provides a programmatic interface to the [SWAT+](https://swat.tamu.edu/software/plus/) model, allowing users to run simulations and conduct custom experiments.

## ✨ Key Features

- Run `SWAT+` simulations by modifying model parameters through the  `calibration.cal` file.
- Evaluate model performance against observed data using widely recognized statistical indicators.
- Perform sensitivity analysis on model parameters using the [`SALib`](https://github.com/SALib/SALib) Python package.
- Calibrate model parameters through multi-objective optimization and evolutionary algorithms using the [`pymoo`](https://github.com/anyoptimization/pymoo) Python package. 
- Execute sensitivity analysis and model calibration through high-level interfaces with built-in parallel computation support.
- Analyze outputs from model simulations, sensitivity analyses, and calibrations.


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
refere to the [pySWATPlus documentation](https://swat-model.github.io/pySWATPlus/).

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
## 🙏 Acknowledgments
We acknowledge the [University of Oulu](https://www.oulu.fi/en) and [ICRA](https://icra.cat/en) research center for their support and the collaborative environment that made this project possible.
