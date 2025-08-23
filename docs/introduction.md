# pySWATPlus


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14889319.svg)](https://doi.org/10.5281/zenodo.14889319)


`pySWATPlus` is an open-source Python package that provides a programmatic interface to the [SWAT+](https://swat.tamu.edu/software/plus/) model, allowing users to run simulations, modify input files, and streamline custom experimentation through the model’s `TxtInOut` folder.


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
