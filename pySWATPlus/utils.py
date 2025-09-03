from .types import ParamsType, ParamChange, CalParamChanges, CalParamChange
import pandas
from collections.abc import Callable
import pathlib
import typing
from datetime import datetime
from collections.abc import Iterable
import os
import numpy
import SALib.sample.sobol
import copy
import time
import json
import shutil
from .base_sensitivity_analyser import BaseSensitivityAnalyzer


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


"""
Functions related to calibration.cal file
"""


def _format_val_field(value: float) -> str:
    """
    Format a number for the VAL column:
    - 16 characters total: 1 leading space + 15-character numeric field
    - Right-aligned
    - Fixed-point if integer part fits; scientific if too large
    """

    # Convert to string without formatting
    s = str(value)

    if len(s) > 15:
        # Use scientific notation
        formatted = f"{value:.6e}"
    else:
        # If it fits, just use normal string
        formatted = s

    # Right-align to 16 characters
    return f"{formatted:>16}"


def _compact_units(unit_list: Iterable[int]) -> list[int]:
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
    params: CalParamChange
) -> list[str]:
    '''
    Parse the conditions that must be added to that parameter in calibration.cal file
    '''
    conditions = params.get('conditions', {})
    if not conditions:
        return []

    conditions_parsed = []
    for parameter, condition_keys in conditions.items():
        for key in condition_keys:
            conditions_parsed.append(f"{parameter:<19}{'=':<15} {0:<16}{key}")

    return conditions_parsed


def _validate_calibration_params(
    params: CalParamChanges
) -> None:
    '''
    Validate the structure and values of SWAT+ parameter modification input that will be added to calibration.cal file
    '''

    if params is None:
        return

    if not isinstance(params, list):
        _params = [params]
    else:
        _params = params

    valid_change_types = ['absval', 'abschg', 'pctchg']
    mandatory_keys = ['name', 'value']

    for i, param_change in enumerate(_params):
        if not isinstance(param_change, dict):
            raise TypeError(
                f"Parameter {i}: expected a dict, got {type(param_change).__name__}"
            )
        for key in mandatory_keys:
            if key not in param_change:
                raise KeyError(f'Parameter {i}: missing required key "{key}"')

        if not isinstance(param_change["name"], str):
            raise TypeError(
                f'Parameter {i}: "name" must be a string, got {type(param_change["name"]).__name__}'
            )

        if not isinstance(param_change["value"], (int, float)):
            raise TypeError(
                f'Parameter {i} ("{param_change["name"]}"): "value" must be int or float, got {type(param_change["value"]).__name__}'
            )

        change_type = param_change.get("change_type", "absval")
        if change_type not in valid_change_types:
            raise ValueError(
                f'Parameter {i} ("{param_change["name"]}"): invalid change_type "{change_type}". '
                f'Expected one of: {", ".join(valid_change_types)}'
            )

        if "units" in param_change:
            if not isinstance(param_change["units"], Iterable):
                raise TypeError(
                    f'Parameter {i} ("{param_change["name"]}"): "units" must be an iterable of integers, '
                    f'got {type(param_change["units"]).__name__}'
                )

            # Check that all elements are integers and >= 0
            if not all(isinstance(unit, int) and unit >= 0 for unit in param_change["units"]):
                raise ValueError(
                    f'Parameter {i} ("{param_change["name"]}"): all elements in "units" must be integers >= 0'
                )

        if "conditions" in param_change:
            # check that all elements are dict[str, list[str]]
            if not isinstance(param_change["conditions"], dict):
                raise TypeError(
                    f'Parameter {i} ("{param_change["name"]}"): "conditions" must be a dict, '
                    f'got {type(param_change["conditions"]).__name__}'
                )

            for key, value in param_change["conditions"].items():
                if not isinstance(key, str):
                    raise TypeError(
                        f'Parameter {i} ("{param_change["name"]}"): "conditions" keys must be strings, '
                        f'got {type(key).__name__}'
                    )
                if not isinstance(value, list):
                    raise TypeError(
                        f'Parameter {i} ("{param_change["name"]}"): "conditions" values must be lists, '
                        f'got {type(value).__name__}'
                    )
                if not all(isinstance(item, str) for item in value):
                    raise TypeError(
                        f'Parameter {i} ("{param_change["name"]}"): all elements in "conditions"["{key}"] must be strings'
                    )


