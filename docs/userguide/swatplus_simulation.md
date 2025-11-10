# SWAT+ Simulation

`pySWATPlus` executes [SWAT+](https://swat.tamu.edu/software/plus/) simulations using the `TxtInOut` folder generated during project creation with [QSWAT+](https://github.com/swat-model/QSWATPlus).

To run a `SWAT+` simulation, the `TxtInOut` folder must include all required input files, which are created during simulation setup in the [SWAT+ Editor](https://github.com/swat-model/swatplus-editor) via `QSWAT+`.

Additionally, the `TxtInOut` folder must contain the `SWAT+` executable. The executable file compatible with your operating system and `SWAT+` version can be obtained from the [official GitHub releases](https://github.com/swat-model/swatplus/releases).

Once the `TxtInOut` folder is properly configured with the necessary input files and the `SWAT+` executable, you can initialize the `TxtinoutReader` class to interact with the `SWAT+` model:

```python
import pySWATPlus

# Replace this with the path to your project's TxtInOut folder
txtinout_dir = r"C:\Users\Username\project\Scenarios\Default\TxtInOut"

# Initialize TxtinoutReader class
txtinout_reader = pySWATPlus.TxtinoutReader(
    tio_dir=txtinout_dir
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
    sim_dir = r"C:\Users\Username\custom_folder" 

    # Ensure the required files are copied to the custom directory
    txtinout_reader.copy_required_files(
        sim_dir=sim_dir
    )
    ```

- Initialize `TxtinoutReader` class for the custom directory

    ```python
    sim_reader = pySWATPlus.TxtinoutReader(
        tio_dir=sim_dir
    )
    ```
    
- Run simulation

    ```python
    sim_reader.run_swat()
    ```

## Step-wise Configurations and Simulations


The following steps demonstrate how to configure parameters in a custom directory and run a simulation step by step:


- Modify simulation timeline:

    ```python
    # Update timeline in `time.sim` file
    sim_reader.set_simulation_period(
        begin_date='01-Jan-2012',
        end_date='31-Dec-2016'
    )
    ```

- Set warm-up years:

    ```python
    # Set warm-up years in `print.prt` file
    sim_reader.set_warmup_year(
        warmup=1
    )
    ```

- Enable required simulation files:

    ```python
    # Ensure simulation outputs for `channel_sd` object in `print.prt` file  
    sim_reader.enable_object_in_print_prt(
        obj='channel_sd',
        daily=False,
        monthly=True,
        yearly=True,
        avann=True,
    )
    ```
    
- Set print interval within the simulation period:

    ```python
    # Set print interval in `print.prt` file
    sim_reader.set_print_interval(
        interval=1
    )
    ```
    
- Set print period within the simulation timeline to record result in output files:

    ```python
    # Set print period in `print.prt` file  
    sim_reader.set_print_period(
        begin_date='15-Jun-2012',
        end_date='15-Jun-2016'
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
    sim_reader.run_swat(
        parameters=parameters
    )
    ```


## Configurable Simulations in a Single Function

Instead of performing each step separately as explained above, you can run a `SWAT+` simulation in a separate empty directory by configuring all options at once using a single function:

```python
# Run SWAT+ simulation to a custom directory
txtinout_reader.run_swat(
    sim_dir=r"C:\Users\Username\empty_folder",  # directory (optional)
    parameters=[
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
    ],  # modified parameter value (optional)
    begin_date='01-Jan-2012',  # simulation begin date (optional)
    end_date= '31-Dec-2016',  # simulation end date (optional)
    simulation_timestep=0,  # simulation time step (optional)
    warmup=1,  # warm-up years (optional)
    print_prt_control={
        'channel_sd': {'daily': False}
    },  # control print.prt file (optional)
    print_begin_date='15-Jun-2012',  # begin date to print output (optional)
    print_end_date='15-Jun-2016',  # end date to print output (optional)
    print_interval=1  # interval to print output (optional)
)
```
