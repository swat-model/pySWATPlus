# Sensitivity Analysis

Sensitivity analysis helps quantify how variation in input parameters affects model outputs. This tutorial demonstrates how to perform sensitivity analysis on SWAT+ model parameters. Two approaches are provided: a **custom, user-defined workflow** and a **high-level automated interface**, both using the [SALib](https://github.com/SALib/SALib) Python package based on [Sobol](https://doi.org/10.1016/S0378-4754(00)00270-6) sampling from a defined parameter space.


## Custom Workflow

This approach allows users to define the sampling strategy, number of simulations, and custom performance metrics. It is ideal for those seeking fine control over the sensitivity analysis process, tailored to specific research or operational goals. In this example, we focus on two parameters, `epco` and `esco`, located in the `hydrology.hyd` file.

Import the necessary packages and initialize the `TxtinoutReader` class.

```python
# Import packages
import pySWATPlus
import SALib.sample.sobol
import SALib.analyze.sobol
import concurrent.futures
import numpy
import random
import tempfile

# Initialize the TxtinoutReader class
txtinout_reader = pySWATPlus.TxtinoutReader(
    path=r"C:\Users\Username\project\Scenarios\Default\TxtInOut"
)
```

Optionally specify the simulation time period, warm-up years, enable outputs via the `print.prt` file, and fix any parameter values not involved in the sensitivity analysis.

```python
# Set simulation timeline (optional)
txtinout_reader.set_begin_and_end_year(
    begin=2010,
    end=2016
)

# Set warm-up year (optional)
txtinout_reader.set_warmup_year(
    warmup=1
)

# Enable output for channel_sd_day.txt (optional)
txtinout_reader.enable_object_in_print_prt(
    obj='channel_sd',
    daily=True,
    monthly=False,
    yearly=False,
    avann=False
)

# Fix non-sensitive parameters (optional)
hyd_register = simulation_reader.register_file(
    filename='hydrology.hyd',
    has_units=False
)
hyd_df = hyd_register.df
hyd_df['perco'] = 0.1
hyd_register.overwrite_file()
```

Define an evaluation function that runs the SWAT+ model with the specified parameter values and returns an evaluation metric. The current example returns a random value for demonstration purposes. Replace this with a proper objective function using simulated and observed data.

```python
def run_swat_and_evaluate_metric(
    epco: float,
    esco: float
):
    print(f'Running SWAT with epco = {epco} and esco = {esco}')
    print('\n')
    
    # Construct 'params' dictionary
    params =  {
        'hydrology.hyd': {
            'has_units': False,
            'epco': [
                {'value': epco, 'change_type': 'absval'},
            ],
            'esco': [
                {'value': esco, 'change_type': 'absval'},
            ],
        }
    }

    # Temporary directory creation
    with tempfile.TemporaryDirectory() as tmp_dir:
        
        # Run simulation
        simulation_reader = txtinout_reader.run_swat_in_other_dir(
            target_dir=tmp_dir,
            params=params
        )
        
        # Read results
        file_register = simulation_reader.register_file(
            filename='channel_sdmorph_day.txt',
            has_units=True
        )
        
        # Get DataFrame
        file_df = file_register.df

        # Return a random value (replace with real evaluation logic)
        return random.random()

# Wrapper function for parallel execution
def evaluate(params):

    return run_swat_and_evaluate_metric(*params)
```

Define the sensitivity problem and generate samples using `Sobol` sampling.

```python
problem = {
    'num_vars': 2,
    'names': ['epco', 'esco'],
    'bounds': [[0, 1]] * 2
}

# Generate Sobol samples
param_values = SALib.sample.sobol.sample(problem, 2)
```

Run simulations in parallel and compute Sobol indices to analyze parameter influence.

```python
if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor() as executor:
        simulation_output = numpy.array(list(executor.map(evaluate, param_values)))

    sobol_indices = SALib.analyze.sobol.analyze(problem, simulation_output)

    print('First-order Sobol indices:', sobol_indices['S1'])
    print('Total-order Sobol indices:', sobol_indices['ST'])
```


## Sobol-Based Simulation Interface

This high-level interface automates the sensitivity simulation workflow using Sobol samples. It includes:

- Automatic generation of Sobol samples for the defined parameter space
- Parallel computation to accelerate simulation runs
- Output extraction from target data files with filtering options (by date, column values, etc.)
- Structured export of results for downstream analysis

The output data can be used to compute performance metrics, compare with observed data, and estimate Sobol indices to quantify parameter influence.

This interface is ideal for users seeking a scalable, low-configuration solution.


```python
import pySWATPlus

if __name__ == '__main__':
    # Copy required file to a target direcotry to keep original `TxtInOut` folder unchanged
    target_dir = r"C:\Users\Username\target_folder"
    txtinout_reader.copy_required_files(
        target_dir=target_dir
    )
    # Intialize `TxtinOutReader` class by target direcotry
    target_reader = pySWATPlus.TxtinoutReader(
        path=target_dir
    )
    # Disable daily frequency simulation file from generated in print.prt (optional)
    target_reader.enable_object_in_print_prt(
        obj=None,
        daily=False,
        monthly=True,
        yearly=True,
        avann=True
    )
    # Set begin and end year (optional)
    target_reader.set_begin_and_end_year(
        begin=2010,
        end=2012
    )
    # Set warmup year (optional)
    target_reader.set_warmup_year(
        warmup=1
    )
    # Sensitivity variable names
    var_names=[
        'esco',
        '|'.join(['bm_e', 'name == "agrl"'])
    ]
    # Sensitivity variable bounds
    var_bounds = [
        [0, 1],
        [30, 40]
    ]
    # Sensitivity 'params' dictionary to run SWAT+ model
    params={
        'hydrology.hyd': {
            'has_units': False,
            'esco': {'value': 0}
        },
        'plants.plt': {
            'has_units': False,
            'bm_e': {'value': 0, 'filter_by': 'name == "agrl"'}
        }
    }
    # Sensitivity simulation_data dictionary to extract data
    simulation_data = {
        'channel_sd_mon.txt': {
            'has_units': True,
            'start_date': '2011-06-01',
            'end_date': '2012-06-01',
            'apply_filter': {'gis_id': [561]},
            'usecols': ['gis_id', 'flo_out']
        },
        'channel_sd_yr.txt': {
            'has_units': True,
            'apply_filter': {'name': ['cha561'], 'yr': [2012]},
            'usecols': ['gis_id', 'flo_out']
        }
    }
    # Sensitive simulation
    output = pySWATPlus.SensitivityAnalyzer().simulation_by_sobol_sample(
        var_names=var_names,
        var_bounds=var_bounds,
        sample_number=1,
        simulation_folder=r"C:\Users\Username\simulation_folder",
        txtinout_folder=target_dir,
        params=params,
        simulation_data=simulation_data,
        max_workers=4,
        clean_setup=False
    )
```

