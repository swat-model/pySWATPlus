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

## FileReader
This featuer inicializes a ```FileReader``` instance to read data from a file generated for/from SWAT.

To incicialize this class the following parameters are required: 
- ```path``` (str): The path to the file.
- ```has_units``` (bool): Indicates if the file has units (default is False).
- ```index``` (str, optional): The name of the index column (default is None).
- ```usecols``` (List[str]): A list of column names to read (default is an empty list).
- ```filter_by``` (Dict[str, List[str]]): A dictionary of column names and values (list of str) to filter by (default is an empty dictionary).

```py
from pySWATPlus.FileReader import FileReader

reader = FileReader('path', has_units = False, index = 'index', usecols=['col1', 'col2', 'col3'], filter_by={'col1': 'filter'})
```

```py
from pySWATPlus.FileReader import FileReader

reader = FileReader('TxtInOut\\plants.plt', has_units = False, index = 'name', usecols=['name', 'plnt_typ', 'gro_trig'], filter_by={'plnt_typ': 'perennial'})
```

##### ```overwrite_file```
Overwrite the original file with the DataFrame.

It doesn't take any parameters and neither returns anything.

## SWATProblem
This feature inicializes a ```SWATProblem``` instance, which is used to perform optimization of the desired SWAT+ paraleters by using the ```pymoo``` library. Parameters included in the optimisation but not related to SWAT+ can be optimised as well by using a prior function that is executed before the SWAT+ execution and modifies a parameter in the kwargs directory.

The ```SWATProblem``` class takes the following parameters: 
- ```params``` (Dict[str, Tuple[str, List[Tuple[str, str, int, int]]]]): A dictionary containing parameter files. Where the first string is the file name.
- ```function_to_evaluate``` (Callable): The objective function to be minimized. Must take a dictionary as argument, and must return a tuple where the first element is the error and the second element is a dictionary where the key is the name of the output file and the value is the path to the output file. 
Format: function_to_evaluate(Dict[Any, Any]) -> Tuple[int, Dict[str, str]] where the first element is the error and the second element is a dictionary where the key is the name of the output file and the value is the path to the output file.
- ```param_arg_name``` (str): The name of the argument in the objective function representing the parameters.
- ```n_workers``` (int, optional): The number of parallel workers to use (default is 1).
- ```ub_prior``` (List[int], optional): Upper bounds for the prior function X parameter (where X is the list of parameters optimised in the optimisation). Default is None.
- ```lb_prior``` (List[int], optional): Lower bounds for the prior function X parameter (where X is the list of parameters optimised in the optimisation). Default is None.
- ```function_to_evaluate_prior``` (Callable, optional): Prior function to be used for modifying parameters before SWAT+ simulation. Must take X (np.ndarray) as a mandatory argument, and must return a value that will be used to modify a parameter in the kwargs dictionary. Default is None.
- ```args_function_to_evaluate_prior``` (Dict[str, Any], optional): Additional arguments for function_to_evaluate_prior. X does not have to be included here;
- ```param_arg_name_to_modificate_by_prior_function``` (str, optional): Parameter modified in kwargs by the return of function_to_evaluate_prior.
- **```kwargs```: Additional keyword arguments, that will be passed to the objective function.

```py
from pySWATPlus.SWATProblem import SWATProblem

problem = SWATProblem(params = ["path_to_folder",{"filename": (id_col, [(id, col, lb, up)])}, function_to_evaluate = function_to_evaluate([element1,element2]), param_arg_name = "name", n_workers = 2, ub_prior = [ub_param1, ub_param2, ub_param3], lb_prior = [lb_param1, lb_param2, lb_param3], function_to_evaluate_prior = function_to_evaluate_prior([element1, element2]), param_arg_name_to_modificate_by_prior_function = "param_name")
```
##### ```minimize_pymo```
This function performs the optimization by using the pymoo library.

It takes the following parameters:
- ```problem``` (Problem): The optimization problem defined using the pymoo Problem class.
- ```algorithm``` (Algorithm): The optimization algorithm defined using the pymoo Algorithm class.
- ```termination``` (Termination): The termination criteria for the optimization defined using the pymoo Termination class.
- ```seed``` (Optional[int], optional): The random seed for reproducibility (default is None).
- ```verbose``` (bool, optional): If True, print verbose output during optimization (default is False).
- ```callback``` (Optional[Callable], optional): A callback function that is called after each generation (default is None).

It returns the best solution found during the process. The output format is a tuple containing the decision variables, the path to the output files, and the error (Tuple[Optional[np.ndarray], Optional[str], Optional[float]]).

```py
from pySWATPlus.SWATProblem import SWATProblem, minimize_pymoo

x, path, error = minimize_pymoo(self.swat_problem, algorithm, termination, seed = 1, verbose = True, callback = MyCallback())
```