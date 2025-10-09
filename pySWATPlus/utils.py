import pandas
import datetime
import json
import io
import pathlib
import typing
from collections.abc import Iterable
from collections.abc import Callable
from .types import ModifyDict


def _build_line_to_add(
    obj: str,
    daily: bool,
    monthly: bool,
    yearly: bool,
    avann: bool
) -> str:
    '''
    Format lines for `print.prt` file
    '''

    print_periodicity = {
        'daily': daily,
        'monthly': monthly,
        'yearly': yearly,
        'avann': avann,
    }

    arg_to_add = obj.ljust(29)
    for value in print_periodicity.values():
        periodicity = 'y' if value else 'n'
        arg_to_add += periodicity.ljust(14)

    return arg_to_add.rstrip() + '\n'


def _date_str_to_object(
    date_str: str
) -> datetime.date:
    '''
    Convert a date string in 'DD-Mon-YYYY' format to a `datetime.date` object
    '''

    date_fmt = '%d-%b-%Y'
    try:
        get_date = datetime.datetime.strptime(date_str, date_fmt).date()
    except ValueError:
        raise ValueError(
            f'Invalid date format: "{date_str}"; expected format is DD-Mon-YYYY (e.g., 15-Mar-2010)'
        )

    return get_date


def _clean(
    df: pandas.DataFrame
) -> pandas.DataFrame:
    '''
    Clean a DataFrame by stripping whitespace from column names and string values.
    '''

    # Strip spaces from column names
    df.columns = [str(c).strip() for c in df.columns]

    # Strip spaces from string/object values
    obj_cols = df.select_dtypes(include=['object', 'string']).columns
    for col in obj_cols:
        df[col] = df[col].str.strip()

    return df


def _load_file(
    path: pathlib.Path,
    skip_rows: typing.Optional[list[int]] = None
) -> pandas.DataFrame:
    '''
    Attempt to load a dataframe from `path` using multiple parsing strategies.
    '''

    if path.suffix.lower() == '.csv':
        df_from_csv = pandas.read_csv(
            filepath_or_buffer=path,
            skiprows=skip_rows,
            skipinitialspace=True
        )
        return _clean(df_from_csv)

    strategies: list[Callable[[], pandas.DataFrame]] = [
        lambda: pandas.read_csv(path, sep=r'\s+', skiprows=skip_rows),
        lambda: pandas.read_csv(path, sep=r'[ ]{2,}', skiprows=skip_rows),
        lambda: pandas.read_fwf(path, skiprows=skip_rows)
    ]
    for attempt in strategies:
        try:
            df: pandas.DataFrame = attempt()
            return _clean(df)
        except Exception:
            pass

    raise ValueError(f'Error reading the file: {path}')


def _format_val_field(
    value: float
) -> str:
    '''
    Format a number for the VAL column:
    - 16 characters total: 1 leading space + 15-character numeric field
    - Right-aligned
    - Fixed-point if integer part fits; scientific if too large
    '''

    # Convert to string without formatting
    s = str(value)

    if len(s) > 15:
        # Use scientific notation
        formatted = f'{value:.6e}'
    else:
        # If it fits, just use normal string
        formatted = s

    # Right-align to 16 characters
    return f'{formatted:>16}'


def _compact_units(
    unit_list: Iterable[int]
) -> list[int]:
    '''
    Compact a 1-based list of unit IDs into SWAT units syntax.

    Consecutive unit IDs are represented as a range using negative numbers:

    - Single units are listed as positive numbers.
    - Consecutive ranges are represented as [start, -end].

    All IDs must be 1-based (Fortran-style).
    '''

    if not unit_list:
        return []

    if 0 in unit_list:
        raise ValueError('All unit IDs must be 1-based (Fortran-style).')

    # Sort the list
    unit_list = sorted(set(unit_list))
    compact = []
    start = prev = unit_list[0]

    for u in unit_list[1:]:
        if u == prev + 1:
            prev = u
        else:
            if start == prev:
                compact.append(start)
            else:
                compact.extend([start, -prev])
            start = prev = u

    # Add the last sequence
    if start == prev:
        compact.append(start)
    else:
        compact.extend([start, -prev])

    return compact


def _parse_conditions(
    parameters: ModifyDict
) -> list[str]:
    '''
    Parse the conditions that must be added to that parameter in calibration.cal file
    '''

    conditions = parameters.conditions
    if not conditions:
        return []

    conditions_parsed = []
    for parameter, condition_keys in conditions.items():
        for key in condition_keys:
            conditions_parsed.append(f'{parameter:<19}{"=":<15} {0:<16}{key}')

    return conditions_parsed


def _df_observed(
    obs_file: pathlib.Path,
    date_format: str,
    obs_col: str
) -> pandas.DataFrame:
    '''
    Read the CSV file specified by `obs_file`, parses the date column using the provided
    `date_format`, and returns a `DataFrame` with two columns: `date` (as `datetime.date`)
    and `obs_col` (the observed values).
    '''

    # DataFrame
    obs_df = pandas.read_csv(
        filepath_or_buffer=obs_file,
        parse_dates=['date'],
        date_format=date_format
    )

    # Date string to datetime.date objects
    obs_df = obs_df[['date', obs_col]]
    obs_df['date'] = obs_df['date'].dt.date

    # Remove any negative observed data
    obs_df = obs_df[obs_df[obs_col] >= 0].reset_index(drop=True)

    return obs_df


def _df_normalize(
    df: pandas.DataFrame
) -> pandas.DataFrame:
    '''
    Normalize the values in the input `DataFrame` using the formula `(df - min) / (max - min)`,
    where `min` and `max` represent the minimum and maximum values of the `DataFrame`
    prior to normalization.
    '''

    # Minimum and maximum values
    df_min = df.min().min()
    df_max = df.max().max()

    # Normalized DataFrame
    norm_df = (df - df_min) / (df_max - df_min)

    return norm_df


def _retrieve_sensitivity_output(
    sim_file: pathlib.Path,
    df_name: str,
    add_problem: bool,
    add_sample: bool
) -> dict[str, typing.Any]:
    '''
    Retrieve sensitivity simulation data and generate a dictionary containing the following keys:

    - `scenario` (default): A mapping between each scenario integer and its corresponding DataFrame.
    - `problem` (optional): The problem definition.
    - `sample` (optional): The sample list used in the sensitivity simulation.
    '''

    # Load sensitivity simulation dictionary from JSON file
    with open(sim_file, 'r') as input_sim:
        sensitivity_sim = json.load(input_sim)

    # Dictionary of sample DataFrames
    sample_dfs = {}
    for key, val in sensitivity_sim['simulation'].items():
        key_df = pandas.read_json(
            path_or_buf=io.StringIO(val[df_name])
        )
        key_df['date'] = key_df['date'].dt.date
        sample_dfs[int(key)] = key_df

    # Default output dictionary
    output = {
        'scenario': sample_dfs
    }

    # Add problem definition in output
    if add_problem:
        output['problem'] = sensitivity_sim['problem']

    # Add numpy sample array in output
    if add_sample:
        output['sample'] = sensitivity_sim['sample']

    return output
