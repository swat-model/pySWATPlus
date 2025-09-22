import pandas
import pathlib
import typing
import types
import datetime
from .types import ParameterModel, ParameterBoundedModel


def _variable_origin_static_type(
    vars_types: dict[str, typing.Any],
    vars_values: dict[str, typing.Any]
) -> None:
    '''
    Checks that input variables match their expected origin types.
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


def _path_directory(
    path: pathlib.Path
) -> None:
    '''
    Ensures the input path refers to a valid directory.
    '''

    if not path.is_dir():
        raise NotADirectoryError(
            f'Invalid target_dir path: {str(path)}'
        )

    return None


def _date_begin_earlier_end(
    begin_date: datetime.date,
    end_date: datetime.date
) -> None:
    '''
    Checks that begin date is earlier than end date.
    '''

    date_fmt = '%d-%b-%Y'

    if begin_date >= end_date:
        raise ValueError(
            f'begin_date {begin_date.strftime(date_fmt)} must be earlier than end_date {end_date.strftime(date_fmt)}'
        )


def _validate_date_str(
    date_str: str
) -> None:
    '''
    Validates a date string in 'YYYY-MM-DD' format.
    Raises ValueError if invalid.
    '''

    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f'Invalid date format: "{date_str}". Expected YYYY-MM-DD.')


def _calibration_units(
    txtinout_path: pathlib.Path,
    param_change: ParameterModel
) -> None:
    '''
    Validate units for a given parameter change against calibration parameters.
    '''

    units = param_change.units
    name = param_change.name

    if not units:
        return

    cal_parms_df = pandas.read_csv(
        filepath_or_buffer=txtinout_path / "cal_parms.cal",
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
            f'Supported obj_type: [{', '.join(obj_type_files.keys())}].'
        )

    file = obj_type_files[obj_type]
    file_path = txtinout_path / file

    # Open file and check that units id are valid
    df = pandas.read_csv(
        filepath_or_buffer=file_path,
        skiprows=1,
        sep=r'\s+',
        usecols=['id']
    )

    # Id's in the files are consecutive (and starting from 1). We can use the length of the df to check if all units are present
    max_unit = max(units)
    if len(df) < max_unit:
        raise ValueError(
            f'Invalid units for parameter "{name}". '
            f'Some ids exceed the maximum available in {file} '
            f'(requested up to {max_unit}, available {len(df)}).'
        )


def _calibration_conditions(
    txtinout_path: pathlib.Path,
    param_change: ParameterModel
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
        df_textures = pandas.read_fwf(txtinout_path / 'soils.sol', skiprows=1)
        validators['texture'] = set(df_textures['texture'].dropna().unique())
    if 'plant' in conditions:
        df_plants = pandas.read_fwf(txtinout_path / 'plants.plt', sep=r'\s+', skiprows=1)
        validators['plant'] = set(df_plants['name'].dropna().unique())
    if 'landuse' in conditions:
        df_landuse = pandas.read_csv(txtinout_path / 'landuse.lum', sep=r'\s+', skiprows=1)
        validators['landuse'] = set(df_landuse['plnt_com'].dropna().unique())

    # Validate conditions
    for cond_name, cond_values in conditions.items():
        if cond_name not in supported_conditions:
            raise ValueError(
                f'Condition "{cond_name}" for parameter "{name}" is not supported. '
                f'Available conditions are: {', '.join(sorted(supported_conditions))}.'
            )

        valid_values = validators.get(cond_name, set())
        for val in cond_values:
            if val not in valid_values:
                raise ValueError(
                    f'Condition "{cond_name}" for parameter "{name}" has invalid value "{val}". '
                    f'Expected are: {sorted(valid_values)}.'
                )


def _calibration_conditions_and_units(
    txtinout_path: pathlib.Path,
    parameters: list[ParameterModel]
) -> None:
    '''
    This function checks:
    - That the parameter exists in the calibration parameters.
    - That the parameter supports units/conditions (based on 'obj_typ').
    - That specified units correspond to valid IDs in the relevant SWAT+ input files.
    - That conditions (if applicable) exist and are valid.
    '''

    for param_change in parameters:
        try:
            _calibration_conditions(
                txtinout_path=txtinout_path,
                param_change=param_change
            )
            _calibration_units(
                txtinout_path=txtinout_path,
                param_change=param_change
            )
        except ValueError as e:
            raise ValueError(
                f'{e}\n\n'
                f'If you want to ignore the validation, set "skip_validation=True"'
            ) from e


def _calibration_parameters(
    txtinout_path: pathlib.Path,
    parameters: list[ParameterBoundedModel] | list[ParameterModel]
) -> None:
    '''
    Check if parameters exists in cal_parms.cal
    '''

    # Path of cal_parms.cal
    file_path = txtinout_path / 'cal_parms.cal'

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
