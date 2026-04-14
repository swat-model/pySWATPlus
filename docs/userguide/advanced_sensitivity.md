# Advanced Sensitivity Analysis

The built-in [`SensitivityAnalyzer`](../api/sensitivity_analyzer.md) covers the most common scenario:
Sobol sampling over a parameter space, one output file per objective, compared against observed data
with a standard indicator.

For cases that go beyond this — sensitivity across multiple channels or locations, custom scoring,
or samplers other than Sobol — pySWATPlus exposes the building blocks you need to compose your
own sensitivity workflow directly.

## Building blocks

| Task | Tool |
|------|------|
| Run a SWAT+ simulation with parameter changes | [`TxtinoutReader.run_swat`](../api/txtinout_reader.md) |
| Read a SWAT+ output file | [`DataManager.simulated_timeseries_df`](../api/data_manager.md) |
| Compute performance indicators | [`PerformanceMetrics.compute_from_abbr`](../api/performance_metrics.md) |
| Generate parameter samples | `SALib.sample.sobol.sample` (or any other SALib sampler) |
| Compute Sobol indices | `SALib.analyze.sobol.analyze` |
| Parallel execution | `concurrent.futures.ProcessPoolExecutor` |

!!! tip "Use the built-in SensitivityAnalyzer first"
    Before following this guide, check whether the built-in [`SensitivityAnalyzer`](../api/sensitivity_analyzer.md) covers your needs:

    | Scenario | Use |
    |---|---|
    | One output variable compared to observed data | `SensitivityAnalyzer` |
    | Multiple output variables, one per file | `SensitivityAnalyzer` (multi-output) |
    | Multiple channels or locations from the same file | This guide |
    | Custom scoring or aggregation across locations | This guide |
    | Sampler other than Sobol | This guide |

---

## Example: multi-channel Sobol sensitivity

This example computes Sobol sensitivity indices for two parameters against observed daily flow
at two channels simultaneously, using mean NSE across both channels as the scalar metric —
a case the built-in `SensitivityAnalyzer` cannot express directly.

!!! note
    Steps 2 – 5 all belong in **one Python file**. They are shown separately only to explain each part.

### Step 1 — Configure the model

Set the simulation period, output print options, and any fixed parameters before running simulations.
See [Configuration Settings](sensitivity_interface.md#configuration-settings) for a detailed walkthrough.

### Step 2 — Module-level setup

All imports, paths, and data are defined at the top of the file so they are available to every
function defined below.

```python
import json
import logging
import pathlib
import shutil
import concurrent.futures

import numpy
import pandas
import SALib.sample.sobol
import SALib.analyze.sobol

from pySWATPlus import TxtinoutReader, DataManager, PerformanceMetrics

logging.basicConfig(level=logging.INFO)

# --- Paths ---
TXTINOUT_DIR = pathlib.Path(r'C:\Users\Username\custom_folder')
SIM_DIR      = pathlib.Path(r'C:\Users\Username\sensitivity_dir')

# --- Channels to analyse ---
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

### Step 4 — Generate samples and run simulations

Sobol analysis requires a specific sample structure. `SALib.sample.sobol.sample` generates
`2^(sample_number+1) × (n_params + 2)` parameter sets — for 2 parameters and `sample_number=3`
that is 40 sets. Larger values give more accurate indices but require more simulations.

```python
if __name__ == '__main__':
    # Build the SALib problem definition
    problem = {
        'num_vars': len(PARAM_CONFIGS),
        'names':    [cfg['name'] for cfg in PARAM_CONFIGS],
        'bounds':   [[cfg['lower_bound'], cfg['upper_bound']] for cfg in PARAM_CONFIGS],
    }

    # Generate samples — sample_number=3 → 40 simulations for 2 parameters
    sample_array = SALib.sample.sobol.sample(problem, N=pow(2, 3))

    # Run all simulations in parallel — results come back in the same order as sample_array
    with concurrent.futures.ProcessPoolExecutor() as executor:
        all_outputs = list(executor.map(_run_sim, range(len(sample_array)), sample_array))
```

### Step 5 — Score each sample and compute indices

Each sample needs a single scalar metric. Here, mean NSE across both channels is used.
`SALib.analyze.sobol.analyze` then decomposes the variance of that scalar across parameters.

```python
    # Compute a scalar metric for every sample
    pm = PerformanceMetrics()
    Y  = []

    for outputs in all_outputs:
        nse_vals = []
        for ch_id in CHANNEL_IDS:
            merged = outputs[ch_id].merge(obs[ch_id][['date', 'obs']], on='date', how='inner')
            nse_vals.append(pm.compute_from_abbr(merged, 'sim', 'obs', 'NSE'))
        Y.append(numpy.mean(nse_vals))

    Y = numpy.array(Y)

    # Compute Sobol indices
    indices = SALib.analyze.sobol.analyze(problem, Y)

    # S1: first-order index  — direct effect of each parameter alone
    # ST: total-order index  — direct effect plus all interactions with other parameters
    for name, s1, st in zip(problem['names'], indices['S1'], indices['ST']):
        print(f'{name:10s}  S1={s1:.3f}  ST={st:.3f}')

    # Save results to disk
    with open('sensitivity_indices.json', 'w') as f:
        json.dump({
            'param_names': problem['names'],
            'S1':          indices['S1'].tolist(),
            'ST':          indices['ST'].tolist(),
            'S1_conf':     indices['S1_conf'].tolist(),
            'ST_conf':     indices['ST_conf'].tolist(),
        }, f, indent=4)
```

`sensitivity_indices.json` will look like this:

```json
{
    "param_names": ["esco", "cn2"],
    "S1":      [0.42, 0.31],
    "ST":      [0.58, 0.47],
    "S1_conf": [0.05, 0.04],
    "ST_conf": [0.06, 0.05]
}
```

A high `ST` with a low `S1` for a parameter means it interacts strongly with others.
Parameters with both low `S1` and low `ST` have little influence on the output and are
candidates for fixing at a default value during calibration.

---

## Tips

!!! tip "How many samples do you need?"
    Start with `sample_number=3` (40 simulations for 2 parameters) to get a quick picture.
    Increase to `sample_number=6` or higher for publication-quality indices — the required
    number of simulations grows as `2^(sample_number+1) × (n_params + 2)`.

!!! tip "Using other samplers"
    The Sobol sampler is the default choice, but SALib also provides Morris (`SALib.sample.morris`),
    FAST (`SALib.sample.fast_sampler`), and others. Replace the sampling and analysis calls;
    `_run_sim` and the scoring loop are the same regardless of the sampler used.

!!! tip "Single scalar vs multiple metrics"
    `SALib.analyze.sobol.analyze` requires one scalar per sample. If you want sensitivity
    indices for NSE and KGE separately, run `analyze` twice with two different `Y` arrays —
    one built from NSE values, one from KGE values.

!!! tip "Tracking progress"
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
