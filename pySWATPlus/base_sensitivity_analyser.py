import pandas
import typing
from .filereader import FileReader
from . import utils
from abc import ABC, abstractmethod
import numpy
import SALib.sample.sobol
import copy
import time
import json
import shutil
import pathlib
from . import validators


class BaseSensitivityAnalyzer(ABC):
    '''
    Provides functionality for running scenario simulations and analyzing simulated data.
    '''
    @staticmethod
    def simulated_timeseries_df(
        data_file: str | pathlib.Path,
        has_units: bool,
        start_date: typing.Optional[str] = None,
        end_date: typing.Optional[str] = None,
        apply_filter: typing.Optional[dict[str, list[typing.Any]]] = None,
        usecols: typing.Optional[list[str]] = None,
        save_df: bool = False,
        json_file: typing.Optional[str] = None
    ) -> pandas.DataFrame:
        '''
        Extracts data from an input file produced by a simulation and generates
        a time series `DataFrame` by constructing a new `date` column
        containing `datetime.date` objects created from the `yr`, `mon`, and `day` columns.

        Parameters:
            data_file (str | pathlib.Path): Path to the target file used to generate the time series `DataFrame`.
            has_units (bool): If `True`, the third line of the input file contains units for the columns.
            start_date (str): Start date in `'yyyy-mm-dd'` format. If `None` (default),
                the earliest date available in the file is used.
            end_date (str): End date in `'yyyy-mm-dd'` format. If `None` (default),
                the latest date available in the file is used.
            apply_filter (dict[str, list[typing.Any]]): Dictionary where each key is a column name, and the
                corresponding value is a list of values used to filter rows in the DataFrame. If `None` (default),
                no filtering is applied.
            usecols (list[str]): List of column names to use in the output `DataFrame`. If `None` (default),
                all columns from the input file are used.
            save_df (bool): If True, saves the `DataFrame` to a JSON file. Default is False.
            json_file (str): Path to save the `DataFrame` when `save_df=True`. Default is `None`.

        Returns:
            A time series DataFrame with a new column (`date_col`) containing
                `datetime.date` objects created from the `yr`, `mon`, and `day` columns.
        '''

        _data_file = utils._ensure_path(data_file)

        # DataFrame from input file
        file_reader = FileReader(
            path=_data_file,
            has_units=has_units
        )

        # check that dates are in correct format
        if start_date is not None:
            validators._validate_date_str(start_date)
        if end_date is not None:
            validators._validate_date_str(end_date)

        # DataFrame
        df = file_reader.df
        df_cols = list(df.columns)

        # Create date column
        date_col = 'date'
        time_cols = ['yr', 'mon', 'day']
        missing_cols = [col for col in time_cols if col not in df_cols]
        if len(missing_cols) > 0:
            raise ValueError(
                f'Missing required time series columns "{missing_cols}" in file "{_data_file.name}"'
            )
        df[date_col] = pandas.to_datetime(
            df[time_cols].rename(columns={'yr': 'year', 'mon': 'month'})
        ).dt.date

        # filter DataFrame by date
        start_do = pandas.to_datetime(start_date).date() if start_date else df[date_col].iloc[0]
        end_do = pandas.to_datetime(end_date).date() if end_date else df[date_col].iloc[-1]
        df = df.loc[df[date_col].between(start_do, end_do)].reset_index(drop=True)

        # Check if filtering by date removed all rows
        if df.empty:
            raise ValueError(
                f'No data available between "{start_date}" and "{end_date}" in file "{_data_file.name}"'
            )

        # Filter rows by dictionary criteria
        if apply_filter is not None:
            for col, val in apply_filter.items():
                if col not in df_cols:
                    raise ValueError(
                        f'Column "{col}" in apply_filter is not present in file "{_data_file.name}"'
                    )
                if not isinstance(val, list):
                    raise ValueError(
                        f'Filter values for column "{col}" must be a list in file "{_data_file.name}"'
                    )
                df = df.loc[df[col].isin(val)]
                # Check if filtering removed all rows
                if df.empty:
                    raise ValueError(
                        f'Filtering by column "{col}" with values "{val}" removed all rows from file "{_data_file.name}"'
                    )

        # Reset DataFrame index
        df.reset_index(
            drop=True,
            inplace=True
        )

        # Finalize columns for DataFrame
        if usecols is None:
            retain_cols = [date_col] + df_cols
        else:
            if not isinstance(usecols, list):
                raise TypeError(f'"usecols" must be a list, got {type(usecols).__name__}')
            for col in usecols:
                if col not in df_cols:
                    raise ValueError(
                        f'Column "{col}" in usecols list is not present in file "{_data_file.name}"'
                    )
            retain_cols = [date_col] + usecols

        # Output DataFrame
        df = df[retain_cols]

        # Write output
        if save_df:
            if json_file is None:
                raise ValueError('json_file must be a valid JSON file string path when save_df=True')
            df['date'] = df['date'].astype(str)
            df.to_json(
                path_or_buf=json_file,
                orient="records",
                lines=True
            )

        return df

    @classmethod
    @abstractmethod
    def simulation_by_sobol_sample(
        cls,
        params: typing.Any,
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
        '''
        pass

    @staticmethod
    def _validate_simulation_by_sobol_sample_params(
        simulation_folder: pathlib.Path,
        simulation_data: dict[str, dict[str, typing.Any]],
        var_names: list[str],
        var_bounds: list[list[float]],
    ) -> None:
        '''
        Validate parameters for the Sobol sampling simulation.
        '''
        # Check simulation folder
        if not simulation_folder.is_dir():
            raise NotADirectoryError('Provided simulation_folder is not a valid directory path')
        if any(simulation_folder.iterdir()):
            raise ValueError('Provided simulation_folder must be an empty directory')

        # check simulation data dictionary
        if not isinstance(simulation_data, dict):
            raise TypeError(
                f'simulation_data must be a dictionary type, got {type(simulation_data).__name__}'
            )
        sim_validkeys = [
            'start_date',
            'end_date',
            'apply_filter',
            'usecols'
        ]
        for sim_fname, sim_fdict in simulation_data.items():
            if not isinstance(sim_fdict, dict):
                raise TypeError(
                    f'Value for key "{sim_fname}" in simulation_data must be a dictinary type, got {type(sim_fdict).__name__}'
                )
            if 'has_units' not in sim_fdict:
                raise KeyError(
                    f'key has_units is missing for "{sim_fname}" in simulation_data'
                )
            for sim_fkey in sim_fdict:
                if sim_fkey == 'has_units':
                    continue
                if sim_fkey not in sim_validkeys:
                    raise ValueError(
                        f'Invalid key "{sim_fkey}" for "{sim_fname}" in simulation_data. Expected one of: {sim_validkeys}'
                    )

        # Check same length for number of variables and their bounds
        if len(var_names) != len(var_bounds):
            raise ValueError(
                f'Mismatch between number of variables ({len(var_names)}) and their bounds ({len(var_bounds)})'
            )

    @staticmethod
    def _prepare_sobol_samples(
        var_names: list[str],
        var_bounds: list[list[float]],
        sample_number: int
    ) -> tuple[dict[str, typing.Any], numpy.ndarray, numpy.ndarray, int]:
        '''
        Prepare Sobol samples for sensitivity analysis.
        '''
        # Problem definition
        problem = {
            "num_vars": len(var_names),
            "names": var_names,
            "bounds": var_bounds
        }

        # Copy for reproducibility
        problem_dict = copy.deepcopy(problem)

        # Generate Sobol samples
        sample_array = SALib.sample.sobol.sample(problem_dict, N=2**sample_number)

        # Remove duplicate samples
        unique_array = numpy.unique(sample_array, axis=0)

        # Number of unique simulations
        num_sim = len(unique_array)

        return problem, sample_array, unique_array, num_sim

    @staticmethod
    def _collect_sobol_results(
        sample_array: numpy.ndarray,
        var_names: list[str],
        cpu_dict: dict[tuple[float, ...], dict[str, typing.Any]],
        problem_dict: dict[str, typing.Any],
        start_time: float,
        simulation_folder: pathlib.Path,
        save_output: bool = False
    ) -> dict[str, typing.Any]:
        """
        Collect and format Sobol sensitivity simulation results.
        """
        # Build simulation dictionary
        sim_dict = {}
        for idx, arr in enumerate(sample_array, start=1):
            arr_dict = {k: float(v) for k, v in zip(var_names, arr)}
            sim_dict[idx] = {"var": arr_dict}
            sim_dict[idx].update(cpu_dict[tuple(arr)])

        # Compute time statistics
        required_time = time.time() - start_time
        time_stats = {
            "sample_length": len(sample_array),
            "total_time_sec": round(required_time),
            "time_per_sample_sec": round(required_time / len(sample_array), 1),
        }

        # Full output dictionary
        output_dict = {
            "time": time_stats,
            "problem": problem_dict,
            "sample": sample_array,
            "simulation": sim_dict,
        }

        # Save to JSON if requested
        if save_output:
            write_dict = copy.deepcopy(output_dict)

            # Handle "sample" key
            if "sample" in write_dict:
                sample = write_dict["sample"]
                if isinstance(sample, numpy.ndarray):
                    write_dict["sample"] = sample.tolist()

            # Handle "simulation" key with DataFrames
            if "simulation" in write_dict:
                simulation = write_dict["simulation"]
                if isinstance(simulation, dict):
                    for sub_key, sub_value in simulation.items():
                        if isinstance(sub_value, dict):
                            for k, v in sub_value.items():
                                if k.endswith("_df"):
                                    v["date"] = v["date"].astype(str)
                                    sub_value[k] = v.to_json()

            json_file = simulation_folder / "sensitivity_simulation_sobol.json"
            with open(json_file, "w") as output_write:
                json.dump(write_dict, output_write, indent=4)

        return output_dict

    @staticmethod
    def _setup_simulation_directory(
        track_sim: int,
        num_sim: int,
        var_array: numpy.ndarray,
        simulation_folder: pathlib.Path
    ) -> tuple[pathlib.Path, dict[str, typing.Any]]:
        '''
        Creates a simulation directory and returns its path + initial simulation_output dict.
        '''
        # Tracking simulation
        print(f"Started simulation: {track_sim}/{num_sim}", flush=True)

        # Create simulation directory
        dir_name = f"sim_{track_sim}"
        dir_path = simulation_folder / dir_name
        dir_path.mkdir(exist_ok=True)

        # Output simulation dictionary
        simulation_output: dict[str, typing.Any] = {
            "dir": dir_name,
            "array": var_array,
        }

        return dir_path, simulation_output

    @classmethod
    def _extract_simulation_data(
        cls,
        dir_path: pathlib.Path,
        simulation_data: dict[str, dict[str, typing.Any]],
        simulation_output: dict[str, typing.Any],
        clean_setup: bool
    ) -> dict[str, typing.Any]:
        """
        Extracts simulated data into `simulation_output` and cleans up the simulation directory.
        """
        # Extract simulated data
        for sim_fname, sim_fdict in simulation_data.items():
            df = cls.simulated_timeseries_df(
                data_file=dir_path / sim_fname,
                **sim_fdict,
            )
            sim_path = pathlib.Path(sim_fname)
            simulation_output[f"{sim_path.stem}_df"] = df

        # Remove simulation directory
        if clean_setup:
            shutil.rmtree(dir_path, ignore_errors=True)

        return simulation_output
