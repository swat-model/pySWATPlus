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
| Run a SWAT+ simulation with parameter changes | `TxtinoutReader.run_swat(sim_dir=..., parameters=[...])` |
| Read a SWAT+ output file | `DataManager().simulated_timeseries_df(sim_file=..., ...)` |
| Compute performance indicators | `PerformanceMetrics().compute_from_abbr(df, sim_col, obs_col, indicator)` |
| Parallel execution | `concurrent.futures.ProcessPoolExecutor` |
| Optimisation | [pymoo](https://pymoo.org/), [scipy.optimize](https://docs.scipy.org/doc/scipy/reference/optimize.html), [Optuna](https://optuna.org/), … |

No new API is required — everything needed is already public.

---

## Example: multi-channel calibration with pymoo

This example calibrates two parameters against observed daily flow at two channels simultaneously.
Mean NSE and mean KGE (each averaged across both channels) are used as separate Pareto objectives,
which is a case that the built-in `Calibration` class cannot express directly.

### Step 1 — Configure the model

Set the simulation period, output print options, and any fixed parameters before running calibration.
See [Configuration Settings](sensitivity_interface.md#configuration-settings) for a detailed walkthrough.

### Step 2 — Define the simulation function

Each call to the optimiser evaluates an entire population in parallel using
`concurrent.futures.ProcessPoolExecutor`. The function submitted to the executor
must be **defined at module level** — lambdas and nested functions cannot be pickled
and will cause a `PicklingError`.

```python
import logging
import pathlib
import shutil
from pySWATPlus import TxtinoutReader, DataManager

logging.basicConfig(level=logging.INFO)

TXTINOUT_DIR = pathlib.Path(r'C:\Users\Username\custom_folder')
SIM_DIR      = pathlib.Path(r'C:\Users\Username\calibration_dir')
CHANNEL_IDS  = [561, 562]

def _run_sim(args):
    '''Run one SWAT+ simulation and return its outputs. Must be a top-level function.'''
    idx, param_values, param_configs = args

    # Build the parameter list expected by run_swat
    parameters = [
        {
            'name': cfg['name'],
            'change_type': cfg['change_type'],
            'value': float(val)
        }
        for cfg, val in zip(param_configs, param_values)
    ]

    # Each simulation needs its own empty subdirectory
    sim_path = SIM_DIR / f'sim_{idx}'
    sim_path.mkdir()

    try:
        reader   = TxtinoutReader(tio_dir=TXTINOUT_DIR)
        run_path = reader.run_swat(sim_dir=sim_path, parameters=parameters)

        outputs = {}
        for ch_id in CHANNEL_IDS:
            outputs[ch_id] = DataManager().simulated_timeseries_df(
                sim_file=run_path / 'channel_sd_day.txt',
                has_units=True,
                apply_filter={'gis_id': [ch_id]},
                usecols=['flo_out']
            )
    finally:
        shutil.rmtree(sim_path, ignore_errors=True)

    return idx, outputs
```

!!! note
    If a previous run was interrupted and left stale `sim_<n>` directories behind,
    remove them manually before restarting — `run_swat` requires each simulation
    directory to be empty.

### Step 3 — Define the pymoo Problem

Load observed data once at module level so it is available in `_evaluate`.
Indicator computation happens in the main process after simulations complete,
so there is no concern about pickling pandas DataFrames.

```python
import numpy
import pandas
import concurrent.futures
import pymoo.core.problem
from pySWATPlus import PerformanceMetrics

obs = {
    561: pandas.read_csv(r'C:\Users\Username\obs_561.csv', parse_dates=['date']),
    562: pandas.read_csv(r'C:\Users\Username\obs_562.csv', parse_dates=['date']),
}
for df in obs.values():
    df['date'] = df['date'].dt.date
    df.rename(columns={'discharge': 'obs'}, inplace=True)

PARAM_CONFIGS = [
    {'name': 'esco', 'change_type': 'absval', 'lower_bound': 0,  'upper_bound': 1},
    {'name': 'cn2',  'change_type': 'pctchg', 'lower_bound': 25, 'upper_bound': 75},
]


class MultiChannelCalibration(pymoo.core.problem.Problem):

    def __init__(self):
        xl = numpy.array([cfg['lower_bound'] for cfg in PARAM_CONFIGS])
        xu = numpy.array([cfg['upper_bound'] for cfg in PARAM_CONFIGS])
        super().__init__(n_var=len(PARAM_CONFIGS), n_obj=2, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        # Submit all simulations in the population
        args_list = [(i, X[i], PARAM_CONFIGS) for i in range(len(X))]

        results = {}
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = {executor.submit(_run_sim, a): a[0] for a in args_list}
            for future in concurrent.futures.as_completed(futures):
                idx, outputs = future.result()
                results[idx] = outputs

        # Score each individual
        pm = PerformanceMetrics()
        F  = []

        for i in range(len(X)):
            nse_vals = []
            kge_vals = []

            for ch_id in CHANNEL_IDS:
                sim_df = results[i][ch_id].copy()
                sim_df.columns = ['date', 'sim']

                merged = sim_df.merge(obs[ch_id][['date', 'obs']], on='date', how='inner')

                # Normalise by the observed range before computing indicators
                obs_min = merged['obs'].min()
                obs_max = merged['obs'].max()
                norm    = (merged[['sim', 'obs']] - obs_min) / (obs_max - obs_min)

                nse_vals.append(pm.compute_from_abbr(norm, 'sim', 'obs', 'NSE'))
                kge_vals.append(pm.compute_from_abbr(norm, 'sim', 'obs', 'KGE'))

            # Negate: pymoo minimises, NSE and KGE are maximised
            F.append([-numpy.mean(nse_vals), -numpy.mean(kge_vals)])

        out["F"] = numpy.array(F)
```

### Step 4 — Run the optimisation

```python
import pymoo.algorithms.moo.nsga2
import pymoo.optimize

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
```

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
