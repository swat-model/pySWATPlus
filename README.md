# pySWATPlus


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14889320.svg)](https://doi.org/10.5281/zenodo.14889320)
[![flake8](https://github.com/swat-model/pySWATPlus/actions/workflows/linting.yml/badge.svg)](https://github.com/swat-model/pySWATPlus/actions/workflows/linting.yml)


**pySWATPlus** is a Python package that makes working with SWAT+ models easier and more powerful. Whether you're running default setups or custom projects, this tool lets you interact with SWAT+ programmatically, so you can focus on optimizing and analyzing your models like a pro! 🚀

---

## ✨ Key Features

- **Access and Modify SWAT+ Files**: Navigate, read, modify, and write files in the `TxtInOut` folder used by SWAT+. 📂
- **Model Calibration**: Optimize SWAT+ input parameters using the [Pymoo](https://pymoo.org/) optimization framework to get the best results. 🎯

---

## 📦 About

pySWATPlus is an open-source software developed and maintained by [ICRA](https://icra.cat/). It’s available for download and installation via [PyPI](https://pypi.org/project/pySWATPlus/). 

---

## 📥 Install pySWATPlus

To use this package, a Python version above 3.10 is required. You can install pySWATPlus using this simple command:

````py
pip install pySWATPlus
````

---

## 📚 Documentation

For detailed documentation, tutorials, and examples, visit the **[pySWATPlus documentation](https://swat-model.github.io/pySWATPlus/)**. The documentation includes:

- **[Getting Started](https://swat-model.github.io/pySWATPlus/examples/basic_examples/)**: A beginner-friendly guide to setting up and running your first SWAT+ project.
- **[API Reference](https://swat-model.github.io/pySWATPlus/api/txtinoutreader/)**: Comprehensive documentation of all functions, input arguments, and usage examples.
  - **[TxtinoutReader](https://swat-model.github.io/pySWATPlus/api/txtinoutreader/)**: Work with SWAT+ input and output files.
  - **[FileReader](https://swat-model.github.io/pySWATPlus/api/filereader/)**: Read and manipulate SWAT+ files.
---


## 📖 Citation
To cite pySWATPlus, use:

```tex
@misc{Salo_Llorente_2023,
  author    = {Saló, Joan and Llorente, Oliu},
  title     = {{pySWATPlus: A Python Interface for SWAT+ Model Calibration and Analysis}},
  year      = {2023},
  month     = dec,
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.14889320},
  url       = {https://doi.org/10.5281/zenodo.14889320}
}
```
