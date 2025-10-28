import pandas
import pathlib
import typing
import types
import datetime
import json
from . import newtype


def _variable_origin_static_type(
    vars_types: dict[str, typing.Any],
    vars_values: dict[str, typing.Any]
) -> None:
    '''
    Check that input variables match their expected origin types.
    '''

    # iterate name and type of method variables
    for v_name, v_type in vars_types.items():
        # continute if varibale name is return
        if v_name == 'return':
            continue
        # get origin type and value of the variable
        type_origin = typing.get_origin(v_type)
        type_value = vars_values[v_name]
        # if origin type in None
        if type_origin is None:
            if not isinstance(type_value, v_type):
                raise TypeError(
                    f'Expected "{v_name}" to be "{v_type.__name__}", but got type "{type(type_value).__name__}"'
                )
        # if origin type in not None
        else:
            # if origin type is a Union
            if type_origin in (typing.Union, types.UnionType):
                # get argument types
                type_args = tuple(
                    typing.get_origin(arg) or arg for arg in typing.get_args(v_type)
                )
                if not isinstance(type_value, type_args):
                    type_expect = [t.__name__ for t in type_args]
                    raise TypeError(
                        f'Expected "{v_name}" to be one of {type_expect}, but got type "{type(type_value).__name__}"'
                    )
            # if origin type in not a Union
            else:
                if not isinstance(type_value, type_origin):
                    raise TypeError(
                        f'Expected "{v_name}" to be "{type_origin.__name__}", but got type "{type(type_value).__name__}"'
                    )

    return None


def _dir_path(
    input_dir: pathlib.Path
) -> None:
    '''
    Ensure the input directory refers to a valid path.
    '''

    if not input_dir.is_dir():
        raise NotADirectoryError(
            f'Invalid directory path: {str(input_dir)}'
        )

    return None


def _dir_empty(
    input_dir: pathlib.Path
) -> None:
    '''
    Ensure the input directory is empty.
    '''

    if any(input_dir.iterdir()):
        raise FileExistsError(
            f'Input directory {str(input_dir)} contains files; expected an empty directory'
        )

    return None


def _date_begin_earlier_end(
    begin_date: datetime.date,
    end_date: datetime.date
) -> None:
    '''
    Check that begin date is earlier than end date.
    '''

    date_fmt = '%d-%b-%Y'

    if begin_date >= end_date:
        raise ValueError(
            f'begin_date {begin_date.strftime(date_fmt)} must be earlier than end_date {end_date.strftime(date_fmt)}'
        )

    return None


def _date_within_range(
    date_to_check: datetime.date,
    begin_date: datetime.date,
    end_date: datetime.date
) -> None:
    '''
    Check that a given date is within the specified begin and end date range (inclusive).
    '''

    date_fmt = '%d-%b-%Y'

    if not (begin_date <= date_to_check <= end_date):
        raise ValueError(
            f'date {date_to_check.strftime(date_fmt)} must be between '
            f'{begin_date.strftime(date_fmt)} and {end_date.strftime(date_fmt)}'
        )

    return None


def _parameters_contain_unique_dict(
    parameters: list[dict[str, typing.Any]]
) -> None:
    '''
    Check whether the input calibration list contains only unique dictionaries of parameters.
    '''

    # Get unique dictionaries
    unique_dicts = {
        json.dumps(d, sort_keys=True): d for d in parameters
    }

    # Check equal length of unique dictionaries and parameters
    if len(unique_dicts) != len(parameters):
        raise ValueError(
            'Duplicate dictionary found in "parameters" list'
        )

    return None


def _calibration_units(
    input_dir: pathlib.Path,
    param_change: newtype.ModifyDict
) -> None:
    '''
    Validate units for a given parameter change against calibration parameters.
    '''

    units = param_change.units
    name = param_change.name

    if not units:
        return

    cal_parms_df = pandas.read_csv(
        filepath_or_buffer=input_dir / 'cal_parms.cal',
        skiprows=2,
        sep=r'\s+'
    )

    # Get the object type for the parameter
    row = cal_parms_df.loc[cal_parms_df['name'] == name, 'obj_typ']
    obj_type = row.iloc[0]

    # Supported mapping of obj_type
    obj_type_files = {
        'hru': 'hru-data.hru',
        'sol': 'hru-data.hru',
        'res': 'reservoir.res',
        'aqu': 'aquifer.aqu'
    }
    if obj_type not in obj_type_files:
        raise ValueError(
            f'Parameter "{name}" with obj_type "{obj_type}" in "cal_parms.cal" does not support "units" key. '
            f'Supported obj_type: [{", ".join(obj_type_files.keys())}].'
        )

    file = obj_type_files[obj_type]
    file_path = input_dir / file

    # Open file and check that units id are valid
    df = pandas.read_csv(
        filepath_or_buffer=file_path,
        skiprows=1,
        sep=r'\s+',
        usecols=['id']
    )

    # Use the DataFrame length to check if all units starting from 1 are present
    max_unit = max(units)
    if len(df) < max_unit:
        raise ValueError(
            f'Invalid units for parameter "{name}". '
            f'Some ids exceed the maximum available in {file} '
            f'(requested up to {max_unit}, available {len(df)}).'
        )

    return None


