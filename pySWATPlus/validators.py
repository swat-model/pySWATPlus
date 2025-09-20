import pandas
import pathlib
import typing
import types
from datetime import datetime
from .types import ParameterModel, ParameterBoundedModel


def _variable_origin_static_type(
    vars_types: dict[str, typing.Any],
    vars_values: dict[str, typing.Any]
) -> None:
    '''
    Validates input variables against their expected types.
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
    Validates path of the direcotry.
    '''

    if not path.is_dir():
        raise NotADirectoryError(
            f'Invalid target_dir path: {str(path)}'
        )

    return None


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


def _validate_units(param_change: ParameterModel, txtinout_path: pathlib.Path) -> None:
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
    if row.empty:
        raise ValueError(f"Parameter '{name}' not found in file 'cal_parms.cal'.")

    obj_type = row.iloc[0]
    if not obj_type:
        raise ValueError("Missing 'obj_typ' column in 'cal_parms.cal' file.")

    # Supported mapping of obj_type → file
    obj_type_files = {
        'hru': 'hru-data.hru',
        'sol': 'hru-data.hru',
        'res': 'reservoir.res',
        'aqu': 'aquifer.aqu',
    }

    if obj_type not in obj_type_files:
        supported = ", ".join(obj_type_files.keys())
        raise ValueError(
            f"Parameter '{name}' does not support units. "
            f"Only parameters of type [{supported}] support units."
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
            f"Invalid units for parameter '{name}'. "
            f"Some ids exceed the maximum available in {file} "
            f"(requested up to {max_unit}, available {len(df)})."
        )


def _validate_conditions(param_change: ParameterModel, txtinout_path: pathlib.Path) -> None:
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
                f"Condition '{cond_name}' for parameter '{name}' is not supported. "
                f"Available conditions are: {', '.join(sorted(supported_conditions))}."
            )

        valid_values = validators.get(cond_name, set())
        for val in cond_values:
            if val not in valid_values:
                raise ValueError(
                    f"Condition '{cond_name}' for parameter '{name}' "
                    f"has invalid value '{val}'. "
                    f"Valid values are: {sorted(valid_values)}."
                )


def _validate_conditions_and_units(parameters: list[ParameterModel], txtinout_path: pathlib.Path) -> None:
    '''
    This function checks:
    - That the parameter exists in the calibration parameters.
    - That the parameter supports units/conditions (based on 'obj_typ').
    - That specified units correspond to valid IDs in the relevant SWAT+ input files.
    - That conditions (if applicable) exist and are valid.
    '''
    for param_change in parameters:
        try:
            _validate_conditions(param_change, txtinout_path)
            _validate_units(param_change, txtinout_path)
        except ValueError as e:
            raise ValueError(
                f"{e}\n\n"
                f"If you want to ignore the validation, set "
                f"'skip_units_and_conditions_validation=True'"
            ) from e


def _validate_cal_parameters(
    txtinout_folder: pathlib.Path,
    parameters: list[ParameterBoundedModel] | list[ParameterModel]
) -> None:
    '''
    Check if parameters exists in cal_parms.cal
    '''

    file_path = txtinout_folder / "cal_parms.cal"

    if not file_path.exists():
        raise FileNotFoundError("cal_parms.cal file does not exist in the TxtInOut folder")

    cal_parms_df = pandas.read_csv(
        filepath_or_buffer=file_path,
        skiprows=2,
        sep=r'\s+'
    )

    for param in parameters:
        if param.name not in cal_parms_df['name'].values:
            raise ValueError(f"The parameter '{param.name}' is not in cal_parms.cal")
