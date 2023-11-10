import sys
import multiprocessing
import numpy as np
import itertools
import shutil
from typing import Dict, List

this = sys.modules[__name__]

this.X = None
this.path = None
this.error = None
this.lock = multiprocessing.Lock()


def add_solutions(paths_array: List[Dict[str, str]], errors_array: np.ndarray) -> None:
    """
    Update the best solution based on the provided paths and errors.

    Parameters:
    - paths_array (np.ndarray): An array of paths.
    - errors_array (np.ndarray): An array of errors.

    Returns:
    None
    """
    
    min_idx = np.argmin(errors_array)
    path = paths_array[min_idx]
    error = errors_array[min_idx]

    add_solution(None, path, error)

    best = this.path.values()
    all_paths = itertools.chain.from_iterable((map(lambda x: x.values(), paths_array)))

    
    for i in all_paths:
        if i not in best:
            shutil.rmtree(i)


def add_solution(X, path, error):
    with this.lock:
        if this.error is None or this.error > error:
            this.X = X
            this.path = path
            this.error = error


def get_solution():
    with this.lock:
        return this.X, this.path, this.error

