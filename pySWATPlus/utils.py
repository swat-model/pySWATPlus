from .types import ParamsType, ParamChange, ParameterChange, ParameterChanges
import pandas
from collections.abc import Callable
import pathlib
import typing
from datetime import datetime


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


def _apply_param_change(
    df: pandas.DataFrame,
    param_name: str,
    change: ParamChange
) -> None:
    '''
    Apply parameter change to a DataFrame
    '''

    value = change['value']
    change_type = change['change_type'] if 'change_type' in change else 'absval'
    filter_by = change.get('filter_by')

    mask = df.query(filter_by).index if filter_by else df.index

    if change_type == 'absval':
        df.loc[mask, param_name] = value
    elif change_type == 'abschg':
        df.loc[mask, param_name] += value
    elif change_type == 'pctchg':
        df.loc[mask, param_name] *= (1 + value / 100)


def _validate_params(
    params: ParamsType
) -> None:
    '''
    Validate the structure and values of SWAT+ parameter modification input.
    '''

    if params is None:
        return

    if not isinstance(params, dict):
        raise TypeError('Input variable "params" must be a ParamsType dictionary')

    valid_change_types = ['absval', 'abschg', 'pctchg']

    for filename, file_params in params.items():
        if not isinstance(file_params, dict):
            raise TypeError(f'Expected a dictionary for file "{filename}", got {type(file_params).__name__}')

        if 'has_units' in file_params:
            if not isinstance(file_params['has_units'], bool):
                raise TypeError(f'has_units key for file "{filename}" must be a boolean')
        else:
            raise KeyError(f'has_units key is missing for file "{filename}"')

        for key, value in file_params.items():
            if key == 'has_units':
                continue

            # For any other key, value should NOT be bool
            if isinstance(value, bool):
                raise TypeError(f'Unexpected bool value for key "{key}" in file "{filename}"')

            param_changes = value if isinstance(value, list) else [value]

            for change in param_changes:
                if not isinstance(change, dict):
                    raise TypeError(
                        f'"{key}" for file "{filename}" must be either a dictinary or a list of dictionaries, got {type(change).__name__}'
                    )

                if 'value' not in change:
                    raise KeyError(f'Missing "value" key for "{key}" in file "{filename}"')

                if not isinstance(change['value'], (int, float)):
                    raise TypeError(f'"value" type for "{key}" in file "{filename}" must be numeric')

                change_type = change.get('change_type', 'absval')
                if change_type not in valid_change_types:
                    raise ValueError(
                        f'Invalid change_type "{change_type}" for "{key}" in file "{filename}". Expected one of: {valid_change_types}'
                    )

                filter_by = change.get('filter_by')
                if filter_by is not None and not isinstance(filter_by, str):
                    raise TypeError(f'filter_by for "{key}" in file "{filename}" must be a string')


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


def _validate_date_str(
    date_str: str
) -> None:
    '''
    Validates a date string in 'YYYY-MM-DD' format.
    Raises ValueError if invalid.
    '''
    try:
        datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f'Invalid date format: "{date_str}". Expected YYYY-MM-DD.')

# Function to format VAL to exactly 15 digits (including sign, integer, decimal point)


def _format_val_to_15_digits(
    value: float
) -> str:
    '''
    Format a number for VAL column:
    - Right-aligned
    - Max 15 characters total (including sign, digits, decimal point)
    - Fixed-point if possible, scientific if integer part too big
    '''
    abs_val = abs(value)
    sign = '-' if value < 0 else ''

    # number of digits in integer part
    int_digits = len(str(int(abs_val)))

    # total space for decimal part: 15 - int_digits - sign - decimal point
    decimal_places = 15 - int_digits - len(sign) - 1

    if decimal_places >= 0:
        # fixed-point format fits
        s = f"{value:.{decimal_places}f}"
    else:
        # integer part too big, switch to scientific notation
        # reserve 1 char for sign if negative
        s = f"{value:.6e}"  # 6 decimals in scientific notation

    # always right-align in 15 characters
    return f"{s:>16}"


def _validate_calibration_params(
    params: ParameterChanges
) -> None:
    '''
    Validate the structure and values of SWAT+ parameter modification input.
    '''

    if params is None:
        return

    if not isinstance(params, ParameterChanges):
        raise TypeError('Input variable "params" must be a list of ParameterChange dictionaries')

    if not isinstance(params, list):
        _params = [params]
    else:
        _params = params

    valid_change_types = ['absval', 'abschg', 'pctchg']
    mandatory_keys = ['name', 'value']

    for param_change in _params:
        if not isinstance(param_change, ParameterChange):
            raise TypeError(f'Expected a dictionary, got {type(param_change).__name__}')

        for key in mandatory_keys:
            if key not in param_change:
                raise KeyError(f'Missing "{key}" key for "{param_change.get("name", "unknown")}" in `params`')

        if not isinstance(param_change['name'], str):
            raise TypeError('"name" key must be a string in `params`')

        if not isinstance(param_change['value'], (int, float)):
            raise TypeError(f'"value" type for "{param_change["name"]}" in `params` must be numeric')

        change_type = param_change.get('change_type', 'absval')
        if change_type not in valid_change_types:
            raise ValueError(
                f'Invalid change_type "{change_type}" for "{param_change["name"]}" in `params`. Expected one of: {valid_change_types}'
            )
