import subprocess
import shutil
import pathlib
import typing
import logging
from . import newtype
from . import utils
from . import validators

logger = logging.getLogger(__name__)


class TxtinoutReader:
    '''
    Provide functionality for seamless reading, editing, and writing of
    SWAT+ model files located in the `TxtInOut` folder.
    '''

    def __init__(
        self,
        tio_dir: str | pathlib.Path
    ) -> None:
        '''
        Create a TxtinoutReader instance for accessing SWAT+ model files.

        Args:
            tio_dir (str | pathlib.Path): Path to the `TxtInOut` directory, which must contain
                exactly one SWAT+ executable `.exe` file.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.__class__.__init__
            ),
            vars_values=locals()
        )

        # Absolute path
        tio_dir = pathlib.Path(tio_dir).resolve()

        # Check validity of path
        validators._dir_path(
            input_dir=tio_dir
        )

        # Check executable files in the directory
        exe_files = utils._find_executables(tio_dir)

        # Raise error on executable files
        if len(exe_files) != 1:
            raise TypeError(
                'Expected exactly one executable file in the parent folder, but found none or multiple'
            )

        # TxtInOut directory path
        self.root_dir = tio_dir

        # EXE file path
        self.exe_file = tio_dir / exe_files[0]

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
        Update the `print.prt` file to enable or disable output for a specific object (or all objects if `obj` is None)
        at specified time frequencies (daily, monthly, yearly, or average annual). If the object does not exist in the file
        and `obj` is not None, it is appended to the end of the file.

        Note:
            This input does not provide complete control over `print.prt` outputs.
            Some files are internally linked in the SWAT+ model and may still be
            generated even when disabled.

        Args:
            obj (str | None): The name of the object to update (e.g., 'channel_sd', 'reservoir').
                If `None`, all objects in the `print.prt` file are updated with the specified time frequency settings.
            daily (bool): If `True`, enable daily frequency output.
            monthly (bool): If `True`, enable monthly frequency output.
            yearly (bool): If `True`, enable yearly frequency output.
            avann (bool): If `True`, enable average annual frequency output.
            allow_unavailable_object (bool, optional): If True, allows adding an object not in
                the standard SWAT+ output object list. If False and `obj` is not in the standard list,
                a ValueError is raised. Defaults to False.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.enable_object_in_print_prt
            ),
            vars_values=locals()
        )

        # Dictionary of available objects
        obj_dict = {
            'model_components': ['channel', 'channel_sd', 'channel_sdmorph', 'aquifer', 'reservoir', 'recall', 'ru', 'hyd', 'water_allo'],
            'basin_model_components': ['basin_cha', 'basin_sd_cha', 'basin_sd_chamorph', 'basin_aqu', 'basin_res', 'basin_psc'],
            'region_model_components': ['region_sd_cha', 'region_aqu', 'region_res', 'region_psc'],
            'nutrient_balance': ['basin_nb', 'lsunit_nb', 'hru_nb', 'hru-lte_nb', 'region_nb'],
            'water_balance': ['basin_wb', 'lsunit_wb', 'hru_wb', 'hru-lte_wb', 'region_wb'],
            'plant_weather': ['basin_pw', 'lsunit_pw', 'hru_pw', 'hru-lte_pw', 'region_pw'],
            'losses': ['basin_ls', 'lsunit_ls', 'hru_ls', 'hru-lte_ls', 'region_ls'],
            'salts': ['basin_salt', 'hru_salt', 'ru_salt', 'aqu_salt', 'channel_salt', 'res_salt', 'wetland_salt'],
            'constituents': ['basin_cs', 'hru_cs', 'ru_cs', 'aqu_cs', 'channel_cs', 'res_cs', 'wetland_cs']
        }

        # List of objects obtained from the dictionary
        obj_list = [
            i for v in obj_dict.values() for i in v
        ]

        # Check 'obj' is valid
        if obj and obj not in obj_list and not allow_unavailable_object:
            raise ValueError(
                f'Object "{obj}" not found in print.prt file; use "allow_unavailable_object=True" to proceed'
            )

        # File path of print.prt
        print_prt_path = self.root_dir / 'print.prt'

        # Read and modify print.prt file strings
        new_print_prt = ''
        found = False
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
                    new_print_prt += utils._print_prt_line_add(
                        obj=line_obj,
                        daily=daily,
                        monthly=monthly,
                        yearly=yearly,
                        avann=avann
                    )
                elif line_obj == obj:
                    # Already 'obj' exist, replace it in same position
                    new_print_prt += utils._print_prt_line_add(
                        obj=line_obj,
                        daily=daily,
                        monthly=monthly,
                        yearly=yearly,
                        avann=avann
                    )
                    found = True
                else:
                    new_print_prt += line

        if not found and obj is not None:
            new_print_prt += utils._print_prt_line_add(
                obj=obj,
                daily=daily,
                monthly=monthly,
                yearly=yearly,
                avann=avann
            )

        # Store modified print.prt file
        with open(print_prt_path, 'w', newline='') as file:
            file.write(new_print_prt)

        return None

    def set_simulation_period(
        self,
        begin_date: str,
        end_date: str,
    ) -> None:
        '''
        Modify the simulation period by updating
        the begin and end dates in the `time.sim` file.

        Args:
            begin_date (str): Start date of the simulation in DD-Mon-YYYY format (e.g., 01-Jan-2010).
            end_date (str): End date of the simulation in DD-Mon-YYYY format (e.g., 31-Dec-2013).
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.set_simulation_period
            ),
            vars_values=locals()
        )

        # Convert date string to datetime.date object
        begin_dt = utils._date_str_to_object(
            date_str=begin_date
        )
        end_dt = utils._date_str_to_object(
            date_str=end_date
        )

        # Check begin date is earlier than end date
        validators._date_begin_earlier_end(
            begin_date=begin_dt,
            end_date=end_dt
        )

        # Extract years and Julian days
        begin_day = begin_dt.timetuple().tm_yday
        begin_year = begin_dt.year
        end_day = end_dt.timetuple().tm_yday
        end_year = end_dt.year

        # Target line
        nth_line = 3

        # File path of time.sim
        time_sim_path = self.root_dir / 'time.sim'

        # Open the file in read mode and read its contents
        with open(time_sim_path, 'r') as file:
            lines = file.readlines()

        # Split targeted line
        elements = lines[nth_line - 1].split()

        # Update values
        elements[0] = str(begin_day)
        elements[1] = str(begin_year)
        elements[2] = str(end_day)
        elements[3] = str(end_year)

        # Reconstruct the result string while maintaining spaces
        result_string = '{: >8} {: >10} {: >10} {: >10} {: >10} \n'.format(*elements)
        lines[nth_line - 1] = result_string

        # Modify time.sim file
        with open(time_sim_path, 'w') as file:
            file.writelines(lines)

        return None

    def set_simulation_timestep(
        self,
        step: int
    ) -> None:
        '''
        Modify the simulation timestep.

        Args:
            step (int): Simulation timestep. Allowed values are:

                - `0` = 1 day
                - `1` = 12 hours
                - `24` = 1 hour
                - `96` = 15 minutes
                - `1440` = 1 minute
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.set_simulation_timestep
            ),
            vars_values=locals()
        )

        # Valid time step dictionary
        valid_steps = {
            0: '1 day',
            1: '12 hours',
            24: '1 hour',
            96: '15 minutes',
            1440: '1 minute',
        }

        # Check valid steps
        if step not in valid_steps:
            raise ValueError(
                f'Received invalid step: {step}; must be one of the keys in {valid_steps}'
            )

        # Target line
        nth_line = 3

        # File path of time.sim
        time_sim_path = self.root_dir / 'time.sim'

        # Open the file in read mode and read its contents
        with open(time_sim_path, 'r') as file:
            lines = file.readlines()

        # Split targeted line
        elements = lines[nth_line - 1].split()

        # Update values
        elements[4] = str(step)

        # Reconstruct the result string while maintaining spaces
        result_string = '{: >8} {: >10} {: >10} {: >10} {: >10} \n'.format(*elements)
        lines[nth_line - 1] = result_string

        # Modify time.sim file
        with open(time_sim_path, 'w') as file:
            file.writelines(lines)

        return None

    def set_warmup_year(
        self,
        warmup: int
    ) -> None:
        '''
        Modify the warm-up years in the `print.prt` file.

        Args:
            warmup (int): Warm-up years for the simulation, must be ≥ 1.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.set_warmup_year
            ),
            vars_values=locals()
        )

        # Check warmup year is greater than 0
        if warmup <= 0:
            raise ValueError(
                f'Expected warmup >= 1, but received warmup = {warmup}'
            )

        # File path of print.prt
        print_prt_path = self.root_dir / 'print.prt'

        # Open the file in read mode and read its contents
        with open(print_prt_path, 'r') as file:
            lines = file.readlines()

        # Target line
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

        return None

    def _enable_disable_csv_print(
        self,
        enable: bool = True
    ) -> None:
        '''
        Enable or disable print in the `print.prt` file.
        '''

        # File path of print.prt
        print_prt_path = self.root_dir / 'print.prt'

        # Target line
        nth_line = 7

        # Open the file in read mode and read its contents
        with open(print_prt_path, 'r') as file:
            lines = file.readlines()

        # Change line string
        if enable:
            lines[nth_line - 1] = 'y' + lines[nth_line - 1][1:]
        else:
            lines[nth_line - 1] = 'n' + lines[nth_line - 1][1:]

        # Modify print.prt file
        with open(print_prt_path, 'w') as file:
            file.writelines(lines)

        return None

    def enable_csv_print(
        self
    ) -> None:
        '''
        Enable print in the `print.prt` file.
        '''

        self._enable_disable_csv_print(enable=True)

        return None

    def disable_csv_print(
        self
    ) -> None:
        '''
        Disable print in the `print.prt` file.
        '''

        self._enable_disable_csv_print(enable=False)

        return None

    def set_print_interval(
        self,
        interval: int,
    ) -> None:
        '''
        Set the print interval in the `print.prt` file.

        Args:
            interval (int): The output print interval within the simulation period.
                For example, if `interval = 2`, output will be printed every other day.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.set_print_interval
            ),
            vars_values=locals()
        )

        # File path of print.prt
        print_prt_path = self.root_dir / 'print.prt'

        # Open the file in read mode and read its contents
        with open(print_prt_path, 'r') as file:
            lines = file.readlines()

            nth_line = 3
            columns = lines[nth_line - 1].split()
            lines[nth_line - 1] = f"{columns[0]:<12}{columns[1]:<11}{columns[2]:<11}{columns[3]:<10}{columns[4]:<10}{interval}\n"

        # Modify print.prt file
        with open(print_prt_path, 'w') as file:
            file.writelines(lines)

        return None

    def set_print_period(
        self,
        begin_date: str,
        end_date: str,
    ) -> None:
        '''
        Set the start and end date in the `print.prt` file to define when output files begin recording simulation results.

        Args:
            begin_date (str): Start date in `DD-Mon-YYYY` format (e.g., 01-Jun-2010).
            end_date (str): End date in `DD-Mon-YYYY` format (e.g., 31-Dec-2020).
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.set_print_period
            ),
            vars_values=locals()
        )

        # Convert date string to datetime.date object
        begin_dt = utils._date_str_to_object(
            date_str=begin_date
        )
        end_dt = utils._date_str_to_object(
            date_str=end_date
        )

        # Check begin date is earlier than end date
        validators._date_begin_earlier_end(
            begin_date=begin_dt,
            end_date=end_dt
        )

        # Extract years and Julian days
        start_day = begin_dt.timetuple().tm_yday
        start_year = begin_dt.year
        end_day = end_dt.timetuple().tm_yday
        end_year = end_dt.year

        # File path of print.prt
        print_prt_path = self.root_dir / 'print.prt'

        # Open the file in read mode and read its contents
        with open(print_prt_path, 'r') as file:
            lines = file.readlines()

            nth_line = 3
            columns = lines[nth_line - 1].split()
            lines[nth_line - 1] = f"{columns[0]:<12}{start_day:<11}{start_year:<11}{end_day:<10}{end_year:<10}{columns[5]}\n"

        # Modify print.prt file
        with open(print_prt_path, 'w') as file:
            file.writelines(lines)

        return None

    def copy_required_files(
        self,
        sim_dir: str | pathlib.Path,
    ) -> pathlib.Path:
        '''
        Copy the required file from the input directory associated with the
        `TxtinoutReader` instance to the specified directory for SWAT+ simulation.

        Args:
            sim_dir (str | pathlib.Path): Path to the empty directory where the required files will be copied.

        Returns:
            The path to the target directory containing the copied files.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.copy_required_files
            ),
            vars_values=locals()
        )

        # Absolute path of sim_dir
        sim_dir = pathlib.Path(sim_dir).resolve()

        # Check validity of sim_dir
        validators._dir_path(
            input_dir=sim_dir
        )

        # Check sim_dir is empty
        validators._dir_empty(
            input_dir=sim_dir
        )

        # Ignored files
        _ignored_files_endswith = tuple(
            f'_{suffix}.{ext}'
            for suffix in ('day', 'mon', 'yr', 'aa')
            for ext in ('txt', 'csv')
        )

        # Copy files from source folder
        for src_file in self.root_dir.iterdir():
            if src_file.is_dir() or src_file.name.endswith(_ignored_files_endswith):
                continue
            shutil.copy2(src_file, sim_dir / src_file.name)

        return sim_dir

    def _write_calibration_file(
        self,
        parameters: list[newtype.ModifyDict]
    ) -> None:
        '''
        Writes `calibration.cal` file with parameter changes.
        '''

        outfile = self.root_dir / 'calibration.cal'

        # If calibration.cal exists, remove it (always recreate)
        if outfile.exists():
            outfile.unlink()

        # Make sure calibration.cal is enabled in file.cio
        self._calibration_cal_in_file_cio(
            add=True
        )

        # Number of parameters (number of rows in the DataFrame)
        num_parameters = len(parameters)

        # Column widths for right-alignment
        col_widths = {
            'NAME': 12,
            'CHG_TYPE': 8,
            'VAL': 16,
            'CONDS': 16,
            'LYR1': 8,
            'LYR2': 8,
            'YEAR1': 8,
            'YEAR2': 8,
            'DAY1': 8,
            'DAY2': 8,
            'OBJ_TOT': 8
        }

        calibration_cal_rows = []
        for change in parameters:
            units = change.units

            # Convert to compact representation
            compacted_units = utils._dict_units_compact(units) if units else []

            # get conditions
            parsed_conditions = utils._dict_conditions_parse(change)

            calibration_cal_rows.append(
                {
                    'NAME': change.name,
                    'CHG_TYPE': change.change_type,
                    'VAL': change.value,
                    'CONDS': len(parsed_conditions),
                    'LYR1': 0,
                    'LYR2': 0,
                    'YEAR1': 0,
                    'YEAR2': 0,
                    'DAY1': 0,
                    'DAY2': 0,
                    'OBJ_TOT': len(compacted_units),
                    'OBJ_LIST': compacted_units,
                    'PARSED_CONDITIONS': parsed_conditions
                }
            )

        with open(outfile, 'w') as f:
            # Write header
            f.write(f'Number of parameters:\n{num_parameters}\n')
            headers = (
                f"{'NAME':<12}{'CHG_TYPE':<21}{'VAL':<14}{'CONDS':<9}"
                f"{'LYR1':<8}{'LYR2':<7}{'YEAR1':<8}{'YEAR2':<9}"
                f"{'DAY1':<8}{'DAY2':<5}{'OBJ_TOT':>7}"
            )
            f.write(f'{headers}\n')

            # Write rows
            col_names = [c for c in col_widths]
            for row in calibration_cal_rows:
                line = ''
                for col in col_names:
                    if col == 'NAME':
                        line += f'{row[col]:<{col_widths[col]}}'   # left-align
                    elif col == 'VAL' and isinstance(row[col], float):
                        line += utils._calibration_val_field_str(typing.cast(float, row[col]))  # special VAL formatting
                    else:
                        line += f'{row[col]:>{col_widths[col]}}'  # right-align numeric columns

                # Append compacted units at the end (space-separated)
                if row['OBJ_LIST']:
                    line += '       ' + '    '.join(str(u) for u in typing.cast(list[str], row['OBJ_LIST']))

                if row['PARSED_CONDITIONS']:
                    parsed_conditions = typing.cast(list[str], row['PARSED_CONDITIONS'])
                    line += '\n' + '\n'.join(parsed_conditions)

                f.write(line + '\n')

        return None

    def _calibration_cal_in_file_cio(
        self,
        add: bool
    ) -> None:
        '''
        Add or remove the calibration line to 'file.cio'.
        '''

        # Path of file.cio
        file_path = self.root_dir / 'file.cio'

        # Line format
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
            'chg',
            'cal_parms.cal' if add else 'null',
            'calibration.cal',
        ] + ['null'] * 9
        line_to_add = fmt.format(*cal_line_values)

        # Line index for calibration.cal
        line_index = 21

        # Read all lines
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Safety check: ensure the file has enough lines
        if line_index >= len(lines):
            raise IndexError(
                f'The file only has {len(lines)} lines, cannot replace line {line_index + 1}'
            )

        # Replace the line, ensure it ends with a newline
        lines[line_index] = line_to_add.rstrip() + '\n'

        # Modify file.cio
        with open(file_path, 'w') as f:
            f.writelines(lines)

        return None

    def _apply_swat_configuration(
        self,
        begin_date: typing.Optional[str] = None,
        end_date: typing.Optional[str] = None,
        simulation_timestep: typing.Optional[int] = None,
        warmup: typing.Optional[int] = None,
        print_prt_control: typing.Optional[dict[str, dict[str, bool]]] = None,
        print_begin_date: typing.Optional[str] = None,
        print_end_date: typing.Optional[str] = None,
        print_interval: typing.Optional[int] = None
    ) -> None:
        '''
        Configure and write parameter settings to SWAT+ input files.
        '''

        # Ensure both begin and end dates are given
        validators._variables_defined_or_none(
            begin_date=begin_date,
            end_date=end_date
        )

        # Ensure both begin and end print dates are given
        validators._variables_defined_or_none(
            print_begin_date=print_begin_date,
            print_end_date=print_end_date
        )

        # Validate dependencies between simulation and print periods
        if (print_begin_date or print_end_date) and not (begin_date and end_date):
            raise ValueError(
                'print_begin_date or print_end_date cannot be set unless begin_date and end_date are also provided'
            )

        # Validate date relationships
        if print_begin_date and print_end_date and begin_date and end_date:
            begin_dt = utils._date_str_to_object(begin_date)
            end_dt = utils._date_str_to_object(end_date)
            start_print_dt = utils._date_str_to_object(print_begin_date)
            end_print_dt = utils._date_str_to_object(print_end_date)

            validators._date_within_range(
                date_to_check=start_print_dt,
                begin_date=begin_dt,
                end_date=end_dt
            )
            validators._date_within_range(
                date_to_check=end_print_dt,
                begin_date=begin_dt,
                end_date=end_dt
            )

        # Set simulation range time
        if begin_date and end_date:
            self.set_simulation_period(
                begin_date=begin_date,
                end_date=end_date
            )

        # Set simulation timestep
        if simulation_timestep is not None:
            self.set_simulation_timestep(
                step=simulation_timestep
            )

        # Set warmup period
        if warmup is not None:
            self.set_warmup_year(
                warmup=warmup
            )

        # Update print.prt file to write output
        if print_prt_control is not None:
            default_dict = {
                'daily': True,
                'monthly': True,
                'yearly': True,
                'avann': True
            }
            for key, val in print_prt_control.items():
                if key is None:
                    raise ValueError(
                        'Use enable_object_in_print_prt method instead of None as a key in print_prt_control'
                    )
                elif not isinstance(val, dict):
                    raise TypeError(
                        f'Expected a dictionary for key "{key}" in print_prt_control, but got type "{type(val).__name__}"'
                    )
                elif len(val) == 0:
                    self.enable_object_in_print_prt(
                        obj=key,
                        **default_dict
                    )
                else:
                    key_dict = default_dict.copy()
                    for sub_key, sub_val in val.items():
                        if sub_key not in key_dict:
                            raise KeyError(
                                f'Invalids sub-key "{sub_key}" for key "{key}" in print_prt_control, '
                                f'expected sub-keys are [{", ".join(key_dict.keys())}]'
                            )
                        key_dict[sub_key] = sub_val
                    self.enable_object_in_print_prt(
                        obj=key,
                        **key_dict
                    )

        if print_begin_date and print_end_date:
            self.set_print_period(
                begin_date=print_begin_date,
                end_date=print_end_date
            )

        if print_interval is not None:
            self.set_print_interval(
                interval=print_interval
            )

        return None

    def _run_swat_exe(
        self,
    ) -> None:
        '''
        Run the SWAT+ simulation.
        '''

        try:
            # Run simulation
            process = subprocess.Popen(
                [str(self.exe_file.resolve())],
                cwd=str(self.root_dir.resolve()),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                text=True
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
        # Raise error
        except Exception as e:
            logger.error(f'Failed to run SWAT: {str(e)}')
            raise

        return None

    def run_swat(
        self,
        sim_dir: typing.Optional[str | pathlib.Path] = None,
        parameters: typing.Optional[newtype.ModifyType] = None,
        begin_date: typing.Optional[str] = None,
        end_date: typing.Optional[str] = None,
        simulation_timestep: typing.Optional[int] = None,
        warmup: typing.Optional[int] = None,
        print_prt_control: typing.Optional[dict[str, dict[str, bool]]] = None,
        print_begin_date: typing.Optional[str] = None,
        print_end_date: typing.Optional[str] = None,
        print_interval: typing.Optional[int] = None,
        skip_validation: bool = False
    ) -> pathlib.Path:
        '''
        Run the SWAT+ simulation with optional parameter changes.

        Args:
            sim_dir (str | pathlib.Path): Path to the directory where the simulation will be done.
                If None, the simulation runs directly in the current folder.

            parameters (newtype.ModifyType): List of dictionaries specifying parameter changes in the `calibration.cal` file.
                Each dictionary contain the following keys:

                - `name` (str): **Required.** Name of the parameter in the `cal_parms.cal` file.
                - `change_type` (str): **Required.** Type of change to apply. Must be one of `absval`, `abschg`, or `pctchg`.
                - `value` (float): **Required.** Value of the parameter.
                - `units` (Iterable[int]): Optional. List of unit IDs to which the parameter change should be constrained.
                - `conditions` (dict[str, list[str]]): Optional. Conditions to apply when changing the parameter.
                  Supported keys include `'hsg'`, `'texture'`, `'plant'`, and `'landuse'`, each mapped to a list of allowed values.

                Examples:
                ```python
                parameters = [
                    {
                        'name': 'cn2',
                        'change_type': 'pctchg',
                        'value': 50,
                    },
                    {
                        'name': 'perco',
                        'change_type': 'absval',
                        'value': 0.5,
                        'conditions': {'hsg': ['A']}
                    },
                    {
                        'name': 'bf_max',
                        'change_type': 'absval',
                        'value': 0.3,
                        'units': range(1, 194)
                    }
                ]
                ```

            begin_date (str): Start date of the simulation in DD-Mon-YYYY format (e.g., 01-Jan-2010).

            end_date (str): End date of the simulation in DD-Mon-YYYY format (e.g., 31-Dec-2013).

            simulation_timestep (int): Simulation timestep. Defaults to 0. Allowed values:
                - `0` = 1 day
                - `1` = 12 hours
                - `24` = 1 hour
                - `96` = 15 minutes
                - `1440` = 1 minute

            warmup (int): A positive integer representing the number of warm-up years (e.g., 1).

            print_prt_control (dict[str, dict[str, bool]]): A dictionary to control output printing in the `print.prt` file.
                Each outer key corresponds to an object name from `print.prt` (e.g., 'channel_sd', 'basin_wb').
                Each value is a dictionary with keys `daily`, `monthly`, `yearly`, or `avann`, mapped to boolean values.
                Set to `False` to disable printing for a specific time step; defaults to `True` if an empty dictionary is provided.
                The time step keys represent:

                - `daily`: Output for each simulation day.
                - `monthly`: Output aggregated by month.
                - `yearly`: Output aggregated by year.
                - `avann`: Average annual output over the entire simulation period.

                Examples:
                ```python
                print_prt_control = {
                    'channel_sd': {},  # set True for all time frequency
                    'channel_sdmorph': {'monthly': False}
                }
                ```

            print_begin_date (str): The start date for printing the output.

            print_end_date (str): The end date for printing the output.

            print_interval (int): Print interval within the period. For example, if interval = 2, output will be printed for every other day.

            skip_validation (bool): If `True`, skip validation of units and conditions in parameter changes.

        Returns:
            Path where the SWAT+ simulation was executed.
        '''

        # Check input variables type
        validators._variable_origin_static_type(
            vars_types=typing.get_type_hints(
                obj=self.run_swat
            ),
            vars_values=locals()
        )

        # TxtinoutReader class instance
        if sim_dir is not None:
            sim_dir = pathlib.Path(sim_dir).resolve()
            # Check validity of sim_dir
            validators._dir_path(
                input_dir=sim_dir
            )
            run_path = self.copy_required_files(
                sim_dir=sim_dir
            )
            reader = TxtinoutReader(
                tio_dir=run_path
            )
        else:
            reader = self
            run_path = self.root_dir

        # Apply SWAT+ configuration changes
        reader._apply_swat_configuration(
            begin_date=begin_date,
            end_date=end_date,
            simulation_timestep=simulation_timestep,
            warmup=warmup,
            print_prt_control=print_prt_control,
            print_begin_date=print_begin_date,
            print_end_date=print_end_date,
            print_interval=print_interval
        )

        # Create calibration.cal file
        if parameters is not None:

            # List of ModifyDict objects
            params = utils._parameters_modify_dict_list(
                parameters=parameters,
            )

            # Check if input calibration parameters exists in cal_parms.cal
            validators._calibration_parameters(
                input_dir=reader.root_dir,
                parameters=params
            )

            if not skip_validation:
                validators._calibration_conditions_and_units(
                    input_dir=reader.root_dir,
                    parameters=params
                )

            reader._write_calibration_file(
                parameters=params
            )

        # Run simulation
        reader._run_swat_exe()

        return run_path