def _calibration_conditions(
    input_dir: pathlib.Path,
    param_change: newtype.ModifyDict
) -> None:
    '''
    Validate conditions for a given parameter change against calibration parameters.
    '''

    conditions = param_change.conditions
    name = param_change.name
    if not conditions:
        return

    supported_conditions = {'hsg', 'texture', 'plant', 'landuse'}

    # Build validators lazily (only when needed)
    validators = {}

    if 'hsg' in conditions:
        validators['hsg'] = {'A', 'B', 'C', 'D'}
    if 'texture' in conditions:
        df_textures = pandas.read_fwf(input_dir / 'soils.sol', skiprows=1)
        validators['texture'] = set(df_textures['texture'].dropna().unique())
    if 'plant' in conditions:
        df_plants = pandas.read_fwf(input_dir / 'plants.plt', sep=r'\s+', skiprows=1)
        validators['plant'] = set(df_plants['name'].dropna().unique())
    if 'landuse' in conditions:
        df_landuse = pandas.read_csv(input_dir / 'landuse.lum', sep=r'\s+', skiprows=1)
        validators['landuse'] = set(df_landuse['plnt_com'].dropna().unique())

    # Validate conditions
    for cond_name, cond_values in conditions.items():
        if cond_name not in supported_conditions:
            raise ValueError(
                f'Condition "{cond_name}" for parameter "{name}" is not supported. '
                f'Available conditions are: {", ".join(sorted(supported_conditions))}.'
            )

        valid_values = validators.get(cond_name, set())
        for val in cond_values:
            if val not in valid_values:
                raise ValueError(
                    f'Condition "{cond_name}" for parameter "{name}" has invalid value "{val}". '
                    f'Expected are: {sorted(valid_values)}.'
                )

    return None


def _calibration_conditions_and_units(
    input_dir: pathlib.Path,
    parameters: list[newtype.ModifyDict]
) -> None:
    '''
    Check the following:
    - That the parameter exists in the calibration parameters.
    - That the parameter supports units/conditions (based on 'obj_typ').
    - That specified units correspond to valid IDs in the relevant SWAT+ input files.
    - That conditions (if applicable) exist and are valid.
    '''

    for param_change in parameters:
        try:
            _calibration_conditions(
                input_dir=input_dir,
                param_change=param_change
            )
            _calibration_units(
                input_dir=input_dir,
                param_change=param_change
            )
        except ValueError as e:
            raise ValueError(
                f'{e}\n\n'
                f'If you want to ignore the validation, set "skip_validation=True"'
            ) from e

    return None


def _calibration_parameters(
    input_dir: pathlib.Path,
    parameters: list[newtype.BoundDict] | list[newtype.ModifyDict]
) -> None:
    '''
    Validate existence of input calibration parameters in `cal_parms.cal`.
    '''

    # Path of cal_parms.cal
    file_path = input_dir / 'cal_parms.cal'

    # DataFrame from cal_parms.cal file
    parms_df = pandas.read_csv(
        filepath_or_buffer=file_path,
        skiprows=2,
        sep=r'\s+'
    )

    # Check validity of input calibration parameter name
    for param in parameters:
        if param.name not in parms_df['name'].values:
            raise ValueError(
                f'Calibration parameter "{param.name}" not found in cal_parms.cal file'
            )

    return None


def _json_extension(
    json_file: pathlib.Path
) -> None:
    '''
    Validate that the file has a JSON extension.
    '''

    if json_file.suffix.lower() != '.json':
        raise ValueError(
            f'Expected ".json" extension for "json_file", but got "{json_file.suffix}"'
        )

    return None


def _variables_defined_or_none(
    **kwargs: typing.Any
) -> None:
    '''
    Ensure that either all or none of the given arguments are provided (not None).

    Example:
        _ensure_together(begin_date=begin_date, end_date=end_date)
    '''

    total = len(kwargs)
    provided = [name for name, value in kwargs.items() if value is not None]

    # If some (but not all) values are provided → inconsistent input
    if 0 < len(provided) < total:
        missing = [name for name in kwargs if name not in provided]
        all_args = ', '.join(kwargs.keys())
        raise ValueError(
            f'Arguments [{all_args}] must be provided together, but missing: {missing}'
        )

    return None


def _simulation_preliminary_setup(
    sim_dir: pathlib.Path,
    tio_dir: pathlib.Path,
    parameters: list[newtype.BoundDict] | list[newtype.ModifyDict]
) -> None:

    # Check validity of simulation directory path
    _dir_path(
        input_dir=sim_dir
    )

    # Check simulation directory is empty
    _dir_empty(
        input_dir=sim_dir
    )

    # Validate parameter names
    _calibration_parameters(
        input_dir=tio_dir,
        parameters=parameters
    )

    return None


