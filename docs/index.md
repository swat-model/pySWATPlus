# pySWATPlus


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14889320.svg)](https://doi.org/10.5281/zenodo.14889320)


**pySWATPlus** is a Python package that makes working with SWAT+ models easier and more powerful. Whether you're running default setups or custom projects, this tool lets you interact with SWAT+ programmatically, so you can focus on optimizing and analyzing your models like a pro! 🚀

---

## ⚠️ Version Compatibility Notice

**Version 1.x introduces breaking changes and is not compatible with the previous 0.x versions.**

- If you're looking for the legacy 0.x version:
  - 📦 **Install from PyPI**:  
    ```bash
    pip install pySWATPlus==0.2.20
    ```
  - 🗂️ **Access the source code**:  
    [https://github.com/swat-model/pySWATPlus/tree/v0.x](https://github.com/swat-model/pySWATPlus/tree/v0.x)

---

## ✨ Key Features

- **Access and Modify SWAT+ Files**: Navigate, read, modify, and write files in the `TxtInOut` folder used by SWAT+. 📂
- **Model Calibration**: Optimize SWAT+ input parameters using the [Pymoo](https://pymoo.org/) optimization framework to get the best results. 🎯

> ⚠️ **Note**: The `SWATProblem` and `SWATProblemMultimodel` classes have been removed in version 1.x. Tutorials on how to perform calibration analysis will be updated soon.

---

## 📦 About

pySWATPlus is an open-source software developed and maintained by [ICRA](https://icra.cat/). It’s available for download and installation via [PyPI](https://pypi.org/project/pySWATPlus/). 

---

## ⚙️ Requirements

To use this package, a Python version above 3.10 is required.

---

## 📥 Install pySWATPlus

Once the dependencies are installed, you can install pySWATPlus using this simple command:

````py
pip install pySWATPlus
````

---

## 🚀 Getting Started

The **[Getting Started](examples/getting_started.ipynb)** notebook is the perfect place to begin your journey with pySWATPlus. It covers the basics and links to practical examples, from setting up and running a simple SWAT+ project to diving into parameter optimization techniques and sensitivity analysis.

For a deeper dive, check out the **[API Reference](api/txtinoutreader.md)**, which documents all functions, input arguments, and provides short examples on how to use them. The API Reference includes:

- **[TxtinoutReader](api/txtinoutreader.md)**: Work with SWAT+ input and output files.
- **[FileReader](api/filereader.md)**: Read and manipulate SWAT+ files.
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