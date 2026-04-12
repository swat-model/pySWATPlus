# TxtinoutReader

`TxtinoutReader` is the core class for interacting with a SWAT+ model. It reads and modifies
the input files inside a `TxtInOut` directory and runs the simulation.

**Typical workflow:**

1. Instantiate with the path to your `TxtInOut` folder.
2. Optionally configure the simulation period, warmup, output objects, and print settings.
3. Call `run_swat()` — optionally passing a `parameters` list to write a `calibration.cal` file.

```python
import pySWATPlus

reader = pySWATPlus.TxtinoutReader('/path/to/TxtInOut')

reader.run_swat(
    begin_date='01-Jan-2010',
    end_date='31-Dec-2015',
    warmup=2,
    parameters=[
        {'name': 'cn2', 'change_type': 'pctchg', 'value': 10.0},
    ],
    print_prt_control={
        'channel_sd': {},              # enable all timesteps
        'hru_wb': {'monthly': False},  # disable monthly
    }
)
```

!!! tip
    Pass `sim_dir` to `run_swat()` to run in a separate directory, keeping the original
    `TxtInOut` folder unchanged. This is required when running simulations in parallel.

---

::: pySWATPlus.TxtinoutReader
