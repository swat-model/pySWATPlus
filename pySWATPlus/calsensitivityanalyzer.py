import numpy
import time
import functools
import typing
import concurrent.futures
from .types import CalParamsBoundedType, CalParamsType, CalParamBoundedModel
from .base_sensitivity_analyser import BaseSensitivityAnalyzer
import pathlib
from . import utils
from . import validators
from .txtinoutreader import TxtinoutReader


class CalSensitivityAnalyzer(BaseSensitivityAnalyzer):
    '''
    Provides functionality for running scenario simulations and analyzing simulated data.

    Warning:
        This class is currently under development and not recommended for use.

    '''
    @classmethod
    def _simulation_in_cpu(
        cls,
        track_sim: int,
        var_array: numpy.typing.NDArray[numpy.float64],
        num_sim: int,
        var_names: list[str],
        simulation_folder: pathlib.Path,
        txtinout_folder: pathlib.Path,
        params: list[CalParamBoundedModel],
        simulation_data: dict[str, dict[str, typing.Any]],
        clean_setup: bool
    ) -> dict[str, typing.Any]:
        '''
        Private function that runs a SWAT+ simulation asynchronously on a dedicated logical CPU.
        '''
        # variable dictionary
        var_dict = {
            var_names[i]: float(var_array[i]) for i in range(len(var_names))
        }

        # create 'params' dictionary with assigned value
        params_sim: CalParamsType = []

        for param in params:
            name = param.name
            change_type = param.change_type
            units = param.units
            unique_name = utils._make_unique_param_name(name, param)
            value = var_dict[unique_name]
            conditions = param.conditions
            params_sim.append({
                'name': name,
                'value': value,
                'change_type': change_type,
                'units': units,
                'conditions': conditions
            })

        dir_path, simulation_output = cls._setup_simulation_directory(
            track_sim=track_sim,
            num_sim=num_sim,
            var_array=var_array,
            simulation_folder=simulation_folder,
        )

        # Initialize TxtinoutReader class
        txtinout_reader = TxtinoutReader(
            path=txtinout_folder
        )

        # Run SWAT+ model in other directory
        txtinout_reader.cal_run_swat_in_other_dir(
            target_dir=dir_path,
            params=params_sim
        )

        # Extract simulated data
        simulation_output = cls._extract_simulation_data(
            dir_path=dir_path,
            simulation_data=simulation_data,
            simulation_output=simulation_output,
            clean_setup=clean_setup,
        )

        return simulation_output

    @classmethod
    def simulation_by_sobol_sample(
        cls,
        params: CalParamsBoundedType,
        sample_number: int,
        simulation_folder: str | pathlib.Path,
        txtinout_folder: str | pathlib.Path,
        simulation_data: dict[str, dict[str, typing.Any]],
        max_workers: typing.Optional[int] = None,
        save_output: bool = True,
        clean_setup: bool = True
    ) -> dict[str, typing.Any]:
        '''
        Provides a high-level interface for performing sensitivity simulations through parallel computing.

        It uses the method [`SALib.sample.sobol.sample`](https://salib.readthedocs.io/en/latest/api/SALib.sample.html#SALib.sample.sobol.sample),
        based on [`Sobol sequences`](https://doi.org/10.1016/S0378-4754(00)00270-6), to generate samples from the defined parameter space.

        For each sample, a dedicated directory is created, and a simulation is executed as a separate process using
        [`concurrent.futures.ProcessPoolExecutor`](https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor).
        Simulations are executed asynchronously, and to ensure computational efficiency, only unique samples are simulated.

        Each simulation directory is named `sim_<i>`, where `i` ranges from 1 to the number of unique simulations.
        Simulation results are collected by mapping input samples to their corresponding simulation directories.
        This mapping is then used to reorder the simulation outputs to match the original input samples.

        The method returns a detailed dictionary containing time statistics, the problem definition,
        the sample array, and the simulation results for further analysis.

        Args:

            params (CalParamsBoundedType):  Nested dictionary defining the parameter modifications to apply during the simulations.
                Each parameter should include a the lower and upper bounds, and the parameter value
                is dynamically assigned with the corresponding sampled value during execution.
                ```python
                params = {
                    "bf_max": [{
                        "change_type": "absval",
                        "lower_bound": 0.2,
                        "upper_bound": 0.3,
                        "units": range(1, 194)
                    }]
                }
                ```


            sample_number (int): sample_number (int): Determines the number of samples.
                Generates an array of length `2^N * (D + 1)`, where `D` is the number of parameter changes
                and `N = sample_number + 1`. For example, when `sample_number` is 1, 12 samples will be generated.

            simulation_folder (str | pathlib.Path): Path to the folder where individual simulations for each parameter set will be performed.
                Raises an error if the folder is not empty. This precaution helps prevent data deletion, overwriting directories,
                and issues with reading required data files not generated by the simulation.

            txtinout_folder (str | pathlib.Path): Path to the `TxtInOut` folder. Raises an error if the folder does not contain exactly one SWAT+ executable `.exe` file.

            simulation_data (dict[str, dict[str, typing.Any]]):  Nested dictionary that specifies how to extract data
                from SWAT+ simulation-generated files. The keys are filenames (without paths) of the output files.
                Each key must map to a non-empty dictionary with the following subkeys:

                - `has_units (bool)`: Mandatory subkey. If `True`, the third line of the simulated file contains units for the columns.
                - `start_date (str)`: Optional subkey in `YYYY-MM-DD` format. Defaults to the earliest date in the simulated file.
                - `end_date (str)`: Optional subkey in `YYYY-MM-DD` format. Defaults to the latest date in the simulated file.
                - `apply_filter (dict[str, list[typing.Any]])`: Optional subkey. Each key is a column name and the corresponding value
                  is a list of allowed values for filtering rows in the DataFrame. By default, no filtering is applied.
                  An error is raised if filtering produces an empty DataFrame.
                - `usecols (list[str])`: Optional subkey. List of columns to extract from the simulated file. By default, all available columns are used.

                ```python
                simulation_data = {
                    'channel_sd_mon.txt': {
                        'has_units': True,
                        'start_date': '2014-06-01',
                        'end_date': '2016-10-01',
                        'apply_filter': {'gis_id': [561], 'yr': [2015, 2016]},
                        'usecols': ['gis_id', 'flo_out']
                    },
                    'channel_sd_yr.txt': {
                        'has_units': True,
                        'apply_filter': {'name': ['cha561'], 'yr': [2015, 2016]},
                        'usecols': ['gis_id', 'flo_out']
                    }
                }
                ```

            max_workers (int): Number of logical CPUs to use for parallel processing.
                By default, all available logical CPUs are used.

            save_output (bool): If `True` (default), saves the output dictionary to `simulation_folder` as `sensitivity_simulation_sobol.json`.

            clean_setup (bool): If `True` (default), each folder created during the parallel simulation and its contents
                will be deleted dynamically after collecting the required data.

        Returns:
            A dictionary with the follwoing keys:

                - `time`: A dictionary A dictionary containing time-related statistics:

                    - `sample_length`: Total number of samples, including duplicates.
                    - `total_time_sec`: Total time in seconds for the simulation.
                    - `time_per_sample_sec`: Average simulation time per sample in seconds.

                - `problem`: The problem definition dictionary passed to `Sobol` sampling, containing:

                    - `num_vars`: Number of variables.
                    - `names`: Names of the variables.
                    - `bounds`: Lower and upper bounds for each variable.

                - `sample`: The sampled array of parameter sets used in the simulations.

                - `simulation`: Dictionary mapping simulation indices (integers from 1 to `sample_length`) to output sub-dictionaries with the following keys:

                    - `var`: Dictionary mapping each variable name (from `var_names`) to the actual value used in that simulation.
                    - `dir`: Name of the directory (e.g., `sim_<i>`) where the simulation was executed. This is useful when `clean_setup` is `False`, as it allows users
                      to verify whether the sampled values were correctly applied to the target files. The simulation index and directory name (e.g., `sim_<i>`)
                      may not always match one-to-one due to deduplication or asynchronous execution.
                    - `<simulation_data_filename>_df`: Filtered `DataFrame` generated for each file specified in the `simulation_data` dictionary
                      (e.g., `channel_sd_mon_df`, `channel_sd_yr_df`). Each DataFrame includes a `date` column with `datetime.date` objects.


        Note:
            - The `problem` dictionary and `sample` array are used later to calculate Sobol indices
              when comparing performance metrics against observed data.

            - The integer keys in the `simulation` dictionary may not correspond directly to the
              simulation directory indices (given by the `dir` key as `sim_<i>`) due to deduplication
              and asynchronous execution.

            - The computation progress can be tracked through the following `console` messages, where
              the simulation index ranges from 1 to the total number of unique simulations:

                - `Started simulation: <started_index>/<unique_simulations>`
                - `Completed simulation: <completed_index>/<unique_simulations>`

            - The disk space on the computer for `simulation_folder` must be sufficient to run
              parallel simulations (at least `max_workers` times the size of the `TxtInOut` folder).
              Otherwise, no error will be raised by the system, but simulation outputs may not be generated.
        '''

        # start time
        start_time = time.time()

        _txtinout_folder = utils._ensure_path(txtinout_folder)
        _simulation_folder = utils._ensure_path(simulation_folder)

        _params = [CalParamBoundedModel(**param) for param in params]
        validators._validate_cal_parameters(_txtinout_folder, _params)

        var_names = []
        var_bounds = []
        for param in _params:
            unique_name = utils._make_unique_param_name(param.name, param)
            var_names.append(unique_name)
            var_bounds.append([param.lower_bound, param.upper_bound])

        cls._validate_simulation_by_sobol_sample_params(
            simulation_folder=_simulation_folder,
            simulation_data=simulation_data,
            var_names=var_names,
            var_bounds=var_bounds
        )

        problem, sample_array, unique_array, num_sim = cls._prepare_sobol_samples(
            var_names=var_names,
            var_bounds=var_bounds,
            sample_number=sample_number
        )

        # Function for individual CPU simulation
        cpu_sim = functools.partial(
            cls._simulation_in_cpu,
            num_sim=num_sim,
            var_names=var_names,
            simulation_folder=_simulation_folder,
            txtinout_folder=_txtinout_folder,
            params=_params,
            simulation_data=simulation_data,
            clean_setup=clean_setup
        )

        # Assigning model simulation in individual computer CPU and collect results
        cpu_dict = {}
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Multicore simulation
            futures = [
                executor.submit(cpu_sim, idx, arr) for idx, arr in enumerate(unique_array, start=1)
            ]
            for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                # Message for completion of individual simulation for better tracking
                print(f'Completed simulation: {idx}/{num_sim}', flush=True)
                # collect simulation results
                idx_r = future.result()
                cpu_dict[tuple(idx_r['array'])] = {
                    k: v for k, v in idx_r.items() if k != 'array'
                }

        # Generate sensitivity simulation output for all sample_array from unique_array outputs
        output_dict = cls._collect_sobol_results(
            sample_array=sample_array,
            var_names=var_names,
            cpu_dict=cpu_dict,
            problem_dict=problem,
            start_time=start_time,
            simulation_folder=_simulation_folder,
            save_output=save_output
        )

        return output_dict
