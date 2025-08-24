# SWAT+ Simulation

`pySWATPlus` executes [SWAT+](https://swat.tamu.edu/software/plus/) simulations using the `TxtInOut` folder generated during project creation with [QSWAT+](https://github.com/swat-model/QSWATPlus).

To run a `SWAT+` simulation, the `TxtInOut` folder must include all required input files, which are created during simulation setup in the [SWAT+ Editor](https://github.com/swat-model/swatplus-editor) via `QSWAT+`.

Additionally, the `TxtInOut` folder must contain the `SWAT+` executable. If you need help locating it, open the **`Run SWAT+`** tab in the `SWAT+ Editor` to find its path. Once located, copy the executable file into the `TxtInOut` folder. If the executable is missing, the simulation will fail.

Once the `TxtInOut` folder is properly configured with the necessary input files and the `SWAT+` executable, you can initialize the `TxtinoutReader` class to interact with the `SWAT+` model:

```python
import pySWATPlus

# Replace this with the path to your project's TxtInOut folder
txtinout_folder = r"C:\Users\Username\project\Scenarios\Default\TxtInOut"

txtinout_reader = pySWATPlus.TxtinoutReader(
    path=txtinout_folder
)
```

`pySWATPlus` offers multiple options for executing `SWAT+` simulations, providing flexibility for diverse workflows and automation needs.

The following sections demonstrate different approaches, including modifying input parameters, running a single simulation, and performing batch processing.


## A Trial Simulation

This simple example runs a `SWAT+` simulation without changing any input parameters, ensuring that the setup works correctly:


```python
txtinout_reader.run_swat()
```

## Simulations in a Separate Directory (Recommended)


To keep your original `TxtInOut` folder unchanged, it is recommended to run `SWAT+` simulations in a separate directory. This approach allows you to safely modify parameters and input files without affecting your main project. The following steps demonstrate how to perform a simulation in a dedicated directory:


- Copy required files to the target directory:

    ```python
    # Replance this with your desired simulation folder path
    target_dir = r"C:\Users\Username\simulation_folder_1" 

    # Ensure the required files are copied
    txtinout_reader.copy_required_files(
        target_dir=target_dir
    )
    ```

- Initialize `TxtinoutReader` for the target directory

    ```python
    target_reader = pySWATPlus.TxtinoutReader(
        path=target_dir
    )
    ```

- Modify simulation timeline:

    ```python
    # Update timeline in `time.sim` file
    target_reader.set_begin_and_end_year(
        begin=2012,
        end=2016
    )
    ```

- Set warm-up years:

    ```python
    # Set warm-up years in `print.prt` file
    target_reader.set_warmup_year(
        warmup=1
    )
    ```

- Enable required simulation files:

    ```python
    # Ensure simulation outputs for `channel_sd` object in `print.prt` file  
    target_reader.enable_object_in_print_prt(
        obj='channel_sd',
        daily=False,
        monthly=True,
        yearly=True,
        avann=True,
    )
    ```
    
- Modify `esco` parameter:

    ```python
    # Register the `hydrology.hyd` file
    hyd_register = target_reader.register_file(
        filename='hydrology.hyd',
        has_units=False
    )

    # Get the DataFrame and modify the `esco` value
    hyd_df = hyd_register.df
    hyd_df['esco'] = 0.6

    # Overwrite the `hydrology.hyd` file
    hyd_register.overwrite_file()
    ```
    
- Run the SWAT+ simulation:

    ```python
    # Another way to modify `esco` parameter and perform simulation
    params = {
        'hydrology.hyd': {
            'has_units': False,
            'esco': {'value': 0.6}
        }
    }
    target_reader.run_swat(
        params=params  # optional
    )
    ```


## Run Configurable Simulations in a Single Function

Instead of performing each step separately as explained above, you can run a `SWAT+` simulation in a separate directory by configuring all options at once using a single function:

```python
# Configure input parameters
params = {
    'hydrology.hyd': {
        'has_units': False,
        'esco': {'value': 0.6}
    }
}

# Run SWAT+ simulation from the original `TxtInOut` folder
txtinout_reader.run_swat_in_other_dir(
    target_dir=r"C:\Users\Username\simulation_folder_2",  # mandatory
    params=params,  # optional
    begin_and_end_year=(2012, 2016),  # optional
    warmup=1,  # optional
    print_prt_control={'channel_sd': {'daily': False}}  # optional
)
```


## Parallel SWAT+ Simulations

To run multiple SWAT+ simulations in parallel with modified parameters, the following example provides a quick guide to get started:


```python
import multiprocessing
import tempfile

# Define multiple parameter sets
param_sets = [
    {
        'hydrology.hyd': {
            'has_units': False,
            'esco': [
                {'value': 0.6, 'change_type': 'absval'}
            ],
        }
    },
    {
        'plants.plt': {
            'has_units': False,
            'bm_e': [
                {'value': 30, 'change_type': 'absval', 'filter_by': 'name == "agrl"'},
                {'value': 15, 'change_type': 'absval', 'filter_by': 'name == "almd"'},
            ],
        }
    },
]

# Define the function
def run_simulation(params):
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        reader = pySWATPlus.TxtinoutReader(
            path=txtinout_path
        )
        output = reader.run_swat_in_other_dir(
            target_dir=tmp_dir,
            params=params
        )
    
    return output


if __name__ == '__main__':
    # Run simulations in parallel
    with multiprocessing.Pool(processes=2) as pool:
        results = pool.map(run_simulation, param_sets)
    # Print output directories
    for path in results:
        print("Simulation directory:", path)
```







