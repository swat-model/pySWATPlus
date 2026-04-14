# Advanced Calibration

The built-in [`Calibration`](../api/calibration.md) class covers the most common scenario:
one or more output variables, each compared to observed data with a standard indicator (NSE, KGE, RMSE, etc.),
optimised with GA, DE, or NSGA2.

For cases that go beyond this — custom scoring functions, grouped Pareto objectives, integration with
optimisers other than pymoo, or any other non-standard setup — pySWATPlus exposes the building blocks
you need to compose your own calibration workflow directly.

## Building blocks

| Task | Tool |
|------|------|
| Run a SWAT+ simulation with parameter changes | [`TxtinoutReader.run_swat`](../api/txtinout_reader.md) |
| Read a SWAT+ output file | [`DataManager.simulated_timeseries_df`](../api/data_manager.md) |
| Compute performance indicators | [`PerformanceMetrics.compute_from_abbr`](../api/performance_metrics.md) |
| Parallel execution | `concurrent.futures.ProcessPoolExecutor` |
| Optimisation | [pymoo](https://pymoo.org/), [scipy.optimize](https://docs.scipy.org/doc/scipy/reference/optimize.html), [Optuna](https://optuna.org/), … |

!!! tip "Use the built-in Calibration class first"
    Before following this guide, check whether the built-in [`Calibration`](../api/calibration.md) class covers your needs:

    | Scenario | Use |
    |---|---|
    | One output variable compared to observed data | `Calibration` |
    | Multiple output variables, one per file | `Calibration` (multi-objective) |
    | Multiple channels or locations from the same file | This guide |
    | Custom scoring or aggregation across locations | This guide |
    | Optimiser other than GA, DE, or NSGA2 | This guide |

---

## Example: multi-channel calibration with pymoo

This example calibrates two parameters against observed daily flow at two channels simultaneously.
Mean NSE and mean KGE (each averaged across both channels) are used as separate Pareto objectives —
a case that the built-in `Calibration` class cannot express directly.

!!! note
    Steps 2 – 5 all belong in **one Python file**. They are shown separately only to explain each part.

### Step 1 — Configure the model

Set the simulation period, output print options, and any fixed parameters before running calibration.
See [Configuration Settings](sensitivity_interface.md#configuration-settings) for a detailed walkthrough.

### Step 2 — Module-level setup

All imports, paths, and data are defined at the top of the file so they are available to every
function and class defined below.

```python
import json
import logging
import pathlib
import shutil
import concurrent.futures

import numpy
import pandas
import pymoo.algorithms.moo.nsga2
import pymoo.core.problem
import pymoo.optimize

from pySWATPlus import TxtinoutReader, DataManager, PerformanceMetrics

logging.basicConfig(level=logging.INFO)

# --- Paths ---
TXTINOUT_DIR = pathlib.Path(r'C:\Users\Username\custom_folder')
SIM_DIR      = pathlib.Path(r'C:\Users\Username\calibration_dir')

# --- Channels to calibrate against ---
CHANNEL_IDS = [561, 562]

# --- Parameter search space ---
PARAM_CONFIGS = [
    {'name': 'esco', 'change_type': 'absval', 'lower_bound': 0,  'upper_bound': 1},
    {'name': 'cn2',  'change_type': 'pctchg', 'lower_bound': 25, 'upper_bound': 75},
]

# --- Observed discharge (one CSV per channel, must contain 'date' and 'discharge' columns) ---
obs = {
    561: pandas.read_csv(r'C:\Users\Username\obs_561.csv', parse_dates=['date']),
    562: pandas.read_csv(r'C:\Users\Username\obs_562.csv', parse_dates=['date']),
}
for df in obs.values():
    df['date'] = df['date'].dt.date
    df.rename(columns={'discharge': 'obs'}, inplace=True)
```

### Step 3 — Define the simulation function

`_run_sim` must be a **top-level function** (not defined inside a class or another function).
`ProcessPoolExecutor` sends it to worker processes by name, and lambdas or nested functions
cannot be transferred that way — they will raise a `PicklingError`.

```python
def _run_sim(idx, param_values):
    '''Run one SWAT+ simulation and return its channel outputs.'''

    parameters = [
        {'name': cfg['name'], 'change_type': cfg['change_type'], 'value': float(val)}
        for cfg, val in zip(PARAM_CONFIGS, param_values)
    ]

    # Each simulation needs its own empty subdirectory
    sim_path = SIM_DIR / f'sim_{idx}'
    sim_path.mkdir()

    try:
        reader   = TxtinoutReader(tio_dir=TXTINOUT_DIR)
        run_path = reader.run_swat(sim_dir=sim_path, parameters=parameters)

        outputs = {}
        for ch_id in CHANNEL_IDS:
            df = DataManager().simulated_timeseries_df(
                sim_file=run_path / 'channel_sd_day.txt',
                has_units=True,
                apply_filter={'gis_id': [ch_id]},
                usecols=['flo_out']
            )
            # Rename 'flo_out' → 'sim' so PerformanceMetrics can find the simulated column
            outputs[ch_id] = df.rename(columns={'flo_out': 'sim'})
    finally:
        shutil.rmtree(sim_path, ignore_errors=True)

    return outputs
```

!!! note
    If a previous run was interrupted and left stale `sim_<n>` directories behind,
    remove them manually before restarting — `run_swat` requires each simulation
    directory to be empty.

### Step 4 — Define the pymoo Problem

```python
class MultiChannelCalibration(pymoo.core.problem.Problem):

    def __init__(self):
        xl = numpy.array([cfg['lower_bound'] for cfg in PARAM_CONFIGS])
        xu = numpy.array([cfg['upper_bound'] for cfg in PARAM_CONFIGS])
        super().__init__(n_var=len(PARAM_CONFIGS), n_obj=2, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        # Run all simulations in parallel — results come back in the same order as X
        with concurrent.futures.ProcessPoolExecutor() as executor:
            all_outputs = list(executor.map(_run_sim, range(len(X)), X))

        # Score each individual
        pm = PerformanceMetrics()
        F  = []

        for i in range(len(X)):
            nse_vals = []
            kge_vals = []

            for ch_id in CHANNEL_IDS:
                merged = all_outputs[i][ch_id].merge(
                    obs[ch_id][['date', 'obs']], on='date', how='inner'
                )
                nse_vals.append(pm.compute_from_abbr(merged, 'sim', 'obs', 'NSE'))
                kge_vals.append(pm.compute_from_abbr(merged, 'sim', 'obs', 'KGE'))

            # pymoo minimises — negate NSE and KGE so higher is better
            F.append([-numpy.mean(nse_vals), -numpy.mean(kge_vals)])

        out["F"] = numpy.array(F)
```

### Step 5 — Run and save

```python
if __name__ == '__main__':
    result = pymoo.optimize.minimize(
        problem=MultiChannelCalibration(),
        algorithm=pymoo.algorithms.moo.nsga2.NSGA2(pop_size=16),
        termination=('n_gen', 20),
        save_history=True,
        verbose=True
    )

    # Pareto-optimal solutions — un-negate to recover natural direction
    print('Parameters:', result.X)
    print('NSE / KGE:', -result.F)

    # Save results to disk
    PARAM_NAMES = [cfg['name'] for cfg in PARAM_CONFIGS]
    OBJ_NAMES   = ['NSE', 'KGE']

    with open('optimization_result.json', 'w') as f:
        json.dump({
            'param_names': PARAM_NAMES,
            'obj_names':   OBJ_NAMES,
            'variables':   result.X.tolist(),
            'objectives':  (-result.F).tolist()
        }, f, indent=4)

    with open('optimization_history.json', 'w') as f:
        json.dump({
            'param_names': PARAM_NAMES,
            'obj_names':   OBJ_NAMES,
            'generations': {
                i: {
                    'pop': gen.pop.get('X').tolist(),
                    'obj': (-gen.pop.get('F')).tolist()
                }
                for i, gen in enumerate(result.history, start=1)
            }
        }, f, indent=4)
```

`optimization_result.json` will look like this — self-contained, no need to remember the parameter order:

```json
{
    "param_names": ["esco", "cn2"],
    "obj_names":   ["NSE", "KGE"],
    "variables":   [[0.45, 18.2], [0.61, 12.7]],
    "objectives":  [[0.83, 0.71], [0.79, 0.88]]
}
```

Each row in `variables` and `objectives` is one Pareto-optimal solution.

---

## Tips

!!! tip "Choosing pop_size"
    Set `pop_size` to a multiple of your CPU count so each generation runs in a single
    parallel batch. With 16 CPUs and `pop_size=16`, one batch per generation; with
    `pop_size=20`, two batches are needed (16 + 4).

!!! tip "Using other optimisers"
    `_run_sim` is independent of pymoo. The same function works inside any optimisation
    loop — scipy, Optuna, a manual random search, or anything else. Wrap calls to
    `_run_sim` in a `ProcessPoolExecutor` whenever you need to evaluate a batch of
    parameter sets in parallel.

!!! tip "Tracking progress"
    Set `verbose=True` in `pymoo.optimize.minimize` for generation-level logging.
    For per-simulation progress, `pySWATPlus` emits messages via Python's standard
    `logging` module:

    ```python
    import logging
    logging.basicConfig(level=logging.INFO)
    ```

!!! tip "Troubleshooting parallel errors"
    If `ProcessPoolExecutor` raises an unclear error, close the terminal and restart it.
    Lingering background processes or locked files from a previous run can interfere
    with new parallel workloads.
