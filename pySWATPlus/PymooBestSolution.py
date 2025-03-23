import numpy as np
import itertools
import shutil
import multiprocessing
from typing import Dict, List, Tuple

class SolutionManager:
    """
    Class to manage the best solution found during optimization.
    """
    def __init__(self):
        self.X = None
        self.path = None
        self.error = None
        self.lock = multiprocessing.Lock()
        

    def add_solution(self, X: np.ndarray, path: Dict[str, str], error: float) -> None:
        """
        Add a solution if it is better than the current best solution.
        """
        with self.lock:
            if self.error is None or error < self.error:
                self.X = X
                self.path = path
                self.error = error
    
    def get_solution(self) -> Tuple[np.ndarray, Dict[str, str], float]:
        """
        Retrieve the best solution.
        """
        with self.lock:
            return self.X, self.path, self.error
    
    def add_solutions(self, X_array: np.ndarray, paths_array: List[Dict[str, str]], errors_array: np.ndarray) -> None:
        """
        Update the best solution based on provided paths and errors. Only the best solution is kept; others are deleted.
        """
        if len(errors_array) == 0:
            return
        
        min_idx = np.nanargmin(errors_array)
        path = paths_array[min_idx]
        error = errors_array[min_idx]
        X = X_array[min_idx]
        
        self.add_solution(X, path, error)
        
        with self.lock:
            best_paths = set(self.path.values()) if self.path else set()
            all_paths = set(itertools.chain.from_iterable(map(lambda x: x.values(), paths_array)))
        
        for i in all_paths:
            if i not in best_paths and i is not None:
                shutil.rmtree(i, ignore_errors=True)
