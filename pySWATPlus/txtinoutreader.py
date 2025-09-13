import subprocess
import shutil
import pathlib
import typing
import logging
from .filereader import FileReader
from .types import ParamsType, ParamModel
from . import utils
from . import validators

logger = logging.getLogger(__name__)


class TxtinoutReader:
    '''
    Provide functionality for seamless reading, editing, and writing of
    SWAT+ model files located in the `TxtInOut` folder.
    '''

    IGNORED_FILE_PATTERNS: typing.Final[tuple[str, ...]] = tuple(
        f'_{suffix}.{ext}'
        for suffix in ('day', 'mon', 'yr', 'aa')
        for ext in ('txt', 'csv')
    )

    def __init__(
        self,
        path: str | pathlib.Path
    ) -> None:
        '''
        Create a TxtinoutReader instance for accessing SWAT+ model files.

        Args:
            path (str or Path): Path to the `TxtInOut` folder, which must contain
                exactly one SWAT+ executable `.exe` file.

        Raises:
            TypeError: If the path is not a valid string or Path, or if the folder contains
                zero or multiple `.exe` files.
        '''

        path = utils._ensure_path(path)

        # check if folder exists
        if not path.is_dir():
            raise FileNotFoundError('Folder does not exist')

        # check .exe files in the directory
        exe_list = [file for file in path.iterdir() if file.suffix == ".exe"]

        # raise error on .exe file
        if len(exe_list) != 1:
            raise TypeError(
                'Expected exactly one .exe file in the parent folder, but found none or multiple.'
            )

        # find parent directory
        self.root_folder = path
        self.swat_exe_path = path / exe_list[0]

    def enable_object_in_print_prt(
        self,
        obj: typing.Optional[str],
        daily: bool,
        monthly: bool,
        yearly: bool,
        avann: bool,
        allow_unavailable_object: bool = False
    ) -> None:
        '''
        Update or add an object in the `print.prt` file with specified time frequency flags.

        This method modifies the `print.prt` file in a SWAT+ project to enable or disable output
        for a specific object (or all objects if `obj` is None) at specified time frequencies
        (daily, monthly, yearly, or average annual). If the object does not exist in the file
        and `obj` is not None, it is appended to the end of the file.

        Note:
            This input does not provide complete control over `print.prt` outputs.
            Some files are internally linked in the SWAT+ model and may still be
            generated even when disabled.

        Args:
            obj (str or None): The name of the object to update (e.g., 'channel_sd', 'reservoir').
                If `None`, all objects in the `print.prt` file are updated with the specified time frequency settings.
            daily (bool): If `True`, enable daily frequency output.
            monthly (bool): If `True`, enable monthly frequency output.
            yearly (bool): If `True`, enable yearly frequency output.
            avann (bool): If `True`, enable average annual frequency output.
            allow_unavailable_object (bool, optional): If True, allows adding an object not in
                the standard SWAT+ output object list. If False and `obj` is not in the standard list,
                a ValueError is raised. Defaults to False.
        '''

        obj_dict = {
            'model_components': ['channel_sd', 'channel_sdmorph', 'aquifer', 'reservoir', 'recall', 'ru', 'hyd', 'water_allo'],
            'basin_model_components': ['basin_sd_cha', 'basin_sd_chamorph', 'basin_aqu', 'basin_res', 'basin_psc'],
            'nutrient_balance': ['basin_nb', 'lsunit_nb', 'hru-lte_nb'],
            'water_balance': ['basin_wb', 'lsunit_wb', 'hru_wb', 'hru-lte_wb'],
            'plant_weather': ['basin_pw', 'lsunit_pw', 'hru_pw', 'hru-lte_pw'],
            'losses': ['basin_ls', 'lsunit_ls', 'hru_ls', 'hru-lte_ls'],
            'salts': ['basin_salt', 'hru_salt', 'ru_salt', 'aqu_salt', 'channel_salt', 'res_salt', 'wetland_salt'],
            'constituents': ['basin_cs', 'hru_cs', 'ru_cs', 'aqu_cs', 'channel_cs', 'res_cs', 'wetland_cs']
        }

        obj_list = [i for v in obj_dict.values() for i in v]

        # Check 'obj' is either string or NoneType
        if not (isinstance(obj, str) or obj is None):
            raise TypeError(f'Input "obj" to be string type or None, got {type(obj).__name__}')

        # Check 'obj' is valid
        if obj and obj not in obj_list and not allow_unavailable_object:
            raise ValueError(
                f'Object "{obj}" not found in print.prt file. Use allow_unavailable_object=True to proceed.'
            )

        # Time frequency dictionary
        time_dict = {
            'daily': daily,
            'monthly': monthly,
            'yearly': yearly,
            'avann': avann
        }

        for key, val in time_dict.items():
            if not isinstance(val, bool):
                raise TypeError(f'Variable "{key}" for "{obj}" must be a bool value')

        # read all print_prt file, line by line
        print_prt_path = self.root_folder / 'print.prt'
        new_print_prt = ""
        found = False

        # Check if file exists
        if not print_prt_path.exists():
            raise FileNotFoundError("print.prt file does not exist")

        with open(print_prt_path, 'r', newline='') as file:
            for i, line in enumerate(file, start=1):
                if i <= 10:
                    # Always keep first 10 lines as-is
                    new_print_prt += line
                    continue

                stripped = line.strip()
                if not stripped:
                    # Keep blank lines unchanged
                    new_print_prt += line
                    continue

                parts = stripped.split()
                line_obj = parts[0]

                if obj is None:
                    # Update all objects
                    new_print_prt += utils._build_line_to_add(line_obj, daily, monthly, yearly, avann)
                elif line_obj == obj:
                    # obj already exist, replace it in same position
                    new_print_prt += utils._build_line_to_add(line_obj, daily, monthly, yearly, avann)
                    found = True
                else:
                    new_print_prt += line

        if not found and obj is not None:
            new_print_prt += utils._build_line_to_add(obj, daily, monthly, yearly, avann)

        # store new print_prt
        with open(print_prt_path, 'w', newline='') as file:
            file.write(new_print_prt)

    def set_begin_and_end_year(
        self,
        begin: int,
        end: int
    ) -> None:
        '''
        Modify the simulation period by updating
        the begin and end years in the `time.sim` file.

        Args:
            begin (int): Beginning year of the simulation in YYYY format (e.g., 2010).
            end (int): Ending year of the simulation in YYYY format (e.g., 2016).

        Raises:
            ValueError: If the begin year is greater than or equal to the end year.
        '''

        year_dict = {
            'begin': begin,
            'end': end
        }

        for key, val in year_dict.items():
            if not isinstance(val, int):
                raise TypeError(f'"{key}" year must be an integer value')

        if begin >= end:
            raise ValueError('begin year must be less than end year')

        nth_line = 3

        time_sim_path = self.root_folder / 'time.sim'

        # Check if file exists
        if not time_sim_path.exists():
            raise FileNotFoundError("time.sim file does not exist")

        # Open the file in read mode and read its contents
        with open(time_sim_path, 'r') as file:
            lines = file.readlines()

        year_line = lines[nth_line - 1]

        # Split the input string by spaces
        elements = year_line.split()

        # insert years
        elements[1] = str(begin)
        elements[3] = str(end)

        # Reconstruct the result string while maintaining spaces
        result_string = '{: >8} {: >10} {: >10} {: >10} {: >10} \n'.format(*elements)

        lines[nth_line - 1] = result_string

        with open(time_sim_path, 'w') as file:
            file.writelines(lines)

    def set_warmup_year(
        self,
        warmup: int
    ) -> None:
        '''
        Modify the warm-up years in the `print.prt` file.

        Args:
            warmup (int): A positive integer representing the number of years
                the simulation will use for warm-up (e.g., 1).

        Raises:
            ValueError: If the warmup year is less than or equal to 0.
        '''

        if not isinstance(warmup, int):
            raise TypeError('warmup must be an integer value')
        if warmup <= 0:
            raise ValueError('warmup must be a positive integer')

        print_prt_path = self.root_folder / 'print.prt'

        # Check if file exists
        if not print_prt_path.exists():
            raise FileNotFoundError("print.prt file does not exist")

        # Open the file in read mode and read its contents
        with open(print_prt_path, 'r') as file:
            lines = file.readlines()

        nth_line = 3
        year_line = lines[nth_line - 1]

        # Split the input string by spaces
        elements = year_line.split()

        # Modify warmup year
        elements[0] = str(warmup)

        # Reconstruct the result string while maintaining spaces
        result_string = '{: <12} {: <11} {: <11} {: <10} {: <10} {: <10} \n'.format(*elements)

        lines[nth_line - 1] = result_string

        with open(print_prt_path, 'w') as file:
            file.writelines(lines)

    def _enable_disable_csv_print(
        self,
        enable: bool = True
    ) -> None:
        '''
        Enable or disable print in the `print.prt` file.
        '''

        # read
        nth_line = 7

        print_prt_path = self.root_folder / 'print.prt'

        # Check if file exists
        if not print_prt_path.exists():
            raise FileNotFoundError("print.prt file does not exist")

        # Open the file in read mode and read its contents
        with open(print_prt_path, 'r') as file:
            lines = file.readlines()

        if enable:
            lines[nth_line - 1] = 'y' + lines[nth_line - 1][1:]
        else:
            lines[nth_line - 1] = 'n' + lines[nth_line - 1][1:]

        with open(print_prt_path, 'w') as file:
            file.writelines(lines)

    def enable_csv_print(
        self
    ) -> None:
        '''
        Enable print in the `print.prt` file.
        '''

        self._enable_disable_csv_print(enable=True)

    def disable_csv_print(
        self
    ) -> None:
        '''
        Disable print in the `print.prt` file.
        '''

        self._enable_disable_csv_print(enable=False)

    def register_file(
        self,
        filename: str,
        has_units: bool,
    ) -> FileReader:
        '''
        Register a file to work with in the SWAT+ model.

        Args:
            filename (str): Path to the file to register, located in the `TxtInOut` folder.
            has_units (bool): If True, the second row of the file contains units.

        Returns:
            A FileReader instance for the registered file.
        '''

        file_path = self.root_folder / filename

        return FileReader(file_path, has_units)

    def copy_required_files(
        self,
        target_dir: str | pathlib.Path,
    ) -> pathlib.Path:
        '''
        Copy the required file from the input folder associated with the
        `TxtinoutReader` instance to the specified directory for SWAT+ simulation.

        Args:
            target_dir (str or Path): Path to the directory where the required files will be copied.

        Returns:
            The path to the target directory containing the copied files.
        '''

        target_dir = utils._ensure_path(target_dir)

        # Create the directory if it does not exist and copy necessary files
        target_dir.mkdir(parents=True, exist_ok=True)

        dest_path = pathlib.Path(target_dir)

        if any(dest_path.iterdir()):
            raise FileExistsError(f"Target directory {dest_path} is not empty.")

        # Copy files from source folder
        for file in self.root_folder.iterdir():
            if file.is_dir() or file.name.endswith(self.IGNORED_FILE_PATTERNS):
                continue
            shutil.copy2(file, dest_path / file.name)

        return dest_path

    def _write_calibration_file(
        self,
        params: list[ParamModel]
    ) -> None:
        '''
        Writes `calibration.cal` file with parameter changes.
        '''

        outfile = self.root_folder / "calibration.cal"

        # If calibration.cal exists, remove it (always recreate)
        if outfile.exists():
            outfile.unlink()

        # make sure calibration.cal is enabled in file.cio
        self._add_or_remove_calibration_cal_to_file_cio(add=True)

        # Number of parameters (number of rows in the DataFrame)
        num_parameters = len(params)

        # Column widths for right-alignment
        col_widths = {
            "NAME": 12,      # left-aligned
            "CHG_TYPE": 8,
            "VAL": 16,
            "CONDS": 16,
            "LYR1": 8,
            "LYR2": 8,
            "YEAR1": 8,
            "YEAR2": 8,
            "DAY1": 8,
            "DAY2": 8,
            "OBJ_TOT": 8
        }

        calibration_cal_rows = []
        for change in params:
            units = change.units

            # Convert to compact representation
            compacted_units = utils._compact_units(units) if units else []

            # get conditions
            parsed_conditions = utils._parse_conditions(change)

            calibration_cal_rows.append({
                "NAME": change.name,
                "CHG_TYPE": change.change_type,
                "VAL": change.value,
                "CONDS": len(parsed_conditions),
                "LYR1": 0,
                "LYR2": 0,
                "YEAR1": 0,
                "YEAR2": 0,
                "DAY1": 0,
                "DAY2": 0,
                "OBJ_TOT": len(compacted_units),
                "OBJ_LIST": compacted_units,  # Store the compacted units
                "PARSED_CONDITIONS": parsed_conditions
            })

        with open(outfile, "w") as f:
            # Write header
            f.write(f"Number of parameters:\n{num_parameters}\n")
            headers = (
                f"{'NAME':<12}{'CHG_TYPE':<21}{'VAL':<14}{'CONDS':<9}"
                f"{'LYR1':<8}{'LYR2':<7}{'YEAR1':<8}{'YEAR2':<9}"
                f"{'DAY1':<8}{'DAY2':<5}{'OBJ_TOT':>7}"
            )
            f.write(f"{headers}\n")

            # Write rows
            for row in calibration_cal_rows:
                line = ""
                for col in ["NAME", "CHG_TYPE", "VAL", "CONDS", "LYR1", "LYR2",
                            "YEAR1", "YEAR2", "DAY1", "DAY2", "OBJ_TOT"]:
                    if col == "NAME":
                        line += f"{row[col]:<{col_widths[col]}}"   # left-align
                    elif col == "VAL" and isinstance(row[col], float):
                        line += utils._format_val_field(typing.cast(float, row[col]))  # special VAL formatting
                    else:
                        line += f"{row[col]:>{col_widths[col]}}"  # right-align numeric columns

                # Append compacted units at the end (space-separated)
                if row["OBJ_LIST"]:
                    line += "       " + "    ".join(str(u) for u in typing.cast(list[str], row["OBJ_LIST"]))

                if row["PARSED_CONDITIONS"]:
                    parsed_conditions = typing.cast(list[str], row["PARSED_CONDITIONS"])
                    line += "\n" + "\n".join(parsed_conditions)

                f.write(line + "\n")

    def _add_or_remove_calibration_cal_to_file_cio(
        self,
        add: bool
    ) -> None:
        '''
        Adds or removes the calibration line to 'file.cio'
        '''
        file_path = self.root_folder / "file.cio"
        if not file_path.exists():
            raise FileNotFoundError("file.cio file does not exist in the TxtInOut folder")

        fmt = (
            f"{'{:<18}'}"  # chg
            f"{'{:<18}'}"  # cal_parms.cal / null
            f"{'{:<18}'}"  # calibration.cal
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<18}'}"  # null
            f"{'{:<4}'}"   # null
        )

        # Prepare the values for the line
        cal_line_values = [
            "chg",
            "cal_parms.cal" if add else "null",
            "calibration.cal",
        ] + ["null"] * 9  # Fill remaining columns with null

        line_to_add = fmt.format(*cal_line_values)

        line_index = 21

        # Read all lines
        with file_path.open("r") as f:
            lines = f.readlines()

        # Safety check: ensure the file has enough lines
        if line_index >= len(lines):
            raise IndexError(f"The file only has {len(lines)} lines, cannot replace line {line_index+1}.")

        # Replace the line, ensure it ends with a newline
        lines[line_index] = line_to_add.rstrip() + "\n"

        # Write back
        with file_path.open("w") as f:
            f.writelines(lines)

    def _apply_swat_configuration(
        self,
        begin_and_end_year: typing.Optional[tuple[int, int]] = None,
        warmup: typing.Optional[int] = None,
        print_prt_control: typing.Optional[dict[str, dict[str, bool]]] = None
    ) -> None:
        '''
        Sets begin and end year for the simulation, the warm-up period, and toggles the elements in print.prt file
        '''
        # Set simulation range time
        if begin_and_end_year is not None:
            if not isinstance(begin_and_end_year, tuple):
                raise TypeError('begin_and_end_year must be a tuple')
            if len(begin_and_end_year) != 2:
                raise ValueError('begin_and_end_year must contain exactly two elements')
            begin, end = begin_and_end_year
            self.set_begin_and_end_year(
                begin=begin,
                end=end
            )

        # Set warmup period
        if warmup is not None:
            self.set_warmup_year(
                warmup=warmup
            )

        # Update print.prt file to write output
        if print_prt_control is not None:
            if not isinstance(print_prt_control, dict):
                raise TypeError('print_prt_control must be a dictionary')
            if len(print_prt_control) == 0:
                raise ValueError('print_prt_control cannot be an empty dictionary')
            default_dict = {
                'daily': True,
                'monthly': True,
                'yearly': True,
                'avann': True
            }
            for key, val in print_prt_control.items():
                if not isinstance(val, dict):
                    raise ValueError(f'Value of key "{key}" must be a dictionary')
                if len(val) == 0:
                    raise ValueError(f'Value of key "{key}" cannot be an empty dictionary')
                key_dict = default_dict.copy()
                for sub_key, sub_val in val.items():
                    if sub_key not in key_dict:
                        raise ValueError(f'Sub-key "{sub_key}" for key "{key}" is not valid')
                    key_dict[sub_key] = sub_val
                self.enable_object_in_print_prt(
                    obj=key,
                    daily=key_dict['daily'],
                    monthly=key_dict['monthly'],
                    yearly=key_dict['yearly'],
                    avann=key_dict['avann']
                )

    def _run_swat(
        self,
    ) -> None:
        '''
        Run the SWAT+ simulation.
        '''

        # Run simulation
        try:
            process = subprocess.Popen(
                [str(self.swat_exe_path.resolve())],
                cwd=str(self.root_folder.resolve()),  # Sets working dir just for this subprocess
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,  # Line buffered
                text=True   # Handles text output
            )

            # Real-time output handling
            if process.stdout:
                for line in process.stdout:
                    clean_line = line.strip()
                    if clean_line:
                        logger.info(clean_line)

            # Wait for process and check for errors
            return_code = process.wait()
            if return_code != 0:
                stderr = process.stderr.read() if process.stderr else None
                raise subprocess.CalledProcessError(
                    return_code,
                    process.args,
                    stderr=stderr
                )

        except Exception as e:
            logger.error(f"Failed to run SWAT: {str(e)}")
            raise

    def run_swat(
        self,
        params: typing.Optional[ParamsType] = None,
        skip_units_and_conditions_validation: bool = False
    ) -> pathlib.Path:
        '''
        Run the SWAT+ simulation with optional parameter changes.

        Args:
            params (ParamsType, optional): Nested dictionary specifying parameter changes.

                The `params` dictionary should follow this structure:

                ```python
                params = [
                    {
                        "name": str,            # Name of the parameter to which the changes will be applied
                        "value": float,         # New value to assign
                        "change_type": str,     # One of: 'absval', 'abschg', 'pctchg'
                        "units": Iterable[int],  # (Optional) An optional list of unit IDs to constrain the parameter change.
                            **Unit IDs should be 1-based**, i.e., the first object has ID 1.
                        "conditions": dict[str: list[str]],  # (Optional) A dictionary of conditions to apply to the parameter change.
                    },
                    ...
                ]
                ```
            skip_units_and_conditions_validation (bool): If `True`, skip validation of units and conditions in parameter changes.


        Returns:
            Path where the SWAT+ simulation was executed.

        Example:
            ```python
            params = [
                {
                    "name": 'cn2',
                    "change_type": "pctchg",
                    "value": 50,
                },
                {
                    "name": 'perco',
                    "change_type": "absval",
                    "value": 0.5,                        
                    "conditions": {"hsg": ["A"]}
                },
                {
                    'name': 'bf_max',
                    "change_type": "absval",
                    "value": 0.3,
                    "units": range(1, 194)
                }
            ]

            reader.run_swat(params)
            ```
        '''

        if params:
            _params = [ParamModel(**param) for param in params]

            validators._validate_cal_parameters(self.root_folder, _params)

            if not skip_units_and_conditions_validation:
                validators._validate_conditions_and_units(_params, self.root_folder)

            self._write_calibration_file(_params)

        # Run simulation
        self._run_swat()

        return self.root_folder

    def run_swat_in_other_dir(
        self,
        target_dir: str | pathlib.Path,
        params: typing.Optional[ParamsType] = None,
        begin_and_end_year: typing.Optional[tuple[int, int]] = None,
        warmup: typing.Optional[int] = None,
        print_prt_control: typing.Optional[dict[str, dict[str, bool]]] = None,
        skip_units_and_conditions_validation: bool = False
    ) -> pathlib.Path:
        '''
        Run the SWAT+ simulation with optional parameter changes.

        Args:

            target_dir (str or Path): Path to the directory where the simulation will be done.

            params (ParamsType, optional): Nested dictionary specifying parameter changes.

                The `params` dictionary should follow this structure:

                ```python
                params = [
                    {
                        "name": str,            # Name of the parameter to which the changes will be applied
                        "lower_bound": str      # The lower bound for the parameter
                        "upper_bound": str      # The upper bound for the parameter
                        "change_type": str,     # One of: 'absval', 'abschg', 'pctchg'
                        "units": Iterable[int],  # (Optional) An optional list of unit IDs to constrain the parameter change.
                            **Unit IDs should be 1-based**, i.e., the first object has ID 1.
                        "conditions": dict[str: list[str]],  # (Optional) A dictionary of conditions to apply to the parameter change.
                    },              
                    ...
                ]
                ```

            begin_and_end_year (tuple[int, int]): A tuple of begin and end years of the simulation in YYYY format. For example, (2012, 2016).

            warmup (int): A positive integer representing the number of warm-up years (e.g., 1).

            print_prt_control (dict[str, dict[str, bool]], optional): A dictionary to control output printing in the `print.prt` file.
                Each outer key is an object name from `print.prt` (e.g., 'channel_sd', 'basin_wb').
                Each value is a dictionary with keys `daily`, `monthly`, `yearly`, or `avann`, mapped to boolean values.
                Set to `False` to disable printing for that time step; defaults to `True` if not specified.
                An error is raised if an outer key has an empty dictionary.
                The time step keys represent:

                - `daily`: Output for each day of the simulation.
                - `monthly`: Output aggregated for each month.
                - `yearly`: Output aggregated for each year.
                - `avann`: Average annual output over the entire simulation period.

            skip_units_and_conditions_validation (bool): If `True`, skip validation of units and conditions in parameter changes.


        Returns:
            Path where the SWAT+ simulation was executed.

        Example:
            ```python
            simulation = pySWATPlus.TxtinoutReader.run_swat_in_other_dir(
                target_dir="C:\\\\Users\\\\Username\\\\simulation_folder",
                params = [
                    {
                        "name": "bf_max",
                        "change_type": "absval",
                        "lower_bound": 0.2,
                        "upper_bound": 0.3,
                        "units": range(1, 194)
                    }
                ]
                begin_and_end_year=(2012, 2016),
                warmup=1,
                print_prt_control = {
                    'channel_sd': {'daily': False},
                    'channel_sdmorph': {'monthly': False}
                }
            )
            ```
        '''

        tmp_path = self.copy_required_files(target_dir=target_dir)

        # Initialize new TxtinoutReader class
        reader = TxtinoutReader(tmp_path)

        # Apply SWAT+ configuration changes
        reader._apply_swat_configuration(begin_and_end_year, warmup, print_prt_control)

        # Run the SWAT+ simulation
        output = reader.run_swat(
            params=params,
            skip_units_and_conditions_validation=skip_units_and_conditions_validation
        )

        return output
