import pandas
import typing
import os
from .filereader import FileReader
from . import utils
from abc import ABC, abstractmethod


class BaseSensitivityAnalyzer(ABC):
    '''
    Provides functionality for running scenario simulations and analyzing simulated data.
    '''
    @staticmethod
    def simulated_timeseries_df(
        data_file: str,
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
            data_file (str): Path to the target file used to generate the time series `DataFrame`.
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

        # DataFrame from input file
        file_reader = FileReader(
            path=data_file,
            has_units=has_units
        )

        # check that dates are in correct format
        if start_date is not None:
            utils._validate_date_str(start_date)
        if end_date is not None:
            utils._validate_date_str(end_date)

        # DataFrame
        df = file_reader.df
        df_cols = list(df.columns)

        # Create date column
        date_col = 'date'
        time_cols = ['yr', 'mon', 'day']
        missing_cols = [col for col in time_cols if col not in df_cols]
        if len(missing_cols) > 0:
            raise ValueError(
                f'Missing required time series columns "{missing_cols}" in file "{os.path.basename(data_file)}"'
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
                f'No data available between "{start_date}" and "{end_date}" in file "{os.path.basename(data_file)}"'
            )

        # Filter rows by dictionary criteria
        if apply_filter is not None:
            for col, val in apply_filter.items():
                if col not in df_cols:
                    raise ValueError(
                        f'Column "{col}" in apply_filter is not present in file "{os.path.basename(data_file)}"'
                    )
                if not isinstance(val, list):
                    raise ValueError(
                        f'Filter values for column "{col}" must be a list in file "{os.path.basename(data_file)}"'
                    )
                df = df.loc[df[col].isin(val)]
                # Check if filtering removed all rows
                if df.empty:
                    raise ValueError(
                        f'Filtering by column "{col}" with values "{val}" removed all rows from file "{os.path.basename(data_file)}"'
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
                        f'Column "{col}" in usecols list is not present in file "{os.path.basename(data_file)}"'
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

    @abstractmethod
    @classmethod
    def simulation_by_sobol_sample(
        cls,
        var_names: list[str],
        var_bounds: list[list[float]],
        sample_number: int,
        simulation_folder: str,
        txtinout_folder: str,
        params: typing.Any,
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
