import subprocess
import os
from .FileReader import FileReader
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Any, Union

class TxtinoutReader:

    def __init__(
        self,
        path: Union[str, os.PathLike]
    ) -> None:

        """
        Initialize a TxtinoutReader instance for working with SWAT model data.

        Parameters:
        path (str, os.PathLike): The path to the SWAT model folder.

        Raises:
        TypeError: If the provided path is not a string or a Path object, or if the folder does not exist,
                    or if there is more than one .exe file in the folder, or if no .exe file is found.

        Attributes:
        root_folder (Path): The path to the root folder of the SWAT model.
        swat_exe_path (Path): The path to the main SWAT executable file.
        """

        # check if path is a string or a path
        if not isinstance(path, (str, os.PathLike)):
            raise TypeError("path must be a string or os.PathLike object")

        path = Path(path).resolve()

        # check if folder exists
        if not path.is_dir():
            raise FileNotFoundError("Folder does not exist")

        # count files that end with .exe
        count = 0
        swat_exe = None
        for file in os.listdir(path):
            if file.endswith(".exe"):
                if count == 0:
                    swat_exe = file
                elif count > 0:
                    raise TypeError("More than one .exe file found in the parent folder")
                count += 1

        if count == 0:
            raise TypeError(".exe not found in parent folder")

        # find parent directory
        self.root_folder = path
        self.swat_exe_path = path / swat_exe

    def _build_line_to_add(
        self,
        obj: str,
        daily: bool,
        monthly: bool,
        yearly: bool,
        avann: bool
    ) -> str:

        """
        Build a line to add to the 'print.prt' file based on the provided parameters.

        Parameters:
        obj (str): The object name or identifier.
        daily (bool): Flag for daily print frequency.
        monthly (bool): Flag for monthly print frequency.
        yearly (bool): Flag for yearly print frequency.
        avann (bool): Flag for average annual print frequency.

        Returns:
        str: A formatted string representing the line to add to the 'print.prt' file.
        """

        print_periodicity = {
            'daily': daily,
            'monthly': monthly,
            'yearly': yearly,
            'avann': avann,
        }

        arg_to_add = obj.ljust(29)
        for value in print_periodicity.values():
            if value:
                periodicity = 'y'
            else:
                periodicity = 'n'

            arg_to_add += periodicity.ljust(14)

        arg_to_add = arg_to_add.rstrip()
        arg_to_add += '\n'

        return arg_to_add

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

        Parameters:
        obj (str): The object name or identifier.
        daily (bool): Flag for daily print frequency.
        monthly (bool): Flag for monthly print frequency.
        yearly (bool): Flag for yearly print frequency.
        avann (bool): Flag for average annual print frequency.

        Returns:
        None
        """

        # check if obj is object itself or file
        if os.path.splitext(obj)[1] != '':
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
                    new_print_prt += self._build_line_to_add(arg_to_add, daily, monthly, yearly, avann)
                    found = True

        if not found:
            new_print_prt += self._build_line_to_add(arg_to_add, daily, monthly, yearly, avann)

        # store new print_prt
        with open(print_prt_path, 'w') as file:
            file.write(new_print_prt)

    def set_beginning_and_end_year(
        self,
        beginning: int,
        end: int
    ) -> None:

        """
        Modify the beginning and end year in the 'time.sim' file.

        Parameters:
        beginning (int): The new beginning year.
        end (int): The new end year.

        Returns:
        None
        """

        nth_line = 3

        # time_sim_path = f"{self.root_folder}\\{'time.sim'}"
        time_sim_path = self.root_folder / 'time.sim'

        # Open the file in read mode and read its contents
        with open(time_sim_path, 'r') as file:
            lines = file.readlines()

        year_line = lines[nth_line - 1]

        # Split the input string by spaces
        elements = year_line.split()

        elements[1] = beginning
        elements[3] = end

        # Reconstruct the result string while maintaining spaces
        result_string = '{: >8} {: >10} {: >10} {: >10} {: >10} \n'.format(*elements)

        lines[nth_line - 1] = result_string

        with open(time_sim_path, 'w') as file:
            file.writelines(lines)

    def set_warmup(
        self,
        warmup: int
    ) -> None:

        """
        Modify the warmup period in the 'time.sim' file.

        Parameters:
        warmup (int): The new warmup period value.

        Returns:
        None
        """

        time_sim_path = self.root_folder / 'print.prt'

        # Open the file in read mode and read its contents
        with open(time_sim_path, 'r') as file:
            lines = file.readlines()

        nth_line = 3
        year_line = lines[nth_line - 1]

        # Split the input string by spaces
        elements = year_line.split()

        elements[0] = warmup

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
        enable (bool, optional): True to enable CSV print, False to disable (default is True).

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
        index: Optional[str] = None,
        usecols: Optional[list[str]] = None,
        filter_by: Optional[str] = None
    ) -> FileReader:

        """
        Register a file to work with in the SWAT model.

        Parameters:
        filename (str): The name of the file to register.
        has_units (bool): Indicates if the file has units information (default is False).
        index (str, optional): The name of the index column (default is None).
        usecols (List[str], optional): A list of column names to read (default is None).
        filter_by (str, optional): Pandas query string to select applicable rows (default is None).

        Returns:
        FileReader: A FileReader instance for the registered file.
        """

        file_path = os.path.join(self.root_folder, filename)

        return FileReader(file_path, has_units, index, usecols, filter_by)

    def _copy_swat(
        self,
        target_dir: Optional[str] = None,
        overwrite: bool = False
    ) -> str:

        """
        Copy the SWAT model files to a specified directory.

        If 'overwrite' is True, the content of the 'target_dir' folder will be deleted, and the 'txtinout' folder will be copied there.
        If 'overwrite' is False, the 'txtinout' folder will be copied to a new folder inside 'target_dir'.

        Parameters:
        target_dir (str, optional): The target directory where the SWAT model files will be copied. If None, a temporary folder will be created (default is None).
        overwrite (bool, optional): If True, overwrite the content of 'target_dir'; if False, create a new folder inside target_dir (default is False).

        Returns:
        str: The path to the directory where the SWAT model files were copied.
        """

        # if target_dir is None or target_dir is a folder and overwrite is False, create a new folder using mkdtemp
        if (target_dir is None) or (not overwrite and target_dir is not None):

            try:
                temp_folder_path = tempfile.mkdtemp(dir=target_dir)
            except FileNotFoundError:
                os.makedirs(dir, exist_ok=True)
                temp_folder_path = tempfile.mkdtemp(dir=target_dir)

        # if target_dir is a folder and overwrite is True, delete all contents
        elif overwrite:

            if os.path.isdir(target_dir):

                temp_folder_path = target_dir

                # delete all files in target_dir
                for file in os.listdir(target_dir):
                    file_path = os.path.join(target_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(e)

            else:  # if overwrite and dir is not a folder, create dir anyway
                os.makedirs(dir, exist_ok=True)
                temp_folder_path = dir

        # check if dir does not exist
        elif not os.path.isdir(dir):
            # check if dir is a file
            if os.path.isfile(dir):
                raise TypeError("target_dir must be a folder")

            # create dir
            os.makedirs(dir, exist_ok=True)
            temp_folder_path = dir

        else:
            raise TypeError("option not recognized")

        # Get the list of files in the source folder
        source_folder = self.root_folder
        files = os.listdir(source_folder)

        # Exclude files with the specified suffix and copy the remaining files (only the required files for running SWAT are copied)
        for file in files:

            source_file = os.path.join(source_folder, file)

            # Skip directories and unwanted files
            if os.path.isdir(source_file):
                continue

            file_suffix = ['day', 'mon', 'yr', 'aa']
            file_ext = ['txt', 'csv']
            ignored_file = tuple(
                f'_{suf}.{ext}' for suf in file_suffix for ext in file_ext
            )

            if file.endswith(ignored_file):
                continue

            destination_file = os.path.join(temp_folder_path, file)
            shutil.copy2(source_file, destination_file)

        return temp_folder_path

    def _run_swat(
        self,
        show_output: bool = True
    ) -> None:

        """
        Run the SWAT simulation.

        Parameters:
        show_output (bool, optional): If True, print the simulation output; if False, suppress output (default is True).

        Returns:
        None
        """

        # Run siumulation
        swat_exe_path = self.swat_exe_path

        os.chdir(self.root_folder)

        with subprocess.Popen(swat_exe_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            # Read and print the output while it's being produced
            while True:
                # Read a line of output
                raw_output = process.stdout.readline()

                # Check if the output is empty and the subprocess has finished
                if raw_output == b'' and process.poll() is not None:
                    break

                # Decode the output using 'latin-1' encoding
                try:
                    output = raw_output.decode('latin-1').strip()
                except UnicodeDecodeError:
                    # Handle decoding errors here (e.g., skip or replace invalid characters)
                    continue

                # Print the decoded output if needed
                if output and show_output:
                    print(output)



    def run_swat_in_other_dir(
        self,
        target_dir: Optional[str] = None,
        overwrite: bool = False,
        params: Optional[dict[str, dict[str, Any]]] = None,
    ) -> str:

        """
        Copy the SWAT model files to a specified directory, modify input parameters, and run the simulation.

        Parameters:
        target_dir : str, optional
            Path to the directory where the SWAT model files will be copied. If None, a temporary directory will be used.

        overwrite : bool, optional
            If True, allow overwriting the contents of `target_dir`.
            If False (default), a new subdirectory will be created inside `target_dir`.

        params : dict, optional
            A dictionary defining parameter modifications per input file. The structure is:

            {
                'filename.ext': {
                    'has_units': bool,              # Optional; indicates whether the file contains units
                    'parameter_name': {
                        'value': float,         # New value to apply
                        'change_type': str,     # One of: 'absval', 'abschg', 'pctchg'
                        'filter_by': str        # Pandas query string to select applicable rows
                    },
                    # ... include any other actual parameter names for this 'filename.ext' ...
                },
                # ... more files can be added here ...
            }

            - 'change_type':
                * 'absval': Replace with absolute value
                * 'abschg': Add (or subtract) a fixed value
                * 'pctchg': Apply a percentage change (e.g., 0.10 = +10%)

            - 'filter_by': A string-compatible Pandas `.query()` expression used to filter rows
            in the input file before applying the parameter change.

        Returns:
        str
            The path to the directory where the SWAT simulation was executed.
        """

        tmp_path = self._copy_swat(target_dir=target_dir, overwrite=overwrite)
        reader = TxtinoutReader(tmp_path)

        return reader.run_swat(params)



    

    def run_swat(
        self,
        params: Optional[dict[str, dict[str, Any]]] = None,
    ) -> str:
        """
        Run the SWAT simulation with modified input parameters.

        Parameters:
        params : dict, optional
            A dictionary defining parameter modifications per input file. The structure is:

            {
                'filename.ext': {
                    'has_units': bool,              # Optional; indicates whether the file contains units
                    'parameter_name': {
                        'value': float,         # New value to apply
                        'change_type': str,     # One of: 'absval', 'abschg', 'pctchg'
                        'filter_by': str        # Pandas query string to select applicable rows
                    },
                    # ... include any other actual parameter names for this 'filename.ext' ...
                },
                # ... more files can be added here ...
            }

            - 'change_type':
                * 'absval': Replace with absolute value
                * 'abschg': Add (or subtract) a fixed value
                * 'pctchg': Apply a percentage change (e.g., 0.10 = +10%)

            - 'filter_by': A string-compatible Pandas `.query()` expression used to filter rows
            in the input file before applying the parameter change.

        Returns:
        str
            The path to the directory where the SWAT simulation was executed.
        """        
        aux_txtinout = TxtinoutReader(self.root_folder)
        
        _params = params or {}

        # Modify files for simulation
        for filename, file_params in _params.items():

            has_units = file_params.get('has_units', False)
                        
            # Read the file
            file = aux_txtinout.register_file(
                filename,
                has_units=has_units,
            )
                
            df = file.df
            
            reserved_params = ['has_units']

            for param_name, param_info in file_params.items():
                
                if param_name in reserved_params:
                    continue  # Skip reserved parameters
                
                value = param_info.get('value', None)
                
                if value is None:
                    raise ValueError(f"Parameter '{param_name}' in file '{filename}' must have a 'value' specified.")
                
                change_type = param_info.get('change_type', 'absval')
                if change_type not in ['absval', 'abschg', 'pctchg']:
                    raise ValueError(f"Parameter '{param_name}' in file '{filename}' has an invalid 'change_type': {change_type}. "
                                     "Valid options are 'absval', 'abschg', or 'pctchg'.")
                    
                filter_by = param_info.get('filter_by', None)
                
                if filter_by:
                    mask = df.query(filter_by).index
                else:
                    mask = df.index  # Apply to all rows

                # Apply the change directly to df using .loc
                if change_type == 'absval':
                    df.loc[mask, param_name] = value
                elif change_type == 'abschg':
                    df.loc[mask, param_name] += value
                elif change_type == 'pctchg':
                    df.loc[mask, param_name] *= (1 + value / 100)
            
            # Store the modified file
            file.overwrite_file()
            
        # run simulation
        aux_txtinout._run_swat()
        return self.root_folder






