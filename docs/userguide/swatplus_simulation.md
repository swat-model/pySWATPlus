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


## Trial Simulation

This simple example runs a `SWAT+` simulation without changing any input parameters, ensuring that the setup works correctly:


```python
txtinout_reader.run_swat()
```

## Simulation in a Custom Directory

To keep your original `TxtInOut` folder unchanged, it is recommended to run `SWAT+` simulations in a separate empty directory. This allows you to perform experiments without affecting your main project. The following steps demonstrate how to perform a simulation in a custom directory:


- Copy required files to the custom directory:

    ```python
    # Replace this with your desired empty custom directory
    target_dir = r"C:\Users\Username\custom_folder" 

    # Ensure the required files are copied to the custom directory
    txtinout_reader.copy_required_files(
        target_dir=target_dir
    )
    ```

- Initialize `TxtinoutReader` class for the custom directory

    ```python
    target_reader = pySWATPlus.TxtinoutReader(
        path=target_dir
    )
    ```
    
- Run simulation

    ```python
    target_reader.run_swat()
    ```

## Step-wise Configurations and Simulations


The following steps demonstrate how to configure parameters in a custom directory and run a simulation step by step:


- Modify simulation timeline:

    ```python
    # Update timeline in `time.sim` file
    target_reader.set_simulation_period(
        begin_date='01-Jan-2012',
        end_date='31-Dec-2016',
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
    
- Run the SWAT+ simulation with a modified `esco` parameter:

    ```python
    parameters = [
        {
            'name': 'esco',
            'change_type': 'absval',
            'value': 0.5
        }
    ]
    target_reader.run_swat(
        parameters=parameters
    )
    ```


## Configurable Simulations in a Single Function

Instead of performing each step separately as explained above, you can run a `SWAT+` simulation in a separate empty directory by configuring all options at once using a single function:

```python
# Configure modified parameters
parameters = [
    {
        'name': 'esco',
        'change_type': 'absval',
        'value': 0.3
    },
    {
        'name': 'perco',
        'change_type': 'absval',
        'value': 0.6
    }
]

# Run SWAT+ simulation from the original `TxtInOut` folder
txtinout_reader.run_swat(
    target_dir=r"C:\Users\Username\custom_folder",  # mandatory
    parameters=parameters,  # optional
    begin_date='01-Jan-2012', # optional
    end_date= '31-Dec-2016', # optional
    warmup=1,  # optional
    print_prt_control={'channel_sd': {'daily': False}}  # optional
)
```

