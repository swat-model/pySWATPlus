import subprocess 
import os
from .FileReader import FileReader
import shutil
import tempfile
import multiprocessing
import tqdm
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from concurrent.futures import ThreadPoolExecutor
import re


class TxtinoutReader:

    def __init__(self, path: str) -> None:

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


        #check if path is a string or a path
        if not isinstance(path, (str, os.PathLike)):
            raise TypeError("path must be a string or os.PathLike object")
        
        path = Path(path).resolve()                        

        #check if folder exists
        if not path.is_dir():
            raise FileNotFoundError("folder does not exist")
            
        #count files that end with .exe
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
  
        #find parent directory
        self.root_folder = path
        self.swat_exe_path = path / swat_exe


    def _build_line_to_add(self, obj: str, daily: bool, monthly: bool, yearly: bool, avann: bool) -> str:
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

    
    def enable_object_in_print_prt(self, obj: str, daily: bool, monthly: bool, yearly: bool, avann: bool) -> None:
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

        #check if obj is object itself or file 
        if os.path.splitext(obj)[1] != '':
            arg_to_add = obj.rsplit('_', maxsplit=1)[0]
        else:
            arg_to_add = obj
        
        #read all print_prt file, line by line
        print_prt_path = self.root_folder / 'print.prt'
        new_print_prt = ""
        found = False
        with open(print_prt_path) as file:
            for line in file:
                if not line.startswith(arg_to_add + ' '): #Line must start exactly with arg_to_add, not a word that starts with arg_to_add 
                    new_print_prt += line
                else:
                    #obj already exist, replace it in same position
                    new_print_prt += self._build_line_to_add(arg_to_add, daily, monthly, yearly, avann)
                    found = True

        if not found:
            new_print_prt += self._build_line_to_add(arg_to_add, daily, monthly, yearly, avann)


        #store new print_prt
        with open(print_prt_path, 'w') as file:
            file.write(new_print_prt)
        
    #modify yrc_start and yrc_end
    def set_beginning_and_end_year(self, beginning: int, end: int) -> None:
        """
        Modify the beginning and end year in the 'time.sim' file.

        Parameters:
        beginning (int): The new beginning year.
        end (int): The new end year.

        Returns:
        None
        """
                
        nth_line = 3

        #time_sim_path = f"{self.root_folder}\\{'time.sim'}"
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

    #modify warmup
    def set_warmup(self, warmup: int) -> None:
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


    def _enable_disable_csv_print(self, enable: bool = True) -> None:
        """
        Enable or disable CSV print in the 'print.prt' file.

        Parameters:
        enable (bool, optional): True to enable CSV print, False to disable (default is True).

        Returns:
        None
        """

        #read 
        nth_line = 7

        #time_sim_path = f"{self.root_folder}\\{'time.sim'}"
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

        
    def enable_csv_print(self) -> None:
        """
        Enable CSV print in the 'print.prt' file.

        Returns:
        None
        """
        self._enable_disable_csv_print(enable = True)

    def disable_csv_print(self) -> None:
        """
        Disable CSV print in the 'print.prt' file.

        Returns:
        None
        """
        self._enable_disable_csv_print(enable = False)

    
    def register_file(self, filename: str, has_units: bool = False, index: Optional[str] = None, usecols: Optional[List[str]] =  None, filter_by: Dict[str, List[str]] = {}) -> FileReader:

        """
        Register a file to work with in the SWAT model.

        Parameters:
        filename (str): The name of the file to register.
        has_units (bool): Indicates if the file has units information (default is False).
        index (str, optional): The name of the index column (default is None).
        usecols (List[str], optional): A list of column names to read (default is None).
        filter_by (Dict[str, List[str]], optional): A dictionary of column names and values (list of str) to filter by (default is an empty dictionary).

        Returns:
        FileReader: A FileReader instance for the registered file.
        """
        
        file_path = os.path.join(self.root_folder, filename)
        return FileReader(file_path, has_units, index, usecols, filter_by)
    
    """
    if overwrite = True, content of dir folder will be deleted and txtinout folder will be copied there
    if overwrite = False, txtinout folder will be copied to a new folder inside dir
    """
    def copy_swat(self, dir: str = None, overwrite: bool = False) -> str:

        """
        Copy the SWAT model files to a specified directory.

        If 'overwrite' is True, the content of the 'dir' folder will be deleted, and the 'txtinout' folder will be copied there.
        If 'overwrite' is False, the 'txtinout' folder will be copied to a new folder inside 'dir'.

        Parameters:
        dir (str, optional): The target directory where the SWAT model files will be copied. If None, a temporary folder will be created (default is None).
        overwrite (bool, optional): If True, overwrite the content of 'dir'; if False, create a new folder inside dir(default is False).

        Returns:
        str: The path to the directory where the SWAT model files were copied.
        """

        #if dir is None or dir is a folder and overwrite is False, create a new folder using mkdtemp
        if (dir is None) or (not overwrite and dir is not None):

            try: 
                temp_folder_path = tempfile.mkdtemp(dir = dir)
            except FileNotFoundError:
                os.makedirs(dir, exist_ok=True)
                temp_folder_path = tempfile.mkdtemp(dir = dir)
        
        #if dir is a folder and overwrite is True, delete all contents
        elif overwrite:

            if os.path.isdir(dir):
            
                temp_folder_path = dir
                
                #delete all files in dir
                for file in os.listdir(dir):
                    file_path = os.path.join(dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(e)
            
            else:   #if overwrite and dir is not a folder, create dir anyway
                os.makedirs(dir, exist_ok=True)
                temp_folder_path = dir
        
        #check if dir does not exist
        elif not os.path.isdir(dir):
            #check if dir is a file
            if os.path.isfile(dir):
                raise TypeError("dir must be a folder")

            #create dir
            os.makedirs(dir, exist_ok=True)
            temp_folder_path = dir
        
        else:
            raise TypeError("option not recognized")

        # Get the list of files in the source folder
        source_folder = self.root_folder
        files = os.listdir(source_folder)

        # Exclude files with the specified suffix and copy the remaining files
        for file in files:
            if not file.endswith('_aa.txt') and not file.endswith('_aa.csv') and not file.endswith('_yr.txt') and not file.endswith('_yr.csv') and not file.endswith('_day.txt') and not file.endswith('_day.csv') and not file.endswith('_mon.csv') and not file.endswith('_mon.txt'):
                source_file = os.path.join(source_folder, file)
                destination_file = os.path.join(temp_folder_path, file)

                shutil.copy2(source_file, destination_file)

        return temp_folder_path



    def _run_swat(self, show_output: bool = True) -> None:
        """
        Run the SWAT simulation.

        Parameters:
        show_output (bool, optional): If True, print the simulation output; if False, suppress output (default is True).

        Returns:
        None
        """

        #Run siumulation
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
        
    

    """
    params --> {filename: (id_col, [(id, col, value)])}
    """
    def run_swat(self, params: Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]] = {}, show_output: bool = True) -> str:
        """
        Run the SWAT simulation with modified input parameters.

        Parameters:
        params (Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]], optional): 
            A dictionary containing modifications to input files. Format: {filename: (id_col, [(id, col, value)])}.
            'id' can be None to apply the value to all rows or a regex pattern to match multiple IDs.
        show_output (bool, optional): If True, print the simulation output; if False, suppress output (default is True).

        Returns:
        str: The path to the directory where the SWAT simulation was executed.
        """
        aux_txtinout = TxtinoutReader(self.root_folder)

        #Modify files for simulation
        for filename, file_params in params.items():

            id_col, file_mods = file_params

            #get file
            file = aux_txtinout.register_file(filename, has_units = False, index = id_col)

            #for each col_name in file_params
            for id, col_name, value in file_mods:   # 'id' can be None, a str or a regex pattern
                if id is None:
                    file.df[col_name] = value
                elif isinstance(id, re.Pattern):
                    mask = file.df.index.astype(str).str.match(id)
                    file.df.loc[mask, col_name] = value
                else:
                    file.df.loc[id, col_name] = value
            
            #store file
            file.overwrite_file()
                
        
        #run simulation
        aux_txtinout._run_swat(show_output=show_output)

        return self.root_folder


    def run_swat_star(self, args: Tuple[Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]], bool]) -> str:
        """
        Run the SWAT simulation with modified input parameters using arguments provided as a tuple.

        Parameters:
        args (Tuple[Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]]], bool]): 
            A tuple containing simulation parameters.
            The first element is a dictionary with input parameter modifications, 
            the second element is a boolean to show output.

        Returns:
        str: The path to the directory where the SWAT simulation was executed.
        """
        return self.run_swat(*args)

    def copy_and_run(self, dir: str, overwrite: bool = False, params: Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]] = {}, show_output: bool = True) -> str:
        
        """
        Copy the SWAT model files to a specified directory, modify input parameters, and run the simulation.

        Parameters:
        dir (str): The target directory where the SWAT model files will be copied.
        overwrite (bool, optional): If True, overwrite the content of 'dir'; if False, create a new folder inside 'dir' (default is False).
        params (Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]], optional):
            A dictionary containing modifications to input files. Format: {filename: (id_col, [(id, col, value)])}.
        Format: {filename: (id_col, [(id, col, value)])}.
        show_output (bool, optional): If True, print the simulation output; if False, suppress output (default is True).

        Returns:
        str: The path to the directory where the SWAT simulation was executed.
        """
        
        tmp_path = self.copy_swat(dir = dir, overwrite = overwrite)
        reader = TxtinoutReader(tmp_path)
        return reader.run_swat(params, show_output = show_output)


    def copy_and_run_star(self, args: Tuple[str, bool, Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]], bool]) -> str:
        """
        Copy the SWAT model files to a specified directory, modify input parameters, and run the simulation using arguments provided as a tuple.

        Parameters:
        args (Tuple[Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]]], bool]): 
            A tuple containing simulation parameters.
            The first element is a dictionary with input parameter modifications, 
            the second element is a boolean to show output.

        Returns:
        str: The path to the directory where the SWAT simulation was executed.
        """        
        return self.copy_and_run(*args)

    
    """
    params --> [{filename: (id_col, [(id, col, value)])}]
    """
    def run_parallel_swat(self, 
                          params: List[Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]]], 
                          n_workers: int = 1, 
                          dir: str = None,
                          parallelization: str = 'threads') -> List[str]:
        
        """
        Run SWAT simulations in parallel with modified input parameters.

        Parameters:
        params (Dict[str, Tuple[str, List[Tuple[Union[None, str, re.Pattern], str, int]]]], optional):
            A dictionary containing modifications to input files. Format: {filename: (id_col, [(id, col, value)])}.
        n_workers (int, optional): The number of parallel workers to use (default is 1).
        dir (str, optional): The target directory where the SWAT model files will be copied (default is None).
        parallelization (str, optional): The parallelization method to use ('threads' or 'processes') (default is 'threads').

        Returns:
        List[str]: A list of paths to the directories where the SWAT simulations were executed.
        """

        

        max_treads = multiprocessing.cpu_count()
        threads = max(min(n_workers, max_treads), 1)
        
        if n_workers == 1:
            
            results_ret = []

            for i in tqdm.tqdm(range(len(params))):
                results_ret.append(self.copy_and_run(dir = dir,
                                                    overwrite = False,
                                                    params = params[i], 
                                                    show_output = False))
            
            return results_ret

        else:
                
            items = [[dir, False, params[i], False] for i in range(len(params))]

            if parallelization == 'threads':
                with ThreadPoolExecutor(max_workers=threads) as executor:
                    results = list(executor.map(self.copy_and_run_star, items))    
            elif parallelization == 'processes':
                with multiprocessing.Pool(threads) as pool:
                    results = list(pool.map(self.copy_and_run_star, items))
            else:
                raise ValueError("parallelization must be 'threads' or 'processes'")  

            return results
            


        
        

    


