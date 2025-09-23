import pandas
import typing
import pathlib
from .filereader import FileReader
from . import utils
from . import validators


class DataManager:

    '''
    Provides functionality for handling data processings and workflows.
    '''

    def simulated_timeseries_df(
        self,
        target_file: str | pathlib.Path,
        has_units: bool,
        begin_date: typing.Optional[str] = None,
        end_date: typing.Optional[str] = None,
        ref_day: typing.Optional[int] = None,
        ref_month: typing.Optional[int] = None,
        apply_filter: typing.Optional[dict[str, list[typing.Any]]] = None,
        usecols: typing.Optional[list[str]] = None,
        json_file: typing.Optional[str | pathlib.Path] = None
    ) -> pandas.DataFrame:
        '''
        Extract data from a simulation output file and return a time series `DataFrame`.
        A new `date` column is constructed using `datetime.date` objects from the `yr`, `mon`, and `day` columns.

        Parameters:
            target_file (str | pathlib.Path): Path to the input file used to generate the time series.

            has_units (bool): If `True`, the third line of the input file contains column units.

            begin_date (str): Start date in `DD-Mon-YYYY` format (e.g., '01-Jan-2012'), inclusive.
                If `None` (default), the earliest available date is used.

            end_date (str): End date in `DD-Mon-YYYY` format (e.g., '31-Dec-2015'), inclusive.
                If `None` (default), the latest available date is used.

            ref_day (int): Reference day for monthly and yearly time series. For example,
                `2012-01-31` and `2012-02-29` become `2012-01-15` and `2012-02-15` when `ref_day=15`.
                If `None` (default), the last day of the month or year is used, obtained from simulation.
                Not applicable to daily time series files (ending with `_day`).

            ref_month (int): Reference month for yearly time series. For example,
                `2012-12-31` and `2013-12-31` become `2012-06-15` and `2013-06-15` when `ref_day=15` and `ref_month=6`.
                If `None` (default), the last month of the year is used, obtained from simulation.
                Not applicable to monthly time series files (ending with `_mon`).

            apply_filter (dict[str, list[Any]]): Dictionary mapping column names to lists of values for row filtering.
                If `None` (default), no filtering is applied.

            usecols (list[str]): Column names to include in the output. If `None` (default), all columns are used.

            json_file (str | pathlib.Path): Path to save the output `DataFrame` as a JSON file.
                If `None` (default), the DataFrame is not saved.

        Returns:
            Time series `DataFrame` with a new `date` column.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.simulated_timeseries_df
            ),
            vars_values=locals()
        )

        # Absolute file path
        target_file = pathlib.Path(target_file).resolve()

        # DataFrame from input file
        file_reader = FileReader(
            path=target_file,
            has_units=has_units
        )
        df = file_reader.df

        # DataFrame columns
        df_cols = list(df.columns)

        # Create date column
        date_col = 'date'
        time_cols = ['yr', 'mon', 'day']
        missing_cols = [
            col for col in time_cols if col not in df_cols
        ]
        if len(missing_cols) > 0:
            raise ValueError(
                f'Missing required time series columns "{missing_cols}" in file "{target_file.name}"'
            )
        df[date_col] = pandas.to_datetime(
            df[time_cols].rename(columns={'yr': 'year', 'mon': 'month'})
        ).dt.date

        # Fix reference day
        if ref_day is not None:
            if target_file.stem.endswith('_day'):
                raise ValueError(
                    f'Parameter "ref_day" is not applicable for daily time series in file "{target_file.name}" '
                    f'because it would assign the same day to all records within a month.'
                )
            df[date_col] = df[date_col].apply(
                lambda x: x.replace(day=ref_day)
            )

        # Fix reference month
        if ref_month is not None:
            if target_file.stem.endswith('_mon'):
                raise ValueError(
                    f'Parameter "ref_month" is not applicable for monthly time series in file "{target_file.name}" '
                    f'because it would assign the same month to all records within a year.'
                )
            df[date_col] = df[date_col].apply(
                lambda x: x.replace(month=ref_month)
            )

        # Filter DataFrame by date
        begin_dt = utils._date_str_to_object(begin_date) if begin_date is not None else df[date_col].iloc[0]
        end_dt = utils._date_str_to_object(end_date) if end_date is not None else df[date_col].iloc[-1]
        df = df.loc[df[date_col].between(begin_dt, end_dt)].reset_index(drop=True)

        # Check if filtering by date removed all rows
        if df.empty:
            raise ValueError(
                f'No data found between "{begin_date}" and "{end_date}" in file "{target_file.name}"'
            )

        # Filter rows by dictionary criteria
        if apply_filter is not None:
            for col, val in apply_filter.items():
                if col not in df_cols:
                    raise ValueError(
                        f'Column "{col}" in apply_filter was not found in file "{target_file.name}"'
                    )
                if not isinstance(val, list):
                    raise TypeError(
                        f'Column "{col}" in apply_filter for file "{target_file.name}" must be a list, '
                        f'but got type "{type(val).__name__}"'
                    )
                df = df.loc[df[col].isin(val)]
                # Check if filtering removed all rows
                if df.empty:
                    raise ValueError(
                        f'Filtering by column "{col}" with values "{val}" returned no rows in "{target_file.name}"'
                    )

        # Reset DataFrame index
        df = df.reset_index(
            drop=True
        )

        # Finalize columns for DataFrame
        if usecols is None:
            retain_cols = [date_col] + df_cols
        else:
            for col in usecols:
                if col not in df_cols:
                    raise ValueError(
                        f'Column "{col}" specified in "usecols" was not found in file "{target_file.name}"'
                    )
            retain_cols = [date_col] + usecols

        # Output DataFrame
        df = df[retain_cols]

        # Save DataFrame
        if json_file is not None:
            json_file = pathlib.Path(json_file).resolve()
            if json_file.suffix.lower() != '.json':
                raise ValueError(
                    f'Expected ".json" extension for "json_file", but got "{json_file.suffix}"'
                )
            df[date_col] = df[date_col].astype(str)
            df.to_json(
                path_or_buf=json_file,
                orient="records",
                indent=4
            )

        return df
