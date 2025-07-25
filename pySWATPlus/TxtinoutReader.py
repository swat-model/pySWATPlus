import subprocess
import shutil
import pathlib
import typing
import logging
from .FileReader import FileReader
from .types import ParamsType
from .utils import _build_line_to_add, _apply_param_change, _validate_params

logger = logging.getLogger(__name__)


class TxtinoutReader:

    RESERVED_PARAMS: typing.Final[list[str]] = ['has_units']
    IGNORED_FILE_PATTERNS: typing.Final[tuple[str, ...]] = tuple(
        f'_{suffix}.{ext}'
        for suffix in ('day', 'mon', 'yr', 'aa')
        for ext in ('txt', 'csv')
    )

    def __init__(
        self,
        path: str | pathlib.Path
    ) -> None:
        """
        Initialize a TxtinoutReader instance for working with SWAT+ model data.

        Args:
            path (str or Path): The path to the SWAT+ model `TxtinOut` folder.

        Raises:
            TypeError: If the provided path is not a string or Path object,
                    if more than one .exe file is found,
                    or if no .exe file is found.
            FileNotFoundError: If the folder does not exist.
        """

        # check if path is a string or a path
        if not isinstance(path, (str, pathlib.Path)):
            raise TypeError("path must be a string or os.PathLike object")

        path = pathlib.Path(path).resolve()

        # check if folder exists
        if not path.is_dir():
            raise FileNotFoundError("Folder does not exist")

        # check .exe files in the directory
        exe_list = [file for file in path.iterdir() if file.suffix == ".exe"]

        # raise error if empty list
        if not exe_list:
            raise TypeError(".exe not found in parent folder")

        # raise error if more than one .exe file
        if len(exe_list) > 1:
            raise TypeError("More than one .exe file found in the parent folder")

        # find parent directory
        self.root_folder = path
        self.swat_exe_path = path / exe_list[0]

    def enable_object_in_print_prt(
        self,
        obj: str,
        daily: bool,
        monthly: bool,
        yearly: bool,
        avann: bool
    ) -> None:
        """
        Enable or update an object in the 'print.prt' file. If obj is not a default identifier, it will be added at the end of the file.

        Args:
            obj (str): The object name or identifier.
            daily (bool): Flag for daily print frequency.
            monthly (bool): Flag for monthly print frequency.
            yearly (bool): Flag for yearly print frequency.
            avann (bool): Flag for average annual print frequency.

        Returns:
            None
        """

        # check if obj is object itself or file
        if pathlib.Path(obj).suffix:
            arg_to_add = obj.rsplit('_', maxsplit=1)[0]
        else:
            arg_to_add = obj

        # read all print_prt file, line by line
        print_prt_path = self.root_folder / 'print.prt'
        new_print_prt = ""
        found = False
        with open(print_prt_path) as file:
            for line in file:
                if not line.startswith(arg_to_add + ' '):  # Line must start exactly with arg_to_add, not a word that starts with arg_to_add
                    new_print_prt += line
                else:
                    # obj already exist, replace it in same position
                    new_print_prt += _build_line_to_add(arg_to_add, daily, monthly, yearly, avann)
                    found = True

        if not found:
            new_print_prt += _build_line_to_add(arg_to_add, daily, monthly, yearly, avann)

        # store new print_prt
        with open(print_prt_path, 'w') as file:
            file.write(new_print_prt)

    def set_begin_and_end_year(
        self,
        begin: int,
        end: int
    ) -> None:

        '''
        Modify the simulation period by updating the begin and end years in the `time.sim` file.

        Parameters:
            begin (int): Beginning year of the simulation (e.g., 2010).
            end (int): Ending year of the simulation (e.g., 2016).

        Returns:
            None
        '''

        nth_line = 3

        time_sim_path = self.root_folder / 'time.sim'

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
        Modify the warm-up years in the `time.sim` file.

        Args:
            warmup (int): A positive integer representing the number of years
                the simulation will use for warm-up (e.g., 1).

        Returns:
            None
        '''

        time_sim_path = self.root_folder / 'print.prt'

        # Open the file in read mode and read its contents
        with open(time_sim_path, 'r') as file:
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

        with open(time_sim_path, 'w') as file:
            file.writelines(lines)

    def _enable_disable_csv_print(
        self,
        enable: bool = True
    ) -> None:
        """
        Enable or disable CSV print in the 'print.prt' file.

        Parameters:
            enable (bool): True to enable CSV print, False to disable (default is True).

        Returns:
            None
        """

        # read
        nth_line = 7

        # time_sim_path = f"{self.root_folder}\\{'time.sim'}"
        print_prt_path = self.root_folder / 'print.prt'

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
        """
        Enable CSV print in the 'print.prt' file.

        Returns:
            None
        """

        self._enable_disable_csv_print(enable=True)

    def disable_csv_print(
        self
    ) -> None:
        """
        Disable CSV print in the 'print.prt' file.

        Returns:
            None
        """

        self._enable_disable_csv_print(enable=False)

    def register_file(
        self,
        filename: str,
        has_units: bool = False,
        usecols: typing.Optional[list[str]] = None,
        filter_by: typing.Optional[str] = None
    ) -> FileReader:
        """
        Register a file to work with in the SWAT+ model.

        Parameters:
            filename (str): The name of the file to register.
            has_units (bool): Indicates if the file has units information (default is False).
            usecols (List[str], optional): A list of column names to read (default is None).
            filter_by (str, optional): Pandas query string to select applicable rows (default is None).

        Returns:
            FileReader: A FileReader instance for the registered file.
        """

        file_path = self.root_folder / filename

        return FileReader(file_path, has_units, usecols, filter_by)

    def _copy_swat(
        self,
        target_dir: str | pathlib.Path,
    ) -> str:
        """
        Prepare a working directory containing the necessary SWAT+ model files.

        This function copies the contents of the SWAT model input folder (`self.root_folder`)
        to a target directory.

        Parameters:
            target_dir (str or Path): Destination directory for the SWAT model files.

        Returns:
            str: The path to the directory where the SWAT files were copied.
        """

        dest_path = pathlib.Path(target_dir)

        # Copy files from source folder
        for file in self.root_folder.iterdir():
            if file.is_dir() or file.name.endswith(self.IGNORED_FILE_PATTERNS):
                continue
            shutil.copy2(file, dest_path / file.name)

        return str(dest_path)

    def _run_swat(
        self,
    ) -> None:
        """
        Run the SWAT+ simulation.

        Returns:
            None

        Raises:
            subprocess.CalledProcessError: If the SWAT executable fails
            FileNotFoundError: If the SWAT executable is not found
        """

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
        params: ParamsType = None,
    ) -> pathlib.Path:
        """
        Run the SWAT+ simulation with optional parameter changes.

        Args:
            params (ParamsType, optional): Nested dictionary specifying parameter changes to apply.

                The `params` dictionary should follow this structure:

                ```python
                params = {
                    "<input_file>": {
                        "has_units": bool,              # Optional. Whether the file has units information (default is False)
                        "<parameter_name>": [           # One or more changes to apply to the parameter
                            {
                                "value": float,         # New value to assign
                                "change_type": str,     # (Optional) One of: 'absval' (default), 'abschg', 'pctchg'
                                "filter_by": str        # (Optional) pandas `.query()` filter string to select rows
                            },
                            # ... more changes
                        ]
                    },
                    # ... more input files
                }
                ```

        Returns:
            str: The path where the SWAT simulation was executed.

        Example:
            ```python
            params = {
                'plants.plt': {
                    'has_units': False,
                    'bm_e': [
                        {'value': 100, 'change_type': 'absval', 'filter_by': 'name == "agrl"'},
                        {'value': 110, 'change_type': 'absval', 'filter_by': 'name == "almd"'},
                    ],
                },
            }

            reader.run_swat(params)
            ```
        """

        _params = params or {}

        _validate_params(_params)

        # Modify files for simulation
        for filename, file_params in _params.items():
            has_units = file_params.get('has_units', False)

            # adding block only for mypy validation, as it's already validated in _validate_params
            if not isinstance(has_units, bool):
                raise TypeError(f"`has_units` for file '{filename}' must be a boolean.")

            file = self.register_file(
                filename,
                has_units=has_units
            )
            df = file.df

            for param_name, param_spec in file_params.items():
                if param_name in self.RESERVED_PARAMS:
                    continue  # Skip reserved parameters

                # adding block only for mypy validation, as it's already validated in _validate_params
                if isinstance(param_spec, bool):
                    raise TypeError(f"Unexpected bool value for parameter '{param_name}' in file '{filename}'")

                # Normalize to list of changes
                changes = param_spec if isinstance(param_spec, list) else [param_spec]

                # Process each parameter change
                for change in changes:
                    _apply_param_change(df, param_name, change)

            # Store the modified file
            file.overwrite_file()

        # run simulation
        self._run_swat()

        return self.root_folder

    def run_swat_in_other_dir(
        self,
        target_dir: str | pathlib.Path,
        params: ParamsType = None,
    ) -> pathlib.Path:
        """
        Copy the SWAT+ model files to a specified directory, modify input parameters, and run the simulation.

        Args:
            target_dir (str or Path): Path to the directory where the SWAT model files will be copied.

            params (ParamsType, optional): Nested dictionary specifying parameter changes.

                The `params` dictionary should follow this structure:

                ```python
                params = {
                    "<input_file>": {
                        "has_units": bool,              # Optional. Whether the file has units information (default is False)
                        "<parameter_name>": [           # One or more changes to apply to the parameter
                            {
                                "value": float,         # New value to assign
                                "change_type": str,     # (Optional) One of: 'absval' (default), 'abschg', 'pctchg'
                                "filter_by": str        # (Optional) pandas `.query()` filter string to select rows
                            },
                            # ... more changes
                        ]
                    },
                    # ... more input files
                }
                ```

        Returns:
            str: The path to the directory where the SWAT simulation was executed.

        Example:
            ```python
            params = {
                'plants.plt': {
                    'has_units': False,
                    'bm_e': [
                        {'value': 100, 'change_type': 'absval', 'filter_by': 'name == "agrl"'},
                        {'value': 110, 'change_type': 'absval', 'filter_by': 'name == "almd"'},
                    ],
                },
            }

            with tempfile.TemporaryDirectory() as tmp_dir:
                simulation = pySWATPlus.TxtinoutReader.run_swat_in_other_dir(
                    target_dir=tmp_dir,
                    params=params
                )
            ```
        """

        # Validate target_dir
        if not isinstance(target_dir, (str, pathlib.Path)):
            raise TypeError("target_dir must be a string or Path object")

        target_dir = pathlib.Path(target_dir).resolve()

        # Create the directory if it does not exist
        target_dir.mkdir(parents=True, exist_ok=True)

        tmp_path = self._copy_swat(target_dir=target_dir)
        reader = TxtinoutReader(tmp_path)

        return reader.run_swat(params)
