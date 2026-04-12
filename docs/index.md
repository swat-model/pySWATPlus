# pySWATPlus

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14889319.svg)](https://doi.org/10.5281/zenodo.14889319)

`pySWATPlus` is an open-source Python package that provides a programmatic interface to the [SWAT+](https://swat.tamu.edu/software/plus/) model, enabling reproducible simulations and custom experiments from Python code.

---

## Key Features

- Run SWAT+ simulations by modifying model parameters through the `calibration.cal` file.
- Evaluate model performance against observed data using widely recognised statistical indicators.
- Perform sensitivity analysis on model parameters using [SALib](https://github.com/SALib/SALib).
- Calibrate model parameters through multi-objective optimisation and evolutionary algorithms using [pymoo](https://github.com/anyoptimization/pymoo).
- Execute sensitivity analysis and model calibration through high-level interfaces with built-in parallel computation support.
- Analyse outputs from simulations, sensitivity analyses, and calibrations.

---

## Install

```bash
pip install pySWATPlus
```

```python
import pySWATPlus  # verify installation
```

---

## Where to Start

<div class="grid cards" markdown>

- **[SWAT+ Simulation](userguide/swatplus_simulation.md)**
  
    Set up your TxtInOut folder, modify parameters, and run a simulation.

- **[Sensitivity Analysis](userguide/sensitivity_interface.md)**
  
    Use Sobol sampling and parallel computing to rank parameter influence.

- **[Model Calibration](userguide/model_calibration.md)**
  
    Optimise parameters with GA, DE, or NSGA-II evolutionary algorithms.

- **[Data Analysis](userguide/data_analysis.md)**
  
    Load simulation output files and compute performance metrics.

</div>

---

## Quick Example

```python
import pySWATPlus

# Point to your TxtInOut folder
reader = pySWATPlus.TxtinoutReader('/path/to/TxtInOut')

# Run a simulation with parameter changes
reader.run_swat(
    begin_date='01-Jan-2010',
    end_date='31-Dec-2015',
    warmup=2,
    parameters=[
        {'name': 'cn2',  'change_type': 'pctchg', 'value': 10.0},
        {'name': 'esco', 'change_type': 'absval',  'value': 0.8},
    ],
    print_prt_control={'channel_sd': {}}
)

# Evaluate performance against observed data
pm = pySWATPlus.PerformanceMetrics()
nse = pm.indicator_from_file(
    sim_file='/path/to/TxtInOut/channel_sd_day.txt',
    obs_file='/path/to/observed.csv',
    has_units=True,
    sim_col='flo_out',
    obs_col='discharge',
    indicator='NSE',
    date_format='%Y-%m-%d'
)
print(f'NSE: {nse:.3f}')
```

---

## Citation

If you use `pySWATPlus` in your research, please cite it using the following concept DOI:

```bibtex
@software{joan_salo_pyswatplus_latest,
  author       = {Joan Saló and Debasish Pal and Oliu Llorente},
  title        = {swat-model/pySWATPlus},
  year         = 2025,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.14889319},
  url          = {https://doi.org/10.5281/zenodo.14889319},
}
```

## Acknowledgments

We acknowledge the [University of Oulu](https://www.oulu.fi/en) and [ICRA](https://icra.cat/en) research centre for their support and the collaborative environment that made this project possible.