def _extract_data_config(
    extract_data: dict[str, dict[str, typing.Any]],
) -> None:
    '''
    Validate `extract_data` configuration.
    '''

    # List of valid sub-keys of sub-dictionaries
    valid_subkeys = [
        'has_units',
        'begin_date',
        'end_date',
        'ref_day',
        'ref_month',
        'apply_filter',
        'usecols'
    ]

    # Iterate dictionary
    for file_key, file_dict in extract_data.items():
        # Check type of a sub-dictionary
        if not isinstance(file_dict, dict):
            raise TypeError(
                f'Expected "{file_key}" in extract_data must be a dictionary, '
                f'but got type "{type(file_dict).__name__}"'
            )
        # Check mandatory 'has_units' sub-key in sub-dictionary
        if 'has_units' not in file_dict:
            raise KeyError(
                f'Key has_units is missing for "{file_key}" in extract_data'
            )
        # Iterate sub-key
        for sub_key in file_dict:
            # Check valid sub-key
            if sub_key not in valid_subkeys:
                raise KeyError(
                    f'Invalid sub-key "{sub_key}" for "{file_key}" in extract_data; '
                    f'expected sub-keys are {json.dumps(valid_subkeys)}'
                )

    return None


def _metric_config(
    input_dict: dict[str, dict[str, str]],
    var_name: str
) -> None:
    '''
    Validate metric dictionary configuration.
    '''

    # List of valid sub-keys of sub-dictionaries
    valid_subkeys = [
        'sim_col',
        'obs_col',
        'indicator'
    ]

    # List of valid indicators
    valid_indicators = [
        'NSE',
        'KGE',
        'MSE',
        'RMSE',
        'PBIAS',
        'MARE'
    ]

    # Iterate dictionary
    for file_key, file_dict in input_dict.items():
        # Check type of a sub-dictionary
        if not isinstance(file_dict, dict):
            raise TypeError(
                f'Expected "{file_key}" in {var_name} must be a dictionary, '
                f'but got type "{type(file_dict).__name__}"'
            )
        # Check sub-dictionary length
        if len(file_dict) != 3:
            raise ValueError(
                f'Length of "{file_key}" sub-dictionary in {var_name} must be 3, '
                f'but got {len(file_dict)}'
            )
        # Iterate sub-key
        for sub_key in file_dict:
            # Check valid sub-key
            if sub_key not in valid_subkeys:
                raise KeyError(
                    f'Invalid sub-key "{sub_key}" for "{file_key}" in {var_name}; '
                    f'expected sub-keys are {json.dumps(valid_subkeys)}'
                )
            if sub_key == 'indicator' and file_dict[sub_key] not in valid_indicators:
                raise ValueError(
                    f'Invalid "indicator" value "{file_dict[sub_key]}" for "{file_key}" in {var_name}; '
                    f'expected indicators are {valid_indicators}'
                )

    return None


def _observe_data_config(
    observe_data: dict[str, dict[str, str]],
) -> None:
    '''
    Validate `observe_data` configuration.
    '''

    # List of valid sub-keys of sub-dictionaries
    valid_subkeys = [
        'obs_file',
        'date_format'
    ]

    # Iterate dictionary
    for file_key, file_dict in observe_data.items():
        # Check type of a sub-dictionary
        if not isinstance(file_dict, dict):
            raise TypeError(
                f'Expected "{file_key}" in observe_data must be a dictionary, '
                f'but got type "{type(file_dict).__name__}"'
            )
        # Check sub-dictionary length
        if len(file_dict) != 2:
            raise ValueError(
                f'Length of "{file_key}" sub-dictionary in observe_data must be 2, '
                f'but got {len(file_dict)}'
            )
        # Iterate sub-key
        for sub_key in file_dict:
            # Check valid sub-key
            if sub_key not in valid_subkeys:
                raise KeyError(
                    f'Invalid sub-key "{sub_key}" for "{file_key}" in observe_data; '
                    f'expected sub-keys are {json.dumps(valid_subkeys)}'
                )

        return None


def _dict_key_equal(
    **dicts: dict[str, typing.Any]
) -> None:
    '''
    Validate equal top-level keys across input dictionaries.
    '''

    # List of dictionary name and their values
    dict_items = list(dicts.items())

    # Get reference name and keys from the first dictionary
    ref_name, ref_dict = dict_items[0]

    # Compare with each subsequent dictionary
    for c_name, c_dict in dict_items[1:]:
        if c_dict.keys() != ref_dict.keys():
            raise ValueError(
                f'Top-level keys mismatch between "{ref_name}" and "{c_name}"'
            )

    return None
