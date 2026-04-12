# Calibration

`Calibration` performs automatic parameter optimisation for SWAT+ using evolutionary algorithms
from [pymoo](https://pymoo.org/). It subclasses `pymoo.core.problem.Problem` and supports both
single-objective and multi-objective optimisation.

**Available algorithms:**

| Algorithm | Type | Use when |
|-----------|------|----------|
| `GA` | Single-objective | One output variable and one indicator |
| `DE` | Single-objective | One output variable and one indicator |
| `NSGA2` | Multi-objective | Multiple output variables or indicators |

**Typical workflow:**

1. Define parameter bounds (same format as `SensitivityAnalyzer`).
2. Instantiate `Calibration` with simulation directories, observed data, and objectives.
3. Call `parameter_optimization()` to run the evolutionary algorithm.

```python
import logging
import pySWATPlus

logging.basicConfig(level=logging.INFO)  # track generation progress

cal = pySWATPlus.Calibration(
    parameters=[
        {'name': 'cn2',  'change_type': 'pctchg', 'lower_bound': 25, 'upper_bound': 75},
        {'name': 'esco', 'change_type': 'absval',  'lower_bound': 0,  'upper_bound': 1},
    ],
    calsim_dir='/path/to/cal_dir',
    txtinout_dir='/path/to/TxtInOut',
    extract_data={
        'channel_sd_day.txt': {
            'has_units': True,
            'apply_filter': {'gis_id': [42]}
        }
    },
    observe_data={
        'channel_sd_day.txt': {
            'obs_file': '/path/to/observed.csv',
            'date_format': '%Y-%m-%d'
        }
    },
    objective_config={
        'channel_sd_day.txt': {
            'sim_col': 'flo_out',
            'obs_col': 'discharge',
            'indicator': 'NSE'
        }
    },
    algorithm='NSGA2',
    n_gen=20,
    pop_size=16,
)

result = cal.parameter_optimization(json_output='/path/to/results.json')
```

!!! tip
    Choose `pop_size` as a multiple of your CPU count to maximise parallel efficiency.
    With 16 CPUs and `pop_size=16`, each generation runs in a single parallel batch.

!!! note
    Do **not** include `usecols` in `extract_data` for `Calibration` — it is automatically
    derived from the `sim_col` values in `objective_config`.

---

::: pySWATPlus.Calibration
