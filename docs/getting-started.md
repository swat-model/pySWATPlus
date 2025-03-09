# Getting Started

## Installation

```bash
pip install pandas numpy pymoo tqdm dask
pip install pySWATPlus
```

## Basic Usage

```python
from pySWATPlus.TxtinoutReader import TxtinoutReader

# Initialize with your SWAT+ project
reader = TxtinoutReader("path/to/swatplus_project")

# Run SWAT+ with modified parameters
results = reader.run_swat(
    params={'plants.plt': ('name', [('bana', 'bm_e', 45)])},
    show_output=False
)
```

[View more examples](https://github.com/swat-model/pySWATPlus/tree/main/examples)