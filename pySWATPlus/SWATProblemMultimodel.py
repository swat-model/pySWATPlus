from pymoo.core.problem import Problem
from .PymooBestSolution import get_solution, add_solutions
import copy
import numpy as np
from typing import Optional, Callable, Tuple, Any, Dict, List
from pymoo.optimize import minimize
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

def minimize_pymoo(
        problem: Problem, 
        algorithm: Any,
        termination: Any, 
        seed: Optional[int] = None, 
        verbose: bool = False, 
        callback: Optional[Callable] = None) -> Tuple[Optional[np.ndarray], Optional[str], Optional[float]]:
    
    """
    Perform optimization using the pymoo library.

    Parameters:
    - problem (pyswatplus SWATProblem): The optimization problem defined using the SWATProblem class.
    - algorithm (pymoo Algorithm): The optimization algorithm defined using the pymoo Algorithm class.
    - termination (pymoo Termination): The termination criteria for the optimization defined using the pymoo Termination class.
    - seed (Optional[int], optional): The random seed for reproducibility (default is None).
    - verbose (bool, optional): If True, print verbose output during optimization (default is False).
    - callback (Optional[Callable], optional): A callback function that is called after each generation (default is None).

    Returns:
    - Tuple[np.ndarray, Dict[str, str], float]: The best solution found during the optimization process, in the form of a tuple containing the decision variables, the path to the output files with the identifier, and the error.
    """

    if callback is None:
        minimize(problem,
            algorithm,
            seed=seed,
            verbose=verbose,
            termination = termination
        )
    else:
        minimize(problem,
            algorithm,
            seed=seed,
            verbose=verbose,
            callback=callback,
            termination = termination
        )


    return get_solution()


