# Model Calibration

This tutorial demonstrates how to perform `SWAT+` model calibration to optimize sensitive parameters based on observed data.

Before running the calibration, ensure the model is properly configured. This includes setting the simulation timeline, managing file outputs, and fixing non-sensitive parameters so that they remain constant across all scenarios. A detailed explanation of these steps is provided in the [`Configuration Settings`](https://swat-model.github.io/pySWATPlus/userguide/sensitivity_interface/#configuration-settings) section.

Leveraging the multi-objective optimization and evolutionary algorithms available in the [`pymoo`](https://github.com/anyoptimization/pymoo) Python package,
the calibration interface offers flexible options for optimizing model parameters:

- Single- or multi-objective optimization (e.g., single objective such as flow discharge, or multiple objectives such as flow discharge and nitrogen concentration together).  
- Multiple algorithm options for both single- and multi-objective optimization:

    - Single-objective algorithms
    
        - Genetic Alogorithm
        - [Differential Evolution Algorithm](https://doi.org/10.1007/3-540-31306-0)
        
    - Multi-objective algorithms
    
        - [Non-dominated sorted Genetic Algorithm-II](https://doi.org/10.1109/4235.996017)
        
- Five indicators for comparing simulated and observed values:

    - Nash–Sutcliffe Efficiency
    - Kling–Gupta Efficiency
    - Mean Squared Error
    - Root Mean Squared Error
    - Mean Absolute Relative Error

- Parallel computation support for faster processing.

- Automatic saving of optimization history for each generation, enabling analysis of optimization progress, convergence trends, performance indicators, and visualization.


The interface provides a [`Calibration`](https://swat-model.github.io/pySWATPlus/api/calibration/) class that must be initialized with the required parameters.
This class includes the [`parameter_optimization`](https://swat-model.github.io/pySWATPlus/api/calibration/#pySWATPlus.Calibration.parameter_optimization) method,
which performs parameter optimization using multi-objective algorithms, evolutionary strategies, and parallel computation.

The following code provides an example of optimizing flow discharge for both daily and monthly time-series data using multi-objective evolutionary computation.
The usage of both daily and monthly flow discharge is just for illustrative purposes on how multi-objective optimization can be performed. Users should replace monthly flow
discharge by nitorgen or phosporus concentration according to their needs.


```python
# Define parameter space
parameters = [
    {
        'name': 'esco',
        'change_type': 'absval',
        'lower_bound': 0,
        'upper_bound': 1
    },
    {
        'name': 'perco',
        'change_type': 'absval',
        'lower_bound': 0,
        'upper_bound': 1
    }
]


# Extract data configuration
extract_data = {
    'channel_sd_day.txt': {
        'has_units': True,
        'apply_filter': {'name': ['cha561']}
    },
    'channel_sd_mon.txt': {
        'has_units': True,
        'ref_day': 1,
        'apply_filter': {'name': ['cha561']}
    }
}

# Observe data configuration
observe_data = {
    'channel_sd_day.txt': {
        'obs_file': r"C:\Users\Username\observed_folder\discharge_daily.csv",
        'date_format': '%Y-%m-%d'
    },
    'channel_sd_mon.txt': {
        'obs_file': r"C:\Users\Username\observed_folder\discharge_monthly.csv",
        'date_format': '%Y-%m-%d'
    }
}

# Objective configuration
objective_config = {
    'channel_sd_day.txt': {
        'sim_col': 'flo_out',
        'obs_col': 'discharge',
        'indicator': 'NSE'
    },
    'channel_sd_mon.txt': {
        'sim_col': 'flo_out',
        'obs_col': 'mean',
        'indicator': 'RMSE'
    }
}

# Model calibration
if __name__ == '__main__':
    calibration = pySWATPlus.Calibration(
        parameters=parameters,
        calsim_dir=r"C:\Users\Username\simulation_calibration",
        txtinout_dir=r"C:\Users\Username\project\Scenarios\Default\TxtInOut",
        extract_data=extract_data,
        observe_data=observe_data,
        objective_config=objective_config,
        algorithm='NSGA2',
        n_gen=2,
        pop_size=5
    )

    output = calibration.parameter_optimization()
```


!!! tip "Troubleshooting Parallel Processing Errors"
    If you encounter an error related to `concurrent.futures.ProcessPoolExecutor` and  `multiprocessing` without a clear description,
    try closing the current command terminal and restarting it. This issue can occasionally occur due to lingering background processes
    or locked resources from previous runs.

