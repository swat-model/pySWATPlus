from pymoo.core.problem import ElementwiseProblem, Problem
from pySWATPlus.PymooBestSolution import get_solution, add_solutions 
import pymoo
import copy
import multiprocessing
import numpy as np
from typing import Optional, Callable, Tuple, Any, Dict, List

def minimize_pymoo(
        problem: Problem, 
        algorithm, 
        termination, 
        seed: Optional[int] = None, 
        verbose: bool = False, 
        callback: Optional[Callable] = None) -> Tuple[Optional[np.ndarray], Optional[str], Optional[float]]:
    
    """
    Perform optimization using the pymoo library.

    Parameters:
    - problem (Problem): The optimization problem defined using the pymoo Problem class.
    - algorithm (Algorithm): The optimization algorithm defined using the pymoo Algorithm class.
    - termination (Termination): The termination criteria for the optimization defined using the pymoo Termination class.
    - seed (Optional[int], optional): The random seed for reproducibility (default is None).
    - verbose (bool, optional): If True, print verbose output during optimization (default is False).
    - callback (Optional[Callable], optional): A callback function that is called after each generation (default is None).

    Returns:
    - Tuple[Optional[np.ndarray], Optional[str], Optional[float]]: The best solution found during the optimization process, in the form of a tuple containing the decision variables, the path to the output files, and the error.
    """

    pymoo.optimize.minimize(problem,
        algorithm,
        seed=seed,
        verbose=verbose,
        callback=callback,
        termination = termination
    )

    return get_solution()


class SWATProblem(Problem):

    def __init__(self, 
                 params: Dict[str, Tuple[str, List[Tuple[str, str, int, int]]]],
                 function_to_evaluate: Callable,
                 param_arg_name: str,
                 n_workers: int = 1,
                 ub_prior: Optional[List[int]] = None,
                 lb_prior: Optional[List[int]] = None,
                 function_to_evaluate_prior: Optional[Callable] = None, #Must get X (np.ndarray) as mandatory argument, as well as **args_function_to_evaluate_prior
                 args_function_to_evaluate_prior: Optional[Dict[str, Any]] = None,  #X does not have to be in here, it's added in the function
                 param_arg_name_to_modificate_by_prior_function: Optional[str] = None,  #param that is modified in kwargs by the return of the prior function
                 **kwargs: Dict[str, Any]
                 ) -> None:
        
        """
        Initialize the SWATProblem class, that is used to perform optimization of SWAT+ parameters using the pymoo library. Parameters included in the optimisation but not related to SWAT+ 
        can be optimised as well, using a prior function that is executed before the SWAT+ execution and modifies a parameter in the kwargs dictionary.

        Parameters:
        - params (Dict[str, Tuple[str, List[Tuple[str, str, int, int]]]]): A dictionary containing parameter files.
          Format: {filename: (id_col, [(id, col, min_value, max_value)])}.
        - function_to_evaluate (Callable): The objective function to be minimized. Must take a dictionary as argument, and must return a tuple where the first element is the error and the second element is a dictionary where the key is the name of the output file and the value is the path to the output file.
          Format: function_to_evaluate(Dict[Any, Any]) -> Tuple[int, Dict[str, str]] where the first element is the error and the second element is a dictionary where the key is the name of the output file and the value is the path to the output file.
        - param_arg_name (str): The name of the argument in the objective function representing the parameters.
        - n_workers (int, optional): The number of parallel workers to use (default is 1).

        - ub_prior (List[int], optional): Upper bounds for the prior function X parameter (where X is the list of parameters optimised in the optimisation). Default is None.
        - lb_prior (List[int], optional): Lower bounds for the prior function X parameter (where X is the list of parameters optimised in the optimisation). Default is None.
        - function_to_evaluate_prior (Callable, optional): Prior function to be used for modifying parameters before SWAT+ simulation. Must take X (np.ndarray) as a mandatory argument, and must return a value that will be used to modify a parameter in the kwargs dictionary. Default is None.
        - args_function_to_evaluate_prior (Dict[str, Any], optional): Additional arguments for function_to_evaluate_prior. X does not have to be included here;
        - param_arg_name_to_modificate_by_prior_function (str, optional): Parameter modified in kwargs by the return of function_to_evaluate_prior.
        - **kwargs: Additional keyword arguments, that will be passed to the objective function.

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

        self.fuction_to_evaluate = function_to_evaluate
        self.n_workers = n_workers
        self.params = params
        self.kwargs = kwargs
        self.param_arg_name = param_arg_name
        self.function_to_evaluate_prior = function_to_evaluate_prior
        self.args_function_to_evaluate_prior = args_function_to_evaluate_prior
        self.param_arg_name_to_modificate_by_prior_function = param_arg_name_to_modificate_by_prior_function
        
        self.pool = multiprocessing.Pool(n_workers)
        
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

        args_array = []

        for x in X:

            X_prior = x[:self.n_vars_prior]
            X_swat = x[self.n_vars_prior:]
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
        
        F = self.pool.map(self.fuction_to_evaluate, args_array)

        errors, paths = zip(*F)

        errors_array = np.array(errors)
        paths_array = np.array(paths)

        add_solutions(paths_array, errors_array)
        
        #minimitzar error 
        out["F"] = errors_array
        
    