class SWATProblemMultimodel(Problem):

    def __init__(self, 
                 params: Dict[str, Tuple[str, List[Tuple[str, str, float, float]]]],
                 function_to_evaluate: Callable,
                 param_arg_name: str,
                 n_workers: int = 1,
                 parallelization: str = 'threads',
                 ub_prior: Optional[List[int]] = None,
                 lb_prior: Optional[List[int]] = None,
                 function_to_evaluate_prior: Optional[Callable] = None, #Must get X (np.ndarray) as mandatory argument
                 args_function_to_evaluate_prior: Optional[Dict[str, Any]] = None,  #X does not have to be in here, it's added in the function
                 param_arg_name_to_modificate_by_prior_function: Optional[str] = None,  #param that is modified in kwargs by the return of the prior function
                 debug: bool = False,

                 **kwargs: Dict[str, Any]
                 ) -> None:
        
        """
        This class serves the same purpose as SWATProblem, with the added capability of running another model before executing SWAT+. This enables running a prior model in the same calibration process, wherein the parameters are calibrated simultaneously. For example, the prior model can modify an input file of SWAT+ before initiating SWAT+ (according to the parameters of the calibration).

        Parameters:
        - params Dict[str, Tuple[str, List[Tuple[str, str, int, int]]]]): A dictionary containing the range of values to optimize.
          Format: {filename: (id_col, [(id, col, upper_bound, lower_bound)])}
        - function_to_evaluate (Callable): An objective function to minimize. This function, which has to be created entirely by the user, should be responsible for adjusting the necessary values based on the calibration iteration, running SWAT, reading the results, comparing them with observations, and calculating an error measure. The function can accept any user-defined arguments, but it must receive at least one argument (named as indicated by param_arg_name), which takes a dictionary in the format {filename: (id_col, [(id, col, value)])}, representing the current calibration values. 
          Format: function_to_evaluate(Dict[Any, Any]) -> Tuple[int, Dict[str, str]] where the first element is the error produced in the observations and the second element is a dictionary containing a user-desired identifier as the key and the location where the simulation has been saved as the value.
        - param_arg_name (str): The name of the argument within function_to_evaluate function where the current calibration parameters are expected to be passed. This parameter must be included in **kwargs
        - n_workers (int, optional): The number of parallel workers to use (default is 1).
        - parallelization (str, optional): The parallelization method to use ('threads' or 'processes') (default is 'threads').
        - ub_prior (List[int], optional): Upper bounds list of calibrated parameters of the prior model. Default is None.
        - lb_prior (List[int], optional): Lower bounds list of calibrated parameters of the prior model. Default is None.
        - function_to_evaluate_prior (Callable, optional): Prior function to be used for modifying parameters before SWAT+ simulation. Must take the name indicated by args_function_to_evaluate_prior as a mandatory argument, and must be a np.ndarray, so in the source code the following is done: function_to_evaluate_prior(args_function_to_evaluate_prior = np.ndarray, ...). Must return a value that will be used to modify a parameter in the kwargs dictionary. Default is None. 
        - args_function_to_evaluate_prior (Dict[str, Any], optional): Additional arguments for function_to_evaluate_prior. args_function_to_evaluate_prior does not have to be included here. This dictionary will be unpacked and passed as keyword arguments of  args_function_to_evaluate_prior.
        - param_arg_name_to_modificate_by_prior_function (str, optional): Parameter modified in kwargs by the return of function_to_evaluate_prior, so in the source code the following is done: kwargs[param_arg_name_to_modificate_by_prior_function] = function_to_evaluate_prior(...)
        - debug (bool, optional): If True, print debug output during optimization (default is False).
        - **kwargs: Additional keyword arguments, that will be passed to function_to_evaluate.

        
        Returns:
        None
        """
        
        lb = []
        ub = []
        for _, params_file in list(params.values()):
            for x in params_file:
                lb.append(x[2])
                ub.append(x[3])
        n_vars = len(lb)


        self.n_vars_prior = 0
        if ub_prior is not None and lb_prior is not None:

            if len(ub_prior) != len(lb_prior):
                raise ValueError('ub_prior and lb_prior must have the same length')

            n_vars += len(ub_prior)
            lb = [*lb_prior, *lb]
            ub = [*ub_prior, *ub]
            self.n_vars_prior = len(ub_prior)

        self.function_to_evaluate = function_to_evaluate
        self.n_workers = n_workers
        self.parallelization = parallelization
        self.params = params
        self.kwargs = kwargs
        self.param_arg_name = param_arg_name
        self.function_to_evaluate_prior = function_to_evaluate_prior
        self.args_function_to_evaluate_prior = args_function_to_evaluate_prior
        self.param_arg_name_to_modificate_by_prior_function = param_arg_name_to_modificate_by_prior_function
        self.debug = debug
                
        
        super().__init__(n_var=n_vars, n_obj=1, n_constr=0, xl=lb, xu=ub, elementwise_evaluation=False)

        

    def _evaluate(self, 
                  X: np.ndarray, 
                  out: Dict[str, Any],
                  *args: Any, 
                  **kwargs: Any):
        
        """
        Evaluate the objective function for a given set of input parameters.

        Parameters:
        - X (np.ndarray): The input parameters to be evaluated.
        - out (Dict[str, Any]): A dictionary to store the output values.
        - *args (Any): Additional positional arguments.
        - **kwargs (Any): Additional keyword arguments.

        Returns:
        None
        """
        if self.debug:
            print('starting _evaluate')
        
        args_array = []

        for x in X:

            X_prior = x[:self.n_vars_prior]
            X_swat = x[self.n_vars_prior:]
            
            if self.function_to_evaluate_prior is not None:
                return_function_prior = self.function_to_evaluate_prior(X = X_prior, **self.args_function_to_evaluate_prior)

            _id = 0
            new_params = {}     #in the end will be {filename: (id_col, [(id, col, value)])}
            params = self.params    #{filename: (id_col, [(id, col, lb, ub)])}

            for file in params.keys():
                index, params_tuple = params[file]
                new_params[file] = (index, [])
                for param in params_tuple:
                    new_params[file][1].append((param[0], param[1], X_swat[_id]))
                    _id += 1

            self.kwargs[self.param_arg_name] = new_params

            if self.param_arg_name_to_modificate_by_prior_function is not None:
                self.kwargs[self.param_arg_name_to_modificate_by_prior_function] = return_function_prior
            
            args_array.append(copy.deepcopy(self.kwargs))
        
        #F = self.pool.map(self.fuction_to_evaluate, args_array)
        if self.parallelization == 'threads':
            with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
                F = list(executor.map(self.function_to_evaluate, args_array))      
        elif self.parallelization == 'processes':
            with multiprocessing.Pool(self.n_workers) as pool:
                F = list(pool.map(self.function_to_evaluate, args_array))
        else:
            raise ValueError("parallelization must be 'threads' or 'processes'")  

                
        errors, paths = zip(*F)

        errors_array = np.array(errors)
        paths_array = np.array(paths)

        if self.debug:
            print(errors_array)

        #replace nan error by 1e10 (infinity)
        errors_array[np.isnan(errors_array)] = 1e10

        #check if nans and print message
        if np.isnan(errors_array).any() and self.debug:
            print('ERROR: some errors are nan')
            print(errors_array)
            print(paths_array)

        if self.debug:
            print('adding solutions')

        add_solutions(paths_array, errors_array)
    
        if self.debug:
            print('exit adding solutions')

        #minimitzar error 
        out["F"] = errors_array
        
        if self.debug:
            print('returning from _evaluate')

        
    

        

