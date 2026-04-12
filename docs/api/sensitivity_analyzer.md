# SensitivityAnalyzer

`SensitivityAnalyzer` provides a high-level interface for global sensitivity analysis of SWAT+ parameters.
It uses [Sobol sequences](https://doi.org/10.1016/S0378-4754(00)00270-6) via
[SALib](https://salib.readthedocs.io/) to generate parameter samples, runs each sample as a parallel SWAT+
simulation, and computes first-order, total-order, and second-order sensitivity indices.

**Typical workflow:**

1. Define parameter bounds.
2. Call `simulation_by_sample_parameters()` — runs all simulations in parallel and returns a results dict.
3. Call `parameter_sensitivity_indices()` on the result to get SALib sensitivity indices.

Alternatively, use `simulation_and_indices()` to do both in a single call without saving detailed simulation data.

```python
import logging
import pySWATPlus

logging.basicConfig(level=logging.INFO)  # track progress

sa = pySWATPlus.SensitivityAnalyzer()

result = sa.simulation_by_sample_parameters(
    parameters=[
        {'name': 'cn2',  'change_type': 'pctchg', 'lower_bound': 25, 'upper_bound': 75},
        {'name': 'esco', 'change_type': 'absval',  'lower_bound': 0,  'upper_bound': 1},
    ],
    sample_number=2,   # generates 2^3 * (2+1) = 24 samples
    sensim_dir='/path/to/sens_dir',
    txtinout_dir='/path/to/TxtInOut',
    extract_data={
        'channel_sd_day.txt': {
            'has_units': True,
            'apply_filter': {'gis_id': [42]},
            'usecols': ['gis_id', 'flo_out']
        }
    }
)

indices = sa.parameter_sensitivity_indices(result, sim_col='flo_out')
```

!!! note
    `sample_number` controls sample size: the number of simulations is `2^(sample_number+1) × (D + 1)`,
    where `D` is the number of parameters. Start with `sample_number=1` or `2` for quick tests.

---

::: pySWATPlus.SensitivityAnalyzer
