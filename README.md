# pySWATPlus
pySWATPlus is a python package for running and calibrating default or custom SWAT+ projects with python.

With this package and by providing an existing SWAT+ model, modelers can do the following: 
- Acces the TxtInOut folder used by SWAT+ and navigate through all its files in order to read, modify and write them.
- Calibrate the different SWAT+ input parameters in order to optimize the output through the Pymoo.

# Installation
pySWATPlus can be installed via PyPI and requires additional packages to be installed first for its proper functioning. These are the commands required for installing the necessary packages:
- ```pip install pandas```
- ```pip install numpy```
- ```pip install dask```
- ```pip install pymoo```
- ```pip install tqdm```
- ```pip install "dask[distributed]" --upgrade```

To use this package, a Python version above 3.6 is required.

After all the requirements are met the package can be installed through the following command:
````py
pip install pySWATPlus
````

# Package Structure
The package consists of three main features: 
- ```TxtinoutReader```
- ```FileReader```
- ```SWATProblem```

## TxtinoutReader
This feature inicializes a ```TxtinoutReader``` class instance that allows users to work with SWAT model data. It requires a path to the SWAT model folder as shown in the following example
```py
from pySWATPlus.TxtinoutReader import TxtinoutReader

reader = TxtinoutReader(txtinout_folder_path)
```
This class allows users to do the following: 
##### ```set_beginning_and_end_year```
It allows the user to modify the begining and end year in the ```time.sim``` file.

It takes two parameters:
- ```beginning``` (int): specifies the begining year
- ```end``` (int): specifies the end year

```py
reader.set_beginning_and_end_year(beginning, end)
```

```py
reader.set_beginning_and_end_year(2010, 2020)
```
##### ```set_warmup```
This function allows the user to modify the warmup period (years) in the "time.sim" file.

As a parameter it takes the ```warmup``` (int) value.
```py
reader.set_warmup(warmup)
```

```py
reader.set_warmup(3)
```

##### ```enable_object_in_print_prt```
Enable or update an object in the ```print.prt``` file. If ```obj``` is not a default identifier, it will be added at the end of the file.

It takes the following parameters:
- ```obj``` (str): The object name or identifier
- ```daily``` (bool): Flag for daily print freuency
- ```monthly``` (bool): Flag for monthly print frequency
- ```yearly``` (bool): Flag for yearly print frequency
- ```avann``` (bool): Flag for average annual print frequency

```py
reader.enable_object_in_print_prt(obj='object_name', daily=True, monthly=False, yearly=False, avann=False)
```
```py
reader.enable_object_in_print_prt('channel_sd', True, False, False, False)
```

##### ```enable_csv_print```
Enable CSV print in the ```print.prt``` file

It takes no parameters
```py
reader.enable_csv_print()
```

##### ```disable_csv_print```
Disable CSV print in the ```print.prt``` file

It takes no parameters
```py
reader.disable_csv_print()
```

##### ```register_file```
Register a file to work with in the SWAT model.

The function takes the following parameters: 
- ```filename``` (str): The name of the file to register
- ```has_units``` (bool): Indicates if the file has units information (default is False)
- ```index``` (str, optional): The name of the index column (default is None)
- ```usecols``` (List[str], optional): A list of column names to read (default is None)
- ```filter_by``` (Dict[str, List[str]], optional): A dictionary of column names and values (list of str) to filter by (default is an empty dictionary)

The function returns a ```FileReader``` instance for the registered file.

```py
file = reader.register_file('filename', has_units = False, index = 'index_name', usecols=['index_name', 'col1', 'col2', 'col3'], filter_by={'col1': ['filter_value1', 'filter_value2']})
```

```py
file = reader.register_file('exco.con', has_units = False, index = "name", usecols = ['name', 'gis_id', 'area', 'hyd_typ'], filter_by={'gis_id':[5, 11, 35]})
```

##### ```run_swat```
Run the SWAT simulation with modified input parameters.

The function takes the following parameters:
- ```params``` (Dict[str, Tuple[str, List[Tuple[str, str, int]]], optional): A dictionary containing modifications to input files. **Format:** {filename: (id_col, [(id, col, value)])}
- ```show_output``` (bool, optional): If True, print the simulation output; if False, suppress output (default is True)

The function returns the path to the directory where the simulation was executed (str)

```py
txt_in_out_result = reader.run_swat(params = {'file_name': [('id_col', ['id', 'col', value)])}, show_output=False)
```
```py
txt_in_out_result = reader.run_swat(params = {'plants.plt': [('name', ['bana', 'bm_e', 45)])}, show_output=False)
```

##### ```copy_and_run```
Copy the SWAT model files to a specified directory, modify input parameters, and run the simulation

The function takes the following parameters: 
- ```dir``` (str): The target directory where the SWAT model files will be copied
- ```overwrite``` (bool, optional): If True, overwrite the content of 'dir'; if False, create a new folder (default is False)
- ```params``` (Dict[str, Tuple[str, List[Tuple[str, str, int]]], optional): A dictionary containing modifications to input files. **Format:** {filename: (id_col, [(id, col, value)])}
- ```show_output``` (bool, optional): If True, print the simulation output; if False, suppress output (default is True)

The function returns the path to the directory where the SWAT simulation was executed

```py
txt_in_out_result =  reader.copy_and_run(dir="directory_path", overwrite=False, params={'file_name': [('id_col', ['id', 'col', value)])}, show_output=False)
```
```py
txt_in_out_result = reader.copy_and_run(dir = "directory_path", overwrite=False, params = {'plants.plt': [('name', ['bana', 'bm_e', 45)])}, show_output=False)
```

##### ```run_parallel_swat```
Run SWAT simulations in parallel with modified input parameters.

Parameters:
- ```params``` (List[Dict[str, Tuple[str, List[Tuple[str, str, int]]]]): A list of dictionaries containing modifications to input files. **Format:** [{filename: (id_col, [(id, col, value)])}]
- ```n_workers``` (int, optional): The number of parallel workers to use (default is 1)
- ```dir``` (str, optional): The target directory where the SWAT model files will be copied (default is None)
- ```client``` (dask.distributed.Client, optional): A Dask client for parallel execution (default is None)

The function returns a list of paths to the directories where the SWAT simulations were executed. list[str]
```py
txt_in_out_result = reader.run_parallel_swat(params = [{'file_name': [('id_col', ['id', 'col', value)])}], show_output=False)
```
```py
txt_in_out_result = reader.run_parallel_swat(params = [{'plants.plt': [('name', ['bana', 'bm_e', 40)])}, {'plants.plt': [('name', ['bana', 'bm_e', 45)])}], show_output=False)
```



