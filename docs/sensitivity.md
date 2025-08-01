# Sensitivity Analysis

This tutorial demonstrates how to perform a sensitivity analysis on SWAT+ model parameters using the [SALib](https://github.com/SALib/SALib) Python package. The analysis focuses on two parameters, `epco` and `esco`, located in the `hydrology.hyd` file.

### Required Packages

This section imports the essential libraries needed to interact with the SWAT+ model, generate parameter samples, execute simulations, handle data, and perform sensitivity analysis.

```python
# Import required packages
import pySWATPlus
import SALib.sample.sobol
import SALib.analyze.sobol
import concurrent.futures
import numpy
import random
import tempfile
```

## Input Variables

Here, we configure the SWAT+ model environment by specifying the `TxtInOut` folder path, simulation time period, warm-up years, and the output files to be generated.

```python
# Input TxtInOut folder path
txtinout_path = r"C:\Users\Username\project\Scenarios\Default\TxtInOut"

# Intialize the TxtinoutReader class
txtinout_reader = pySWATPlus.TxtinoutReader(
    path=txtinout_path
)

# Set simulation timeline (optional)
txtinout_reader.set_begin_and_end_year(
    begin=2010,
    end=2012
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

# Fix any value, if necessary, other that sensitive paramters (optional)
hyd_register = simulation_reader.register_file(
    filename='hydrology.hyd',
    has_units=False
)
hyd_df = hyd_register.df
hyd_df['perco'] = 0.1
hyd_register.overwrite_file()
```

## Evaluation Function

This section sets up the core logic to run the SWAT+ model with different values of `epco` and `esco`, and reads the resulting output. The current implementation returns a random value for demonstration; in practice, this should be replaced with a proper objective function using simulated and observed data.

```python
# Define a function whose output will be used in sensitivity analysis
def run_and_evaluate_swat(
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

    return run_and_evaluate_swat(*params)
```

## Sample Sensitive Parameters
We define the sensitivity problem, including the parameter names and bounds, and use `Sobol` sampling to generate test combinations for the analysis.

```python
problem = {
    'num_vars': 2,  # Number of parameters
    'names': ['epco', 'esco'],  # Parameter names
    'bounds': [[0, 1]] * 2  # Parameter bounds
}

# Generate parameter samples
param_values = SALib.sample.sobol.sample(problem, 2)  
```


## Result Analysis
We run the model simulations in parallel using the parameter samples and analyze the sensitivity of each parameter using `Sobol` indices. 

```python
if __name__ == '__main__':
    
    # Parallel evaluation of Sensitive Parameters
    with concurrent.futures.ProcessPoolExecutor() as executor:
        y = numpy.array(list(executor.map(evaluate, param_values)))

    # Analyze results
    sobol_indices = SALib.analyze.sobol.analyze(problem, y)
    print('First-order Sobol indices:', sobol_indices['S1'])
    print('Total-order Sobol indices:', sobol_indices['ST'])
```










