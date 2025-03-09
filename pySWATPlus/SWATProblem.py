from typing import Callable, Tuple, Any, Dict, List
from .SWATProblemMultimodel import SWATProblemMultimodel



class SWATProblem(SWATProblemMultimodel):

    def __init__(self, 
                 params: Dict[str, Tuple[str, List[Tuple[str, str, float, float]]]],
                 function_to_evaluate: Callable,
                 param_arg_name: str,
                 n_workers: int = 1,
                 parallelization: str = 'threads',
                 debug: bool = False,
                 **kwargs: Dict[str, Any]
                 ) -> None:
        
        """
        This feature inicializes a SWATProblem instance, which is used to perform optimization of the desired SWAT+ parameters by using the pymoo library.

        Parameters:
        - params Dict[str, Tuple[str, List[Tuple[str, str, int, int]]]]): A dictionary containing the range of values to optimize.
          Format: {filename: (id_col, [(id, col, upper_bound, lower_bound)])}
        - function_to_evaluate (Callable): An objective function to minimize. This function, which has to be created entirely by the user, should be responsible for adjusting the necessary values based on the calibration iteration, running SWAT, reading the results, comparing them with observations, and calculating an error measure. The function can accept any user-defined arguments, but it must receive at least one argument (named as indicated by param_arg_name), which takes a dictionary in the format {filename: (id_col, [(id, col, value)])}, representing the current calibration values. 
          Format: function_to_evaluate(Dict[Any, Any]) -> Tuple[int, Dict[str, str]] where the first element is the error produced in the observations and the second element is a dictionary containing a user-desired identifier as the key and the location where the simulation has been saved as the value.
        - param_arg_name (str): The name of the argument within function_to_evaluate function where the current calibration parameters are expected to be passed. This parameter must be included in **kwargs
        - n_workers (int, optional): The number of parallel workers to use (default is 1).
        - parallelization (str, optional): The parallelization method to use ('threads' or 'processes') (default is 'threads').
        - debug (bool, optional): If True, print debug output during optimization (default is False).
        - **kwargs: Additional keyword arguments, that will be passed to function_to_evaluate.
        
        Returns:
        None
        """
        
        #SWATProblemMultimodel.__init__(self, params, function_to_evaluate, param_arg_name, n_workers, parallelization, None, None, None, None, None, debug, **kwargs)
        super().__init__(params, function_to_evaluate, param_arg_name, n_workers, parallelization, None, None, None, None, None, debug, **kwargs)