def _validate_units(param_change: CalParamChange, txtinout_path: pathlib.Path) -> None:
    '''
    Validate units for a given parameter change against calibration parameters.
    '''

    name = param_change['name']
    units = param_change.get('units', None)

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


def _validate_conditions(param_change: CalParamChange, txtinout_path: pathlib.Path) -> None:
    '''
    Validate conditions for a given parameter change against calibration parameters.
    '''

    name = param_change['name']
    conditions = param_change.get('conditions', None)
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


def _validate_conditions_and_units(params: CalParamChanges, txtinout_path: pathlib.Path) -> None:
    '''
    This function checks:
    - That the parameter exists in the calibration parameters.
    - That the parameter supports units/conditions (based on 'obj_typ').
    - That specified units correspond to valid IDs in the relevant SWAT+ input files.
    - That conditions (if applicable) exist and are valid.
    '''
    _params = params if isinstance(params, list) else [params]
    for param in _params:
        try:
            _validate_conditions(param, txtinout_path)
            _validate_units(param, txtinout_path)
        except ValueError as e:
            raise ValueError(
                f"{e}\n\n"
                f"If you want to ignore the validation, set "
                f"'skip_units_and_conditions_validation=True'"
            ) from e


def _check_swatplus_parameters(
    txtinout_folder: pathlib.Path,
    params: CalParamChanges
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
    _params = params if isinstance(params, list) else [params]
    parameter_names = [change['name'] for change in _params]

    for parameter in parameter_names:
        if parameter not in cal_parms_df['name'].values:
            raise ValueError(f"The parameter '{parameter}' is not in cal_parms.cal")


"""
Sensitivity Analysis
"""


def _validate_simulation_by_sobol_sample_params(
    simulation_folder: str,
    simulation_data: dict[str, dict[str, typing.Any]],
    var_names: list[str],
    var_bounds: list[list[float]],
) -> None:
    '''
    Validate parameters for the Sobol sampling simulation.
    '''
    # Check simulation folder
    if not os.path.isdir(simulation_folder):
        raise NotADirectoryError('Provided simulation_folder is not a valid directory path')
    if len(os.listdir(simulation_folder)) > 0:
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


def _collect_sobol_results(
    sample_array: numpy.ndarray,
    var_names: list[str],
    cpu_dict: dict[tuple[float, ...], dict[str, typing.Any]],
    problem_dict: dict[str, typing.Any],
    start_time: float,
    simulation_folder: str,
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

        json_file = os.path.join(simulation_folder, "sensitivity_simulation_sobol.json")
        with open(json_file, "w") as output_write:
            json.dump(write_dict, output_write, indent=4)

    return output_dict


def _setup_simulation_directory(
    track_sim: int,
    num_sim: int,
    var_array: numpy.ndarray,
    simulation_folder: str
) -> tuple[str, dict[str, typing.Any]]:
    '''
    Creates a simulation directory and returns its path + initial simulation_output dict.
    '''
    # Tracking simulation
    print(f"Started simulation: {track_sim}/{num_sim}", flush=True)

    # Create simulation directory
    dir_name = f"sim_{track_sim}"
    dir_path = os.path.join(simulation_folder, dir_name)
    os.makedirs(name=dir_path, exist_ok=True)

    # Output simulation dictionary
    simulation_output: dict[str, typing.Any] = {
        "dir": dir_name,
        "array": var_array,
    }

    return dir_path, simulation_output


def _extract_simulation_data(
    dir_path: str,
    simulation_data: dict[str, dict[str, typing.Any]],
    simulation_output: dict[str, typing.Any],
    clean_setup: bool
) -> dict[str, typing.Any]:
    """
    Extracts simulated data into `simulation_output` and cleans up the simulation directory.
    """
    # Extract simulated data
    for sim_fname, sim_fdict in simulation_data.items():
        df = BaseSensitivityAnalyzer.simulated_timeseries_df(
            data_file=os.path.join(dir_path, sim_fname),
            **sim_fdict,
        )
        simulation_output[f"{os.path.splitext(sim_fname)[0]}_df"] = df

    # Remove simulation directory
    if clean_setup:
        shutil.rmtree(dir_path, ignore_errors=True)

    return simulation_output
