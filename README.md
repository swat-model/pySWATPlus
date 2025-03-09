# pySWATPlus


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14889320.svg)](https://doi.org/10.5281/zenodo.14889320)


pySWATPlus is a python package for running and calibrating default or custom SWAT+ projects with Python.

With this package and by providing an existing SWAT+ model, modelers can do the following: 
- Acces the TxtInOut folder used by SWAT+ and navigate through all its files in order to read, modify and write them.
- Calibrate the different SWAT+ input parameters in order to optimize the output through the Pymoo.

pySWATPlus is open source software released by [ICRA](https://icra.cat/). It is available for download on [PyPI](https://pypi.org/project/pySWATPlus/).

# Installation
pySWATPlus can be installed via PyPI and requires additional packages to be installed first for its proper functioning. These are the commands required for installing the necessary packages:
- ```pip install pandas```
- ```pip install numpy```
- ```pip install pymoo```
- ```pip install tqdm```
- ```pip install dask```


To use this package, a Python version above 3.6 is required.

After all the requirements are met the package can be installed through the following command:
````py
pip install pySWATPlus
````
# How to use it
[https://github.com/swat-model/pySWATPlus/tree/main/examples](https://github.com/swat-model/pySWATPlus/tree/main/examples)

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

#### Attributes:
##### ```root_folder```
Returns the path of the used TxtInOut folder
```py
reader.root_folder
```
##### ```swat_exe_path```
The path to the main SWAT executable file
```py
reader.swat_exe_path
```
#### Methods:
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
txt_in_out_result = reader.run_swat(params = {'file_name': ('id_col', [('id', 'col', value)])}, show_output=False)
```
```py
txt_in_out_result = reader.run_swat(params = {'plants.plt': ('name', [('bana', 'bm_e', 45)])}, show_output=False)
```
For running the SWAT model without any parameter modification:
```py
txt_in_out_result = reader.run_swat()
```

##### ```copy_swat```
Copy the SWAT model files to a specified directory.

The function takes the following parameters:
- ```dir (str, optional)```: The target directory where the SWAT model files will be copied. If None, a temporary folder will be created (default is None).

- ```overwrite``` (bool, optional): If True, overwrite the content of ```dir```; if False, create a new folder inside ```dir``` (default is False).


The function returns the path to the directory where the SWAT model files were copied (str)

```py
new_path = reader.copy_swat(dir = 'new_path', overwrite = False)
```



##### ```copy_and_run```
Copy the SWAT model files to a specified directory, modify input parameters, and run the simulation

The function takes the following parameters: 
- ```dir``` (str): The target directory where the SWAT model files will be copied
- ```overwrite``` (bool, optional): If True, overwrite the content of ```dir```; if False, create a new folder inside ```dir```(default is False)
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
- ```parallelization``` (str, optional): The parallelization method to use ('threads' or 'processes') (default is 'threads')

The function returns a list of paths to the directories where the SWAT simulations were executed. list[str]
```py
txt_in_out_result = reader.run_parallel_swat(params = [{'file_name': [('id_col', ['id', 'col', value)])}], n_workers = n_workers, parallelization = 'parallelization_mode')
```
```py
txt_in_out_result = reader.run_parallel_swat(params = [{'plants.plt': ('name', [('bana', 'bm_e', 45)])}, {'plants.plt': ('name', [('bana', 'bm_e', 40)])}], n_workers = 2, parallelization = 'threads')
```

## FileReader
This featuer inicializes a ```FileReader``` instance to read data from a file generated for/from SWAT.

To incicialize this class the following parameters are required: 
- ```path``` (str): The path to the file.
- ```has_units``` (bool): Indicates if the file has units (default is False).
- ```index``` (str, optional): The name of the index column (default is None).
- ```usecols``` (List[str], optional): A list of column names to read (default is None).
- ```filter_by``` (Dict[str, List[str]]): A dictionary of column names and values (list of str) to filter by (default is an empty dictionary).

```py
from pySWATPlus.FileReader import FileReader

reader = FileReader('path', has_units = False, index = 'index', usecols=['col1', 'col2', 'col3'], filter_by={'col1': 'filter'})
```

```py
from pySWATPlus.FileReader import FileReader

reader = FileReader('TxtInOut\\plants.plt', has_units = False, index = 'name', usecols=['name', 'plnt_typ', 'gro_trig'], filter_by={'plnt_typ': 'perennial'})
```

#### Attributes:
##### ```df```
Returns a reference to the pandas DataFrame containing the data read from the file.
```py
reader.df
```
#### Methods:
##### ```overwrite_file```
Overwrite the original file with the DataFrame.

It doesn't take any parameters and neither returns anything.
```py
reader.overwrite_file()
```

## SWATProblem
This feature inicializes a ```SWATProblem``` instance, which is used to perform optimization of the desired SWAT+ parameters by using the ```pymoo``` library.

The ```SWATProblem``` class takes the following parameters: 

- ```params``` (Dict[str, Tuple[str, List[Tuple[str, str, int, int]]]]): A dictionary containing the range of values to optimize. **Format:** {filename: (id_col, [(id, col, upper_bound, lower_bound)])}
  
- ```function_to_evaluate``` (Callable): An objective function to minimize. This function, which has to be created entirely by the user, should be responsible for adjusting the necessary values based on the calibration iteration, running SWAT, reading the results, comparing them with observations, and calculating an error measure. The function must receive a single argument, which is a dictionary that can contain any user-defined items. However, it must receive at least one item (named as indicated by ```param_arg_name```), which takes a dictionary in the format {filename: (id_col, [(id, col, value)])}, representing the current calibration values. **Format**: function_to_evaluate(Dict[Any, Any]) -> Tuple[int, Dict[str, str]] where the first element is the error produced in the observations and the second element is a dictionary containing a user-desired identifier as the key and the location where the simulation has been saved as the value.
- ```param_arg_name``` (str): The name of the argument within ```function_to_evaluate``` function where the current calibration parameters are expected to be passed. This parameter must be included in ```**kwargs```
- ```n_workers``` (int, optional): The number of parallel workers to use (default is 1).
- ```parallelization``` (str, optional): The parallelization method to use ('threads' or 'processes') (default is 'threads').
- ```debug``` (bool, optional): If True, print debug output during optimization (default is False).
- ```**kwargs```: Additional keyword arguments, that will be passed to the ```function_to_evaluate```.


```py
from pySWATPlus.SWATProblem import SWATProblem
problem = SWATProblem(params = {"filename": (id_col, [(id, col, lb, up)])}, function_to_evaluate = function, param_arg_name = "name", n_workers = 2, parallelization = 'threads', debug = False, kwarg1 = arg1, kwarg2 = arg2)
```

#### Methods:
##### ```minimize_pymoo```
This function performs the optimization by using the pymoo library.

It takes the following parameters:
- ```problem``` (pyswatplus SWATProblem): The optimization problem defined using the SWATProblem class.
- ```algorithm``` (Algorithm): The optimization algorithm defined using the pymoo Algorithm class.
- ```termination``` (Termination): The termination criteria for the optimization defined using the pymoo Termination class.
- ```seed``` (Optional[int], optional): The random seed for reproducibility (default is None).
- ```verbose``` (bool, optional): If True, print verbose output during optimization (default is False).
- ```callback``` (Optional[Callable], optional): A callback function that is called after each generation (default is None).

It returns the best solution found during the process. The output format is a tuple containing the decision variables, the path to the output files, and the error (Tuple[np.ndarray, Dict[str, str], float]).

```py
from pySWATPlus.SWATProblem import SWATProblem, minimize_pymoo
x, path, error = minimize_pymoo(self.swat_problem, algorithm, termination, seed = 1, verbose = True, callback = MyCallback())
```

## SWATProblemMultimodel
:warning:
This class is only for advanced users

This class serves the same purpose as ```SWATProblem```, with the added capability of running another model before executing SWAT+. This enables running a prior model in the same calibration process, wherein the parameters are calibrated simultaneously. For example, the prior model can modify an input file of SWAT+ before initiating SWAT+ (according to the parameters of the calibration).

The ```SWATProblemMultimodel``` class takes the following parameters: 
- ```params``` (Dict[str, Tuple[str, List[Tuple[str, str, int, int]]]]): A dictionary containing the range of values to optimize. **Format:** {filename: (id_col, [(id, col, upper_bound, lower_bound)])}

- ```function_to_evaluate``` (Callable): An objective function to minimize. This function, which has to be created entirely by the user, should be responsible for adjusting the necessary values based on the calibration iteration, running SWAT, reading the results, comparing them with observations, and calculating an error measure. The function must receive a single argument, which is a dictionary that can contain any user-defined items. However, it must receive at least one item (named as indicated by ```param_arg_name```), which takes a dictionary in the format {filename: (id_col, [(id, col, value)])}, representing the current calibration values. **Format**: function_to_evaluate(Dict[Any, Any]) -> Tuple[int, Dict[str, str]] where the first element is the error produced in the observations and the second element is a dictionary containing a user-desired identifier as the key and the location where the simulation has been saved as the value.
- ```param_arg_name``` (str): The name of the argument within `o`function_to_evaluate``` function where the current calibration parameters are expected to be passed. This parameter must be included in ```**kwargs```
- ```n_workers``` (int, optional): The number of parallel workers to use (default is 1).
- ```parallelization``` (str, optional): The parallelization method to use ('threads' or 'processes') (default is 'threads').
- ```ub_prior``` (List[int], optional): Upper bounds list of calibrated parameters of the prior model. Default is None.
- ```lb_prior``` (List[int], optional): Lower bounds list of calibrated parameters of the prior model. Default is None.
- ```function_to_evaluate_prior``` (Callable, optional): Prior function to be used for modifying parameters before SWAT+ simulation. Must take the name indicated by ```args_function_to_evaluate_prior``` as a mandatory argument, and must be a np.ndarray, so in the source code the following is done: ```function_to_evaluate_prior(args_function_to_evaluate_prior = np.ndarray, ...)```. Must return a value that will be used to modify a parameter in the kwargs dictionary. Default is None. 
- ```args_function_to_evaluate_prior``` (Dict[str, Any], optional): Additional arguments for function_to_evaluate_prior. ```args_function_to_evaluate_prior``` does not have to be included here. This dictionary will be unpacked and passed as keyword arguments of  ```args_function_to_evaluate_prior```.
- ```debug``` (bool, optional): If True, print debug output during optimization (default is False).

- ```param_arg_name_to_modificate_by_prior_function``` (str, optional): Parameter modified in kwargs by the return of ```function_to_evaluate_prior```, so in the source code the following is done: ```kwargs[param_arg_name_to_modificate_by_prior_function] = function_to_evaluate_prior(...)```
- ```**kwargs```: Additional keyword arguments, that will alse be passed to the ```function_to_evaluate```.


```py
from pySWATPlus.SWATProblem import SWATProblem

problem = SWATProblem(params = {"filename": (id_col, [(id, col, lb, up)])}, function_to_evaluate = function, param_arg_name = "name", n_workers = 2, parallelization = 'threads', ub_prior = [ub_param1, ub_param2, ub_param3], lb_prior = [lb_param1, lb_param2, lb_param3], args_function_to_evaluate_prior = 'name2', function_to_evaluate_prior = function_to_evaluate_prior, param_arg_name_to_modificate_by_prior_function = "param_name", debug=False, kwarg1 = arg1, kwarg2 = arg2)
```

#### Methods:
##### ```minimize_pymoo```
This function performs the optimization by using the pymoo library.

It takes the following parameters:
- ```problem``` (pyswatplus SWATProblem): The optimization problem defined using the SWATProblem class.
- ```algorithm``` (Algorithm): The optimization algorithm defined using the pymoo Algorithm class.
- ```termination``` (Termination): The termination criteria for the optimization defined using the pymoo Termination class.
- ```seed``` (Optional[int], optional): The random seed for reproducibility (default is None).
- ```verbose``` (bool, optional): If True, print verbose output during optimization (default is False).
- ```callback``` (Optional[Callable], optional): A callback function that is called after each generation (default is None).

It returns the best solution found during the process. The output format is a tuple containing the decision variables, the path to the output files, and the error (Tuple[np.ndarray, Dict[str, str], float]).

```py
from pySWATPlus.SWATProblem import SWATProblem, minimize_pymoo

x, path, error = minimize_pymoo(self.swat_problem, algorithm, termination, seed = 1, verbose = True, callback = MyCallback())
```
#### 📖 Citation
If you use **pySWATPlus**, please cite it as follows:
```bibtex
@software{Salo_Llorente_2025,
  author    = {Joan Saló and Oliu Llorente},
  title     = {swat-model/pySWATPlus: pySWATPlus},
  year      = {2025},
  version   = {0.1.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.14889320},
  url       = {https://doi.org/10.5281/zenodo.14889320}
}

