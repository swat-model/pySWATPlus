# Sensitivity Analysis

Sensitivity analysis helps quantify how variation in input parameters affects model outputs. This tutorial demonstrates how to perform sensitivity analysis on SWAT+ model parameters.  
The parameter sampling is handled by the [SALib](https://github.com/SALib/SALib) Python package using [Sobol](https://doi.org/10.1016/S0378-4754(00)00270-6) sampling from a defined parameter space.

- **Configuration Settings**

    ```python
    import pySWATPlus
    
    # Initialize the project's TxtInOut folder
    txtinout_reader = pySWATPlus.TxtinoutReader(
        path=r"C:\Users\Username\project\Scenarios\Default\TxtInOut"
    )

    # Copy required files to an empty custom directory
    target_dir = r"C:\Users\Username\custom_folder" 
    target_dir = txtinout_reader.copy_required_files(
        target_dir=target_dir
    )

    # Initialize TxtinoutReader with the custom directory
    target_reader = pySWATPlus.TxtinoutReader(
        path=target_dir
    )

    # Disable CSV file generation to save time
    target_reader.disable_csv_print()

    # Disable daily time series in print.prt (saves time and space)
    target_reader.enable_object_in_print_prt(
        obj=None,
        daily=False,
        monthly=True,
        yearly=True,
        avann=True
    )
    
    # Run a trial simulation to verify expected time series outputs
    begin_and_end_date = {
        'begin_date': '01-Jan-2010',
        'end_date': '31-Dec-2012'
    }
    target_reader.run_swat(
        begin_and_end_date=begin_and_end_date,
        warmup=1,
        print_prt_control={
            'channel_sd': {}
        }  # enable daily time series for 'channel_sd'
    ```

---

- **Sobol-Based Interface**

    This high-level interface builds on the above configuration to run sensitivity simulations using Sobol sampling. It includes:

    - Automatic generation of Sobol samples for the parameter space  
    - Parallel computation to speed up simulations  
    - Output extraction with filtering options (by date, column values, etc.)  
    - Structured export of results for downstream analysis  

    The results can be used to compute performance metrics, compare with observed data, and calculate Sobol indices.

    ```python
    # Sensitivity parameter space
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
    
    # Target data extraction from sensitivity simulation
    simulation_data = {
        'channel_sdmorph_yr.txt': {
            'has_units': True,
            'ref_day': 15,
            'ref_month': 6,
            'apply_filter': {'gis_id': [561]},
            'usecols': ['gis_id', 'flo_out']
        },
        'channel_sd_mon.txt': {
            'has_units': True,
            'begin_date': '01-Jun-2011',
            'ref_day': 15,
            'apply_filter': {'name': ['cha561'], 'yr': [2012]},
            'usecols': ['gis_id', 'flo_out']
        }
    }

    # Sensitivity simulation
    if __name__ == '__main__':
        output = pySWATPlus.SensitivityAnalyzer().simulation_by_sobol_sample(
            parameters=parameters,
            sample_number=1,
            simulation_folder=r"C:\Users\Username\simulation_folder",
            txtinout_folder=target_dir,
            simulation_data=simulation_data,
            clean_setup=True
        )
        print(output)
    ```

