import numpy
import SALib.sample.sobol
import SALib.analyze.sobol
import functools
import concurrent.futures
import pathlib
import typing
import time
import copy
import json
import shutil
import collections
from .txtinout_reader import TxtinoutReader
from .data_manager import DataManager
from .types import BoundType, BoundDict
from .performance_metrics import PerformanceMetrics
from . import validators


class SensitivityAnalyzer:
    '''
    Provide functionality for sensitivity analyzis.
    '''

    def _validate_extract_data_config(
        self,
        extract_data: dict[str, dict[str, typing.Any]],
    ) -> None:
        '''
        Validate `extract_data` configuration.
        '''

        valid_subkeys = [
            'has_units',
            'begin_date',
            'end_date',
            'ref_day',
            'ref_month',
            'apply_filter',
            'usecols'
        ]
        for sim_fname, sim_fdict in extract_data.items():
            if not isinstance(sim_fdict, dict):
                raise TypeError(
                    f'Expected "{sim_fname}" in simulation_date must be a dictionary, but got type "{type(sim_fdict).__name__}"'
                )
            if 'has_units' not in sim_fdict:
                raise KeyError(
                    f'Key has_units is missing for "{sim_fname}" in extract_data'
                )
            for sim_fkey in sim_fdict:
                if sim_fkey not in valid_subkeys:
                    raise ValueError(
                        f'Invalid key "{sim_fkey}" for "{sim_fname}" in extract_data; expected subkeys are {valid_subkeys}'
                    )

        return None

    def _create_sobol_problem(
        self,
        params_bounds: list[BoundDict]
    ) -> dict[str, typing.Any]:

        '''
        Prepare Sobol problem dictionary for sensitivity analysis.
        '''

        # Count variables
        count_vars = collections.Counter(
            p.name for p in params_bounds
        )

        # Intialize dictionary to keeps track the count of variables
        current_count = {
            v: 0 for v in list(count_vars)
        }

        # List of unique names and bounds of paramters
        var_names = []
        var_bounds = []
        for param in params_bounds:
            p_name = param.name
            if count_vars[p_name] == 1:
                # Keep same name if occur only once in the list
                var_names.append(p_name)
            else:
                # Add counter suffix if occur multiple times
                current_count[p_name] = current_count[p_name] + 1
                var_names.append(f'{p_name}|{current_count[p_name]}')
            var_bounds.append([param.lower_bound, param.upper_bound])

        # Sobol problem
        problem = {
            'num_vars': len(var_names),
            'names': var_names,
            'bounds': var_bounds
        }

        return problem

    def _cpu_simulation(
        self,
        track_sim: int,
        var_array: numpy.typing.NDArray[numpy.float64],
        num_sim: int,
        var_names: list[str],
        sensim_dir: pathlib.Path,
        txtinout_dir: pathlib.Path,
        params_bounds: list[BoundDict],
        extract_data: dict[str, dict[str, typing.Any]],
        clean_setup: bool
    ) -> dict[str, typing.Any]:
        '''
        Execute the simulation on a dedicated logical CPU.
        '''

        # Dictionary mapping for sensitivity simulation name and variable
        var_dict = {
            var_names[i]: float(var_array[i]) for i in range(len(var_names))
        }

        # Create ParameterType dictionary to write calibration.cal file
        params_sim = []
        for i, param in enumerate(params_bounds):
            params_sim.append(
                {
                    'name': param.name,
                    'change_type': param.change_type,
                    'value': var_dict[var_names[i]],
                    'units': param.units,
                    'conditions': param.conditions
                }
            )

        # Tracking simulation
        print(
            f'Started simulation: {track_sim}/{num_sim}',
            flush=True
        )

        # Create simulation directory
        cpu_dir = f'sim_{track_sim}'
        cpu_path = sensim_dir / cpu_dir
        cpu_path.mkdir()

        # Output simulation dictionary
        cpu_output = {
            'dir': cpu_dir,
            'array': var_array
        }

        # Initialize TxtinoutReader class
        txtinout_reader = TxtinoutReader(
            tio_dir=txtinout_dir
        )

        # Run SWAT+ model in CPU directory
        txtinout_reader.run_swat(
            sim_dir=cpu_path,
            parameters=params_sim
        )

        # Extract simulated data
        for sim_fname, sim_fdict in extract_data.items():
            sim_file = cpu_path / sim_fname
            df = DataManager().simulated_timeseries_df(
                sim_file=sim_file,
                **sim_fdict
            )
            cpu_output[f'{sim_file.stem}_df'] = df

        # Remove simulation directory
        if clean_setup:
            shutil.rmtree(cpu_path, ignore_errors=True)

        return cpu_output

    def _save_output_in_json(
        self,
        sensim_dir: pathlib.Path,
        sensim_output: dict[str, typing.Any]
    ) -> None:
        '''
        Write sensitivity simulation outputs to the file `sensitivity_simulation.json`
        within the `sensim_dir`.
        '''

        # copy the sensim_output dictionary
        copy_simulation = copy.deepcopy(
            x=sensim_output
        )

        # Modify the copied dictionary
        for key, value in copy_simulation.items():
            # Convert 'sample' array to list
            if key == 'sample':
                copy_simulation[key] = value.tolist()
            # Convert datetime.date objects to string in 'simulation' dictionary
            if key == 'simulation':
                for sub_key, sub_value in value.items():
                    for k, v in sub_value.items():
                        if k.endswith('_df'):
                            v['date'] = v['date'].apply(lambda x: x.strftime('%d-%b-%Y'))
                            copy_simulation[key][sub_key][k] = v.to_json()

        # Path to the JOSN file
        json_file = sensim_dir / 'sensitivity_simulation.json'

        # Write output to the JSON file
        with open(json_file, 'w') as output_write:
            json.dump(copy_simulation, output_write, indent=4)

        return None

    def simulation_by_sample_parameters(
        self,
        parameters: BoundType,
        sample_number: int,
        sensim_dir: str | pathlib.Path,
        txtinout_dir: str | pathlib.Path,
        extract_data: dict[str, dict[str, typing.Any]],
        max_workers: typing.Optional[int] = None,
        save_output: bool = True,
        clean_setup: bool = True
    ) -> dict[str, typing.Any]:
        '''
        Provide a high-level interface for performing sensitivity simulations through parallel computing.

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
            parameters (BoundType): List of dictionaries defining parameter configurations for sensitivity simulations.
                Each dictionary contain the following keys:

                - `name` (str): **Required.** Name of the parameter in the `cal_parms.cal` file.
                - `change_type` (str): **Required.** Type of change to apply. Must be one of 'absval', 'abschg', or 'pctchg'.
                - `lower_bound` (float): **Required.** Lower bound for the parameter.
                - `upper_bound` (float): **Required.** Upper bound for the parameter.
                - `units` (Iterable[int]): Optional. List of unit IDs to which the parameter change should be constrained.
                - `conditions` (dict[str, list[str]]): Optional. Conditions to apply when changing the parameter,
                  specified as a dictionary mapping condition types to lists of values.

                Example:
                    ```python
                    parameters = [
                        {
                            'name': 'cn2',
                            'change_type': 'pctchg',
                            'lower_bound': 25,
                            'upper_bound': 75,
                        },
                        {
                            'name': 'perco',
                            'change_type': 'absval',
                            'lower_bound': 0,
                            'upper_bound': 1,
                            'conditions': {'hsg': ['A']}
                        },
                        {
                            'name': 'bf_max',
                            'change_type': 'absval',
                            'lower_bound': 0.1,
                            'upper_bound': 2.0,
                            'units': range(1, 194)
                        }
                    ]
                    ```

            sample_number (int): sample_number (int): Determines the number of samples.
                Generates an array of length `2^N * (D + 1)`, where `D` is the number of parameter changes
                and `N = sample_number + 1`. For example, when `sample_number` is 1, 12 samples will be generated.

            sensim_dir (str | pathlib.Path): Path to the directory where individual simulations for each parameter set will be performed.
                Raises an error if the folder is not empty. This precaution helps prevent data deletion, overwriting directories,
                and issues with reading required data files not generated by the simulation.

            txtinout_dir (str | pathlib.Path): Path to the `TxtInOut` directory. Raises an error if the folder does not contain exactly one SWAT+ executable `.exe` file.

            extract_data (dict[str, dict[str, typing.Any]]): A nested dictionary specifying how to extract data from SWAT+ simulation output files.
                The top-level keys are filenames of the output files, without paths (e.g., `channel_sd_day.txt`). Each key must map to a non-empty dictionary
                containing the following subkeys, as defined in [`simulated_timeseries_df`](https://swat-model.github.io/pySWATPlus/api/data_manager/#pySWATPlus.DataManager.simulated_timeseries_df):

                - `has_units` (bool): **Required.** If `True`, the third line of the simulated file contains units for the columns.
                - `begin_date` (str): Optional. Start date in `DD-Mon-YYYY` format (e.g., 01-Jan-2010). Defaults to the earliest date in the simulated file.
                - `end_date` (str): Optional. End date in `DD-Mon-YYYY` format (e.g., 31-Dec-2013). Defaults to the latest date in the simulated file.
                - `ref_day` (int): Optional. Reference day for monthly and yearly time series.
                   If `None` (default), the last day of the month or year is used, obtained from simulation. Not applicable to daily time series files (ending with `_day`).
                - `ref_month` (int): Optional. Reference month for yearly time series. If `None` (default), the last month of the year is used, obtained from simulation.
                  Not applicable to monthly time series files (ending with `_mon`).
                - `apply_filter` (dict[str, list[typing.Any]]): Optional. Each key is a column name and the corresponding value
                  is a list of allowed values for filtering rows in the DataFrame. By default, no filtering is applied.
                  An error is raised if filtering produces an empty DataFrame.
                - `usecols` (list[str]): Optional. List of columns to extract from the simulated file. By default, all available columns are used.

                ```python
                extract_data = {
                    'channel_sd_mon.txt': {
                        'has_units': True,
                        'begin_date': '01-Jun-2014',
                        'end_date': '01-Oct-2016',
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

            max_workers (int): Number of logical CPUs to use for parallel processing. If `None` (default), all available logical CPUs are used.

            save_output (bool): If `True` (default), saves the output dictionary to `sensim_dir` as `sensitivity_simulation.json`.

            clean_setup (bool): If `True` (default), each folder created during the parallel simulation and its contents
                will be deleted dynamically after collecting the required data.

        Returns:
            A dictionary with the follwoing keys:

                - `time`: A dictionary containing time-related statistics:

                    - `sample_length`: Total number of samples, including duplicates.
                    - `total_time_sec`: Total time in seconds for the simulation.
                    - `time_per_sample_sec`: Average simulation time per sample in seconds.

                - `problem`: The problem definition dictionary passed to `Sobol` sampling, containing:

                    - `num_vars`: Total number of variables in `parameters`.
                    - `names`: Variable names derived from the `name` field of each dictionary in `parameters`. If a parameter appears multiple times
                      due to different `units` or `conditions`, occurrences are suffixed with a counter (e.g., `perco|1`, `perco|2`).
                    - `bounds`:  A list of [`lower_bound`, `upper_bound`] pairs corresponding to each dictionary in `parameters`.

                - `sample`: The sampled array of parameter sets used in the simulations.

                - `simulation`: Dictionary mapping simulation indices (integers from 1 to `sample_length`) to output sub-dictionaries with the following keys:

                    - `var`: Dictionary mapping each variable name (from `var_names`) to the actual value used in that simulation.
                    - `dir`: Name of the directory (e.g., `sim_<i>`) where the simulation was executed. This is useful when `clean_setup` is `False`, as it allows users
                      to verify whether the sampled values were correctly applied to the target files. The simulation index and directory name (e.g., `sim_<i>`)
                      may not always match one-to-one due to deduplication or asynchronous execution.
                    - `<extract_data_filename>_df`: Filtered `DataFrame` generated for each file specified in the `extract_data` dictionary
                      (e.g., `channel_sd_mon_df`, `channel_sd_yr_df`). Each DataFrame includes a `date` column with `datetime.date` objects.

        Note:
            - The `problem` dictionary and `sample` array are used later to calculate Sobol indices
              when comparing performance metrics against observed data.

            - The integer keys in the `simulation` dictionary may not correspond directly to the
              simulation directory indices (given by the `dir` key as `sim_<i>`) due to deduplication
              and asynchronous execution.

            - The output dictionary contains `datetime.date` objects in the `date` column for each `DataFrame` in the `simulation` dictionary.
              These `datetime.date` objects are converted to `DD-Mon-YYYY` strings when saving the output dictionary to
              `sensitivity_simulation.json` within the `sensim_dir`.

            - The computation progress can be tracked through the following `console` messages, where
              the simulation index ranges from 1 to the total number of unique simulations:

                - `Started simulation: <started_index>/<unique_simulations>`
                - `Completed simulation: <completed_index>/<unique_simulations>`

            - The disk space on the computer for `sensim_dir` must be sufficient to run
              parallel simulations (at least `max_workers` times the size of the `TxtInOut` folder).
              Otherwise, no error will be raised by the system, but simulation outputs may not be generated.
        '''

        # start time
        start_time = time.time()

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.simulation_by_sample_parameters
            ),
            vars_values=locals()
        )

        # Absolute path
        txtinout_dir = pathlib.Path(txtinout_dir).resolve()
        sensim_dir = pathlib.Path(sensim_dir).resolve()

        # Check validity of directory path
        validators._dir_path(
            input_dir=txtinout_dir
        )
        validators._dir_path(
            input_dir=sensim_dir
        )

        # Check sensim_dir is empty
        validators._dir_empty(
            input_dir=sensim_dir
        )

        # Validate extract_data configuration
        self._validate_extract_data_config(
            extract_data=extract_data
        )

        # Validate unique dictionaries for parameters
        validators._calibration_list_contain_unique_dict(
            parameters=parameters
        )

        # Validate input keys in dictionaries for sensitive parameters
        params_bounds = [
            BoundDict(**param) for param in parameters
        ]
        validators._calibration_parameters(
            input_dir=txtinout_dir,
            parameters=params_bounds
        )

        # problem dictionary
        problem = self._create_sobol_problem(
            params_bounds=params_bounds
        )
        copy_problem = copy.deepcopy(
            x=problem
        )

        # Generate sample array
        sample_array = SALib.sample.sobol.sample(
            problem=copy_problem,
            N=pow(2, sample_number)
        )

        # Unique array to avoid duplicate computations
        unique_array = numpy.unique(
            ar=sample_array,
            axis=0
        )

        # Number of unique simulations
        num_sim = len(unique_array)

        # Sensitivity simulation in separate CPU
        cpu_sim = functools.partial(
            self._cpu_simulation,
            num_sim=num_sim,
            var_names=copy_problem['names'],
            sensim_dir=sensim_dir,
            txtinout_dir=txtinout_dir,
            params_bounds=params_bounds,
            extract_data=extract_data,
            clean_setup=clean_setup
        )

        # Assign model simulation in individual computer CPU and collect results
        cpu_dict = {}
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Multicore simulation
            futures = [
                executor.submit(cpu_sim, idx, arr) for idx, arr in enumerate(unique_array, start=1)
            ]
            for future in concurrent.futures.as_completed(futures):
                # Message for completion of individual simulation for better tracking
                print(f'Completed simulation: {futures.index(future) + 1}/{num_sim}', flush=True)
                # Collect simulation results
                f_r = future.result()
                cpu_dict[tuple(f_r['array'])] = {
                    k: v for k, v in f_r.items() if k != 'array'
                }

        # Generate sensitivity simulation output for all sample_array from unique_array outputs
        sim_dict = {}
        for idx, arr in enumerate(sample_array, start=1):
            arr_dict = {
                k: float(v) for k, v in zip(copy_problem['names'], arr)
            }
            sim_dict[idx] = {
                'var': arr_dict
            }
            # Create a deep copy of the dictionary so changes do not affect other copies
            idx_dict = copy.deepcopy(
                x=cpu_dict[tuple(arr)]
            )
            for k, v in idx_dict.items():
                sim_dict[idx][k] = v

        # Time statistics
        required_time = time.time() - start_time
        time_stats = {
            'sample_length': len(sample_array),
            'total_time_sec': round(required_time),
            'time_per_sample_sec': round(required_time / len(sample_array), 1),
        }

        # Sensitivity simulaton output
        sensim_output = {
            'time': time_stats,
            'problem': problem,
            'sample': sample_array,
            'simulation': sim_dict
        }

        # Write output to the file 'sensitivity_simulation.json' in simulation folder
        if save_output:
            self._save_output_in_json(
                sensim_dir=sensim_dir,
                sensim_output=sensim_output
            )

        return sensim_output

    def parameter_sensitivity_indices(
        self,
        sensim_file: str | pathlib.Path,
        df_name: str,
        sim_col: str,
        obs_file: str | pathlib.Path,
        date_format: str,
        obs_col: str,
        indicators: list[str],
        json_file: typing.Optional[str | pathlib.Path] = None
    ) -> dict[str, typing.Any]:
        '''
        Compute parameter sensitivy indices for sample scenarios obtained using
        the [`simulation_by_sample_parameters`](https://swat-model.github.io/pySWATPlus/api/sensitivity_analyzer/#pySWATPlus.SensitivityAnalyzer.simulation_by_sample_parameters) method.

        The method returns a dictionary with two keys:

        - `problem`: The definition dictionary passed to sampling.
        - `sensitivty_indices`: A dictionary where each key is an indicator name and the corresponding value is the computed sensitivity indices.

        Args:
            sensim_file (str | pathlib.Path): Path to the `sensitivity_simulation.json` file produced by `simulation_by_sample_parameters`.

            df_name (str): Name of the `DataFrame` within `sensitivity_simulation.json` from which to compute scenario indicators.

            sim_col (str): Name of the column in `df_name` containing simulated values.

            obs_file (str | pathlib.Path): Path to the CSV file containing observed data. The file must include a
                `date` column (used to merge simulated and observed data) and use a comma as the separator.

            date_format (str): Date format of the `date` column in `obs_file`, used to parse `datetime.date` objects from date strings.

            obs_col (str): Name of the column in `obs_file` containing observed data. All negative and `None` observed values are removed before analysis.

            indicators (list[str]): List of indicators to compute sensitivity indices. Available options:

                - `NSE`: Nash–Sutcliffe Efficiency
                - `KGE`: Kling–Gupta Efficiency
                - `MSE`: Mean Squared Error
                - `RMSE`: Root Mean Squared Error
                - `PBIAS`: Percent Bias
                - `MARE`: Mean Absolute Relative Error

            json_file (str | pathlib.Path, optional): Path to a JSON file for saving the output dictionary where each key is an indicator name
                and the corresponding value is the computed sensitivity indices. If `None` (default), the dictionary is not saved.

        Returns:
            Dictionary with two keys, `problem` and `sensitivity_indices`, and their corresponding values.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.parameter_sensitivity_indices
            ),
            vars_values=locals()
        )

        # Problem and indicators
        prob_inct = PerformanceMetrics().scenario_indicators(
            sensim_file=sensim_file,
            df_name=df_name,
            sim_col=sim_col,
            obs_file=obs_file,
            date_format=date_format,
            obs_col=obs_col,
            indicators=indicators
        )
        problem = prob_inct['problem']
        indicator_df = prob_inct['indicator']

        # Sensitivity indices
        sensitivity_indices = {}
        for indicator in indicators:
            # Indicator sensitivity indices
            indicator_sensitivity = SALib.analyze.sobol.analyze(
                problem=copy.deepcopy(problem),
                Y=indicator_df[indicator].values
            )
            sensitivity_indices[indicator] = indicator_sensitivity

        # Save the sensitivity indices
        if json_file is not None:
            # Raise error for invalid JSON file extension
            json_file = pathlib.Path(json_file).resolve()
            validators._json_extension(
                json_file=json_file
            )
            # Modify sensitivity index to write in the JSON file
            copy_indices = copy.deepcopy(sensitivity_indices)
            write_indices = {}
            for indicator in indicators:
                write_indices[indicator] = {
                    k: v.tolist() for k, v in copy_indices[indicator].items()
                }
            # saving output data
            with open(json_file, 'w') as output_json:
                json.dump(write_indices, output_json, indent=4)

        # Output dictionary
        output = {
            'problem': problem,
            'sensitivity_indices': sensitivity_indices
        }

        return output
