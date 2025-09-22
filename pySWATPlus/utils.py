from .types import ParameterModel
import pandas
from collections.abc import Callable
import pathlib
import typing
from collections.abc import Iterable
from pydantic import BaseModel
import hashlib
import json
import datetime


def _build_line_to_add(
    obj: str,
    daily: bool,
    monthly: bool,
    yearly: bool,
    avann: bool
) -> str:
    '''
    Helper function to format lines for `print.prt` file
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
    Converts a date string in 'YYYY-MM-DD' format to a `datetime.date` object
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
    Cleans a DataFrame by stripping whitespace from column names and string values.
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
    skip_rows: typing.Optional[list[int]] = None,
    usecols: typing.Optional[list[str]] = None
) -> pandas.DataFrame:
    '''
    Attempt to load a dataframe from `path` using multiple parsing strategies.
    '''

    if path.suffix.lower() == '.csv':
        df_from_csv = pandas.read_csv(path, skiprows=skip_rows, usecols=usecols, skipinitialspace=True)
        return _clean(df_from_csv)

    strategies: list[Callable[[], pandas.DataFrame]] = [
        lambda: pandas.read_csv(path, sep=r'\s+', skiprows=skip_rows, usecols=usecols),
        lambda: pandas.read_csv(path, sep=r'[ ]{2,}', skiprows=skip_rows, usecols=usecols),
        lambda: pandas.read_fwf(path, skiprows=skip_rows, usecols=usecols),
    ]
    for attempt in strategies:
        try:
            df: pandas.DataFrame = attempt()
            return _clean(df)
        except Exception:
            pass

    raise ValueError(f'Error reading the file: {path}')


def _ensure_path(p: str | pathlib.Path) -> pathlib.Path:
    '''
    Validate and convert a path-like argument to a resolved pathlib.Path object.
    '''

    if not isinstance(p, (str, pathlib.Path)):
        raise TypeError(f"Argument must be a string or Path object, got {type(p).__name__}")
    return pathlib.Path(p).resolve()


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
    parameters: ParameterModel
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
            conditions_parsed.append(f'{parameter:<19}{'=':<15} {0:<16}{key}')

    return conditions_parsed


def _make_unique_param_name(
    param_key: str,
    model: BaseModel
) -> str:
    '''
    Generate a unique, deterministic parameter identifier by combining the parameter key
    with a hash of the Pydantic model's serialized contents.
    '''

    payload = json.dumps(model.model_dump(), sort_keys=True)
    uid = hashlib.md5(payload.encode()).hexdigest()
    return f'{param_key}|{uid}'
