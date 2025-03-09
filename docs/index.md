# pySWATPlus


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14889320.svg)](https://doi.org/10.5281/zenodo.14889320)


**pySWATPlus** is a Python package that makes working with SWAT+ models easier and more powerful. Whether you're running default setups or custom projects, this tool lets you interact with SWAT+ programmatically, so you can focus on optimizing and analyzing your models like a pro! 🚀

---

## ✨ Key Features

- **Access and Modify SWAT+ Files**: Navigate, read, modify, and write files in the `TxtInOut` folder used by SWAT+. 📂
- **Model Calibration**: Optimize SWAT+ input parameters using the [Pymoo](https://pymoo.org/) optimization framework to get the best results. 🎯

---

## 📦 About

pySWATPlus is an open-source software developed and maintained by [ICRA](https://icra.cat/). It’s available for download and installation via [PyPI](https://pypi.org/project/pySWATPlus/). 

---

## 🛠️ Installation

Before installing pySWATPlus, make sure you have the following dependencies installed:

```py
pip install pandas numpy pymoo tqdm dask
```

---

## ⚙️ Requirements

To use this package, a Python version above 3.6 is required.

---

## 📥 Install pySWATPlus

Once the dependencies are installed, you can install pySWATPlus using this simple command:

````py
pip install pySWATPlus
````

---

## 🚀 Getting Started

The **[Getting Started](getting-started.md)** page is the perfect place to begin your journey with pySWATPlus. It covers the basics and links to practical examples, from setting up and running a simple SWAT+ project to diving into parameter optimization techniques and sensitivity analysis.

For a deeper dive, check out the **[API Reference](api/txtinoutreader.md)**, which documents all functions, input arguments, and provides short examples on how to use them. The API Reference includes:

- **[TxtinoutReader](api/txtinoutreader.md)**: Work with SWAT+ input and output files.
- **[FileReader](api/filereader.md)**: Read and manipulate SWAT+ files.
- **[SWATProblem](api/swatproblem.md)**: Define and solve SWAT+ optimization problems.
- **[SWATProblemMultimodel](api/swatproblemmultimodel.md)**: Handle multi-model calibration scenarios.
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
  version   = {0.1.0},
  doi       = {10.5281/zenodo.14889320},
  url       = {https://doi.org/10.5281/zenodo.14889320}
}
```