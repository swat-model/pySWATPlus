# DataManager

`DataManager` provides utilities for loading and processing SWAT+ simulation output files.

**Key methods:**

- `simulated_timeseries_df` — load a SWAT+ output file into a pandas `DataFrame` with datetime indexing,
  optional date filtering, column selection, and row filtering.
- `hru_stats_from_daily_simulation` — derive monthly and yearly statistics from a daily HRU output file.
- `read_sensitive_dfs` — load per-simulation DataFrames from a `sensitivity_simulation.json` file
  produced by `SensitivityAnalyzer`.

```python
import pySWATPlus

dm = pySWATPlus.DataManager()

# Load a daily channel output file, filtered to a specific reach
df = dm.simulated_timeseries_df(
    input_file='/path/to/TxtInOut/channel_sd_day.txt',
    has_units=True,
    begin_date='01-Jan-2012',
    end_date='31-Dec-2015',
    apply_filter={'gis_id': [42]},
    usecols=['gis_id', 'flo_out']
)

# Aggregate daily HRU output to monthly/yearly stats
stats = dm.hru_stats_from_daily_simulation(
    input_file='/path/to/TxtInOut/hru_wb_day.txt',
    has_units=True,
    apply_filter={'name': ['hru001']}
)
```

!!! note
    Set `has_units=True` when the third line of the output file contains column units
    (most SWAT+ output files do). Set `has_units=False` for files without a units row.

---

::: pySWATPlus.DataManager
