import pandas
import numpy
import time
import functools
import SALib.sample.sobol
import typing
import os
import shutil
import json
import copy
import concurrent.futures
from .types import ParamsType
from .FileReader import FileReader
from .TxtinoutReader import TxtinoutReader
from . import utils


class Scenario:

    '''
    Provides functionality for running scenario simulations and analyzing simulated data.
    '''

    def simulated_timeseries_df(
        self,
        data_file: str,
        unit_row: bool = True,
        start_date: typing.Optional[str] = None,
        end_date: typing.Optional[str] = None,
        filter_rows: dict[str, list[typing.Any]] = {},
        retain_cols: typing.Optional[list[str]] = None
    ) -> pandas.DataFrame:
        '''
        Extracts data from an input file produced by a simulation and generates
        a time series `DataFrame` by constructing a new `date` column
        containing `datetime.date` objects created from the `yr`, `mon`, and `day` columns.

        Parameters:
            data_file (str): Path to the target file used to generate the time series `DataFrame`.
            unit_row (bool): If `True`, the third line of the input file contains units for the columns.
            start_date (str): Start date in `'yyyy-mm-dd'` format. By default,
                the earliest date available in the file is used.
            end_date (str): End date in `'yyyy-mm-dd'` format. By default,
                the latest date available in the file is used.
            filter_rows (dict[str, list[typing.Any]]): Dictionary where each key is a column name, and the
                corresponding value is a list of values used to filter the DataFrame. By default,
                no row filtering is applied.
            retain_cols (list[str]): List of column names to retain in the output `DataFrame`. By default,
                all columns from the input file are retained.

        Returns:
            A time series DataFrame with a new column (`date_col`) containing
                `datetime.date` objects created from the `yr`, `mon`, and `day` columns.
        '''

        # DataFrame from input file
        file_reader = FileReader(
            path=data_file,
            has_units=unit_row,
        )

        # check that dates are in correct format
        if start_date is not None:
            utils._validate_date_str(start_date)
        if end_date is not None:
            utils._validate_date_str(end_date)

        df = file_reader.df

        # Create date column
        date_col = 'date'
        df_cols = list(df.columns)

        time_cols = ['yr', 'mon', 'day']
        missing_cols = [col for col in time_cols if col not in df_cols]
        if len(missing_cols) > 0:
            raise ValueError(
                f'Missing required time series columns "{missing_cols}" in file "{os.path.basename(data_file)}"'
            )

        df[date_col] = pandas.to_datetime(
            df[['yr', 'mon', 'day']].rename(columns={'yr': 'year', 'mon': 'month', 'day': 'day'})
        ).dt.date

        # filter DataFrame by date
        start_do = pandas.to_datetime(start_date).date() if start_date else df[date_col].iloc[0]
        end_do = pandas.to_datetime(end_date).date() if end_date else df[date_col].iloc[-1]
        df = df.loc[df[date_col].between(start_do, end_do)].reset_index(drop=True)

        # Check if filtering by date removed all rows
        if df.empty:
            raise ValueError(
                f'No data available between {start_do} and {end_do} in file "{os.path.basename(data_file)}"'
            )

        # filter by row values
        for col, val in filter_rows.items():
            if col not in df_cols:
                raise ValueError(f'Column name "{col}" to filter rows is not valid')
            if not isinstance(val, list):
                raise ValueError(f'Filter values for column "{col}" must be provided as a list')
            df = df.loc[df[col].isin(val)].reset_index(drop=True)

        # DataFrame with selected columns
        if retain_cols is None:
            final_cols = [date_col] + [col for col in df.columns if col != date_col]
        else:
            final_cols = [date_col] + retain_cols

        df = df[final_cols]
        return df

    def _simulation_in_cpu(
        self,
        track_sim: int,
        var_array: numpy.typing.NDArray[numpy.float64],
        num_sim: int,
        var_names: list[str],
        simulation_folder: str,
        txtinout_folder: str,
        params: ParamsType,
        data_file: str,
        unit_row: bool,
        start_date: str | None,
        end_date: str | None,
        filter_rows: dict[str, list[typing.Any]],
        retain_cols: list[str] | None,
        clean_setup: bool
    ) -> dict[str, typing.Any]:
        '''
        Private function that runs a SWAT+ simulation asynchronously on a dedicated logical CPU.
        '''

        # variable dictionary
        var_dict = {
            var_names[i]: float(var_array[i]) for i in range(len(var_names))
        }

        # modify 'params' dictionary
        params_sim = copy.deepcopy(params)
        for file_name, file_dict in params_sim.items():
            # iterate entries for the file
            for file_key, file_value in file_dict.items():
                # skip loop for the has_units key with bool values
                if isinstance(file_value, bool):
                    continue
                # change dictionary to list if required
                change_list = file_value if isinstance(file_value, list) else [file_value]
                # iterate dictionary in change list
                for change_dict in change_list:
                    change_param = '|'.join([file_key, change_dict['filter_by']]) if 'filter_by' in change_dict else file_key
                    change_dict['value'] = var_dict[change_param]

        # Tracking simulation
        print(
            f'Started simulation: {track_sim}/{num_sim}',
            flush=True
        )

        # Create simulation directory
        dir_name = f'sim_{track_sim}'
        dir_path = os.path.join(simulation_folder, dir_name)
        os.makedirs(
            name=dir_path
        )

        # Initialize TxtinoutReader class
        txtinout_reader = TxtinoutReader(
            path=txtinout_folder
        )

        # Run SWAT+ model in other directory
        txtinout_reader.run_swat_in_other_dir(
            target_dir=dir_path,
            params=params_sim
        )

        # Extract simulated data
        df = self.simulated_timeseries_df(
            data_file=os.path.join(dir_path, data_file),
            unit_row=unit_row,
            start_date=start_date,
            end_date=end_date,
            filter_rows=filter_rows,
            retain_cols=retain_cols
        )

        # output
        output = {
            'dir': dir_name,
            'array': var_array,
            'df': df
        }

        # Remove simulation directory
        if clean_setup:
            shutil.rmtree(dir_path, ignore_errors=True)

        return output

    def simulation_by_sobol_sample(
        self,
        var_names: list[str],
        var_bounds: list[list[float]],
        sample_number: int,
        simulation_folder: str,
        txtinout_folder: str,
        params: ParamsType,
        data_file: str,
        unit_row: bool = True,
        start_date: typing.Optional[str] = None,
        end_date: typing.Optional[str] = None,
        filter_rows: dict[str, list[typing.Any]] = {},
        retain_cols: typing.Optional[list[str]] = None,
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
            var_names (list[str]): List of parameter names used for sensitivity analysis, corresponding to entries in the input `params` dictionary.
                If a parameter includes a `filter_by` condition, the name must be constructed as:

                `'|'.join([<parameter>, <parameter['filter_by']>])`.

                For the given `params` dictionary, the corresponding list is:
                ```python
                var_names = [
                    'esco',
                    '|'.join(['bm_e', 'name == "agrl"'])
                ]
                ```

            var_bounds (list[list[float]]): A list containing `[min, max]` bounds for each parameter in `var_names`, in the same order.
                ```python
                var_bounds = [
                    [0, 1],  # bounds for 'esco'
                    [30, 40]  # bounds 'bm_e | name == "agrl"'
                ]
                ```

            sample_number (int): sample_number (int): Determines the number of samples.
                Generates an array of length `2^N * (D + 1)`, where `D` is the length of `var_names`
                and `N = sample_number + 1`. For example, when `sample_number` is 1, 12 samples will be generated.

            simulation_folder (str): Path to the folder where individual simulations for each parameter set will be performed.
                Raises an error if the folder is not empty. This precaution helps prevent data deletion, overwriting directories,
                and issues with reading required data files not generated by the simulation.

            txtinout_folder (str): Path to the `TxtInOut` folder. Raises an error if the folder does not contain exactly one SWAT+ executable `.exe` file.

            params (ParamsType):  Nested dictionary defining the parameter modifications to apply during the simulations.
                Each parameter should include a default value (typically `0` or another `float`) to maintain a valid structure.
                Before each simulation, a deep copy (`copy.deepcopy(params)`) is made to ensure the original dictionary remains unchanged.
                The parameter value is dynamically replaced with the corresponding sampled value during execution.
                ```python
                params = {
                    'hydrology.hyd': {
                        'has_units': False,
                        'esco': {'value': 0}
                    },
                    'plants.plt': {
                        'has_units': False,
                        'bm_e': {'value': 0, 'filter_by': 'name == "agrl"'}
                    }
                }
                ```
            data_file (str): Path to the target file used to generate the time series `DataFrame`.

            unit_row (bool): If `True`, the third line of the input file contains units for the columns.

            start_date (str): Start date in `'yyyy-mm-dd'` format. By default, the earliest date available in the file is used.

            end_date (str): End date in `'yyyy-mm-dd'` format. By default, the latest date available in the file is used.

            filter_rows (dict[str, list[typing.Any]]): Dictionary where each key is a column name, and the
                corresponding value is a list of values used to filter the DataFrame. By default, no row filtering is applied.

            retain_cols (list[str]): List of column names to retain in the output `DataFrame`. By default,
                all columns from the input file are retained.

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

                - `simulation`: A dictionary mapping simulation indices (integers starting from 1 to `sample_length`) to output sub-dictionaries with the following keys:

                    - `var`: A dictionary mapping each variable name (from `var_names`) to the actual value used in the simulation.
                    - `dir`: Name of the directory (e.g., `sim_<i>`) where the simulation was performed. Useful when `clean_setup` is `False`,
                      allowing users to verify whether the sample values were correctly applied in the target files.
                      Note: The simulation index and directory name (e.g., `sim_<i>`) may not match one-to-one due to deduplication and asynchronous execution.
                    - `df`: The filtered `DataFrame` obtained from the `data_file`, including a `date` column.

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

        # Check simulation folder
        if not os.path.isdir(simulation_folder):
            raise NotADirectoryError('Provided simulation_folder is not a valid directory path')
        if len(os.listdir(simulation_folder)) > 0:
            raise ValueError('Provided simulation_folder must be an empty directory')

        # Check same length for number of variables and their bounds
        if len(var_names) != len(var_bounds):
            raise ValueError(
                f'Mismatch between number of variables ({len(var_names)}) and their bounds ({len(var_bounds)})'
            )

        # validate that params is correct
        utils._validate_params(params)

        # Counting and collecting sensitive parameters from 'params' dictionary for robust error checking
        count_params = 0
        collect_params = []
        for file_name, file_dict in params.items():
            # iterate entries for the file
            for file_key, file_value in file_dict.items():
                # skip loop for the has_units key with bool values
                if isinstance(file_value, bool):
                    continue
                # change dictionary to list if required
                change_list = file_value if isinstance(file_value, list) else [file_value]
                # update count parameters
                count_params = count_params + len(change_list)
                # iterate dictionary in change list
                for change_dict in change_list:
                    change_param = '|'.join([file_key, change_dict['filter_by']]) if 'filter_by' in change_dict else file_key
                    collect_params.append(change_param)

        # Check equality between number of variables and number of sensitivity parameters
        if len(var_names) != count_params:
            raise ValueError(
                f'Mismatch between number of variables ({len(var_names)}) and sensitivity parameters ({count_params})'
            )

        # Check that all sensitive parameters are included in variable names
        for p in collect_params:
            if p not in var_names:
                raise ValueError(
                    f'The var_names list does not contain the parameter "{p}" from the params dictionary'
                )

        # check file and parameter mapping in the 'params' dictionary
        for key, value in params.items():
            file_path = os.path.join(txtinout_folder, key)
            has_units = value['has_units']
            file_reader = FileReader(
                path=file_path,
                has_units=has_units
            )
            df = file_reader.df
            for p in value:
                if p == 'has_units':
                    continue
                if p not in list(df.columns):
                    raise Exception(f'Parameter "{p}" not found in columns of the file "{key}"')

        # problem definition
        problem = {
            'num_vars': len(var_names),
            'names': var_names,
            'bounds': var_bounds
        }

        # Copy problem dictionary to save later
        problem_dict = copy.deepcopy(problem)

        # Generate sample array
        sample_array = SALib.sample.sobol.sample(
            problem=problem_dict,
            N=pow(2, sample_number)
        )

        # Unique array to avoid duplicate computations
        unique_array = numpy.unique(
            ar=sample_array,
            axis=0
        )

        # Number of unique simulations
        num_sim = len(unique_array)

        # Function for individual CPU simulation
        cpu_sim = functools.partial(
            self._simulation_in_cpu,
            num_sim=num_sim,
            var_names=var_names,
            simulation_folder=simulation_folder,
            txtinout_folder=txtinout_folder,
            params=params,
            data_file=data_file,
            unit_row=unit_row,
            start_date=start_date,
            end_date=end_date,
            filter_rows=filter_rows,
            retain_cols=retain_cols,
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
                    'dir': idx_r['dir'],
                    'df': idx_r['df']
                }

        # Generate sensitivity simulation output for all sample_array from unique_array outputs
        sim_dict = {}
        for idx, arr in enumerate(sample_array, start=1):
            idx_dict = cpu_dict[tuple(arr)]
            sim_dict[idx] = {
                'var': {
                    k: float(v) for k, v in zip(var_names, arr)
                },
                'dir': idx_dict['dir'],
                'df': idx_dict['df']
            }

        # Time statistics
        required_time = time.time() - start_time
        time_stats = {
            'sample_length': len(sample_array),
            'total_time_sec': round(required_time),
            'time_per_sample_sec': round(required_time / len(sample_array), 1),
        }

        # output dictionary
        output_dict = {
            'time': time_stats,
            'problem': problem,
            'sample': sample_array,
            'simulation': sim_dict
        }

        # write dictionary
        if save_output:
            # Copy the output dictionary
            write_dict = copy.deepcopy(output_dict)
            for key, value in write_dict.items():
                # Formatting the 'sample' array
                if key == 'sample':
                    write_dict[key] = value.tolist()
                # Formatting the 'simulation' subdictionary
                if key == 'simulation':
                    for sub_key, sub_value in value.items():
                        for k, v in sub_value.items():
                            if k == 'df':
                                v['date'] = v['date'].astype(str)
                                write_dict[key][sub_key][k] = v.to_json()
            # Path to the JOSN file
            json_file = os.path.join(simulation_folder, 'sensitivity_simulation_sobol.json')
            # Write to the JSON file
            with open(json_file, 'w') as output_write:
                json.dump(write_dict, output_write, indent=4)

        # Remove simulation folders
        if clean_setup:
            for k, v in cpu_dict.items():
                v_folder = os.path.join(simulation_folder, v['dir'])
                if os.path.exists(v_folder):
                    shutil.rmtree(v_folder, ignore_errors=True)

        return output_dict
